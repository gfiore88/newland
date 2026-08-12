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
