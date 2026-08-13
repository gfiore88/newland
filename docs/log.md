# REGISTRO ATTIVITÀ WIKI (KARPATHY LLM-WIKI LOG)

Registro cronologico append-only delle attività di Ingest, Query e Lint della wiki.

---

## [2026-08-12] init | Inizializzazione Karpathy LLM-Wiki RAG Architecture (ADR-0002)
- Creata la struttura a 3 livelli: `docs/raw/`, `docs/wiki/`, `docs/wiki-schema.md`.
- Inizializzato il catalogo `docs/index.md` e la direttiva di manutenzione `docs/wiki-schema.md`.

## [2026-08-12] ingest | Specifica Primordiale Universo Parallelo Newland
- Ingerito documento di dominio `docs/domain/newland-universe-spec.md`.

## [2026-08-12] adr | Registrazione ADR-0003 - Architettura dell'Osservatore Integrato
- Registrato ADR-0003 `docs/adr/adr-0003-silent-chronicler-observer-architecture.md`.

## [2026-08-12] adr | Registrazione ADR-0004 - Auto-Annealing Personaggi 100% Autonomo
- Registrato ADR-0004 `docs/adr/adr-0004-autonomous-character-auto-annealing.md`.

## [2026-08-12] adr | Registrazione ADR-0005 - Stack Tecnico & Modelli LLM Locali (Ollama)
- Registrato ADR-0005 `docs/adr/adr-0005-technical-engine-local-llm-architecture.md`.

## [2026-08-12] adr | Registrazione ADR-0006 - Narrative-First 2.5D WebGL Observer Engine Architecture
- Registrato ADR-0006 `docs/adr/adr-0006-observer-engine-2d-webgl-architecture.md`.
- Definizione dell'engine visuale 2.5D basato su PixiJS con mappa zoomabile semantica, streaming eventi SSE e pannelli DOM/CSS per il Cronista e la Console.

## [2026-08-12] adr | Registrazione ADR-0007 - Autonomous Agent Minds and Event-Driven World Runtime
- Registrato ADR-0007 `docs/adr/adr-0007-autonomous-agent-mind-and-world-runtime.md`.
- Definizione dell'architettura cognitiva degli agenti (`AgentMind`), scomposizione tra percezione soggettiva ed intenzione strutturata, World Adjudicator deterministico con persistenza canonica su SQLite (Event Sourcing) e proiezioni su file Markdown.

## [2026-08-12] implementation | Milestone 1 - Vertical Slice Agentico
- Creati i contratti implementativi e la roadmap sotto `docs/architecture/`.
- Implementato il runtime Python con event store SQLite, replay, `AgentMind` persistenti, percezione privata, memorie auditate, scheduler event-driven e `WorldAdjudicator`.
- Implementati fallback deterministico e adattatore Ollama con intenzioni validate tramite JSON Schema.
- Verificata una conversazione autonoma fra due Newlander sia offline sia con `qwen3:4b` locale.
- Aggiunti test per persistenza, isolamento percettivo, anti-ricorsione della memoria, replay e rifiuto delle azioni impossibili.

