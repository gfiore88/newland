from __future__ import annotations

from dataclasses import dataclass

from .models import EventEnvelope

PERCEPTIBLE_EVENT_TYPES = {
    "AgentArrived",
    "AgentMoved",
    "AgentRested",
    "SpeechUttered",
    "HelpOffered",
    "ActionRejected",
    "NeedsChanged",
    "ResourceGathered",
    "ResourceConsumed",
    "ActivityPerformed",
}


@dataclass(frozen=True, slots=True)
class Observation:
    event: EventEnvelope


class PerceptionService:
    def perceive(self, agent_id: str, events: list[EventEnvelope]) -> list[Observation]:
        visible: list[Observation] = []
        for event in events:
            if event.event_type not in PERCEPTIBLE_EVENT_TYPES:
                continue
            if not self._visible_to(agent_id, event):
                continue
            visible.append(Observation(event=event))
        return visible

    @staticmethod
    def _visible_to(agent_id: str, event: EventEnvelope) -> bool:
        if event.visibility == "public":
            return True
        return agent_id in event.recipient_ids
