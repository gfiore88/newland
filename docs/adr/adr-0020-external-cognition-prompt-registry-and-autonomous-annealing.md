---
id: adr-0020
title: "External Cognition Prompt Registry and Bounded Autonomous Annealing"
status: "Accepted"
date: "2026-08-13"
authors: ["Agent AI", "Giovanni Fiore"]
tags: ["cognition", "prompts", "self-annealing", "registry", "evaluation", "rollback", "governance"]
---

# ADR-0020: External Cognition Prompt Registry and Bounded Autonomous Annealing

## Context & Problem Statement

Il prompt cognitivo canonico di Newland e parte delle istruzioni di repair sono
stringhe incorporate nei moduli Python. Il processo importa queste funzioni e
continua a usare la versione caricata fino al riavvio. Correggere una debolezza
richiede quindi una modifica al codice, una nuova esecuzione dei test e il
riavvio del runtime; non esistono promozione atomica, canary del prompt o
rollback indipendenti dal rilascio applicativo.

Il canary live di `qwen-flash-character` ha reso misurabile il costo di questo
limite: quattro attivazioni differite hanno generato otto richieste remote prima
che correzioni manuali di prompt e parser permettessero una risposta valida al
primo tentativo. Il ledger cloud ha contabilizzato 57.579 token in nove
richieste. Il repair corrente può recuperare una singola attivazione, ma non
trasforma automaticamente un errore riutilizzabile in una lezione persistente.

Newland richiede un self-annealing reale senza permettere al runtime di
riscrivere i principi che proteggono autonomia, privacy e confine percettivo
degli abitanti. Dobbiamo separare il codice eseguibile dal contratto testuale,
registrare evidenze redatte, generare lezioni circoscritte, provarle sulle
normali attivazioni e promuoverle o revocarle senza interrompere una transazione
canonica.

## Stakeholders

- [STK-001] **Newlander**: una lezione tecnica non deve prescrivere azioni, motivazioni, valori o interpretazioni psicologiche.
- [STK-002] **Giovanni Fiore**: deve poter osservare versioni, evidenze, metriche e rollback senza modificare codice Python per ogni correzione.
- [STK-003] **Runtime live**: deve caricare una versione coerente del prompt a confini transazionali e continuare con l'ultima versione valida se registry o annealer falliscono.
- [STK-004] **Provider generativi**: Ollama e DashScope devono ricevere lo stesso contratto versionato e attribuibile.
- [STK-005] **Governance**: principi e schema canonico restano human-gated; soltanto chiarimenti tecnici entro limiti verificabili possono essere promossi autonomamente.

## Decision Drivers

- [DRV-001] **Apprendimento persistente**: un errore classificato non deve essere dimenticato al termine della richiesta o del processo.
- [DRV-002] **Riduzione dei repair remoti**: il tasso di validità al primo tentativo deve guidare l'annealing e il consumo evitato deve essere misurabile.
- [DRV-003] **Nessuna mutazione del codice live**: il ciclo di apprendimento non deve modificare moduli Python, installazioni o processi in esecuzione.
- [DRV-004] **Sovranità agentica**: nessuna lezione può scegliere o favorire un'azione, una relazione, un ricordo o un aggiornamento mentale.
- [DRV-005] **Provenienza verificabile**: ogni inferenza deve registrare versione e hash effettivi di base, overlay e schema.
- [DRV-006] **Promozione reversibile**: una regressione deve produrre rollback atomico senza migrare mondo o menti.
- [DRV-007] **Privacy**: il learning ledger non deve conservare prompt privati, output integrali, segreti o chain-of-thought.
- [DRV-008] **Economia cognitiva**: la generazione delle lezioni deve essere locale e subordinata alle menti; il canary deve riusare attivazioni naturali senza chiamate cloud ombra obbligatorie.
- [DRV-009] **Compatibilità semantica**: parser, validatore e arbitro restano l'autorità sul contratto; il prompt non può allentare un invariante di codice.

## Considered Alternatives

### Alternative 1: Conservare i prompt hard-coded e migliorare soltanto i repair

- **Description**: Aggiungere messaggi di repair più dettagliati mantenendo il prompt nei moduli Python.
- **Rejection Rationale**: [REJ-001] Ogni nuova lezione richiederebbe ancora modifica, test, rilascio e riavvio del codice; il costo del primo fallimento si ripeterebbe fra run.

### Alternative 2: Permettere al runtime di riscrivere liberamente il system prompt

- **Description**: Un modello modifica direttamente il prompt attivo dopo ogni errore e il processo ricarica il file.
- **Rejection Rationale**: [REJ-002] Una modifica non vincolata potrebbe introdurre coaching comportamentale, drift cumulativo, prompt injection persistente o indebolimento degli invarianti senza un rollback affidabile.

