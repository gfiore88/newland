from __future__ import annotations

from pathlib import Path
from typing import Self

from .arrivals import ArrivalProfile, ArrivalService
from .cognition import (
    ActivityAffordance,
    CognitionContext,
    CognitionProvider,
    CognitionUnavailable,
    CooperationAffordance,
    DisputeAffordance,
    MemoryAppraisal,
    ResonanceNodeAffordance,
    ResourceAffordance,
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


# NOTE: Test fixture profiles for seed_initial_encounter live in tests/helpers.py
# per ADR-0008 [AUT-007]. No static identity data in production code.


INITIAL_TERRITORY = {
    "locations": {
        "cittadina_iniziale": ["bosco_est", "campo_nord"],
        "campo_nord": ["cittadina_iniziale", "sorgente_chiara"],
        "bosco_est": ["cittadina_iniziale", "sorgente_chiara"],
        "sorgente_chiara": ["bosco_est", "campo_nord"],
    },
    "resources": {
        "deposito_legna_caduta": {
            "kind": "legna",
            "label": "legna caduta",
            "location": "bosco_est",
            "quantity": 80.0,
            "unit": "kg",
            "renewable": False,
        },
        "cespugli_bacche": {
            "kind": "bacche",
            "label": "bacche selvatiche",
            "location": "bosco_est",
            "quantity": 30.0,
            "unit": "kg",
            "renewable": True,
        },
        "vena_sorgente": {
            "kind": "acqua",
            "label": "acqua di sorgente",
            "location": "sorgente_chiara",
            "quantity": 500.0,
            "unit": "litri",
            "renewable": True,
        },
    },
    "resource_effects": {
        "acqua": {"thirst": 0.5},
        "bacche": {"hunger": 0.35, "energy": 0.05},
    },
    "activities": {
        "esaminare_edifici": {
            "label": "esaminare gli edifici silenziosi",
            "location": "cittadina_iniziale",
            "energy_cost": 0.01,
            "practiced_skill": "osservazione",
            "minimum_proficiency": 0.2,
            "skill_gain": 0.01,
        },
        "osservare_terreno": {
            "label": "osservare il terreno del campo",
            "location": "campo_nord",
            "energy_cost": 0.02,
            "practiced_skill": "osservazione",
            "minimum_proficiency": 0.2,
            "skill_gain": 0.01,
        },
        "esplorare_sottobosco": {
            "label": "esplorare il sottobosco",
            "location": "bosco_est",
            "energy_cost": 0.04,
            "practiced_skill": "orientamento",
            "minimum_proficiency": 0.25,
            "skill_gain": 0.015,
        },
        "ascoltare_sorgente": {
            "label": "ascoltare e osservare la sorgente",
            "location": "sorgente_chiara",
            "energy_cost": 0.01,
            "practiced_skill": "osservazione",
            "minimum_proficiency": 0.1,
            "skill_gain": 0.005,
        },
    },
    "resonance_nodes": {
        "eco_della_sorgente": {
            "label": "eco sottile della sorgente",
            "location": "sorgente_chiara",
            "intensity": 0.72,
        },
        "quiete_del_bosco": {
            "label": "quiete profonda del sottobosco",
            "location": "bosco_est",
            "intensity": 0.48,
        },
    },
}


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
        self.arrivals = ArrivalService()
        self.scheduler = ActivationScheduler()
        self.state = replay(self.store.events())
        self.minds = self.store.load_minds()
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return
        if self.store.event_count() > 0:
            if self.state.agents and not self.minds:
                raise RuntimeError(
                    "event store contains a world with agents but no persisted minds"
                )
            self._ensure_territory()
            self._rebuild_agenda()
            self._initialized = True
            return

        tick = 0
        world_time = world_time_for_tick(tick)
        events = [
            EventEnvelope(
                event_type="WorldInitialized",
                world_tick=tick,
                world_time=world_time,
                payload={"name": "Newland", **INITIAL_TERRITORY},
            )
        ]
        persisted = self.store.append_many(events)
        self.state = replay(persisted)
        self._initialized = True

    def _ensure_territory(self) -> None:
        if not self.state.resources or not self.state.activities:
            events = [
                EventEnvelope(
                    event_type="TerritoryConfigured",
                    world_tick=self.state.tick,
                    world_time=world_time_for_tick(self.state.tick),
                    payload=INITIAL_TERRITORY,
                )
            ]
        else:
            events = []
            if not all(
                activity.practiced_skill is not None
                for activity in self.state.activities.values()
            ):
                events.append(
                    EventEnvelope(
                        event_type="TerritoryActivitiesConfigured",
                        world_tick=self.state.tick,
                        world_time=world_time_for_tick(self.state.tick),
                        payload={"activities": INITIAL_TERRITORY["activities"]},
                    )
                )
            if not self.state.resonance_nodes:
                events.append(
                    EventEnvelope(
                        event_type="ResonanceNodesConfigured",
                        world_tick=self.state.tick,
                        world_time=world_time_for_tick(self.state.tick),
                        payload={
                            "resonance_nodes": INITIAL_TERRITORY["resonance_nodes"]
                        },
                    )
                )
        if not events:
            return
        persisted = self.store.append_many(events)
        for event in persisted:
            reduce_event(self.state, event)

    def seed_initial_encounter(
        self, profiles: tuple[ArrivalProfile, ...] | None = None
    ) -> None:
        """Seed world with test fixture profiles (ADR-0008 [AUT-007]: test doubles only)."""
        self.initialize()
        if not self.minds and profiles is not None:
            self.admit_arrivals(profiles)
        if self.scheduler:
            return
        self._rebuild_agenda()
        if not self.scheduler and self.minds:
            first_agent = min(self.minds)
            self.scheduler.schedule(
                first_agent,
                tick=max(1, self.state.tick + 1),
                reason="prima percezione cosciente nella cittadina",
                priority=10,
            )

    def admit_arrivals(
        self, profiles: tuple[ArrivalProfile, ...], *, tick: int | None = None
    ) -> list[EventEnvelope]:
        self.initialize()
        arrival_tick = self.state.tick if tick is None else tick
        events = self.arrivals.prepare(self.state, profiles, tick=arrival_tick)
        minds = tuple(
            AgentMind.from_dict(profile.mind.to_dict()) for profile in profiles
        )
        persisted = self.store.append_many_with_minds(events, minds)
        for event in persisted:
            reduce_event(self.state, event)
        for mind in minds:
            self.minds[mind.agent_id] = mind
            self.scheduler.schedule(
                mind.agent_id,
                tick=max(1, arrival_tick + 1),
                reason="esperienza privata della transizione e nuovo ambiente",
                priority=5,
            )
        new_ids = {mind.agent_id for mind in minds}
        for event in persisted:
            if event.event_type != "AgentArrived":
                continue
            for observer_id in event.recipient_ids:
                if observer_id in new_ids:
                    continue
                self.scheduler.schedule(
                    observer_id,
                    tick=max(1, arrival_tick + 1),
                    reason=f"nuovo arrivo osservato: {event.actor_ids[0]}",
                    priority=15,
                )
        return persisted

    def _rebuild_agenda(self) -> None:
        for agent_id, mind in self.minds.items():
            if self.state.agents[agent_id].is_dead:
                continue
            unseen = self.store.events(after_sequence=mind.last_perceived_sequence)
            if self.perception.perceive(
                agent_id,
                unseen,
                resonance_receptive=mind.resonance_receptive,
            ):
                self.scheduler.schedule(
                    agent_id,
                    tick=max(1, self.state.tick),
                    reason="eventi percepibili non ancora elaborati",
                    priority=20,
                )
            if mind.next_activation_tick is not None:
                self.scheduler.schedule(
                    agent_id,
                    tick=max(self.state.tick, mind.next_activation_tick),
                    reason=mind.next_activation_reason,
                    priority=50,
                )
            for commitment in mind.commitments.values():
                if commitment.status == "active":
                    self.scheduler.schedule(
                        agent_id,
                        tick=max(self.state.tick, commitment.due_tick),
                        reason=f"impegno generato: {commitment.description}",
                        priority=30,
                    )
            if not self.scheduler:
                self.scheduler.schedule(
                    agent_id,
                    tick=max(1, self.state.tick),
                    reason="presenza cosciente nel mondo",
                    priority=10,
                )

    def _sync_with_store(self) -> None:
        latest_minds = self.store.load_minds()
        new_agent_ids = set(latest_minds) - set(self.minds)
        if new_agent_ids:
            self.minds = latest_minds
            self.state = replay(self.store.events())
            self._rebuild_agenda()

    def run(self, *, max_activations: int = 8) -> list[EventEnvelope]:
        self.initialize()
        self._sync_with_store()
        if not self.scheduler and self.minds:
            self._rebuild_agenda()
        produced: list[EventEnvelope] = []
        activations = 0
        while self.scheduler and activations < max_activations:
            activation = self.scheduler.pop()
            if activation is None:
                break
            if self.state.agents[activation.agent_id].is_dead:
                continue
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
        observations = self.perception.perceive(
            agent_id,
            unseen,
            resonance_receptive=mind.resonance_receptive,
        )

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
            world_tick=tick,
            adjacent_locations=tuple(sorted(self.state.locations[material.location])),
            local_resources=tuple(
                ResourceAffordance(
                    resource_id=resource.resource_id,
                    kind=resource.kind,
                    label=resource.label,
                    quantity=resource.quantity,
                    unit=resource.unit,
                )
                for resource in self.state.resources_at(material.location)
            ),
            available_activities=tuple(
                ActivityAffordance(
                    activity_id=activity.activity_id,
                    label=activity.label,
                    practiced_skill=activity.practiced_skill,
                    minimum_proficiency=activity.minimum_proficiency,
                )
                for activity in self.state.activities_at(material.location)
            ),
            local_resonance_nodes=tuple(
                ResonanceNodeAffordance(
                    node_id=node.node_id,
                    label=node.label,
                    intensity=node.intensity,
                )
                for node in self.state.resonance_nodes_at(material.location)
            ),
            social_proposals=tuple(
                CooperationAffordance(
                    proposal_id=proposal.proposal_id,
                    proposer_id=proposal.proposer_id,
                    target_id=proposal.target_id,
                    activity_id=proposal.activity_id,
                    status=proposal.status,
                )
                for proposal in self.state.cooperations.values()
                if agent_id in {proposal.proposer_id, proposal.target_id}
                and proposal.status in {"pending", "accepted"}
            ),
            active_disputes=tuple(
                DisputeAffordance(
                    dispute_id=dispute.dispute_id,
                    opener_id=dispute.opener_id,
                    target_id=dispute.target_id,
                    subject_event_id=dispute.subject_event_id,
                    status=dispute.status,
                    resolution_offered_by=dispute.resolution_offered_by,
                )
                for dispute in self.state.disputes.values()
                if agent_id in {dispute.opener_id, dispute.target_id}
                and dispute.status != "resolved"
            ),
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
        next_activation_tick = (
            tick + cognition_result.attention_schedule.next_activation_in_ticks
        )
        working_mind.next_activation_tick = next_activation_tick
        working_mind.next_activation_reason = cognition_result.attention_schedule.reason
        attention_event = EventEnvelope(
            event_type="AttentionScheduled",
            world_tick=tick,
            world_time=world_time_for_tick(tick),
            actor_ids=(working_mind.agent_id,),
            payload={
                "next_activation_tick": next_activation_tick,
                "reason": cognition_result.attention_schedule.reason,
                "cognition": cognition_result.provenance(),
            },
            visibility="private",
            recipient_ids=(working_mind.agent_id,),
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
        activation_events = [
            *memory_events,
            *mental_events,
            attention_event,
            *pending,
        ]
        persisted = self.store.append_many_with_mind(activation_events, working_mind)
        self.minds[agent_id] = working_mind
        pending_ids = {event.event_id for event in pending}
        persisted_pending = [
            event for event in persisted if event.event_id in pending_ids
        ]
        for event in persisted:
            reduce_event(self.state, event)
        self._schedule_generated_agenda(working_mind, tick=tick)
        self._schedule_reactions(agent_id, tick, persisted_pending)
        return persisted

    def _schedule_generated_agenda(self, mind: AgentMind, *, tick: int) -> None:
        if mind.next_activation_tick is not None:
            self.scheduler.schedule(
                mind.agent_id,
                tick=mind.next_activation_tick,
                reason=mind.next_activation_reason,
                priority=50,
            )
        for commitment in mind.commitments.values():
            if commitment.status == "active" and commitment.due_tick > tick:
                self.scheduler.schedule(
                    mind.agent_id,
                    tick=commitment.due_tick,
                    reason=f"impegno generato: {commitment.description}",
                    priority=30,
                )

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
            if event.event_type == "ResonanceSignalReceived":
                if self.minds[actor_id].resonance_receptive:
                    self.scheduler.schedule(
                        actor_id,
                        tick=tick + 1,
                        reason="segnale corporeo di risonanza percepito",
                        priority=5,
                    )
                continue
            if event.event_type in {"SpeechUttered", "HelpOffered"}:
                target_id = event.payload.get("target_id")
                if target_id and target_id != actor_id:
                    self.scheduler.schedule(
                        target_id,
                        tick=tick + 1,
                        reason=f"reazione a {event.event_type} di {actor_id}",
                        priority=20,
                    )
                continue
            if event.event_type in {
                "CooperationProposed",
                "DisputeOpened",
            }:
                target_id = event.payload.get("target_id")
                if target_id and target_id != actor_id:
                    self.scheduler.schedule(
                        target_id,
                        tick=tick + 1,
                        reason=f"risposta autonoma a {event.event_type}",
                        priority=15,
                    )
                continue
            if event.event_type in {
                "CooperationResponded",
                "DisputeResponded",
            }:
                participants = {
                    event.payload.get("proposer_id"),
                    event.payload.get("opener_id"),
                    event.payload.get("target_id"),
                } - {None, actor_id}
                for participant_id in participants:
                    self.scheduler.schedule(
                        participant_id,
                        tick=tick + 1,
                        reason=f"esito sociale percepito: {event.event_type}",
                        priority=15,
                    )
                continue
            if event.event_type not in {
                "AgentMoved",
                "AgentRested",
                "ResourceGathered",
                "ResourceConsumed",
                "ActivityPerformed",
                "CooperationPerformed",
                "ResonanceAttunementPerformed",
            }:
                continue
            for observer_id in event.recipient_ids:
                if observer_id == actor_id:
                    continue
                self.scheduler.schedule(
                    observer_id,
                    tick=tick + 1,
                    reason=f"evento locale osservabile: {event.event_type}",
                    priority=25,
                )

    def close(self) -> None:
        self.store.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
