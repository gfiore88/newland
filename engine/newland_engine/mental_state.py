from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
from uuid import uuid4

from .cognition import MentalUpdates
from .models import AgentMind, Belief, Reflection


@dataclass(frozen=True, slots=True)
class MindMutation:
    event_type: str
    payload: dict[str, Any]
    source_event_ids: tuple[str, ...] = ()
    source_memory_ids: tuple[str, ...] = ()


class MentalStateApplier:
    """Applies generated mental updates without choosing their content."""

    def apply(
        self, mind: AgentMind, updates: MentalUpdates, *, tick: int
    ) -> list[MindMutation]:
        mutations: list[MindMutation] = []
        for revision in updates.beliefs:
            belief = mind.beliefs.get(revision.key)
            if belief is None:
                belief = Belief(
                    key=revision.key,
                    statement=revision.statement,
                    confidence=revision.confidence,
                    source_memory_ids=list(revision.source_memory_ids),
                    updated_tick=tick,
                    source_event_ids=list(revision.source_event_ids),
                )
                mind.beliefs[revision.key] = belief
            else:
                belief.statement = revision.statement
                belief.confidence = revision.confidence
                belief.updated_tick = tick
                self._extend_unique(belief.source_event_ids, revision.source_event_ids)
                self._extend_unique(
                    belief.source_memory_ids, revision.source_memory_ids
                )
            mutations.append(
                MindMutation(
                    "BeliefUpdated",
                    asdict(belief),
                    revision.source_event_ids,
                    revision.source_memory_ids,
                )
            )

        for revision in updates.relationships:
            relationship = mind.relationship_with(revision.other_agent_id)
            relationship.familiarity = self._bounded(
                relationship.familiarity + revision.familiarity_delta
            )
            relationship.trust = self._bounded(
                relationship.trust + revision.trust_delta
            )
            relationship.warmth = self._bounded(
                relationship.warmth + revision.warmth_delta
            )
            relationship.tension = self._bounded(
                relationship.tension + revision.tension_delta
            )
            relationship.interaction_count += 1
            relationship.last_interaction_tick = tick
            relationship.last_interpretation = revision.interpretation
            self._extend_unique(
                relationship.source_event_ids, revision.source_event_ids
            )
            self._extend_unique(
                relationship.source_memory_ids, revision.source_memory_ids
            )
            mutations.append(
                MindMutation(
                    "RelationshipUpdated",
                    asdict(relationship),
                    revision.source_event_ids,
                    revision.source_memory_ids,
                )
            )

        if updates.affect is not None:
            revision = updates.affect
            mind.affect["calm"] = self._bounded(
                mind.affect.get("calm", 0.5) + revision.calm_delta
            )
            mind.affect["curiosity"] = self._bounded(
                mind.affect.get("curiosity", 0.5) + revision.curiosity_delta
            )
            mind.affect["melancholy"] = self._bounded(
                mind.affect.get("melancholy", 0.5) + revision.melancholy_delta
            )
            mutations.append(
                MindMutation(
                    "AffectUpdated",
                    {
                        "affect": dict(mind.affect),
                        "interpretation": revision.interpretation,
                    },
                    revision.source_event_ids,
                    revision.source_memory_ids,
                )
            )

        for draft in updates.reflections:
            reflection = Reflection(
                reflection_id=str(uuid4()),
                statement=draft.statement,
                confidence=draft.confidence,
                source_memory_ids=list(draft.source_memory_ids),
                created_tick=tick,
            )
            mind.reflections.append(reflection)
            mutations.append(
                MindMutation(
                    "ReflectionCreated",
                    asdict(reflection),
                    source_memory_ids=draft.source_memory_ids,
                )
            )

        for revision in updates.goals:
            changed = False
            if revision.operation == "add" and revision.goal not in mind.goals:
                mind.goals.append(revision.goal)
                changed = True
            elif revision.operation == "remove" and revision.goal in mind.goals:
                mind.goals.remove(revision.goal)
                changed = True
            mutations.append(
                MindMutation(
                    "GoalRevised",
                    {
                        "operation": revision.operation,
                        "goal": revision.goal,
                        "reason": revision.reason,
                        "changed": changed,
                        "active_goals": list(mind.goals),
                    },
                    revision.source_event_ids,
                    revision.source_memory_ids,
                )
            )
        return mutations

    @staticmethod
    def _bounded(value: float) -> float:
        return max(0.0, min(1.0, value))

    @staticmethod
    def _extend_unique(target: list[str], values: tuple[str, ...]) -> None:
        for value in values:
            if value not in target:
                target.append(value)
