from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal, Protocol
from urllib.error import URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from .models import AgentMind, Intention, MaterialAgentState
from .perception import Observation


@dataclass(frozen=True, slots=True)
class CognitionContext:
    mind: AgentMind
    material_state: MaterialAgentState
    observations: tuple[Observation, ...]
    nearby_agents: tuple[tuple[str, str], ...]
    activation_reason: str
    world_tick: int = 0


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
            if not -0.25 <= getattr(self, name) <= 0.25:
                raise ValueError(f"{name} must be between -0.25 and 0.25")


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
            if not -0.25 <= getattr(self, name) <= 0.25:
                raise ValueError(f"{name} must be between -0.25 and 0.25")


@dataclass(frozen=True, slots=True)
class ReflectionDraft:
    statement: str
    confidence: float
    source_memory_ids: tuple[str, ...]


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
    prompt_version: str = "agent-cognition-v2"

    def provenance(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "inference_id": self.inference_id,
            "attempts": self.attempts,
            "prompt_version": self.prompt_version,
        }


class CognitionUnavailable(RuntimeError):
    def __init__(self, failures: list[dict[str, str]]) -> None:
        super().__init__("no generative cognition provider returned a valid intention")
        self.failures = failures


class CognitionProvider(Protocol):
    def decide(self, context: CognitionContext) -> CognitionResult: ...


