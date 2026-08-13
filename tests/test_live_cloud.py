from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from newland_engine.cognition.cloud_budget import (
    CloudBudgetExceeded,
    CloudUsageLedger,
)
from newland_engine.cognition.configuration import (
    LiveCloudConfigurationError,
    ModelSpec,
    validate_live_model_specs,
)


ALIBABA_ENDPOINT = (
    "https://workspace.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"
)


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


if __name__ == "__main__":
    unittest.main()
