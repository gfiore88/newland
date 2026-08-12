from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from helpers import (
    CooperativeCycleTestCognition,
    GeneratedAgendaTestCognition,
    GeneratedAnamnesisTestCognition,
    GeneratedMentalStateTestCognition,
    GeneratedReflectionTestCognition,
    GeneratedRoleInterpretationTestCognition,
    InvalidAppraisalTestCognition,
    InvalidCommitmentTestCognition,
    ScriptedTestCognition,
    SituatedActivityTestCognition,
    TEST_FIXTURE_PROFILES,
    UnavailableTestCognition,
)
from newland_engine.event_store import EventStore
from newland_engine.models import (
    AgentMind,
    EventEnvelope,
    Intention,
    world_time_for_tick,
)
from newland_engine.simulation import NewlandSimulation
from newland_engine.world import reduce_event, replay


class SimulationTests(unittest.TestCase):
    def test_resonance_does_not_create_static_flashback_when_cognition_fails(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "newland.db"
            with NewlandSimulation(
                path, cognition=UnavailableTestCognition()
            ) as simulation:
                simulation.seed_initial_encounter(TEST_FIXTURE_PROFILES)
                movement = simulation.adjudicator.adjudicate(
                    simulation.state,
                    "nwl-001",
                    Intention(action_type="move", destination="bosco_est"),
                    tick=1,
                    cognition={
                        "provider": "test-double",
                        "model": "setup-movement",
                        "inference_id": "setup",
                    },
                )
                persisted = simulation.store.append_many(movement)
                for event in persisted:
                    reduce_event(simulation.state, event)

                produced = simulation.run(max_activations=1)
                mind = simulation.minds["nwl-001"]

            event_types = {event.event_type for event in produced}
            self.assertIn("CognitionDeferred", event_types)
            self.assertNotIn("AnamnesisFragmentRevised", event_types)
            self.assertNotIn("ResonanceOrientationRevised", event_types)
            self.assertEqual({}, mind.anamnesis_fragments)
            self.assertIsNone(mind.resonance_orientation)

    def test_flashback_content_and_channel_closure_are_generated_privately(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "newland.db"
            with NewlandSimulation(
                path, cognition=GeneratedAnamnesisTestCognition()
            ) as simulation:
                simulation.seed_initial_encounter(TEST_FIXTURE_PROFILES)
                movement = simulation.adjudicator.adjudicate(
                    simulation.state,
                    "nwl-001",
                    Intention(action_type="move", destination="bosco_est"),
                    tick=1,
                    cognition={
                        "provider": "test-double",
                        "model": "setup-movement",
                        "inference_id": "setup",
                    },
                )
                persisted = simulation.store.append_many(movement)
                for event in persisted:
                    reduce_event(simulation.state, event)
                signal = next(
                    event
                    for event in persisted
                    if event.event_type == "ResonanceSignalReceived"
                )
                self.assertEqual({}, simulation.minds["nwl-001"].anamnesis_fragments)

                produced = simulation.run(max_activations=1)
                mind = simulation.minds["nwl-001"]

            fragment = mind.anamnesis_fragments["cerchio_di_luce_senza_nome"]
            self.assertEqual(
                "immagine improvvisa e incompleta", fragment.phenomenon_label
            )
            self.assertEqual([signal.event_id], fragment.source_event_ids)
            self.assertFalse(mind.resonance_receptive)
            mental_events = [
                event
                for event in produced
                if event.event_type
                in {"AnamnesisFragmentRevised", "ResonanceOrientationRevised"}
            ]
            self.assertEqual(2, len(mental_events))
            reflection = next(
                event for event in produced if event.event_type == "ReflectionCreated"
            )
            self.assertEqual((signal.event_id,), reflection.payload["source_event_ids"])
            self.assertEqual((), reflection.payload["source_memory_ids"])
            self.assertTrue(
                all(
                    event.visibility == "private"
                    and event.recipient_ids == ("nwl-001",)
                    and event.payload["cognition"]["model"]
                    == "generated-anamnesis-fixture"
                    for event in mental_events
                )
            )

            with NewlandSimulation(
                path, cognition=GeneratedAnamnesisTestCognition()
            ) as restarted:
                restored = restarted.minds["nwl-001"]
                self.assertFalse(restored.resonance_receptive)
                self.assertIn(
                    "cerchio_di_luce_senza_nome", restored.anamnesis_fragments
                )

    def test_roles_exist_only_after_private_generative_interpretation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "newland.db"
            with NewlandSimulation(
                path, cognition=GeneratedRoleInterpretationTestCognition()
            ) as simulation:
                simulation.seed_initial_encounter(TEST_FIXTURE_PROFILES)
                self.assertEqual({}, simulation.minds["nwl-001"].role_interpretations)
                self.assertIn("mediazione", simulation.state.agents["nwl-002"].skills)
                produced = simulation.run(max_activations=1)
                roles = simulation.minds["nwl-001"].role_interpretations

            self.assertEqual(
                {
                    "amina_presenza_di_soglia",
                    "elia_ascoltatore_del_luogo",
                },
                set(roles),
            )
            self.assertEqual(
                "custode delle soglie incerte",
                roles["amina_presenza_di_soglia"].role_label,
            )
            role_events = [
                event
                for event in produced
                if event.event_type == "RoleInterpretationRevised"
            ]
            self.assertEqual(2, len(role_events))
            self.assertTrue(
                all(
                    event.visibility == "private"
                    and event.recipient_ids == ("nwl-001",)
                    and event.payload["cognition"]["model"]
                    == "generated-role-interpretation-fixture"
                    for event in role_events
                )
            )

            with NewlandSimulation(
                path, cognition=GeneratedRoleInterpretationTestCognition()
            ) as restarted:
                self.assertEqual(
                    "ascoltatore del luogo vuoto",
                    restarted.minds["nwl-001"]
                    .role_interpretations["elia_ascoltatore_del_luogo"]
                    .role_label,
                )

    def test_generated_social_actions_complete_a_replayable_cooperation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "newland.db"
            with NewlandSimulation(
                path, cognition=CooperativeCycleTestCognition()
            ) as simulation:
                simulation.seed_initial_encounter(TEST_FIXTURE_PROFILES)
                produced = simulation.run(max_activations=3)
                social_types = [
                    event.event_type
                    for event in produced
                    if event.event_type.startswith("Cooperation")
                ]
                proposal_id = next(
                    event.event_id
                    for event in produced
                    if event.event_type == "CooperationProposed"
                )
                expected_energy = {
                    agent_id: agent.energy
                    for agent_id, agent in simulation.state.agents.items()
                }

            self.assertEqual(
                [
                    "CooperationProposed",
                    "CooperationResponded",
                    "CooperationPerformed",
                ],
                social_types,
            )
            self.assertTrue(
                all(
                    event.payload["cognition"]["model"] == "cooperative-cycle-fixture"
                    for event in produced
                    if event.event_type == "ActionProposed"
                )
            )

            with EventStore(path) as store:
                reconstructed = replay(store.events())
            self.assertEqual(
                "completed", reconstructed.cooperations[proposal_id].status
            )
            self.assertEqual(
                expected_energy,
                {
                    agent_id: agent.energy
                    for agent_id, agent in reconstructed.agents.items()
                },
            )

    def test_vertical_slice_produces_two_sided_conversation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "newland.db"
            with NewlandSimulation(
                path, cognition=ScriptedTestCognition()
            ) as simulation:
                simulation.seed_initial_encounter(TEST_FIXTURE_PROFILES)
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
                simulation.seed_initial_encounter(TEST_FIXTURE_PROFILES)
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
                simulation.seed_initial_encounter(TEST_FIXTURE_PROFILES)
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
                simulation.seed_initial_encounter(TEST_FIXTURE_PROFILES)
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
                simulation.seed_initial_encounter(TEST_FIXTURE_PROFILES)
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
                simulation.seed_initial_encounter(TEST_FIXTURE_PROFILES)
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
                simulation.seed_initial_encounter(TEST_FIXTURE_PROFILES)
                simulation.run(max_activations=1)

            with NewlandSimulation(
                path, cognition=GeneratedReflectionTestCognition()
            ) as simulation:
                simulation.seed_initial_encounter(TEST_FIXTURE_PROFILES)
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

    def test_generated_plan_commitment_and_attention_are_durable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "newland.db"
            with NewlandSimulation(
                path, cognition=GeneratedAgendaTestCognition()
            ) as simulation:
                simulation.seed_initial_encounter(TEST_FIXTURE_PROFILES)
                produced = simulation.run(max_activations=1)
                mind = simulation.minds["nwl-001"]
                self.assertEqual("active", mind.plans["incontro_cauto"].status)
                commitment_tick = mind.commitments["parlare_con_altro"].due_tick
                attention_tick = mind.next_activation_tick
                self.assertEqual(4, commitment_tick)
                self.assertEqual(10, attention_tick)
                self.assertEqual(
                    {
                        "PlanRevised",
                        "CommitmentRevised",
                        "AttentionScheduled",
                    },
                    {
                        event.event_type
                        for event in produced
                        if event.event_type
                        in {
                            "PlanRevised",
                            "CommitmentRevised",
                            "AttentionScheduled",
                        }
                    },
                )

            with NewlandSimulation(
                path, cognition=GeneratedAgendaTestCognition()
            ) as restarted:
                restarted.seed_initial_encounter(TEST_FIXTURE_PROFILES)
                pending = restarted.scheduler.pending()
                self.assertTrue(
                    any(
                        activation.agent_id == "nwl-001"
                        and activation.tick == commitment_tick
                        and activation.reason.startswith("impegno generato:")
                        for activation in pending
                    )
                )
                self.assertTrue(
                    any(
                        activation.agent_id == "nwl-001"
                        and activation.tick == attention_tick
                        and activation.reason
                        == "Rivedere il piano quando avrò osservato abbastanza."
                        for activation in pending
                    )
                )

    def test_invalid_generated_commitment_defers_without_action(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "newland.db"
            with NewlandSimulation(
                path, cognition=InvalidCommitmentTestCognition()
            ) as simulation:
                simulation.seed_initial_encounter(TEST_FIXTURE_PROFILES)
                produced = simulation.run(max_activations=1)

            event_types = {event.event_type for event in produced}
            self.assertIn("CognitionDeferred", event_types)
            self.assertNotIn("ActionProposed", event_types)
            self.assertNotIn("CommitmentRevised", event_types)

    def test_agent_receives_only_situated_affordances_and_can_choose_one(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "newland.db"
            cognition = SituatedActivityTestCognition()
            with NewlandSimulation(path, cognition=cognition) as simulation:
                simulation.seed_initial_encounter(TEST_FIXTURE_PROFILES)
                produced = simulation.run(max_activations=1)

            context = cognition.contexts[0]
            self.assertEqual(("bosco_est", "campo_nord"), context.adjacent_locations)
            self.assertEqual((), context.local_resources)
            self.assertEqual(
                ("esaminare_edifici",),
                tuple(
                    activity.activity_id for activity in context.available_activities
                ),
            )
            activity = next(
                event for event in produced if event.event_type == "ActivityPerformed"
            )
            self.assertEqual("esaminare_edifici", activity.payload["activity_id"])
            self.assertEqual(
                "situated-activity-fixture",
                next(
                    event for event in produced if event.event_type == "ActionProposed"
                ).payload["cognition"]["model"],
            )

    def test_existing_world_receives_a_replayable_territory_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "newland.db"
            legacy_mind = AgentMind(
                agent_id="nwl-001",
                name="Legacy Newlander",
                values=["continuità"],
                temperament=["vigile"],
            )
            with EventStore(path) as store:
                store.append_many(
                    [
                        EventEnvelope(
                            event_type="WorldInitialized",
                            world_tick=0,
                            world_time=world_time_for_tick(0),
                            payload={
                                "name": "Newland",
                                "locations": {"cittadina_iniziale": []},
                            },
                        ),
                        EventEnvelope(
                            event_type="AgentRegistered",
                            world_tick=0,
                            world_time=world_time_for_tick(0),
                            actor_ids=(legacy_mind.agent_id,),
                            location="cittadina_iniziale",
                            payload={
                                "name": legacy_mind.name,
                                "location": "cittadina_iniziale",
                            },
                            visibility="private",
                            recipient_ids=(legacy_mind.agent_id,),
                        ),
                    ]
                )
                store.save_mind(legacy_mind)

            with NewlandSimulation(
                path, cognition=ScriptedTestCognition()
            ) as simulation:
                simulation.initialize()
                self.assertIn("vena_sorgente", simulation.state.resources)
                self.assertEqual(
                    "und", simulation.state.agents["nwl-001"].native_language
                )
                self.assertEqual(
                    "TerritoryConfigured", simulation.store.events()[-1].event_type
                )

            with EventStore(path) as store:
                reconstructed = replay(store.events())
            self.assertIn("bosco_est", reconstructed.locations)
            self.assertIn("esplorare_sottobosco", reconstructed.activities)

    def test_activity_migration_preserves_existing_resource_quantities(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "newland.db"
            legacy_mind = AgentMind(
                agent_id="nwl-legacy",
                name="Legacy Newlander",
                values=["continuità"],
                temperament=["vigile"],
            )
            with EventStore(path) as store:
                store.append_many(
                    [
                        EventEnvelope(
                            event_type="WorldInitialized",
                            world_tick=0,
                            world_time=world_time_for_tick(0),
                            payload={
                                "locations": {"cittadina_iniziale": []},
                                "resources": {
                                    "risorsa_esistente": {
                                        "kind": "bacche",
                                        "label": "risorsa già modificata",
                                        "location": "cittadina_iniziale",
                                        "quantity": 7.0,
                                        "unit": "kg",
                                        "renewable": True,
                                    }
                                },
                                "activities": {
                                    "attivita_legacy": {
                                        "label": "attività senza competenza",
                                        "location": "cittadina_iniziale",
                                        "energy_cost": 0.0,
                                    }
                                },
                            },
                        ),
                        EventEnvelope(
                            event_type="AgentRegistered",
                            world_tick=0,
                            world_time=world_time_for_tick(0),
                            actor_ids=(legacy_mind.agent_id,),
                            location="cittadina_iniziale",
                            payload={
                                "name": legacy_mind.name,
                                "location": "cittadina_iniziale",
                            },
                            visibility="private",
                            recipient_ids=(legacy_mind.agent_id,),
                        ),
                    ]
                )
                store.save_mind(legacy_mind)

            with NewlandSimulation(
                path, cognition=ScriptedTestCognition()
            ) as simulation:
                simulation.initialize()
                self.assertEqual(
                    7.0, simulation.state.resources["risorsa_esistente"].quantity
                )
                self.assertEqual(
                    [
                        "TerritoryActivitiesConfigured",
                        "ResonanceNodesConfigured",
                    ],
                    [event.event_type for event in simulation.store.events()[-2:]],
                )
                self.assertIn("eco_della_sorgente", simulation.state.resonance_nodes)
                self.assertEqual(
                    "osservazione",
                    simulation.state.activities["esaminare_edifici"].practiced_skill,
                )


if __name__ == "__main__":
    unittest.main()