## [2026-08-12] architecture | Inizializzazione Mondo Vergine (0 Abitanti di Default)
- Modificato il runtime di inizializzazione del mondo in `simulation.py` affinché ogni nuovo mondo nasca 100% vergine e privo di abitanti pre-popolati (`DEFAULT_AGENTS = ()`).
- Gli abitanti entrano in Newland esclusivamente via `ArrivalService` (CLI `newland arrive` o comandi dell'Architetto) quando l'utente decide di introdurli.
- Il metodo `seed_initial_encounter()` viene mantenuto esclusivamente come helper esplicito per le suite di test automatizzate che richiedono la coppia Elia e Amina.

## [2026-08-12] tooling | Script Unificato e Pannello di Controllo Interactive (./newland.sh)
- Creato lo script unico ed interattivo `./newland.sh` a menu ed opzioni rapide (1: Reset, 2: Start, 3: Arrive).
- Supporta sia la selezione numerica sia l'esecuzione diretta di argomenti (`./newland.sh reset`, `./newland.sh start`, `./newland.sh arrive "Nome"`).

## [2026-08-12] adr | Accettazione ADR-0008 - Zero Decisioni Statiche
- Registrato e accettato ADR-0008 `docs/adr/adr-0008-zero-static-agent-decisions.md` su esplicita direttiva di Giovanni Fiore.
- Rimosso il fallback decisionale deterministico dal runtime di produzione e dalla CLI.
- Stabilito che fisica e validazione possono essere deterministiche, mentre intenzioni, parole, priorità e riflessioni appartengono esclusivamente alla cognizione generativa privata degli agenti.
- In caso di indisponibilità: riparazione generativa, failover verso altro modello generativo o evento `CognitionDeferred`, senza azione materiale sostitutiva.
- Esteso lo stesso vincolo alla vita interiore: salienza, tono emotivo e riassunto soggettivo delle memorie sono prodotti dalla mente generativa, non dal `PerceptionService`.
- Aggiunta validazione della provenienza: una mente non può formare una memoria riferita a un evento che non ha percepito.

## [2026-08-12] implementation | Milestone 2 - Consolidamento Mentale Generativo
- Esteso il contratto cognitivo con revisioni generative di beliefs, relazioni, affetto, obiettivi e riflessioni.
- Introdotto `MentalStateApplier`, responsabile unicamente di validare limiti e applicare output già scelti dalla mente.
- Persistiti gli eventi privati `BeliefUpdated`, `RelationshipUpdated`, `AffectUpdated`, `GoalRevised` e `ReflectionCreated` con fonti e provenienza del modello.
- Verificata la persistenza su riavvio e il vincolo che una riflessione possa citare solo memorie realmente possedute.
- Verificato il contratto completo con Ollama `qwen3:4b`: memoria soggettiva, aggiornamento affettivo e azione autonoma prodotti nello stesso ciclo cognitivo.

## [2026-08-12] implementation | Milestone 2 - Bisogni Corporei Percettivi
- Implementato `PhysiologySystem` per l'evoluzione canonica di energia, fame e sete in funzione del tempo del mondo.
- Introdotta **Morte Permanente (Permadeath)** e **Istinto di Sopravvivenza**: gli agenti con parametri vitali fatali per 20 ore simulate muoiono inesorabilmente. L'istinto è iniettato nel prompt per costringere il LLM a riposare o mangiare.
- Aggiunto l'evento privato `NeedsChanged` e il relativo replay nello stato materiale.
- Le soglie corporee producono soltanto un interrupt cognitivo: nessuna risposta o azione viene scelta dal codice.
- Aggiornato il contesto privato dell'agente affinché la mente generativa percepisca lo stato corrente del proprio corpo.

## [2026-08-12] implementation | Milestone 2 - Piani, Impegni e Agenda Autonoma
- Esteso l'output cognitivo con piani strutturati, impegni a scadenza e scelta generativa della prossima attivazione.
- Persistiti `PlanRevised`, `CommitmentRevised` e `AttentionScheduled` come eventi privati con provenienza del modello.
- Il runtime esegue esclusivamente il richiamo temporale scelto dall'agente: alla scadenza non viene selezionata alcuna risposta automatica.
- Ricostruita l'agenda dopo il riavvio usando percezioni inevase, attenzione persistita e impegni attivi.
- Validati fonti, persone coinvolte e scadenze; un riferimento inventato differisce la cognizione senza produrre azioni.
- Verificato il contratto ampliato con Ollama `qwen3:4b`: Elia ha scelto in tempo reale parola, motivazione e tick della successiva attenzione.

## [2026-08-12] implementation | Milestone 3 - Territorio Situato e Risorse
- Estesa la topologia iniziale a cittadina, campo, bosco e sorgente con adiacenze canoniche.
- Aggiunte risorse locali, inventario e capacità di trasporto, effetti corporei del consumo e attività legate ai luoghi.
- Esteso il vocabolario generativo con `gather`, `consume` e `perform_activity`; nessuna affordance seleziona automaticamente un comportamento.
- Il contesto privato espone soltanto destinazioni adiacenti, risorse presenti e attività disponibili nella posizione corrente.
- Persistiti e resi percepibili localmente `ResourceGathered`, `ResourceConsumed` e `ActivityPerformed`.
- Aggiunto `TerritoryConfigured` per migrare e ricostruire via replay i mondi creati prima del territorio esteso.
- Limitato il contesto Ollama della cognizione ordinaria per evitare occupazione GPU e timeout non necessari, senza ridurre il vocabolario decisionale.
- Verificato con `qwen3:4b`: Elia ha scelto autonomamente `esaminare_edifici`, accettato dall'arbitro con conseguenza fisica e costo energetico.

## [2026-08-12] implementation | Milestone 3 - Arrivi, Lingue, Competenze e Famiglie
- Introdotto `ArrivalService` per registrare singoli e gruppi familiari come transazioni atomiche, senza generare persone o destini sociali dal codice.
- Aggiunti lingua madre, proficienze linguistiche, competenze pratiche e appartenenza familiare allo stato materiale replayable.
- Ogni nuovo Newlander riceve `TransitionRemembered`, evento privato contenente l'esperienza della propria soglia; i residenti percepiscono soltanto l'arrivo osservabile.
- Il parlato conserva lingua e testo originali senza traduzione automatica; comprensione, incomprensione ed empatia sono lasciate alla cognizione generativa.
- Le attività verificano capacità ed energia e possono incrementare esperienza, ma nessun ruolo comunitario viene assegnato dal runtime.
- Aggiunte migrazioni event-sourced per capacità, attività e ricordi iniziali, preservando risorse già consumate nei mondi esistenti.
- Semplificata la provenienza LLM in `source_ids`, riclassificata e validata dal runtime contro soli eventi percepiti e memorie possedute.
- Verificato con Ollama `qwen3:4b`: Elia ha integrato lingua, competenze e memoria della transizione e ha scelto autonomamente di esplorare il bosco.

## [2026-08-12] implementation | Milestone 3 - Cooperazione, Conflitti e Ruoli Emergenti
- Aggiunto un protocollo event-sourced nel quale proposta, accettazione o rifiuto ed esecuzione cooperativa sono decisioni generative separate; nessun effetto condiviso avviene senza consenso esplicito.
- Introdotto il confronto su eventi realmente percepiti con contestazione, offerta di risoluzione e accettazione come azioni autonome distinte; il runtime non chiude conflitti da solo.
- Resi cooperazioni e conflitti percepibili soltanto ai destinatari e osservatori locali presenti al momento dell'evento, preservando memoria e ragionamento privati.
- Aggiunte interpretazioni private e persistenti dei ruoli con etichette libere generate dalle menti; competenze e statistiche materiali non assegnano alcun ruolo.
- Validati replay, consenso, provenienza, riferimenti sociali e assenza di tassonomie con 52 test automatici.
- Verificato con Ollama `qwen3:8b`: Elia ha scelto `perform_activity` e ha generato separatamente per sé il ruolo `Osservatore Silenzioso`, fondato su eventi percepiti e non presente nel codice.
- Impostato `qwen3:8b` come default locale dopo che il contratto cognitivo ampliato ha mostrato maggiore affidabilità rispetto al 4B; errori residui producono esclusivamente retry generativi o `CognitionDeferred`.

## [2026-08-12] implementation | Milestone 3 - Risonanza, Flashback e Anamnesi
- Aggiunti nodi territoriali replayable nel bosco e presso la sorgente, esposti come affordance fisiche locali senza contenuti narrativi.
- Entrare in un nodo produce `ResonanceSignalReceived`, evento privato contenente soltanto identificatore, intensità e modalità di esposizione.
- Introdotta `attune_resonance` come azione volontaria generata; l'arbitro verifica esclusivamente che il nodo esista e sia locale.
- Aggiunti frammenti di anamnesi con etichetta e contenuto liberi, confidenza e provenienza obbligatoriamente riconducibile a un segnale percepito.
- La mente può scegliere generativamente se restare ricettiva o chiudere il canale; il filtro attentivo rispetta la scelta senza cancellare il segnale fisico.
- Le riflessioni possono ora fondarsi direttamente su eventi percepiti oltre che su memorie persistite; le variazioni affettive intense restano scelte dal modello e lo stato finale rimane limitato fra zero e uno.
- Verificati isolamento, replay, migrazione, assenza di tassonomie e assenza di flashback statici con 62 test automatici.
- Verificato con Ollama `qwen3:8b`: dopo il segnale del bosco Elia ha generato autonomamente due esperienze soggettive, una riflessione, la scelta di restare ricettivo e un'azione separata poi correttamente rifiutata dall'arbitro perché fisicamente invalida.

## [2026-08-12] implementation | Milestone 2 - Routing Cognitivo
- Introdotto `RoutedCognition` con tier ordinario e riflessivo, entrambi conformi allo stesso contratto generativo e allo stesso confine privato per agente.
- I segnali di risonanza percepiti e i conflitti attivi vengono inoltrati al tier riflessivo; le altre attivazioni restano sul tier ordinario.
- Il router non seleziona, corregge o sostituisce azioni e mutazioni mentali: inoltra integralmente il `CognitionResult` del modello e aggiunge soltanto la route alla provenienza.
- La CLI accetta pool ripetibili `--model` e `--reflective-model`; senza configurazione riflessiva distinta riusa il pool ordinario senza caricare un altro modello.
- Verificati routing, identità del contesto privato e provenienza con 64 test automatici.

## [2026-08-12] implementation | Milestone 4 - Observer API read-only
- Implementato il read model privilegiato dell'Observer con snapshot coerente di mondo e menti, ricostruito dal log canonico e dagli snapshot cognitivi persistiti.
- Aggiunti endpoint HTTP per health, snapshot e paginazione incrementale degli eventi, più stream SSE ordinato e riprendibile tramite `Last-Event-ID`.
- SQLite viene aperto in modalità realmente read-only; richieste e stream non producono eventi e non alterano le menti.
- Limitato CORS alle sole origini loopback per impedire a pagine esterne di leggere lo stato privato della Console dell'Architetto.
- Aggiunto il comando `newland serve`, bindato per default a `127.0.0.1:8765`.
- Verificati replay, riservatezza locale, ripresa SSE e non-interferenza con 70 test automatici.

## [2026-08-12] implementation | Milestone 4 - Mappa WebGL
- Creato il client locale Vite/TypeScript con store Observer, bootstrap da snapshot, stream `newland-event`, deduplicazione delle sequenze e refresh canonico.
- Implementata la scena PixiJS in modalità WebGL con proiezione deterministica del grafo, terreno, percorsi, luoghi, risorse, nodi di risonanza e Newlander.
- Aggiunti pan, zoom, selezione canvas e un percorso DOM equivalente per ispezionare ogni abitante senza produrre comandi o eventi.
- La Console dell'Architetto espone corpo e snapshot mentale privilegiato; il registro mostra envelope canonici e visibilità senza inventare prosa.
- Verificati store e layout con 4 test frontend, build TypeScript/Vite di produzione e integrazione HTTP col database reale; la QA visiva nel browser resta da completare appena è disponibile un'istanza browser collegata.

## [2026-08-12] implementation | Milestone 4 - Cronista e Console
- Implementato il Cronista Silenzioso come agente generativo extradiegetico: legge batch di eventi committati e non può agire, essere percepito o fermare il runtime.
- Persistite le voci in un database derivato separato, con provenienza passaggio per passaggio, modello, inference id, tentativi e range canonico osservato.
- Il generatore non dispone di prosa statica: usa retry e failover fra provider generativi; un fallimento lascia il batch pendente senza produrre testo sostitutivo.
- Aggiunta una revisione generativa di grounding e una validazione che respinge inferenze d'assenza prive di un esplicito evento negativo.
- Esposti query e stream SSE `chronicle-entry` read-only; la UI visualizza direttamente titolo e prosa persistiti insieme alla provenienza.
- Verificato end-to-end con `qwen3:8b`: una prima bozza non conforme è stata respinta e la voce accettata è stata generata al secondo tentativo.
- Suite complessiva: 78 test Python, 5 test frontend e build Vite di produzione.

## [2026-08-12] implementation | Milestone 4 - Tempo visuale
- Aggiunto replay materiale server-side fino a una sequenza canonica richiesta, con indicazione separata della testa live.
- Gli snapshot cognitivi storici vengono omessi esplicitamente perché il log materiale non consente di ricostruirli senza inventare stato mentale.
- Lo store frontend mantiene distinti snapshot/eventi live e snapshot/eventi visualizzati; gli stream continuano a ricevere il presente durante la pausa.
- Aggiunti pausa visiva, scrub, replay sequenziale e riallineamento al presente senza endpoint di comando e senza interferenza sulla simulazione.
- Registro, mappa e Diario seguono il cursore osservato; il Cronista e i Newlander continuano a operare sul tempo corrente.
- Milestone 4 completata funzionalmente con 80 test Python, 6 test frontend e build Vite di produzione; resta una QA visiva manuale quando sarà disponibile un browser collegato alla sessione.

## [2026-08-12] implementation | Milestone 5 - Runtime continuo
- Aggiunta la modalità `newland run --continuous`, che esegue indefinitamente le attivazioni scelte dallo scheduler e dalle agende generate dai Newlander.
- Ogni iterazione completa deliberazione, arbitraggio e persistenza atomica prima di pubblicare gli eventi su standard output.
- Ctrl-C arresta il processo senza creare eventi diegetici, modificare intenzioni o sostituire una deliberazione in corso.
- Verificato il lifecycle con tre attivazioni complete simulate e una prova Ollama reale interrotta durante una deliberazione: exit code pulito e nessun output parziale.
- In Ollama risultava caricato soltanto `qwen3:8b`, usato da Newland; nessun processo LLM estraneo era presente.
- Suite complessiva aggiornata a 82 test Python; 6 test frontend e build Vite restano verdi.

## [2026-08-12] adr | Proposta ADR-0009 - Supervisore e priorità inferenza
- Proposto ADR-0009 `docs/adr/adr-0009-supervised-runtime-and-inference-priority.md`.
- La decisione evita che il Cronista downstream competa senza controllo con le menti dei Newlander sullo stesso Ollama locale.
- Proposta una coda seriale agent-first con rapporto iniziale almeno `8:1`, health operativo separato dal mondo, servizio statico della UI e shutdown coordinato.
- Implementazione sospesa in attesa dell'approvazione esplicita di Giovanni Fiore, come richiesto dalla governance ADR.

## [2026-08-12] adr | Proposta ADR-0010 - Capacità di carico corporea dinamica
- Proposto ADR-0010 `docs/adr/adr-0010-dynamic-embodied-carrying-capacity.md`.
- Individuato il valore universale `inventory_capacity = 20.0` nello stato materiale, nel bootstrap, negli arrivi e nel replay legacy.
- Proposto un profilo corporeo obbligatorio importato dalla scheda agentica e uno stato fisico event-sourced che separa età, somatotipo, massa, forza, condizionamento, mobilità, fatica, lesioni e malattia.
- La capacità effettiva sarà derivata da una policy fisica versionata; l'LLM continuerà a decidere ogni tentativo e ogni reazione, senza poter riscrivere i limiti materiali.
- La migrazione di Elia e Amina non inventerà dati mancanti e richiederà profili corporei espliciti prima dell'implementazione completa.
- Implementazione sospesa in attesa dell'approvazione esplicita di Giovanni Fiore, come richiesto dalla governance ADR.

## [2026-08-12] adr | Approvazione ADR-0009 - Supervisore e priorità inferenza
- Giovanni Fiore ha approvato esplicitamente ADR-0009.
- Lo stato di `docs/adr/adr-0009-supervised-runtime-and-inference-priority.md` è passato da `Proposed` ad `Accepted`.
- È autorizzata l'implementazione incrementale del supervisore locale, dell'ammissione inferenza agent-first e della telemetria operativa non diegetica.
- ADR-0010 resta separatamente in stato `Proposed` e non autorizza ancora modifiche al modello corporeo.

## [2026-08-12] implementation | ADR-0009 - Runtime supervisionato agent-first
- Aggiunta un'ammissione Ollama seriale condivisa con priorità alle menti, turno pesato del Cronista, nessuna preemption e telemetria di code, attese e fallimenti.
- Introdotto `newland live` per eseguire ciclo agentico, Cronista, Observer API e build WebGL sotto un unico lifecycle con shutdown coordinato.
- L'Observer serve `ui/dist/` sullo stesso endpoint loopback ed espone health operativo separato dallo stato canonico.
- Health distingue attivazioni riuscite, `CognitionDeferred`, cursore canonico, cursore narrato e backlog derivato.
- Il supervisore non scarica modelli o processi Ollama estranei; un fallimento del Cronista viene registrato e ritentato senza fermare gli abitanti.
- Verifica completata con 90 test Python, 6 test frontend e build Vite di produzione.
- Smoke test reale con `qwen3:8b`: UI e health hanno mostrato i tre componenti attivi, una deliberazione agente in corso e il Cronista correttamente accodato.
- La deliberazione ha esaurito tre riparazioni generative per provenienza di anamnesi non valida ed è diventata `CognitionDeferred`; nessuna azione o esperienza statica ha sostituito la mente.
- Lo smoke ha rivelato che un job già accodato poteva partire durante lo shutdown; l'ammissione ora entra in stato chiuso, lascia terminare soltanto la chiamata attiva e rifiuta quelle in attesa.
- Il modello Ollama caricato dallo smoke è stato arrestato; al termine non risultano processi LLM attivi.

## [2026-08-13] ingest | Proposta UI dell'Observer (ADR-0014)
- Ingerito il design system e la proposta visuale `docs/raw/newland-ui-proposal.md`.
- Generato `docs/wiki/sources/src-newland-ui-proposal.md` e collegato alle entità esistenti *Cronista Silenzioso* e *Console dell'Architetto*.
- Approvato e registrato ADR-0014 `docs/adr/adr-0014-observer-ui-architecture-and-aesthetics.md` per l'adozione del design system (DOM overlay su PixiJS WebGL).

## [2026-08-13] ingest | Brainstorming 09 - Economia cognitiva multi-modello
- Conservata la fonte grezza in `docs/raw/raw-brainstorming-09-cognitive-economy-and-model-tiers.md`.
- Creata la sintesi fonte e il concetto candidato di economia cognitiva, distinguendo esempi dimensionali, ipotesi sperimentali e invarianti già approvati.
- Collegati benchmark John, ADR-0008, ADR-0009, ADR-0013, ADR-0016 e Cronista Silenzioso.
- Nessuna policy di routing, integrazione cloud o corsia d'inferenza indipendente è stata approvata o implementata tramite questo ingest.

## [2026-08-13] ingest | Brainstorming 10 - Alibaba Model Studio e benchmark cognitivo cloud
- Conservata la proposta grezza e verificati quote, durata, thinking mode e `Free Quota Only` sulle fonti ufficiali Alibaba disponibili alla data dell'ingest.
- Qualificato il milione di token come budget per modello e non come numero di decisioni; input, output, reasoning e retry possono consumarlo rapidamente.
- Proposto ADR-0018 per un pilot offline di 10–20 snapshot, sanitizzato, opt-in, senza chain-of-thought persistita e con arresto locale della spesa.
- Nessun provider cloud, comando di benchmark o cambiamento del runtime live è stato implementato; ADR-0018 attende approvazione esplicita.

## [2026-08-13] query | Idoneità di Qwen Character e conservazione quote grandi
- Verificati Qwen Plus Character e Flash Character: specializzazione role-play, quota separata, prezzi, session cache e assenza di thinking/structured output.
- Aggiornato ADR-0018 con un funnel Character-first e cap distinti: il 235B riceve al massimo `75k` token e soltanto 5–10 casi del disagreement set.
- La session cache resta esclusa dalla valutazione di qualità e non può diventare memoria remota implicita degli abitanti.
- Persistita la valutazione in `docs/wiki/synthesis/syn-qwen-character-model-fit.md`; nessuna integrazione è stata implementata e ADR-0018 resta proposto.

## [2026-08-13] adr | Approvazione ADR-0018 - Benchmark cognitivo cloud limitato
- Giovanni Fiore ha approvato esplicitamente ADR-0018.
- Lo stato di `docs/adr/adr-0018-bounded-cloud-cognition-benchmark.md` è passato da `Proposed` ad `Accepted`.
- Sono autorizzati l'harness offline, i test senza rete e il pilot Alibaba entro sanitizzazione, opt-in, `Free Quota Only`, funnel e cap per modello definiti nell'ADR.
- Il provider cloud resta vietato nei comandi live e nel Cronista; ogni adozione operativa richiederà un ADR successivo.

## [2026-08-13] implementation | ADR-0019 - Cognition Alibaba live
- Integrato DashScope nei comandi `run` e `live` tramite model spec qualificati, opt-in esplicito, endpoint HTTPS consentito e ledger token persistente non canonico.
- Conservata la sovranità agentica: failover soltanto fra provider generativi dichiarati; ogni esaurimento produce `CognitionDeferred` senza azioni statiche.
- Mantenuto il Cronista locale e separato dal cambio di provider delle menti.
- Verificato il canary reale finito di John Flower: `ActionProposed` 71 generato da `dashscope:qwen-flash-character`, accettato e avviato, con inference ID e senza reasoning o credenziali persistiti.
- Il ledger registra 57.579 token in nove chiamate, inclusi quattro canary differiti usati per irrobustire grounding e parsing; budget residuo locale 42.421 token.
- Suite complessiva: 145 test Python verdi.

## [2026-08-13] adr | Proposta ADR-0020 - Prompt registry e annealing cognitivo
- Rilevato che il prompt cognitivo e il repair sono incorporati nei moduli Python e non possono evolvere o fare rollback indipendentemente dal rilascio applicativo.
- Proposto un registry versionato sotto `docs/`, un learning ledger redatto, lesson overlay tecnici, annealer locale subordinato, canary sulle attivazioni naturali e rollback atomico.
- Separato il nucleo human-gated dall'overlay autonomo: nessuna lezione può prescrivere azioni o modificare schema, eventi, menti o principi del mondo.
- Nessuna modifica al runtime è autorizzata finché ADR-0020 non riceve approvazione esplicita.

## [2026-08-13] adr | Approvazione ADR-0020 - Prompt registry e annealing cognitivo
- Giovanni Fiore ha approvato esplicitamente ADR-0020 con l'indicazione di procedere.
- Lo stato di `docs/adr/adr-0020-external-cognition-prompt-registry-and-autonomous-annealing.md` è passato da `Proposed` ad `Accepted`.
- Sono autorizzati registry esterno, learning ledger redatto, overlay autonomi limitati, canary, hot reload transazionale e rollback entro i gate dell'ADR.

## [2026-08-13] implementation | ADR-0020 - Prompt registry e annealing cognitivo
- Migrato `agent-cognition-v4` da stringhe Python a un registry verificato sotto `docs/prompts/agent-cognition/`, condiviso da Ollama, DashScope live e benchmark cloud.
- Ogni inferenza congela prompt e schema, registra versione e hash canonici e mantiene lo stesso artefatto durante il repair.
- Aggiunto learning ledger separato con fingerprint e categorie strutturate senza prompt privati, output integrali, segreti o reasoning.
- Aggiunto annealer Ollama locale a priorità inferiore alle menti, policy anti-coaching, trigger aggregato, canary naturale, promozione e rollback atomici.
- Aggiunti i comandi `newland prompts status|run|rollback` e l'opt-in live `--allow-prompt-annealing`.
- Il repair DashScope include ora la risposta invalida precedente senza prescrivere un'azione, evitando una seconda richiesta priva del dato da correggere.
- Il regression set esterno conserva in forma sintetica i quattro difetti emersi nei canary Alibaba; hash, hot reload tra inferenze e isolamento del manifest sono coperti dai test.
- Verifica finale completata con 171 test Python verdi, compilazione dei moduli, controllo diff e stato CLI del registry `healthy`.
