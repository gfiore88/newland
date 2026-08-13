from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from newland_engine.cognition.prompt_learning import (
    PromptAnnealingPolicy,
    PromptFailure,
    PromptFailureLedger,
    PromptLesson,
    PromptLessonRejected,
    LocalPromptAnnealer,
)


class PromptFailureLedgerTests(unittest.TestCase):
    def test_equivalent_failures_deduplicate_private_identifiers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "learning.db"
            with PromptFailureLedger(path) as ledger:
                first = ledger.record(
                    PromptFailure(
                        violation_code="reference.unknown",
                        field_path="mental_updates.beliefs[0].source_ids",
                        observed_type="string",
                        provider="dashscope",
                        model="qwen-flash-character",
                        prompt_version="agent-cognition-v4",
                        prompt_hash="a" * 64,
                        schema_hash="b" * 64,
                        attempt=1,
                        detail="unknown nwl-123 and event 11111111-1111-1111-1111-111111111111",
                    )
                )
                second = ledger.record(
                    PromptFailure(
                        violation_code="reference.unknown",
                        field_path="mental_updates.beliefs[0].source_ids",
                        observed_type="string",
                        provider="dashscope",
                        model="qwen-flash-character",
                        prompt_version="agent-cognition-v4",
                        prompt_hash="a" * 64,
                        schema_hash="b" * 64,
                        attempt=2,
                        detail="unknown nwl-999 and event 22222222-2222-2222-2222-222222222222",
                    )
                )

                summary = ledger.summary()

            self.assertEqual(first, second)
            self.assertEqual(1, summary["unique_fingerprints"])
            self.assertEqual(2, summary["failures"])

    def test_ledger_persists_redacted_evidence_across_restart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "learning.db"
            secret = "secret-private-value"
            with PromptFailureLedger(path) as ledger:
                fingerprint = ledger.record(
                    PromptFailure(
                        violation_code="response.shape",
                        field_path="intention",
                        observed_type="str",
                        provider="dashscope",
                        model="qwen-flash-character",
                        prompt_version="agent-cognition-v4",
                        prompt_hash="a" * 64,
                        schema_hash="b" * 64,
                        attempt=1,
                        detail=f"unexpected content bearer {secret}",
                    )
                )
            with PromptFailureLedger(path) as reopened:
                evidence = reopened.evidence(fingerprint)

            self.assertEqual(1, evidence["count"])
            self.assertNotIn(secret, str(evidence))
            self.assertNotIn("bearer", str(evidence).lower())
            self.assertEqual(
                "response.shape|intention|str", evidence["redacted_detail"]
            )

    def test_untrusted_field_path_cannot_persist_private_identifier(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with PromptFailureLedger(Path(directory) / "learning.db") as ledger:
                fingerprint = ledger.record(
                    PromptFailure(
                        violation_code="reference.unknown",
                        field_path="nwl-private-person",
                        observed_type="KeyError",
                        provider="dashscope",
                        model="qwen-flash-character",
                        prompt_version="agent-cognition-v4",
                        prompt_hash="a" * 64,
                        schema_hash="b" * 64,
                        attempt=1,
                        detail="private",
                    )
                )
                evidence = ledger.evidence(fingerprint)

            self.assertEqual("response", evidence["field_path"])
            self.assertNotIn("nwl-private-person", str(evidence))


class PromptAnnealingPolicyTests(unittest.TestCase):
    def test_accepts_concise_technical_lesson_for_observed_violation(self) -> None:
        policy = PromptAnnealingPolicy()
        lesson = PromptLesson(
            lesson_id="les-source-field",
            violation_codes=("memory.source_field",),
            text="In memory_appraisals usa source_event_id e non source_ids.",
            rationale="Evita una forma non conforme.",
            risks=(),
        )

        policy.validate(lesson, observed_codes={"memory.source_field"})

    def test_rejects_lesson_that_coaches_an_action(self) -> None:
        policy = PromptAnnealingPolicy()
        lesson = PromptLesson(
            lesson_id="les-coaching",
            violation_codes=("material.consume_unavailable",),
            text="Se non puoi consumare, scegli rest.",
            rationale="Evita il rifiuto.",
            risks=(),
        )

        with self.assertRaises(PromptLessonRejected):
            policy.validate(
                lesson, observed_codes={"material.consume_unavailable"}
            )

    def test_rejects_english_or_natural_language_action_coaching(self) -> None:
        policy = PromptAnnealingPolicy()

        for text in ("If blocked, choose rest.", "Se sei stanco, devi riposare."):
            with self.subTest(text=text), self.assertRaises(PromptLessonRejected):
                policy.validate(
                    PromptLesson(
                        lesson_id="les-coaching",
                        violation_codes=("material.consume_unavailable",),
                        text=text,
                        rationale="Evita il rifiuto.",
                        risks=(),
                    ),
                    observed_codes={"material.consume_unavailable"},
                )

    def test_rejects_lesson_with_private_identifier(self) -> None:
        policy = PromptAnnealingPolicy()
        lesson = PromptLesson(
            lesson_id="les-private",
            violation_codes=("reference.unknown",),
            text="Non usare mai nwl-123456 come source_id.",
            rationale="Evita un riferimento errato.",
            risks=(),
        )

        with self.assertRaises(PromptLessonRejected):
            policy.validate(lesson, observed_codes={"reference.unknown"})


class LocalPromptAnnealerTests(unittest.TestCase):
    def test_repeated_failure_generates_validated_candidate_locally(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            from tests.test_prompt_registry import write_registry
            from newland_engine.cognition.prompt_registry import PromptRegistry

            registry_path = root / "registry"
            write_registry(registry_path)
            ledger = PromptFailureLedger(root / "learning.db")
            failure = PromptFailure(
                violation_code="memory.source_field",
                field_path="memory_appraisals[].source_event_id",
                observed_type="KeyError",
                provider="dashscope",
                model="qwen-flash-character",
                prompt_version="agent-cognition-v4",
                prompt_hash="a" * 64,
                schema_hash="b" * 64,
                attempt=1,
                detail="missing source_event_id",
            )
            ledger.record(failure)
            ledger.record(failure)
            requests: list[dict[str, object]] = []

            def requester(payload: dict[str, object]) -> dict[str, object]:
                requests.append(payload)
                return {
                    "lesson_id": "les-memory-source",
                    "violation_codes": ["memory.source_field"],
                    "text": "In memory_appraisals usa source_event_id, mai source_ids.",
                    "rationale": "Chiarisce il campo strutturale richiesto.",
                    "risks": [],
                }

            registry = PromptRegistry(registry_path)
            annealer = LocalPromptAnnealer(
                registry=registry,
                ledger=ledger,
                model="qwen2.5:3b",
                requester=requester,
                evidence_threshold=2,
            )

            candidate = annealer.run_once()

            self.assertIsNotNone(candidate)
            self.assertIn("memory.source_field", str(requests[0]))
            self.assertNotIn("missing source_event_id", str(requests[0]))
            self.assertEqual(candidate.version, registry.health()["candidate_version"])
            registry.observe(candidate.version, first_attempt_valid=False)
            self.assertIsNone(annealer.run_once())
            ledger.close()

    def test_no_repeated_evidence_makes_no_local_model_call(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            from tests.test_prompt_registry import write_registry
            from newland_engine.cognition.prompt_registry import PromptRegistry

            registry_path = root / "registry"
            write_registry(registry_path)
            with PromptFailureLedger(root / "learning.db") as ledger:
                annealer = LocalPromptAnnealer(
                    registry=PromptRegistry(registry_path),
                    ledger=ledger,
                    requester=lambda payload: (_ for _ in ()).throw(
                        AssertionError("local model must not be called")
                    ),
                    evidence_threshold=2,
                )

                self.assertIsNone(annealer.run_once())


if __name__ == "__main__":
    unittest.main()
