from __future__ import annotations

import unittest

from newland_engine.models import (
    EventEnvelope,
    MaterialAgentState,
    WorldState,
    world_time_for_tick,
)
from newland_engine.physiology import PhysiologySystem
from newland_engine.world import reduce_event, replay


class PhysiologySystemTests(unittest.TestCase):
    def test_advances_body_without_selecting_an_action(self) -> None:
        state = WorldState(
            tick=0,
            agents={
                "nwl-001": MaterialAgentState(
                    "nwl-001", "Elia", "village", energy=0.8, hunger=0.1, thirst=0.1
                )
            },
        )
        advance = PhysiologySystem().advance(state, to_tick=5)

        self.assertEqual(1, len(advance.events))
        event = advance.events[0]
        self.assertEqual("NeedsChanged", event.event_type)
        self.assertNotIn("action_type", event.payload)
        self.assertAlmostEqual(0.75, event.payload["current"]["energy"])
        self.assertAlmostEqual(0.175, event.payload["current"]["hunger"])
        self.assertAlmostEqual(0.2, event.payload["current"]["thirst"])

        reduce_event(state, event)
        self.assertAlmostEqual(0.75, state.agents["nwl-001"].energy)

    def test_threshold_crossing_requests_attention_without_prescribing_response(
        self,
    ) -> None:
        state = WorldState(
            tick=0,
            agents={
                "nwl-001": MaterialAgentState(
                    "nwl-001", "Elia", "village", energy=0.26, hunger=0.74, thirst=0.74
                )
            },
        )
        advance = PhysiologySystem().advance(state, to_tick=1)

        self.assertEqual(("nwl-001",), advance.interrupted_agent_ids)
        self.assertEqual(
            ["energy_low", "hunger_high", "thirst_high"],
            advance.events[0].payload["crossed_thresholds"],
        )

    def test_no_elapsed_time_produces_no_body_event(self) -> None:
        state = WorldState(tick=3)
        advance = PhysiologySystem().advance(state, to_tick=3)
        self.assertEqual((), advance.events)

    def test_fatal_exposures_are_separate_and_replayable(self) -> None:
        registered = EventEnvelope(
            event_type="AgentRegistered",
            world_tick=0,
            world_time=world_time_for_tick(0),
            actor_ids=("nwl-001",),
            location="village",
            payload={
                "name": "Elia",
                "location": "village",
                "energy": 1.0,
                "hunger": 1.0,
                "thirst": 0.0,
            },
        )
        state = replay([registered])

        first_advance = PhysiologySystem().advance(state, to_tick=50)
        needs_changed = first_advance.events[0]
        reduce_event(state, needs_changed)

        self.assertEqual(
            {"exhaustion": 0, "starvation": 50, "dehydration": 0},
            needs_changed.payload["fatal_exposure_ticks"],
        )

        restored = replay([registered, needs_changed])
        self.assertEqual(0, restored.agents["nwl-001"].exhaustion_ticks)
        self.assertEqual(50, restored.agents["nwl-001"].starvation_ticks)
        self.assertEqual(0, restored.agents["nwl-001"].dehydration_ticks)

        second_advance = PhysiologySystem().advance(restored, to_tick=201)

        self.assertEqual("NeedsChanged", second_advance.events[0].event_type)
        self.assertEqual("AgentDied", second_advance.events[1].event_type)
        self.assertEqual(
            ["starvation"], second_advance.events[1].payload["causes"]
        )
        self.assertEqual(
            {
                "exhaustion": 101,
                "starvation": 201,
                "dehydration": 151,
            },
            second_advance.events[1].payload["fatal_exposure_ticks"],
        )

    def test_fatal_exposure_counts_only_time_after_crossing(self) -> None:
        state = WorldState(
            tick=0,
            agents={
                "nwl-001": MaterialAgentState(
                    "nwl-001",
                    "Elia",
                    "village",
                    energy=0.8,
                    hunger=0.91,
                    thirst=0.0,
                )
            },
        )

        advance = PhysiologySystem().advance(state, to_tick=10)

        self.assertEqual(
            4,
            advance.events[0].payload["fatal_exposure_ticks"]["starvation"],
        )

    def test_recovery_resets_only_the_resolved_fatal_exposure(self) -> None:
        agent = MaterialAgentState(
            "nwl-001",
            "Elia",
            "village",
            energy=0.0,
            hunger=0.5,
            thirst=1.0,
            exhaustion_ticks=20,
            starvation_ticks=100,
            dehydration_ticks=80,
        )
        state = WorldState(tick=10, agents={agent.agent_id: agent})

        advance = PhysiologySystem().advance(state, to_tick=11)

        self.assertEqual(
            {"exhaustion": 21, "starvation": 0, "dehydration": 81},
            advance.events[0].payload["fatal_exposure_ticks"],
        )


if __name__ == "__main__":
    unittest.main()
