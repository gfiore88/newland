from __future__ import annotations

import heapq
from dataclasses import dataclass, field


@dataclass(order=True, slots=True)
class Activation:
    tick: int
    priority: int
    agent_id: str
    reason: str = field(compare=False)


class ActivationScheduler:
    def __init__(self) -> None:
        self._queue: list[Activation] = []
        self._scheduled: set[tuple[int, str]] = set()

    def schedule(
        self, agent_id: str, *, tick: int, reason: str, priority: int = 100
    ) -> None:
        key = (tick, agent_id)
        if key in self._scheduled:
            return
        self._scheduled.add(key)
        heapq.heappush(self._queue, Activation(tick, priority, agent_id, reason))

    def pop(self) -> Activation | None:
        if not self._queue:
            return None
        activation = heapq.heappop(self._queue)
        self._scheduled.discard((activation.tick, activation.agent_id))
        return activation

    def pending(self) -> tuple[Activation, ...]:
        return tuple(sorted(self._queue))

    def __bool__(self) -> bool:
        return bool(self._queue)
