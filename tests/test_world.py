from __future__ import annotations

import unittest

from newland_engine.models import Intention, MaterialAgentState, WorldState
from newland_engine.world import WorldAdjudicator


class WorldAdjudicatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = WorldState(
            locations={"village": {"field"}, "field": {"village"}},
            agents={
                "nwl-001": MaterialAgentState("nwl-001", "Elia", "village"),
                "nwl-002": MaterialAgentState("nwl-002", "Amina", "field"),
            },
        )
        self.adjudicator = WorldAdjudicator()

    def test_rejects_speech_to_absent_target_without_material_consequence(self) -> None:
        events = self.adjudicator.adjudicate(
            self.state,
            "nwl-001",
            Intention(
                action_type="speak", target_id="nwl-002", spoken_content="Amina?"
            ),
            tick=1,
        )
        self.assertEqual(
            ["ActionProposed", "ActionRejected"], [event.event_type for event in events]
        )
        self.assertNotIn("SpeechUttered", [event.event_type for event in events])

    def test_accepts_adjacent_movement(self) -> None:
        events = self.adjudicator.adjudicate(
            self.state,
            "nwl-001",
            Intention(action_type="move", destination="field"),
            tick=1,
        )
        self.assertEqual("AgentMoved", events[-1].event_type)
        self.assertEqual("field", events[-1].payload["destination"])

    def test_rejects_unknown_destination(self) -> None:
        events = self.adjudicator.adjudicate(
            self.state,
            "nwl-001",
            Intention(action_type="move", destination="sea"),
            tick=1,
        )
        self.assertEqual("ActionRejected", events[-1].event_type)


if __name__ == "__main__":
    unittest.main()
