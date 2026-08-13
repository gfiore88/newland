---
id: adr-0019
title: "Live Cloud Cognition with Persistent Budget and Generative Continuity"
status: "Accepted"
date: "2026-08-13"
authors: ["Agent AI", "Giovanni Fiore"]
tags: ["cognition", "live", "qwen", "dashscope", "budget", "privacy", "autonomy"]
---

# ADR-0019: Live Cloud Cognition with Persistent Budget and Generative Continuity

## Context & Problem Statement

ADR-0018 ha introdotto Alibaba Model Studio esclusivamente come harness offline
e ha vietato la selezione DashScope da `newland live`. Lo smoke test su
`qwen-flash-character` ha ora dimostrato che il provider può produrre un
`CognitionResult` accettato dal parser e dal validatore canonici, usando JSON
mode, schema esplicito e grounding osservabile. Giovanni Fiore ha chiesto di
portare Alibaba nella live affinché le intenzioni dei Newlander possano essere
generate in tempo reale dal provider cloud.

La promozione cambia il confine di fiducia: contesto corporeo, memorie,
relazioni, obiettivi e percezioni private lasciano il Mac a ogni attivazione.
Inoltre una quota gratuita non è un'infrastruttura permanente: retry, riavvii e
modelli grandi possono consumarla rapidamente. La continuità non può essere
ottenuta introducendo azioni statiche, perché ADR-0008 attribuisce ogni scelta
alla mente generativa dell'abitante.

## Stakeholders

- [STK-001] **Newlander**: la loro cognizione deve restare autonoma, situata e separata fra individui anche quando il modello è remoto.
- [STK-002] **Giovanni Fiore**: deve poter scegliere consapevolmente provider, modelli e tetto di consumo senza rischiare addebiti impliciti.
- [STK-003] **Runtime live**: deve tollerare latenza, quota esaurita e indisponibilità cloud senza corrompere transazioni canoniche.
- [STK-004] **Osservatore**: deve mostrare salute e consumo del provider senza ricevere segreti, prompt privati o chain-of-thought.
- [STK-005] **Cronista**: deve restare un workload derivato e non sottrarre priorità alla cognizione degli abitanti.

## Decision Drivers

- [DRV-001] **Sovranità agentica**: Alibaba genera intenzione, aggiornamenti mentali e agenda; il runtime valida ma non decide al posto dell'agente.
- [DRV-002] **Controllo persistente dei consumi**: un riavvio non deve azzerare il limite locale e riaprire accidentalmente la spesa.
- [DRV-003] **Continuità generativa**: un guasto cloud può passare soltanto a un altro modello generativo esplicitamente configurato o produrre `CognitionDeferred`.
- [DRV-004] **Routing proporzionato**: i modelli costosi devono ricevere soltanto attivazioni la cui classe cognitiva ne giustifica l'uso.
- [DRV-005] **Privacy esplicita**: nessuna richiesta remota deve partire senza consenso live, endpoint approvato e credenziale locale.
- [DRV-006] **Audit operativo**: provider, modello, token, latenza, circuit state e fallimenti devono essere osservabili senza contaminare la mente degli agenti.
- [DRV-007] **Compatibilità**: cloud e locale devono attraversare gli stessi prompt, parser, validatori e contratti di arbitraggio.
- [DRV-008] **Adozione reversibile**: l'operatore deve poter tornare a Ollama modificando configurazione, senza migrare lo stato canonico.

## Considered Alternatives

### Alternative 1: Sostituire Ollama globalmente con Alibaba

- **Description**: Ogni comando e ogni workload usa automaticamente un solo modello DashScope.
- **Rejection Rationale**: [REJ-001] Crea dipendenza totale dalla rete e dalla quota, invia contesti privati senza opt-in per processo e impedisce una continuità generativa configurabile.

### Alternative 2: Chiamare Alibaba solo quando Ollama fallisce

- **Description**: Il cloud diventa un fallback implicito e invisibile del provider locale.
- **Rejection Rationale**: [REJ-002] Un guasto locale provocherebbe trasferimento remoto non esplicito di dati privati e consumo non pianificato.

