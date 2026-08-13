from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher

from ..models import Memory
from .types import CognitionContext


@dataclass(frozen=True, slots=True)
class RetrievedMemory:
    memory_id: str
    summary: str
    salience: float
    emotional_tone: str
    confidence: float
    created_tick: int
    occurrence_count: int
    memory_ids: tuple[str, ...]
    source_event_ids: tuple[str, ...]


def retrieve_memories(
    context: CognitionContext,
    limit: int = 12,
    salience_weight: float = 0.5,
    recency_weight: float = 0.5,
) -> list[RetrievedMemory]:
    """Retrieve diverse memory groups without changing the stored memories."""
    if not context.mind.memories:
        return []

    def score_memory(memory: Memory) -> float:
        age = context.world_tick - memory.created_tick
        recency = max(0.0, 1.0 - (age / 1000.0))
        score = (memory.salience * salience_weight) + (recency * recency_weight)
        summary_lower = memory.summary.lower()
        if (
            context.material_state.location
            and context.material_state.location.lower() in summary_lower
        ):
            score += 0.2
        for _, name in context.nearby_agents:
            if name.lower() in summary_lower:
                score += 0.2
        return score

    groups: list[list[Memory]] = []
    normalized_representatives: list[str] = []
    for memory in sorted(context.mind.memories, key=lambda item: item.created_tick):
        normalized = _normalize_summary(memory.summary)
        matching_index = next(
            (
                index
                for index, representative in enumerate(normalized_representatives)
                if _summaries_equivalent(normalized, representative)
            ),
            None,
        )
        if matching_index is None:
            groups.append([memory])
            normalized_representatives.append(normalized)
        else:
            groups[matching_index].append(memory)

    retrieved: list[tuple[float, RetrievedMemory]] = []
    for group in groups:
        representative = max(
            group, key=lambda memory: (score_memory(memory), memory.created_tick)
        )
        retrieved.append(
            (
                score_memory(representative),
                RetrievedMemory(
                    memory_id=representative.memory_id,
                    summary=representative.summary,
                    salience=representative.salience,
                    emotional_tone=representative.emotional_tone,
                    confidence=representative.confidence,
                    created_tick=representative.created_tick,
                    occurrence_count=len(group),
                    memory_ids=tuple(memory.memory_id for memory in group),
                    source_event_ids=tuple(memory.source_event_id for memory in group),
                ),
            )
        )

    top_groups = sorted(
        retrieved, key=lambda item: (item[0], item[1].created_tick), reverse=True
    )[:limit]
    return sorted(
        (memory for _, memory in top_groups), key=lambda memory: memory.created_tick
    )


def _normalize_summary(summary: str) -> str:
    normalized = unicodedata.normalize("NFKC", summary).casefold()
    return " ".join(re.findall(r"\w+", normalized, flags=re.UNICODE))


def _summaries_equivalent(left: str, right: str) -> bool:
    if left == right:
        return True
    if not left or not right:
        return False
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    token_union = left_tokens | right_tokens
    token_similarity = (
        len(left_tokens & right_tokens) / len(token_union) if token_union else 1.0
    )
    sequence_similarity = SequenceMatcher(None, left, right).ratio()
    return token_similarity >= 0.9 or sequence_similarity >= 0.94
