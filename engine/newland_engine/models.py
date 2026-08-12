from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import uuid4

Visibility = Literal["public", "local", "private"]
ActionType = Literal[
    "speak",
    "move",
    "rest",
    "offer_help",
    "gather",
    "consume",
    "perform_activity",
    "propose_cooperation",
    "respond_cooperation",
    "perform_cooperation",
    "open_dispute",
    "respond_dispute",
]
ACTION_ARGUMENTS: dict[str, frozenset[str]] = {
    "speak": frozenset({"target_id", "spoken_content", "language"}),
    "move": frozenset({"destination"}),
    "rest": frozenset(),
    "offer_help": frozenset({"target_id"}),
    "gather": frozenset({"resource_id", "quantity"}),
    "consume": frozenset({"resource_id", "quantity"}),
    "perform_activity": frozenset({"activity_id"}),
    "propose_cooperation": frozenset(
        {"target_id", "spoken_content", "language", "activity_id"}
    ),
    "respond_cooperation": frozenset(
        {"spoken_content", "language", "proposal_id", "response"}
    ),
    "perform_cooperation": frozenset({"proposal_id"}),
    "open_dispute": frozenset(
        {"target_id", "spoken_content", "language", "subject_event_id"}
    ),
    "respond_dispute": frozenset(
        {"spoken_content", "language", "dispute_id", "response"}
    ),
}


def world_time_for_tick(tick: int) -> str:
    origin = datetime(1, 1, 1, 6, 0, tzinfo=UTC)
    return (origin + timedelta(minutes=tick * 10)).isoformat()


@dataclass(frozen=True, slots=True)
class EventEnvelope:
    event_type: str
    world_tick: int
    world_time: str
    actor_ids: tuple[str, ...] = ()
    location: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    visibility: Visibility = "public"
    recipient_ids: tuple[str, ...] = ()
    causation_id: str | None = None
    event_id: str = field(default_factory=lambda: str(uuid4()))
    schema_version: int = 1
    sequence: int | None = None

    def __post_init__(self) -> None:
        if self.world_tick < 0:
            raise ValueError("world_tick must be non-negative")
        if self.visibility == "private" and not self.recipient_ids:
            raise ValueError("private events require recipient_ids")
        if not self.event_type:
            raise ValueError("event_type is required")


@dataclass(slots=True)
class Memory:
    memory_id: str
    source_event_id: str
    event_type: str
    summary: str
    salience: float
    emotional_tone: str
    confidence: float
    created_tick: int
    participants: tuple[str, ...] = ()
    location: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    last_accessed_tick: int | None = None
    access_count: int = 0
    consolidated: bool = False


@dataclass(slots=True)
class Belief:
    key: str
    statement: str
    confidence: float
    source_memory_ids: list[str]
    updated_tick: int
    source_event_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Relationship:
    agent_id: str
    familiarity: float = 0.0
    trust: float = 0.5
    warmth: float = 0.0
    tension: float = 0.0
    interaction_count: int = 0
    last_interaction_tick: int | None = None
    last_interpretation: str = ""
    source_event_ids: list[str] = field(default_factory=list)
    source_memory_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Reflection:
    reflection_id: str
    statement: str
    confidence: float
    source_memory_ids: list[str]
    created_tick: int


