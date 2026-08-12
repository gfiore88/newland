from __future__ import annotations

from dataclasses import dataclass, field

from .models import AgentMind, EventEnvelope, WorldState, world_time_for_tick


@dataclass(frozen=True, slots=True)
class ArrivalProfile:
    mind: AgentMind
    native_language: str
    arrival_memory: str
    language_proficiencies: dict[str, float] = field(default_factory=dict)
    skills: dict[str, float] = field(default_factory=dict)
    family_group_id: str | None = None
    location: str = "cittadina_iniziale"
    energy: float = 0.8
    hunger: float = 0.1
    thirst: float = 0.1
    inventory_capacity: float = 20.0


class ArrivalService:
    """Turns externally supplied people into canonical events; it invents no person."""

    def prepare(
        self,
        state: WorldState,
        profiles: tuple[ArrivalProfile, ...],
        *,
        tick: int,
    ) -> list[EventEnvelope]:
        self._validate(state, profiles, tick=tick)
        world_time = world_time_for_tick(tick)
        recipients_by_location = {
            location: tuple(
                sorted(
                    set(state.agents_at(location))
                    | {
                        profile.mind.agent_id
                        for profile in profiles
                        if profile.location == location
                    }
                )
            )
            for location in {profile.location for profile in profiles}
        }
        events: list[EventEnvelope] = []

        grouped: dict[str, list[str]] = {}
        for profile in profiles:
            if profile.family_group_id:
                grouped.setdefault(profile.family_group_id, []).append(
                    profile.mind.agent_id
                )
        for group_id, arriving_ids in sorted(grouped.items()):
            members = tuple(
                sorted(
                    set(state.family_groups.get(group_id, set())) | set(arriving_ids)
                )
            )
            events.append(
                EventEnvelope(
                    event_type="FamilyGroupUpdated",
                    world_tick=tick,
                    world_time=world_time,
                    actor_ids=tuple(sorted(arriving_ids)),
                    payload={
                        "family_group_id": group_id,
                        "member_ids": members,
                        "operation": (
                            "joined" if group_id in state.family_groups else "formed"
                        ),
                    },
                    visibility="private",
                    recipient_ids=members,
                )
            )

        for profile in profiles:
            agent_id = profile.mind.agent_id
            languages = dict(profile.language_proficiencies)
            languages[profile.native_language] = 1.0
            events.extend(
                [
                    EventEnvelope(
                        event_type="AgentRegistered",
                        world_tick=tick,
                        world_time=world_time,
                        actor_ids=(agent_id,),
                        location=profile.location,
                        payload={
                            "name": profile.mind.name,
                            "location": profile.location,
                            "energy": profile.energy,
                            "hunger": profile.hunger,
                            "thirst": profile.thirst,
                            "native_language": profile.native_language,
                            "language_proficiencies": languages,
                            "skills": profile.skills,
                            "family_group_id": profile.family_group_id,
                            "inventory_capacity": profile.inventory_capacity,
                        },
                        visibility="private",
                        recipient_ids=(agent_id,),
                    ),
                    EventEnvelope(
                        event_type="AgentArrived",
                        world_tick=tick,
                        world_time=world_time,
                        actor_ids=(agent_id,),
                        location=profile.location,
                        payload={
                            "name": profile.mind.name,
                            "arrival_companion_ids": tuple(
                                other.mind.agent_id
                                for other in profiles
                                if other.mind.agent_id != agent_id
                                and other.location == profile.location
                            ),
                        },
                        visibility="local",
                        recipient_ids=recipients_by_location[profile.location],
                    ),
                    EventEnvelope(
                        event_type="TransitionRemembered",
                        world_tick=tick,
                        world_time=world_time,
                        actor_ids=(agent_id,),
                        location=profile.location,
                        payload={"experience": profile.arrival_memory},
                        visibility="private",
                        recipient_ids=(agent_id,),
                    ),
                ]
            )
        return events

    @staticmethod
    def _validate(
        state: WorldState, profiles: tuple[ArrivalProfile, ...], *, tick: int
    ) -> None:
        if not profiles:
            raise ValueError("at least one arrival profile is required")
        if tick < state.tick:
            raise ValueError("arrival cannot occur in the past")
        agent_ids = [profile.mind.agent_id for profile in profiles]
        if len(agent_ids) != len(set(agent_ids)):
            raise ValueError("arrival profiles contain duplicate agent ids")
        if set(agent_ids) & set(state.agents):
            raise ValueError("arrival profile references an existing agent")
        for profile in profiles:
            if profile.location not in state.locations:
                raise ValueError("arrival location does not exist")
            if not profile.native_language.strip():
                raise ValueError("native language is required")
            if not profile.arrival_memory.strip():
                raise ValueError("arrival memory is required")
            if profile.inventory_capacity <= 0:
                raise ValueError("inventory capacity must be positive")
            for proficiency in (
                *profile.language_proficiencies.values(),
                *profile.skills.values(),
            ):
                if not 0.0 <= proficiency <= 1.0:
                    raise ValueError("language and skill proficiency must be bounded")
