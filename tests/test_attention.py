from __future__ import annotations

import json
import unittest
from dataclasses import replace

from newland_engine.cognition import (
    AttentionSchedule,
    CognitionContext,
    CognitionResult,
    CognitionUnavailable,
    ContextExpansionRequest,
    DisputeAffordance,
    MentalUpdates,
    ProgressiveCognition,
)
from newland_engine.cognition.attention import (
    compact_schema_contract,
    minimum_attention_level,
    parse_context_expansion,
    progressive_response_schema,
    visible_attention_source_ids,
)
from newland_engine.cognition.prompting import build_private_context
from newland_engine.models import (
    AgentMind,
    AnamnesisFragment,
    Belief,
    Commitment,
    Intention,
    MaterialAgentState,
    Memory,
    EventEnvelope,
    Plan,
    Reflection,
    Relationship,
    RoleInterpretation,
)
from newland_engine.models import world_time_for_tick
from newland_engine.perception import Observation


def rich_context() -> CognitionContext:
    mind = AgentMind(
        agent_id="nwl-self",
        name="Ada",
        values=["autonomia", "cura"],
        temperament=["vigile"],
        goals=["Parlare con Bruno della sorgente", "Esplorare il bosco"],
    )
    mind.beliefs = {
        "water": Belief(
            "water",
            "Bruno conosce la sorgente",
            0.8,
            ["memory-bruno"],
            8,
        ),
        "forest": Belief(
            "forest", "Il bosco è silenzioso", 0.6, ["memory-forest"], 7
        ),
    }
    mind.relationships = {
        "nwl-bruno": Relationship("nwl-bruno", familiarity=0.8, trust=0.7),
        "nwl-cora": Relationship("nwl-cora", familiarity=0.5, trust=0.2),
    }
    mind.plans = {
        "water-plan": Plan(
            "water-plan",
            "Chiedere a Bruno della sorgente",
            ["incontrare Bruno", "parlare"],
            "active",
            5,
            8,
        ),
        "forest-plan": Plan(
            "forest-plan",
            "Esplorare il bosco",
            ["raggiungere il sentiero"],
            "active",
            4,
            7,
        ),
    }
    mind.commitments = {
        "bruno-promise": Commitment(
            "bruno-promise",
            "Incontrare Bruno",
            12,
            ["nwl-bruno"],
            "active",
            4,
            8,
        )
    }
    mind.role_interpretations = {
        "bruno-guide": RoleInterpretation(
            "bruno-guide",
            "nwl-bruno",
            "conoscitore della sorgente",
            "Bruno sembra orientarsi bene",
            0.7,
            6,
            8,
        )
    }
    mind.anamnesis_fragments = {
        "old-water": AnamnesisFragment(
            "old-water",
            "odore metallico",
            "Un'acqua dal sapore metallico",
            "Potrebbe essere un ricordo incerto",
            0.4,
            3,
            3,
        )
    }
    mind.reflections = [
        Reflection(
            "reflection-1",
            "La fiducia richiede attenzione.",
            0.7,
            ["memory-bruno"],
            8,
        )
    ]
    mind.memories = [
        Memory(
            "memory-bruno",
            "event-bruno",
            "AgentSpoke",
            "Bruno mi ha parlato della sorgente.",
            0.8,
            "curiosità",
            0.9,
            8,
            participants=("nwl-bruno",),
        ),
        Memory(
            "memory-forest",
            "event-forest",
            "AgentMoved",
            "Ho attraversato il bosco con Cora.",
            0.9,
            "allerta",
            0.8,
            9,
            participants=("nwl-cora",),
        ),
    ]
    return CognitionContext(
        mind=mind,
        material_state=MaterialAgentState(
            "nwl-self",
            "Ada",
            "piazza",
            native_language="it",
            language_proficiencies={"it": 1.0},
        ),
        observations=(),
        nearby_agents=(("nwl-bruno", "Bruno"),),
        activation_reason="presenza di Bruno in piazza",
        world_tick=10,
        action_contracts={"consume": {"carried": []}},
    )


