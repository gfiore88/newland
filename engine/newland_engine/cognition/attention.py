from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from threading import RLock
from typing import Any, Protocol

from ..physiology import project_somatic_state
from .exceptions import CognitionUnavailable
from .retrieval import RetrievedMemory, retrieve_memories
from .types import (
    AttentionDomain,
    AttentionLevel,
    CognitionContext,
    CognitionResult,
    ContextExpansionRequest,
)


_LEVEL_ORDER: tuple[AttentionLevel, ...] = (
    "focal",
    "contextual",
    "reflective",
)
_VALID_DOMAINS = {
    "memories",
    "relationships",
    "beliefs",
    "goals",
    "plans",
    "commitments",
    "roles",
    "anamnesis",
}
_SOCIAL_EVENTS = {
    "AgentSpoke",
    "CooperationProposed",
    "CooperationResponded",
    "DisputeOpened",
    "DisputeResponded",
}
ATTENTION_SYSTEM_INSTRUCTION = (
    "Puoi restituire il normale risultato cognitivo oppure, se il contesto non "
    "è sufficiente per decidere autonomamente, soltanto "
    '{"context_expansion":{"domains":[...],"anchor_ids":[...],"reason":"..."}}. '
    "Chiedi esclusivamente domini ammessi e anchor_id già visibili. Una richiesta "
    "non è un'azione e non deve contenere intenzione o aggiornamenti mentali."
)
COMPACT_SCHEMA_LEGEND = (
    "Legenda contratto: obj! vieta campi extra; field! obbligatorio; field? "
    "opzionale; oneof(A|B) richiede una sola forma; arr[min..max]<T> è un array; "
    "enum(a|b) limita i valori; [min..max], >n e len[min..max] sono vincoli."
)


@dataclass(frozen=True, slots=True)
class AttentionSelection:
    level: AttentionLevel
    reasons: tuple[str, ...]


class ExpandingProvider(Protocol):
    def decide(
        self, context: CognitionContext
    ) -> CognitionResult | ContextExpansionRequest: ...


def progressive_response_schema(decision_schema: dict[str, Any]) -> dict[str, Any]:
    expansion_schema = {
        "type": "object",
        "properties": {
            "context_expansion": {
                "type": "object",
                "properties": {
                    "domains": {
                        "type": "array",
                        "items": {"type": "string", "enum": sorted(_VALID_DOMAINS)},
                        "minItems": 1,
                        "maxItems": len(_VALID_DOMAINS),
                        "uniqueItems": True,
                    },
                    "anchor_ids": {
                        "type": "array",
                        "items": {"type": "string", "maxLength": 160},
                        "maxItems": 12,
                        "uniqueItems": True,
                    },
                    "reason": {"type": "string", "minLength": 1, "maxLength": 300},
                },
                "required": ["domains", "anchor_ids", "reason"],
                "additionalProperties": False,
            }
        },
        "required": ["context_expansion"],
        "additionalProperties": False,
    }
    return {"oneOf": [decision_schema, expansion_schema]}


def compact_schema_contract(schema: dict[str, Any]) -> str:
    """Render validation-relevant JSON Schema as a deterministic grammar."""

    def render(node: dict[str, Any]) -> str:
        if "oneOf" in node:
            return "oneof(" + "|".join(render(item) for item in node["oneOf"]) + ")"
        if "enum" in node:
            result = "enum(" + "|".join(
                json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                for value in node["enum"]
            ) + ")"
        else:
            raw_type = node.get("type", "any")
            types = raw_type if isinstance(raw_type, list) else [raw_type]
            if "object" in types:
                required = set(node.get("required", ()))
                closed = "!" if node.get("additionalProperties") is False else ""
                fields = [
                    f"{key}{'!' if key in required else '?'}:{render(value)}"
                    for key, value in node.get("properties", {}).items()
                ]
                result = f"obj{closed}" + "{" + ",".join(fields) + "}"
            elif "array" in types:
                bounds = _compact_bounds(
                    node, minimum_key="minItems", maximum_key="maxItems"
                )
                unique = "!unique" if node.get("uniqueItems") else ""
                result = f"arr{bounds}{unique}<" + render(node.get("items", {})) + ">"
            else:
                result = "|".join(str(value) for value in types)
        constraints = _compact_constraints(node)
        return result + constraints

    return render(schema)


