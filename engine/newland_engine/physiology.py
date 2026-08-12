from __future__ import annotations

from dataclasses import dataclass

from .models import EventEnvelope, MaterialAgentState, WorldState, world_time_for_tick


@dataclass(frozen=True, slots=True)
class PhysiologyAdvance:
    events: tuple[EventEnvelope, ...]
    interrupted_agent_ids: tuple[str, ...]


class PhysiologySystem:
    """Advances bodily state; it never selects an inhabitant action."""

    ENERGY_DRAIN_PER_TICK = 0.01
    HUNGER_GAIN_PER_TICK = 0.015
    THIRST_GAIN_PER_TICK = 0.02
    ENERGY_INTERRUPT = 0.25
    HUNGER_INTERRUPT = 0.75
    THIRST_INTERRUPT = 0.75

    def advance(self, state: WorldState, *, to_tick: int) -> PhysiologyAdvance:
        elapsed = to_tick - state.tick
        if elapsed <= 0:
            return PhysiologyAdvance((), ())

        events: list[EventEnvelope] = []
        interrupted: list[str] = []
        for agent_id in sorted(state.agents):
            agent = state.agents[agent_id]
            previous = self._needs(agent)
            current = {
                "energy": self._bounded(
                    agent.energy - elapsed * self.ENERGY_DRAIN_PER_TICK
                ),
                "hunger": self._bounded(
                    agent.hunger + elapsed * self.HUNGER_GAIN_PER_TICK
                ),
                "thirst": self._bounded(
                    agent.thirst + elapsed * self.THIRST_GAIN_PER_TICK
                ),
            }
            crossed = self._crossed_thresholds(previous, current)
            if crossed:
                interrupted.append(agent_id)
            
            # Starvation Logic
            fatal_condition = current["energy"] == 0.0 or current["hunger"] == 1.0 or current["thirst"] == 1.0
            if fatal_condition:
                agent.starvation_ticks += elapsed
            else:
                agent.starvation_ticks = 0
            
            # se supera 200 tick (circa 20 ore simulate), muore.
            if agent.starvation_ticks > 200 and not agent.is_dead:
                events.append(
                    EventEnvelope(
                        event_type="AgentDied",
                        world_tick=to_tick,
                        world_time=world_time_for_tick(to_tick),
                        actor_ids=(agent_id,),
                        location=agent.location,
                        payload={"reason": "starvation or dehydration"},
                        visibility="public",
                        recipient_ids=(),
                    )
                )
                interrupted.append(agent_id)

            events.append(
                EventEnvelope(
                    event_type="NeedsChanged",
                    world_tick=to_tick,
                    world_time=world_time_for_tick(to_tick),
                    actor_ids=(agent_id,),
                    location=agent.location,
                    payload={
                        "elapsed_ticks": elapsed,
                        "previous": previous,
                        "current": current,
                        "crossed_thresholds": crossed,
                    },
                    visibility="private",
                    recipient_ids=(agent_id,),
                )
            )
        return PhysiologyAdvance(tuple(events), tuple(interrupted))

    def _crossed_thresholds(
        self, previous: dict[str, float], current: dict[str, float]
    ) -> list[str]:
        crossed: list[str] = []
        if previous["energy"] > self.ENERGY_INTERRUPT >= current["energy"]:
            crossed.append("energy_low")
        if previous["hunger"] < self.HUNGER_INTERRUPT <= current["hunger"]:
            crossed.append("hunger_high")
        if previous["thirst"] < self.THIRST_INTERRUPT <= current["thirst"]:
            crossed.append("thirst_high")
        return crossed

    @staticmethod
    def _needs(agent: MaterialAgentState) -> dict[str, float]:
        return {
            "energy": agent.energy,
            "hunger": agent.hunger,
            "thirst": agent.thirst,
        }

    @staticmethod
    def _bounded(value: float) -> float:
        return max(0.0, min(1.0, value))
