from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Literal, Protocol

from ..models import AgentMind, Intention, MaterialAgentState
from ..perception import Observation


AttentionLevel = Literal["full", "focal", "contextual", "reflective"]
AttentionDomain = Literal[
    "memories",
    "relationships",
    "beliefs",
    "goals",
    "plans",
    "commitments",
    "roles",
    "anamnesis",
]


@dataclass(frozen=True, slots=True)
class ContextExpansionRequest:
    domains: tuple[AttentionDomain, ...]
    anchor_ids: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        if not self.domains:
            raise ValueError("context expansion requires at least one domain")
        if not self.reason.strip():
            raise ValueError("context expansion reason is required")


@dataclass(frozen=True, slots=True)
class ResourceAffordance:
    resource_id: str
    kind: str
    label: str
    quantity: float
    unit: str


@dataclass(frozen=True, slots=True)
class ActivityAffordance:
    activity_id: str
    label: str
    practiced_skill: str | None
    minimum_proficiency: float
    energy_cost_per_10_minutes: float = 0.0


@dataclass(frozen=True, slots=True)
class ResonanceNodeAffordance:
    node_id: str
    label: str
    intensity: float


@dataclass(frozen=True, slots=True)
class CooperationAffordance:
    proposal_id: str
    proposer_id: str
    target_id: str
    activity_id: str
    status: str


@dataclass(frozen=True, slots=True)
class DisputeAffordance:
    dispute_id: str
    opener_id: str
    target_id: str
    subject_event_id: str
    status: str
    resolution_offered_by: str | None


@dataclass(frozen=True, slots=True)
class CognitionContext:
    mind: AgentMind
    material_state: MaterialAgentState
    observations: tuple[Observation, ...]
    nearby_agents: tuple[tuple[str, str], ...]
    activation_reason: str
    world_tick: int = 0
    adjacent_locations: tuple[str, ...] = ()
    local_resources: tuple[ResourceAffordance, ...] = ()
    available_activities: tuple[ActivityAffordance, ...] = ()
    local_resonance_nodes: tuple[ResonanceNodeAffordance, ...] = ()
    social_proposals: tuple[CooperationAffordance, ...] = ()
    active_disputes: tuple[DisputeAffordance, ...] = ()
    action_contracts: dict[str, Any] = field(default_factory=dict)
    attention_level: AttentionLevel = "full"
    attention_domains: tuple[AttentionDomain, ...] = ()
    attention_anchor_ids: tuple[str, ...] = ()
    attention_reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MemoryAppraisal:
    source_event_id: str
    subjective_summary: str
    salience: float
    emotional_tone: str
    confidence: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.salience <= 1.0:
            raise ValueError("memory appraisal salience must be between 0 and 1")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("memory appraisal confidence must be between 0 and 1")
        if not self.subjective_summary.strip():
            raise ValueError("memory appraisal summary is required")


@dataclass(frozen=True, slots=True)
class BeliefRevision:
    key: str
    statement: str
    confidence: float
    source_event_ids: tuple[str, ...] = ()
    source_memory_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RelationshipRevision:
    other_agent_id: str
    familiarity_delta: float
    trust_delta: float
    warmth_delta: float
    tension_delta: float
    interpretation: str
    source_event_ids: tuple[str, ...] = ()
    source_memory_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "familiarity_delta",
            "trust_delta",
            "warmth_delta",
            "tension_delta",
        ):
            if not -1.0 <= getattr(self, name) <= 1.0:
                raise ValueError(f"{name} must be between -1 and 1")


@dataclass(frozen=True, slots=True)
class AffectRevision:
    calm_delta: float
    curiosity_delta: float
    melancholy_delta: float
    interpretation: str
    source_event_ids: tuple[str, ...] = ()
    source_memory_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("calm_delta", "curiosity_delta", "melancholy_delta"):
            if not -1.0 <= getattr(self, name) <= 1.0:
                raise ValueError(f"{name} must be between -1 and 1")


