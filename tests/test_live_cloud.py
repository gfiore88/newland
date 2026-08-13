from __future__ import annotations

import json
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError

from newland_engine.cognition.cloud_budget import (
    CloudBudgetExceeded,
    CloudUsageLedger,
)
from newland_engine.cognition.dashscope_adapter import DashScopeCognition
from newland_engine.cognition.configuration import (
    LiveCloudConfigurationError,
    ModelSpec,
    validate_live_model_specs,
)
from newland_engine.cognition.runtime import build_configured_cognition
from newland_engine.cognition import (
    AttentionSchedule,
    CognitionContext,
    CognitionResult,
    CognitionUnavailable,
    GenerativeCognitionPool,
    MentalUpdates,
)
from newland_engine.models import AgentMind, Intention, MaterialAgentState


ALIBABA_ENDPOINT = (
    "https://workspace.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"
)
API_KEY = "test-secret-that-must-never-appear"


def cognition_context() -> CognitionContext:
    return CognitionContext(
        mind=AgentMind(
            agent_id="nwl-live-cloud",
            name="Live Cloud Newlander",
            values=["autonomia"],
            temperament=["vigile"],
        ),
        material_state=MaterialAgentState(
            agent_id="nwl-live-cloud",
            name="Live Cloud Newlander",
            location="cittadina_iniziale",
            native_language="it",
            language_proficiencies={"it": 1.0},
        ),
        observations=(),
        nearby_agents=(),
        activation_reason="test live cloud",
    )


def valid_response(*, include_usage: bool = True) -> dict[str, object]:
    content = {
        "intention": {
            "action_type": "rest",
            "target_id": None,
            "destination": None,
            "duration_minutes": 10,
            "spoken_content": None,
            "language": None,
            "resource_id": None,
            "quantity": None,
            "activity_id": None,
            "proposal_id": None,
            "dispute_id": None,
            "subject_event_id": None,
            "response": None,
            "node_id": None,
            "motivation_summary": "Scelgo autonomamente di ascoltare il corpo.",
            "confidence": 0.7,
        },
        "memory_appraisals": [],
        "mental_updates": {
            "beliefs": [],
            "relationships": [],
            "affect": None,
            "reflections": [],
            "goals": [],
            "plans": [],
            "commitments": [],
            "role_interpretations": [],
            "anamnesis_fragments": [],
            "resonance_orientation": None,
        },
        "attention_schedule": {
            "next_activation_in_ticks": 3,
            "reason": "Riascoltare il corpo.",
        },
    }
    response: dict[str, object] = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(content),
                    "reasoning_content": "never persist this private reasoning",
                }
            }
        ]
    }
    if include_usage:
        response["usage"] = {
            "prompt_tokens": 50,
            "completion_tokens": 33,
            "total_tokens": 83,
            "completion_tokens_details": {"reasoning_tokens": 12},
        }
    return response


