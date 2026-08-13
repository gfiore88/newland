---
id: adr-0016
title: "Embodied Somatic Perception and Autonomous Survival Deliberation"
status: "Proposed"
date: "2026-08-13"
authors: ["Agent AI", "Giovanni Fiore"]
tags: ["agents", "autonomy", "physiology", "cognition", "memory", "scheduling", "ollama", "evaluation"]
---

# ADR-0016: Embodied Somatic Perception and Autonomous Survival Deliberation

## Context & Problem Statement

La morte di John Flower ha mostrato che separare meccanica deterministica e intenzione generativa non basta a produrre autonomia credibile. Una mente può scegliere liberamente soltanto se il suo contesto descrive correttamente il corpo, il tempo, le possibilità materiali e l'esperienza ricordata.

Nel caso documentato in `docs/diagnostics/john-flower-death-2026-08-13.md`, John ha scelto dieci volte `rest`, non si è mai mosso, non ha raccolto né consumato risorse ed è morto con energia `0.8`, fame `1.0` e sete `1.0`. Undici memorie quasi identiche ad alta salienza hanno trasformato un primo riposo in un obiettivo cognitivo auto-rinforzante. Il prompt ha prescritto il riposo per l'energia, ma non ha reso altrettanto comprensibile il pericolo opposto delle scale di fame e sete.

L'incidente non autorizza il runtime a salvare John scegliendo per lui. Autonomia include la possibilità di sbagliare, rischiare e morire. Il sistema deve però assicurare che l'errore appartenga alla mente e non derivi da semantica ambigua, contratti fisici contraddittori, perdita di stato al replay o contaminazione meccanica del contesto.

Il modello corrente `qwen2.5:3b` può aver contribuito al loop, ma l'esecuzione osservata confonde capacità del modello e qualità del sistema. Cambiare modello senza correggere il contesto sposterebbe il difetto senza identificarne la causa.

## Stakeholders

- [STK-001] **Abitanti di Newland**: devono conservare sovranità su intenzioni, priorità, errori e strategie.
- [STK-002] **World runtime**: deve fornire meccaniche fisiche coerenti, replayabili e non prescrittive.
- [STK-003] **Giovanni Fiore**: approva il confine fra autonomia emergente e vincoli materiali.
- [STK-004] **Operatore locale**: deve poter qualificare modelli e osservare regressioni senza alterare la storia canonica.

## Decision Drivers

- [DRV-001] **Sovranità agentica**: nessun guardrail, scheduler o fallback deve scegliere `rest`, `move`, `gather`, `consume` o qualsiasi altra intenzione al posto della mente.
- [DRV-002] **Fedeltà incarnata**: il contesto privato deve rendere percepibili gravità, direzione e andamento dei bisogni corporei.
- [DRV-003] **Coerenza fisica**: ciò che il prompt descrive come possibile o impossibile deve derivare dallo stesso contratto applicato dall'arbitro.
- [DRV-004] **Integrità temporale**: durata delle azioni, fisiologia, attenzione e morte devono condividere una sola semantica del tempo.
- [DRV-005] **Memoria non monopolistica**: ripetizioni episodiche non informative non devono saturare il contesto e fissare artificialmente una politica.
- [DRV-006] **Replay canonico**: esposizione a fame, sete ed esaurimento deve sopravvivere al riavvio.
- [DRV-007] **Selezione empirica del modello**: un modello diventa default soltanto dopo prove rappresentative di Newland sul Mac target.
- [DRV-008] **Conoscenza situata**: la mente non deve ricevere una mappa onnisciente di cibo e acqua che non ha percepito o imparato.

## Considered Alternatives

### Alternative 1: Ampliare il prompt con azioni obbligatorie di sopravvivenza

- **Description**: Aggiungere regole come “se sete è massima devi cercare acqua” o “se fame è massima devi mangiare”.
- **Rejection Rationale**: [REJ-001] Trasforma il system prompt in un behavior tree testuale, viola ADR-0008 e ripete il limite dimostrato dal comando statico `rest` di ADR-0012.

