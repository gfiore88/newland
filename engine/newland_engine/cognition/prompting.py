from typing import Any
from .types import CognitionContext
from .retrieval import retrieve_memories
from ..physiology import project_somatic_state
from .prompt_registry import PromptRegistry
from .schema import DEFAULT_PROMPT_REGISTRY
from .attention import select_attention_context


def build_system_prompt() -> str:
    """Compatibility accessor; the prompt source is the external registry."""
    return PromptRegistry(DEFAULT_PROMPT_REGISTRY).snapshot().system_prompt


def build_private_context(context: CognitionContext) -> dict[str, Any]:
    full_context = {
        "self": {
            "agent_id": context.mind.agent_id,
            "name": context.mind.name,
            "values": context.mind.values,
            "temperament": context.mind.temperament,
            "needs": {
                "energy": context.material_state.energy,
                "hunger": context.material_state.hunger,
                "thirst": context.material_state.thirst,
            },
            "somatic_state": project_somatic_state(context.material_state),
            "affect": context.mind.affect,
            "goals": context.mind.goals,
            "plans": [
                {
                    "plan_key": plan.plan_key,
                    "description": plan.description,
                    "steps": plan.steps,
                    "status": plan.status,
                }
                for plan in context.mind.plans.values()
            ],
            "commitments": [
                {
                    "commitment_key": commitment.commitment_key,
                    "description": commitment.description,
                    "due_tick": commitment.due_tick,
                    "involved_agent_ids": commitment.involved_agent_ids,
                    "status": commitment.status,
                }
                for commitment in context.mind.commitments.values()
            ],
            "inventory": context.material_state.inventory,
            "inventory_capacity": context.material_state.inventory_capacity,
            "native_language": context.material_state.native_language,
            "language_proficiencies": context.material_state.language_proficiencies,
            "skills": context.material_state.skills,
            "family_group_id": context.material_state.family_group_id,
            "location": context.material_state.location,
        },
        "local_affordances": {
            "adjacent_locations": context.adjacent_locations,
            "resources": [
                {
                    "resource_id": resource.resource_id,
                    "kind": resource.kind,
                    "label": resource.label,
                    "quantity": resource.quantity,
                    "unit": resource.unit,
                }
                for resource in context.local_resources
            ],
            "activities": [
                {
                    "activity_id": activity.activity_id,
                    "label": activity.label,
                    "practiced_skill": activity.practiced_skill,
                    "minimum_proficiency": activity.minimum_proficiency,
                    "energy_cost_per_10_minutes": activity.energy_cost_per_10_minutes,
                }
                for activity in context.available_activities
            ],
            "resonance_nodes": [
                {
                    "node_id": node.node_id,
                    "label": node.label,
                    "intensity": node.intensity,
                }
                for node in context.local_resonance_nodes
            ],
        },
        "action_contracts": context.action_contracts,
        "social_affordances": {
            "cooperations": [
                {
                    "proposal_id": proposal.proposal_id,
                    "proposer_id": proposal.proposer_id,
                    "target_id": proposal.target_id,
                    "activity_id": proposal.activity_id,
                    "status": proposal.status,
                }
                for proposal in context.social_proposals
            ],
            "disputes": [
                {
                    "dispute_id": dispute.dispute_id,
                    "opener_id": dispute.opener_id,
                    "target_id": dispute.target_id,
                    "subject_event_id": dispute.subject_event_id,
                    "status": dispute.status,
                    "resolution_offered_by": dispute.resolution_offered_by,
                }
                for dispute in context.active_disputes
            ],
        },
        "world_tick": context.world_tick,
        "activation_reason": context.activation_reason,
        "recent_memories": [
            {
                "memory_id": memory.memory_id,
                "summary": memory.summary,
                "salience": memory.salience,
                "emotional_tone": memory.emotional_tone,
                "confidence": memory.confidence,
                "occurrence_count": memory.occurrence_count,
                "memory_ids": list(memory.memory_ids),
                "source_event_ids": list(memory.source_event_ids),
            }
            for memory in retrieve_memories(context)
        ],
        "beliefs": [
            {
                "key": belief.key,
                "statement": belief.statement,
                "confidence": belief.confidence,
            }
            for belief in context.mind.beliefs.values()
        ],
        "relationships": [
            {
                "agent_id": relationship.agent_id,
                "familiarity": relationship.familiarity,
                "trust": relationship.trust,
                "warmth": relationship.warmth,
                "tension": relationship.tension,
            }
            for relationship in context.mind.relationships.values()
        ],
        "role_interpretations": [
            {
                "interpretation_key": role.interpretation_key,
                "subject_agent_id": role.subject_agent_id,
                "role_label": role.role_label,
                "interpretation": role.interpretation,
                "confidence": role.confidence,
            }
            for role in context.mind.role_interpretations.values()
        ],
        "anamnesis_fragments": [
            {
                "fragment_key": fragment.fragment_key,
                "phenomenon_label": fragment.phenomenon_label,
                "content": fragment.content,
                "interpretation": fragment.interpretation,
                "confidence": fragment.confidence,
            }
            for fragment in context.mind.anamnesis_fragments.values()
        ],
        "resonance_orientation": (
            {
                "receptive": context.mind.resonance_orientation.receptive,
                "interpretation": context.mind.resonance_orientation.interpretation,
            }
            if context.mind.resonance_orientation is not None
            else None
        ),
        "reflections": [
            {
                "statement": reflection.statement,
                "confidence": reflection.confidence,
            }
            for reflection in context.mind.reflections[-6:]
        ],
        "observations": [
            {
                "event_id": item.event.event_id,
                "event_type": item.event.event_type,
                "actor_ids": item.event.actor_ids,
                "location": item.event.location,
                "payload": item.event.payload,
            }
            for item in context.observations
        ],
        "nearby_agents": [
            {"agent_id": agent_id, "name": name}
            for agent_id, name in context.nearby_agents
        ],
    }
    return select_attention_context(full_context, context)
