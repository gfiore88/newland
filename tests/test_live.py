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


if __name__ == "__main__":
    unittest.main()
