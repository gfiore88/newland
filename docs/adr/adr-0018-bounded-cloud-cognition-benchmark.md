---
id: adr-0018
title: "Bounded Cloud Cognition Benchmark with Alibaba Model Studio"
status: "Proposed"
date: "2026-08-13"
authors: ["Agent AI", "Giovanni Fiore"]
tags: ["cognition", "evaluation", "qwen", "dashscope", "cloud", "privacy", "cost-control"]
---

# ADR-0018: Bounded Cloud Cognition Benchmark with Alibaba Model Studio

## Context & Problem Statement

Le prove sull'incidente di John hanno mostrato che validità JSON, comprensione somatica e fattibilità materiale divergono tra modelli locali. Non sappiamo ancora quanto questo limite dipenda dall'architettura cognitiva e quanto dalla capacità del modello. Alibaba Model Studio offre temporaneamente quote gratuite separate per diversi modelli Qwen nel deployment International, rendendo possibile confrontare una baseline locale con modelli cloud altrimenti non eseguibili sul Mac target.

L'integrazione cloud introduce però un nuovo confine di fiducia: un `CognitionContext` contiene stato corporeo, memoria, relazioni e identità private dell'abitante. Introduce inoltre scadenza delle quote, rischio di addebito, variabilità remota e modelli thinking-only che non garantiscono structured output. Il free tier non autorizza quindi l'uso nel mondo live.

Questa decisione riguarda esclusivamente un benchmark offline, finito e non canonico. Non decide il modello di produzione, non implementa ancora il routing multi-modello e non assegna il Cronista a un provider cloud.

## Stakeholders

- [STK-001] **Abitanti di Newland**: il loro contesto privato deve restare minimo, situato e non deve produrre effetti canonici durante il benchmark.
- [STK-002] **Giovanni Fiore**: deve approvare il trasferimento cloud e poter arrestare la prova senza rischio di spesa automatica.
- [STK-003] **Operatore del benchmark**: necessita di risultati ripetibili, consumi visibili e fallimenti espliciti.
- [STK-004] **Runtime live**: non deve condividere la corsia del benchmark né avanzare mentre il replay sperimentale è in corso.

## Decision Drivers

- [DRV-001] **Misura dell'upper bound**: distinguere i limiti del modello da quelli di prompt, percezione, retrieval e schema.
- [DRV-002] **Comparabilità**: tutti i candidati devono ricevere gli stessi fatti privati e gli stessi vincoli semantici.
- [DRV-003] **Zero effetti canonici**: nessuna risposta sperimentale deve modificare mondo, mente o diario.
- [DRV-004] **Sovranità agentica**: il benchmark valuta decisioni generate; non contiene un'azione corretta da imitare.
- [DRV-005] **Privacy by minimization**: nessun database, profilo completo o contesto estraneo allo scenario deve lasciare il Mac.
- [DRV-006] **Arresto di spesa**: il test deve terminare prima di usare capacità a pagamento anche se la configurazione remota è errata.
- [DRV-007] **Auditabilità senza chain-of-thought**: risultati finali e metriche devono essere verificabili senza conservare ragionamento privato del provider.
- [DRV-008] **Compatibilità col runtime**: l'esperimento deve riusare schema, parser e validatore canonici senza aprire una seconda implementazione cognitiva divergente.

## Considered Alternatives

### Alternative 1: Collegare subito tutti i Newlander al free tier

- **Description**: Usare Alibaba Model Studio come provider live finché resta quota disponibile.
- **Rejection Rationale**: [REJ-001] Mescola esperimento e storia canonica, rende la continuità dipendente da una quota temporanea e invia continuamente contesti privati prima di misurare il beneficio.

### Alternative 2: Restare esclusivamente su modelli locali

- **Description**: Continuare la qualificazione Ollama senza alcun riferimento cloud.
- **Rejection Rationale**: [REJ-002] Non fornisce un upper bound credibile per capire se la cognition corrente è model-limited, benché resti la soluzione prevista per il ciclo continuo.

### Alternative 3: Benchmark cloud offline, sanitizzato e strettamente budgetato

- **Description**: Aggiungere un adapter DashScope utilizzabile soltanto dall'harness offline, confrontare pochi snapshot identici e arrestare localmente la prova prima della quota.
- **Rejection Rationale**: N/A (Selected Option).

### Alternative 4: Spostare immediatamente il Cronista su Alibaba