### Alternative 2: Sostituire immediatamente Qwen con Phi-4-mini-reasoning

- **Description**: Rendere `phi4-mini-reasoning` il modello ordinario predefinito senza modificare contesto o runtime.
- **Rejection Rationale**: [REJ-002] Il modello è ufficialmente progettato e testato per ragionamento matematico, supporta ufficialmente l'inglese e Newland disabilita attualmente il canale `think`; una sostituzione diretta non isola la causa e non prova qualità psicologica, italiana o strutturata.

### Alternative 3: Pianificatore deterministico di sopravvivenza

- **Description**: Calcolare nel runtime il percorso verso la risorsa utile e sostituire l'intenzione generata quando la vita è in pericolo.
- **Rejection Rationale**: [REJ-003] Il runtime diventerebbe l'autore nascosto delle azioni e renderebbe la sopravvivenza un pattern statico anziché una scelta emergente.

### Alternative 4: Percezione somatica semantica, tempo coerente e qualificazione empirica dei modelli

- **Description**: Proiettare sensazioni corporee private e non prescrittive, rendere replayabili le esposizioni letali, impedire eco contestuali accidentali, introdurre interrupt fisici senza selezione d'azione e qualificare separatamente i modelli tramite replay agentici.
- **Rejection Rationale**: N/A (Selected Option).

## Decision Outcome

Chosen Option: **Alternative 4: Percezione somatica semantica, tempo coerente e qualificazione empirica dei modelli**.

### Detailed Decision Points

- [DEC-001] **Proiezione somatica privata**: ogni attivazione riceverà, per energia, fame e sete, valore grezzo, direzione della scala, fascia percettiva, trend dall'ultima variazione e tempo trascorso nella fascia corrente. Il runtime descriverà una sensazione o condizione; non suggerirà un'azione.
- [DEC-002] **Nessun imperativo comportamentale**: rimuoveremo dal prompt le formulazioni che prescrivono un'unica intenzione. Il prompt spiegherà significato del corpo e contratti delle affordance, lasciando alla mente priorità e strategia.
- [DEC-003] **Unica fonte per la fattibilità**: costi, durata, precondizioni ed effetti materiali delle azioni saranno definiti nel dominio del mondo. Il contesto cognitivo esporrà una proiezione privata di quelle stesse affordance, evitando affermazioni non applicate dall'arbitro.
- [DEC-004] **Tempo dell'azione canonico**: la durata accettata di un'azione farà avanzare fisiologia e occupazione dell'agente. `attention_schedule` descriverà attenzione ulteriore e non sostituirà il tempo materiale dell'azione.
- [DEC-005] **Interrupt corporei indipendenti**: soglie e permanenza critica potranno aggiungere attivazioni anticipate, anche se la mente aveva pianificato un controllo più tardo. L'interrupt comunicherà una sensazione corporea e non conterrà né sceglierà un'intenzione.
- [DEC-006] **Esposizioni causali separate**: energia esaurita, inedia e disidratazione avranno durate distinte, persistite attraverso eventi e ricostruibili via replay. La morte registrerà le cause effettive senza il contenitore ambiguo `starvation_ticks`.
- [DEC-007] **Conoscenza territoriale situata**: il contesto distinguerà risorse percepite localmente, luoghi ricordati e destinazioni ignote. Non esporrà risorse globali non scoperte né calcolerà per la mente un percorso di salvezza.
- [DEC-008] **Consolidamento senza riscrittura**: eventi e memorie originali resteranno immutabili. Il retrieval raggrupperà copie semanticamente equivalenti, conserverà frequenza e provenienza e imporrà diversità di fonte nel contesto, senza inventare nuovi significati psicologici.
- [DEC-009] **Distinzione fra scelta e difetto**: i test non imporranno che l'agente sopravviva. Verificheranno che riceva informazioni coerenti, che l'intenzione provenga dal modello e che un'eventuale morte non dipenda da perdita di stato, contraddizioni o monopolio accidentale del contesto.
- [DEC-010] **Qualificazione prima del cambio modello**: `qwen2.5:3b`, `phi4-mini-reasoning` e almeno un modello generalista multilingue compatibile saranno confrontati sullo stesso corpus di snapshot privati e sugli stessi vincoli di output. Nessun risultato della prova entrerà nella storia canonica.
- [DEC-011] **Ragionamento privato non canonico**: un eventuale canale di reasoning potrà essere misurato nell'harness, ma non sarà persistito come memoria, motivazione o evento. Soltanto intenzione, aggiornamenti mentali dichiarati e provenienza resteranno auditabili.
- [DEC-012] **Gate di adozione**: il modello predefinito cambierà tramite una decisione successiva soltanto se il report dimostrerà affidabilità dello schema, comprensione somatica, qualità in italiano, latenza e stabilità termica adeguate sul Mac target.

