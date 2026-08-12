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
    RoleInterpretationRevision,
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
        language = context.material_state.native_language
        if incoming:
            intention = Intention(
                action_type="speak",
                target_id=incoming[-1].actor_ids[0],
                spoken_content=self._line(language, reply=True),
                language=language,
                motivation_summary="Verificare il ciclo di reazione.",
                confidence=0.9,
            )
        else:
            target_id = context.nearby_agents[0][0]
            intention = Intention(
                action_type="speak",
                target_id=target_id,
                spoken_content=self._line(language, reply=False),
                language=language,
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

    @staticmethod
    def _line(language: str, *, reply: bool) -> str:
        lines = {
            "ar": (
                "إجابة مولدة من نموذج الاختبار."
                if reply
                else "تحية مولدة من نموذج الاختبار."
            ),
            "es": (
                "Respuesta generada por el doble de prueba."
                if reply
                else "Saludo generado por el doble de prueba."
            ),
            "it": (
                "Risposta generata dal test double."
                if reply
                else "Saluto generato dal test double."
            ),
        }
        return lines.get(language, lines["it"])


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


class GeneratedRoleInterpretationTestCognition:
    def decide(self, context: CognitionContext) -> CognitionResult:
        source_event_id = context.observations[-1].event.event_id
        other_id = context.nearby_agents[0][0]
        return CognitionResult(
            intention=Intention(
                action_type="rest",
                duration_minutes=5,
                motivation_summary="Lasciare sedimentare una lettura sociale personale.",
                confidence=0.78,
            ),
            memory_appraisals=(),
            mental_updates=MentalUpdates(
                role_interpretations=(
                    RoleInterpretationRevision(
                        operation="upsert",
                        interpretation_key="amina_presenza_di_soglia",
                        subject_agent_id=other_id,
                        role_label="custode delle soglie incerte",
                        interpretation=(
                            "La sua prudenza mi appare capace di proteggere i passaggi "
                            "che nessuno comprende ancora."
                        ),
                        confidence=0.73,
                        source_event_ids=(source_event_id,),
                    ),
                    RoleInterpretationRevision(
                        operation="upsert",
                        interpretation_key="elia_ascoltatore_del_luogo",
                        subject_agent_id=context.mind.agent_id,
                        role_label="ascoltatore del luogo vuoto",
                        interpretation=(
                            "Mi riconosco, per ora, nella disposizione ad ascoltare "
                            "prima di decidere cosa costruire."
                        ),
                        confidence=0.69,
                        source_event_ids=(source_event_id,),
                    ),
                )
            ),
            attention_schedule=AttentionSchedule(
                next_activation_in_ticks=10,
                reason="Verificare se queste interpretazioni resistono all'esperienza.",
            ),
            provider="test-double",
            model="generated-role-interpretation-fixture",
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


class SituatedActivityTestCognition:
    def __init__(self) -> None:
        self.contexts: list[CognitionContext] = []

    def decide(self, context: CognitionContext) -> CognitionResult:
        self.contexts.append(context)
        activity = context.available_activities[0]
        return CognitionResult(
            intention=Intention(
                action_type="perform_activity",
                activity_id=activity.activity_id,
                duration_minutes=10,
                motivation_summary="Esplorare un'affordance locale percepita.",
                confidence=0.8,
            ),
            memory_appraisals=(),
            mental_updates=MentalUpdates(),
            attention_schedule=AttentionSchedule(
                next_activation_in_ticks=5,
                reason="Valutare ciò che l'attività mi avrà mostrato.",
            ),
            provider="test-double",
            model="situated-activity-fixture",
            inference_id=str(uuid4()),
            attempts=1,
        )


class CooperativeCycleTestCognition:
    """Test-only LLM stand-in proving that social transitions follow generated acts."""

    def decide(self, context: CognitionContext) -> CognitionResult:
        proposal = next(iter(context.social_proposals), None)
        language = context.material_state.native_language
        if proposal is None:
            intention = Intention(
                action_type="propose_cooperation",
                target_id=context.nearby_agents[0][0],
                activity_id=context.available_activities[0].activity_id,
                spoken_content="Vorrei lavorare insieme su questo luogo.",
                language=language,
                motivation_summary="Proporre liberamente un'attività condivisa.",
                confidence=0.86,
            )
        elif proposal.status == "pending":
            intention = Intention(
                action_type="respond_cooperation",
                proposal_id=proposal.proposal_id,
                response="accept",
                spoken_content="أقبل أن نعمل معًا.",
                language=language,
                motivation_summary="Accettare liberamente la proposta percepita.",
                confidence=0.84,
            )
        else:
            intention = Intention(
                action_type="perform_cooperation",
                proposal_id=proposal.proposal_id,
                duration_minutes=10,
                motivation_summary="Dare seguito all'accordo condiviso.",
                confidence=0.88,
            )
        return CognitionResult(
            intention=intention,
            memory_appraisals=(),
            mental_updates=MentalUpdates(),
            attention_schedule=AttentionSchedule(
                next_activation_in_ticks=12,
                reason="Riconsiderare autonomamente l'esperienza condivisa.",
            ),
            provider="test-double",
            model="cooperative-cycle-fixture",
            inference_id=str(uuid4()),
            attempts=1,
        )