def _compact_bounds(
    node: dict[str, Any], *, minimum_key: str, maximum_key: str
) -> str:
    minimum = node.get(minimum_key, "")
    maximum = node.get(maximum_key, "")
    return f"[{minimum}..{maximum}]" if minimum != "" or maximum != "" else ""


def _compact_constraints(node: dict[str, Any]) -> str:
    constraints: list[str] = []
    if "minLength" in node or "maxLength" in node:
        constraints.append(
            "len" + _compact_bounds(
                node, minimum_key="minLength", maximum_key="maxLength"
            )
        )
    if "minimum" in node or "maximum" in node:
        constraints.append(
            _compact_bounds(node, minimum_key="minimum", maximum_key="maximum")
        )
    if "exclusiveMinimum" in node:
        constraints.append(f">{node['exclusiveMinimum']}")
    return "" if not constraints else "[" + ";".join(constraints) + "]"


def parse_context_expansion(data: dict[str, Any]) -> ContextExpansionRequest:
    if set(data) != {"context_expansion"}:
        raise ValueError("context expansion must be the only response field")
    raw = data["context_expansion"]
    if not isinstance(raw, dict) or set(raw) != {"domains", "anchor_ids", "reason"}:
        raise ValueError("invalid context expansion shape")
    domains = raw["domains"]
    anchors = raw["anchor_ids"]
    reason = raw["reason"]
    if (
        not isinstance(domains, list)
        or not domains
        or len(domains) > len(_VALID_DOMAINS)
        or any(not isinstance(domain, str) for domain in domains)
        or len(set(domains)) != len(domains)
        or not set(domains) <= _VALID_DOMAINS
    ):
        raise ValueError("invalid context expansion domains")
    if (
        not isinstance(anchors, list)
        or len(anchors) > 12
        or any(
            not isinstance(anchor, str) or not anchor.strip() or len(anchor) > 160
            for anchor in anchors
        )
        or len(set(anchors)) != len(anchors)
    ):
        raise ValueError("invalid context expansion anchors")
    if not isinstance(reason, str) or not 0 < len(reason.strip()) <= 300:
        raise ValueError("invalid context expansion reason")
    return ContextExpansionRequest(
        domains=tuple(domains),  # type: ignore[arg-type]
        anchor_ids=tuple(anchors),
        reason=reason.strip(),
    )


def minimum_attention_level(context: CognitionContext) -> AttentionSelection:
    reasons: list[str] = []
    observed_types = {
        observation.event.event_type for observation in context.observations
    }
    somatic = project_somatic_state(context.material_state)
    if somatic["overall_condition"] in {"critical", "life_threatening"}:
        reasons.append("critical_somatic_state")
    if "ResonanceSignalReceived" in observed_types:
        reasons.append("resonance_signal")
    if context.active_disputes:
        reasons.append("active_dispute")
    if reasons:
        return AttentionSelection("reflective", tuple(reasons))

    if sum(
        observation.event.event_type == "ActionRejected"
        for observation in context.observations
    ) >= 2:
        reasons.append("repeated_action_rejection")
    if any(
        commitment.status == "active" and commitment.due_tick <= context.world_tick
        for commitment in context.mind.commitments.values()
    ):
        reasons.append("due_commitment")
    if context.nearby_agents:
        reasons.append("nearby_agent")
    if context.social_proposals or observed_types & _SOCIAL_EVENTS:
        reasons.append("direct_social_context")
    if reasons:
        return AttentionSelection("contextual", tuple(reasons))
    return AttentionSelection("focal", ("ordinary_activation",))


