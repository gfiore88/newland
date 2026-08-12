from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
from uuid import uuid4

from .cognition import MentalUpdates
from .models import (
    AgentMind,
    AnamnesisFragment,
    Belief,
    Commitment,
    Plan,
    Reflection,
    ResonanceOrientation,
    RoleInterpretation,
)


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
                source_event_ids=list(draft.source_event_ids),
            )
            mind.reflections.append(reflection)
            mutations.append(
                MindMutation(
                    "ReflectionCreated",
                    asdict(reflection),
                    source_event_ids=draft.source_event_ids,
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

        for revision in updates.plans:
            plan = mind.plans.get(revision.plan_key)
            if revision.operation == "upsert":
                if plan is None:
                    plan = Plan(
                        plan_key=revision.plan_key,
                        description=revision.description,
                        steps=list(revision.steps),
                        status="active",
                        created_tick=tick,
                        updated_tick=tick,
                        source_event_ids=list(revision.source_event_ids),
                        source_memory_ids=list(revision.source_memory_ids),
                    )
                    mind.plans[revision.plan_key] = plan
                else:
                    plan.description = revision.description
                    plan.steps = list(revision.steps)
                    plan.status = "active"
                    plan.updated_tick = tick
                    self._extend_unique(
                        plan.source_event_ids, revision.source_event_ids
                    )
                    self._extend_unique(
                        plan.source_memory_ids, revision.source_memory_ids
                    )
            elif plan is not None:
                plan.status = (
                    "completed" if revision.operation == "complete" else "abandoned"
                )
                plan.updated_tick = tick
                self._extend_unique(plan.source_event_ids, revision.source_event_ids)
                self._extend_unique(plan.source_memory_ids, revision.source_memory_ids)
            if plan is not None:
                mutations.append(
                    MindMutation(
                        "PlanRevised",
                        {"operation": revision.operation, **asdict(plan)},
                        revision.source_event_ids,
                        revision.source_memory_ids,
                    )
                )

        for revision in updates.commitments:
            commitment = mind.commitments.get(revision.commitment_key)
            if revision.operation == "add":
                if commitment is None:
                    commitment = Commitment(
                        commitment_key=revision.commitment_key,
                        description=revision.description,
                        due_tick=revision.due_tick,
                        involved_agent_ids=list(revision.involved_agent_ids),
                        status="active",
                        created_tick=tick,
                        updated_tick=tick,
                        source_event_ids=list(revision.source_event_ids),
                        source_memory_ids=list(revision.source_memory_ids),
                    )
                    mind.commitments[revision.commitment_key] = commitment
                else:
                    commitment.description = revision.description
                    commitment.due_tick = revision.due_tick
                    commitment.involved_agent_ids = list(revision.involved_agent_ids)
                    commitment.status = "active"
                    commitment.updated_tick = tick
                    self._extend_unique(
                        commitment.source_event_ids, revision.source_event_ids
                    )
                    self._extend_unique(
                        commitment.source_memory_ids, revision.source_memory_ids
                    )
            elif commitment is not None:
                commitment.status = (
                    "completed" if revision.operation == "complete" else "abandoned"
                )
                commitment.updated_tick = tick
                self._extend_unique(
                    commitment.source_event_ids, revision.source_event_ids
                )
                self._extend_unique(
                    commitment.source_memory_ids, revision.source_memory_ids
                )
            if commitment is not None:
                mutations.append(
                    MindMutation(
                        "CommitmentRevised",
                        {"operation": revision.operation, **asdict(commitment)},
                        revision.source_event_ids,
                        revision.source_memory_ids,
                    )
                )

        for revision in updates.role_interpretations:
            role = mind.role_interpretations.get(revision.interpretation_key)
            if revision.operation == "upsert":
                if role is None:
                    role = RoleInterpretation(
                        interpretation_key=revision.interpretation_key,
                        subject_agent_id=revision.subject_agent_id,
                        role_label=revision.role_label,
                        interpretation=revision.interpretation,
                        confidence=revision.confidence,
                        created_tick=tick,
                        updated_tick=tick,
                        source_event_ids=list(revision.source_event_ids),
                        source_memory_ids=list(revision.source_memory_ids),
                    )
                    mind.role_interpretations[revision.interpretation_key] = role
                else:
                    role.subject_agent_id = revision.subject_agent_id
                    role.role_label = revision.role_label
                    role.interpretation = revision.interpretation
                    role.confidence = revision.confidence
                    role.updated_tick = tick
                    self._extend_unique(
                        role.source_event_ids, revision.source_event_ids
                    )
                    self._extend_unique(
                        role.source_memory_ids, revision.source_memory_ids
                    )
                mutations.append(
                    MindMutation(
                        "RoleInterpretationRevised",
                        {"operation": revision.operation, **asdict(role)},
                        revision.source_event_ids,
                        revision.source_memory_ids,
                    )
                )
            elif role is not None:
                removed = mind.role_interpretations.pop(revision.interpretation_key)
                mutations.append(
                    MindMutation(
                        "RoleInterpretationRevised",
                        {"operation": revision.operation, **asdict(removed)},
                        revision.source_event_ids,
                        revision.source_memory_ids,
                    )
                )

        for revision in updates.anamnesis_fragments:
            fragment = mind.anamnesis_fragments.get(revision.fragment_key)
            if fragment is None:
                fragment = AnamnesisFragment(
                    fragment_key=revision.fragment_key,
                    phenomenon_label=revision.phenomenon_label,
                    content=revision.content,
                    interpretation=revision.interpretation,
                    confidence=revision.confidence,
                    created_tick=tick,
                    updated_tick=tick,
                    source_event_ids=list(revision.source_event_ids),
                    source_memory_ids=list(revision.source_memory_ids),
                )
                mind.anamnesis_fragments[revision.fragment_key] = fragment
            else:
                fragment.phenomenon_label = revision.phenomenon_label
                fragment.content = revision.content
                fragment.interpretation = revision.interpretation
                fragment.confidence = revision.confidence
                fragment.updated_tick = tick
                self._extend_unique(
                    fragment.source_event_ids, revision.source_event_ids
                )
                self._extend_unique(
                    fragment.source_memory_ids, revision.source_memory_ids
                )
            mutations.append(
                MindMutation(
                    "AnamnesisFragmentRevised",
                    asdict(fragment),
                    revision.source_event_ids,
                    revision.source_memory_ids,
                )
            )

        if updates.resonance_orientation is not None:
            revision = updates.resonance_orientation
            orientation = ResonanceOrientation(
                receptive=revision.receptive,
                interpretation=revision.interpretation,
                updated_tick=tick,
                source_event_ids=list(revision.source_event_ids),
                source_memory_ids=list(revision.source_memory_ids),
            )
            mind.resonance_orientation = orientation
            mutations.append(
                MindMutation(
                    "ResonanceOrientationRevised",
                    asdict(orientation),
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
