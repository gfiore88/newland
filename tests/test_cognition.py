from __future__ import annotations

import unittest

from helpers import ScriptedTestCognition, UnavailableTestCognition
from newland_engine.cognition import (
    AffectRevision,
    AnamnesisFragmentRevision,
    AttentionSchedule,
    CognitionContext,
    CognitionResult,
    DisputeAffordance,
    GenerativeCognitionPool,
    MentalUpdates,
    OllamaCognition,
    ResonanceNodeAffordance,
    RoleInterpretationRevision,
    RoutedCognition,
    validate_cognition_result,
)
from newland_engine.models import (
    AgentMind,
    EventEnvelope,
    Intention,
    MaterialAgentState,
    Memory,
    world_time_for_tick,
)
from newland_engine.perception import Observation


class RecordingCognition:
    def __init__(self, model: str) -> None:
        self.model = model
        self.contexts: list[CognitionContext] = []

    def decide(self, cognition_context: CognitionContext) -> CognitionResult:
        self.contexts.append(cognition_context)
        return CognitionResult(
            intention=Intention(
                action_type="rest",
                motivation_summary=f"Decisione generata da {self.model}.",
            ),
            memory_appraisals=(),
            mental_updates=MentalUpdates(),
            attention_schedule=AttentionSchedule(4, "Riesaminare la situazione."),
            provider="recording-test-double",
            model=self.model,
            inference_id=f"inference-{self.model}",
            attempts=1,
        )


def context() -> CognitionContext:
    mind = AgentMind(
        agent_id="nwl-test",
        name="Test Newlander",
        values=["autonomia"],
        temperament=["vigile"],
    )
    return CognitionContext(
        mind=mind,
        material_state=MaterialAgentState(
            "nwl-test",
            "Test Newlander",
            "village",
            native_language="it",
            language_proficiencies={"it": 1.0},
        ),
        observations=(),
        nearby_agents=(("nwl-other", "Other Newlander"),),
        activation_reason="test generative failover",
    )