### Alternative 3: Provider qualificati, routing esplicito e budget persistente

- **Description**: `live` accetta modelli qualificati per provider, richiede un opt-in cloud, contabilizza i token in un ledger non canonico e usa soltanto failover generativi dichiarati.
- **Rejection Rationale**: N/A (Selected Option).

### Alternative 4: Usare subito 80B o 235B come mente ordinaria

- **Description**: Ogni attivazione viene inviata ai modelli thinking di capacità massima.
- **Rejection Rationale**: [REJ-003] Consuma quote scarse su decisioni ordinarie, aumenta latenza e non dispone ancora di evidenza live sufficiente sulla validità del contratto.

### Alternative 5: Spostare insieme agenti e Cronista su Alibaba

- **Description**: La stessa modifica introduce sia cognition cloud sia narrazione cloud.
- **Rejection Rationale**: [REJ-004] I due workload hanno schemi, privacy, metriche e politiche di priorità differenti; accoppiarli renderebbe impossibile attribuire consumo e regressioni.

## Decision Outcome

Chosen Option: **Alternative 3: Provider qualificati, routing esplicito e budget persistente**.

### Detailed Decision Points

- [DEC-001] **Promozione limitata alla cognition live**: `newland live` e `newland run` potranno istanziare DashScope per le menti degli abitanti. Il Cronista e la generazione degli arrivi restano locali finché decisioni successive non ne definiscono contratti cloud specifici.
- [DEC-002] **Specifiche qualificate**: i model spec useranno `ollama:<model>` o `dashscope:<model>`. Per compatibilità, un nome privo di prefisso continuerà a indicare Ollama; nessun comando esistente inizierà improvvisamente a inviare dati al cloud.
- [DEC-003] **Opt-in live obbligatorio**: la presenza di almeno un model spec `dashscope:` richiederà `--allow-cloud-live`, `DASHSCOPE_API_KEY`, un endpoint Alibaba HTTPS consentito e un cap token esplicito. Il bootstrap fallirà prima di avviare thread o richieste se manca un gate.
- [DEC-004] **Modelli live iniziali**: `qwen-flash-character` sarà ammesso nel pool ordinario o riflessivo; `qwen-plus-character` e `qwen3-32b` saranno ammessi soltanto nel pool riflessivo. `qwen3-next-80b-a3b-thinking` e `qwen3-235b-a22b-thinking-2507` resteranno esclusi dalla live.
- [DEC-005] **Routing non comportamentale**: il router esistente continuerà a classificare come `reflective` risonanza e dispute attive. Il router sceglie capacità computazionale, non azione, motivazione o psicologia dell'agente.
- [DEC-006] **Failover dichiarato**: l'ordine ripetuto dei model spec definirà il pool generativo. Un pool potrà contenere cloud e locale; il passaggio avverrà soltanto dopo indisponibilità o output invalido e riceverà lo stesso `CognitionContext` privato. Se tutti falliscono, il runtime emetterà `CognitionDeferred` senza azione statica.
- [DEC-007] **Nessun fallback cloud implicito**: un pool composto soltanto da Ollama non chiamerà mai Alibaba. Un pool cloud non aggiungerà automaticamente Ollama o un altro modello non elencato dall'operatore.
- [DEC-008] **Ledger persistente non canonico**: token riservati e consumati saranno registrati atomicamente in un database operativo separato dall'event store e dal Chronicle. Il consumo cumulativo sopravvivrà ai riavvii e sarà indicizzato per provider e modello.
- [DEC-009] **Cap cumulativo esplicito**: `--cloud-token-cap` rappresenterà il massimo cumulativo consentito dal ledger, non una nuova allocazione a ogni avvio. Il valore non potrà superare i cap iniziali di ADR-0018 per il modello selezionato senza una nuova decisione.
- [DEC-010] **Prenotazione conservativa**: prima di ogni chiamata il ledger riserverà input stimato più massimo output; dopo la risposta riconcilierà il totale dichiarato dal provider. Se il provider non espone usage, conserverà l'intera prenotazione come consumo.
- [DEC-011] **Free-tier stop**: `AllocationQuota.FreeTierOnly`, billing, autenticazione e autorizzazione saranno errori terminali per quel provider durante l'attivazione. Non produrranno retry cloud né passaggi verso un altro modello cloud; un eventuale provider locale successivo potrà ancora generare autonomamente.
- [DEC-012] **Repair limitato**: ogni provider cloud avrà al massimo un repair generativo per output non valido. Il repair conterrà l'errore di contratto redatto ma nessuna azione consigliata.
- [DEC-013] **Circuit breaker operativo**: fallimenti di trasporto o server consecutivi apriranno temporaneamente il circuito del provider. Il circuito controlla soltanto ammissione e failover e non inserisce percezioni o motivazioni nella mente.
- [DEC-014] **Richieste stateless**: la live non invierà session ID Character né userà memoria remota implicita. Ogni identità continuerà a derivare esclusivamente dalla mente persistita e dal retrieval locale.
- [DEC-015] **Chain-of-thought effimera**: il runtime scarterà qualsiasi reasoning content. Persistirà soltanto risposta finale validata, provenienza, conteggi token, latenza ed errori redatti.
- [DEC-016] **Endpoint e redirect**: la chiave potrà essere inviata soltanto a un endpoint HTTPS `*.aliyuncs.com/compatible-mode/v1`; i redirect resteranno disabilitati.
- [DEC-017] **Health non diegetico**: `/api/health` esporrà provider configurati, token consumati/cap, richieste, latenza e stato circuito. Non esporrà chiave, header, prompt, risposte private o contenuto di reasoning.
- [DEC-018] **Una corsia di attivazione**: le chiamate cloud degli agenti attraverseranno `AdmittedCognition` e manterranno le transazioni cognitive seriali iniziali. La separazione fisica fra lane cloud e GPU locale richiederà misure successive e non modificherà il comportamento degli agenti.
- [DEC-019] **Canary finito prima della continuità**: l'implementazione sarà verificata con una singola attivazione live reale di `qwen-flash-character`, quindi arrestata fra transazioni integre. Soltanto dopo tale prova l'operatore lancerà il mondo continuo.
- [DEC-020] **Nessuna promozione automatica dei risultati**: il modello cloud genera decisioni canoniche solo quando è stato esplicitamente selezionato per quella esecuzione live; benchmark e scoring non cambiano configurazione da soli.