### Alternative 3: Usare soltanto un database di errori con correzione umana

- **Description**: Persistiamo i fallimenti, ma ogni nuova versione viene scritta e promossa manualmente.
- **Rejection Rationale**: [REJ-003] Migliora l'audit ma non realizza self-annealing autonomo e continua a dipendere dalla disponibilità umana per errori tecnici ripetitivi.

### Alternative 4: Registry esterno con nucleo governato e overlay autonomo limitato

- **Description**: Esternalizziamo prompt e schema in un registry versionato; un learning ledger redatto alimenta un annealer locale che può modificare soltanto lesson overlay tecnici. Candidati, canary, promozione e rollback seguono gate deterministici.
- **Rejection Rationale**: N/A (Selected Option).

### Alternative 5: Affidare l'intero annealing ad Alibaba

- **Description**: Ogni errore apre una seconda sessione cloud dedicata a riscrivere e valutare il prompt.
- **Rejection Rationale**: [REJ-004] Consumerebbe la stessa quota che intendiamo preservare, invierebbe ulteriore contesto operativo e renderebbe l'apprendimento dipendente dal provider interessato dalla regressione.

## Decision Outcome

Chosen Option: **Alternative 4: Registry esterno con nucleo governato e overlay autonomo limitato**.

### Detailed Decision Points

- [DEC-001] **Registry sotto `docs/`**: la sorgente RAG del contratto cognitivo risiederà in `docs/prompts/agent-cognition/` e conterrà manifest, prompt base, lesson overlay, esempi e JSON Schema versionati.
- [DEC-002] **Nessun prompt cognitivo completo in Python**: i provider riceveranno un `PromptArtifact` caricato dal registry; il codice conterrà soltanto loader, policy, parser e validatori.
- [DEC-003] **Nucleo human-gated**: prompt base, schema, esempi normativi e policy dell'annealer potranno cambiare soltanto tramite modifica approvata. Il runtime non potrà sovrascriverli.
- [DEC-004] **Overlay annealabile**: l'annealer potrà aggiungere, sostituire o ritirare esclusivamente lezioni tecniche su forma, provenienza, riferimenti e affordance. Una lezione non potrà nominare un'azione preferita, suggerire motivazioni o modificare la visione del mondo.
- [DEC-005] **Manifest atomico**: `manifest.json` identificherà versione attiva, candidate e precedente, hash SHA-256 degli artefatti, stato del rollout e soglie. La promozione userà sostituzione atomica e file immutabili per versione.
- [DEC-006] **Reload transazionale**: il runtime controllerà il manifest prima di iniziare un'attivazione e manterrà lo stesso `PromptArtifact` per tutti i tentativi di quella inferenza. Nessuna promozione potrà cambiare il prompt a metà transazione.
- [DEC-007] **Provenienza reale**: `CognitionResult` riceverà `prompt_version`, `prompt_hash` e `schema_hash` dal `PromptArtifact`; verrà eliminato il valore predefinito statico che può mentire sulla versione effettiva.
- [DEC-008] **Learning ledger separato**: `data/newland.prompt-runtime.db` conserverà fingerprint, codice violazione, provider, modello, hash del prompt, numero tentativo, esito e contatori. Resterà separato da eventi canonici, menti, Chronicle e cloud budget ledger.
- [DEC-009] **Redazione e minimizzazione**: il ledger non conserverà system prompt completo, contesto privato, output integrale, authorization header o reasoning. Potrà conservare soltanto percorso del campo, codice stabile, tipo osservato, categorie di affordance e dettaglio redatto con lunghezza limitata.
- [DEC-010] **Violazioni strutturate**: parser e validatore esporranno codici stabili invece di usare la sola stringa dell'eccezione. Il fingerprint ignorerà ID, nomi e valori privati affinché errori equivalenti vengano aggregati.
- [DEC-011] **Trigger autonomo limitato**: un errore nuovo sarà registrato immediatamente; l'annealer creerà un candidato dopo una soglia configurata di evidenze equivalenti o quando una violazione deterministica indica una contraddizione del contratto. Nessun trigger lancerà automaticamente una richiesta Alibaba aggiuntiva.
- [DEC-012] **Annealer locale e subordinato**: la proposta di lezione userà un modello Ollama esplicitamente configurato attraverso l'ammissione a priorità inferiore rispetto alle menti. Se Ollama non è disponibile, l'evidenza resta pendente senza bloccare la live.
- [DEC-013] **Formato candidato vincolato**: l'annealer restituirà un oggetto con `lesson_id`, codici coperti, testo conciso, motivazione tecnica e rischi. Non potrà modificare direttamente manifest o artefatti attivi.
- [DEC-014] **Gate deterministici**: prima del canary, il candidato dovrà passare schema, limite dimensionale, deduplicazione, termini vietati, assenza di riferimenti privati, compatibilità con gli invarianti e suite di fixture storiche.
- [DEC-015] **Canary sulle chiamate naturali**: un candidato ammesso verrà applicato a un numero limitato di normali attivazioni. Non verranno create chiamate cloud ombra obbligatorie; provider e agente continueranno a essere scelti dalla configurazione live.
- [DEC-016] **Metriche di promozione**: il gate confronterà validità al primo tentativo, repair per attivazione, `CognitionDeferred`, token per risposta valida e nuove categorie di violazione contro la versione precedente, separando provider e modello.
- [DEC-017] **Promozione e rollback autonomi**: una lezione che raggiunge le soglie minime senza regressioni diventerà attiva; un aumento dei fallimenti o una violazione di policy ripristinerà atomicamente la versione precedente e marcherà il candidato come respinto.
- [DEC-018] **Fallback fail-closed del registry**: manifest invalido, hash errato o artefatto mancante non attiveranno un candidato. Il processo continuerà con l'ultimo `PromptArtifact` verificato in memoria e segnalerà health degradato.
- [DEC-019] **Nessuna autorità materiale**: registry, ledger e annealer non potranno scrivere eventi canonici, modificare menti o chiamare l'arbitro. Influenzano soltanto il contratto testuale inviato al provider.
- [DEC-020] **Repair ancora limitato**: l'annealing ridurrà i repair ma non li sostituirà; un output stocastico invalido continuerà a ricevere il repair massimo autorizzato da ADR-0019 e poi failover o `CognitionDeferred`.
- [DEC-021] **Health non diegetico**: `/api/health` esporrà versione attiva, stato candidate/canary, fingerprint aggregati, tassi di primo tentativo e rollback senza contenuti privati.
- [DEC-022] **Comandi operativi**: la CLI offrirà ispezione del registry, audit del learning ledger, esecuzione singola dell'annealer e rollback manuale; il supervisore potrà eseguire l'annealer autonomamente soltanto con opt-in esplicito.
- [DEC-023] **Bootstrap iniziale**: il prompt corrente `agent-cognition-v4` e lo schema canonico saranno migrati senza cambiamenti semantici a una prima versione esterna; prima si proverà parità, poi si abiliterà l'annealing.
- [DEC-024] **Corpus dalle evidenze esistenti**: i quattro fallimenti del canary Alibaba diventeranno fixture iniziali con dati sintetici o redatti e codici di violazione stabili.

