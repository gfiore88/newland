from __future__ import annotations

import math
from typing import Any

from .models import (
    ActivityDefinition,
    CooperationState,
    DisputeState,
    EventEnvelope,
    Intention,
    MaterialAgentState,
    PendingAction,
    ResonanceNode,
    ResourceNode,
    WorldState,
    world_time_for_tick,
)
from .physiology import somatic_condition_for


def _record_instant_somatic_change(
    agent: MaterialAgentState, previous: dict[str, float]
) -> None:
    exposure_fields = {
        "energy": "exhaustion_ticks",
        "hunger": "starvation_ticks",
        "thirst": "dehydration_ticks",
    }
    for need in ("energy", "hunger", "thirst"):
        before = previous[need]
        after = float(getattr(agent, need))
        if after == before:
            continue
        agent.need_trends[need] = "rising" if after > before else "falling"
        if somatic_condition_for(need, before) != somatic_condition_for(need, after):
            agent.somatic_condition_ticks[need] = 0
        if somatic_condition_for(need, after) != "fatal":
            setattr(agent, exposure_fields[need], 0)


def reduce_event(state: WorldState, event: EventEnvelope) -> WorldState:
    state.event_ids.add(event.event_id)
    state.event_witnesses[event.event_id] = set(event.actor_ids) | set(
        event.recipient_ids
    )
    state.tick = max(state.tick, event.world_tick)
    state.world_time = event.world_time

    if event.event_type in {
        "WorldInitialized",
        "TerritoryConfigured",
        "TerritoryActivitiesConfigured",
        "ResonanceNodesConfigured",
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
        fatal_exposure_ticks = event.payload.get("fatal_exposure_ticks")
        if fatal_exposure_ticks is not None:
            agent.exhaustion_ticks = int(fatal_exposure_ticks["exhaustion"])
            agent.starvation_ticks = int(fatal_exposure_ticks["starvation"])
            agent.dehydration_ticks = int(fatal_exposure_ticks["dehydration"])
        somatic_condition_ticks = event.payload.get("somatic_condition_ticks")
        if somatic_condition_ticks is not None:
            agent.somatic_condition_ticks = {
                need: int(duration)
                for need, duration in somatic_condition_ticks.items()
            }
        need_trends = event.payload.get("need_trends")
        if need_trends is not None:
            agent.need_trends = {
                need: str(trend) for need, trend in need_trends.items()
            }
    elif event.event_type == "AgentDied":
        agent = state.agents[event.actor_ids[0]]
        agent.is_dead = True
        agent.active = False
        agent.pending_action = None
        agent.current_action = None
    elif event.event_type == "AgentMoved":
        state.agents[event.actor_ids[0]].location = event.payload["destination"]
    elif event.event_type == "AgentRested":
        agent = state.agents[event.actor_ids[0]]
        previous = {"energy": agent.energy, "hunger": agent.hunger, "thirst": agent.thirst}
        agent.energy = min(
            1.0, agent.energy + float(event.payload.get("energy_recovered", 0.1))
        )
        _record_instant_somatic_change(agent, previous)
    elif event.event_type == "ResourceGathered":
        resource = state.resources[event.payload["resource_id"]]
        quantity = float(event.payload["quantity"])
        resource.quantity = max(0.0, resource.quantity - quantity)
        agent = state.agents[event.actor_ids[0]]
        kind = event.payload["resource_kind"]
        agent.inventory[kind] = agent.inventory.get(kind, 0.0) + quantity
    elif event.event_type == "ResourceConsumed":
        agent = state.agents[event.actor_ids[0]]
        previous = {"energy": agent.energy, "hunger": agent.hunger, "thirst": agent.thirst}
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
        _record_instant_somatic_change(agent, previous)
    elif event.event_type == "ActivityPerformed":
        agent = state.agents[event.actor_ids[0]]
        previous = {"energy": agent.energy, "hunger": agent.hunger, "thirst": agent.thirst}
        agent.energy = max(
            0.0, agent.energy - float(event.payload.get("energy_spent", 0.0))
        )
        _record_instant_somatic_change(agent, previous)
        practiced_skill = event.payload.get("practiced_skill")
        if practiced_skill:
            agent.skills[practiced_skill] = min(
                1.0,
                agent.skills.get(practiced_skill, 0.0)
                + float(event.payload.get("skill_gain", 0.0)),
            )
    elif event.event_type == "CooperationProposed":
        state.cooperations[event.event_id] = CooperationState(
            proposal_id=event.event_id,
            proposer_id=event.actor_ids[0],
            target_id=event.payload["target_id"],
            activity_id=event.payload["activity_id"],
            status="pending",
            created_tick=event.world_tick,
        )
    elif event.event_type == "CooperationResponded":
        cooperation = state.cooperations[event.payload["proposal_id"]]
        cooperation.status = (
            "accepted" if event.payload["response"] == "accept" else "declined"
        )
        cooperation.response_tick = event.world_tick
    elif event.event_type == "CooperationPerformed":
        cooperation = state.cooperations[event.payload["proposal_id"]]
        cooperation.status = "completed"
        for agent_id in event.actor_ids:
            agent = state.agents[agent_id]
            agent.energy = max(
                0.0, agent.energy - float(event.payload.get("energy_spent_each", 0.0))
            )
            practiced_skill = event.payload.get("practiced_skill")
            if practiced_skill:
                agent.skills[practiced_skill] = min(
                    1.0,
                    agent.skills.get(practiced_skill, 0.0)
                    + float(event.payload.get("skill_gain_each", 0.0)),
                )
    elif event.event_type == "ActionAccepted":
        agent = state.agents[event.actor_ids[0]]
        agent.current_action = event.payload.get("action_type")
    elif event.event_type == "ActionStarted":
        agent = state.agents[event.actor_ids[0]]
        agent.pending_action = PendingAction(
            action_id=event.event_id,
            intention=Intention(**event.payload["intention"]),
            started_tick=event.world_tick,
            completion_tick=int(event.payload["completion_tick"]),
        )
    elif event.event_type in {"ActionCompleted", "ActionInterrupted"}:
        agent = state.agents[event.actor_ids[0]]
        agent.pending_action = None
        agent.current_action = None
    elif event.event_type == "DisputeOpened":
        state.disputes[event.event_id] = DisputeState(
            dispute_id=event.event_id,
            opener_id=event.actor_ids[0],
            target_id=event.payload["target_id"],
            subject_event_id=event.payload["subject_event_id"],
            status="open",
            created_tick=event.world_tick,
        )
    elif event.event_type == "DisputeResponded":
        dispute = state.disputes[event.payload["dispute_id"]]
        response = event.payload["response"]
        if response == "offer_resolution":
            dispute.status = "resolution_offered"
            dispute.resolution_offered_by = event.actor_ids[0]
        elif response == "accept_resolution":
            dispute.status = "resolved"
        else:
            dispute.status = "open"
            dispute.resolution_offered_by = None
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
    if "resonance_nodes" in payload:
        state.resonance_nodes = {
            node_id: ResonanceNode(node_id=node_id, **definition)
            for node_id, definition in payload.get("resonance_nodes", {}).items()
        }


def replay(events: list[EventEnvelope]) -> WorldState:
    state = WorldState()
    for event in events:
        reduce_event(state, event)
    return state


class WorldAdjudicator:
    TICK_MINUTES = 10
    REST_ENERGY_PER_MINUTE = 0.03

    @classmethod
    def action_contracts(cls, state: WorldState) -> dict[str, object]:
        return {
            "tick_minutes": cls.TICK_MINUTES,
            "duration_semantics": (
                "accepted actions complete only after their duration has elapsed"
            ),
            "rest": {
                "energy_recovered_per_minute": cls.REST_ENERGY_PER_MINUTE
            },
            "consumables": {
                kind: dict(effects)
                for kind, effects in state.resource_effects.items()
            },
        }

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

    def begin_action(
        self,
        state: WorldState,
        actor_id: str,
        intention: Intention,
        *,
        tick: int,
        cognition: dict[str, object] | None = None,
    ) -> list[EventEnvelope]:
        adjudicated = self.adjudicate(
            state,
            actor_id,
            intention,
            tick=tick,
            cognition=cognition,
        )
        if adjudicated[-1].event_type == "ActionRejected":
            return adjudicated

        proposal, accepted = adjudicated[:2]
        duration_ticks = max(
            1, math.ceil(intention.duration_minutes / self.TICK_MINUTES)
        )
        started = EventEnvelope(
            event_type="ActionStarted",
            world_tick=tick,
            world_time=world_time_for_tick(tick),
            actor_ids=(actor_id,),
            location=state.agents[actor_id].location,
            payload={
                "action_type": intention.action_type,
                "intention": intention.to_dict(),
                "completion_tick": tick + duration_ticks,
            },
            visibility="private",
            recipient_ids=(actor_id,),
            causation_id=accepted.event_id,
        )
        return [proposal, accepted, started]

    def complete_action(
        self,
        state: WorldState,
        actor_id: str,
        pending: PendingAction,
        *,
        tick: int,
    ) -> list[EventEnvelope]:
        intention = pending.intention
        rejection = self._validate(state, actor_id, intention)
        if rejection:
            return [
                EventEnvelope(
                    event_type="ActionInterrupted",
                    world_tick=tick,
                    world_time=world_time_for_tick(tick),
                    actor_ids=(actor_id,),
                    location=state.agents[actor_id].location,
                    payload={
                        "action_type": intention.action_type,
                        "reason": rejection,
                    },
                    visibility="private",
                    recipient_ids=(actor_id,),
                    causation_id=pending.action_id,
                )
            ]

        actor = state.agents[actor_id]
        consequences = self._consequences(
            state,
            actor_id,
            intention,
            tick=tick,
            world_time=world_time_for_tick(tick),
            recipients=state.agents_at(actor.location),
            causation_id=pending.action_id,
        )
        completed = EventEnvelope(
            event_type="ActionCompleted",
            world_tick=tick,
            world_time=world_time_for_tick(tick),
            actor_ids=(actor_id,),
            location=actor.location,
            payload={"action_type": intention.action_type},
            visibility="private",
            recipient_ids=(actor_id,),
            causation_id=pending.action_id,
        )
        return [*consequences, completed]

    @staticmethod
    def _validate(state: WorldState, actor_id: str, intention: Intention) -> str | None:
        actor = state.agents[actor_id]
        targeted_actions = {
            "speak",
            "offer_help",
            "propose_cooperation",
            "open_dispute",
        }
        if intention.action_type in targeted_actions and intention.target_id:
            target = state.agents.get(intention.target_id)
            if target is None:
                return "target does not exist"
            if target.location != actor.location:
                return "target is not present at actor location"
            if target.agent_id == actor_id:
                return "social action cannot target the actor"
        if intention.action_type == "move":
            if intention.destination not in state.locations:
                return "destination does not exist"
            if intention.destination not in state.locations.get(actor.location, set()):
                return "destination is not adjacent"
        if intention.action_type == "speak" and not intention.target_id:
            return "speech requires a target"
        communicative_actions = {
            "speak",
            "propose_cooperation",
            "respond_cooperation",
            "open_dispute",
            "respond_dispute",
        }
        if intention.action_type in communicative_actions:
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
        if intention.action_type == "attune_resonance":
            node = state.resonance_nodes.get(intention.node_id or "")
            if node is None:
                return "resonance node does not exist"
            if node.location != actor.location:
                return "resonance node is not present at actor location"
        if intention.action_type == "propose_cooperation":
            activity = state.activities.get(intention.activity_id or "")
            if activity is None:
                return "cooperative activity does not exist"
            if activity.location != actor.location:
                return "cooperative activity is not available at actor location"
        if intention.action_type == "respond_cooperation":
            cooperation = state.cooperations.get(intention.proposal_id or "")
            if cooperation is None:
                return "cooperation proposal does not exist"
            if cooperation.status != "pending":
                return "cooperation proposal is no longer pending"
            if cooperation.target_id != actor_id:
                return "only the proposal target may respond"
            if state.agents[cooperation.proposer_id].location != actor.location:
                return "cooperation proposer is not present"
        if intention.action_type == "perform_cooperation":
            cooperation = state.cooperations.get(intention.proposal_id or "")
            if cooperation is None:
                return "cooperation proposal does not exist"
            if cooperation.status != "accepted":
                return "cooperation has not been accepted"
            if actor_id not in {cooperation.proposer_id, cooperation.target_id}:
                return "only a cooperation participant may initiate the activity"
            partner_id = (
                cooperation.target_id
                if actor_id == cooperation.proposer_id
                else cooperation.proposer_id
            )
            partner = state.agents[partner_id]
            if partner.location != actor.location:
                return "cooperation partner is not present"
            activity = state.activities.get(cooperation.activity_id)
            if activity is None:
                return "cooperative activity no longer exists"
            if activity.location != actor.location:
                return "cooperative activity is not available at actor location"
            for participant in (actor, partner):
                energy_cost = activity.energy_cost * (intention.duration_minutes / 10.0)
                if energy_cost > participant.energy:
                    return "a participant does not have enough energy"
                if (
                    activity.practiced_skill
                    and participant.skills.get(activity.practiced_skill, 0.0)
                    < activity.minimum_proficiency
                ):
                    return "a participant lacks the required skill proficiency"
        if intention.action_type == "open_dispute":
            if intention.subject_event_id not in state.event_ids:
                return "dispute subject event does not exist"
            witnesses = state.event_witnesses.get(
                intention.subject_event_id or "", set()
            )
            if actor_id not in witnesses:
                return "actor did not perceive the dispute subject event"
        if intention.action_type == "respond_dispute":
            dispute = state.disputes.get(intention.dispute_id or "")
            if dispute is None:
                return "dispute does not exist"
            if actor_id not in {dispute.opener_id, dispute.target_id}:
                return "only dispute participants may respond"
            counterpart_id = (
                dispute.target_id
                if actor_id == dispute.opener_id
                else dispute.opener_id
            )
            if state.agents[counterpart_id].location != actor.location:
                return "dispute counterpart is not present"
            if dispute.status == "resolved":
                return "dispute is already resolved"
            if intention.response == "offer_resolution" and dispute.status != "open":
                return "a resolution is already pending"
            if intention.response == "accept_resolution":
                if dispute.status != "resolution_offered":
                    return "no resolution is pending"
                if dispute.resolution_offered_by == actor_id:
                    return "an agent cannot accept its own resolution offer"
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
                        "energy_recovered": min(
                            1.0,
                            intention.duration_minutes
                            * WorldAdjudicator.REST_ENERGY_PER_MINUTE,
                        ),
                    },
                    **common,
                )
            ]
        if intention.action_type == "move":
            destination = intention.destination
            destination_recipients = tuple(
                sorted(set(recipients) | set(state.agents_at(destination or "")))
            )
            events = [
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
            events.extend(
                EventEnvelope(
                    event_type="ResonanceSignalReceived",
                    world_tick=tick,
                    world_time=world_time,
                    actor_ids=(actor_id,),
                    location=destination,
                    payload={
                        "node_id": node.node_id,
                        "intensity": node.intensity,
                        "exposure_mode": "arrival",
                    },
                    visibility="private",
                    recipient_ids=(actor_id,),
                    causation_id=events[0].event_id,
                )
                for node in state.resonance_nodes_at(destination or "")
            )
            return events
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
        if intention.action_type == "attune_resonance":
            node = state.resonance_nodes[intention.node_id or ""]
            performed = EventEnvelope(
                event_type="ResonanceAttunementPerformed",
                payload={
                    "node_id": node.node_id,
                    "duration_minutes": intention.duration_minutes,
                },
                **common,
            )
            signal = EventEnvelope(
                event_type="ResonanceSignalReceived",
                world_tick=tick,
                world_time=world_time,
                actor_ids=(actor_id,),
                location=actor.location,
                payload={
                    "node_id": node.node_id,
                    "intensity": node.intensity,
                    "exposure_mode": "attunement",
                },
                visibility="private",
                recipient_ids=(actor_id,),
                causation_id=performed.event_id,
            )
            return [performed, signal]
        if intention.action_type == "propose_cooperation":
            return [
                EventEnvelope(
                    event_type="CooperationProposed",
                    payload={
                        "target_id": intention.target_id,
                        "activity_id": intention.activity_id,
                        "content": intention.spoken_content,
                        "language": intention.language,
                    },
                    **common,
                )
            ]
        if intention.action_type == "respond_cooperation":
            cooperation = state.cooperations[intention.proposal_id or ""]
            return [
                EventEnvelope(
                    event_type="CooperationResponded",
                    payload={
                        "proposal_id": cooperation.proposal_id,
                        "proposer_id": cooperation.proposer_id,
                        "target_id": cooperation.target_id,
                        "activity_id": cooperation.activity_id,
                        "response": intention.response,
                        "content": intention.spoken_content,
                        "language": intention.language,
                    },
                    **common,
                )
            ]
        if intention.action_type == "perform_cooperation":
            cooperation = state.cooperations[intention.proposal_id or ""]
            activity = state.activities[cooperation.activity_id]
            participant_ids = tuple(
                sorted((cooperation.proposer_id, cooperation.target_id))
            )
            return [
                EventEnvelope(
                    event_type="CooperationPerformed",
                    world_tick=tick,
                    world_time=world_time,
                    actor_ids=participant_ids,
                    location=actor.location,
                    payload={
                        "proposal_id": cooperation.proposal_id,
                        "initiator_id": actor_id,
                        "activity_id": activity.activity_id,
                        "label": activity.label,
                        "duration_minutes": intention.duration_minutes,
                        "energy_spent_each": min(
                            1.0,
                            activity.energy_cost * (intention.duration_minutes / 10.0),
                        ),
                        "practiced_skill": activity.practiced_skill,
                        "skill_gain_each": activity.skill_gain,
                    },
                    visibility="local",
                    recipient_ids=recipients,
                    causation_id=causation_id,
                )
            ]
        if intention.action_type == "open_dispute":
            return [
                EventEnvelope(
                    event_type="DisputeOpened",
                    payload={
                        "target_id": intention.target_id,
                        "subject_event_id": intention.subject_event_id,
                        "content": intention.spoken_content,
                        "language": intention.language,
                    },
                    **common,
                )
            ]
        if intention.action_type == "respond_dispute":
            dispute = state.disputes[intention.dispute_id or ""]
            return [
                EventEnvelope(
                    event_type="DisputeResponded",
                    payload={
                        "dispute_id": dispute.dispute_id,
                        "opener_id": dispute.opener_id,
                        "target_id": dispute.target_id,
                        "response": intention.response,
                        "content": intention.spoken_content,
                        "language": intention.language,
                    },
                    **common,
                )
            ]
        raise ValueError(f"unsupported action: {intention.action_type}")
