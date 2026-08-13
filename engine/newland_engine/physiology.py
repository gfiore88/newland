from __future__ import annotations

import math
from dataclasses import dataclass

from .models import EventEnvelope, MaterialAgentState, WorldState, world_time_for_tick


def somatic_condition_for(need: str, value: float) -> str:
    if need == "energy":
        if value <= 0.0:
            return "fatal"
        if value <= 0.25:
            return "critical"
        if value <= 0.5:
            return "strained"
        return "regulated"
    if need in {"hunger", "thirst"}:
        if value >= 1.0:
            return "fatal"
        if value >= 0.75:
            return "critical"
        if value >= 0.5:
            return "strained"
        return "regulated"
    raise ValueError(f"unknown somatic need: {need}")


def project_somatic_state(agent: MaterialAgentState) -> dict[str, object]:
    exposure_by_need = {
        "energy": agent.exhaustion_ticks,
        "hunger": agent.starvation_ticks,
        "thirst": agent.dehydration_ticks,
    }
    scale_by_need = {
        "energy": "higher_is_healthier",
        "hunger": "higher_is_more_severe",
        "thirst": "higher_is_more_severe",
    }
    values = {
        "energy": agent.energy,
        "hunger": agent.hunger,
        "thirst": agent.thirst,
    }
    projected: dict[str, object] = {}
    critical_causes: list[str] = []
    conditions: list[str] = []
    for need, value in values.items():
        condition = somatic_condition_for(need, value)
        conditions.append(condition)
        if condition in {"critical", "fatal"}:
            critical_causes.append(need)
        projected[need] = {
            "value": value,
            "scale": scale_by_need[need],
            "condition": condition,
            "trend": agent.need_trends.get(need, "stable"),
            "ticks_in_condition": agent.somatic_condition_ticks.get(need, 0),
            "fatal_exposure_ticks": exposure_by_need[need],
        }
    if "fatal" in conditions:
        overall_condition = "life_threatening"
    elif "critical" in conditions:
        overall_condition = "critical"
    elif "strained" in conditions:
        overall_condition = "strained"
    else:
        overall_condition = "regulated"
    projected["overall_condition"] = overall_condition
    projected["critical_causes"] = critical_causes
    return projected


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
    FATAL_EXPOSURE_LIMIT = 200

    def advance(self, state: WorldState, *, to_tick: int) -> PhysiologyAdvance:
        elapsed = to_tick - state.tick
        if elapsed <= 0:
            return PhysiologyAdvance((), ())

        events: list[EventEnvelope] = []
        interrupted: list[str] = []
        for agent_id in sorted(state.agents):
            agent = state.agents[agent_id]
            if agent.is_dead:
                continue
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

            fatal_exposure_ticks = {
                "exhaustion": self._advance_fatal_exposure(
                    previous=previous["energy"],
                    current=current["energy"],
                    elapsed=elapsed,
                    prior_exposure=agent.exhaustion_ticks,
                    fatal_value=0.0,
                    rate_per_tick=self.ENERGY_DRAIN_PER_TICK,
                ),
                "starvation": self._advance_fatal_exposure(
                    previous=previous["hunger"],
                    current=current["hunger"],
                    elapsed=elapsed,
                    prior_exposure=agent.starvation_ticks,
                    fatal_value=1.0,
                    rate_per_tick=self.HUNGER_GAIN_PER_TICK,
                ),
                "dehydration": self._advance_fatal_exposure(
                    previous=previous["thirst"],
                    current=current["thirst"],
                    elapsed=elapsed,
                    prior_exposure=agent.dehydration_ticks,
                    fatal_value=1.0,
                    rate_per_tick=self.THIRST_GAIN_PER_TICK,
                ),
            }
            somatic_condition_ticks = {
                "energy": self._advance_condition_ticks(
                    need="energy",
                    previous=previous["energy"],
                    current=current["energy"],
                    elapsed=elapsed,
                    prior_duration=agent.somatic_condition_ticks.get("energy", 0),
                    rate_per_tick=self.ENERGY_DRAIN_PER_TICK,
                ),
                "hunger": self._advance_condition_ticks(
                    need="hunger",
                    previous=previous["hunger"],
                    current=current["hunger"],
                    elapsed=elapsed,
                    prior_duration=agent.somatic_condition_ticks.get("hunger", 0),
                    rate_per_tick=self.HUNGER_GAIN_PER_TICK,
                ),
                "thirst": self._advance_condition_ticks(
                    need="thirst",
                    previous=previous["thirst"],
                    current=current["thirst"],
                    elapsed=elapsed,
                    prior_duration=agent.somatic_condition_ticks.get("thirst", 0),
                    rate_per_tick=self.THIRST_GAIN_PER_TICK,
                ),
            }
            need_trends = {
                need: self._trend(previous[need], current[need])
                for need in ("energy", "hunger", "thirst")
            }
            causes = [
                cause
                for cause, exposure in fatal_exposure_ticks.items()
                if exposure > self.FATAL_EXPOSURE_LIMIT
            ]

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
                        "fatal_exposure_ticks": fatal_exposure_ticks,
                        "somatic_condition_ticks": somatic_condition_ticks,
                        "need_trends": need_trends,
                    },
                    visibility="private",
                    recipient_ids=(agent_id,),
                )
            )
            if causes:
                events.append(
                    EventEnvelope(
                        event_type="AgentDied",
                        world_tick=to_tick,
                        world_time=world_time_for_tick(to_tick),
                        actor_ids=(agent_id,),
                        location=agent.location,
                        payload={
                            "reason": " and ".join(causes),
                            "causes": causes,
                            "fatal_exposure_ticks": fatal_exposure_ticks,
                        },
                        visibility="public",
                        recipient_ids=(),
                    )
                )
                interrupted.append(agent_id)
        return PhysiologyAdvance(tuple(events), tuple(interrupted))

    @staticmethod
    def _advance_fatal_exposure(
        *,
        previous: float,
        current: float,
        elapsed: int,
        prior_exposure: int,
        fatal_value: float,
        rate_per_tick: float,
    ) -> int:
        current_is_fatal = current == fatal_value
        if not current_is_fatal:
            return 0
        if previous == fatal_value:
            return prior_exposure + elapsed

        distance = abs(fatal_value - previous)
        ticks_until_fatal = math.ceil((distance / rate_per_tick) - 1e-12)
        return max(0, elapsed - ticks_until_fatal)

    @staticmethod
    def _advance_condition_ticks(
        *,
        need: str,
        previous: float,
        current: float,
        elapsed: int,
        prior_duration: int,
        rate_per_tick: float,
    ) -> int:
        previous_condition = somatic_condition_for(need, previous)
        current_condition = somatic_condition_for(need, current)
        if previous_condition == current_condition:
            return prior_duration + elapsed

        entry_thresholds = {
            "energy": {
                "strained": 0.5,
                "critical": 0.25,
                "fatal": 0.0,
            },
            "hunger": {
                "strained": 0.5,
                "critical": 0.75,
                "fatal": 1.0,
            },
            "thirst": {
                "strained": 0.5,
                "critical": 0.75,
                "fatal": 1.0,
            },
        }
        threshold = entry_thresholds[need][current_condition]
        distance = abs(previous - threshold)
        ticks_until_entry = math.ceil((distance / rate_per_tick) - 1e-12)
        return max(0, elapsed - ticks_until_entry)

    @staticmethod
    def _trend(previous: float, current: float) -> str:
        if current > previous:
            return "rising"
        if current < previous:
            return "falling"
        return "stable"

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