- **Description**: Usare un modello cloud leggero o gratuito per isolare la prosa dalla GPU locale.
- **Rejection Rationale**: [REJ-003] È una decisione operativa distinta dal benchmark: richiede misure di backlog, costo post-quota, privacy degli eventi e revisione della corsia prevista da ADR-0009.

## Decision Outcome

Chosen Option: **Alternative 3: Benchmark cloud offline, sanitizzato e strettamente budgetato**.

### Detailed Decision Points

- [DEC-001] **Scope offline esclusivo**: introdurremo il provider cloud soltanto nel percorso di valutazione. `newland live`, `run` e `chronicle` non potranno selezionarlo.
- [DEC-002] **Opt-in esplicito**: ogni esecuzione richiederà un flag intenzionale di autorizzazione cloud oltre alla presenza della chiave API. L'assenza di uno dei due impedirà qualsiasi richiesta remota.
- [DEC-003] **Runtime fermo**: l'harness manterrà il controllo già esistente che rifiuta il benchmark quando `agent_loop` o `chronicle` risultano attivi.
- [DEC-004] **Corpus minimo e sanitizzato**: il pilot userà 10–20 snapshot selezionati dal corpus John e da scenari sociali futuri, privati di dati non necessari. Non invierà il database o la scheda agentica completa.
- [DEC-005] **Confronto equo**: ogni configurazione riceverà lo stesso `CognitionContext`, prompt versionato, schema semantico e budget finale. Le differenze obbligatorie di template o reasoning saranno registrate.
- [DEC-006] **Riutilizzo dei contratti**: l'adapter cloud produrrà la stessa struttura attraversando parser e `validate_cognition_result`; non creerà un secondo tipo di risultato.
- [DEC-007] **Structured output non presunto**: poiché il 235B thinking dichiara structured outputs non supportati, il benchmark misurerà JSON al primo tentativo e repair generativo. Non inserirà fallback statici.
- [DEC-008] **Reasoning effimero**: eventuale chain-of-thought non sarà scritta su disco, log, eventi, memoria o report. Saranno conservati soltanto risposta finale, token accounting disponibile, latenza, errori sanitizzati e provenienza.
- [DEC-009] **Segreti fuori dal repository**: la chiave DashScope sarà letta da ambiente o secret store locale, redatta da eccezioni e mai persistita in fixture, configurazioni versionate o telemetry.
- [DEC-010] **Doppio arresto di spesa**: prima del test l'operatore dovrà abilitare `Free Quota Only` nella console; inoltre l'harness imporrà limiti locali di richieste e token stimati e non effettuerà fallback a pagamento.
- [DEC-011] **403 terminale**: `AllocationQuota.FreeTierOnly`, errori di billing o autorizzazione termineranno la configurazione interessata. Non saranno trattati come motivo per inviare la stessa cognizione a un altro provider cloud.
- [DEC-012] **Pilot prima della scala**: partiremo con al massimo 20 snapshot, due campioni e un budget inferiore al 50% della quota visibile per modello. L'estensione a 50–100 snapshot richiederà consumo reale misurato e quota residua verificata.
- [DEC-013] **Candidati iniziali limitati**: confronteremo la baseline locale corrente con `qwen3-32b`, `qwen3-next-80b-a3b-thinking` e `qwen3-235b-a22b-thinking-2507`. Ulteriori modelli verranno aggiunti soltanto se rispondono a una domanda sperimentale distinta.
- [DEC-014] **Nessuna promozione automatica**: risultati migliori non cambieranno provider, modello ordinario, modello riflessivo o routing. Ogni adozione live richiederà un ADR successivo.

## Evaluation Protocol

- [EVA-001] Misureremo validità JSON al primo tentativo e dopo repair, validità completa del contratto e tasso di accettazione simulata dell'arbitro.
- [EVA-002] Misureremo conoscenza impossibile, riferimenti inventati, comprensione somatica, uso causale della memoria e coerenza fra motivazione, aggiornamenti mentali, piano e intenzione.
- [EVA-003] Misureremo diversità intra-modello e omogeneità tra agenti senza premiare verbosità, teatralità o sopravvivenza come risposte corrette.
- [EVA-004] Registreremo token input/output e reasoning quando esposti come soli conteggi, numero di retry, latenza media/p50/p95, errori e costo teorico post-quota.
- [EVA-005] Il report distinguerà capacità del modello, compatibilità del protocollo e costo. Un modello che ragiona bene ma non produce risultati validabili non è automaticamente idoneo al runtime.
- [EVA-006] La valutazione umana userà risposte anonimizzate rispetto al modello quando possibile e criteri dichiarati prima dell'esecuzione.

## Consequences

