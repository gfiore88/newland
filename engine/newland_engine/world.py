from __future__ import annotations

from typing import Any

from .models import (
    ActivityDefinition,
    EventEnvelope,
    Intention,
    MaterialAgentState,
    ResourceNode,
    WorldState,
    world_time_for_tick,
)


def reduce_event(state: WorldState, event: EventEnvelope) -> WorldState:
    state.tick = max(state.tick, event.world_tick)
    state.world_time = event.world_time

    if event.event_type in {
        "WorldInitialized",
        "TerritoryConfigured",
        "TerritoryActivitiesConfigured",
    }:
        _configure_territory(state, event.payload)
    elif event.event_type == "AgentRegistered":
        agent_id = event.actor_ids[0]
        native_language = str(event.payload.get("native_language", "und"))
        language_proficiencies = {
            key: float(value)
            for key, value in event.payload.get("language_proficiencies", {}).items()
        }
        if native_language != "und":
            language_proficiencies[native_language] = 1.0
        state.agents[agent_id] = MaterialAgentState(
            agent_id=agent_id,
            name=event.payload["name"],
            location=event.location or event.payload["location"],
            energy=float(event.payload.get("energy", 0.8)),
            hunger=float(event.payload.get("hunger", 0.1)),
            thirst=float(event.payload.get("thirst", 0.1)),
            native_language=native_language,
            language_proficiencies=language_proficiencies,
            skills={
                key: float(value)
                for key, value in event.payload.get("skills", {}).items()
            },
            family_group_id=event.payload.get("family_group_id"),
            inventory={
                key: float(value)
                for key, value in event.payload.get("inventory", {}).items()
            },
            inventory_capacity=float(event.payload.get("inventory_capacity", 20.0)),
        )
    elif event.event_type in {"FamilyGroupRegistered", "FamilyGroupUpdated"}:
        group_id = event.payload["family_group_id"]
        state.family_groups[group_id] = set(
            event.payload.get("member_ids", event.actor_ids)
        )
    elif event.event_type == "AgentCapabilitiesConfigured":
        agent = state.agents[event.actor_ids[0]]
        agent.native_language = event.payload["native_language"]
        agent.language_proficiencies = {
            key: float(value)
            for key, value in event.payload["language_proficiencies"].items()
        }
        agent.skills = {
            key: float(value) for key, value in event.payload["skills"].items()
        }
        agent.family_group_id = event.payload.get("family_group_id")
    elif event.event_type == "NeedsChanged":
        agent = state.agents[event.actor_ids[0]]
        agent.energy = float(event.payload["current"]["energy"])
        agent.hunger = float(event.payload["current"]["hunger"])
        agent.thirst = float(event.payload["current"]["thirst"])
    elif event.event_type == "AgentMoved":
        state.agents[event.actor_ids[0]].location = event.payload["destination"]
    elif event.event_type == "AgentRested":
        agent = state.agents[event.actor_ids[0]]
        agent.energy = min(
            1.0, agent.energy + float(event.payload.get("energy_recovered", 0.1))
        )
    elif event.event_type == "ResourceGathered":
        resource = state.resources[event.payload["resource_id"]]
        quantity = float(event.payload["quantity"])
        resource.quantity = max(0.0, resource.quantity - quantity)
        agent = state.agents[event.actor_ids[0]]
        kind = event.payload["resource_kind"]
        agent.inventory[kind] = agent.inventory.get(kind, 0.0) + quantity
    elif event.event_type == "ResourceConsumed":
        agent = state.agents[event.actor_ids[0]]
        kind = event.payload["resource_kind"]
        quantity = float(event.payload["quantity"])
        remaining = max(0.0, agent.inventory.get(kind, 0.0) - quantity)
        if remaining:
            agent.inventory[kind] = remaining
        else:
            agent.inventory.pop(kind, None)
        effects = event.payload.get("effects", {})
        agent.energy = min(1.0, agent.energy + float(effects.get("energy", 0.0)))
        agent.hunger = max(0.0, agent.hunger - float(effects.get("hunger", 0.0)))
        agent.thirst = max(0.0, agent.thirst - float(effects.get("thirst", 0.0)))
    elif event.event_type == "ActivityPerformed":
        agent = state.agents[event.actor_ids[0]]
        agent.energy = max(
            0.0, agent.energy - float(event.payload.get("energy_spent", 0.0))
        )
        practiced_skill = event.payload.get("practiced_skill")
        if practiced_skill:
            agent.skills[practiced_skill] = min(
                1.0,
                agent.skills.get(practiced_skill, 0.0)
                + float(event.payload.get("skill_gain", 0.0)),
            )
    return state