class SelectiveAttentionContextTests(unittest.TestCase):
    def test_focal_context_keeps_self_and_local_state_but_not_global_mind(self) -> None:
        base = rich_context()
        full = build_private_context(base)
        focal = build_private_context(replace(base, attention_level="focal"))

        self.assertEqual(["autonomia", "cura"], focal["self"]["values"])
        self.assertEqual("presenza di Bruno in piazza", focal["activation_reason"])
        for global_collection in (
            "recent_memories",
            "beliefs",
            "relationships",
            "role_interpretations",
            "anamnesis_fragments",
            "reflections",
        ):
            self.assertNotIn(global_collection, focal)
        self.assertLess(
            len(json.dumps(focal, ensure_ascii=False)),
            len(json.dumps(full, ensure_ascii=False)) * 0.6,
        )

    def test_contextual_context_recovers_only_requested_focus(self) -> None:
        base = rich_context()
        contextual = build_private_context(
            replace(
                base,
                attention_level="contextual",
                attention_domains=("relationships", "memories", "plans"),
                attention_anchor_ids=("nwl-bruno",),
            )
        )

        self.assertEqual(
            ["nwl-bruno"],
            [item["agent_id"] for item in contextual["relationships"]],
        )
        self.assertEqual(
            ["memory-bruno"],
            [item["memory_id"] for item in contextual["recent_memories"]],
        )
        self.assertEqual(
            ["water-plan"],
            [item["plan_key"] for item in contextual["self"]["plans"]],
        )
        self.assertNotIn("anamnesis_fragments", contextual)

    def test_contextual_provenance_names_only_memories_in_the_working_set(self) -> None:
        base = rich_context()
        summaries = (
            "Bruno custodisce una mappa della sorgente.",
            "Ieri Bruno ha evitato il sentiero orientale.",
            "La borraccia di Bruno aveva un odore metallico.",
            "Bruno si fida della guardiana del pozzo.",
            "Al tramonto Bruno torna sempre verso la piazza.",
        )
        base.mind.memories.extend(
            Memory(
                f"memory-bruno-{index}",
                f"event-bruno-{index}",
                "AgentSpoke",
                summary,
                0.7,
                "curiosita",
                0.8,
                10 + index,
                participants=("nwl-bruno",),
            )
            for index, summary in enumerate(summaries)
        )
        focused = replace(
            base,
            attention_level="contextual",
            attention_domains=("memories",),
            attention_anchor_ids=("nwl-bruno",),
        )

        payload = build_private_context(focused)
        source_ids = set(visible_attention_source_ids(focused))
        visible_memories = payload["recent_memories"]
        included_ids = {
            identifier
            for memory in visible_memories
            for identifier in (
                memory["memory_id"],
                *memory["memory_ids"],
                *memory["source_event_ids"],
            )
        }
        all_memory_ids = {
            identifier
            for memory in base.mind.memories
            for identifier in (memory.memory_id, memory.source_event_id)
        }

        self.assertEqual(4, len(visible_memories))
        self.assertEqual(included_ids, source_ids & all_memory_ids)

    def test_reflective_context_can_recover_the_full_private_mind(self) -> None:
        reflective = build_private_context(
            replace(rich_context(), attention_level="reflective")
        )

        self.assertEqual(2, len(reflective["beliefs"]))
        self.assertEqual(2, len(reflective["relationships"]))
        self.assertEqual(2, len(reflective["recent_memories"]))
        self.assertEqual(1, len(reflective["anamnesis_fragments"]))

    def test_canonical_signals_set_a_minimum_level_without_selecting_action(self) -> None:
        base = rich_context()
        base.material_state.thirst = 0.95

        selection = minimum_attention_level(base)

        self.assertEqual("reflective", selection.level)
        self.assertIn("critical_somatic_state", selection.reasons)
        self.assertFalse(hasattr(selection, "action_type"))

    def test_repeated_rejections_promote_to_contextual_attention(self) -> None:
        base = rich_context()
        rejections = tuple(
            Observation(
                EventEnvelope(
                    event_type="ActionRejected",
                    world_tick=index,
                    world_time=world_time_for_tick(index),
                    actor_ids=(base.mind.agent_id,),
                    payload={"reason": "vincolo materiale"},
                    visibility="private",
                    recipient_ids=(base.mind.agent_id,),
                )
            )
            for index in (8, 9)
        )

        selection = minimum_attention_level(replace(base, observations=rejections))

        self.assertEqual("contextual", selection.level)
        self.assertIn("repeated_action_rejection", selection.reasons)

    def test_nearby_person_promotes_context_without_selecting_a_response(self) -> None:
        selection = minimum_attention_level(rich_context())

        self.assertEqual("contextual", selection.level)
        self.assertIn("nearby_agent", selection.reasons)
        self.assertFalse(hasattr(selection, "action_type"))

    def test_due_commitment_promotes_to_contextual_attention(self) -> None:
        context = replace(rich_context(), nearby_agents=(), world_tick=12)

        selection = minimum_attention_level(context)

        self.assertEqual("contextual", selection.level)
        self.assertIn("due_commitment", selection.reasons)

    def test_dispute_and_resonance_each_require_reflective_attention(self) -> None:
        base = replace(rich_context(), nearby_agents=())
        dispute = DisputeAffordance(
            "dispute-1",
            "nwl-bruno",
            base.mind.agent_id,
            "event-bruno",
            "open",
            None,
        )
        signal = Observation(
            EventEnvelope(
                event_type="ResonanceSignalReceived",
                world_tick=10,
                world_time=world_time_for_tick(10),
                actor_ids=(base.mind.agent_id,),
                payload={"node_id": "node-1"},
                visibility="private",
                recipient_ids=(base.mind.agent_id,),
            )
        )

        dispute_selection = minimum_attention_level(
            replace(base, active_disputes=(dispute,))
        )
        resonance_selection = minimum_attention_level(
            replace(base, observations=(signal,))
        )

        self.assertEqual("reflective", dispute_selection.level)
        self.assertIn("active_dispute", dispute_selection.reasons)
        self.assertEqual("reflective", resonance_selection.level)
        self.assertIn("resonance_signal", resonance_selection.reasons)