class OllamaCognition:
    def __init__(
        self,
        model: str = "qwen3:4b",
        endpoint: str = "http://127.0.0.1:11434/api/chat",
        timeout_seconds: float = 120.0,
        max_attempts: int = 2,
    ) -> None:
        self.model = model
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self.max_attempts = max_attempts

    def decide(self, context: CognitionContext) -> CognitionResult:
        inference_id = str(uuid4())
        messages = [
            {"role": "system", "content": self._system_prompt()},
            {
                "role": "user",
                "content": json.dumps(
                    self._private_context(context), ensure_ascii=False
                ),
            },
        ]
        failures: list[dict[str, str]] = []
        for attempt in range(1, self.max_attempts + 1):
            try:
                content = self._request(messages)
                parsed = json.loads(content)
                intention = Intention(**parsed["intention"])
                appraisals = tuple(
                    MemoryAppraisal(**item) for item in parsed["memory_appraisals"]
                )
                mental_updates = self._parse_mental_updates(parsed["mental_updates"])
                attention_schedule = AttentionSchedule(**parsed["attention_schedule"])
                result = CognitionResult(
                    intention=intention,
                    memory_appraisals=appraisals,
                    mental_updates=mental_updates,
                    attention_schedule=attention_schedule,
                    provider="ollama",
                    model=self.model,
                    inference_id=inference_id,
                    attempts=attempt,
                )
                validate_cognition_result(result, context)
                return result
            except (RuntimeError, TypeError, ValueError, json.JSONDecodeError) as error:
                failures.append({"model": self.model, "error": str(error)})
                messages.extend(
                    [
                        {"role": "assistant", "content": locals().get("content", "")},
                        {
                            "role": "user",
                            "content": (
                                "La risposta precedente non rispettava lo schema o i vincoli: "
                                f"{error}. Rivaluta autonomamente la stessa situazione privata e "
                                "restituisci una sola intenzione JSON valida."
                            ),
                        },
                    ]
                )
        raise CognitionUnavailable(failures)

    def _request(self, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "format": self._schema(),
            "options": {"temperature": 0.7},
            "messages": messages,
        }
        request = Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, TimeoutError, json.JSONDecodeError) as error:
            raise RuntimeError(f"Ollama inference failed: {error}") from error
        try:
            return str(body["message"]["content"])
        except (KeyError, TypeError) as error:
            raise RuntimeError(
                f"Ollama returned no intention content: {error}"
            ) from error

    @staticmethod
    def _system_prompt() -> str:
        return (
            "Sei una mente abitante di Newland, non un narratore onnisciente. "
            "Decidi una sola azione usando esclusivamente identità, memoria e osservazioni fornite. "
            "Interpreta soggettivamente soltanto gli eventi osservati e usa i loro event_id nelle memory_appraisals; "
            "puoi scegliere di non memorizzare un evento. Beliefs, relazioni, affetti, riflessioni e obiettivi "
            "cambiano soltanto se tu produci un mental_update con fonti valide; usa array vuoti se nulla cambia. "
            "Scegli inoltre quando vorrai riesaminare la situazione tramite attention_schedule. "
            "Non inventare oggetti, persone, luoghi o conoscenze. "
            "Restituisci soltanto il JSON richiesto. "
            "motivation_summary deve essere una motivazione breve e dichiarabile, non ragionamento nascosto."
        )

    @staticmethod
    def _validate_appraisals(
        appraisals: tuple[MemoryAppraisal, ...], context: CognitionContext
    ) -> None:
        visible_ids = {
            observation.event.event_id for observation in context.observations
        }
        source_ids = [appraisal.source_event_id for appraisal in appraisals]
        unknown = set(source_ids) - visible_ids
        if unknown:
            raise ValueError(
                f"memory appraisals reference unobserved events: {sorted(unknown)}"
            )
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("memory appraisals contain duplicate source events")

    @staticmethod
    def _parse_mental_updates(data: dict[str, Any]) -> MentalUpdates:
        affect_data = data.get("affect")
        return MentalUpdates(
            beliefs=tuple(BeliefRevision(**item) for item in data["beliefs"]),
            relationships=tuple(
                RelationshipRevision(**item) for item in data["relationships"]
            ),
            affect=AffectRevision(**affect_data) if affect_data is not None else None,
            reflections=tuple(ReflectionDraft(**item) for item in data["reflections"]),
            goals=tuple(GoalRevision(**item) for item in data["goals"]),
            plans=tuple(PlanRevision(**item) for item in data["plans"]),
            commitments=tuple(
                CommitmentRevision(**item) for item in data["commitments"]
            ),
        )

    @staticmethod
    def _validate_mental_updates(
        updates: MentalUpdates, context: CognitionContext
    ) -> None:
        visible_ids = {
            observation.event.event_id for observation in context.observations
        }
        memory_ids = {memory.memory_id for memory in context.mind.memories}
        perceived_agents = {
            actor_id
            for observation in context.observations
            for actor_id in observation.event.actor_ids
        }
        for observation in context.observations:
            target_id = observation.event.payload.get("target_id")
            if isinstance(target_id, str):
                perceived_agents.add(target_id)
        known_agents = (
            perceived_agents
            | set(context.mind.relationships)
            | {agent_id for agent_id, _ in context.nearby_agents}
        ) - {context.mind.agent_id}

        sourced_updates: list[object] = [
            *updates.beliefs,
            *updates.relationships,
            *updates.goals,
            *updates.plans,
            *updates.commitments,
        ]
        if updates.affect is not None:
            sourced_updates.append(updates.affect)
        for update in sourced_updates:
            source_events = set(update.source_event_ids)
            source_memories = set(update.source_memory_ids)
            if not source_events and not source_memories:
                raise ValueError("mental updates require event or memory provenance")
            if source_events - visible_ids:
                raise ValueError("mental update references unobserved events")
            if source_memories - memory_ids:
                raise ValueError("mental update references unknown memories")
        for relationship in updates.relationships:
            if relationship.other_agent_id not in known_agents:
                raise ValueError("relationship update references an unknown agent")
        for plan in updates.plans:
            if plan.operation != "upsert" and plan.plan_key not in context.mind.plans:
                raise ValueError("plan revision references an unknown plan")
        for commitment in updates.commitments:
            unknown_agents = set(commitment.involved_agent_ids) - known_agents
            if unknown_agents:
                raise ValueError("commitment references unknown agents")
            if (
                commitment.operation == "add"
                and commitment.due_tick < context.world_tick
            ):
                raise ValueError("new commitment cannot be due in the past")
            if (
                commitment.operation != "add"
                and commitment.commitment_key not in context.mind.commitments
            ):
                raise ValueError("commitment revision references an unknown commitment")
        for reflection in updates.reflections:
            if not reflection.source_memory_ids:
                raise ValueError("reflection requires supporting memories")
            if set(reflection.source_memory_ids) - memory_ids:
                raise ValueError("reflection references unknown memories")

    @staticmethod
    def _private_context(context: CognitionContext) -> dict[str, Any]:
        return {
            "self": {
                "agent_id": context.mind.agent_id,
                "name": context.mind.name,
                "values": context.mind.values,
                "temperament": context.mind.temperament,
                "needs": {
                    "energy": context.material_state.energy,
                    "hunger": context.material_state.hunger,
                    "thirst": context.material_state.thirst,
                },
                "affect": context.mind.affect,
                "goals": context.mind.goals,
                "plans": [
                    {
                        "plan_key": plan.plan_key,
                        "description": plan.description,
                        "steps": plan.steps,
                        "status": plan.status,
                    }
                    for plan in context.mind.plans.values()
                ],
                "commitments": [
                    {
                        "commitment_key": commitment.commitment_key,
                        "description": commitment.description,
                        "due_tick": commitment.due_tick,
                        "involved_agent_ids": commitment.involved_agent_ids,
                        "status": commitment.status,
                    }
                    for commitment in context.mind.commitments.values()
                ],
                "location": context.material_state.location,
            },
            "world_tick": context.world_tick,
            "activation_reason": context.activation_reason,
            "recent_memories": [
                {
                    "memory_id": memory.memory_id,
                    "summary": memory.summary,
                    "salience": memory.salience,
                    "emotional_tone": memory.emotional_tone,
                    "confidence": memory.confidence,
                }
                for memory in context.mind.memories[-12:]
            ],
            "beliefs": [
                {
                    "key": belief.key,
                    "statement": belief.statement,
                    "confidence": belief.confidence,
                }
                for belief in context.mind.beliefs.values()
            ],
            "relationships": [
                {
                    "agent_id": relationship.agent_id,
                    "familiarity": relationship.familiarity,
                    "trust": relationship.trust,
                    "warmth": relationship.warmth,
                    "tension": relationship.tension,
                }
                for relationship in context.mind.relationships.values()
            ],
            "reflections": [
                {
                    "statement": reflection.statement,
                    "confidence": reflection.confidence,
                }
                for reflection in context.mind.reflections[-6:]
            ],
            "observations": [
                {
                    "event_id": item.event.event_id,
                    "event_type": item.event.event_type,
                    "actor_ids": item.event.actor_ids,
                    "location": item.event.location,
                    "payload": item.event.payload,
                }
                for item in context.observations
            ],
            "nearby_agents": [
                {"agent_id": agent_id, "name": name}
                for agent_id, name in context.nearby_agents
            ],
        }

    @staticmethod
    def _schema() -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "intention": {
                    "type": "object",
                    "properties": {
                        "action_type": {
                            "type": "string",
                            "enum": ["speak", "move", "rest", "offer_help"],
                        },
                        "target_id": {"type": ["string", "null"]},
                        "destination": {"type": ["string", "null"]},
                        "duration_minutes": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 240,
                        },
                        "spoken_content": {"type": ["string", "null"]},
                        "motivation_summary": {"type": "string", "maxLength": 300},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                    "required": [
                        "action_type",
                        "target_id",
                        "destination",
                        "duration_minutes",
                        "spoken_content",
                        "motivation_summary",
                        "confidence",
                    ],
                    "additionalProperties": False,
                },
                "memory_appraisals": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source_event_id": {"type": "string"},
                            "subjective_summary": {"type": "string", "maxLength": 500},
                            "salience": {"type": "number", "minimum": 0, "maximum": 1},
                            "emotional_tone": {"type": "string", "maxLength": 100},
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                            },
                        },
                        "required": [
                            "source_event_id",
                            "subjective_summary",
                            "salience",
                            "emotional_tone",
                            "confidence",
                        ],
                        "additionalProperties": False,
                    },
                },
                "mental_updates": {
                    "type": "object",
                    "properties": {
                        "beliefs": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "key": {"type": "string", "maxLength": 120},
                                    "statement": {"type": "string", "maxLength": 500},
                                    "confidence": {
                                        "type": "number",
                                        "minimum": 0,
                                        "maximum": 1,
                                    },
                                    "source_event_ids": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "source_memory_ids": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                },
                                "required": [
                                    "key",
                                    "statement",
                                    "confidence",
                                    "source_event_ids",
                                    "source_memory_ids",
                                ],
                                "additionalProperties": False,
                            },
                        },
                        "relationships": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "other_agent_id": {"type": "string"},
                                    "familiarity_delta": {
                                        "type": "number",
                                        "minimum": -0.25,
                                        "maximum": 0.25,
                                    },
                                    "trust_delta": {
                                        "type": "number",
                                        "minimum": -0.25,
                                        "maximum": 0.25,
                                    },
                                    "warmth_delta": {
                                        "type": "number",
                                        "minimum": -0.25,
                                        "maximum": 0.25,
                                    },
                                    "tension_delta": {
                                        "type": "number",
                                        "minimum": -0.25,
                                        "maximum": 0.25,
                                    },
                                    "interpretation": {
                                        "type": "string",
                                        "maxLength": 500,
                                    },
                                    "source_event_ids": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "source_memory_ids": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                },
                                "required": [
                                    "other_agent_id",
                                    "familiarity_delta",
                                    "trust_delta",
                                    "warmth_delta",
                                    "tension_delta",
                                    "interpretation",
                                    "source_event_ids",
                                    "source_memory_ids",
                                ],
                                "additionalProperties": False,
                            },
                        },
                        "affect": {
                            "type": ["object", "null"],
                            "properties": {
                                "calm_delta": {
                                    "type": "number",
                                    "minimum": -0.25,
                                    "maximum": 0.25,
                                },
                                "curiosity_delta": {
                                    "type": "number",
                                    "minimum": -0.25,
                                    "maximum": 0.25,
                                },
                                "melancholy_delta": {
                                    "type": "number",
                                    "minimum": -0.25,
                                    "maximum": 0.25,
                                },
                                "interpretation": {"type": "string", "maxLength": 500},
                                "source_event_ids": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "source_memory_ids": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                            "required": [
                                "calm_delta",
                                "curiosity_delta",
                                "melancholy_delta",
                                "interpretation",
                                "source_event_ids",
                                "source_memory_ids",
                            ],
                            "additionalProperties": False,
                        },
                        "reflections": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "statement": {"type": "string", "maxLength": 700},
                                    "confidence": {
                                        "type": "number",
                                        "minimum": 0,
                                        "maximum": 1,
                                    },
                                    "source_memory_ids": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "minItems": 1,
                                    },
                                },
                                "required": [
                                    "statement",
                                    "confidence",
                                    "source_memory_ids",
                                ],
                                "additionalProperties": False,
                            },
                        },
                        "goals": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "operation": {
                                        "type": "string",
                                        "enum": ["add", "remove"],
                                    },
                                    "goal": {"type": "string", "maxLength": 300},
                                    "reason": {"type": "string", "maxLength": 500},
                                    "source_event_ids": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "source_memory_ids": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                },
                                "required": [
                                    "operation",
                                    "goal",
                                    "reason",
                                    "source_event_ids",
                                    "source_memory_ids",
                                ],
                                "additionalProperties": False,
                            },
                        },
                        "plans": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "operation": {
                                        "type": "string",
                                        "enum": ["upsert", "complete", "abandon"],
                                    },
                                    "plan_key": {"type": "string", "maxLength": 120},
                                    "description": {"type": "string", "maxLength": 500},
                                    "steps": {
                                        "type": "array",
                                        "items": {"type": "string", "maxLength": 300},
                                    },
                                    "source_event_ids": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "source_memory_ids": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                },
                                "required": [
                                    "operation",
                                    "plan_key",
                                    "description",
                                    "steps",
                                    "source_event_ids",
                                    "source_memory_ids",
                                ],
                                "additionalProperties": False,
                            },
                        },
                        "commitments": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "operation": {
                                        "type": "string",
                                        "enum": ["add", "complete", "abandon"],
                                    },
                                    "commitment_key": {
                                        "type": "string",
                                        "maxLength": 120,
                                    },
                                    "description": {"type": "string", "maxLength": 500},
                                    "due_tick": {"type": "integer", "minimum": 0},
                                    "involved_agent_ids": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "source_event_ids": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "source_memory_ids": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                },
                                "required": [
                                    "operation",
                                    "commitment_key",
                                    "description",
                                    "due_tick",
                                    "involved_agent_ids",
                                    "source_event_ids",
                                    "source_memory_ids",
                                ],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": [
                        "beliefs",
                        "relationships",
                        "affect",
                        "reflections",
                        "goals",
                        "plans",
                        "commitments",
                    ],
                    "additionalProperties": False,
                },
                "attention_schedule": {
                    "type": "object",
                    "properties": {
                        "next_activation_in_ticks": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 144,
                        },
                        "reason": {"type": "string", "maxLength": 300},
                    },
                    "required": ["next_activation_in_ticks", "reason"],
                    "additionalProperties": False,
                },
            },
            "required": [
                "intention",
                "memory_appraisals",
                "mental_updates",
                "attention_schedule",
            ],
            "additionalProperties": False,
        }


class GenerativeCognitionPool:
    def __init__(self, providers: list[CognitionProvider]) -> None:
        if not providers:
            raise ValueError("at least one generative cognition provider is required")
        self.providers = providers

    def decide(self, context: CognitionContext) -> CognitionResult:
        failures: list[dict[str, str]] = []
        for provider in self.providers:
            try:
                return provider.decide(context)
            except CognitionUnavailable as error:
                failures.extend(error.failures)
        raise CognitionUnavailable(failures)


def validate_cognition_result(
    result: CognitionResult, context: CognitionContext
) -> None:
    OllamaCognition._validate_appraisals(result.memory_appraisals, context)
    OllamaCognition._validate_mental_updates(result.mental_updates, context)
