from __future__ import annotations

import json
from dataclasses import dataclass, replace
from typing import Any, Literal, Protocol
from urllib.error import URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from .models import ACTION_ARGUMENTS, AgentMind, Intention, MaterialAgentState
from .perception import Observation


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
    prompt_version: str = "agent-cognition-v4"
    route: str = "ordinary"

    def provenance(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "inference_id": self.inference_id,
            "attempts": self.attempts,
            "prompt_version": self.prompt_version,
            "route": self.route,
        }


class CognitionUnavailable(RuntimeError):
    def __init__(self, failures: list[dict[str, str]]) -> None:
        super().__init__("no generative cognition provider returned a valid intention")
        self.failures = failures


class CognitionProvider(Protocol):
    def decide(self, context: CognitionContext) -> CognitionResult: ...


class RoutedCognition:
    """Routes private context to a model tier without choosing agent behavior."""

    def __init__(
        self,
        ordinary: CognitionProvider,
        reflective: CognitionProvider,
    ) -> None:
        self.ordinary = ordinary
        self.reflective = reflective

    def decide(self, context: CognitionContext) -> CognitionResult:
        route = self.route_for(context)
        provider = self.reflective if route == "reflective" else self.ordinary
        return replace(provider.decide(context), route=route)

    @staticmethod
    def route_for(context: CognitionContext) -> Literal["ordinary", "reflective"]:
        observed_types = {
            observation.event.event_type for observation in context.observations
        }
        if "ResonanceSignalReceived" in observed_types or context.active_disputes:
            return "reflective"
        return "ordinary"


