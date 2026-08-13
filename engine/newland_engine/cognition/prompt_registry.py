from __future__ import annotations

import hashlib
import json
import os
import fcntl
import re
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4


class PromptRegistryError(RuntimeError):
    pass


_PRIVATE_IDENTIFIER = re.compile(
    r"\bnwl-[A-Za-z0-9_-]+\b|"
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
_ACTION_COACHING = re.compile(
    r"\b(?:scegli|preferisci|devi|dovresti|choose|prefer|must|should)\b"
    r"[^.\n]{0,40}\b(?:"
    r"speak|move|rest|offer_help|gather|consume|perform_activity|"
    r"propose_cooperation|respond_cooperation|perform_cooperation|"
    r"open_dispute|respond_dispute|attune_resonance|"
    r"parlare|muoverti|spostarti|riposare|aiutare|raccogliere|consumare|"
    r"cooperare|contestare|sintonizzarti"
    r")\b",
    re.IGNORECASE,
)


def lesson_safety_violation(content: str) -> str | None:
    if _PRIVATE_IDENTIFIER.search(content):
        return "private"
    if _ACTION_COACHING.search(content):
        return "coaching"
    return None


@dataclass(frozen=True, slots=True)
class PromptArtifact:
    version: str
    base_prompt: str
    lessons: tuple[dict[str, object], ...]
    schema: dict[str, Any]
    examples: tuple[dict[str, object], ...]
    system_prompt: str
    prompt_hash: str
    schema_hash: str


class PromptRegistry:
    """Loads immutable prompt artifacts and atomically manages prompt rollout."""

    MAX_LESSON_TEXT_CHARACTERS = 4_000
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.manifest_path = self.path / "manifest.json"
        self._lock = RLock()
        self._last_verified: PromptArtifact | None = None
        self._status = "healthy"
        self._last_error: str | None = None
        self._rollback_count = 0
        try:
            self._last_verified = self._selected_artifact(self._read_manifest())
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
            raise PromptRegistryError(str(error)) from error

    def snapshot(self) -> PromptArtifact:
        with self._lock:
            try:
                artifact = self._selected_artifact(self._read_manifest())
            except (
                OSError,
                ValueError,
                TypeError,
                KeyError,
                json.JSONDecodeError,
            ) as error:
                self._status = "degraded"
                self._last_error = str(error)
                if self._last_verified is None:
                    raise PromptRegistryError(str(error)) from error
                return self._last_verified
            self._last_verified = artifact
            self._status = "healthy"
            self._last_error = None
            return artifact

    def stage_candidate(
        self, *, lessons: list[dict[str, object]]
    ) -> PromptArtifact:
        with self._lock:
            with self._manifest_lock():
                return self._stage_candidate_locked(lessons)

    def _stage_candidate_locked(
        self, lessons: list[dict[str, object]]
    ) -> PromptArtifact:
        self._validate_lessons(lessons)
        manifest = self._read_manifest()
        if manifest.get("candidate_version") is not None:
            raise PromptRegistryError("a prompt candidate is already in canary")
        active = self._load_version(manifest, str(manifest["active_version"]))
        version = f"{active.version}-annealed-{uuid4().hex[:12]}"
        descriptor = self._write_version(
            version,
            base_prompt=active.base_prompt,
            lessons=lessons,
            schema=active.schema,
            examples=list(active.examples),
        )
        versions = dict(manifest["versions"])
        versions[version] = descriptor
        manifest["versions"] = versions
        manifest["candidate_version"] = version
        manifest["rollout"] = {
            **dict(manifest.get("rollout", {})),
            "state": "canary",
            "successes": 0,
            "failures": 0,
            "baseline_metrics": dict(manifest.get("metrics", {})),
            "candidate_metrics": {},
        }
        self._write_manifest(manifest)
        return self._load_version(manifest, version)

    def observe(
        self,
        version: str,
        *,
        first_attempt_valid: bool,
        provider: str = "unknown",
        model: str = "unknown",
        tokens: int | None = None,
    ) -> None:
        with self._lock:
            with self._manifest_lock():
                self._observe_locked(
                    version,
                    first_attempt_valid=first_attempt_valid,
                    provider=provider,
                    model=model,
                    tokens=tokens,
                )

    def _observe_locked(
        self,
        version: str,
        *,
        first_attempt_valid: bool,
        provider: str,
        model: str,
        tokens: int | None,
    ) -> None:
        manifest = self._read_manifest()
        metric_key = f"{provider}:{model}"
        if manifest.get("candidate_version") != version:
            if manifest.get("active_version") == version:
                metrics = dict(manifest.get("metrics", {}))
                metrics[metric_key] = self._record_metric(
                    dict(metrics.get(metric_key, {})),
                    first_attempt_valid=first_attempt_valid,
                    tokens=tokens,
                )
                manifest["metrics"] = metrics
                self._write_manifest(manifest)
            return
        rollout = dict(manifest.get("rollout", {}))
        key = "successes" if first_attempt_valid else "failures"
        rollout[key] = int(rollout.get(key, 0)) + 1
        candidate_metrics = dict(rollout.get("candidate_metrics", {}))
        candidate_metrics[metric_key] = self._record_metric(
            dict(candidate_metrics.get(metric_key, {})),
            first_attempt_valid=first_attempt_valid,
            tokens=tokens,
        )
        rollout["candidate_metrics"] = candidate_metrics
        minimum = int(rollout.get("minimum_observations", 2))
        if not first_attempt_valid:
            manifest["candidate_version"] = None
            rollout["state"] = "stable"
            manifest["rollback_count"] = int(
                manifest.get("rollback_count", 0)
            ) + 1
        elif int(rollout["successes"]) >= minimum:
            if self._candidate_improves(rollout):
                previous = str(manifest["active_version"])
                manifest["previous_version"] = previous
                manifest["active_version"] = version
                manifest["candidate_version"] = None
                rollout["state"] = "stable"
                manifest["metrics"] = candidate_metrics
            else:
                manifest["candidate_version"] = None
                rollout["state"] = "stable"
                manifest["rollback_count"] = int(
                    manifest.get("rollback_count", 0)
                ) + 1
        manifest["rollout"] = rollout
        self._write_manifest(manifest)

    def rollback(self) -> PromptArtifact:
        with self._lock:
            with self._manifest_lock():
                return self._rollback_locked()

    def _rollback_locked(self) -> PromptArtifact:
        manifest = self._read_manifest()
        previous = manifest.get("previous_version")
        if not isinstance(previous, str) or not previous:
            raise PromptRegistryError("no previous prompt version to restore")
        active = str(manifest["active_version"])
        manifest["active_version"] = previous
        manifest["previous_version"] = active
        manifest["candidate_version"] = None
        manifest["rollout"] = {
            **dict(manifest.get("rollout", {})),
            "state": "stable",
            "successes": 0,
            "failures": 0,
        }
        manifest["rollback_count"] = int(
            manifest.get("rollback_count", 0)
        ) + 1
        self._write_manifest(manifest)
        artifact = self._load_version(manifest, previous)
        self._last_verified = artifact
        return artifact

    def health(self) -> dict[str, object]:
        with self._lock:
            try:
                manifest = self._read_manifest()
            except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
                manifest = {}
            rollout = dict(manifest.get("rollout", {}))
            return {
                "status": self._status,
                "last_error": self._last_error,
                "active_version": manifest.get("active_version"),
                "previous_version": manifest.get("previous_version"),
                "candidate_version": manifest.get("candidate_version"),
                "rollout_state": rollout.get("state"),
                "canary_successes": rollout.get("successes", 0),
                "canary_failures": rollout.get("failures", 0),
                "baseline_metrics": rollout.get("baseline_metrics", {}),
                "candidate_metrics": rollout.get("candidate_metrics", {}),
                "rollback_count": manifest.get(
                    "rollback_count", self._rollback_count
                ),
            }

    def _selected_artifact(self, manifest: dict[str, Any]) -> PromptArtifact:
        candidate = manifest.get("candidate_version")
        selected = candidate if isinstance(candidate, str) else manifest["active_version"]
        return self._load_version(manifest, str(selected))

    def _read_manifest(self) -> dict[str, Any]:
        manifest = json.loads(self.manifest_path.read_text())
        if manifest.get("format_version") != 1:
            raise ValueError("unsupported prompt manifest format")
        if not isinstance(manifest.get("versions"), dict):
            raise ValueError("prompt manifest versions must be an object")
        return manifest

    def _load_version(
        self, manifest: dict[str, Any], version: str
    ) -> PromptArtifact:
        descriptor = manifest["versions"][version]
        if not isinstance(descriptor, dict):
            raise ValueError(f"invalid descriptor for prompt version {version}")
        hashes = descriptor.get("hashes")
        if not isinstance(hashes, dict):
            raise ValueError(f"missing hashes for prompt version {version}")
        loaded: dict[str, bytes] = {}
        for key in ("base", "lessons", "schema", "examples"):
            target = self._safe_path(str(descriptor[key]))
            content = target.read_bytes()
            if self._digest(content) != hashes.get(key):
                raise ValueError(f"hash mismatch for {key} in prompt version {version}")
            loaded[key] = content
        base_prompt = loaded["base"].decode().strip()
        lessons = json.loads(loaded["lessons"])
        schema = json.loads(loaded["schema"])
        examples = json.loads(loaded["examples"])
        if not isinstance(lessons, list) or not isinstance(schema, dict):
            raise ValueError(f"invalid prompt artifact shape for {version}")
        if not isinstance(examples, list):
            raise ValueError(f"invalid prompt examples for {version}")
        lesson_texts = [
            str(lesson["text"]).strip()
            for lesson in lessons
            if isinstance(lesson, dict) and str(lesson.get("text", "")).strip()
        ]
        system_prompt = base_prompt
        if lesson_texts:
            system_prompt += "\n\nLezioni tecniche attive:\n- " + "\n- ".join(
                lesson_texts
            )
        prompt_hash = self._digest(system_prompt.encode())
        return PromptArtifact(
            version=version,
            base_prompt=base_prompt,
            lessons=tuple(dict(lesson) for lesson in lessons),
            schema=schema,
            examples=tuple(dict(example) for example in examples),
            system_prompt=system_prompt,
            prompt_hash=prompt_hash,
            schema_hash=str(hashes["schema"]),
        )

    def _safe_path(self, relative: str) -> Path:
        target = (self.path / relative).resolve()
        root = self.path.resolve()
        if target != root and root not in target.parents:
            raise ValueError("prompt artifact path escapes registry")
        return target

    def _write_version(
        self,
        version: str,
        *,
        base_prompt: str,
        lessons: list[dict[str, object]],
        schema: dict[str, Any],
        examples: list[dict[str, object]],
    ) -> dict[str, object]:
        directory = self.path / "versions" / version
        directory.mkdir(parents=True, exist_ok=False)
        contents = {
            "base": base_prompt.encode(),
            "lessons": json.dumps(
                lessons, ensure_ascii=False, sort_keys=True, indent=2
            ).encode(),
            "schema": json.dumps(
                schema, ensure_ascii=False, sort_keys=True, indent=2
            ).encode(),
            "examples": json.dumps(
                examples, ensure_ascii=False, sort_keys=True, indent=2
            ).encode(),
        }
        filenames = {
            "base": "base.md",
            "lessons": "lessons.json",
            "schema": "schema.json",
            "examples": "examples.json",
        }
        descriptor: dict[str, object] = {"hashes": {}}
        for key, content in contents.items():
            filename = filenames[key]
            (directory / filename).write_bytes(content)
            descriptor[key] = f"versions/{version}/{filename}"
            descriptor["hashes"][key] = self._digest(content)  # type: ignore[index]
        return descriptor

    def _validate_lessons(self, lessons: list[dict[str, object]]) -> None:
        lesson_ids: set[str] = set()
        normalized_texts: set[str] = set()
        total_characters = 0
        for lesson in lessons:
            if not isinstance(lesson, dict):
                raise PromptRegistryError("prompt lessons must be objects")
            lesson_id = str(lesson.get("lesson_id", "")).strip()
            text = str(lesson.get("text", "")).strip()
            if not lesson_id or not text:
                raise PromptRegistryError("prompt lessons require id and text")
            combined = " ".join(
                (
                    text,
                    str(lesson.get("rationale", "")),
                    *(str(value) for value in lesson.get("risks", [])),
                )
            )
            violation = lesson_safety_violation(combined)
            if violation == "private":
                raise PromptRegistryError(
                    "prompt lesson contains a private identifier"
                )
            if violation == "coaching":
                raise PromptRegistryError("prompt lesson coaches an agent action")
            normalized = " ".join(text.lower().split())
            if lesson_id in lesson_ids or normalized in normalized_texts:
                raise PromptRegistryError("duplicate prompt lesson")
            lesson_ids.add(lesson_id)
            normalized_texts.add(normalized)
            total_characters += len(text)
        if total_characters > self.MAX_LESSON_TEXT_CHARACTERS:
            raise PromptRegistryError("prompt lesson overlay exceeds size budget")

    def _write_manifest(self, manifest: dict[str, Any]) -> None:
        self.path.mkdir(parents=True, exist_ok=True)
        temporary = self.path / f".manifest-{uuid4().hex}.tmp"
        temporary.write_text(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2)
            + "\n"
        )
        os.replace(temporary, self.manifest_path)

    @contextmanager
    def _manifest_lock(self):
        self.path.mkdir(parents=True, exist_ok=True)
        lock_path = self.path / ".manifest.lock"
        with lock_path.open("a+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def _record_metric(
        metric: dict[str, object], *, first_attempt_valid: bool, tokens: int | None
    ) -> dict[str, object]:
        observations = int(metric.get("observations", 0)) + 1
        valid = int(metric.get("first_attempt_valid", 0)) + int(
            first_attempt_valid
        )
        token_observations = int(metric.get("token_observations", 0))
        total_tokens = int(metric.get("total_tokens", 0))
        if tokens is not None and tokens >= 0:
            token_observations += 1
            total_tokens += tokens
        return {
            "observations": observations,
            "first_attempt_valid": valid,
            "token_observations": token_observations,
            "total_tokens": total_tokens,
        }

    @staticmethod
    def _candidate_improves(rollout: dict[str, object]) -> bool:
        baseline = dict(rollout.get("baseline_metrics", {}))
        candidate = dict(rollout.get("candidate_metrics", {}))
        for key, raw_candidate in candidate.items():
            current = dict(raw_candidate)
            previous = dict(baseline.get(key, {}))
            current_observations = int(current.get("observations", 0))
            if current_observations == 0:
                continue
            current_rate = int(current.get("first_attempt_valid", 0)) / current_observations
            previous_observations = int(previous.get("observations", 0))
            if previous_observations:
                previous_rate = int(previous.get("first_attempt_valid", 0)) / previous_observations
                if current_rate < previous_rate:
                    return False
            current_token_count = int(current.get("token_observations", 0))
            previous_token_count = int(previous.get("token_observations", 0))
            if current_token_count and previous_token_count:
                current_average = int(current.get("total_tokens", 0)) / current_token_count
                previous_average = int(previous.get("total_tokens", 0)) / previous_token_count
                if current_average > previous_average:
                    return False
        return True

    @staticmethod
    def _digest(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()