def select_attention_context(
    full: dict[str, Any], context: CognitionContext
) -> dict[str, Any]:
    level = context.attention_level
    if level == "full":
        return full
    selected = {
        key: value
        for key, value in full.items()
        if key
        in {
            "self",
            "local_affordances",
            "action_contracts",
            "social_affordances",
            "world_tick",
            "activation_reason",
            "observations",
            "nearby_agents",
        }
    }
    selected["self"] = dict(selected["self"])
    for key in ("goals", "plans", "commitments"):
        selected["self"].pop(key, None)
    selected["attention"] = {
        "level": level,
        "reasons": list(context.attention_reasons),
        "requested_domains": list(context.attention_domains),
    }
    if level == "focal":
        return selected
    if level == "reflective":
        reflective = dict(full)
        reflective["attention"] = selected["attention"]
        return reflective

    domains = set(context.attention_domains) or {
        "memories",
        "relationships",
        "beliefs",
        "goals",
        "plans",
        "commitments",
        "roles",
    }
    focus_terms = _focus_terms(context)
    if "goals" in domains:
        selected["self"]["goals"] = _matching_strings(
            full["self"]["goals"], focus_terms
        )
    if "plans" in domains:
        selected["self"]["plans"] = _matching_records(
            full["self"]["plans"], focus_terms
        )
    if "commitments" in domains:
        selected["self"]["commitments"] = _matching_commitments(
            full["self"]["commitments"], context, focus_terms
        )
    if "memories" in domains:
        selected["recent_memories"] = _matching_memories(
            full["recent_memories"], context, focus_terms
        )
    if "relationships" in domains:
        selected["relationships"] = [
            relationship
            for relationship in full["relationships"]
            if relationship["agent_id"] in _focus_agent_ids(context)
        ]
    if "beliefs" in domains:
        selected["beliefs"] = _matching_records(full["beliefs"], focus_terms)
    if "roles" in domains:
        selected["role_interpretations"] = [
            role
            for role in full["role_interpretations"]
            if role["subject_agent_id"] in _focus_agent_ids(context)
            or _record_matches(role, focus_terms)
        ]
    if "anamnesis" in domains:
        selected["anamnesis_fragments"] = _matching_records(
            full["anamnesis_fragments"], focus_terms
        )
    return selected


def visible_attention_source_ids(context: CognitionContext) -> tuple[str, ...]:
    identifiers: set[str] = {context.mind.agent_id}
    identifiers.update(agent_id for agent_id, _ in context.nearby_agents)
    for observation in context.observations:
        identifiers.add(observation.event.event_id)
        identifiers.update(observation.event.actor_ids)
    identifiers.update(resource.resource_id for resource in context.local_resources)
    identifiers.update(activity.activity_id for activity in context.available_activities)
    identifiers.update(node.node_id for node in context.local_resonance_nodes)
    identifiers.update(proposal.proposal_id for proposal in context.social_proposals)
    identifiers.update(dispute.dispute_id for dispute in context.active_disputes)
    identifiers.update(context.attention_anchor_ids)
    if context.attention_level in {"contextual", "reflective", "full"}:
        for memory in _visible_retrieved_memories(context):
            identifiers.add(memory.memory_id)
            identifiers.update(memory.memory_ids)
            identifiers.update(memory.source_event_ids)
        identifiers.update(_focus_agent_ids(context))
    return tuple(sorted(identifier for identifier in identifiers if identifier))


def _visible_retrieved_memories(context: CognitionContext) -> list[RetrievedMemory]:
    retrieved = retrieve_memories(context)
    if context.attention_level in {"reflective", "full"}:
        return retrieved
    domains = set(context.attention_domains)
    if domains and "memories" not in domains:
        return []
    matching_ids = {
        memory.memory_id
        for memory in context.mind.memories
        if _memory_matches(memory, context, _focus_terms(context))
    }
    return [
        memory
        for memory in retrieved
        if memory.memory_id in matching_ids
        or set(memory.memory_ids) & matching_ids
    ][:4]


