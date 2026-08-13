from __future__ import annotations

import json
import unittest
from io import BytesIO
from urllib.error import HTTPError

from newland_engine.cloud_evaluation import (
    MODEL_POLICIES,
    CloudEvaluationConfigurationError,
    CloudQuotaExhausted,
    DashScopeEvaluationCognition,
)
from newland_engine.cognition import CognitionContext
from newland_engine.models import AgentMind, MaterialAgentState


API_KEY = "test-secret-that-must-never-appear"
BASE_URL = (
    "https://workspace.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"
)


def cognition_context() -> CognitionContext:
    return CognitionContext(
        mind=AgentMind(
            agent_id="nwl-benchmark",
            name="Benchmark Newlander",
            values=["autonomia"],
            temperament=["vigile"],
        ),
        material_state=MaterialAgentState(
            agent_id="nwl-benchmark",
            name="Benchmark Newlander",
            location="cittadina_iniziale",
            native_language="it",
            language_proficiencies={"it": 1.0},
        ),
        observations=(),
        nearby_agents=(),
        activation_reason="benchmark offline sanitizzato",
    )


def valid_response(*, total_tokens: int = 83) -> dict[str, object]:
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
            "motivation_summary": "Ascolto il corpo prima di scegliere altro.",
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
    return {
        "id": "completion-test",
        "choices": [
            {
                "message": {
                    "content": json.dumps(content),
                    "reasoning_content": "private reasoning must be discarded",
                }
            }
        ],
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 33,
            "total_tokens": total_tokens,
            "completion_tokens_details": {"reasoning_tokens": 12},
        },
    }


