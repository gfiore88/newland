from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

from helpers import ScriptedTestCognition
from newland_engine.chronicle import ChronicleContext, ChronicleEntry
from newland_engine.live import LiveSupervisor
from newland_engine.simulation import NewlandSimulation


def valid_dashscope_response() -> dict[str, object]:
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
            "motivation_summary": "Decisione autonoma del provider cloud.",
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
            "reason": "Riconsiderare autonomamente la situazione.",
        },
    }
    return {
        "choices": [{"message": {"content": json.dumps(content)}}],
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 30,
            "total_tokens": 80,
        },
    }


class GeneratedTestChronicler:
    def narrate(self, context: ChronicleContext) -> ChronicleEntry:
        first = context.events[0]
        last = context.events[-1]
        assert first.sequence is not None
        assert last.sequence is not None
        return ChronicleEntry(
            from_sequence=first.sequence,
            through_sequence=last.sequence,
            world_tick=last.world_tick,
            world_time=last.world_time,
            title="Voce generata dal test",
            prose="Il test double ha prodotto questa voce dai soli eventi ricevuti.",
            source_event_ids=tuple(event.event_id for event in context.events),
            provider="test-double",
            model="generated-test-chronicler",
            inference_id="live-test-inference",
            attempts=1,
        )


class LiveSupervisorTests(unittest.TestCase):
    def test_supervises_agent_chronicle_observer_and_static_ui(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            static_directory = root / "dist"
            static_directory.mkdir()
            (static_directory / "index.html").write_text(
                "<!doctype html><title>Newland live</title>", encoding="utf-8"
            )
            activation = threading.Event()
            supervisor = LiveSupervisor(
                root / "newland.db",
                static_directory=static_directory,
                port=0,
                poll_interval=0.01,
                cognition=ScriptedTestCognition(),
                chronicler=GeneratedTestChronicler(),
                emit=lambda events: activation.set(),
            )
            from helpers import TEST_FIXTURE_PROFILES
            with NewlandSimulation(
                root / "newland.db", cognition=ScriptedTestCognition()
            ) as sim:
                sim.admit_arrivals(TEST_FIXTURE_PROFILES)
            try:
                supervisor.start()
                self.assertTrue(activation.wait(timeout=2))
                address = supervisor.address
                assert address is not None
                with urllib.request.urlopen(
                    f"http://{address[0]}:{address[1]}/api/health"
                ) as response:
                    health = json.loads(response.read().decode("utf-8"))
                self.assertEqual("running", health["runtime"]["components"]["agent_loop"])
                self.assertGreaterEqual(
                    health["runtime"]["successful_activations"], 1
                )
                self.assertGreaterEqual(
                    health["runtime"]["inference"]["completed_agent_jobs"], 1
                )
                with urllib.request.urlopen(
                    f"http://{address[0]}:{address[1]}/"
                ) as response:
                    self.assertIn("Newland live", response.read().decode("utf-8"))
            finally:
                supervisor.shutdown()
            self.assertEqual("stopped", supervisor.health()["components"]["agent_loop"])

    def test_requires_a_built_webgl_interface(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "WebGL build not found"):
                LiveSupervisor(
                    Path(directory) / "newland.db",
                    static_directory=Path(directory) / "missing",
                    cognition=ScriptedTestCognition(),
                    chronicler=GeneratedTestChronicler(),
                )

    def test_finite_canary_stops_after_one_complete_activation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            static_directory = root / "dist"
            static_directory.mkdir()
            (static_directory / "index.html").write_text(
                "<!doctype html><title>Newland live</title>", encoding="utf-8"
            )
            from helpers import TEST_FIXTURE_PROFILES

            with NewlandSimulation(
                root / "newland.db", cognition=ScriptedTestCognition()
            ) as simulation:
                simulation.admit_arrivals(TEST_FIXTURE_PROFILES[:1])
            supervisor = LiveSupervisor(
                root / "newland.db",
                static_directory=static_directory,
                port=0,
                poll_interval=0.01,
                max_activations=1,
                cognition=ScriptedTestCognition(),
                chronicler=GeneratedTestChronicler(),
            )

            supervisor.start()
            supervisor.wait()
            supervisor.shutdown()

            self.assertEqual(1, supervisor.health()["successful_activations"])

    def test_dashscope_canary_is_canonical_and_visible_in_http_health(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            static_directory = root / "dist"
            static_directory.mkdir()
            (static_directory / "index.html").write_text(
                "<!doctype html><title>Newland live</title>", encoding="utf-8"
            )
            from helpers import TEST_FIXTURE_PROFILES

            database = root / "newland.db"
            with NewlandSimulation(
                database, cognition=ScriptedTestCognition()
            ) as simulation:
                simulation.admit_arrivals(TEST_FIXTURE_PROFILES[:1])
            from tests.test_prompt_registry import write_registry

            prompt_registry_path = root / "prompt-registry"
            write_registry(prompt_registry_path)
            supervisor = LiveSupervisor(
                database,
                static_directory=static_directory,
                port=0,
                poll_interval=0.01,
                models=("dashscope:qwen-flash-character",),
                reflective_models=("dashscope:qwen-flash-character",),
                allow_cloud_live=True,
                dashscope_api_key="test-key",
                dashscope_base_url=(
                    "https://workspace.ap-southeast-1.maas.aliyuncs.com/"
                    "compatible-mode/v1"
                ),
                cloud_token_cap=10_000,
                cloud_ledger_path=root / "cloud.db",
                prompt_registry_path=prompt_registry_path,
                max_activations=1,
                dashscope_requester=(
                    lambda request, timeout: valid_dashscope_response()
                ),
                chronicler=GeneratedTestChronicler(),
            )
            try:
                supervisor.start()
                supervisor.wait()
                address = supervisor.address
                assert address is not None
                with urllib.request.urlopen(
                    f"http://{address[0]}:{address[1]}/api/health"
                ) as response:
                    health = json.loads(response.read().decode("utf-8"))
            finally:
                supervisor.shutdown()

            self.assertEqual(
                80,
                health["runtime"]["cloud_cognition"]["cloud_budget"][
                    "consumed_tokens"
                ],
            )
            self.assertEqual(
                ["qwen2.5:3b"],
                health["runtime"]["configured_models"]["chronicle"],
            )
            with NewlandSimulation(
                database, cognition=ScriptedTestCognition()
            ) as simulation:
                proposals = [
                    event
                    for event in simulation.store.events()
                    if event.event_type == "ActionProposed"
                ]
            self.assertEqual(
                "dashscope", proposals[-1].payload["cognition"]["provider"]
            )
            self.assertEqual(
                "agent-cognition-v4",
                proposals[-1].payload["cognition"]["prompt_version"],
            )
            self.assertEqual(
                64, len(proposals[-1].payload["cognition"]["prompt_hash"])
            )
            self.assertEqual(
                64, len(proposals[-1].payload["cognition"]["schema_hash"])
            )
            self.assertEqual(
                "healthy",
                health["runtime"]["cloud_cognition"]["prompt_registry"]["status"],
            )


if __name__ == "__main__":
    unittest.main()
