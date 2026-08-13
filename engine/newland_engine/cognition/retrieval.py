from typing import Sequence
from ..models import Memory
from .types import CognitionContext

def retrieve_memories(
    context: CognitionContext,
    limit: int = 12,
    salience_weight: float = 0.5,
    recency_weight: float = 0.5,
) -> list[Memory]:
    """Retrieve the most relevant memories for the current cognitive context."""
    if not context.mind.memories:
        return []

    current_tick = context.world_tick
    
    def score_memory(memory: Memory) -> float:
        # Recency score (0.0 to 1.0)
        age = current_tick - memory.created_tick
        # Decay over time, max score at age 0, decays to 0 at age 1000
        recency = max(0.0, 1.0 - (age / 1000.0))
        
        score = (memory.salience * salience_weight) + (recency * recency_weight)
        
        # Context bonuses
        summary_lower = memory.summary.lower()
        
        # Bonus if memory mentions the current location
        if context.material_state.location and context.material_state.location.lower() in summary_lower:
            score += 0.2
            
        # Bonus if memory mentions a nearby agent
        for _, name in context.nearby_agents:
            if name.lower() in summary_lower:
                score += 0.2
                
        return score

    # Sort by score descending
    scored_memories = sorted(context.mind.memories, key=score_memory, reverse=True)
    
    # Take top N
    top_memories = scored_memories[:limit]
    
    # Re-sort chronologically for the LLM prompt to maintain temporal coherence
    return sorted(top_memories, key=lambda m: m.created_tick)