class OllamaCognition:
    def __init__(
        self,
        model: str = "qwen2.5:3b",
        endpoint: str = "http://127.0.0.1:11434/api/chat",
        timeout_seconds: float = 120.0,
        max_attempts: int = 3,
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
                intention = self._parse_intention(parsed["intention"])
                appraisals = tuple(
                    MemoryAppraisal(**item) for item in parsed["memory_appraisals"]
                )
                mental_updates = self._parse_mental_updates(
                    parsed["mental_updates"], context
                )
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

    @staticmethod
    def _parse_intention(data: dict[str, Any]) -> Intention:
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

    def _request(self, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "think": False,
            "format": self._schema(),
            "options": {
                "temperature": 0.7,
                "num_ctx": 8192,
                "num_predict": 2048,
            },
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
            "puoi scegliere di non memorizzare un evento. Beliefs, relazioni, affetti, riflessioni, obiettivi e ruoli interpretati "
            "cambiano soltanto se tu produci un mental_update con source_ids non vuoto, composto esclusivamente "
            "da event_id osservati o memory_id posseduti; usa array vuoti se nulla cambia. "
            "Puoi interpretare te stesso o una persona conosciuta con un ruolo emergente: genera liberamente role_label, "
            "senza scegliere da una tassonomia e senza trattarlo come un incarico ufficiale assegnato dal mondo. "
            "Per creare o cambiare una tua interpretazione di ruolo usa operation=upsert; usa operation=remove soltanto "
            "con un interpretation_key già presente in role_interpretations. Se non esistono ruoli interpretati, non puoi rimuoverne. "
            "Un ResonanceSignalReceived è soltanto uno stimolo: non sei obbligato a viverlo come flashback. "
            "Se emerge davvero un'immagine, memoria somatica, intuizione o altro fenomeno, formulalo liberamente in anamnesis_fragments, "
            "come esperienza soggettiva incerta e non come verità canonica. Puoi anche non produrre alcun frammento. "
            "ATTENZIONE: Puoi generare anamnesis_fragments o modificare resonance_orientation ESCLUSIVAMENTE se hai osservato un evento ResonanceSignalReceived nel contesto. In assenza di questo evento, anamnesis_fragments DEVE essere vuoto e resonance_orientation DEVE essere null. "
            "Con resonance_orientation puoi scegliere liberamente se restare ricettivo o chiudere il canale interiore; usa null se non vuoi cambiare scelta. "
            "Scegli inoltre quando vorrai riesaminare la situazione tramite attention_schedule. "
            "Puoi usare soltanto destination, resource_id e activity_id elencati nelle affordance locali; "
            "la loro presenza non ti obbliga a usarli. "
            "Puoi usare attune_resonance soltanto con un node_id locale; il nodo è uno stimolo fisico, "
            "non implica automaticamente un flashback o un significato. "
            "Usa proposal_id e dispute_id soltanto dalle affordance sociali fornite. "
            "Nei campi intention non pertinenti all'action_type scelto restituisci null. "
            "Se parli, scegli una lingua che conosci e scrivi spoken_content in quella lingua; "
            "interpreta le lingue altrui attraverso la tua esperienza, il contesto e l'empatia, senza fingere conoscenze. "
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
    def _parse_mental_updates(
        data: dict[str, Any], context: CognitionContext
    ) -> MentalUpdates:
        affect_data = data.get("affect")
        return MentalUpdates(
            beliefs=tuple(
                BeliefRevision(**OllamaCognition._classify_sources(item, context))
                for item in data["beliefs"]
            ),
            relationships=tuple(
                RelationshipRevision(**OllamaCognition._classify_sources(item, context))
                for item in data["relationships"]
            ),
            affect=(
                AffectRevision(
                    **OllamaCognition._classify_sources(affect_data, context)
                )
                if affect_data is not None
                else None
            ),
            reflections=tuple(
                ReflectionDraft(**OllamaCognition._classify_sources(item, context))
                for item in data["reflections"]
            ),
            goals=tuple(
                GoalRevision(**OllamaCognition._classify_sources(item, context))
                for item in data["goals"]
            ),
            plans=tuple(
                PlanRevision(**OllamaCognition._classify_sources(item, context))
                for item in data["plans"]
            ),
            commitments=tuple(
                CommitmentRevision(**OllamaCognition._classify_sources(item, context))
                for item in data["commitments"]
            ),
            role_interpretations=tuple(
                RoleInterpretationRevision(
                    **OllamaCognition._classify_sources(item, context)
                )
                for item in data["role_interpretations"]
            ),
            anamnesis_fragments=tuple(
                AnamnesisFragmentRevision(
                    **OllamaCognition._classify_sources(item, context)
                )
                for item in data["anamnesis_fragments"]
            ),
            resonance_orientation=(
                ResonanceOrientationRevision(
                    **OllamaCognition._classify_sources(
                        data["resonance_orientation"], context
                    )
                )
                if data["resonance_orientation"] is not None
                else None
            ),
        )

    @staticmethod
    def _classify_sources(
        data: dict[str, Any], context: CognitionContext
    ) -> dict[str, Any]:
        normalized = dict(data)
        source_ids = tuple(normalized.pop("source_ids"))
        visible_ids = {
            observation.event.event_id for observation in context.observations
        }
        memory_ids = {memory.memory_id for memory in context.mind.memories}
        normalized["source_event_ids"] = tuple(
            source_id for source_id in source_ids if source_id in visible_ids
        )
        normalized["source_memory_ids"] = tuple(
            source_id for source_id in source_ids if source_id in memory_ids
        )
        unknown = set(source_ids) - visible_ids - memory_ids
        if unknown:
            raise ValueError(
                f"mental update references unknown sources: {sorted(unknown)}"
            )
        return normalized

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
            *updates.reflections,
            *updates.goals,
            *updates.plans,
            *updates.commitments,
            *updates.role_interpretations,
            *updates.anamnesis_fragments,
        ]
        if updates.affect is not None:
            sourced_updates.append(updates.affect)
        if updates.resonance_orientation is not None:
            sourced_updates.append(updates.resonance_orientation)
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
        role_subjects = known_agents | {context.mind.agent_id}
        for role in updates.role_interpretations:
            if role.subject_agent_id not in role_subjects:
                raise ValueError("role interpretation references an unknown agent")
            if (
                role.operation == "remove"
                and role.interpretation_key not in context.mind.role_interpretations
            ):
                raise ValueError("role revision references an unknown interpretation")
        resonance_event_ids = {
            observation.event.event_id
            for observation in context.observations
            if observation.event.event_type == "ResonanceSignalReceived"
        }
        resonance_memory_ids = {
            memory.memory_id
            for memory in context.mind.memories
            if memory.event_type == "ResonanceSignalReceived"
        }
        resonance_updates: list[object] = [*updates.anamnesis_fragments]
        if updates.resonance_orientation is not None:
            resonance_updates.append(updates.resonance_orientation)
        for update in resonance_updates:
            if not (
                set(update.source_event_ids) & resonance_event_ids
                or set(update.source_memory_ids) & resonance_memory_ids
            ):
                raise ValueError(
                    "anamnesis and resonance orientation require perceived resonance provenance"
                )
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

    @staticmethod
    def _validate_intention_context(
        intention: Intention, context: CognitionContext
    ) -> None:
        nearby_ids = {agent_id for agent_id, _ in context.nearby_agents}
        if (
            intention.action_type
            in {
                "speak",
                "offer_help",
                "propose_cooperation",
                "open_dispute",
            }
            and intention.target_id not in nearby_ids
        ):
            raise ValueError(
                "social intention targets an agent outside local perception"
            )
        if (
            intention.action_type
            in {
                "speak",
                "propose_cooperation",
                "respond_cooperation",
                "open_dispute",
                "respond_dispute",
            }
            and context.material_state.language_proficiencies.get(
                intention.language or "", 0.0
            )
            <= 0.0
        ):
            raise ValueError("social intention uses an unknown language")

        proposal_ids = {proposal.proposal_id for proposal in context.social_proposals}
        if (
            intention.action_type in {"respond_cooperation", "perform_cooperation"}
            and intention.proposal_id not in proposal_ids
        ):
            raise ValueError("cooperation intention references an unknown proposal")

        dispute_ids = {dispute.dispute_id for dispute in context.active_disputes}
        if (
            intention.action_type == "respond_dispute"
            and intention.dispute_id not in dispute_ids
        ):
            raise ValueError("dispute response references an unknown dispute")
        if intention.action_type == "open_dispute":
            known_event_ids = {
                observation.event.event_id for observation in context.observations
            } | {memory.source_event_id for memory in context.mind.memories}
            if intention.subject_event_id not in known_event_ids:
                raise ValueError("dispute references an event unknown to the agent")
        node_ids = {node.node_id for node in context.local_resonance_nodes}
        if (
            intention.action_type == "attune_resonance"
            and intention.node_id not in node_ids
        ):
            raise ValueError("resonance intention references a non-local node")

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
                "inventory": context.material_state.inventory,
                "inventory_capacity": context.material_state.inventory_capacity,
                "native_language": context.material_state.native_language,
                "language_proficiencies": context.material_state.language_proficiencies,
                "skills": context.material_state.skills,
                "family_group_id": context.material_state.family_group_id,
                "location": context.material_state.location,
            },
            "local_affordances": {
                "adjacent_locations": context.adjacent_locations,
                "resources": [
                    {
                        "resource_id": resource.resource_id,
                        "kind": resource.kind,
                        "label": resource.label,
                        "quantity": resource.quantity,
                        "unit": resource.unit,
                    }
                    for resource in context.local_resources
                ],
                "activities": [
                    {
                        "activity_id": activity.activity_id,
                        "label": activity.label,
                        "practiced_skill": activity.practiced_skill,
                        "minimum_proficiency": activity.minimum_proficiency,
                    }
                    for activity in context.available_activities
                ],
                "resonance_nodes": [
                    {
                        "node_id": node.node_id,
                        "label": node.label,
                        "intensity": node.intensity,
                    }
                    for node in context.local_resonance_nodes
                ],
            },
            "social_affordances": {
                "cooperations": [
                    {
                        "proposal_id": proposal.proposal_id,
                        "proposer_id": proposal.proposer_id,
                        "target_id": proposal.target_id,
                        "activity_id": proposal.activity_id,
                        "status": proposal.status,
                    }
                    for proposal in context.social_proposals
                ],
                "disputes": [
                    {
                        "dispute_id": dispute.dispute_id,
                        "opener_id": dispute.opener_id,
                        "target_id": dispute.target_id,
                        "subject_event_id": dispute.subject_event_id,
                        "status": dispute.status,
                        "resolution_offered_by": dispute.resolution_offered_by,
                    }
                    for dispute in context.active_disputes
                ],
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
            "role_interpretations": [
                {
                    "interpretation_key": role.interpretation_key,
                    "subject_agent_id": role.subject_agent_id,
                    "role_label": role.role_label,
                    "interpretation": role.interpretation,
                    "confidence": role.confidence,
                }
                for role in context.mind.role_interpretations.values()
            ],
            "anamnesis_fragments": [
                {
                    "fragment_key": fragment.fragment_key,
                    "phenomenon_label": fragment.phenomenon_label,
                    "content": fragment.content,
                    "interpretation": fragment.interpretation,
                    "confidence": fragment.confidence,
                }
                for fragment in context.mind.anamnesis_fragments.values()
            ],
            "resonance_orientation": (
                {
                    "receptive": context.mind.resonance_orientation.receptive,
                    "interpretation": context.mind.resonance_orientation.interpretation,
                }
                if context.mind.resonance_orientation is not None
                else None
            ),
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
                            "enum": [
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
                                "attune_resonance",
                            ],
                        },
                        "target_id": {"type": ["string", "null"]},
                        "destination": {"type": ["string", "null"]},
                        "duration_minutes": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 240,
                        },
                        "spoken_content": {"type": ["string", "null"]},
                        "language": {"type": ["string", "null"]},
                        "resource_id": {"type": ["string", "null"]},
                        "quantity": {
                            "type": ["number", "null"],
                            "exclusiveMinimum": 0,
                        },
                        "activity_id": {"type": ["string", "null"]},
                        "proposal_id": {"type": ["string", "null"]},
                        "dispute_id": {"type": ["string", "null"]},
                        "subject_event_id": {"type": ["string", "null"]},
                        "response": {
                            "type": ["string", "null"],
                            "enum": [
                                "accept",
                                "decline",
                                "contest",
                                "offer_resolution",
                                "accept_resolution",
                                None,
                            ],
                        },
                        "node_id": {"type": ["string", "null"]},
                        "motivation_summary": {"type": "string", "maxLength": 300},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                    "required": [
                        "action_type",
                        "target_id",
                        "destination",
                        "duration_minutes",
                        "spoken_content",
                        "language",
                        "resource_id",
                        "quantity",
                        "activity_id",
                        "proposal_id",
                        "dispute_id",
                        "subject_event_id",
                        "response",
                        "node_id",
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
                                    "source_ids": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "minItems": 1,
                                    },
                                },
                                "required": [
                                    "key",
                                    "statement",
                                    "confidence",
                                    "source_ids",
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
                                        "minimum": -1,
                                        "maximum": 1,
                                    },
                                    "trust_delta": {
                                        "type": "number",
                                        "minimum": -1,
                                        "maximum": 1,
                                    },
                                    "warmth_delta": {
                                        "type": "number",
                                        "minimum": -1,
                                        "maximum": 1,
                                    },
                                    "tension_delta": {
                                        "type": "number",
                                        "minimum": -1,
                                        "maximum": 1,
                                    },
                                    "interpretation": {
                                        "type": "string",
                                        "maxLength": 500,
                                    },
                                    "source_ids": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "minItems": 1,
                                    },
                                },
                                "required": [
                                    "other_agent_id",
                                    "familiarity_delta",
                                    "trust_delta",
                                    "warmth_delta",
                                    "tension_delta",
                                    "interpretation",
                                    "source_ids",
                                ],
                                "additionalProperties": False,
                            },
                        },
                        "affect": {
                            "type": ["object", "null"],
                            "properties": {
                                "calm_delta": {
                                    "type": "number",
                                    "minimum": -1,
                                    "maximum": 1,
                                },
                                "curiosity_delta": {
                                    "type": "number",
                                    "minimum": -1,
                                    "maximum": 1,
                                },
                                "melancholy_delta": {
                                    "type": "number",
                                    "minimum": -1,
                                    "maximum": 1,
                                },
                                "interpretation": {"type": "string", "maxLength": 500},
                                "source_ids": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "minItems": 1,
                                },
                            },
                            "required": [
                                "calm_delta",
                                "curiosity_delta",
                                "melancholy_delta",
                                "interpretation",
                                "source_ids",
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
                                    "source_ids": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "minItems": 1,
                                    },
                                },
                                "required": [
                                    "statement",
                                    "confidence",
                                    "source_ids",
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
                                    "source_ids": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "minItems": 1,
                                    },
                                },
                                "required": [
                                    "operation",
                                    "goal",
                                    "reason",
                                    "source_ids",
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
                                    "source_ids": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "minItems": 1,
                                    },
                                },
                                "required": [
                                    "operation",
                                    "plan_key",
                                    "description",
                                    "steps",
                                    "source_ids",
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
                                    "source_ids": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "minItems": 1,
                                    },
                                },
                                "required": [
                                    "operation",
                                    "commitment_key",
                                    "description",
                                    "due_tick",
                                    "involved_agent_ids",
                                    "source_ids",
                                ],
                                "additionalProperties": False,
                            },
                        },
                        "role_interpretations": {
                            "type": "array",
                            "description": (
                                "Interpretazioni soggettive opzionali. Usare remove solo "
                                "per interpretation_key già presenti nel contesto privato."
                            ),
                            "items": {
                                "type": "object",
                                "properties": {
                                    "operation": {
                                        "type": "string",
                                        "enum": ["upsert", "remove"],
                                    },
                                    "interpretation_key": {
                                        "type": "string",
                                        "maxLength": 120,
                                        "description": (
                                            "Chiave stabile scelta dalla mente per upsert, oppure "
                                            "chiave esistente esatta per remove."
                                        ),
                                    },
                                    "subject_agent_id": {"type": "string"},
                                    "role_label": {
                                        "type": "string",
                                        "maxLength": 160,
                                    },
                                    "interpretation": {
                                        "type": "string",
                                        "maxLength": 600,
                                    },
                                    "confidence": {
                                        "type": "number",
                                        "minimum": 0,
                                        "maximum": 1,
                                    },
                                    "source_ids": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "minItems": 1,
                                    },
                                },
                                "required": [
                                    "operation",
                                    "interpretation_key",
                                    "subject_agent_id",
                                    "role_label",
                                    "interpretation",
                                    "confidence",
                                    "source_ids",
                                ],
                                "additionalProperties": False,
                            },
                        },
                        "anamnesis_fragments": {
                            "type": "array",
                            "description": (
                                "Esperienze soggettive opzionali generate solo da segnali "
                                "di risonanza percepiti; non sono fatti canonici sul passato."
                            ),
                            "items": {
                                "type": "object",
                                "properties": {
                                    "fragment_key": {
                                        "type": "string",
                                        "maxLength": 120,
                                    },
                                    "phenomenon_label": {
                                        "type": "string",
                                        "maxLength": 160,
                                    },
                                    "content": {"type": "string", "maxLength": 900},
                                    "interpretation": {
                                        "type": "string",
                                        "maxLength": 700,
                                    },
                                    "confidence": {
                                        "type": "number",
                                        "minimum": 0,
                                        "maximum": 1,
                                    },
                                    "source_ids": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "minItems": 1,
                                    },
                                },
                                "required": [
                                    "fragment_key",
                                    "phenomenon_label",
                                    "content",
                                    "interpretation",
                                    "confidence",
                                    "source_ids",
                                ],
                                "additionalProperties": False,
                            },
                        },
                        "resonance_orientation": {
                            "type": ["object", "null"],
                            "properties": {
                                "receptive": {"type": "boolean"},
                                "interpretation": {
                                    "type": "string",
                                    "maxLength": 700,
                                },
                                "source_ids": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "minItems": 1,
                                },
                            },
                            "required": [
                                "receptive",
                                "interpretation",
                                "source_ids",
                            ],
                            "additionalProperties": False,
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
                        "role_interpretations",
                        "anamnesis_fragments",
                        "resonance_orientation",
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
    OllamaCognition._validate_intention_context(result.intention, context)