class CloudEvaluationTests(unittest.TestCase):
    def test_model_caps_match_the_accepted_adr(self) -> None:
        self.assertEqual(250_000, MODEL_POLICIES["qwen-flash-character"].token_cap)
        self.assertEqual(200_000, MODEL_POLICIES["qwen-plus-character"].token_cap)
        self.assertEqual(200_000, MODEL_POLICIES["qwen3-32b"].token_cap)
        self.assertEqual(
            100_000,
            MODEL_POLICIES["qwen3-next-80b-a3b-thinking"].token_cap,
        )
        self.assertEqual(
            75_000,
            MODEL_POLICIES["qwen3-235b-a22b-thinking-2507"].token_cap,
        )

    def test_cloud_requires_both_explicit_opt_in_and_api_key(self) -> None:
        for allow_cloud, api_key in ((False, API_KEY), (True, "")):
            with self.subTest(allow_cloud=allow_cloud, api_key=bool(api_key)):
                with self.assertRaises(CloudEvaluationConfigurationError):
                    DashScopeEvaluationCognition(
                        model="qwen-flash-character",
                        api_key=api_key,
                        base_url=BASE_URL,
                        allow_cloud=allow_cloud,
                    )

    def test_api_key_cannot_be_sent_outside_alibaba_https(self) -> None:
        for base_url in (
            "http://workspace.ap-southeast-1.maas.aliyuncs.com/v1",
            "https://attacker.example/v1",
            "",
        ):
            with self.subTest(base_url=base_url):
                with self.assertRaises(CloudEvaluationConfigurationError):
                    DashScopeEvaluationCognition(
                        model="qwen-flash-character",
                        api_key=API_KEY,
                        base_url=base_url,
                        allow_cloud=True,
                    )

    def test_non_positive_local_cap_is_rejected(self) -> None:
        with self.assertRaises(CloudEvaluationConfigurationError):
            DashScopeEvaluationCognition(
                model="qwen-flash-character",
                api_key=API_KEY,
                base_url=BASE_URL,
                allow_cloud=True,
                token_cap=0,
            )

    def test_large_models_are_limited_to_disagreement_cases(self) -> None:
        with self.assertRaises(CloudEvaluationConfigurationError):
            DashScopeEvaluationCognition(
                model="qwen3-235b-a22b-thinking-2507",
                api_key=API_KEY,
                base_url=BASE_URL,
                allow_cloud=True,
            )

    def test_final_result_uses_canonical_parser_and_discards_reasoning(self) -> None:
        client = DashScopeEvaluationCognition(
            model="qwen-flash-character",
            api_key=API_KEY,
            base_url=BASE_URL,
            allow_cloud=True,
            requester=lambda request, timeout: valid_response(),
        )

        result = client.decide(cognition_context())

        self.assertEqual("rest", result.intention.action_type)
        self.assertEqual("dashscope-evaluation", result.provider)
        self.assertEqual(83, client.usage.total_tokens)
        self.assertEqual(12, client.usage.reasoning_tokens)
        persisted = json.dumps(client.report_metrics())
        self.assertEqual(12, client.report_metrics()["reasoning_tokens"])
        self.assertNotIn("private reasoning must be discarded", persisted)

    def test_character_payload_uses_json_mode_and_embeds_canonical_schema(self) -> None:
        captured: dict[str, object] = {}

        def requester(request: object, timeout: float) -> dict[str, object]:
            captured.update(json.loads(request.data.decode("utf-8")))
            return valid_response()

        client = DashScopeEvaluationCognition(
            model="qwen-flash-character",
            api_key=API_KEY,
            base_url=BASE_URL,
            allow_cloud=True,
            requester=requester,
        )

        client.decide(cognition_context())

        self.assertEqual({"type": "json_object"}, captured["response_format"])
        system_prompt = captured["messages"][0]["content"]
        self.assertIn("JSON Schema vincolante", system_prompt)
        self.assertIn('"attention_schedule"', system_prompt)

    def test_secret_is_redacted_from_transport_failures(self) -> None:
        def fail(request: object, timeout: float) -> dict[str, object]:
            raise OSError(f"transport failed for bearer {API_KEY}")

        client = DashScopeEvaluationCognition(
            model="qwen-flash-character",
            api_key=API_KEY,
            base_url=BASE_URL,
            allow_cloud=True,
            requester=fail,
            max_attempts=1,
        )

        with self.assertRaisesRegex(RuntimeError, r"\[REDACTED\]") as raised:
            client.decide(cognition_context())
        self.assertNotIn(API_KEY, str(raised.exception))

    def test_malformed_nested_shape_gets_one_generative_repair(self) -> None:
        requests: list[dict[str, object]] = []
        responses = [
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "intention": "rest",
                                    "memory_appraisals": [],
                                    "mental_updates": {},
                                    "attention_schedule": {},
                                }
                            )
                        }
                    }
                ],
                "usage": {"total_tokens": 20},
            },
            valid_response(total_tokens=83),
        ]

        def requester(request: object, timeout: float) -> dict[str, object]:
            requests.append(json.loads(request.data.decode("utf-8")))
            return responses.pop(0)

        client = DashScopeEvaluationCognition(
            model="qwen-flash-character",
            api_key=API_KEY,
            base_url=BASE_URL,
            allow_cloud=True,
            requester=requester,
        )

        result = client.decide(cognition_context())

        self.assertEqual(2, result.attempts)
        self.assertEqual(103, client.usage.total_tokens)
        repair = requests[1]["messages"][-1]["content"]
        self.assertIn("'str' object has no attribute 'get'", repair)

    def test_free_tier_403_is_terminal_and_not_retried(self) -> None:
        calls = 0

        def quota_exhausted(request: object, timeout: float) -> dict[str, object]:
            nonlocal calls
            calls += 1
            body = json.dumps(
                {
                    "code": "AllocationQuota.FreeTierOnly",
                    "message": "Free quota exhausted",
                }
            ).encode()
            raise HTTPError(
                url="https://workspace.example",
                code=403,
                msg="Forbidden",
                hdrs=None,
                fp=BytesIO(body),
            )

        client = DashScopeEvaluationCognition(
            model="qwen-flash-character",
            api_key=API_KEY,
            base_url=BASE_URL,
            allow_cloud=True,
            requester=quota_exhausted,
            max_attempts=3,
        )

        with self.assertRaises(CloudQuotaExhausted):
            client.decide(cognition_context())
        self.assertEqual(1, calls)

    def test_local_budget_stops_before_opening_a_connection(self) -> None:
        called = False

        def requester(request: object, timeout: float) -> dict[str, object]:
            nonlocal called
            called = True
            return valid_response()

        client = DashScopeEvaluationCognition(
            model="qwen-flash-character",
            api_key=API_KEY,
            base_url=BASE_URL,
            allow_cloud=True,
            requester=requester,
            token_cap=10,
            max_output_tokens=8,
        )

        with self.assertRaises(CloudQuotaExhausted):
            client.decide(cognition_context())
        self.assertFalse(called)


if __name__ == "__main__":
    unittest.main()
