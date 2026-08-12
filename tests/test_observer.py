from __future__ import annotations

import http.client
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from newland_engine.event_store import EventStore
from newland_engine.models import AgentMind, EventEnvelope, world_time_for_tick
from newland_engine.observer import ObserverReadModel, ObserverServer


class ObserverReadModelTests(unittest.TestCase):
    def test_snapshot_projects_world_and_privileged_mind_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "newland.db"
            expected_mind = self._seed(path)
            before = self._stored_state(path)

            snapshot = ObserverReadModel(path).snapshot()

            self.assertEqual(1, snapshot["schema_version"])
            self.assertEqual("architect-local-read-only", snapshot["observer_scope"])
            self.assertEqual(2, snapshot["last_sequence"])
            self.assertEqual(["spring"], snapshot["world"]["locations"]["village"])
            self.assertEqual(
                "village", snapshot["world"]["agents"]["nwl-test"]["location"]
            )
            self.assertEqual(
                expected_mind.private_state,
                snapshot["minds"]["nwl-test"]["private_state"],
            )
            self.assertEqual(before, self._stored_state(path))

    def test_event_projection_preserves_private_envelope_and_sequence_order(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "newland.db"
            self._seed(path)

            events = ObserverReadModel(path).events(after_sequence=1)

            self.assertEqual([2], [event["sequence"] for event in events])
            event = events[0]
            self.assertEqual("AgentRegistered", event["event_type"])
            self.assertEqual("private", event["visibility"])
            self.assertEqual(("nwl-test",), event["recipient_ids"])
            self.assertEqual(("nwl-test",), event["actor_ids"])

    @staticmethod
    def _seed(path: Path) -> AgentMind:
        events = [
            EventEnvelope(
                event_type="WorldInitialized",
                world_tick=0,
                world_time=world_time_for_tick(0),
                payload={
                    "name": "Newland",
                    "locations": {"village": ["spring"], "spring": ["village"]},
                    "resonance_nodes": {
                        "spring-echo": {
                            "label": "spring echo",
                            "location": "spring",
                            "intensity": 0.7,
                        }
                    },
                },
            ),
            EventEnvelope(
                event_type="AgentRegistered",
                world_tick=0,
                world_time=world_time_for_tick(0),
                actor_ids=("nwl-test",),
                location="village",
                payload={"name": "Elia", "location": "village"},
                visibility="private",
                recipient_ids=("nwl-test",),
            ),
        ]
        mind = AgentMind(
            agent_id="nwl-test",
            name="Elia",
            values=["cura"],
            temperament=["quieto"],
            private_state={"unspoken": "Non so ancora se fidarmi."},
        )
        with EventStore(path) as store:
            persisted = store.append_many(events)
            mind.last_perceived_sequence = persisted[-1].sequence or 0
            store.save_mind(mind)
        return mind

    @staticmethod
    def _stored_state(path: Path) -> tuple[list[dict[str, object]], dict[str, dict]]:
        with EventStore(path, read_only=True) as store:
            events = [
                {
                    "event_id": event.event_id,
                    "sequence": event.sequence,
                    "event_type": event.event_type,
                    "payload": event.payload,
                }
                for event in store.events()
            ]
            minds = {
                agent_id: mind.to_dict()
                for agent_id, mind in store.load_minds().items()
            }
        return events, minds


class ObserverHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "newland.db"
        ObserverReadModelTests._seed(self.database_path)
        self.server = ObserverServer(
            self.database_path,
            port=0,
            poll_interval=0.01,
        )
        self.server_thread = threading.Thread(
            target=self.server.serve_forever,
            daemon=True,
        )
        self.server_thread.start()
        self.base_url = f"http://{self.server.address.host}:{self.server.address.port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server_thread.join(timeout=2)
        self.temporary_directory.cleanup()

    def test_health_snapshot_and_events_are_read_only(self) -> None:
        before = ObserverReadModelTests._stored_state(self.database_path)

        health = self._get_json("/api/health")
        snapshot = self._get_json("/api/snapshot")
        events = self._get_json("/api/events?after_sequence=1&limit=1")

        self.assertEqual({"status": "ok", "last_sequence": 2}, health)
        self.assertEqual("Elia", snapshot["world"]["agents"]["nwl-test"]["name"])
        self.assertEqual([2], [event["sequence"] for event in events["events"]])
        self.assertEqual(
            before, ObserverReadModelTests._stored_state(self.database_path)
        )

    def test_sse_streams_ordered_canonical_events_without_writes(self) -> None:
        before = ObserverReadModelTests._stored_state(self.database_path)
        connection = http.client.HTTPConnection(
            self.server.address.host,
            self.server.address.port,
            timeout=2,
        )
        connection.request("GET", "/api/stream?after_sequence=1")
        response = connection.getresponse()

        self.assertEqual(200, response.status)
        self.assertEqual(
            "text/event-stream; charset=utf-8", response.getheader("Content-Type")
        )
        block: dict[str, str] = {}
        while True:
            line = response.fp.readline().decode("utf-8").strip()
            if not line:
                if block:
                    break
                continue
            key, value = line.split(":", 1)
            block[key] = value.strip()
        connection.close()

        self.assertEqual("2", block["id"])
        self.assertEqual("AgentRegistered", block["event"])
        self.assertEqual(2, json.loads(block["data"])["sequence"])
        self.assertEqual(
            before, ObserverReadModelTests._stored_state(self.database_path)
        )

    def test_last_event_id_resumes_stream_and_invalid_queries_are_rejected(
        self,
    ) -> None:
        connection = http.client.HTTPConnection(
            self.server.address.host,
            self.server.address.port,
            timeout=2,
        )
        connection.request(
            "GET",
            "/api/stream?after_sequence=0",
            headers={"Last-Event-ID": "1"},
        )
        response = connection.getresponse()
        first_line = response.fp.readline().decode("utf-8").strip()
        connection.close()
        self.assertEqual("id: 2", first_line)

        with self.assertRaises(urllib.error.HTTPError) as raised:
            self._get_json("/api/events?after_sequence=-1")
        self.assertEqual(400, raised.exception.code)
        raised.exception.close()

    def test_cors_allows_local_ui_but_not_external_origins(self) -> None:
        local_request = urllib.request.Request(
            f"{self.base_url}/api/health",
            headers={"Origin": "http://localhost:5173"},
        )
        with urllib.request.urlopen(local_request, timeout=2) as response:
            self.assertEqual(
                "http://localhost:5173",
                response.getheader("Access-Control-Allow-Origin"),
            )

        external_request = urllib.request.Request(
            f"{self.base_url}/api/health",
            headers={"Origin": "https://example.com"},
        )
        with urllib.request.urlopen(external_request, timeout=2) as response:
            self.assertIsNone(response.getheader("Access-Control-Allow-Origin"))

    def _get_json(self, path: str) -> dict:
        with urllib.request.urlopen(f"{self.base_url}{path}", timeout=2) as response:
            return json.load(response)


if __name__ == "__main__":
    unittest.main()