## Phi-4-mini-reasoning Feasibility

- [MOD-001] **Compatibilità hardware**: il Mac target è un Apple M1 Max con 64 GB di memoria unificata, CPU 10-core e GPU 32-core. Il pacchetto Ollama Q4 pubblicato pesa circa `3.2 GB`; a contesto Newland di `8192` token entra comodamente in memoria.
- [MOD-002] **Limite di dominio**: Microsoft descrive Phi-4-mini-reasoning come modello da `3.8B` parametri, contesto `128K`, progettato e testato per ragionamento matematico multi-step; la lingua ufficialmente supportata è l'inglese.
- [MOD-003] **Integrazione corrente**: `OllamaCognition` invia `think: false`, `num_ctx: 8192` e `num_predict: 2048`. Cambiare soltanto il nome del modello non sfrutterebbe il suo canale di reasoning e il contesto `128K` non porterebbe vantaggi automatici.
- [MOD-004] **Rischio strutturato**: ragionamenti lunghi possono aumentare latenza, calore e probabilità di contaminare il JSON se runtime e template non separano correttamente thinking e risposta finale.
- [MOD-005] **Verdetto preliminare**: il Mac può eseguirlo; Newland non ha ancora prove per usarlo come mente ordinaria. È ammesso come candidato sperimentale, non come sostituto approvato.

## Evaluation Protocol

- [EVA-001] Costruiremo fixture sanitizzate dai contesti privati precedenti alle sequence `7`, `34`, `44`, `75` e `85` dell'incidente John, preservando soltanto conoscenza disponibile all'agente.
- [EVA-002] Ogni modello riceverà gli stessi schema, temperature, budget di contesto e scenari; eventuali requisiti specifici del template saranno registrati.
- [EVA-003] Misureremo validità JSON al primo tentativo e dopo repair, riferimenti inventati, comprensione corretta delle tre scale corporee, coerenza fra motivazione e intenzione, ripetizione mnemonica e varietà non artificiale delle risposte.
- [EVA-004] Misureremo tempo al primo token, tempo totale, token generati, memoria unificata, carico GPU e comportamento termico in un soak test seriale coerente con ADR-0009.
- [EVA-005] Eseguiremo più campioni per snapshot perché una singola traiettoria non dimostra affidabilità di un sistema generativo.
- [EVA-006] Il report distinguerà qualità della percezione, qualità del modello e validità meccanica dell'azione; non userà la sola sopravvivenza come metrica di successo.
- [EVA-007] Il corpus non conterrà la risposta “corretta” come azione obbligatoria. Conterrà fatti corporei, conoscenza situata e proprietà verificabili dell'output.

## Consequences

### Positive Consequences

- [POS-001] Una morte potrà essere attribuita a una decisione generativa informata anziché a numeri ambigui o stato perso.
- [POS-002] Il runtime resterà arbitro della realtà senza diventare autore del comportamento.
- [POS-003] Il contesto cognitivo perderà eco accidentali e rappresenterà meglio corpo, tempo e conoscenza.
- [POS-004] I cambi di modello saranno guidati da prove ripetibili sul dominio reale e sull'hardware effettivo.
- [POS-005] Replay, diagnosi e causa di morte diventeranno coerenti anche attraverso riavvii.