## Operational Configuration

- [CFG-001] **Ordinary example**: `--model dashscope:qwen-flash-character`.
- [CFG-002] **Generative continuity example**: `--model dashscope:qwen-flash-character --model ollama:qwen2.5:3b`.
- [CFG-003] **Reflective example**: `--reflective-model dashscope:qwen-plus-character --reflective-model ollama:qwen2.5:7b`.
- [CFG-004] **Required gate**: `--allow-cloud-live --cloud-token-cap <cumulative-token-limit>`.
- [CFG-005] **Secrets**: `DASHSCOPE_API_KEY` e `DASHSCOPE_BASE_URL` restano in `.env` ignorato da Git.

## Consequences

### Positive Consequences

- [POS-001] I Newlander possono usare in tempo reale modelli Character o Qwen più capaci mantenendo la stessa sovranità generativa.
- [POS-002] Lo scarico sul cloud riduce la pressione GPU locale della cognition e lascia aperta la possibilità di dedicare Ollama al Cronista.
- [POS-003] Provider e modelli diventano componibili e reversibili senza migrazione del mondo o delle menti.
- [POS-004] Cap persistenti, Free Quota Only e health rendono consumo e arresto verificabili anche attraverso riavvii.
- [POS-005] Il failover resta una seconda mente generativa sullo stesso contesto, mai un comportamento scritto dal runtime.

### Negative Consequences & Risks

