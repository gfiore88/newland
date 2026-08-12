from __future__ import annotations

from uuid import uuid4

from newland_engine.cognition import (
    AffectRevision,
    AttentionSchedule,
    BeliefRevision,
    CognitionContext,
    CognitionResult,
    CognitionUnavailable,
    CommitmentRevision,
    GoalRevision,
    MemoryAppraisal,
    MentalUpdates,
    PlanRevision,
    ReflectionDraft,
    RelationshipRevision,
)
from newland_engine.models import Intention


class ScriptedTestCognition:
    """Engine test double. It is deliberately unavailable to the production CLI."""

    def decide(self, context: CognitionContext) -> CognitionResult:
        incoming = [
            observation.event
            for observation in context.observations
            if observation.event.event_type == "SpeechUttered"
            and observation.event.payload.get("target_id") == context.mind.agent_id
        ]
        if incoming:
            intention = Intention(
                action_type="speak",
                target_id=incoming[-1].actor_ids[0],
                spoken_content="Risposta generata dal test double.",
                motivation_summary="Verificare il ciclo di reazione.",
                confidence=0.9,
            )
        else:
            target_id = context.nearby_agents[0][0]
            intention = Intention(
                action_type="speak",
                target_id=target_id,
                spoken_content="Saluto generato dal test double.",
                motivation_summary="Verificare l'inizio dell'interazione.",
                confidence=0.9,
            )
        return CognitionResult(
            intention=intention,
            memory_appraisals=tuple(
                MemoryAppraisal(
                    source_event_id=observation.event.event_id,
                    subjective_summary=f"Valutazione generativa di test: {observation.event.event_type}",
                    salience=0.7,
                    emotional_tone="attenzione",
                    confidence=0.9,
                )
                for observation in context.observations
            ),
            mental_updates=MentalUpdates(),
            attention_schedule=AttentionSchedule(
                next_activation_in_ticks=6,
                reason="Riesaminare autonomamente la situazione.",
            ),
            provider="test-double",
            model="scripted-invariant-fixture",
            inference_id=str(uuid4()),
            attempts=1,
        )


class UnavailableTestCognition:
    def decide(self, context: CognitionContext) -> CognitionResult:
        raise CognitionUnavailable(
            [{"model": "unavailable-test-provider", "error": "forced outage"}]
        )


class InvalidAppraisalTestCognition:
    def decide(self, context: CognitionContext) -> CognitionResult:
        return CognitionResult(
            intention=Intention(
                action_type="rest",
                motivation_summary="Intento che non deve essere committato.",
            ),
            memory_appraisals=(
                MemoryAppraisal(
                    source_event_id="evento-mai-percepito",
                    subjective_summary="Interpretazione non autorizzata.",
                    salience=1.0,
                    emotional_tone="impossibile",
                    confidence=1.0,
                ),
            ),
            mental_updates=MentalUpdates(),
            attention_schedule=AttentionSchedule(
                next_activation_in_ticks=6,
                reason="Riesaminare autonomamente la situazione.",
            ),
            provider="test-double",
            model="invalid-appraisal-fixture",
            inference_id=str(uuid4()),
            attempts=1,
        )


class GeneratedMentalStateTestCognition:
    def decide(self, context: CognitionContext) -> CognitionResult:
        source_event_id = context.observations[-1].event.event_id
        other_id = context.nearby_agents[0][0]
        return CognitionResult(
            intention=Intention(
                action_type="rest",
                duration_minutes=5,
                motivation_summary="Azione generata dal fixture mentale.",
                confidence=0.8,
            ),
            memory_appraisals=(
                MemoryAppraisal(
                    source_event_id=source_event_id,
                    subjective_summary="Interpreto la presenza dell'altro come significativa.",
                    salience=0.85,
                    emotional_tone="cauta apertura",
                    confidence=0.8,
                ),
            ),
            mental_updates=MentalUpdates(
                beliefs=(
                    BeliefRevision(
                        key="non_sono_solo",
                        statement="Un'altra persona è realmente qui con me.",
                        confidence=0.88,
                        source_event_ids=(source_event_id,),
                    ),
                ),
                relationships=(
                    RelationshipRevision(
                        other_agent_id=other_id,
                        familiarity_delta=0.1,
                        trust_delta=0.04,
                        warmth_delta=0.08,
                        tension_delta=-0.02,
                        interpretation="La sua presenza attenua il senso di isolamento.",
                        source_event_ids=(source_event_id,),
                    ),
                ),
                affect=AffectRevision(
                    calm_delta=0.05,
                    curiosity_delta=0.08,
                    melancholy_delta=-0.04,
                    interpretation="La presenza umana modifica il mio stato interiore.",
                    source_event_ids=(source_event_id,),
                ),
                goals=(
                    GoalRevision(
                        operation="add",
                        goal="conoscere con prudenza l'altra persona",
                        reason="La presenza osservata rende possibile una relazione.",
                        source_event_ids=(source_event_id,),
                    ),
                ),
            ),
            attention_schedule=AttentionSchedule(
                next_activation_in_ticks=7,
                reason="Valutare come evolve la presenza condivisa.",
            ),
            provider="test-double",
            model="generated-mental-state-fixture",
            inference_id=str(uuid4()),
            attempts=1,
        )


