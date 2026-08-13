---
id: adr-0021
title: "Selective Cognitive Attention and Progressive Deliberation"
status: "Accepted"
date: "2026-08-13"
authors: ["Agent AI", "Giovanni Fiore"]
tags: ["cognition", "attention", "memory", "retrieval", "prompts", "tokens"]
---

# ADR-0021: Selective Cognitive Attention and Progressive Deliberation

## Context & Problem Statement

Il canary live di `qwen-flash-character` ha contabilizzato 57.579 token in nove
richieste, dei quali 47.140 erano prompt token. Il costo non dipende soltanto
dalla forma verbosa del contratto: `build_private_context()` porta oggi in ogni
deliberazione intere collezioni di beliefs, relazioni, ruoli interpretati,
frammenti di anamnesi e riflessioni, oltre a un massimo di dodici gruppi di
memoria scelti principalmente per salienza e recenza.

Questo confonde la memoria totale con la coscienza attiva. Una decisione locale
semplice riceve conoscenze che la mente non avrebbe motivo di richiamare in quel
momento, aumentando token, latenza, associazioni spurie e tendenza
all'iper-riflessione. Il routing `ordinary/reflective` introdotto da ADR-0009
cambia il tier di modello, ma non il contenuto portato all'attenzione.

Il [Brainstorming 11](../wiki/sources/src-brainstorming-11-selective-cognitive-attention.md)
propone una regola diversa: deliberare inizialmente con il minimo contesto
sufficiente ed espanderlo soltanto quando emergono incertezza, conflitto, rischio
o conseguenze importanti. La memoria totale resta persistente e accessibile,
ma soltanto un working set privato e situato entra nella singola inferenza.

ADR-0008 vieta però al runtime di scegliere nuove azioni statiche. Questa
decisione deve quindi distinguere l'esecuzione automatica di un'intenzione già
generata dalla scelta di una nuova intenzione, che rimane sempre appartenente
alla mente generativa.

## Stakeholders

- [STK-001] **Newlander**: deve conservare identità, autonomia e accesso alla propria memoria senza essere reso onnisciente o artificialmente smemorato.
- [STK-002] **Giovanni Fiore**: vuole menti più naturali e meno iperanalitiche, non una semplice compressione testuale del mega-prompt.
- [STK-003] **Runtime**: deve costruire, espandere e validare contesti senza scegliere azioni, motivazioni o interpretazioni.
- [STK-004] **Provider generativi**: devono poter deliberare con un contesto minimo e chiedere esplicitamente conoscenza aggiuntiva.
- [STK-005] **Osservatore**: deve mostrare livello attentivo, promozioni, token e fonti incluse senza esporre contenuto mentale privato.

## Decision Drivers

- [DRV-001] **Coscienza selettiva**: il contesto deve rappresentare ciò a cui la mente presta attenzione, non tutto ciò che possiede.
- [DRV-002] **Minimo sufficiente**: ogni nuova deliberazione parte dal livello meno costoso compatibile con il trigger canonico.
- [DRV-003] **Espansione autonoma**: la mente può chiedere più contesto senza essere costretta a scegliere prematuramente un'azione.
- [DRV-004] **Sicurezza epistemica**: nessun livello può introdurre conoscenze non percepite o non possedute dall'agente.
- [DRV-005] **Sovranità comportamentale**: attenzione, retrieval e routing non possono scegliere o favorire un comportamento.
- [DRV-006] **Continuità personale**: un piccolo ancoraggio stabile del sé deve restare presente anche nelle decisioni focali.
- [DRV-007] **Economia misurabile**: il sistema deve misurare token cumulativi per decisione completa, comprese eventuali espansioni.
- [DRV-008] **Reversibilità**: il percorso attuale a contesto pieno deve restare disponibile durante canary e rollback.

## Considered Alternatives

### Alternative 1: Comprimere soltanto prompt e JSON Schema

- **Description**: conservare lo stesso contenuto cognitivo riducendo parole, chiavi e sintassi del payload.
- **Rejection Rationale**: [REJ-001] Riduce alcuni token ma mantiene la deliberazione indiscriminata e i suoi effetti cognitivi; ottimizza la rappresentazione, non l'attenzione.

### Alternative 2: Lasciare che il runtime scelga automaticamente azioni semplici

