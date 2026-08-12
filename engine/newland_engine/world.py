from __future__ import annotations

from .models import (
    EventEnvelope,
    Intention,
    MaterialAgentState,
    WorldState,
    world_time_for_tick,
)


def reduce_event(state: WorldState, event: EventEnvelope) -> WorldState:
    state.tick = max(state.tick, event.world_tick)
    state.world_time = event.world_time

    if event.event_type == "WorldInitialized":
        state.locations = {
            name: set(neighbors)
            for name, neighbors in event.payload.get("locations", {}).items()
        }
    elif event.event_type == "AgentRegistered":
        agent_id = event.actor_ids[0]
        state.agents[agent_id] = MaterialAgentState(
            agent_id=agent_id,
            name=event.payload["name"],
            location=event.location or event.payload["location"],
            energy=float(event.payload.get("energy", 0.8)),
        )
    elif event.event_type == "AgentMoved":
        state.agents[event.actor_ids[0]].location = event.payload["destination"]
    elif event.event_type == "AgentRested":
        agent = state.agents[event.actor_ids[0]]
        agent.energy = min(
            1.0, agent.energy + float(event.payload.get("energy_recovered", 0.1))
        )
    return state


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
        if intention.target_id:
            target = state.agents.get(intention.target_id)
            if target is None:
                return "target does not exist"
            if (
                intention.action_type in {"speak", "offer_help"}
                and target.location != actor.location
            ):
                return "target is not present at actor location"
        if intention.action_type == "move":
            if intention.destination not in state.locations:
                return "destination does not exist"
            if intention.destination not in state.locations.get(actor.location, set()):
                return "destination is not adjacent"
        if intention.action_type == "speak" and not intention.target_id:
            return "speech requires a target"
        if intention.action_type == "offer_help" and not intention.target_id:
            return "help requires a target"
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
        raise ValueError(f"unsupported action: {intention.action_type}")