@dataclass(frozen=True, slots=True)
class ReflectionDraft:
    statement: str
    confidence: float
    source_event_ids: tuple[str, ...] = ()
    source_memory_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class GoalRevision:
    operation: Literal["add", "remove"]
    goal: str
    reason: str
    source_event_ids: tuple[str, ...] = ()
    source_memory_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PlanRevision:
    operation: Literal["upsert", "complete", "abandon"]
    plan_key: str
    description: str
    steps: tuple[str, ...]
    source_event_ids: tuple[str, ...] = ()
    source_memory_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CommitmentRevision:
    operation: Literal["add", "complete", "abandon"]
    commitment_key: str
    description: str
    due_tick: int
    involved_agent_ids: tuple[str, ...]
    source_event_ids: tuple[str, ...] = ()
    source_memory_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.due_tick < 0:
            raise ValueError("commitment due_tick must be non-negative")


@dataclass(frozen=True, slots=True)
class RoleInterpretationRevision:
    operation: Literal["upsert", "remove"]
    interpretation_key: str
    subject_agent_id: str
    role_label: str
    interpretation: str
    confidence: float
    source_event_ids: tuple[str, ...] = ()
    source_memory_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("role interpretation confidence must be between 0 and 1")
        if not self.interpretation_key.strip():
            raise ValueError("role interpretation key is required")
        if not self.role_label.strip():
            raise ValueError("role label is required")


@dataclass(frozen=True, slots=True)
class AnamnesisFragmentRevision:
    fragment_key: str
    phenomenon_label: str
    content: str
    interpretation: str
    confidence: float
    source_event_ids: tuple[str, ...] = ()
    source_memory_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.fragment_key.strip():
            raise ValueError("anamnesis fragment key is required")
        if not self.phenomenon_label.strip() or not self.content.strip():
            raise ValueError("anamnesis phenomenon and content are required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("anamnesis confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class ResonanceOrientationRevision:
    receptive: bool
    interpretation: str
    source_event_ids: tuple[str, ...] = ()
    source_memory_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.interpretation.strip():
            raise ValueError("resonance orientation interpretation is required")


@dataclass(frozen=True, slots=True)
class AttentionSchedule:
    next_activation_in_ticks: int
    reason: str

    def __post_init__(self) -> None:
        if not 1 <= self.next_activation_in_ticks <= 144:
            raise ValueError("next activation must be between 1 and 144 ticks")
        if not self.reason.strip():
            raise ValueError("next activation reason is required")


@dataclass(frozen=True, slots=True)
class MentalUpdates:
    beliefs: tuple[BeliefRevision, ...] = ()
    relationships: tuple[RelationshipRevision, ...] = ()
    affect: AffectRevision | None = None
    reflections: tuple[ReflectionDraft, ...] = ()
    goals: tuple[GoalRevision, ...] = ()
    plans: tuple[PlanRevision, ...] = ()
    commitments: tuple[CommitmentRevision, ...] = ()
    role_interpretations: tuple[RoleInterpretationRevision, ...] = ()
    anamnesis_fragments: tuple[AnamnesisFragmentRevision, ...] = ()
    resonance_orientation: ResonanceOrientationRevision | None = None


@dataclass(frozen=True, slots=True)
class CognitionResult:
    intention: Intention
    memory_appraisals: tuple[MemoryAppraisal, ...]
    mental_updates: MentalUpdates
    attention_schedule: AttentionSchedule
    provider: str
    model: str
    inference_id: str
    attempts: int
    prompt_version: str = "unversioned"
    prompt_hash: str = ""
    schema_hash: str = ""
    route: str = "ordinary"
    attention_level: AttentionLevel = "full"
    attention_expansions: int = 0
    attention_domains: tuple[str, ...] = ()
    attention_source_ids: tuple[str, ...] = ()

    def provenance(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "inference_id": self.inference_id,
            "attempts": self.attempts,
            "prompt_version": self.prompt_version,
            "prompt_hash": self.prompt_hash,
            "schema_hash": self.schema_hash,
            "route": self.route,
            "attention_level": self.attention_level,
            "attention_expansions": self.attention_expansions,
            "attention_domains": list(self.attention_domains),
            "attention_source_ids": list(self.attention_source_ids),
        }