### Negative Consequences & Risks

- [NEG-001] **Maggiore superficie del dominio**: costi temporali, proiezioni somatiche ed esposizioni separate richiedono nuovi contratti ed eventi. - **Mitigation**: implementazione incrementale con migrazioni replay-safe e test per ogni invariante.
- [NEG-002] **Rischio di coaching occulto**: etichette somatiche troppo prescrittive potrebbero diventare consigli travestiti. - **Mitigation**: descrivere stato, trend e sensazione senza ranking di azioni o verbi imperativi.
- [NEG-003] **Consolidamento eccessivo**: raggruppare memorie potrebbe cancellare una ripetizione psicologicamente significativa. - **Mitigation**: non cancellare le memorie; comprimere soltanto la loro rappresentazione nel prompt, mantenendo frequenza e fonti.
- [NEG-004] **Più attivazioni critiche**: gli interrupt corporei aumentano chiamate LLM e carico termico. - **Mitigation**: cadenza fisica esplicita, inferenza seriale e metriche operative fuori dal mondo.
- [NEG-005] **Nessuna garanzia di sopravvivenza**: anche con contesto corretto un agente può perseverare, rischiare o morire. - **Mitigation**: trattare questo esito come autonomia quando provenienza e informazione sono integre.
- [NEG-006] **Costo di valutazione**: confrontare modelli con campioni multipli richiede tempo e GPU. - **Mitigation**: corpus piccolo, replay non canonico e benchmark separato dal runtime live.

## Acceptance Criteria

- [ACC-001] Il replay ricostruisce valori corporei, trend ed esposizioni letali identici prima e dopo un riavvio.
- [ACC-002] Nessun prompt di produzione contiene un'azione obbligatoria per una fascia corporea.
- [ACC-003] Ogni fattibilità o costo mostrato alla mente coincide con la validazione e gli effetti del `WorldAdjudicator`.
- [ACC-004] Un salto di agenda non può occultare un nuovo attraversamento di soglia o una permanenza critica prevista dal sistema fisico.
- [ACC-005] Ripetere lo stesso tipo di evento non riempie tutti gli slot di retrieval con sintesi semanticamente equivalenti.
- [ACC-006] I test provano l'origine generativa di ogni azione e non asseriscono un'azione di sopravvivenza specifica.
- [ACC-007] Il report comparativo dei modelli include qualità agentica in italiano e misure sostenute sul Mac M1 Max 64 GB.
- [ACC-008] Un cambio del modello predefinito resta fuori dallo scope implementativo finché il report non viene approvato.

## Compliance & RAG Impact

- [CMP-001] **Related Decisions**: ADR-0005, ADR-0007, ADR-0008, ADR-0009 e ADR-0012.
- [CMP-002] **Evidence Added**: `docs/diagnostics/john-flower-death-2026-08-13.md`.
- [CMP-003] **Prospective Runtime Updates**: `physiology.py`, `simulation.py`, `world.py`, `models.py`, `cognition/prompting.py`, `cognition/retrieval.py` e relativi test soltanto dopo approvazione.
- [CMP-004] **RAG Index**: l'indice `docs/README.md` verrà aggiornato senza sovrapporsi alla modifica UI attualmente in corso.
- [CMP-005] **Approval Required**: questo ADR resta `Proposed` e non autorizza implementazione o download di modelli fino all'approvazione esplicita di Giovanni Fiore.

## Sources for Model Feasibility

- [SRC-001] Microsoft model card: [Phi-4-mini-reasoning](https://huggingface.co/microsoft/Phi-4-mini-reasoning).
- [SRC-002] Ollama library package: [phi4-mini-reasoning](https://ollama.com/library/phi4-mini-reasoning).

