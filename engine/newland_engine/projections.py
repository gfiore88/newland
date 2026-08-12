from __future__ import annotations

from typing import Any

from .models import EventEnvelope, WorldState


def event_projection(event: EventEnvelope) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "sequence": event.sequence,
        "schema_version": event.schema_version,
        "world_tick": event.world_tick,
        "world_time": event.world_time,
        "event_type": event.event_type,
        "actor_ids": event.actor_ids,
        "location": event.location,
        "payload": event.payload,
        "visibility": event.visibility,
        "recipient_ids": event.recipient_ids,
        "causation_id": event.causation_id,
    }


def world_projection(state: WorldState) -> dict[str, Any]:
    return {
        "tick": state.tick,
        "world_time": state.world_time,
        "locations": {
            location: sorted(neighbors)
            for location, neighbors in state.locations.items()
        },
        "agents": {
            agent_id: {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "location": agent.location,
                "energy": agent.energy,
                "hunger": agent.hunger,
                "thirst": agent.thirst,
                "native_language": agent.native_language,
                "language_proficiencies": agent.language_proficiencies,
                "skills": agent.skills,
                "family_group_id": agent.family_group_id,
                "inventory": agent.inventory,
                "inventory_capacity": agent.inventory_capacity,
                "active": agent.active,
            }
            for agent_id, agent in state.agents.items()
        },
        "resources": {
            resource_id: {
                "resource_id": resource.resource_id,
                "kind": resource.kind,
                "label": resource.label,
                "location": resource.location,
                "quantity": resource.quantity,
                "unit": resource.unit,
                "renewable": resource.renewable,
            }
            for resource_id, resource in state.resources.items()
        },
        "activities": {
            activity_id: {
                "activity_id": activity.activity_id,
                "label": activity.label,
                "location": activity.location,
                "energy_cost": activity.energy_cost,
                "practiced_skill": activity.practiced_skill,
                "minimum_proficiency": activity.minimum_proficiency,
                "skill_gain": activity.skill_gain,
            }
            for activity_id, activity in state.activities.items()
        },
        "resonance_nodes": {
            node_id: {
                "node_id": node.node_id,
                "label": node.label,
                "location": node.location,
                "intensity": node.intensity,
            }
            for node_id, node in state.resonance_nodes.items()
        },
        "family_groups": {
            group_id: sorted(members)
            for group_id, members in state.family_groups.items()
        },
        "cooperations": {
            proposal_id: {
                "proposal_id": cooperation.proposal_id,
                "proposer_id": cooperation.proposer_id,
                "target_id": cooperation.target_id,
                "activity_id": cooperation.activity_id,
                "status": cooperation.status,
                "created_tick": cooperation.created_tick,
                "response_tick": cooperation.response_tick,
            }
            for proposal_id, cooperation in state.cooperations.items()
        },
        "disputes": {
            dispute_id: {
                "dispute_id": dispute.dispute_id,
                "opener_id": dispute.opener_id,
                "target_id": dispute.target_id,
                "subject_event_id": dispute.subject_event_id,
                "status": dispute.status,
                "created_tick": dispute.created_tick,
                "resolution_offered_by": dispute.resolution_offered_by,
            }
            for dispute_id, dispute in state.disputes.items()
        },
    }
