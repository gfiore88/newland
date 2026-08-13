from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import RLock
from urllib.request import Request, urlopen

from .prompt_registry import (
    PromptArtifact,
    PromptRegistry,
    lesson_safety_violation,
)


@dataclass(frozen=True, slots=True)
class PromptFailure:
    violation_code: str
    field_path: str
    observed_type: str
    provider: str
    model: str
    prompt_version: str
    prompt_hash: str
    schema_hash: str
    attempt: int
    detail: str = ""


@dataclass(frozen=True, slots=True)
class PromptLesson:
    lesson_id: str
    violation_codes: tuple[str, ...]
    text: str
    rationale: str
    risks: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class PromptLessonRejected(ValueError):
    pass


class PromptAnnealingPolicy:
    MAX_TEXT_LENGTH = 600

    def validate(
        self, lesson: PromptLesson, *, observed_codes: set[str]
    ) -> None:
        if not lesson.lesson_id.startswith("les-"):
            raise PromptLessonRejected("lesson_id must start with les-")
        if not lesson.violation_codes or not set(lesson.violation_codes) <= observed_codes:
            raise PromptLessonRejected("lesson references unobserved violation codes")
        text = lesson.text.strip()
        if not text or len(text) > self.MAX_TEXT_LENGTH:
            raise PromptLessonRejected("lesson text is empty or too long")
        combined = " ".join((lesson.text, lesson.rationale, *lesson.risks))
        violation = lesson_safety_violation(combined)
        if violation == "private":
            raise PromptLessonRejected("lesson contains a private identifier")
        if violation == "coaching":
            raise PromptLessonRejected("lesson coaches an agent action")