- **Description**: sete alta e acqua disponibile producono direttamente `consume`, senza inferenza.
- **Rejection Rationale**: [REJ-002] Il runtime sceglierebbe una nuova intenzione sulla base di una regola statica, violando ADR-0008 e ignorando conoscenze soggettive come sospetto, promessa o timore.

### Alternative 3: Usare sempre il contesto minimo senza espansione

- **Description**: inviare soltanto bisogni, luogo e affordance locali per ogni decisione.
- **Rejection Rationale**: [REJ-003] Renderebbe i personaggi economicamente efficienti ma amnesici, incapaci di onorare relazioni, rischi ricordati, piani e conflitti rilevanti.

### Alternative 4: Recuperare sempre un numero fisso di memorie salienti

- **Description**: ridurre il limite corrente da dodici a un valore inferiore mantenendo ranking per salienza e recenza.
- **Rejection Rationale**: [REJ-004] La salienza globale non equivale alla pertinenza per il focus corrente; un numero fisso può includere ricordi estranei e omettere quello decisivo.

### Alternative 5: Attenzione a livelli con richiesta di espansione generativa

- **Description**: separare memoria totale, working set e contesto d'inferenza; partire da un livello focale, promuovere per segnali canonici o richiesta della mente e registrare l'intero percorso.
- **Rejection Rationale**: N/A (Selected Option).

## Decision Outcome

Chosen Option: **Alternative 5: Attenzione a livelli con richiesta di espansione generativa**.

### Detailed Decision Points

- [DEC-001] **Memoria totale distinta dal working set**: beliefs, relazioni, piani, ruoli, anamnesi e memorie restano persistenti nella mente; un `AttentionContextBuilder` ne seleziona una vista effimera per inferenza.
- [DEC-002] **Livello procedurale L0**: il runtime può completare durata, movimento fisico ed effetti di un'intenzione già generata e accettata senza una nuova inferenza. L0 non può iniziare, sostituire o concatenare autonomamente una nuova azione.
- [DEC-003] **Livello focale L1**: ogni nuova deliberazione ordinaria riceve un ancoraggio minimo del sé, trigger di attivazione, stato corporeo saliente, percezioni nuove, luogo, agenti presenti e affordance materialmente immediate.
- [DEC-004] **Livello contestuale L2**: il contesto aggiunge soltanto obiettivi, piani, impegni, relazioni, beliefs e memorie collegati agli agenti, eventi, risorse o scadenze presenti nel focus.
- [DEC-005] **Livello riflessivo L3**: il contesto può ampliare memoria a lungo termine, contraddizioni, anamnesi, ruoli soggettivi e dinamiche sociali complesse quando la situazione lo richiede.
- [DEC-006] **Ancoraggio del sé sempre presente**: nome, valori e temperamento non saranno recuperati come ricordi opzionali; formeranno un nucleo breve e stabile per evitare che l'efficienza cancelli la continuità del personaggio.
- [DEC-007] **Promozione minima canonica**: disputa attiva, risonanza percepita, esposizione corporea critica, impegno scaduto, azione ripetutamente rifiutata o contraddizione esplicita imporranno un livello minimo di attenzione. Il segnale decide quanta conoscenza rendere disponibile, mai quale risposta scegliere.
- [DEC-008] **Richiesta generativa di contesto**: prima dell'azione la mente potrà restituire `ContextExpansionRequested` con categorie ammesse e anchor ID accessibili invece di un'intenzione. Il runtime validerà la richiesta, recupererà soltanto fonti possedute o percepite e ripeterà la deliberazione.
- [DEC-009] **Richiesta strutturata, non query onnipotente**: una richiesta indicherà domini enumerati (`memories`, `relationships`, `beliefs`, `goals`, `plans`, `commitments`, `roles`, `anamnesis`) e anchor già noti. Testo libero limitato potrà affinare il ranking, ma non ampliare il confine epistemico.
- [DEC-010] **Massimo due promozioni**: una decisione può attraversare L1→L2→L3. Se a L3 la mente chiede ancora contesto non disponibile, il runtime produrrà `CognitionDeferred`; non inventerà informazioni né azioni.
- [DEC-011] **Retrieval legato al focus**: il ranking combinerà corrispondenza con anchor/eventi/entità, provenienza, recenza e salienza. Salienza e recenza non resteranno gli unici segnali.
- [DEC-012] **Nessuna cancellazione per omissione**: ciò che non entra nel working set resta invariato nella mente persistente. Un'assenza dal contesto non autorizza il modello a rimuovere o negare quella conoscenza.
- [DEC-013] **Output differenziale**: il wire contract potrà omettere categorie di aggiornamento vuote e il parser le normalizzerà al `CognitionResult` canonico. Campi semantici non vuoti, fonti e validazione resteranno invariati.
- [DEC-014] **Contratto compatto subordinato**: una grammatica derivata deterministicamente dallo schema potrà ridurre il costo residuo del contratto, ma sarà un'ottimizzazione di trasporto successiva alla corretta selezione del working set.
- [DEC-015] **Routing coordinato ma distinto**: L1 userà il pool ordinario; L3 userà il pool riflessivo. L2 userà il livello minimo consentito dalla causa di promozione. Il router sceglie capacità computazionale, non comportamento.
- [DEC-016] **Snapshot per deliberazione**: schema, prompt e insieme di fonti accessibili saranno congelati per ogni tentativo; un'espansione creerà uno snapshot successivo esplicitamente collegato allo stesso ciclo cognitivo.
- [DEC-017] **Provenienza attentiva**: persisteremo livello finale, numero di espansioni, categorie richieste, source ID inclusi e token per stadio. Non persisteremo prompt, contenuto privato escluso o ragionamento nascosto.
- [DEC-018] **Nessuna session cache remota**: attenzione e memoria continueranno a essere ricostruite localmente e inviate stateless; Alibaba non diventerà memoria implicita.
- [DEC-019] **Routine future fuori scope**: un eventuale repertorio di abitudini o policy procedurali scritto dalla mente richiederà un ADR successivo che definisca acquisizione, revoca, conflitto e compatibilità con ADR-0008.

