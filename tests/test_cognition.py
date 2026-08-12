from __future__ import annotations

import unittest

from helpers import ScriptedTestCognition, UnavailableTestCognition
from newland_engine.cognition import (
    CognitionContext,
    GenerativeCognitionPool,
    OllamaCognition,
)
from newland_engine.models import (
    AgentMind,
    EventEnvelope,
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