## Operational Configuration

- [CFG-001] **Registry predefinito**: `--prompt-registry docs/prompts/agent-cognition`.
- [CFG-002] **Learning ledger predefinito**: `--prompt-ledger data/newland.prompt-runtime.db`.
- [CFG-003] **Opt-in annealer live**: `--allow-prompt-annealing` con modello locale qualificato.
- [CFG-004] **Modalità conservativa**: senza opt-in il runtime usa comunque il registry e registra evidenze, ma non genera né promuove candidati.
- [CFG-005] **Rollback**: `newland prompts rollback` ripristina la versione precedente verificata senza riavviare il mondo e diventa effettivo dalla prossima attivazione.

## Consequences

### Positive Consequences

- [POS-001] Gli errori pagati diventano evidenze persistenti, deduplicate e verificabili invece di sparire con il processo.
- [POS-002] Prompt e lesson overlay possono evolvere e fare rollback senza modificare o ricaricare codice Python.
- [POS-003] Versione e hash effettivi rendono confrontabili provider, modelli e tassi di repair.
- [POS-004] Canary naturali e annealer locale riducono richieste cloud dedicate all'ottimizzazione.
- [POS-005] Il nucleo governato e i gate sull'overlay preservano autonomia agentica e invarianti materiali.
- [POS-006] Lo stesso registry elimina divergenze silenziose fra percorso Ollama, DashScope live e benchmark.

### Negative Consequences & Risks