@dataclass(slots=True)
class Plan:
    plan_key: str
    description: str
    steps: list[str]
    status: str
    created_tick: int
    updated_tick: int
    source_event_ids: list[str] = field(default_factory=list)
    source_memory_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Commitment:
    commitment_key: str
    description: str
    due_tick: int
    involved_agent_ids: list[str]
    status: str
    created_tick: int
    updated_tick: int
    source_event_ids: list[str] = field(default_factory=list)
    source_memory_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RoleInterpretation:
    interpretation_key: str
    subject_agent_id: str
    role_label: str
    interpretation: str
    confidence: float
    created_tick: int
    updated_tick: int
    source_event_ids: list[str] = field(default_factory=list)
    source_memory_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AgentMind:
    agent_id: str
    name: str
    values: list[str]
    temperament: list[str]
    needs: dict[str, float] = field(
        default_factory=lambda: {"energy": 0.8, "hunger": 0.1, "belonging": 0.5}
    )
    affect: dict[str, float] = field(
        default_factory=lambda: {"calm": 0.5, "curiosity": 0.5, "melancholy": 0.5}
    )
    beliefs: dict[str, Belief] = field(default_factory=dict)
    relationships: dict[str, Relationship] = field(default_factory=dict)
    goals: list[str] = field(default_factory=list)
    plans: dict[str, Plan] = field(default_factory=dict)
    commitments: dict[str, Commitment] = field(default_factory=dict)
    role_interpretations: dict[str, RoleInterpretation] = field(default_factory=dict)
    memories: list[Memory] = field(default_factory=list)
    reflections: list[Reflection] = field(default_factory=list)
    last_perceived_sequence: int = 0
    next_activation_tick: int | None = None
    next_activation_reason: str = ""
    private_state: dict[str, Any] = field(default_factory=dict)

    def remember(
        self,
        event: EventEnvelope,
        summary: str,
        *,
        salience: float,
        emotional_tone: str,
        confidence: float,
    ) -> Memory | None:
        if any(memory.source_event_id == event.event_id for memory in self.memories):
            return None
        memory = Memory(
            memory_id=str(uuid4()),
            source_event_id=event.event_id,
            event_type=event.event_type,
            summary=summary,
            salience=max(0.0, min(1.0, salience)),
            emotional_tone=emotional_tone,
            confidence=max(0.0, min(1.0, confidence)),
            created_tick=event.world_tick,
            participants=event.actor_ids,
            location=event.location,
            metadata=dict(event.payload),
        )
        self.memories.append(memory)
        if event.sequence is not None:
            self.last_perceived_sequence = max(
                self.last_perceived_sequence, event.sequence
            )
        return memory

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentMind:
        normalized = dict(data)
        normalized["memories"] = [Memory(**item) for item in data.get("memories", [])]
        normalized["beliefs"] = {
            key: value if isinstance(value, Belief) else Belief(**value)
            for key, value in data.get("beliefs", {}).items()
        }
        normalized["relationships"] = {
            key: value if isinstance(value, Relationship) else Relationship(**value)
            for key, value in data.get("relationships", {}).items()
        }
        normalized["reflections"] = [
            value if isinstance(value, Reflection) else Reflection(**value)
            for value in data.get("reflections", [])
        ]
        normalized["plans"] = {
            key: value if isinstance(value, Plan) else Plan(**value)
            for key, value in data.get("plans", {}).items()
        }
        commitments = data.get("commitments", {})
        normalized["commitments"] = (
            {
                key: value if isinstance(value, Commitment) else Commitment(**value)
                for key, value in commitments.items()
            }
            if isinstance(commitments, dict)
            else {}
        )
        normalized["role_interpretations"] = {
            key: (
                value
                if isinstance(value, RoleInterpretation)
                else RoleInterpretation(**value)
            )
            for key, value in data.get("role_interpretations", {}).items()
        }
        return cls(**normalized)

    def relationship_with(self, other_id: str) -> Relationship:
        if other_id == self.agent_id:
            raise ValueError("an agent cannot have a relationship with itself")
        return self.relationships.setdefault(other_id, Relationship(agent_id=other_id))