class PromptFailureLedger:
    """Persists minimized prompt failures without cognitive content."""

    _ARRAY_INDEX = re.compile(r"\[\d+\]")
    _SAFE_FIELD_PATH = re.compile(
        r"^(?:response|intention|memory_appraisals|mental_updates|"
        r"attention_schedule)(?:\[\]|\.[A-Za-z_][A-Za-z0-9_]*)*$"
    )

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        with self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS prompt_failures (
                    fingerprint TEXT PRIMARY KEY,
                    violation_code TEXT NOT NULL,
                    field_path TEXT NOT NULL,
                    observed_type TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    prompt_version TEXT NOT NULL,
                    prompt_hash TEXT NOT NULL,
                    schema_hash TEXT NOT NULL,
                    redacted_detail TEXT NOT NULL,
                    count INTEGER NOT NULL,
                    first_attempt_count INTEGER NOT NULL,
                    repair_attempt_count INTEGER NOT NULL,
                    annealed_count INTEGER NOT NULL DEFAULT 0,
                    first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            columns = {
                str(row["name"])
                for row in self._connection.execute(
                    "PRAGMA table_info(prompt_failures)"
                ).fetchall()
            }
            if "annealed_count" not in columns:
                self._connection.execute(
                    "ALTER TABLE prompt_failures "
                    "ADD COLUMN annealed_count INTEGER NOT NULL DEFAULT 0"
                )

    def record(self, failure: PromptFailure) -> str:
        if failure.attempt < 1:
            raise ValueError("prompt failure attempt must be positive")
        candidate_path = self._ARRAY_INDEX.sub("[]", failure.field_path.strip())
        field_path = (
            candidate_path
            if self._SAFE_FIELD_PATH.fullmatch(candidate_path)
            else "response"
        )
        canonical = {
            "violation_code": failure.violation_code.strip(),
            "field_path": field_path,
            "observed_type": failure.observed_type.strip(),
            "provider": failure.provider.strip(),
            "model": failure.model.strip(),
            "prompt_version": failure.prompt_version.strip(),
            "prompt_hash": failure.prompt_hash,
            "schema_hash": failure.schema_hash,
        }
        fingerprint = hashlib.sha256(
            json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        detail = self._minimized_detail(failure)
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO prompt_failures (
                    fingerprint, violation_code, field_path, observed_type,
                    provider, model, prompt_version, prompt_hash, schema_hash,
                    redacted_detail, count, first_attempt_count,
                    repair_attempt_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                ON CONFLICT(fingerprint) DO UPDATE SET
                    count = count + 1,
                    first_attempt_count = first_attempt_count + excluded.first_attempt_count,
                    repair_attempt_count = repair_attempt_count + excluded.repair_attempt_count,
                    redacted_detail = excluded.redacted_detail,
                    last_seen_at = CURRENT_TIMESTAMP
                """,
                (
                    fingerprint,
                    canonical["violation_code"],
                    canonical["field_path"],
                    canonical["observed_type"],
                    canonical["provider"],
                    canonical["model"],
                    canonical["prompt_version"],
                    canonical["prompt_hash"],
                    canonical["schema_hash"],
                    detail,
                    1 if failure.attempt == 1 else 0,
                    1 if failure.attempt > 1 else 0,
                ),
            )
        return fingerprint

    def evidence(self, fingerprint: str) -> dict[str, object]:
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM prompt_failures WHERE fingerprint = ?",
                (fingerprint,),
            ).fetchone()
        if row is None:
            raise KeyError(fingerprint)
        return dict(row)

    def summary(self) -> dict[str, int]:
        with self._lock:
            row = self._connection.execute(
                "SELECT COUNT(*) AS unique_fingerprints, "
                "COALESCE(SUM(count), 0) AS failures FROM prompt_failures"
            ).fetchone()
        return {
            "unique_fingerprints": int(row["unique_fingerprints"]),
            "failures": int(row["failures"]),
        }

    def pending(self, *, minimum_count: int) -> list[dict[str, object]]:
        if minimum_count < 1:
            raise ValueError("minimum prompt failure count must be positive")
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT fingerprint, violation_code, field_path, observed_type,
                       provider, model, prompt_version, prompt_hash, schema_hash,
                       count, first_attempt_count, repair_attempt_count
                FROM prompt_failures
                WHERE count - annealed_count >= ?
                ORDER BY (count - annealed_count) DESC, fingerprint
                """,
                (minimum_count,),
            ).fetchall()
        return [dict(row) for row in rows]

    def mark_annealed(self, fingerprint: str) -> None:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                "UPDATE prompt_failures SET annealed_count = count "
                "WHERE fingerprint = ?",
                (fingerprint,),
            )
        if cursor.rowcount != 1:
            raise KeyError(fingerprint)

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> PromptFailureLedger:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def _minimized_detail(self, failure: PromptFailure) -> str:
        # Free-form exception text can contain private cognitive content. Keep
        # only the already structured categories used by the annealer.
        return (
            f"{failure.violation_code}|"
            f"{self._safe_field_path(failure.field_path)}|"
            f"{failure.observed_type}"
        )[:500]

    def _safe_field_path(self, field_path: str) -> str:
        candidate = self._ARRAY_INDEX.sub("[]", field_path.strip())
        return candidate if self._SAFE_FIELD_PATH.fullmatch(candidate) else "response"


AnnealerRequester = Callable[[dict[str, object]], dict[str, object]]


class LocalPromptAnnealer:
    """Turns aggregated structural failures into policy-checked lesson candidates."""

    def __init__(
        self,
        *,
        registry: PromptRegistry,
        ledger: PromptFailureLedger,
        model: str = "qwen2.5:3b",
        endpoint: str = "http://127.0.0.1:11434/api/chat",
        requester: AnnealerRequester | None = None,
        evidence_threshold: int = 3,
        policy: PromptAnnealingPolicy | None = None,
    ) -> None:
        if evidence_threshold < 1:
            raise ValueError("prompt annealing threshold must be positive")
        self.registry = registry
        self.ledger = ledger
        self.model = model
        self.endpoint = endpoint
        self.requester = requester or self._request_ollama
        self.evidence_threshold = evidence_threshold
        self.policy = policy or PromptAnnealingPolicy()

    def run_once(self) -> PromptArtifact | None:
        if self.registry.health().get("candidate_version") is not None:
            return None
        evidence = self.ledger.pending(minimum_count=self.evidence_threshold)
        if not evidence:
            return None
        selected = evidence[0]
        code = str(selected["violation_code"])
        payload = {
            "model": self.model,
            "failure": {
                "violation_code": code,
                "field_path": selected["field_path"],
                "observed_type": selected["observed_type"],
                "provider": selected["provider"],
                "model": selected["model"],
                "count": selected["count"],
            },
            "requirements": {
                "technical_only": True,
                "no_action_coaching": True,
                "no_private_identifiers": True,
                "max_text_length": self.policy.MAX_TEXT_LENGTH,
            },
        }
        parsed = self.requester(payload)
        lesson = PromptLesson(
            lesson_id=str(parsed["lesson_id"]),
            violation_codes=tuple(str(value) for value in parsed["violation_codes"]),
            text=str(parsed["text"]),
            rationale=str(parsed["rationale"]),
            risks=tuple(str(value) for value in parsed.get("risks", [])),
        )
        self.policy.validate(lesson, observed_codes={code})
        active = self.registry.snapshot()
        lessons = [dict(existing) for existing in active.lessons]
        lessons.append(lesson.to_dict())
        candidate = self.registry.stage_candidate(lessons=lessons)
        self.ledger.mark_annealed(str(selected["fingerprint"]))
        return candidate

    def _request_ollama(self, payload: dict[str, object]) -> dict[str, object]:
        lesson_schema = {
            "type": "object",
            "properties": {
                "lesson_id": {"type": "string"},
                "violation_codes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                },
                "text": {"type": "string", "maxLength": 600},
                "rationale": {"type": "string", "maxLength": 600},
                "risks": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "lesson_id",
                "violation_codes",
                "text",
                "rationale",
                "risks",
            ],
            "additionalProperties": False,
        }
        request_payload = {
            "model": self.model,
            "stream": False,
            "think": False,
            "format": lesson_schema,
            "options": {"temperature": 0.2, "num_ctx": 4096, "num_predict": 512},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Genera una sola lezione tecnica concisa che chiarisca un "
                        "contratto JSON. Non suggerire azioni, motivazioni o psicologia "
                        "del personaggio. Non includere identificatori o dati privati."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(payload, ensure_ascii=False),
                },
            ],
        }
        request = Request(
            self.endpoint,
            data=json.dumps(request_payload, ensure_ascii=False).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode())
        return dict(json.loads(body["message"]["content"]))