class LiveModelConfigurationTests(unittest.TestCase):
    def test_model_specs_preserve_bare_ollama_tags_and_accept_qualified_models(
        self,
    ) -> None:
        self.assertEqual(
            ModelSpec("ollama", "qwen2.5:3b"),
            ModelSpec.parse("qwen2.5:3b"),
        )
        self.assertEqual(
            ModelSpec("ollama", "qwen2.5:7b"),
            ModelSpec.parse("ollama:qwen2.5:7b"),
        )
        self.assertEqual(
            ModelSpec("dashscope", "qwen-flash-character"),
            ModelSpec.parse("dashscope:qwen-flash-character"),
        )

    def test_cloud_specs_require_all_live_gates(self) -> None:
        ordinary = (ModelSpec.parse("dashscope:qwen-flash-character"),)
        valid = {
            "ordinary": ordinary,
            "reflective": ordinary,
            "allow_cloud_live": True,
            "api_key": "test-key",
            "base_url": ALIBABA_ENDPOINT,
            "cloud_token_cap": 100_000,
        }
        for missing, replacement in (
            ("allow_cloud_live", False),
            ("api_key", ""),
            ("base_url", ""),
            ("cloud_token_cap", None),
        ):
            values = {**valid, missing: replacement}
            with self.subTest(missing=missing):
                with self.assertRaises(LiveCloudConfigurationError):
                    validate_live_model_specs(**values)

    def test_ollama_only_specs_do_not_require_cloud_configuration(self) -> None:
        validate_live_model_specs(
            ordinary=(ModelSpec.parse("qwen2.5:3b"),),
            reflective=(ModelSpec.parse("ollama:qwen2.5:7b"),),
            allow_cloud_live=False,
            api_key="",
            base_url="",
            cloud_token_cap=None,
        )

    def test_expensive_models_are_refused_and_medium_models_are_reflective_only(
        self,
    ) -> None:
        for model in (
            "qwen3-next-80b-a3b-thinking",
            "qwen3-235b-a22b-thinking-2507",
        ):
            with self.subTest(model=model):
                with self.assertRaises(LiveCloudConfigurationError):
                    validate_live_model_specs(
                        ordinary=(ModelSpec("dashscope", model),),
                        reflective=(ModelSpec("dashscope", model),),
                        allow_cloud_live=True,
                        api_key="test-key",
                        base_url=ALIBABA_ENDPOINT,
                        cloud_token_cap=50_000,
                    )

        for model in ("qwen-plus-character", "qwen3-32b"):
            with self.subTest(model=model):
                with self.assertRaises(LiveCloudConfigurationError):
                    validate_live_model_specs(
                        ordinary=(ModelSpec("dashscope", model),),
                        reflective=(ModelSpec("dashscope", model),),
                        allow_cloud_live=True,
                        api_key="test-key",
                        base_url=ALIBABA_ENDPOINT,
                        cloud_token_cap=50_000,
                    )

    def test_cloud_cap_cannot_exceed_the_smallest_selected_model_policy(self) -> None:
        with self.assertRaises(LiveCloudConfigurationError):
            validate_live_model_specs(
                ordinary=(ModelSpec.parse("dashscope:qwen-flash-character"),),
                reflective=(ModelSpec.parse("dashscope:qwen-plus-character"),),
                allow_cloud_live=True,
                api_key="test-key",
                base_url=ALIBABA_ENDPOINT,
                cloud_token_cap=200_001,
            )


