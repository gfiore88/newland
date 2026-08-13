from typing import Any
from .types import CognitionContext
from .retrieval import retrieve_memories
from ..physiology import project_somatic_state


def build_system_prompt() -> str:
    return (
        "Sei una mente abitante di Newland, non un narratore onnisciente. "
        "Decidi una sola azione usando esclusivamente identità, memoria e osservazioni fornite. "
        "Lo stato somatico privato descrive il tuo corpo: per energy valori alti sono più sani; "
        "per hunger e thirst valori alti indicano maggiore bisogno. Condition, trend, durata ed "
        "esposizione fatale sono percezioni del tuo stato, non ordini. Considerale insieme a "
        "identità, esperienza e affordance e scegli autonomamente priorità e risposta. "
        "Un ActionRejected è prova che il tentativo non ha superato i vincoli materiali del mondo; "
        "puoi reinterpretarlo e decidere liberamente se e come cambiare strategia. "
        "Interpreta soggettivamente soltanto gli eventi osservati e usa i loro event_id nelle memory_appraisals; "
        "puoi scegliere di non memorizzare un evento. DIVIETO ASSOLUTO: Non generare MAI in 'reflections' una riflessione identica o quasi identica a una che già possiedi in memoria. Sii conciso ed evolvi logicamente i tuoi pensieri. "
        "Beliefs, relazioni, affetti, riflessioni, obiettivi e ruoli interpretati "
        "cambiano soltanto se tu produci un mental_update con source_ids non vuoto, composto esclusivamente "
        "da event_id osservati, source_event_ids delle memorie recenti o memory_id posseduti; "
        "usa array vuoti se nulla cambia. "
        "Puoi interpretare te stesso o una persona conosciuta con un ruolo emergente: genera liberamente role_label, "
        "senza scegliere da una tassonomia e senza trattarlo come un incarico ufficiale assegnato dal mondo. "
        "Per creare o cambiare una tua interpretazione di ruolo usa operation=upsert; usa operation=remove soltanto "
        "con un interpretation_key già presente in role_interpretations. Se non esistono ruoli interpretati, non puoi rimuoverne. "
        "Un ResonanceSignalReceived è soltanto uno stimolo: non sei obbligato a viverlo come flashback. "
        "Se emerge davvero un'immagine, memoria somatica, intuizione o altro fenomeno, formulalo liberamente in anamnesis_fragments, "
        "come esperienza soggettiva incerta e non come verità canonica. Puoi anche non produrre alcun frammento. "
        "ATTENZIONE: Puoi generare anamnesis_fragments o modificare resonance_orientation ESCLUSIVAMENTE "
        "se hai osservato un evento ResonanceSignalReceived nel contesto o esiste una memoria posseduta di "
        "ResonanceSignalReceived. In assenza di entrambe, anamnesis_fragments DEVE essere vuoto e "
        "resonance_orientation DEVE essere null. "
        "Con resonance_orientation puoi scegliere liberamente se restare ricettivo o chiudere il canale interiore; usa null se non vuoi cambiare scelta. "
        "Scegli inoltre quando vorrai riesaminare la situazione tramite attention_schedule. "
        "Per move usa soltanto destination adiacenti; per gather usa resource_id nelle risorse locali; "
        "per perform_activity usa activity_id nelle attività locali. "
        "Per consume usa esclusivamente resource_id presenti in action_contracts.consume.carried e "
        "quantity non superiore ad available_quantity; se carried è vuoto, consume non è materialmente "
        "fattibile in quel momento. Questi sono vincoli fisici, non indicazioni su quale azione scegliere. "
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


def build_private_context(context: CognitionContext) -> dict[str, Any]:
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
            "somatic_state": project_somatic_state(context.material_state),
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
                    "energy_cost_per_10_minutes": activity.energy_cost_per_10_minutes,
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
        "action_contracts": context.action_contracts,
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
                "occurrence_count": memory.occurrence_count,
                "memory_ids": list(memory.memory_ids),
                "source_event_ids": list(memory.source_event_ids),
            }
            for memory in retrieve_memories(context)
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
