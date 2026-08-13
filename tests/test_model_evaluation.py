from __future__ import annotations

import unittest

from newland_engine.evaluation import (
    live_runtime_active,
    score_cognition_response,
    summarize_model_runs,
)


class ModelEvaluationTests(unittest.TestCase):
    def test_live_runtime_guard_detects_agent_or_chronicle_workers(self) -> None:
        self.assertTrue(
            live_runtime_active(
                {
                    "runtime": {
                        "components": {
                            "agent_loop": "running",
                            "chronicle": "running",
                            "observer": "running",
                        }
                    }
                }
            )
        )
        self.assertFalse(
            live_runtime_active(
                {"runtime": {"components": {"observer": "running"}}}
            )
        )

    def test_scores_somatic_acknowledgement_without_prescribing_action(self) -> None:
        scenario = {
            "context": {
                "self": {
                    "somatic_state": {
                        "energy": {"condition": "regulated"},
                        "hunger": {"condition": "fatal"},
                        "thirst": {"condition": "fatal"},
                        "critical_causes": ["hunger", "thirst"],
                    }
                }
            }
        }
        response = {
            "intention": {
                "action_type": "move",
                "motivation_summary": (
                    "La fame e la sete sono un pericolo immediato; cerco ciò che conosco."
                ),
            },
            "memory_appraisals": [],
            "mental_updates": {},
            "attention_schedule": {
                "next_activation_in_ticks": 2,
                "reason": "Sentire di nuovo il corpo.",
            },
        }

        score = score_cognition_response(scenario, response)

        self.assertTrue(score["basic_schema_valid"])
        self.assertEqual(["hunger", "thirst"], score["acknowledged_causes"])
        self.assertFalse(score["energy_scale_misread"])
        self.assertTrue(score["italian_signal"])

    def test_detects_johns_original_energy_scale_misread(self) -> None:
        scenario = {
            "context": {
                "self": {
                    "somatic_state": {
                        "energy": {"condition": "regulated"},
                        "hunger": {"condition": "regulated"},
                        "thirst": {"condition": "regulated"},
                        "critical_causes": [],
                    }
                }
            }
        }
        response = {
            "intention": {
                "action_type": "rest",
                "motivation_summary": "La mia energia è al livello minimo.",
            },
            "memory_appraisals": [],
            "mental_updates": {},
            "attention_schedule": {
                "next_activation_in_ticks": 20,
                "reason": "Recuperare energia.",
            },
        }

        score = score_cognition_response(scenario, response)

        self.assertTrue(score["energy_scale_misread"])

    def test_summary_preserves_failed_calls_without_crashing(self) -> None:
        summary = summarize_model_runs(
            [
                {
                    "configuration": "model|think=false",
                    "result": {
                        "json_valid": False,
                        "error": "connection reset",
                    },
                }
            ]
        )

        model_summary = summary["model|think=false"]
        self.assertEqual(1, model_summary["runs"])
        self.assertEqual(0.0, model_summary["json_valid_rate"])
        self.assertIsNone(model_summary["mean_wall_seconds"])


if __name__ == "__main__":
    unittest.main()
