from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from helpers import (
    GeneratedMentalStateTestCognition,
    GeneratedReflectionTestCognition,
    InvalidAppraisalTestCognition,
    ScriptedTestCognition,
    UnavailableTestCognition,
)
from newland_engine.event_store import EventStore
from newland_engine.simulation import NewlandSimulation
from newland_engine.world import replay


class SimulationTests(unittest.TestCase):
    def test_vertical_slice_produces_two_sided_conversation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "newland.db"
            with NewlandSimulation(
                path, cognition=ScriptedTestCognition()
            ) as simulation:
                produced = simulation.run(max_activations=2)
                speech = [
                    event for event in produced if event.event_type == "SpeechUttered"
                ]
                minds = simulation.minds

            self.assertEqual(2, len(speech))
            self.assertEqual(
                ["nwl-001", "nwl-002"], [event.actor_ids[0] for event in speech]
            )
            self.assertIsNot(minds["nwl-001"], minds["nwl-002"])
            self.assertNotEqual(minds["nwl-001"].values, minds["nwl-002"].values)
            self.assertTrue(minds["nwl-001"].memories)
            self.assertTrue(minds["nwl-002"].memories)

    def test_event_replay_matches_persisted_material_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "newland.db"
            with NewlandSimulation(
                path, cognition=ScriptedTestCognition()
            ) as simulation:
                simulation.run(max_activations=4)
                expected_tick = simulation.state.tick
                expected_agents = {
                    key: (value.location, value.energy)
                    for key, value in simulation.state.agents.items()
                }

            with EventStore(path) as store:
                reconstructed = replay(store.events())

            self.assertEqual(expected_tick, reconstructed.tick)
            self.assertEqual(
                expected_agents,
                {
                    key: (value.location, value.energy)
                    for key, value in reconstructed.agents.items()
                },
            )

    def test_restart_loads_distinct_persistent_minds(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "newland.db"
            with NewlandSimulation(
                path, cognition=ScriptedTestCognition()
            ) as simulation:
                simulation.run(max_activations=2)
                first_memory_counts = {
                    agent_id: len(mind.memories)
                    for agent_id, mind in simulation.minds.items()
                }

            with NewlandSimulation(
                path, cognition=ScriptedTestCognition()
            ) as restarted:
                self.assertEqual(set(first_memory_counts), set(restarted.minds))
                self.assertEqual(
                    first_memory_counts,
                    {
                        agent_id: len(mind.memories)
                        for agent_id, mind in restarted.minds.items()
                    },
                )
                events = restarted.store.events()
                self.assertLess(
                    max(
                        mind.last_perceived_sequence
                        for mind in restarted.minds.values()
                    ),
                    events[-1].sequence,
                )

    def test_failed_generation_defers_without_static_material_action(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "newland.db"
            with NewlandSimulation(
                path, cognition=UnavailableTestCognition()
            ) as simulation:
                produced = simulation.run(max_activations=1)

            types = [event.event_type for event in produced]
            self.assertIn("CognitionDeferred", types)
            self.assertNotIn("ActionProposed", types)
            self.assertNotIn("AgentRested", types)
            self.assertNotIn("SpeechUttered", types)

    def test_action_proposal_records_generative_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "newland.db"
            with NewlandSimulation(
                path, cognition=ScriptedTestCognition()
            ) as simulation:
                produced = simulation.run(max_activations=1)

            proposal = next(
                event for event in produced if event.event_type == "ActionProposed"
            )
            self.assertEqual("test-double", proposal.payload["cognition"]["provider"])
            self.assertEqual(
                "scripted-invariant-fixture", proposal.payload["cognition"]["model"]
            )
            self.assertTrue(proposal.payload["cognition"]["inference_id"])

    def test_unperceived_memory_appraisal_defers_and_cannot_drive_action(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "newland.db"
            with NewlandSimulation(
                path, cognition=InvalidAppraisalTestCognition()
            ) as simulation:
                produced = simulation.run(max_activations=1)

            types = [event.event_type for event in produced]
            self.assertIn("CognitionDeferred", types)
            self.assertNotIn("ActionProposed", types)

    def test_generated_mental_updates_are_applied_and_audited(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "newland.db"
            with NewlandSimulation(
                path, cognition=GeneratedMentalStateTestCognition()
            ) as simulation:
                produced = simulation.run(max_activations=1)
                mind = simulation.minds["nwl-001"]

            self.assertEqual(
                "Un'altra persona è realmente qui con me.",
                mind.beliefs["non_sono_solo"].statement,
            )
            relationship = mind.relationships["nwl-002"]
            self.assertAlmostEqual(0.1, relationship.familiarity)
            self.assertAlmostEqual(0.54, relationship.trust)
            self.assertIn("conoscere con prudenza l'altra persona", mind.goals)
            event_types = {event.event_type for event in produced}
            self.assertTrue(
                {"BeliefUpdated", "RelationshipUpdated", "AffectUpdated", "GoalRevised"}
                <= event_types
            )
            mental_event = next(
                event for event in produced if event.event_type == "BeliefUpdated"
            )
            self.assertEqual(
                "generated-mental-state-fixture",
                mental_event.payload["cognition"]["model"],
            )
            with NewlandSimulation(
                path, cognition=GeneratedMentalStateTestCognition()
            ) as restarted:
                self.assertIn("non_sono_solo", restarted.minds["nwl-001"].beliefs)
                self.assertIn("nwl-002", restarted.minds["nwl-001"].relationships)

    def test_generated_reflection_uses_persisted_memory_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "newland.db"
            with NewlandSimulation(
                path, cognition=ScriptedTestCognition()
            ) as simulation:
                simulation.run(max_activations=1)

            with NewlandSimulation(
                path, cognition=GeneratedReflectionTestCognition()
            ) as simulation:
                produced = simulation.run(max_activations=1)
                reflections = simulation.minds["nwl-001"].reflections

            self.assertEqual(1, len(reflections))
            reflection_event = next(
                event for event in produced if event.event_type == "ReflectionCreated"
            )
            self.assertEqual(
                reflections[0].source_memory_ids,
                list(reflection_event.payload["source_memory_ids"]),
            )


if __name__ == "__main__":
    unittest.main()
