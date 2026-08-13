from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import os
from pathlib import Path

from newland_engine.cognition.prompt_registry import (
    PromptRegistry,
    PromptRegistryError,
)


BASE_PROMPT = "Decidi autonomamente. Restituisci soltanto JSON."
SCHEMA = {
    "type": "object",
    "properties": {"intention": {"type": "object"}},
    "required": ["intention"],
    "additionalProperties": False,
}


def digest_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def write_version(
    registry: Path,
    version: str,
    *,
    lessons: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    version_dir = registry / "versions" / version
    version_dir.mkdir(parents=True)
    base = BASE_PROMPT.encode()
    lesson_bytes = json.dumps(
        lessons or [], ensure_ascii=False, sort_keys=True, indent=2
    ).encode()
    schema_bytes = json.dumps(
        SCHEMA, ensure_ascii=False, sort_keys=True, indent=2
    ).encode()
    examples = b"[]"
    (version_dir / "base.md").write_bytes(base)
    (version_dir / "lessons.json").write_bytes(lesson_bytes)
    (version_dir / "schema.json").write_bytes(schema_bytes)
    (version_dir / "examples.json").write_bytes(examples)
    return {
        "base": f"versions/{version}/base.md",
        "lessons": f"versions/{version}/lessons.json",
        "schema": f"versions/{version}/schema.json",
        "examples": f"versions/{version}/examples.json",
        "hashes": {
            "base": digest_bytes(base),
            "lessons": digest_bytes(lesson_bytes),
            "schema": digest_bytes(schema_bytes),
            "examples": digest_bytes(examples),
        },
    }


def write_registry(registry: Path) -> None:
    version = "agent-cognition-v4"
    descriptor = write_version(registry, version)
    manifest = {
        "format_version": 1,
        "active_version": version,
        "previous_version": None,
        "candidate_version": None,
        "rollout": {
            "state": "stable",
            "minimum_observations": 2,
            "successes": 0,
            "failures": 0,
        },
        "versions": {version: descriptor},
    }
    (registry / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2)
    )