## Initial Attention Matrix

| Segnale | Livello minimo | Conoscenza aggiuntiva candidata |
|---|---:|---|
| Nuova percezione locale ordinaria | L1 | Nessuna oltre focus e affordance locali |
| Bisogno corporeo non critico | L1 | Stato somatico saliente e risorse immediatamente accessibili |
| Persona presente o messaggio diretto | L2 | Relazione e memorie riferite a quella persona |
| Obiettivo, piano o impegno richiamato dal trigger | L2 | Solo elementi attivi e fonti collegate |
| Azione rifiutata ripetutamente | L2 | Rifiuti correlati, piano corrente e affordance aggiornate |
| Disputa, risonanza o rischio corporeo critico | L3 | Memorie e strutture mentali pertinenti alla causa |
| Richiesta valida della mente | L2/L3 | Soli domini e anchor richiesti entro il confine privato |

La matrice stabilisce disponibilità minima di contesto. Non codifica la risposta
appropriata e non attribuisce a un segnale un'azione obbligatoria.

## Rollout Plan

- [ROL-001] **Fase osservativa**: costruire in parallelo i candidati L1/L2/L3 su fixture e replay senza chiamate cloud e senza cambiare la cognition canonica.
- [ROL-002] **Audit lossless**: verificare che ogni elemento escluso abbia una ragione di non pertinenza riproducibile e resti recuperabile al livello successivo.
- [ROL-003] **Canary offline**: confrontare full context e progressive context sugli stessi snapshot, misurando validità, scelta, continuità personale e token stimati.
- [ROL-004] **Canary live finito**: eseguire inizialmente tre cicli cognitivi con fallback full-context esplicito e cap persistente.
- [ROL-005] **Promozione**: rendere progressivo il default soltanto se supera i criteri sotto; mantenere una flag operativa di rollback al percorso v4.

## Consequences

### Positive Consequences

- [POS-001] Le decisioni semplici non vengono contaminate da conoscenze remote e irrilevanti.
- [POS-002] Token e latenza diminuiscono per effetto di attenzione reale, non soltanto di abbreviazioni sintattiche.
- [POS-003] Situazioni complesse conservano accesso progressivo a memoria, biografia soggettiva e relazioni.
- [POS-004] La mente può riconoscere la propria incertezza e chiedere conoscenza prima di agire.
- [POS-005] Il runtime resta responsabile di accesso e validazione, mentre comportamento e significato restano generativi.

