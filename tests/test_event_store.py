from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from newland_engine.event_store import EventStore
from newland_engine.models import AgentMind, EventEnvelope, world_time_for_tick


class EventStoreTests(unittest.TestCase):
    def test_events_and_minds_survive_reopen(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "newland.db"
            original = EventEnvelope(
                event_type="WorldInitialized",
                world_tick=0,
                world_time=world_time_for_tick(0),
                payload={"locations": {"village": []}},
            )
            mind = AgentMind(
                agent_id="nwl-test",
                name="Test Newlander",
                values=["cura"],
                temperament=["quieto"],
            )
            with EventStore(path) as store:
                persisted = store.append(original)
                mind.last_perceived_sequence = persisted.sequence or 0
                store.save_mind(mind)

            with EventStore(path) as reopened:
                events = reopened.events()
                minds = reopened.load_minds()

            self.assertEqual(1, len(events))
            self.assertEqual(original.event_id, events[0].event_id)
            self.assertEqual(1, events[0].sequence)
            self.assertEqual("Test Newlander", minds["nwl-test"].name)
            self.assertEqual(1, minds["nwl-test"].last_perceived_sequence)

    def test_private_event_requires_recipient(self) -> None:
        with self.assertRaises(ValueError):
            EventEnvelope(
                event_type="PrivateThoughtRecorded",
                world_tick=1,
                world_time=world_time_for_tick(1),
                visibility="private",
            )

    def test_activation_events_and_mind_snapshot_rollback_together(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "newland.db"
            existing = EventEnvelope(
                event_type="WorldInitialized",
                world_tick=0,
                world_time=world_time_for_tick(0),
            )
            valid = EventEnvelope(
                event_type="ActionProposed",
                world_tick=1,
                world_time=world_time_for_tick(1),
                visibility="private",
                recipient_ids=("nwl-test",),
            )
            mind = AgentMind(
                agent_id="nwl-test",
                name="Test Newlander",
                values=["cura"],
                temperament=["quieto"],
            )
            with EventStore(path) as store:
                store.append(existing)
                with self.assertRaises(sqlite3.IntegrityError):
                    store.append_many_with_mind([valid, existing], mind)
                self.assertEqual(1, store.event_count())
                self.assertEqual({}, store.load_minds())

    def test_multi_mind_transition_rolls_back_as_one_unit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "newland.db"
            duplicate = EventEnvelope(
                event_type="AgentArrived",
                world_tick=1,
                world_time=world_time_for_tick(1),
                event_id="duplicate-arrival",
            )
            minds = (
                AgentMind("nwl-a", "A", ["cura"], ["vigile"]),
                AgentMind("nwl-b", "B", ["cura"], ["vigile"]),
            )
            with EventStore(path) as store:
                with self.assertRaises(sqlite3.IntegrityError):
                    store.append_many_with_minds([duplicate, duplicate], minds)
                self.assertEqual(0, store.event_count())
                self.assertEqual({}, store.load_minds())


if __name__ == "__main__":
    unittest.main()