- [NEG-001] **Trasferimento continuo di contesto privato**: memorie, bisogni e relazioni attraversano Alibaba. - **Mitigation**: opt-in per esecuzione, contesto agent-scoped, TLS, endpoint allowlist e nessuna session cache.
- [NEG-002] **Quota insufficiente per una live lunga**: il prompt canonico può usare migliaia di token per attivazione. - **Mitigation**: cap cumulativo persistente, usage health, attention scheduling e canary prima del continuo.
- [NEG-003] **Dipendenza dalla rete**: latenza e outage possono deferire cognizioni o spostarle su provider generativi configurati. - **Mitigation**: timeout, circuit breaker, failover esplicito e transazioni atomiche.
- [NEG-004] **Character può privilegiare role-play rispetto al grounding**: lo smoke ha già osservato fonti inventate su un fixture povero. - **Mitigation**: stesso validatore canonico, repair limitato e scoring live degli `ActionRejected`/`CognitionDeferred`.
- [NEG-005] **Ledger operativo aggiuntivo**: prenotazioni interrotte possono sovrastimare consumo. - **Mitigation**: preferire sovrastima sicura, registrare stato e prevedere riconciliazione manuale auditabile senza riduzioni automatiche.
- [NEG-006] **Pool misto meno comparabile**: decisioni consecutive possono provenire da modelli diversi. - **Mitigation**: provenienza su ogni `ActionProposed`, health del routing e ordine configurato esplicito.
- [NEG-007] **Serializzazione conservativa**: una chiamata cloud può ritardare temporaneamente il Cronista locale. - **Mitigation**: misurare p95 e backlog prima di introdurre lane concorrenti.

## Acceptance Criteria

- [ACC-001] `newland live` e `newland run` accettano model spec qualificati e costruiscono provider DashScope soltanto con opt-in esplicito.
- [ACC-002] Flag, chiave, endpoint o cap mancanti fanno fallire il bootstrap prima di thread, eventi o richieste remote.
- [ACC-003] Test automatici provano che configurazioni solo Ollama non importano né chiamano il provider cloud.
- [ACC-004] Test automatici provano cap cumulativo attraverso due riavvii del ledger e prenotazione conservativa in caso di usage assente.
- [ACC-005] Test automatici provano 403 terminale, circuit breaker, redazione del segreto, redirect disabilitati e assenza di chain-of-thought persistita.
- [ACC-006] Test automatici provano che 80B e 235B sono rifiutati nella live e che Plus Character/32B non entrano nel pool ordinario.
- [ACC-007] Output DashScope attraversa parser e validatore canonici; output invalido produce repair generativo, failover dichiarato o `CognitionDeferred`, mai un'intenzione locale statica.
- [ACC-008] Una prova reale finita produce almeno un `ActionProposed` canonico con `provider=dashscope`, modello e inference ID, senza scrivere credenziali o reasoning.
- [ACC-009] `/api/health` espone consumo cumulativo, cap e stato circuito senza contenuto privato.
- [ACC-010] La suite completa resta verde e un riavvio della live conserva mente, mondo e contabilità cloud.
- [ACC-011] Il Cronista continua sulla propria configurazione locale e non usa Alibaba come effetto collaterale dell'abilitazione cognition cloud.
- [ACC-012] La documentazione contiene comando di avvio, arresto, rotazione chiave e lettura del budget residuo.

## Compliance & RAG Impact

- [CMP-001] **ADR-0018 supersession parziale**: dopo approvazione, questo ADR sostituirà soltanto `[DEC-001]`, `[DEC-014]`, `[ACC-001]` e `[ACC-009]` per la cognition degli abitanti; benchmark, cap iniziali e divieti sul reasoning restano validi.
- [CMP-002] **ADR-0008 preservato**: nessun provider, budget gate o circuit breaker sceglierà azioni statiche.
- [CMP-003] **ADR-0009 esteso**: la cognition cloud entra nella corsia agent-first esistente; il Cronista resta derivato e locale.
- [CMP-004] **ADR-0005 raffinato**: Ollama non è più l'unico provider live consentito, ma resta il default retrocompatibile e la continuità locale consigliata.
- [CMP-005] **Prospective files after approval**: `engine/newland_engine/cognition/`, `engine/newland_engine/live.py`, `engine/newland_engine/cli.py`, `engine/newland_engine/inference.py`, `scripts/start-live.sh`, documentazione e test dedicati.
- [CMP-006] **Approval**: Giovanni Fiore ha approvato esplicitamente l'ADR 019 il 2026-08-13 e ha autorizzato implementazione, test e canary live finito entro i gate qui definiti.