- [NEG-001] **Prompt injection persistente**: un errore derivato da contenuto osservato potrebbe contaminare una lezione. - **Mitigation**: nessun contenuto privato nel ledger, codici strutturati, candidate schema, termini vietati e impossibilità per l'annealer di modificare base o schema.
- [NEG-002] **Overfitting a pochi fallimenti**: una lezione può migliorare un caso e peggiorarne altri. - **Mitigation**: deduplicazione, fixture storiche, canary limitato, metriche per modello e rollback automatico.
- [NEG-003] **Crescita del prompt**: lezioni accumulate aumentano input token e possono confondere il modello. - **Mitigation**: budget dimensionale, sostituzione di lezioni equivalenti, scadenza e compattazione locale con nuova valutazione.
- [NEG-004] **Annealer locale imperfetto**: Ollama può proporre testo ambiguo o comportamentale. - **Mitigation**: output strutturato, gate deterministici, allowlist delle categorie e candidato mai applicato direttamente dal modello.
- [NEG-005] **Metriche rumorose**: poche attivazioni non dimostrano causalità. - **Mitigation**: stato canary esplicito, soglie minime, segmentazione provider/modello e promozione reversibile.
- [NEG-006] **Complessità operativa**: registry, ledger e rollout aggiungono stato non canonico. - **Mitigation**: un solo manifest atomico, database separato, health, CLI di audit e recovery fail-closed.
- [NEG-007] **Carico Ollama aggiuntivo**: l'annealing può competere col Cronista o con il fallback locale. - **Mitigation**: priorità inferiore alle menti, trigger aggregato e nessun blocco della live se il job viene differito.
- [NEG-008] **Schema esterno in drift dal parser**: un file JSON potrebbe divergere dai tipi Python. - **Mitigation**: test di equivalenza obbligatori, hash registrato e nessuna modifica autonoma dello schema.

## Acceptance Criteria

- [ACC-001] Nessun provider cognitivo costruisce il system prompt canonico da una stringa completa hard-coded in Python.
- [ACC-002] Un registry iniziale esterno riproduce semanticamente `agent-cognition-v4` e viene usato da Ollama, DashScope live e harness cloud.
- [ACC-003] Il loader rifiuta hash o manifest invalidi e conserva l'ultimo artefatto verificato durante la live.
- [ACC-004] Ogni `CognitionResult` ed `ActionProposed` registra versione e hash effettivi di prompt e schema.
- [ACC-005] Due errori equivalenti con ID e nomi differenti producono lo stesso fingerprint; nessun dato privato o segreto compare nel learning ledger.
- [ACC-006] Un errore non valido produce evidenza persistente anche dopo riavvio e il repair resta limitato come in ADR-0019.
- [ACC-007] Un annealer simulato genera un candidato senza poter modificare base, schema, eventi o menti.
- [ACC-008] Candidate con coaching comportamentale, riferimenti privati, duplicati o dimensione eccessiva vengono respinti prima del canary.
- [ACC-009] Una fixture dimostra promozione atomica dopo metriche migliori e un'altra dimostra rollback automatico dopo regressione.
- [ACC-010] Un'attivazione iniziata con una versione usa la stessa versione anche se il manifest cambia durante il repair.
- [ACC-011] L'assenza di Ollama o il fallimento dell'annealer non arrestano le menti e lasciano l'evidenza pendente.
- [ACC-012] `/api/health` e CLI espongono stato, metriche e rollback senza prompt privati, output o reasoning.
- [ACC-013] La suite di regressione include i quattro difetti osservati nel canary Alibaba e misura validità al primo tentativo.
- [ACC-014] Un test di parità prova che la migrazione iniziale non cambia il prompt composto né lo schema inviati ai provider, salvo metadati di versione.
- [ACC-015] La suite completa resta verde e un canary locale finito prova hot reload al confine fra attivazioni.
- [ACC-016] Qualsiasi canary Alibaba successivo richiede ancora opt-in cloud e cap cumulativo; l'annealing non amplia l'autorità di spesa.

## Compliance & RAG Impact

- [CMP-001] **ADR-0001 preservato**: modifiche a `AGENTS.md`, skill, prompt base, schema e policy restano human-gated; l'autonomia riguarda soltanto overlay tecnici entro policy già approvata.
- [CMP-002] **ADR-0004 distinto**: l'evoluzione psicologica dei personaggi resta separata dall'annealing del contratto di inferenza.
- [CMP-003] **ADR-0007 e ADR-0008 preservati**: parser, validatore e arbitro restano autorità; nessuna lezione introduce decisioni statiche.
- [CMP-004] **ADR-0018 esteso**: benchmark e valutazioni useranno versione e hash del registry invece di una label statica.
- [CMP-005] **ADR-0019 esteso**: il repair cloud resta limitato e contabilizzato; il nuovo learning ledger non sostituisce il budget ledger.
- [CMP-006] **Prospective files after approval**: `docs/prompts/agent-cognition/`, `engine/newland_engine/cognition/prompt_registry.py`, `engine/newland_engine/cognition/prompt_learning.py`, provider cognitivi, CLI, supervisor, health, test e documentazione operativa.
- [CMP-007] **Approval**: Giovanni Fiore ha approvato esplicitamente ADR-0020 il 2026-08-13 e ha autorizzato l'implementazione entro i gate definiti dalla decisione.
