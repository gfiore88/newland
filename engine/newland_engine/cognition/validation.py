from .types import CognitionContext, CognitionResult, MemoryAppraisal, MentalUpdates
from ..models import Intention


def validate_cognition_result(
    result: CognitionResult, context: CognitionContext
) -> None:
    validate_appraisals(result.memory_appraisals, context)
    validate_mental_updates(result.mental_updates, context)
    validate_intention_context(result.intention, context)


def validate_appraisals(
    appraisals: tuple[MemoryAppraisal, ...], context: CognitionContext
) -> None:
    visible_ids = {
        observation.event.event_id for observation in context.observations
    }
    source_ids = [appraisal.source_event_id for appraisal in appraisals]
    unknown = set(source_ids) - visible_ids
    if unknown:
        raise ValueError(
            f"memory appraisals reference unobserved events: {sorted(unknown)}"
        )
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("memory appraisals contain duplicate source events")


def validate_mental_updates(
    updates: MentalUpdates, context: CognitionContext
) -> None:
    visible_ids = {
        observation.event.event_id for observation in context.observations
    }
    memory_ids = {memory.memory_id for memory in context.mind.memories}
    perceived_agents = {
        actor_id
        for observation in context.observations
        for actor_id in observation.event.actor_ids
    }
    for observation in context.observations:
        target_id = observation.event.payload.get("target_id")
        if isinstance(target_id, str):
            perceived_agents.add(target_id)
    known_agents = (
        perceived_agents
        | set(context.mind.relationships)
        | {agent_id for agent_id, _ in context.nearby_agents}
    ) - {context.mind.agent_id}

    sourced_updates: list[object] = [
        *updates.beliefs,
        *updates.relationships,
        *updates.reflections,
        *updates.goals,
        *updates.plans,
        *updates.commitments,
        *updates.role_interpretations,
        *updates.anamnesis_fragments,
    ]
    if updates.affect is not None:
        sourced_updates.append(updates.affect)
    if updates.resonance_orientation is not None:
        sourced_updates.append(updates.resonance_orientation)
    for update in sourced_updates:
        source_events = set(update.source_event_ids)
        source_memories = set(update.source_memory_ids)
        if not source_events and not source_memories:
            raise ValueError("mental updates require event or memory provenance")
        if source_events - visible_ids:
            raise ValueError("mental update references unobserved events")
        if source_memories - memory_ids:
            raise ValueError("mental update references unknown memories")
    for relationship in updates.relationships:
        if relationship.other_agent_id not in known_agents:
            raise ValueError("relationship update references an unknown agent")
    role_subjects = known_agents | {context.mind.agent_id}
    for role in updates.role_interpretations:
        if role.subject_agent_id not in role_subjects:
            raise ValueError("role interpretation references an unknown agent")
        if (
            role.operation == "remove"
            and role.interpretation_key not in context.mind.role_interpretations
        ):
            raise ValueError("role revision references an unknown interpretation")
    resonance_event_ids = {
        observation.event.event_id
        for observation in context.observations
        if observation.event.event_type == "ResonanceSignalReceived"
    }
    resonance_memory_ids = {
        memory.memory_id
        for memory in context.mind.memories
        if memory.event_type == "ResonanceSignalReceived"
    }
    resonance_updates: list[object] = [*updates.anamnesis_fragments]
    if updates.resonance_orientation is not None:
        resonance_updates.append(updates.resonance_orientation)
    for update in resonance_updates:
        if not (
            set(update.source_event_ids) & resonance_event_ids
            or set(update.source_memory_ids) & resonance_memory_ids
        ):
            raise ValueError("mental updates require resonance provenance")
    for plan in updates.plans:
        if plan.operation != "upsert" and plan.plan_key not in context.mind.plans:
            raise ValueError("plan revision references an unknown plan")
    for commitment in updates.commitments:
        unknown_agents = set(commitment.involved_agent_ids) - known_agents
        if unknown_agents:
            raise ValueError("commitment references unknown agents")
        if (
            commitment.operation == "add"
            and commitment.due_tick < context.world_tick
        ):
            raise ValueError("new commitment cannot be due in the past")
        if (
            commitment.operation != "add"
            and commitment.commitment_key not in context.mind.commitments
        ):
            raise ValueError("commitment revision references an unknown commitment")


def validate_intention_context(
    intention: Intention, context: CognitionContext
) -> None:
    nearby_ids = {agent_id for agent_id, _ in context.nearby_agents}
    if (
        intention.action_type
        in {
            "speak",
            "offer_help",
            "propose_cooperation",
            "open_dispute",
        }
        and intention.target_id not in nearby_ids
    ):
        raise ValueError(
            "social intention targets an agent outside local perception"
        )
    if (
        intention.action_type
        in {
            "speak",
            "propose_cooperation",
            "respond_cooperation",
            "open_dispute",
            "respond_dispute",
        }
        and context.material_state.language_proficiencies.get(
            intention.language or "", 0.0
        )
        <= 0.0
    ):
        raise ValueError("social intention uses an unknown language")

    proposal_ids = {proposal.proposal_id for proposal in context.social_proposals}
    if (
        intention.action_type in {"respond_cooperation", "perform_cooperation"}
        and intention.proposal_id not in proposal_ids
    ):
        raise ValueError("cooperation intention references an unknown proposal")

    dispute_ids = {dispute.dispute_id for dispute in context.active_disputes}
    if (
        intention.action_type == "respond_dispute"
        and intention.dispute_id not in dispute_ids
    ):
        raise ValueError("dispute response references an unknown dispute")
    if intention.action_type == "open_dispute":
        known_event_ids = {
            observation.event.event_id for observation in context.observations
        } | {memory.source_event_id for memory in context.mind.memories}
        if intention.subject_event_id not in known_event_ids:
            raise ValueError("dispute references an event unknown to the agent")
    node_ids = {node.node_id for node in context.local_resonance_nodes}
    if (
        intention.action_type == "attune_resonance"
        and intention.node_id not in node_ids
    ):
        raise ValueError("resonance intention references a non-local node")