def _configure_territory(state: WorldState, payload: dict[str, Any]) -> None:
    if "locations" in payload:
        state.locations = {
            name: set(neighbors)
            for name, neighbors in payload.get("locations", {}).items()
        }
    if "resources" in payload:
        state.resources = {
            resource_id: ResourceNode(resource_id=resource_id, **definition)
            for resource_id, definition in payload.get("resources", {}).items()
        }
    if "resource_effects" in payload:
        state.resource_effects = {
            kind: {name: float(value) for name, value in effects.items()}
            for kind, effects in payload.get("resource_effects", {}).items()
        }
    if "activities" in payload:
        state.activities = {
            activity_id: ActivityDefinition(activity_id=activity_id, **definition)
            for activity_id, definition in payload.get("activities", {}).items()
        }


def replay(events: list[EventEnvelope]) -> WorldState:
    state = WorldState()
    for event in events:
        reduce_event(state, event)
    return state


class WorldAdjudicator:
    def adjudicate(
        self,
        state: WorldState,
        actor_id: str,
        intention: Intention,
        *,
        tick: int,
        cognition: dict[str, object] | None = None,
    ) -> list[EventEnvelope]:
        if actor_id not in state.agents:
            raise ValueError(f"unknown actor: {actor_id}")
        actor = state.agents[actor_id]
        world_time = world_time_for_tick(tick)
        proposal = EventEnvelope(
            event_type="ActionProposed",
            world_tick=tick,
            world_time=world_time,
            actor_ids=(actor_id,),
            location=actor.location,
            payload={**intention.to_dict(), "cognition": cognition or {}},
            visibility="private",
            recipient_ids=(actor_id,),
        )

        rejection = self._validate(state, actor_id, intention)
        if rejection:
            return [
                proposal,
                EventEnvelope(
                    event_type="ActionRejected",
                    world_tick=tick,
                    world_time=world_time,
                    actor_ids=(actor_id,),
                    location=actor.location,
                    payload={"reason": rejection, "action_type": intention.action_type},
                    visibility="private",
                    recipient_ids=(actor_id,),
                    causation_id=proposal.event_id,
                ),
            ]

        accepted = EventEnvelope(
            event_type="ActionAccepted",
            world_tick=tick,
            world_time=world_time,
            actor_ids=(actor_id,),
            location=actor.location,
            payload={"action_type": intention.action_type},
            visibility="private",
            recipient_ids=(actor_id,),
            causation_id=proposal.event_id,
        )
        recipients = state.agents_at(actor.location)
        consequences = self._consequences(
            state,
            actor_id,
            intention,
            tick=tick,
            world_time=world_time,
            recipients=recipients,
            causation_id=accepted.event_id,
        )
        return [proposal, accepted, *consequences]

    @staticmethod
    def _validate(state: WorldState, actor_id: str, intention: Intention) -> str | None:
        actor = state.agents[actor_id]
        if intention.action_type in {"speak", "offer_help"} and intention.target_id:
            target = state.agents.get(intention.target_id)
            if target is None:
                return "target does not exist"
            if target.location != actor.location:
                return "target is not present at actor location"
        if intention.action_type == "move":
            if intention.destination not in state.locations:
                return "destination does not exist"
            if intention.destination not in state.locations.get(actor.location, set()):
                return "destination is not adjacent"
        if intention.action_type == "speak" and not intention.target_id:
            return "speech requires a target"
        if intention.action_type == "speak":
            proficiency = actor.language_proficiencies.get(
                intention.language or "", 0.0
            )
            if proficiency <= 0.0:
                return "actor cannot speak the selected language"
        if intention.action_type == "offer_help" and not intention.target_id:
            return "help requires a target"
        if intention.action_type == "gather":
            resource = state.resources.get(intention.resource_id or "")
            if resource is None:
                return "resource does not exist"
            if resource.location != actor.location:
                return "resource is not present at actor location"
            if (intention.quantity or 0.0) > resource.quantity:
                return "requested quantity is not available"
            carried = sum(actor.inventory.values())
            if carried + float(intention.quantity or 0.0) > actor.inventory_capacity:
                return "inventory capacity would be exceeded"
        if intention.action_type == "consume":
            resource_kind = intention.resource_id or ""
            if resource_kind not in state.resource_effects:
                return "resource is not consumable"
            if (intention.quantity or 0.0) > actor.inventory.get(resource_kind, 0.0):
                return "requested quantity is not in inventory"
        if intention.action_type == "perform_activity":
            activity = state.activities.get(intention.activity_id or "")
            if activity is None:
                return "activity does not exist"
            if activity.location != actor.location:
                return "activity is not available at actor location"
            energy_cost = activity.energy_cost * (intention.duration_minutes / 10.0)
            if energy_cost > actor.energy:
                return "actor does not have enough energy for activity"
            if activity.practiced_skill:
                proficiency = actor.skills.get(activity.practiced_skill, 0.0)
                if proficiency < activity.minimum_proficiency:
                    return "actor lacks the required skill proficiency"
        return None

    @staticmethod
    def _consequences(
        state: WorldState,
        actor_id: str,
        intention: Intention,
        *,
        tick: int,
        world_time: str,
        recipients: tuple[str, ...],
        causation_id: str,
    ) -> list[EventEnvelope]:
        actor = state.agents[actor_id]
        common = {
            "world_tick": tick,
            "world_time": world_time,
            "actor_ids": (actor_id,),
            "location": actor.location,
            "visibility": "local",
            "recipient_ids": recipients,
            "causation_id": causation_id,
        }
        if intention.action_type == "speak":
            return [
                EventEnvelope(
                    event_type="SpeechUttered",
                    payload={
                        "target_id": intention.target_id,
                        "content": intention.spoken_content,
                        "language": intention.language,
                    },
                    **common,
                )
            ]
        if intention.action_type == "offer_help":
            return [
                EventEnvelope(
                    event_type="HelpOffered",
                    payload={
                        "target_id": intention.target_id,
                        "duration_minutes": intention.duration_minutes,
                    },
                    **common,
                )
            ]
        if intention.action_type == "rest":
            return [
                EventEnvelope(
                    event_type="AgentRested",
                    payload={
                        "duration_minutes": intention.duration_minutes,
                        "energy_recovered": min(0.25, intention.duration_minutes / 240),
                    },
                    **common,
                )
            ]
        if intention.action_type == "move":
            destination = intention.destination
            destination_recipients = tuple(
                sorted(set(recipients) | set(state.agents_at(destination or "")))
            )
            return [
                EventEnvelope(
                    event_type="AgentMoved",
                    world_tick=tick,
                    world_time=world_time,
                    actor_ids=(actor_id,),
                    location=actor.location,
                    payload={"origin": actor.location, "destination": destination},
                    visibility="local",
                    recipient_ids=destination_recipients,
                    causation_id=causation_id,
                )
            ]
        if intention.action_type == "gather":
            resource = state.resources[intention.resource_id or ""]
            return [
                EventEnvelope(
                    event_type="ResourceGathered",
                    payload={
                        "resource_id": resource.resource_id,
                        "resource_kind": resource.kind,
                        "label": resource.label,
                        "quantity": intention.quantity,
                        "unit": resource.unit,
                    },
                    **common,
                )
            ]
        if intention.action_type == "consume":
            resource_kind = intention.resource_id or ""
            quantity = float(intention.quantity or 0.0)
            unit_effects = state.resource_effects[resource_kind]
            return [
                EventEnvelope(
                    event_type="ResourceConsumed",
                    payload={
                        "resource_kind": resource_kind,
                        "quantity": quantity,
                        "effects": {
                            key: value * quantity for key, value in unit_effects.items()
                        },
                    },
                    **common,
                )
            ]
        if intention.action_type == "perform_activity":
            activity = state.activities[intention.activity_id or ""]
            return [
                EventEnvelope(
                    event_type="ActivityPerformed",
                    payload={
                        "activity_id": activity.activity_id,
                        "label": activity.label,
                        "duration_minutes": intention.duration_minutes,
                        "energy_spent": min(
                            1.0,
                            activity.energy_cost * (intention.duration_minutes / 10.0),
                        ),
                        "practiced_skill": activity.practiced_skill,
                        "skill_gain": activity.skill_gain,
                    },
                    **common,
                )
            ]
        raise ValueError(f"unsupported action: {intention.action_type}")