class GeneratedReflectionTestCognition:
    def decide(self, context: CognitionContext) -> CognitionResult:
        memory_id = context.mind.memories[0].memory_id
        return CognitionResult(
            intention=Intention(
                action_type="rest",
                duration_minutes=5,
                motivation_summary="Integrare ciò che è già accaduto.",
                confidence=0.8,
            ),
            memory_appraisals=tuple(
                MemoryAppraisal(
                    source_event_id=observation.event.event_id,
                    subjective_summary="Un nuovo dettaglio si lega a ciò che ricordo.",
                    salience=0.6,
                    emotional_tone="riflessivo",
                    confidence=0.75,
                )
                for observation in context.observations
            ),
            mental_updates=MentalUpdates(
                reflections=(
                    ReflectionDraft(
                        statement="La presenza condivisa cambia il significato dell'arrivo.",
                        confidence=0.82,
                        source_memory_ids=(memory_id,),
                    ),
                )
            ),
            attention_schedule=AttentionSchedule(
                next_activation_in_ticks=8,
                reason="Lasciare sedimentare la riflessione.",
            ),
            provider="test-double",
            model="generated-reflection-fixture",
            inference_id=str(uuid4()),
            attempts=1,
        )


class GeneratedAgendaTestCognition:
    def decide(self, context: CognitionContext) -> CognitionResult:
        source_event_id = context.observations[-1].event.event_id
        other_id = context.nearby_agents[0][0]
        return CognitionResult(
            intention=Intention(
                action_type="rest",
                duration_minutes=5,
                motivation_summary="Preparare un incontro scelto autonomamente.",
                confidence=0.84,
            ),
            memory_appraisals=(),
            mental_updates=MentalUpdates(
                plans=(
                    PlanRevision(
                        operation="upsert",
                        plan_key="incontro_cauto",
                        description="Avvicinarmi con prudenza all'altra persona.",
                        steps=("Osservare", "Scegliere un momento", "Parlare"),
                        source_event_ids=(source_event_id,),
                    ),
                ),
                commitments=(
                    CommitmentRevision(
                        operation="add",
                        commitment_key="parlare_con_altro",
                        description="Riconsiderare se parlare con l'altra persona.",
                        due_tick=context.world_tick + 3,
                        involved_agent_ids=(other_id,),
                        source_event_ids=(source_event_id,),
                    ),
                ),
            ),
            attention_schedule=AttentionSchedule(
                next_activation_in_ticks=9,
                reason="Rivedere il piano quando avrò osservato abbastanza.",
            ),
            provider="test-double",
            model="generated-agenda-fixture",
            inference_id=str(uuid4()),
            attempts=1,
        )


class InvalidCommitmentTestCognition:
    def decide(self, context: CognitionContext) -> CognitionResult:
        source_event_id = context.observations[-1].event.event_id
        return CognitionResult(
            intention=Intention(
                action_type="rest",
                motivation_summary="Questa azione non deve raggiungere il mondo.",
            ),
            memory_appraisals=(),
            mental_updates=MentalUpdates(
                commitments=(
                    CommitmentRevision(
                        operation="add",
                        commitment_key="persona_inventata",
                        description="Incontrare qualcuno che non conosco.",
                        due_tick=context.world_tick + 2,
                        involved_agent_ids=("nwl-inesistente",),
                        source_event_ids=(source_event_id,),
                    ),
                )
            ),
            attention_schedule=AttentionSchedule(
                next_activation_in_ticks=4,
                reason="Controllare un impegno invalido.",
            ),
            provider="test-double",
            model="invalid-commitment-fixture",
            inference_id=str(uuid4()),
            attempts=1,
        )