class PromptRegistryTests(unittest.TestCase):
    def test_repository_registry_has_migration_parity_with_v4_contract(self) -> None:
        from newland_engine.cognition.schema import DEFAULT_PROMPT_REGISTRY

        registry = PromptRegistry(DEFAULT_PROMPT_REGISTRY)

        artifact = registry.snapshot()

        self.assertEqual("agent-cognition-v4", artifact.version)
        self.assertIn("Sei una mente abitante di Newland", artifact.system_prompt)
        self.assertIn("Restituisci soltanto il JSON richiesto", artifact.system_prompt)
        self.assertEqual(
            {
                "intention",
                "memory_appraisals",
                "mental_updates",
                "attention_schedule",
            },
            set(artifact.schema["required"]),
        )
        self.assertFalse(artifact.schema["additionalProperties"])
        self.assertEqual(
            {
                "reference.source_field",
                "material.consume_unavailable",
                "response.shape",
            },
            {
                str(example["violation_code"])
                for example in artifact.examples
            },
        )
        self.assertEqual(4, len(artifact.examples))

    def test_default_registry_loads_outside_repository_working_directory(self) -> None:
        from newland_engine.cognition.schema import DEFAULT_PROMPT_REGISTRY

        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                artifact = PromptRegistry(DEFAULT_PROMPT_REGISTRY).snapshot()
            finally:
                os.chdir(previous)

        self.assertEqual("agent-cognition-v4", artifact.version)

    def test_loads_verified_external_artifact_and_composes_lessons(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry_path = Path(directory) / "registry"
            write_registry(registry_path)
            registry = PromptRegistry(registry_path)

            artifact = registry.snapshot()

            self.assertEqual("agent-cognition-v4", artifact.version)
            self.assertEqual(BASE_PROMPT, artifact.base_prompt)
            self.assertEqual(SCHEMA, artifact.schema)
            self.assertEqual(BASE_PROMPT, artifact.system_prompt)
            self.assertEqual(64, len(artifact.prompt_hash))
            self.assertEqual(64, len(artifact.schema_hash))

    def test_tampered_artifact_keeps_last_verified_snapshot_and_degrades_health(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry_path = Path(directory) / "registry"
            write_registry(registry_path)
            registry = PromptRegistry(registry_path)
            verified = registry.snapshot()
            (registry_path / "versions/agent-cognition-v4/base.md").write_text(
                "prompt manomesso"
            )

            retained = registry.snapshot()

            self.assertIs(verified, retained)
            self.assertEqual("degraded", registry.health()["status"])
            self.assertIn("hash", str(registry.health()["last_error"]))

    def test_initial_tampering_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry_path = Path(directory) / "registry"
            write_registry(registry_path)
            (registry_path / "versions/agent-cognition-v4/base.md").write_text(
                "prompt manomesso"
            )

            with self.assertRaises(PromptRegistryError):
                PromptRegistry(registry_path)

    def test_rejects_duplicate_or_oversized_lesson_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry_path = Path(directory) / "registry"
            write_registry(registry_path)
            registry = PromptRegistry(registry_path)
            duplicated = {
                "lesson_id": "les-duplicate",
                "violation_codes": ["response.shape"],
                "text": "Usa la forma richiesta.",
                "rationale": "Forma tecnica.",
                "risks": [],
            }

            with self.assertRaisesRegex(PromptRegistryError, "duplicate"):
                registry.stage_candidate(lessons=[duplicated, duplicated])
            with self.assertRaisesRegex(PromptRegistryError, "size budget"):
                registry.stage_candidate(
                    lessons=[
                        {
                            **duplicated,
                            "lesson_id": "les-too-large",
                            "text": "x" * 4_001,
                        }
                    ]
                )

    def test_registry_itself_rejects_coaching_and_private_lessons(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry_path = Path(directory) / "registry"
            write_registry(registry_path)
            registry = PromptRegistry(registry_path)
            base = {
                "lesson_id": "les-policy",
                "violation_codes": ["material.consume_unavailable"],
                "rationale": "Chiarimento tecnico.",
                "risks": [],
            }

            with self.assertRaisesRegex(PromptRegistryError, "coaches"):
                registry.stage_candidate(
                    lessons=[{**base, "text": "Se manca acqua, scegli rest."}]
                )
            with self.assertRaisesRegex(PromptRegistryError, "coaches"):
                registry.stage_candidate(
                    lessons=[{**base, "text": "If blocked, choose rest."}]
                )
            with self.assertRaisesRegex(PromptRegistryError, "coaches"):
                registry.stage_candidate(
                    lessons=[{**base, "text": "Se sei stanco, devi riposare."}]
                )
            with self.assertRaisesRegex(PromptRegistryError, "private"):
                registry.stage_candidate(
                    lessons=[
                        {
                            **base,
                            "text": "Non usare nwl-private-person come fonte.",
                        }
                    ]
                )

    def test_canary_promotes_candidate_after_first_attempt_successes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry_path = Path(directory) / "registry"
            write_registry(registry_path)
            registry = PromptRegistry(registry_path)
            candidate = registry.stage_candidate(
                lessons=[
                    {
                        "lesson_id": "les-source-event-id",
                        "violation_codes": ["memory.source_field"],
                        "text": "In memory_appraisals usa sempre source_event_id.",
                        "rationale": "Corregge il nome del campo.",
                        "risks": [],
                    }
                ]
            )

            selected = registry.snapshot()
            self.assertEqual(candidate.version, selected.version)
            self.assertIn("source_event_id", selected.system_prompt)
            registry.observe(candidate.version, first_attempt_valid=True)
            registry.observe(candidate.version, first_attempt_valid=True)

            health = registry.health()
            self.assertEqual("stable", health["rollout_state"])
            self.assertEqual(candidate.version, health["active_version"])
            self.assertEqual("agent-cognition-v4", health["previous_version"])

    def test_canary_rolls_back_when_candidate_needs_repair(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry_path = Path(directory) / "registry"
            write_registry(registry_path)
            registry = PromptRegistry(registry_path)
            candidate = registry.stage_candidate(
                lessons=[
                    {
                        "lesson_id": "les-bad",
                        "violation_codes": ["response.shape"],
                        "text": "Mantieni la forma richiesta.",
                        "rationale": "Test candidate.",
                        "risks": [],
                    }
                ]
            )

            registry.observe(candidate.version, first_attempt_valid=False)

            health = registry.health()
            self.assertEqual("stable", health["rollout_state"])
            self.assertEqual("agent-cognition-v4", health["active_version"])
            self.assertIsNone(health["candidate_version"])
            self.assertEqual(1, health["rollback_count"])

    def test_candidate_does_not_promote_when_segmented_metrics_regress(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry_path = Path(directory) / "registry"
            write_registry(registry_path)
            registry = PromptRegistry(registry_path)
            registry.observe(
                "agent-cognition-v4",
                first_attempt_valid=True,
                provider="dashscope",
                model="qwen-flash-character",
                tokens=80,
            )
            candidate = registry.stage_candidate(
                lessons=[
                    {
                        "lesson_id": "les-shape",
                        "violation_codes": ["response.shape"],
                        "text": "Restituisci tutti i campi richiesti.",
                        "rationale": "Mantiene il contratto.",
                        "risks": [],
                    }
                ]
            )
            registry.observe(
                candidate.version,
                first_attempt_valid=True,
                provider="dashscope",
                model="qwen-flash-character",
                tokens=100,
            )
            registry.observe(
                candidate.version,
                first_attempt_valid=True,
                provider="dashscope",
                model="qwen-flash-character",
                tokens=100,
            )

            health = registry.health()
            self.assertEqual("stable", health["rollout_state"])
            self.assertIsNone(health["candidate_version"])
            self.assertEqual("agent-cognition-v4", health["active_version"])
            self.assertEqual(1, health["rollback_count"])

    def test_transport_failure_does_not_roll_back_candidate(self) -> None:
        from newland_engine.cognition.llm_adapter import OllamaCognition
        from newland_engine.cognition.exceptions import CognitionUnavailable

        with tempfile.TemporaryDirectory() as directory:
            registry_path = Path(directory) / "registry"
            write_registry(registry_path)
            registry = PromptRegistry(registry_path)
            candidate = registry.stage_candidate(
                lessons=[
                    {
                        "lesson_id": "les-shape",
                        "violation_codes": ["response.shape"],
                        "text": "Restituisci tutti i campi richiesti.",
                        "rationale": "Mantiene il contratto.",
                        "risks": [],
                    }
                ]
            )
            provider = OllamaCognition(
                model="missing-model",
                endpoint="http://127.0.0.1:1/api/chat",
                timeout_seconds=0.01,
                prompt_registry=registry,
            )
            from tests.test_live_cloud import cognition_context

            with self.assertRaises(CognitionUnavailable):
                provider.decide(cognition_context())

            self.assertEqual(
                candidate.version, registry.health()["candidate_version"]
            )
            self.assertEqual(0, registry.health()["rollback_count"])

    def test_inference_snapshot_does_not_change_after_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry_path = Path(directory) / "registry"
            write_registry(registry_path)
            registry = PromptRegistry(registry_path)
            original = registry.snapshot()
            candidate = registry.stage_candidate(
                lessons=[
                    {
                        "lesson_id": "les-shape",
                        "violation_codes": ["response.shape"],
                        "text": "Restituisci tutti i campi richiesti.",
                        "rationale": "Mantiene il contratto.",
                        "risks": [],
                    }
                ]
            )
            registry.observe(candidate.version, first_attempt_valid=True)
            registry.observe(candidate.version, first_attempt_valid=True)

            self.assertEqual("agent-cognition-v4", original.version)
            self.assertNotIn("tutti i campi", original.system_prompt)
            self.assertEqual(candidate.version, registry.snapshot().version)

    def test_manual_rollback_swaps_active_and_previous_versions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry_path = Path(directory) / "registry"
            write_registry(registry_path)
            registry = PromptRegistry(registry_path)
            candidate = registry.stage_candidate(
                lessons=[
                    {
                        "lesson_id": "les-shape",
                        "violation_codes": ["response.shape"],
                        "text": "Restituisci tutti i campi richiesti.",
                        "rationale": "Mantiene il contratto.",
                        "risks": [],
                    }
                ]
            )
            registry.observe(candidate.version, first_attempt_valid=True)
            registry.observe(candidate.version, first_attempt_valid=True)

            rolled_back = registry.rollback()

            self.assertEqual("agent-cognition-v4", rolled_back.version)
            self.assertEqual("agent-cognition-v4", registry.health()["active_version"])


if __name__ == "__main__":
    unittest.main()
