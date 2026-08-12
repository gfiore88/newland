from __future__ import annotations

import unittest

from newland_engine.models import MaterialAgentState, WorldState
from newland_engine.physiology import PhysiologySystem
from newland_engine.world import reduce_event


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


if __name__ == "__main__":
    unittest.main()
