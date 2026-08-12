from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import uuid4

Visibility = Literal["public", "local", "private"]
ActionType = Literal["speak", "move", "rest", "offer_help"]


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
    motivation_summary: str = ""
    confidence: float = 0.5

    def __post_init__(self) -> None:
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.action_type == "speak" and not self.spoken_content:
            raise ValueError("speak requires spoken_content")
        if self.action_type == "move" and not self.destination:
            raise ValueError("move requires destination")

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
    active: bool = True


@dataclass(slots=True)
class WorldState:
    tick: int = 0
    world_time: str = field(default_factory=lambda: world_time_for_tick(0))
    locations: dict[str, set[str]] = field(default_factory=dict)
    agents: dict[str, MaterialAgentState] = field(default_factory=dict)

    def agents_at(self, location: str) -> tuple[str, ...]:
        return tuple(
            sorted(
                agent_id
                for agent_id, state in self.agents.items()
                if state.location == location
            )
        )
