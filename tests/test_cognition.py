from __future__ import annotations

import unittest

from helpers import ScriptedTestCognition, UnavailableTestCognition
from newland_engine.cognition import (
    AttentionSchedule,
    CognitionContext,
    CognitionResult,
    GenerativeCognitionPool,
    MentalUpdates,
    OllamaCognition,
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