class CloudUsageLedgerTests(unittest.TestCase):
    def test_consumption_survives_restart_and_reduces_remaining_budget(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runtime.db"
            with CloudUsageLedger(path, global_cap=100) as first:
                reservation = first.reserve(
                    provider="dashscope",
                    model="qwen-flash-character",
                    estimated_input_tokens=20,
                    max_output_tokens=30,
                    model_cap=100,
                )
                first.settle(
                    reservation,
                    prompt_tokens=15,
                    completion_tokens=10,
                    reasoning_tokens=0,
                    total_tokens=25,
                )

            with CloudUsageLedger(path, global_cap=100) as reopened:
                snapshot = reopened.snapshot()
                self.assertEqual(25, snapshot.consumed_tokens)
                self.assertEqual(75, snapshot.remaining_tokens)
                with self.assertRaises(CloudBudgetExceeded):
                    reopened.reserve(
                        provider="dashscope",
                        model="qwen-flash-character",
                        estimated_input_tokens=46,
                        max_output_tokens=30,
                        model_cap=100,
                    )

    def test_interrupted_reservation_is_charged_conservatively_after_restart(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runtime.db"
            with CloudUsageLedger(path, global_cap=100) as first:
                first.reserve(
                    provider="dashscope",
                    model="qwen-flash-character",
                    estimated_input_tokens=20,
                    max_output_tokens=30,
                    model_cap=100,
                )

            with CloudUsageLedger(path, global_cap=100) as reopened:
                snapshot = reopened.snapshot()
                self.assertEqual(50, snapshot.consumed_tokens)
                self.assertEqual(0, snapshot.reserved_tokens)
                self.assertEqual(1, snapshot.interrupted_reservations)

    def test_missing_provider_usage_charges_the_full_reservation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with CloudUsageLedger(
                Path(directory) / "runtime.db", global_cap=100
            ) as ledger:
                reservation = ledger.reserve(
                    provider="dashscope",
                    model="qwen-flash-character",
                    estimated_input_tokens=20,
                    max_output_tokens=30,
                    model_cap=100,
                )
                ledger.settle(
                    reservation,
                    prompt_tokens=0,
                    completion_tokens=0,
                    reasoning_tokens=0,
                    total_tokens=None,
                )

                snapshot = ledger.snapshot()
                self.assertEqual(50, snapshot.consumed_tokens)
                self.assertEqual(0, snapshot.reserved_tokens)


class DashScopeLiveCognitionTests(unittest.TestCase):
    def test_valid_cloud_result_has_canonical_live_provenance_and_usage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with CloudUsageLedger(
                Path(directory) / "runtime.db", global_cap=20_000
            ) as ledger:
                provider = DashScopeCognition(
                    model="qwen-flash-character",
                    api_key=API_KEY,
                    base_url=ALIBABA_ENDPOINT,
                    ledger=ledger,
                    model_token_cap=20_000,
                    requester=lambda request, timeout: valid_response(),
                )

                result = provider.decide(cognition_context())

                self.assertEqual("dashscope", result.provider)
                self.assertEqual("qwen-flash-character", result.model)
                self.assertEqual("rest", result.intention.action_type)
                self.assertEqual(83, ledger.snapshot().consumed_tokens)
                health = json.dumps(provider.health())
                self.assertNotIn("never persist this private reasoning", health)
                self.assertNotIn(API_KEY, health)

    def test_missing_usage_charges_full_request_reservation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with CloudUsageLedger(
                Path(directory) / "runtime.db", global_cap=20_000
            ) as ledger:
                provider = DashScopeCognition(
                    model="qwen-flash-character",
                    api_key=API_KEY,
                    base_url=ALIBABA_ENDPOINT,
                    ledger=ledger,
                    model_token_cap=20_000,
                    max_output_tokens=128,
                    requester=lambda request, timeout: valid_response(
                        include_usage=False
                    ),
                )

                provider.decide(cognition_context())

                self.assertGreater(ledger.snapshot().consumed_tokens, 128)

    def test_free_tier_403_is_terminal_for_cloud_family_without_retry(self) -> None:
        calls = 0

        def quota_exhausted(request: object, timeout: float) -> dict[str, object]:
            nonlocal calls
            calls += 1
            body = json.dumps(
                {
                    "code": "AllocationQuota.FreeTierOnly",
                    "message": f"quota stopped for {API_KEY}",
                }
            ).encode()
            raise HTTPError(
                url=ALIBABA_ENDPOINT,
                code=403,
                msg="Forbidden",
                hdrs=None,
                fp=BytesIO(body),
            )

        with tempfile.TemporaryDirectory() as directory:
            with CloudUsageLedger(
                Path(directory) / "runtime.db", global_cap=20_000
            ) as ledger:
                provider = DashScopeCognition(
                    model="qwen-flash-character",
                    api_key=API_KEY,
                    base_url=ALIBABA_ENDPOINT,
                    ledger=ledger,
                    model_token_cap=20_000,
                    requester=quota_exhausted,
                )

                with self.assertRaises(CognitionUnavailable) as raised:
                    provider.decide(cognition_context())

                self.assertEqual("dashscope", raised.exception.stop_provider_family)
                self.assertEqual(1, calls)
                self.assertNotIn(API_KEY, str(raised.exception.failures))
                self.assertGreater(ledger.snapshot().consumed_tokens, 0)

    def test_circuit_opens_after_consecutive_transport_failures(self) -> None:
        calls = 0

        def unavailable(request: object, timeout: float) -> dict[str, object]:
            nonlocal calls
            calls += 1
            raise OSError("network unavailable")

        with tempfile.TemporaryDirectory() as directory:
            with CloudUsageLedger(
                Path(directory) / "runtime.db", global_cap=20_000
            ) as ledger:
                provider = DashScopeCognition(
                    model="qwen-flash-character",
                    api_key=API_KEY,
                    base_url=ALIBABA_ENDPOINT,
                    ledger=ledger,
                    model_token_cap=20_000,
                    requester=unavailable,
                    max_attempts=1,
                    circuit_failure_threshold=2,
                    circuit_cooldown_seconds=60,
                    clock=lambda: 10.0,
                )
                for _ in range(3):
                    with self.assertRaises(CognitionUnavailable):
                        provider.decide(cognition_context())

                self.assertEqual(2, calls)
                self.assertEqual("open", provider.health()["circuit_state"])

    def test_terminal_cloud_failure_skips_other_cloud_and_uses_local_generator(
        self,
    ) -> None:
        class TerminalCloud:
            provider_family = "dashscope"

            def decide(self, context: CognitionContext) -> CognitionResult:
                raise CognitionUnavailable(
                    [{"model": "cloud-primary", "error": "quota"}],
                    stop_provider_family="dashscope",
                )

        class ForbiddenCloud:
            provider_family = "dashscope"

            def decide(self, context: CognitionContext) -> CognitionResult:
                raise AssertionError("second cloud provider must be skipped")

        class LocalGenerator:
            provider_family = "ollama"

            def decide(self, context: CognitionContext) -> CognitionResult:
                return CognitionResult(
                    intention=Intention(
                        action_type="rest",
                        motivation_summary="Decisione generata localmente.",
                    ),
                    memory_appraisals=(),
                    mental_updates=MentalUpdates(),
                    attention_schedule=AttentionSchedule(
                        3, "Riconsiderare la situazione."
                    ),
                    provider="ollama",
                    model="local-generator",
                    inference_id="local-inference",
                    attempts=1,
                )

        result = GenerativeCognitionPool(
            [TerminalCloud(), ForbiddenCloud(), LocalGenerator()]
        ).decide(cognition_context())

        self.assertEqual("ollama", result.provider)


class ConfiguredCognitionRuntimeTests(unittest.TestCase):
    def test_factory_builds_mixed_pool_and_exposes_safe_cloud_health(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            configured = build_configured_cognition(
                ordinary_models=(
                    "dashscope:qwen-flash-character",
                    "ollama:qwen2.5:3b",
                ),
                reflective_models=("ollama:qwen2.5:7b",),
                allow_cloud_live=True,
                api_key=API_KEY,
                base_url=ALIBABA_ENDPOINT,
                cloud_token_cap=10_000,
                ledger_path=Path(directory) / "cloud.db",
                dashscope_requester=lambda request, timeout: valid_response(),
            )
            try:
                result = configured.cognition.decide(cognition_context())
                health = configured.health()
            finally:
                configured.close()
            closed_health = configured.health()

        self.assertEqual("dashscope", result.provider)
        self.assertEqual(
            ["dashscope:qwen-flash-character", "ollama:qwen2.5:3b"],
            health["configured_models"]["ordinary"],
        )
        rendered = json.dumps(health)
        self.assertNotIn(API_KEY, rendered)
        self.assertEqual(83, health["cloud_budget"]["consumed_tokens"])
        self.assertEqual(health, closed_health)

    def test_factory_rejects_missing_cloud_gate_before_creating_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger_path = Path(directory) / "cloud.db"
            with self.assertRaises(LiveCloudConfigurationError):
                build_configured_cognition(
                    ordinary_models=("dashscope:qwen-flash-character",),
                    reflective_models=(),
                    allow_cloud_live=False,
                    api_key=API_KEY,
                    base_url=ALIBABA_ENDPOINT,
                    cloud_token_cap=10_000,
                    ledger_path=ledger_path,
                )
            self.assertFalse(ledger_path.exists())


if __name__ == "__main__":
    unittest.main()