@dataclass(frozen=True, slots=True)
class Intention:
    action_type: ActionType
    target_id: str | None = None
    destination: str | None = None
    duration_minutes: int = 10
    spoken_content: str | None = None
    language: str | None = None
    resource_id: str | None = None
    quantity: float | None = None
    activity_id: str | None = None
    proposal_id: str | None = None
    dispute_id: str | None = None
    subject_event_id: str | None = None
    response: str | None = None
    motivation_summary: str = ""
    confidence: float = 0.5

    def __post_init__(self) -> None:
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        communicative = {
            "speak",
            "propose_cooperation",
            "respond_cooperation",
            "open_dispute",
            "respond_dispute",
        }
        if self.action_type in communicative and not self.spoken_content:
            raise ValueError(f"{self.action_type} requires spoken_content")
        if self.action_type in communicative and not self.language:
            raise ValueError(f"{self.action_type} requires language")
        if self.action_type == "move" and not self.destination:
            raise ValueError("move requires destination")
        if self.action_type in {"gather", "consume"}:
            if not self.resource_id:
                raise ValueError(f"{self.action_type} requires resource_id")
            if self.quantity is None or self.quantity <= 0:
                raise ValueError(f"{self.action_type} requires a positive quantity")
        if self.action_type == "perform_activity" and not self.activity_id:
            raise ValueError("perform_activity requires activity_id")
        if self.action_type == "propose_cooperation" and (
            not self.target_id or not self.activity_id
        ):
            raise ValueError("propose_cooperation requires target_id and activity_id")
        if self.action_type == "respond_cooperation" and (
            not self.proposal_id or self.response not in {"accept", "decline"}
        ):
            raise ValueError(
                "respond_cooperation requires proposal_id and accept/decline"
            )
        if self.action_type == "perform_cooperation" and not self.proposal_id:
            raise ValueError("perform_cooperation requires proposal_id")
        if self.action_type == "open_dispute" and (
            not self.target_id or not self.subject_event_id
        ):
            raise ValueError("open_dispute requires target_id and subject_event_id")
        if self.action_type == "respond_dispute" and (
            not self.dispute_id
            or self.response
            not in {
                "contest",
                "offer_resolution",
                "accept_resolution",
            }
        ):
            raise ValueError(
                "respond_dispute requires dispute_id and a supported response"
            )
        allowed_fields = ACTION_ARGUMENTS[self.action_type]
        optional_values = {
            "target_id": self.target_id,
            "destination": self.destination,
            "spoken_content": self.spoken_content,
            "language": self.language,
            "resource_id": self.resource_id,
            "quantity": self.quantity,
            "activity_id": self.activity_id,
            "proposal_id": self.proposal_id,
            "dispute_id": self.dispute_id,
            "subject_event_id": self.subject_event_id,
            "response": self.response,
        }
        extraneous = sorted(
            field_name
            for field_name, value in optional_values.items()
            if value is not None and field_name not in allowed_fields
        )
        if extraneous:
            raise ValueError(
                f"{self.action_type} contains fields for another action: {extraneous}"
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class MaterialAgentState:
    agent_id: str
    name: str
    location: str
    energy: float = 0.8
    hunger: float = 0.1
    thirst: float = 0.1
    native_language: str = "und"
    language_proficiencies: dict[str, float] = field(default_factory=dict)
    skills: dict[str, float] = field(default_factory=dict)
    family_group_id: str | None = None
    inventory: dict[str, float] = field(default_factory=dict)
    inventory_capacity: float = 20.0
    active: bool = True


@dataclass(slots=True)
class ResourceNode:
    resource_id: str
    kind: str
    label: str
    location: str
    quantity: float
    unit: str
    renewable: bool = False


@dataclass(slots=True)
class ActivityDefinition:
    activity_id: str
    label: str
    location: str
    energy_cost: float = 0.0
    practiced_skill: str | None = None
    minimum_proficiency: float = 0.0
    skill_gain: float = 0.0


@dataclass(slots=True)
class CooperationState:
    proposal_id: str
    proposer_id: str
    target_id: str
    activity_id: str
    status: str
    created_tick: int
    response_tick: int | None = None


@dataclass(slots=True)
class DisputeState:
    dispute_id: str
    opener_id: str
    target_id: str
    subject_event_id: str
    status: str
    created_tick: int
    resolution_offered_by: str | None = None


@dataclass(slots=True)
class WorldState:
    tick: int = 0
    world_time: str = field(default_factory=lambda: world_time_for_tick(0))
    locations: dict[str, set[str]] = field(default_factory=dict)
    agents: dict[str, MaterialAgentState] = field(default_factory=dict)
    resources: dict[str, ResourceNode] = field(default_factory=dict)
    resource_effects: dict[str, dict[str, float]] = field(default_factory=dict)
    activities: dict[str, ActivityDefinition] = field(default_factory=dict)
    family_groups: dict[str, set[str]] = field(default_factory=dict)
    cooperations: dict[str, CooperationState] = field(default_factory=dict)
    disputes: dict[str, DisputeState] = field(default_factory=dict)
    event_ids: set[str] = field(default_factory=set)
    event_witnesses: dict[str, set[str]] = field(default_factory=dict)

    def agents_at(self, location: str) -> tuple[str, ...]:
        return tuple(
            sorted(
                agent_id
                for agent_id, state in self.agents.items()
                if state.location == location
            )
        )

    def resources_at(self, location: str) -> tuple[ResourceNode, ...]:
        return tuple(
            sorted(
                (
                    resource
                    for resource in self.resources.values()
                    if resource.location == location and resource.quantity > 0
                ),
                key=lambda resource: resource.resource_id,
            )
        )

    def activities_at(self, location: str) -> tuple[ActivityDefinition, ...]:
        return tuple(
            sorted(
                (
                    activity
                    for activity in self.activities.values()
                    if activity.location == location
                ),
                key=lambda activity: activity.activity_id,
            )
        )
