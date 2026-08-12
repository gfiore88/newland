from __future__ import annotations

import unittest

from newland_engine.models import (
    ActivityDefinition,
    Intention,
    MaterialAgentState,
    ResourceNode,
    WorldState,
)
from newland_engine.world import WorldAdjudicator, reduce_event


class WorldAdjudicatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = WorldState(
            locations={"village": {"field"}, "field": {"village"}},
            agents={
                "nwl-001": MaterialAgentState(
                    "nwl-001",
                    "Elia",
                    "village",
                    hunger=0.8,
                    thirst=0.8,
                    native_language="it",
                    language_proficiencies={"it": 1.0},
                    skills={"observation": 0.5},
                    inventory={"water": 1.0},
                ),
                "nwl-002": MaterialAgentState("nwl-002", "Amina", "field"),
            },
            resources={
                "berry_patch": ResourceNode(
                    "berry_patch", "berries", "wild berries", "village", 4.0, "kg"
                ),
                "remote_wood": ResourceNode(
                    "remote_wood", "wood", "fallen wood", "field", 10.0, "kg"
                ),
            },
            resource_effects={
                "water": {"thirst": 0.5},
                "berries": {"hunger": 0.3},
            },
            activities={
                "inspect_houses": ActivityDefinition(
                    "inspect_houses",
                    "inspect the houses",
                    "village",
                    0.05,
                    practiced_skill="observation",
                    minimum_proficiency=0.4,
                    skill_gain=0.02,
                )
            },
        )
        self.adjudicator = WorldAdjudicator()

    def test_rejects_speech_to_absent_target_without_material_consequence(self) -> None:
        events = self.adjudicator.adjudicate(
            self.state,
            "nwl-001",
            Intention(
                action_type="speak",
                target_id="nwl-002",
                spoken_content="Amina?",
                language="it",
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

    def test_gathering_updates_resource_and_inventory_only_after_reduction(
        self,
    ) -> None:
        events = self.adjudicator.adjudicate(
            self.state,
            "nwl-001",
            Intention(action_type="gather", resource_id="berry_patch", quantity=1.5),
            tick=1,
        )
        gathered = events[-1]
        self.assertEqual("ResourceGathered", gathered.event_type)
        self.assertEqual(4.0, self.state.resources["berry_patch"].quantity)

        reduce_event(self.state, gathered)
        self.assertEqual(2.5, self.state.resources["berry_patch"].quantity)
        self.assertEqual(1.5, self.state.agents["nwl-001"].inventory["berries"])

    def test_rejects_resource_outside_actor_location(self) -> None:
        events = self.adjudicator.adjudicate(
            self.state,
            "nwl-001",
            Intention(action_type="gather", resource_id="remote_wood", quantity=1.0),
            tick=1,
        )
        self.assertEqual("ActionRejected", events[-1].event_type)
        self.assertEqual(
            "resource is not present at actor location", events[-1].payload["reason"]
        )

    def test_rejects_gathering_beyond_inventory_capacity(self) -> None:
        self.state.agents["nwl-001"].inventory_capacity = 1.2
        events = self.adjudicator.adjudicate(
            self.state,
            "nwl-001",
            Intention(action_type="gather", resource_id="berry_patch", quantity=0.5),
            tick=1,
        )
        self.assertEqual("ActionRejected", events[-1].event_type)
        self.assertEqual(
            "inventory capacity would be exceeded", events[-1].payload["reason"]
        )

    def test_consumption_uses_inventory_and_applies_canonical_body_effects(
        self,
    ) -> None:
        events = self.adjudicator.adjudicate(
            self.state,
            "nwl-001",
            Intention(action_type="consume", resource_id="water", quantity=0.5),
            tick=1,
        )
        consumed = events[-1]
        self.assertEqual("ResourceConsumed", consumed.event_type)

        reduce_event(self.state, consumed)
        agent = self.state.agents["nwl-001"]
        self.assertEqual(0.5, agent.inventory["water"])
        self.assertAlmostEqual(0.55, agent.thirst)

    def test_activity_must_be_local_and_spends_physical_energy(self) -> None:
        events = self.adjudicator.adjudicate(
            self.state,
            "nwl-001",
            Intention(
                action_type="perform_activity",
                target_id="irrelevant-model-field",
                activity_id="inspect_houses",
                duration_minutes=20,
            ),
            tick=1,
        )
        performed = events[-1]
        self.assertEqual("ActivityPerformed", performed.event_type)

        reduce_event(self.state, performed)
        self.assertAlmostEqual(0.7, self.state.agents["nwl-001"].energy)
        self.assertAlmostEqual(0.52, self.state.agents["nwl-001"].skills["observation"])

    def test_rejects_language_the_speaker_does_not_know(self) -> None:
        events = self.adjudicator.adjudicate(
            self.state,
            "nwl-001",
            Intention(
                action_type="speak",
                target_id="nwl-001",
                spoken_content="مرحبا",
                language="ar",
            ),
            tick=1,
        )
        self.assertEqual("ActionRejected", events[-1].event_type)
        self.assertEqual(
            "actor cannot speak the selected language", events[-1].payload["reason"]
        )

    def test_rejects_activity_without_required_skill(self) -> None:
        self.state.agents["nwl-001"].skills["observation"] = 0.2
        events = self.adjudicator.adjudicate(
            self.state,
            "nwl-001",
            Intention(
                action_type="perform_activity",
                activity_id="inspect_houses",
            ),
            tick=1,
        )
        self.assertEqual("ActionRejected", events[-1].event_type)
        self.assertEqual(
            "actor lacks the required skill proficiency",
            events[-1].payload["reason"],
        )


if __name__ == "__main__":
    unittest.main()
