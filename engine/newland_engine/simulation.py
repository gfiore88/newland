from __future__ import annotations

from pathlib import Path
from typing import Self

from .cognition import (
    CognitionContext,
    CognitionProvider,
    CognitionUnavailable,
    MemoryAppraisal,
    validate_cognition_result,
)
from .event_store import EventStore
from .mental_state import MentalStateApplier, MindMutation
from .models import (
    AgentMind,
    EventEnvelope,
    Memory,
    world_time_for_tick,
)
from .perception import Observation, PerceptionService
from .physiology import PhysiologySystem
from .scheduler import ActivationScheduler
from .world import WorldAdjudicator, reduce_event, replay

DEFAULT_AGENTS = (
    AgentMind(
        agent_id="nwl-001",
        name="Elia Moretti",
        values=["cura", "sincerità", "custodia"],
        temperament=["meditativo", "pragmatico", "melanconico"],
        goals=["comprendere la cittadina senza forzare risposte"],
    ),
    AgentMind(
        agent_id="nwl-002",
        name="Amina Haddad",
        values=["dignità", "reciprocità", "prudenza"],
        temperament=["osservatrice", "riservata", "tenace"],
        goals=["trovare un ritmo sicuro nel nuovo luogo"],
    ),
)


class NewlandSimulation:
    def __init__(
        self, database_path: str | Path, cognition: CognitionProvider | None = None
    ) -> None:
        self.store = EventStore(database_path)
        if cognition is None:
            raise ValueError("a generative cognition provider is required")
        self.cognition = cognition
        self.perception = PerceptionService()
        self.mental_state = MentalStateApplier()
        self.physiology = PhysiologySystem()
        self.adjudicator = WorldAdjudicator()
        self.scheduler = ActivationScheduler()
        self.state = replay(self.store.events())
        self.minds = self.store.load_minds()

    def initialize(self) -> None:
        if self.store.event_count() > 0:
            if not self.minds:
                raise RuntimeError(
                    "event store contains a world but no persisted minds"
                )
            return

        minds = {
            mind.agent_id: AgentMind.from_dict(mind.to_dict())
            for mind in DEFAULT_AGENTS
        }
        tick = 0
        world_time = world_time_for_tick(tick)
        location = "cittadina_iniziale"
        all_agents = tuple(sorted(minds))
        events = [
            EventEnvelope(
                event_type="WorldInitialized",
                world_tick=tick,
                world_time=world_time,
                payload={
                    "name": "Newland",
                    "locations": {
                        "cittadina_iniziale": ["campo_nord"],
                        "campo_nord": ["cittadina_iniziale"],
                    },
                },
            )
        ]
        for mind in minds.values():
            events.extend(
                [
                    EventEnvelope(
                        event_type="AgentRegistered",
                        world_tick=tick,
                        world_time=world_time,
                        actor_ids=(mind.agent_id,),
                        location=location,
                        payload={
                            "name": mind.name,
                            "location": location,
                            "energy": 0.8,
                            "hunger": 0.1,
                            "thirst": 0.1,
                        },
                        visibility="private",
                        recipient_ids=(mind.agent_id,),
                    ),
                    EventEnvelope(
                        event_type="AgentArrived",
                        world_tick=tick,
                        world_time=world_time,
                        actor_ids=(mind.agent_id,),
                        location=location,
                        payload={"name": mind.name},
                        visibility="local",
                        recipient_ids=all_agents,
                    ),
                ]
            )
        persisted = self.store.append_many(events)
        self.state = replay(persisted)
        self.minds = minds
        for mind in self.minds.values():
            self.store.save_mind(mind)

    def seed_initial_encounter(self) -> None:
        self.initialize()
        if not self.scheduler:
            first_agent = min(self.minds)
            self.scheduler.schedule(
                first_agent,
                tick=max(1, self.state.tick + 1),
                reason="prima presenza umana percepita nella cittadina",
                priority=10,
            )

    def run(self, *, max_activations: int = 8) -> list[EventEnvelope]:
        self.seed_initial_encounter()
        produced: list[EventEnvelope] = []
        activations = 0
        while self.scheduler and activations < max_activations:
            activation = self.scheduler.pop()
            if activation is None:
                break
            produced.extend(
                self._advance_physiology(
                    to_tick=activation.tick,
                    activating_agent_id=activation.agent_id,
                )
            )
            produced.extend(
                self._activate(activation.agent_id, activation.tick, activation.reason)
            )
            activations += 1
        return produced

    def _advance_physiology(
        self, *, to_tick: int, activating_agent_id: str
    ) -> list[EventEnvelope]:
        advance = self.physiology.advance(self.state, to_tick=to_tick)
        if not advance.events:
            return []
        persisted = self.store.append_many(advance.events)
        for event in persisted:
            reduce_event(self.state, event)
        for agent_id in advance.interrupted_agent_ids:
            if agent_id == activating_agent_id:
                continue
            self.scheduler.schedule(
                agent_id,
                tick=to_tick,
                reason="segnale corporeo oltre soglia percettiva",
                priority=0,
            )
        return persisted

    def _activate(self, agent_id: str, tick: int, reason: str) -> list[EventEnvelope]:
        mind = self.minds[agent_id]
        unseen = self.store.events(after_sequence=mind.last_perceived_sequence)
        observations = self.perception.perceive(agent_id, unseen)

        material = self.state.agents[agent_id]
        nearby = tuple(
            (other_id, self.state.agents[other_id].name)
            for other_id in self.state.agents_at(material.location)
            if other_id != agent_id
        )
        context = CognitionContext(
            mind=mind,
            material_state=material,
            observations=tuple(observations),
            nearby_agents=nearby,
            activation_reason=reason,
        )
        try:
            cognition_result = self.cognition.decide(context)
            validate_cognition_result(cognition_result, context)
        except CognitionUnavailable as error:
            return self._defer_cognition(
                mind,
                tick=tick,
                reason=reason,
                failures=error.failures,
            )
        except (TypeError, ValueError) as error:
            return self._defer_cognition(
                mind,
                tick=tick,
                reason=reason,
                failures=[{"model": "provider-validation", "error": str(error)}],
            )

        working_mind = AgentMind.from_dict(mind.to_dict())
        intention = cognition_result.intention
        try:
            encoded = self._apply_memory_appraisals(
                working_mind, observations, cognition_result.memory_appraisals
            )
        except ValueError as error:
            return self._defer_cognition(
                mind,
                tick=tick,
                reason=reason,
                failures=[
                    {
                        "model": cognition_result.model,
                        "error": f"invalid generative memory appraisal: {error}",
                    }
                ],
            )
        memory_events = self._memory_events(working_mind, encoded, tick=tick)
        mental_mutations = self.mental_state.apply(
            working_mind, cognition_result.mental_updates, tick=tick
        )
        mental_events = self._mental_events(
            working_mind,
            mental_mutations,
            tick=tick,
            cognition=cognition_result.provenance(),
        )
        if unseen and unseen[-1].sequence is not None:
            working_mind.last_perceived_sequence = unseen[-1].sequence
        pending = self.adjudicator.adjudicate(
            self.state,
            agent_id,
            intention,
            tick=tick,
            cognition=cognition_result.provenance(),
        )
        activation_events = [*memory_events, *mental_events, *pending]
        persisted = self.store.append_many_with_mind(activation_events, working_mind)
        self.minds[agent_id] = working_mind
        pending_ids = {event.event_id for event in pending}
        persisted_pending = [
            event for event in persisted if event.event_id in pending_ids
        ]
        for event in persisted_pending:
            reduce_event(self.state, event)
        self._schedule_reactions(agent_id, tick, persisted_pending)
        return persisted

    @staticmethod
    def _mental_events(
        mind: AgentMind,
        mutations: list[MindMutation],
        *,
        tick: int,
        cognition: dict[str, object],
    ) -> list[EventEnvelope]:
        return [
            EventEnvelope(
                event_type=mutation.event_type,
                world_tick=tick,
                world_time=world_time_for_tick(tick),
                actor_ids=(mind.agent_id,),
                payload={
                    **mutation.payload,
                    "source_event_ids": mutation.source_event_ids,
                    "source_memory_ids": mutation.source_memory_ids,
                    "cognition": cognition,
                },
                visibility="private",
                recipient_ids=(mind.agent_id,),
                causation_id=(
                    mutation.source_event_ids[0] if mutation.source_event_ids else None
                ),
            )
            for mutation in mutations
        ]

    @staticmethod
    def _apply_memory_appraisals(
        mind: AgentMind,
        observations: list[Observation],
        appraisals: tuple[MemoryAppraisal, ...],
    ) -> list[Memory]:
        events_by_id = {
            observation.event.event_id: observation.event
            for observation in observations
        }
        memories: list[Memory] = []
        for appraisal in appraisals:
            event = events_by_id.get(appraisal.source_event_id)
            if event is None:
                raise ValueError(
                    "cognition appraised an event outside its perception boundary"
                )
            memory = mind.remember(
                event,
                appraisal.subjective_summary,
                salience=appraisal.salience,
                emotional_tone=appraisal.emotional_tone,
                confidence=appraisal.confidence,
            )
            if memory is not None:
                memories.append(memory)
        return memories

    def _defer_cognition(
        self,
        mind: AgentMind,
        *,
        tick: int,
        reason: str,
        failures: list[dict[str, str]],
    ) -> list[EventEnvelope]:
        deferred = EventEnvelope(
            event_type="CognitionDeferred",
            world_tick=tick,
            world_time=world_time_for_tick(tick),
            actor_ids=(mind.agent_id,),
            location=self.state.agents[mind.agent_id].location,
            payload={
                "activation_reason": reason,
                "failures": failures,
                "retry_tick": tick + 1,
            },
            visibility="private",
            recipient_ids=(mind.agent_id,),
        )
        persisted = self.store.append_many_with_mind([deferred], mind)
        self.scheduler.schedule(
            mind.agent_id,
            tick=tick + 1,
            reason="ripresa di una deliberazione generativa differita",
            priority=5,
        )
        return persisted

    @staticmethod
    def _memory_events(
        mind: AgentMind, memories: list[Memory], *, tick: int
    ) -> list[EventEnvelope]:
        return [
            EventEnvelope(
                event_type="MemoryEncoded",
                world_tick=tick,
                world_time=world_time_for_tick(tick),
                actor_ids=(mind.agent_id,),
                payload={
                    "memory_id": memory.memory_id,
                    "source_event_id": memory.source_event_id,
                    "summary": memory.summary,
                    "salience": memory.salience,
                    "emotional_tone": memory.emotional_tone,
                    "confidence": memory.confidence,
                },
                visibility="private",
                recipient_ids=(mind.agent_id,),
                causation_id=memory.source_event_id,
            )
            for memory in memories
        ]

    def _schedule_reactions(
        self, actor_id: str, tick: int, events: list[EventEnvelope]
    ) -> None:
        for event in events:
            if event.event_type not in {"SpeechUttered", "HelpOffered"}:
                continue
            target_id = event.payload.get("target_id")
            if target_id and target_id != actor_id:
                self.scheduler.schedule(
                    target_id,
                    tick=tick + 1,
                    reason=f"reazione a {event.event_type} di {actor_id}",
                    priority=20,
                )

    def close(self) -> None:
        self.store.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