### Positive Consequences

- [POS-001] Otteniamo un riferimento di qualità difficilmente eseguibile in locale senza compromettere il mondo vivo.
- [POS-002] Il confronto nella stessa famiglia Qwen riduce, pur senza eliminarle, differenze estranee dovute a convenzioni di modello.
- [POS-003] Budget, privacy e assenza di effetti canonici diventano proprietà testabili dell'harness.
- [POS-004] Possiamo decidere con dati se investire nell'architettura, in un modello locale maggiore o in un provider remoto.

### Negative Consequences & Risks

- [NEG-001] **Quota rapidamente consumabile**: reasoning e retry possono bruciare il milione di token prima del corpus completo. - **Mitigation**: pilot piccolo, cap locali e stop sotto il 50% della quota visibile.
- [NEG-002] **Dati fuori dal Mac**: anche un contesto sanitizzato attraversa un provider esterno. - **Mitigation**: minimizzazione, opt-in esplicito, corpus controllato e nessun uso live.
- [NEG-003] **Comparabilità imperfetta**: modelli thinking-only e template remoti non sono identici a Ollama. - **Mitigation**: registrare configurazione, separare protocollo da qualità e non attribuire causalità ai soli parametri.
- [NEG-004] **Offerta temporanea**: disponibilità, prezzi, quote e modelli possono cambiare. - **Mitigation**: verificare console e documentazione alla data di ogni esecuzione e riportarla nei risultati.
- [NEG-005] **Dipendenza aggiuntiva**: un adapter remoto amplia errori HTTP, rate limit e parsing. - **Mitigation**: standard library o dipendenze già presenti, timeout espliciti, errori tipizzati e nessun retry illimitato.
- [NEG-006] **Benchmark come teatro**: risposte più lunghe possono apparire più intelligenti senza migliorare le decisioni. - **Mitigation**: scoring su grounding, coerenza e fattibilità, con verbosità esclusa dai criteri positivi.

## Acceptance Criteria

- [ACC-001] Nessun comando live può istanziare il provider DashScope.
- [ACC-002] Senza flag cloud o segreto il benchmark termina prima di aprire una connessione remota.
- [ACC-003] Test automatici provano redazione del segreto, arresto su 403/quota e rispetto dei cap locali.
- [ACC-004] Le fixture inviate sono sanitizzate, versionate e non includono il database completo.
- [ACC-005] Output cloud e locale attraversano lo stesso parser, validatore e scoring applicabile.
- [ACC-006] Nessuna chain-of-thought compare negli artefatti persistiti.
- [ACC-007] Il report contiene configurazioni, numero di campioni, consumo, latenza, fallimenti e limiti metodologici.
- [ACC-008] Il benchmark non scrive eventi canonici, memorie o proiezioni del Cronista.
- [ACC-009] Nessun modello cloud diventa default senza un nuovo ADR approvato.

## Compliance & RAG Impact

- [CMP-001] **Related Decisions**: ADR-0005, ADR-0008, ADR-0009, ADR-0013 e ADR-0016.
- [CMP-002] **ADR-0005 Refinement**: l'uso cloud viene ammesso soltanto come strumento sperimentale finito; il ciclo continuo resta locale e senza costo API.
- [CMP-003] **ADR-0009 Preservation**: il benchmark resta fuori dal supervisore live e non modifica le priorità `agent`/`chronicle`.
- [CMP-004] **Prospective Files After Approval**: `engine/newland_engine/cognition/`, `engine/newland_engine/evaluation.py`, `scripts/evaluate-cognition-models.py`, CLI e test dedicati.
- [CMP-005] **No Implementation Before Approval**: questo ADR resta `Proposed`; nessuna chiamata Alibaba o modifica runtime è autorizzata finché Giovanni Fiore non lo approva esplicitamente.

## Verified External Sources

- [SRC-001] [Alibaba Model Studio free quota for new users](https://www.alibabacloud.com/help/en/model-studio/new-free-quota), verificata il 2026-08-13.
- [SRC-002] [Alibaba Model Studio model pricing and free quotas](https://www.alibabacloud.com/help/en/model-studio/model-pricing), verificata il 2026-08-13.
- [SRC-003] [Alibaba Model Studio deep-thinking models](https://www.alibabacloud.com/help/en/model-studio/deep-thinking), verificata il 2026-08-13.
- [SRC-004] [qwen3-235b-a22b-thinking-2507 model information](https://www.alibabacloud.com/help/en/model-studio/qwen3-235b-a22b-thinking-2507), verificata il 2026-08-13.