class ProgressiveCognition:
    """Expands private attention without selecting or rewriting an action."""

    def __init__(self, provider: ExpandingProvider, *, max_expansions: int = 2) -> None:
        if max_expansions < 0 or max_expansions > 2:
            raise ValueError("progressive cognition supports at most two expansions")
        self.provider = provider
        self.max_expansions = max_expansions
        self._lock = RLock()
        self._decisions = 0
        self._deferred = 0
        self._expansions = 0
        self._by_level = {level: 0 for level in _LEVEL_ORDER}

    def decide(self, context: CognitionContext) -> CognitionResult:
        try:
            return self._decide(context)
        except CognitionUnavailable:
            with self._lock:
                self._deferred += 1
            raise

    def _decide(self, context: CognitionContext) -> CognitionResult:
        selection = minimum_attention_level(context)
        current = replace(
            context,
            attention_level=selection.level,
            attention_domains=(),
            attention_anchor_ids=(),
            attention_reasons=selection.reasons,
        )
        requested_domains: set[str] = set()
        expansions = 0
        while True:
            output = self.provider.decide(current)
            if isinstance(output, CognitionResult):
                result = replace(
                    output,
                    attention_level=current.attention_level,
                    attention_expansions=expansions,
                    attention_domains=tuple(sorted(requested_domains)),
                    attention_source_ids=visible_attention_source_ids(current),
                )
                with self._lock:
                    self._decisions += 1
                    self._expansions += expansions
                    self._by_level[current.attention_level] += 1
                return result
            if not isinstance(output, ContextExpansionRequest):
                raise CognitionUnavailable(
                    [{"model": "attention", "error": "unsupported cognition output"}]
                )
            if (
                expansions >= self.max_expansions
                or current.attention_level == "reflective"
            ):
                raise CognitionUnavailable(
                    [{"model": "attention", "error": "attention expansion ceiling reached"}]
                )
            visible = set(visible_attention_source_ids(current))
            unknown = set(output.anchor_ids) - visible
            invalid_domains = set(output.domains) - _VALID_DOMAINS
            if unknown or invalid_domains:
                raise CognitionUnavailable(
                    [
                        {
                            "model": "attention",
                            "error": "context expansion references inaccessible anchors or domains",
                        }
                    ]
                )
            expansions += 1
            requested_domains.update(output.domains)
            next_level = _LEVEL_ORDER[_LEVEL_ORDER.index(current.attention_level) + 1]
            current = replace(
                current,
                attention_level=next_level,
                attention_domains=tuple(sorted(requested_domains)),  # type: ignore[arg-type]
                attention_anchor_ids=tuple(
                    sorted(set(current.attention_anchor_ids) | set(output.anchor_ids))
                ),
                attention_reasons=(*current.attention_reasons, "mind_requested_context"),
            )

    def health(self) -> dict[str, object]:
        with self._lock:
            return {
                "enabled": True,
                "decisions": self._decisions,
                "deferred": self._deferred,
                "expansions": self._expansions,
                "by_level": dict(self._by_level),
                "max_expansions": self.max_expansions,
            }


def _focus_agent_ids(context: CognitionContext) -> set[str]:
    known_agents = {agent_id for agent_id, _ in context.nearby_agents}
    known_agents.update(
        anchor for anchor in context.attention_anchor_ids if anchor in context.mind.relationships
    )
    for observation in context.observations:
        known_agents.update(observation.event.actor_ids)
    return known_agents - {context.mind.agent_id}


def _focus_terms(context: CognitionContext) -> set[str]:
    values: list[str] = [context.activation_reason, *context.attention_anchor_ids]
    focus_agents = _focus_agent_ids(context)
    values.extend(name for agent_id, name in context.nearby_agents if agent_id in focus_agents)
    for observation in context.observations:
        values.extend((observation.event.event_type, observation.event.location or ""))
        values.extend(str(value) for value in observation.event.payload.values())
    return set(re.findall(r"\w+", " ".join(values).casefold()))


def _matching_strings(values: list[str], terms: set[str]) -> list[str]:
    return [value for value in values if _text_matches(value, terms)]


def _matching_records(
    values: list[dict[str, Any]], terms: set[str]
) -> list[dict[str, Any]]:
    return [value for value in values if _record_matches(value, terms)]


def _matching_commitments(
    values: list[dict[str, Any]], context: CognitionContext, terms: set[str]
) -> list[dict[str, Any]]:
    focus_agents = _focus_agent_ids(context)
    return [
        value
        for value in values
        if value["due_tick"] <= context.world_tick
        or set(value["involved_agent_ids"]) & focus_agents
        or _record_matches(value, terms)
    ]


def _matching_memories(
    values: list[dict[str, Any]], context: CognitionContext, terms: set[str]
) -> list[dict[str, Any]]:
    matching_ids = {
        memory.memory_id
        for memory in context.mind.memories
        if _memory_matches(memory, context, terms)
    }
    return [
        value
        for value in values
        if value["memory_id"] in matching_ids
        or set(value.get("memory_ids", ())) & matching_ids
    ][:4]


def _memory_matches(memory: Any, context: CognitionContext, terms: set[str]) -> bool:
    return bool(
        set(memory.participants) & _focus_agent_ids(context)
        or memory.memory_id in context.attention_anchor_ids
        or memory.source_event_id in context.attention_anchor_ids
        or _text_matches(memory.summary, terms)
    )


def _record_matches(value: dict[str, Any], terms: set[str]) -> bool:
    return _text_matches(" ".join(str(item) for item in value.values()), terms)


def _text_matches(value: str, terms: set[str]) -> bool:
    tokens = set(re.findall(r"\w+", value.casefold()))
    return bool(tokens & terms)