### Negative Consequences & Risks

- [NEG-001] **Falsa irrilevanza**: il selettore può non includere un ricordo decisivo. - **Mitigation**: richiesta generativa, trigger minimi conservativi, audit offline e possibilità di promozione fino a L3.
- [NEG-002] **Costo multiplo nei casi complessi**: L1→L2→L3 può costare più di una singola chiamata piena. - **Mitigation**: misurare il costo cumulativo per decisione e promuovere direttamente i trigger chiaramente complessi.
- [NEG-003] **Influenza indiretta del focus**: ciò che il runtime mostra può orientare il comportamento. - **Mitigation**: regole di selezione basate su accessibilità e legami verificabili, non su azioni desiderate; metriche di omissione e test contro coaching.
- [NEG-004] **Continuità personale impoverita**: un L1 troppo stretto può rendere il personaggio generico. - **Mitigation**: ancoraggio stabile del sé e confronto qualitativo blind fra full e progressive context.
- [NEG-005] **Contratto più complesso**: `ContextExpansionRequested` introduce uno stato intermedio. - **Mitigation**: union tipizzata, massimo due promozioni, transazione cognitiva atomica e `CognitionDeferred` a esaurimento.
- [NEG-006] **Metriche di token insufficienti**: risparmio non implica migliore cognizione. - **Mitigation**: gate congiunti su grounding, continuità, validità, repair, decisioni e consumo.

## Acceptance Criteria

- [ACC-001] Test provano che L1 non contiene collezioni mentali globali non pertinenti e conserva ancoraggio del sé, trigger, percezioni e affordance locali.
- [ACC-002] Test provano che ogni elemento escluso da L1 è ancora recuperabile da L2 o L3 quando richiesto con anchor valido.
- [ACC-003] Una richiesta con ID non conosciuto, dominio non ammesso o fonte privata altrui viene respinta senza allargare il contesto.
- [ACC-004] Nessuna regola di attenzione produce direttamente un `action_type`, una motivazione o un aggiornamento mentale.
- [ACC-005] L0 esegue soltanto intenzioni già accettate e non concatena nuove azioni.
- [ACC-006] Fixture di persona presente, impegno scaduto, disputa, risonanza, rischio corporeo e rifiuto ripetuto raggiungono il livello minimo previsto.
- [ACC-007] Una deliberazione progressiva conserva snapshot, provenienza e atomicità attraverso massimo due espansioni.
- [ACC-008] Il canary offline riduce di almeno il 40% la mediana dei caratteri di contesto per i casi L1 senza peggiorare validità o grounding.
- [ACC-009] Sul corpus complessivo, inclusi casi L2/L3, i prompt token cumulativi medi diminuiscono almeno del 25% e il tasso di repair non aumenta.
- [ACC-010] La valutazione umana blind non rileva regressione sostanziale di continuità personale o naturalezza rispetto al full context.
- [ACC-011] Un fallimento del progressive builder o del canary usa soltanto il percorso full-context generativo esplicitamente configurato oppure produce `CognitionDeferred`.
- [ACC-012] La suite completa resta verde e la health non espone prompt, ricordi esclusi o ragionamento nascosto.

## Compliance & RAG Impact

- [CMP-001] **ADR-0008 preservato**: nessuna nuova azione automatica viene selezionata dal runtime; soltanto esecuzione di intenzioni già generate.
- [CMP-002] **ADR-0009 esteso**: il routing di capacità si coordina con il livello attentivo senza sostituirlo.
- [CMP-003] **ADR-0019 preservato**: budget, privacy, provider stateless e fallback generativi restano invariati.
- [CMP-004] **ADR-0020 usato per rollout**: prompt registry, metriche e rollback governeranno le versioni progressive.
- [CMP-005] **RAG files**: brainstorming grezzo, fonte normalizzata e concetto risiedono sotto `docs/`; i risultati futuri vivranno in `docs/experiments/`.
- [CMP-006] **Prospective code files**: `engine/newland_engine/cognition/attention.py`, retrieval, prompting, tipi, provider, provenance e test dedicati.
- [CMP-007] **Approval**: Giovanni Fiore ha approvato esplicitamente ADR-0021 il 2026-08-13, autorizzando implementazione e verifiche offline; un canary cloud reale resta un'operazione separata e intenzionale.