class GenerativeCognitionPoolTests(unittest.TestCase):
    def test_router_changes_only_model_tier_and_records_route(self) -> None:
        ordinary = RecordingCognition("ordinary-model")
        reflective = RecordingCognition("reflective-model")
        router = RoutedCognition(ordinary, reflective)
        ordinary_context = context()

        ordinary_result = router.decide(ordinary_context)

        self.assertEqual("ordinary-model", ordinary_result.model)
        self.assertEqual("rest", ordinary_result.intention.action_type)
        self.assertEqual("ordinary", ordinary_result.provenance()["route"])
        self.assertIs(ordinary_context, ordinary.contexts[0])
        self.assertEqual([], reflective.contexts)

        signal = EventEnvelope(
            event_type="ResonanceSignalReceived",
            world_tick=1,
            world_time=world_time_for_tick(1),
            actor_ids=("nwl-test",),
            payload={
                "node_id": "local-node",
                "intensity": 0.5,
                "exposure_mode": "arrival",
            },
            visibility="private",
            recipient_ids=("nwl-test",),
        )
        reflective_context = CognitionContext(
            mind=ordinary_context.mind,
            material_state=ordinary_context.material_state,
            observations=(Observation(signal),),
            nearby_agents=ordinary_context.nearby_agents,
            activation_reason="segnale percepito",
        )

        reflective_result = router.decide(reflective_context)

        self.assertEqual("reflective-model", reflective_result.model)
        self.assertEqual("rest", reflective_result.intention.action_type)
        self.assertEqual("reflective", reflective_result.provenance()["route"])
        self.assertIs(reflective_context, reflective.contexts[0])

    def test_active_dispute_uses_reflective_tier_without_global_context(self) -> None:
        ordinary = RecordingCognition("ordinary-model")
        reflective = RecordingCognition("reflective-model")
        router = RoutedCognition(ordinary, reflective)
        base = context()
        dispute_context = CognitionContext(
            mind=base.mind,
            material_state=base.material_state,
            observations=(),
            nearby_agents=base.nearby_agents,
            activation_reason="conflitto attivo",
            active_disputes=(
                DisputeAffordance(
                    dispute_id="dispute-1",
                    opener_id="nwl-test",
                    target_id="nwl-other",
                    subject_event_id="event-1",
                    status="open",
                    resolution_offered_by=None,
                ),
            ),
        )

        result = router.decide(dispute_context)

        self.assertEqual("reflective", result.route)
        self.assertEqual("reflective-model", result.model)
        self.assertEqual([], ordinary.contexts)
        self.assertEqual([dispute_context], reflective.contexts)

    def test_intense_generated_affect_is_valid(self) -> None:
        revision = AffectRevision(
            calm_delta=-0.8,
            curiosity_delta=0.9,
            melancholy_delta=0.6,
            interpretation="Una risposta intensa scelta dalla mente.",
            source_event_ids=("event",),
        )
        self.assertEqual(-0.8, revision.calm_delta)

    def test_anamnesis_requires_a_perceived_resonance_source(self) -> None:
        cognition_context = context()
        ordinary_event = EventEnvelope(
            event_type="AgentArrived",
            world_tick=1,
            world_time=world_time_for_tick(1),
            event_id="ordinary-event",
            actor_ids=("nwl-other",),
            visibility="local",
            recipient_ids=("nwl-test",),
        )
        cognition_context = CognitionContext(
            mind=cognition_context.mind,
            material_state=cognition_context.material_state,
            observations=(Observation(ordinary_event),),
            nearby_agents=cognition_context.nearby_agents,
            activation_reason=cognition_context.activation_reason,
        )
        result = CognitionResult(
            intention=Intention(action_type="rest"),
            memory_appraisals=(),
            mental_updates=MentalUpdates(
                anamnesis_fragments=(
                    AnamnesisFragmentRevision(
                        fragment_key="unsupported",
                        phenomenon_label="immagine inventata",
                        content="Un contenuto senza alcun segnale di risonanza.",
                        interpretation="Non è fondato nell'esperienza prevista.",
                        confidence=0.5,
                        source_event_ids=(ordinary_event.event_id,),
                    ),
                )
            ),
            attention_schedule=AttentionSchedule(4, "Riesaminare l'esperienza."),
            provider="test-double",
            model="invalid-anamnesis-fixture",
            inference_id="inference-test",
            attempts=1,
        )

        with self.assertRaisesRegex(ValueError, "resonance provenance"):
            validate_cognition_result(result, cognition_context)

    def test_anamnesis_labels_are_free_text_not_runtime_categories(self) -> None:
        schema = OllamaCognition._schema()["properties"]["mental_updates"][
            "properties"
        ]["anamnesis_fragments"]["items"]["properties"]["phenomenon_label"]
        self.assertNotIn("enum", schema)

    def test_resonance_action_must_reference_a_local_node(self) -> None:
        cognition_context = context()
        result = CognitionResult(
            intention=Intention(action_type="attune_resonance", node_id="remote_node"),
            memory_appraisals=(),
            mental_updates=MentalUpdates(),
            attention_schedule=AttentionSchedule(4, "Riesaminare il segnale."),
            provider="test-double",
            model="invalid-resonance-reference-fixture",
            inference_id="inference-test",
            attempts=1,
        )

        with self.assertRaisesRegex(ValueError, "non-local node"):
            validate_cognition_result(result, cognition_context)

        valid_context = CognitionContext(
            mind=cognition_context.mind,
            material_state=cognition_context.material_state,
            observations=(),
            nearby_agents=cognition_context.nearby_agents,
            activation_reason=cognition_context.activation_reason,
            local_resonance_nodes=(
                ResonanceNodeAffordance("remote_node", "eco locale", 0.4),
            ),
        )
        validate_cognition_result(result, valid_context)

    def test_intention_rejects_invented_parameters_from_other_actions(self) -> None:
        with self.assertRaisesRegex(ValueError, "fields for another action"):
            Intention(
                action_type="speak",
                target_id="nwl-other",
                spoken_content="Ti vedo.",
                language="it",
                activity_id="conversation_invented_by_model",
            )

    def test_ollama_parser_discards_only_irrelevant_schema_filler(self) -> None:
        intention = OllamaCognition._parse_intention(
            {
                "action_type": "propose_cooperation",
                "target_id": "nwl-other",
                "destination": "invented-place",
                "duration_minutes": 10,
                "spoken_content": "Vuoi osservare il luogo insieme?",
                "language": "it",
                "resource_id": "invented-resource",
                "quantity": 1,
                "activity_id": "observed-activity",
                "proposal_id": "irrelevant-proposal",
                "dispute_id": "irrelevant-dispute",
                "subject_event_id": "irrelevant-event",
                "response": "accept",
                "motivation_summary": "Condividere una scelta.",
                "confidence": 0.8,
            }
        )

        self.assertEqual("propose_cooperation", intention.action_type)
        self.assertEqual("nwl-other", intention.target_id)
        self.assertEqual("observed-activity", intention.activity_id)
        self.assertIsNone(intention.destination)
        self.assertIsNone(intention.resource_id)
        self.assertIsNone(intention.proposal_id)

    def test_role_labels_are_free_text_not_a_runtime_taxonomy(self) -> None:
        role_schema = OllamaCognition._schema()["properties"]["mental_updates"][
            "properties"
        ]["role_interpretations"]["items"]["properties"]["role_label"]
        self.assertNotIn("enum", role_schema)

    def test_generated_role_cannot_describe_an_unknown_agent(self) -> None:
        cognition_context = context()
        observed = EventEnvelope(
            event_type="AgentArrived",
            world_tick=1,
            world_time=world_time_for_tick(1),
            event_id="event-visible",
            actor_ids=("nwl-other",),
            recipient_ids=("nwl-test",),
            visibility="local",
        )
        cognition_context = CognitionContext(
            mind=cognition_context.mind,
            material_state=cognition_context.material_state,
            observations=(Observation(observed),),
            nearby_agents=cognition_context.nearby_agents,
            activation_reason=cognition_context.activation_reason,
        )
        result = CognitionResult(
            intention=Intention(action_type="rest"),
            memory_appraisals=(),
            mental_updates=MentalUpdates(
                role_interpretations=(
                    RoleInterpretationRevision(
                        operation="upsert",
                        interpretation_key="invented_person_role",
                        subject_agent_id="nwl-invented",
                        role_label="figura mai incontrata",
                        interpretation="Una lettura senza alcuna esperienza.",
                        confidence=0.5,
                        source_event_ids=(observed.event_id,),
                    ),
                )
            ),
            attention_schedule=AttentionSchedule(4, "Riesaminare la situazione."),
            provider="test-double",
            model="invalid-role-subject-fixture",
            inference_id="inference-test",
            attempts=1,
        )

        with self.assertRaisesRegex(ValueError, "unknown agent"):
            validate_cognition_result(result, cognition_context)

    def test_generated_social_references_must_come_from_agent_context(self) -> None:
        result = CognitionResult(
            intention=Intention(
                action_type="respond_cooperation",
                proposal_id="proposal-invented",
                response="accept",
                spoken_content="Accetto.",
                language="it",
            ),
            memory_appraisals=(),
            mental_updates=MentalUpdates(),
            attention_schedule=AttentionSchedule(4, "Riconsiderare l'incontro."),
            provider="test-double",
            model="invalid-social-reference-fixture",
            inference_id="inference-test",
            attempts=1,
        )

        with self.assertRaisesRegex(ValueError, "unknown proposal"):
            validate_cognition_result(result, context())

    def test_generated_dispute_must_reference_a_perceived_event(self) -> None:
        result = CognitionResult(
            intention=Intention(
                action_type="open_dispute",
                target_id="nwl-other",
                subject_event_id="event-invented",
                spoken_content="Contesto ciò che è accaduto.",
                language="it",
            ),
            memory_appraisals=(),
            mental_updates=MentalUpdates(),
            attention_schedule=AttentionSchedule(4, "Riconsiderare il conflitto."),
            provider="test-double",
            model="invalid-dispute-reference-fixture",
            inference_id="inference-test",
            attempts=1,
        )

        with self.assertRaisesRegex(ValueError, "unknown to the agent"):
            validate_cognition_result(result, context())

    def test_failover_uses_another_generative_provider(self) -> None:
        pool = GenerativeCognitionPool(
            [UnavailableTestCognition(), ScriptedTestCognition()]
        )
        result = pool.decide(context())
        self.assertEqual("test-double", result.provider)
        self.assertEqual("speak", result.intention.action_type)

    def test_pool_without_provider_is_invalid(self) -> None:
        with self.assertRaises(ValueError):
            GenerativeCognitionPool([])

    def test_compact_sources_are_classified_without_losing_provenance(self) -> None:
        cognition_context = context()
        event = EventEnvelope(
            event_type="AgentArrived",
            world_tick=1,
            world_time=world_time_for_tick(1),
            event_id="event-visible",
        )
        memory = Memory(
            memory_id="memory-owned",
            source_event_id="older-event",
            event_type="AgentArrived",
            summary="Ricordo precedente.",
            salience=0.7,
            emotional_tone="calma",
            confidence=0.8,
            created_tick=0,
        )
        cognition_context.mind.memories.append(memory)
        cognition_context = CognitionContext(
            mind=cognition_context.mind,
            material_state=cognition_context.material_state,
            observations=(Observation(event),),
            nearby_agents=cognition_context.nearby_agents,
            activation_reason=cognition_context.activation_reason,
        )

        classified = OllamaCognition._classify_sources(
            {
                "key": "presenza",
                "statement": "Qualcuno è arrivato.",
                "confidence": 0.8,
                "source_ids": [event.event_id, memory.memory_id],
            },
            cognition_context,
        )
        self.assertEqual((event.event_id,), classified["source_event_ids"])
        self.assertEqual((memory.memory_id,), classified["source_memory_ids"])

        with self.assertRaises(ValueError):
            OllamaCognition._classify_sources(
                {"source_ids": ["invented-source"]}, cognition_context
            )


if __name__ == "__main__":
    unittest.main()
