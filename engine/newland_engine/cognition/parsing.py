from typing import Any
from ..models import ACTION_ARGUMENTS, Intention
from .types import (
    CognitionContext,
    MemoryAppraisal,
    MentalUpdates,
    BeliefRevision,
    RelationshipRevision,
    AffectRevision,
    ReflectionDraft,
    GoalRevision,
    PlanRevision,
    CommitmentRevision,
    RoleInterpretationRevision,
    AnamnesisFragmentRevision,
    ResonanceOrientationRevision,
)


def parse_memory_appraisals(data: list[dict[str, Any]]) -> tuple[MemoryAppraisal, ...]:
    """Discard retrieval metadata without altering subjective appraisal fields."""
    fields = {
        "source_event_id",
        "subjective_summary",
        "salience",
        "emotional_tone",
        "confidence",
    }
    return tuple(
        MemoryAppraisal(**{key: value for key, value in item.items() if key in fields})
        for item in data
    )


def _classify_sources(data: dict[str, Any], context: CognitionContext) -> dict[str, Any]:
    normalized = dict(data)
    source_ids = tuple(normalized.pop("source_ids"))
    visible_ids = {
        observation.event.event_id for observation in context.observations
    }
    remembered_event_ids = {
        memory.source_event_id for memory in context.mind.memories
    }
    known_event_ids = visible_ids | remembered_event_ids
    memory_ids = {memory.memory_id for memory in context.mind.memories}
    normalized["source_event_ids"] = tuple(
        source_id for source_id in source_ids if source_id in known_event_ids
    )
    normalized["source_memory_ids"] = tuple(
        source_id for source_id in source_ids if source_id in memory_ids
    )
    unknown = set(source_ids) - known_event_ids - memory_ids
    if unknown:
        raise ValueError(
            f"mental update references unknown sources: {sorted(unknown)}"
        )
    return normalized


def parse_intention(data: dict[str, Any]) -> Intention:
    """Discard schema filler without changing the generated action semantics."""
    action_type = data.get("action_type")
    if action_type not in ACTION_ARGUMENTS:
        raise ValueError(f"unsupported generated action: {action_type}")
    common = {
        "action_type",
        "duration_minutes",
        "motivation_summary",
        "confidence",
    }
    relevant = common | ACTION_ARGUMENTS[action_type]
    return Intention(
        **{key: value for key, value in data.items() if key in relevant}
    )


def parse_mental_updates(data: dict[str, Any], context: CognitionContext) -> MentalUpdates:
    affect_data = data.get("affect")
    return MentalUpdates(
        beliefs=tuple(
            BeliefRevision(**_classify_sources(item, context))
            for item in data["beliefs"]
        ),
        relationships=tuple(
            RelationshipRevision(**_classify_sources(item, context))
            for item in data["relationships"]
        ),
        affect=(
            AffectRevision(**_classify_sources(affect_data, context))
            if affect_data is not None
            else None
        ),
        reflections=tuple(
            ReflectionDraft(**_classify_sources(item, context))
            for item in data["reflections"]
        ),
        goals=tuple(
            GoalRevision(**_classify_sources(item, context))
            for item in data["goals"]
        ),
        plans=tuple(
            PlanRevision(**_classify_sources(item, context))
            for item in data["plans"]
        ),
        commitments=tuple(
            CommitmentRevision(**_classify_sources(item, context))
            for item in data["commitments"]
        ),
        role_interpretations=tuple(
            RoleInterpretationRevision(**_classify_sources(item, context))
            for item in data["role_interpretations"]
        ),
        anamnesis_fragments=tuple(
            AnamnesisFragmentRevision(**_classify_sources(item, context))
            for item in data["anamnesis_fragments"]
        ),
        resonance_orientation=(
            ResonanceOrientationRevision(
                **_classify_sources(data["resonance_orientation"], context)
            )
            if data["resonance_orientation"] is not None
            else None
        ),
    )
