from __future__ import annotations

import unittest

from newland_engine.models import EventEnvelope, world_time_for_tick
from newland_engine.perception import PerceptionService


class PerceptionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = PerceptionService()

    def test_private_event_is_visible_only_to_recipient(self) -> None:
        private = EventEnvelope(
            event_type="ActionRejected",
            world_tick=2,
            world_time=world_time_for_tick(2),
            actor_ids=("nwl-001",),
            payload={"reason": "azione impossibile"},
            visibility="private",
            recipient_ids=("nwl-001",),
        )
        self.assertEqual(1, len(self.service.perceive("nwl-001", [private])))
        self.assertEqual([], self.service.perceive("nwl-002", [private]))

    def test_memory_audit_event_does_not_become_recursive_perception(self) -> None:
        memory_audit = EventEnvelope(
            event_type="MemoryEncoded",
            world_tick=2,
            world_time=world_time_for_tick(2),
            actor_ids=("nwl-001",),
            payload={"summary": "un ricordo privato"},
            visibility="private",
            recipient_ids=("nwl-001",),
        )
        self.assertEqual([], self.service.perceive("nwl-001", [memory_audit]))

    def test_local_event_uses_recipients_present_at_event_time(self) -> None:
        local = EventEnvelope(
            event_type="SpeechUttered",
            world_tick=3,
            world_time=world_time_for_tick(3),
            actor_ids=("nwl-001",),
            location="village",
            payload={"target_id": "nwl-002", "content": "Ci sei?"},
            visibility="local",
            recipient_ids=("nwl-001", "nwl-002"),
        )
        self.assertEqual(1, len(self.service.perceive("nwl-002", [local])))
        self.assertEqual([], self.service.perceive("nwl-003", [local]))


if __name__ == "__main__":
    unittest.main()
