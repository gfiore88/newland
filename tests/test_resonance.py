from __future__ import annotations

import unittest

from newland_engine.models import (
    EventEnvelope,
    Intention,
    MaterialAgentState,
    ResonanceNode,
    WorldState,
    world_time_for_tick,
)
from newland_engine.perception import PerceptionService
from newland_engine.world import WorldAdjudicator, replay


class ResonanceMechanicsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = WorldState(
            locations={"village": {"spring"}, "spring": {"village"}},
            agents={
                "nwl-001": MaterialAgentState("nwl-001", "Elia", "village"),
                "nwl-002": MaterialAgentState("nwl-002", "Amina", "village"),
            },
            resonance_nodes={
                "spring_echo": ResonanceNode(
                    "spring_echo", "subtle spring echo", "spring", 0.72
                )
            },
        )
        self.adjudicator = WorldAdjudicator()

    def test_arrival_at_node_emits_only_private_physical_signal(self) -> None:
        events = self.adjudicator.adjudicate(
            self.state,
            "nwl-001",
            Intention(action_type="move", destination="spring"),
            tick=1,
        )
        movement = next(event for event in events if event.event_type == "AgentMoved")
        signal = next(
            event for event in events if event.event_type == "ResonanceSignalReceived"
        )

        self.assertEqual("spring", movement.payload["destination"])
        self.assertEqual("private", signal.visibility)
        self.assertEqual(("nwl-001",), signal.recipient_ids)
        self.assertEqual(
            {
                "node_id": "spring_echo",
                "intensity": 0.72,
                "exposure_mode": "arrival",
            },
            signal.payload,
        )
        self.assertNotIn("flashback", signal.payload)
        self.assertNotIn("meaning", signal.payload)
        self.assertEqual([], PerceptionService().perceive("nwl-002", [signal]))

        reconstructed = replay(
            [
                EventEnvelope(
                    event_type="WorldInitialized",
                    world_tick=0,
                    world_time=world_time_for_tick(0),
                    payload={
                        "locations": {"village": ["spring"], "spring": ["village"]},
                        "resonance_nodes": {
                            "spring_echo": {
                                "label": "subtle spring echo",
                                "location": "spring",
                                "intensity": 0.72,
                            }
                        },
                    },
                ),
                EventEnvelope(
                    event_type="AgentRegistered",
                    world_tick=0,
                    world_time=world_time_for_tick(0),
                    actor_ids=("nwl-001",),
                    location="village",
                    payload={"name": "Elia", "location": "village"},
                    visibility="private",
                    recipient_ids=("nwl-001",),
                ),
                *events,
            ]
        )
        self.assertEqual("spring", reconstructed.agents["nwl-001"].location)
        self.assertEqual(0.72, reconstructed.resonance_nodes["spring_echo"].intensity)

    def test_attunement_is_chosen_action_and_signal_has_no_authored_content(
        self,
    ) -> None:
        self.state.agents["nwl-001"].location = "spring"
        events = self.adjudicator.adjudicate(
            self.state,
            "nwl-001",
            Intention(
                action_type="attune_resonance",
                node_id="spring_echo",
                duration_minutes=20,
                motivation_summary="Restare in ascolto senza presumere un significato.",
            ),
            tick=1,
            cognition={"provider": "test-double", "inference_id": "generated"},
        )

        self.assertEqual(
            [
                "ActionProposed",
                "ActionAccepted",
                "ResonanceAttunementPerformed",
                "ResonanceSignalReceived",
            ],
            [event.event_type for event in events],
        )
        self.assertEqual("generated", events[0].payload["cognition"]["inference_id"])
        self.assertEqual(
            {"node_id", "intensity", "exposure_mode"}, set(events[-1].payload)
        )

    def test_attunement_rejects_remote_or_invented_node(self) -> None:
        remote = self.adjudicator.adjudicate(
            self.state,
            "nwl-001",
            Intention(action_type="attune_resonance", node_id="spring_echo"),
            tick=1,
        )
        invented = self.adjudicator.adjudicate(
            self.state,
            "nwl-001",
            Intention(action_type="attune_resonance", node_id="invented_node"),
            tick=1,
        )

        self.assertEqual("ActionRejected", remote[-1].event_type)
        self.assertEqual("ActionRejected", invented[-1].event_type)


if __name__ == "__main__":
    unittest.main()
