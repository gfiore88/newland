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

    def test_local_resource_action_is_perceptible_without_private_intention(
        self,
    ) -> None:
        gathered = EventEnvelope(
            event_type="ResourceGathered",
            world_tick=4,
            world_time=world_time_for_tick(4),
            actor_ids=("nwl-001",),
            location="forest",
            payload={"resource_id": "berries", "quantity": 1.0},
            visibility="local",
            recipient_ids=("nwl-001", "nwl-002"),
        )
        perceived = self.service.perceive("nwl-002", [gathered])
        self.assertEqual([gathered], [item.event for item in perceived])
        self.assertEqual([], self.service.perceive("nwl-003", [gathered]))

    def test_foreign_speech_preserves_language_without_runtime_translation(
        self,
    ) -> None:
        speech = EventEnvelope(
            event_type="SpeechUttered",
            world_tick=5,
            world_time=world_time_for_tick(5),
            actor_ids=("nwl-002",),
            location="village",
            payload={
                "target_id": "nwl-001",
                "content": "أنا هنا معك.",
                "language": "ar",
            },
            visibility="local",
            recipient_ids=("nwl-001", "nwl-002"),
        )
        perceived = self.service.perceive("nwl-001", [speech])[0].event
        self.assertEqual("ar", perceived.payload["language"])
        self.assertEqual("أنا هنا معك.", perceived.payload["content"])
        self.assertNotIn("translation", perceived.payload)


if __name__ == "__main__":
    unittest.main()