class ScriptedProgressiveProvider:
    def __init__(self, outputs: list[object]) -> None:
        self.outputs = outputs
        self.contexts: list[CognitionContext] = []

    def decide(self, context: CognitionContext):
        self.contexts.append(context)
        return self.outputs.pop(0)


def final_result() -> CognitionResult:
    return CognitionResult(
        intention=Intention(action_type="rest", motivation_summary="Scelta libera."),
        memory_appraisals=(),
        mental_updates=MentalUpdates(),
        attention_schedule=AttentionSchedule(3, "Riesaminare."),
        provider="scripted",
        model="scripted-model",
        inference_id="inference-progressive",
        attempts=1,
    )


class ProgressiveCognitionTests(unittest.TestCase):
    def test_mind_can_expand_context_before_choosing_an_action(self) -> None:
        provider = ScriptedProgressiveProvider(
            [
                ContextExpansionRequest(
                    domains=("relationships", "memories"),
                    anchor_ids=(),
                    reason="Voglio recuperare il contesto pertinente.",
                ),
                final_result(),
            ]
        )
        cognition = ProgressiveCognition(provider)

        context = replace(rich_context(), nearby_agents=())
        result = cognition.decide(context)

        self.assertEqual(["focal", "contextual"], [c.attention_level for c in provider.contexts])
        self.assertEqual("rest", result.intention.action_type)
        self.assertEqual("contextual", result.attention_level)
        self.assertEqual(1, result.attention_expansions)
        self.assertEqual(
            ("memories", "relationships"), result.attention_domains
        )
        self.assertIn("memory-bruno", result.attention_source_ids)

    def test_unknown_anchor_cannot_expand_private_context(self) -> None:
        provider = ScriptedProgressiveProvider(
            [
                ContextExpansionRequest(
                    domains=("memories",),
                    anchor_ids=("memory-forest",),
                    reason="Richiedo un identificatore che non vedo.",
                )
            ]
        )

        with self.assertRaises(CognitionUnavailable):
            ProgressiveCognition(provider).decide(rich_context())

        self.assertEqual(1, len(provider.contexts))

    def test_request_at_reflective_ceiling_defers_without_static_action(self) -> None:
        context = rich_context()
        context.material_state.thirst = 0.95
        provider = ScriptedProgressiveProvider(
            [
                ContextExpansionRequest(
                    domains=("memories",),
                    anchor_ids=(),
                    reason="Serve altro contesto.",
                )
            ]
        )

        with self.assertRaises(CognitionUnavailable):
            ProgressiveCognition(provider).decide(context)

        self.assertEqual("reflective", provider.contexts[0].attention_level)


class ProgressiveResponseContractTests(unittest.TestCase):
    def test_compact_contract_preserves_fields_and_enums_with_less_text(self) -> None:
        from newland_engine.cognition.schema import get_cognition_schema

        schema = progressive_response_schema(get_cognition_schema())
        compact = compact_schema_contract(schema)
        verbose = json.dumps(schema, ensure_ascii=False, separators=(",", ":"))

        self.assertLess(len(compact), len(verbose) * 0.65)
        for required_field in (
            "intention",
            "memory_appraisals",
            "mental_updates",
            "attention_schedule",
            "context_expansion",
            "source_event_id",
            "action_type",
        ):
            self.assertIn(required_field, compact)
        for action in ("speak", "consume", "attune_resonance"):
            self.assertIn(action, compact)
        self.assertIn("obj!{", compact)
        self.assertNotIn('"properties"', compact)

    def test_response_schema_accepts_either_decision_or_bounded_expansion(self) -> None:
        decision_schema = {
            "type": "object",
            "properties": {"intention": {"type": "object"}},
            "required": ["intention"],
        }

        schema = progressive_response_schema(decision_schema)

        self.assertEqual(2, len(schema["oneOf"]))
        expansion = schema["oneOf"][1]
        domains = expansion["properties"]["context_expansion"]["properties"]["domains"]
        self.assertEqual(
            {
                "memories",
                "relationships",
                "beliefs",
                "goals",
                "plans",
                "commitments",
                "roles",
                "anamnesis",
            },
            set(domains["items"]["enum"]),
        )

    def test_parser_rejects_unknown_expansion_domain(self) -> None:
        with self.assertRaises(ValueError):
            parse_context_expansion(
                {
                    "context_expansion": {
                        "domains": ["entire_world"],
                        "anchor_ids": [],
                        "reason": "Voglio sapere tutto.",
                    }
                }
            )


if __name__ == "__main__":
    unittest.main()
