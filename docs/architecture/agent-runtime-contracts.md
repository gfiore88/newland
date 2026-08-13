# NEWLAND AGENT RUNTIME: CONTRATTI E INVARIANTI

> Stato: baseline implementativa di ADR-0007.

## 1. Confini del sistema

- [BND-001] Il database degli eventi rappresenta la verità canonica della simulazione.
- [BND-002] Ogni `AgentMind` possiede stato cognitivo e memoria privati.
- [BND-003] I provider LLM Ollama e DashScope sono stateless: ricevono un contesto privato agent-scoped e restituiscono una proposta d'azione; DashScope richiede consenso e budget live espliciti.
- [BND-004] Il `WorldAdjudicator` è l'unico componente autorizzato a produrre conseguenze canoniche delle azioni.
- [BND-005] Cronista e UI sono proiezioni downstream e non partecipano alla deliberazione.
- [BND-006] Il router cognitivo seleziona soltanto un tier di inferenza; non modifica contesto privato, intenzione o aggiornamenti mentali generati dal provider scelto.

## 2. Event envelope canonico

Ogni evento persistito contiene:

| Campo | Tipo | Invariante |
|---|---|---|
| `event_id` | UUID string | Univoco e immutabile. |
| `sequence` | integer | Assegnato dal database, monotono. |
| `schema_version` | integer | Versione del payload; baseline `1`. |
| `world_tick` | integer | Maggiore o uguale a zero. |
| `world_time` | ISO-8601 string | Tempo diegetico, non tempo macchina. |
| `event_type` | string | Nome al passato di un fatto o di una fase d'azione. |
| `actor_ids` | list[string] | Entità causalmente coinvolte. |
| `location` | string/null | Luogo canonico dell'evento, se applicabile. |
| `payload` | object | Dati schema-versionati specifici dell'evento. |
| `visibility` | `public`, `local`, `private` | Confine percettivo minimo. |
| `recipient_ids` | list[string] | Obbligatorio per eventi `private`. |
| `causation_id` | UUID string/null | Evento o proposta che ha causato il fatto. |

### Eventi baseline

- [EVT-001] `WorldInitialized`, `AgentRegistered`, `AgentArrived` descrivono lo stato iniziale.
- [EVT-002] `ActionProposed` registra un'intenzione schema-validata.
- [EVT-003] `ActionAccepted`, `ActionModified`, `ActionRejected` registrano l'arbitraggio.
- [EVT-004] `SpeechUttered`, `AgentMoved`, `AgentRested`, `HelpOffered` registrano conseguenze osservabili.
- [EVT-005] `MemoryEncoded` è privato e registra l'acquisizione soggettiva di un'esperienza.
- [EVT-006] `TerritoryConfigured` evolve in modo replayable topologia, risorse e attività di un mondo già persistito.
- [EVT-007] `ResourceGathered`, `ResourceConsumed` e `ActivityPerformed` registrano conseguenze materiali osservabili localmente.
- [EVT-008] `AgentArrived` rende visibile una nuova presenza; `TransitionRemembered` conserva privatamente l'esperienza della soglia.
- [EVT-009] `FamilyGroupUpdated` registra legami familiari dichiarati senza assegnare ruoli sociali.
- [EVT-010] `AgentCapabilitiesConfigured` e `TerritoryActivitiesConfigured` migrano identità e attività preesistenti senza riscrivere la storia.
- [EVT-011] `CooperationProposed`, `CooperationResponded` e `CooperationPerformed` registrano proposta, consenso o rifiuto e attività condivisa come fatti distinti.
- [EVT-012] `DisputeOpened` e `DisputeResponded` registrano il confronto fra partecipanti su un evento realmente percepito.
- [EVT-013] `RoleInterpretationRevised` è privato: registra una lettura soggettiva generata dalla mente, non una carica canonica assegnata dal mondo.
- [EVT-014] `ResonanceNodesConfigured` registra posizione e intensità fisica dei nodi senza descrivere effetti mentali.
- [EVT-015] `ResonanceSignalReceived` contiene esclusivamente nodo, intensità e modalità di esposizione ed è privato dell'abitante coinvolto.
- [EVT-016] `AnamnesisFragmentRevised` e `ResonanceOrientationRevised` sono mutazioni private generate dalla mente con provenienza del provider e modello effettivamente selezionati.
- [EVT-017] `ActionStarted`, `ActionCompleted` e `ActionInterrupted` rendono replayable il tempo realmente occupato da un'azione; la conseguenza materiale esiste soltanto al completamento.
- [EVT-018] `NeedsChanged` conserva separatamente esposizione a esaurimento, inedia e disidratazione, così la causa di un eventuale `AgentDied` non dipende da stato volatile.

## 3. Contratto `AgentMind`

La baseline persiste:

- [MND-001] identità, valori e temperamento;
- [MND-002] bisogni e stato affettivo correnti;
- [MND-003] convinzioni con confidenza e provenienza;
- [MND-004] relazioni indicizzate per altro agente;
- [MND-005] obiettivi, piani e impegni strutturati con stato e provenienza;
- [MND-006] cursore dell'ultimo evento percepito;
- [MND-007] memorie episodiche con salienza, tono emotivo e provenienza.
- [MND-008] prossima attivazione scelta dalla mente, con tick e motivazione.
- [MND-009] lingua madre, lingue parlate, competenze pratiche e appartenenza familiare come fatti situati distinti dalle interpretazioni sociali.
- [MND-010] interpretazioni private e rivedibili dei ruoli propri o di persone conosciute, con etichetta libera, confidenza e provenienza.
- [MND-011] frammenti di anamnesi soggettivi, fallibili e rivedibili, distinti dai fatti canonici del mondo.
- [MND-012] orientamento personale verso la risonanza: la mente può scegliere di restare ricettiva o chiudere il proprio canale attentivo.
- [MND-013] Il retrieval può consolidare memorie semanticamente equivalenti nella sola vista cognitiva, esponendo frequenza e provenienza senza cancellare o riscrivere gli episodi originali.

Salienza soggettiva, tono emotivo, convinzioni, interpretazione delle relazioni e riflessioni sono output generativi della mente. Il runtime ne valida intervalli e riferimenti agli eventi percepiti, ma non li assegna con tabelle o euristiche statiche.

### Aggiornamenti mentali generativi

Ogni risposta cognitiva può includere, oltre all'intenzione:

- [GEN-001] `memory_appraisals`: interpretazioni soggettive di eventi effettivamente percepiti;
- [GEN-002] `beliefs`: revisioni di convinzioni con confidenza e fonti;
- [GEN-003] `relationships`: variazioni di familiarità, fiducia, calore e tensione scelte dalla mente;
- [GEN-004] `affect`: variazioni emotive motivate;
- [GEN-005] `reflections`: sintesi sostenute da eventi percepiti o memorie esistenti;
- [GEN-006] `goals`: aggiunte o rimozioni motivate degli obiettivi.
- [GEN-007] `plans`: creazione, revisione, completamento o abbandono di piani con passi espliciti.
- [GEN-008] `commitments`: impegni autonomi con scadenza e persone conosciute coinvolte.
- [GEN-009] `attention_schedule`: momento e ragione della prossima riattivazione spontanea.
- [GEN-010] `role_interpretations`: creazione, revisione o ritiro di significati sociali formulati liberamente dalla mente, senza tassonomia del runtime.
- [GEN-011] `anamnesis_fragments`: immagini, memorie somatiche, intuizioni o fenomeni liberamente descritti e trattati come esperienze soggettive, non rivelazioni canoniche.
- [GEN-012] `resonance_orientation`: scelta motivata di ricevere o filtrare futuri segnali interiori; `null` conserva la scelta precedente.

Il runtime limita i delta numerici, impedisce riferimenti a persone o memorie sconosciute e persiste ogni mutazione come evento privato con provenienza del modello. Non decide se o come uno stato mentale debba cambiare.

La mente non contiene lo stato globale e non può leggere direttamente il database canonico.

## 4. Percezione

`PerceptionService` riceve eventi canonici e lo stato pubblico strettamente necessario dell'agente.

- [PER-001] Un evento `public` è percepibile da tutti.
- [PER-002] Un evento `local` è percepibile solo dagli agenti presenti nel luogo dell'evento.
- [PER-003] Un evento `private` è percepibile solo dai `recipient_ids`.
- [PER-004] Un agente non riceve prompt, memorie, motivazioni private o deliberazioni di un altro agente.
- [PER-005] La percezione può generare una memoria soggettiva, ma non modifica il fatto canonico.
- [PER-006] Il contesto cognitivo espone soltanto uscite adiacenti, risorse presenti e attività disponibili nella posizione corrente.
- [PER-007] Il parlato conserva testo e lingua originali; il runtime non traduce né assegna automaticamente comprensione.
- [PER-008] La memoria della transizione è percepibile esclusivamente dalla persona che l'ha vissuta.
- [PER-009] Un segnale di risonanza non è percepibile da altri abitanti e non contiene flashback, immagini, significato o reazione.
- [PER-010] Dopo una scelta generativa di non ricettività, il filtro attentivo esclude i segnali dalla cognizione senza cancellare o riscrivere gli eventi fisici.

## 5. Intenzione e arbitraggio

Un'intenzione contiene `action_type`, `target_id`, `destination`, `duration_minutes`, `spoken_content`, `resource_id`, `quantity`, `activity_id`, `motivation_summary` e `confidence`.

- [ACT-001] Il runtime rifiuta output non conformi allo schema.
- [ACT-002] Il mondo verifica esistenza, posizione, tempo, risorse e target.
- [ACT-003] La proposta e il suo esito vengono persistiti nello stesso commit transazionale.
- [ACT-004] Il testo libero può diventare dialogo o motivazione, ma non una mutazione arbitraria dello stato.
- [ACT-005] Movimento, raccolta, consumo e attività vengono scelti dalla mente; il mondo verifica adiacenza, presenza, quantità, capacità d'inventario ed energia.
- [ACT-006] Le conseguenze fisiche aggiornano risorse, inventario e corpo soltanto tramite eventi canonici riducibili.
- [ACT-007] Per parlare, la mente sceglie testo e lingua; l'arbitro verifica soltanto che il parlante conosca quella lingua.
- [ACT-008] Le attività possono richiedere una competenza minima e produrre esperienza incrementale; il runtime non deriva da ciò un ruolo comunitario.
- [ACT-009] I parametri estranei all'azione scelta vengono rimossi al confine del protocollo LLM; azione, contenuti e parametri pertinenti restano quelli generati dalla mente e attraversano la normale validazione.
- [ACT-010] `attune_resonance` è un'intenzione generativa volontaria valida soltanto presso un nodo locale; il suo esito fisico non prescrive alcuna esperienza interiore.
- [ACT-011] La durata proposta dalla mente viene convertita in tick canonici: accettazione e inizio non applicano l'effetto materiale, che viene ricalcolato e validato al completamento.
- [ACT-012] Durante un'azione pendente l'agente resta esposto al tempo e alla fisiologia; morte o perdita delle precondizioni producono `ActionInterrupted` senza effetto materiale.
- [ACT-013] Il contesto privato espone costi, unità temporali ed effetti consumabili dalla stessa policy usata dall'arbitro, senza consigliare quale azione scegliere.

## 6. Arrivi e identità sociali

- [ARR-001] Un arrivo è un input esterno esplicito: il runtime non inventa autonomamente nuove persone o famiglie.
- [ARR-002] Registrazione del corpo, evento d'arrivo, memoria privata e snapshot mentali vengono committati atomicamente anche per gruppi familiari.
- [ARR-003] Residenti e nuovi arrivati vengono riattivati dall'evento, ma accoglienza, fiducia, cooperazione e conflitto restano decisioni generative individuali.
- [ARR-004] Lingua madre e capacità sono caratteristiche della persona; mediatore, costruttore, saggio o protettore sono significati sociali emergenti e non campi assegnati dal motore.

## 7. Cooperazione, conflitto e ruoli emergenti

- [SOC-001] Una cooperazione nasce soltanto da `propose_cooperation` scelto da un agente verso una persona presente e un'attività locale realmente disponibile.
- [SOC-002] Soltanto il destinatario decide `accept` o `decline`; prima di un'accettazione esplicita nessun effetto materiale condiviso può avvenire.
- [SOC-003] Dopo il consenso, entrambi i partecipanti possono scegliere di avviare l'attività; il runtime verifica presenza, energia e capacità di entrambi senza scegliere chi agirà.
- [SOC-004] Un conflitto può essere aperto soltanto da chi ha percepito l'evento contestato e prosegue tramite atti generativi distinti di contestazione, proposta o accettazione della risoluzione.
- [SOC-005] Nessun conflitto viene risolto automaticamente: una proposta di risoluzione diventa canonica soltanto quando l'altra parte la accetta esplicitamente.
- [SOC-006] Mediatore, costruttore, saggio, protettore o qualsiasi altra etichetta non appartengono a un enum e non vengono derivati da skill, statistiche o frequenze d'azione.
- [SOC-007] Ogni mente può attribuire a sé o a persone conosciute ruoli differenti e perfino incompatibili; tali interpretazioni restano private finché un agente non le rende osservabili attraverso una propria azione o parola.

## 8. Risonanza e anamnesi

- [RSN-001] I nodi sono fatti territoriali replayable con luogo e intensità; non possiedono tabelle di flashback, archetipi o contenuti narrativi.
- [RSN-002] Entrare nel luogo di un nodo produce un contatto fisico privato; soltanto la mente decide se trasformarlo in memoria, riflessione, frammento di anamnesi o nessun cambiamento.
- [RSN-003] Ogni frammento richiede almeno una fonte riconducibile a un `ResonanceSignalReceived` realmente percepito o ricordato dall'agente.
- [RSN-004] `phenomenon_label`, contenuto, interpretazione e confidenza sono output liberi del modello e non appartengono a enum o pattern del runtime.
- [RSN-005] La stessa esposizione può produrre esperienze diverse in menti diverse; il runtime non confronta personalità o statistiche per scegliere l'esito.
- [RSN-006] La scelta di chiudere il canale impedisce l'interrupt cognitivo dei segnali successivi, ma l'agente può continuare la vita ordinaria o scegliere in futuro una nuova sintonizzazione.
- [RSN-007] Se la cognizione fallisce, il mondo registra `CognitionDeferred` e non crea alcun flashback o orientamento sostitutivo.

## 9. Scheduling

- [SCH-001] Gli agenti vengono attivati da stimoli, soglie di bisogno, incontri, impegni o riflessioni pianificate.
- [SCH-002] I processi fisici e fisiologici deterministici avanzano senza chiamate LLM; nessun processo deterministico sceglie un'intenzione per un abitante.
- [SCH-003] A parità di tick e priorità, l'ordine è stabile per `agent_id`.
- [SCH-004] Un errore di inferenza attiva riparazione generativa, eventuale failover generativo e infine `CognitionDeferred`; non produce mai un'azione statica sostitutiva.
- [SCH-005] Ogni `ActionProposed` registra provider, modello, inference ID, versione prompt, numero di tentativi e route cognitiva.
- [SCH-006] Il runtime persiste `AttentionScheduled` e riattiva la mente al tick scelto dal modello, senza prescrivere il contenuto della deliberazione.
- [SCH-007] Gli impegni attivi producono un richiamo alla scadenza scelta dalla mente; il richiamo non implica alcuna azione automatica.
- [SCH-008] Al riavvio, l'agenda viene ricostruita da eventi non ancora percepiti, prossima attenzione persistita e impegni attivi.
- [SCH-009] Cognizione ordinaria usa il pool rapido; un segnale di risonanza percepito o un conflitto attivo usa il pool riflessivo configurato.
- [SCH-010] Entrambi i pool ricevono lo stesso `CognitionContext` isolato dell'agente e possono contenere più modelli per failover esclusivamente generativo.
- [SCH-011] Se non viene configurato un pool riflessivo distinto, la route resta auditabile ma usa lo stesso pool ordinario; il router non sintetizza mai un risultato.
- [SCH-012] In modalità `--continuous` il processo esegue una sola attivazione completa per iterazione e prosegue finché riceve un arresto esterno.
- [SCH-013] Ctrl-C chiude il processo tra transazioni; non genera azioni, pensieri o eventi canonici di arresto attribuiti ai Newlander.
- [SCH-014] Gli eventi di ogni attivazione vengono emessi su standard output soltanto dopo il commit atomico di evento e snapshot mentale.
- [SCH-015] Una condizione somatica critica o fatale genera richiami ravvicinati finché persiste, senza cambiare obiettivi, intenzione o priorità semantica della mente.
- [SCH-016] Il completamento di un'azione è un'attivazione materiale distinta dalla deliberazione e viene ricostruito da `ActionStarted` dopo un riavvio.

### Supervisione e inferenza condivisa

- [OPS-001] `newland live` avvia in un unico processo il ciclo autonomo, il Cronista, l'Observer e la build statica WebGL.
- [OPS-002] Una sola ammissione seriale coordina inizialmente cognition locale/cloud e Ollama: le menti usano la classe `agent`, il Cronista usa `chronicle` e nessuna richiesta in corso viene interrotta.
- [OPS-003] Quando entrambe le classi restano in attesa, le menti vincono i pareggi e ricevono inizialmente otto turni per ogni turno del Cronista.
- [OPS-004] Il peso è configurazione operativa e non entra in prompt, percezioni, memorie o storia canonica.
- [OPS-005] Fallimento o ritardo del Cronista lascia il batch derivato ripetibile; non ferma il ciclo agentico e non produce prosa sostitutiva.
- [OPS-006] Ctrl-C ferma nuove ammissioni e attende la fine della transazione attiva prima di chiudere database e servizi.
- [OPS-007] `/api/health` distingue componenti, code, workload in corso, attivazioni riuscite, differimenti cognitivi e backlog del Cronista.
- [OPS-008] Il supervisore registra i modelli configurati ma non arresta né scarica processi Ollama che non ha avviato.
- [OPS-009] I model spec qualificati `ollama:<model>` e `dashscope:<model>` definiscono pool e ordine di failover; un tag senza prefisso resta Ollama per retrocompatibilità.
- [OPS-010] La live DashScope richiede `--allow-cloud-live`, credenziale locale, endpoint Alibaba HTTPS e cap cumulativo; il ledger operativo è separato dall'event store canonico.
- [OPS-011] `/api/health` espone budget consumato/residuo e circuit state senza chiavi, prompt, risposte private o chain-of-thought.
- [OPS-012] Errori terminali di quota o billing saltano gli altri provider cloud della stessa attivazione; soltanto un generatore locale esplicitamente configurato può continuare.
- [OPS-013] Il contratto cognitivo viene caricato dal registry esterno `docs/prompts/agent-cognition`; una singola inferenza mantiene immutabili prompt e schema anche durante un repair.
- [OPS-014] Ogni provenienza cognitiva registra `prompt_version`, `prompt_hash` e `schema_hash`; hash o manifest invalidi non vengono attivati.
- [OPS-015] Gli errori strutturali confluiscono nel learning ledger non canonico e minimizzato; l'annealer locale può modificare soltanto lesson overlay tecnici e resta subordinato alle menti.
- [OPS-016] Candidate prompt usano attivazioni naturali come canary: un repair causa rollback, mentre la promozione avviene soltanto al confine fra attivazioni complete.

### Bisogni corporei

- [BDY-001] Energia, fame e sete appartengono allo stato materiale canonico, non alla narrazione del modello.
- [BDY-002] Il tempo modifica questi valori attraverso `NeedsChanged`, evento privato percepibile esclusivamente dall'abitante interessato.
- [BDY-003] Il superamento di una soglia può interrompere e riattivare la cognizione, ma non seleziona riposo, cibo, movimento o alcuna altra risposta.
- [BDY-004] La risposta al corpo resta un'intenzione generativa dell'agente e attraversa il normale arbitraggio del mondo.
- [BDY-005] Il contesto privato traduce le scale opposte di energia, fame e sete in condizioni nominali, trend, durata della condizione e cause critiche; non contiene un'azione obbligatoria.
- [BDY-006] Esaurimento, inedia e disidratazione accumulano esposizioni fatali indipendenti soltanto dopo il reale attraversamento della rispettiva soglia.
- [BDY-007] Recuperare una dimensione corporea azzera soltanto la sua esposizione; le altre cause restano intatte e replayable.

## 10. Replay e test

- [TST-001] Riducendo gli eventi dall'inizio si deve ricostruire lo stesso stato materiale.
- [TST-002] Un evento privato non deve comparire nella percezione di un altro agente.
- [TST-003] Un'azione fisicamente impossibile deve generare `ActionRejected` e nessuna conseguenza materiale.
- [TST-004] Il replay usa decisioni già committate; una nuova inferenza genera un ramo distinto.
- [TST-005] Il replay ricostruisce stato e ciclo delle cooperazioni e dei conflitti senza rieseguire inferenze.
- [TST-006] Una competenza materiale, inclusa `mediazione`, non crea alcun ruolo: serve un'esplicita interpretazione generata dalla mente.
- [TST-007] Replay e migrazione ricostruiscono i nodi di risonanza senza rigenerare esperienze interiori.
- [TST-008] Un test di indisponibilità LLM deve provare che il segnale fisico non produce frammenti o orientamenti statici.
- [TST-009] Il runner continuo deve essere arrestabile soltanto fra attivazioni complete e non deve imporre un limite implicito al numero di cicli.
- [TST-010] I test di sopravvivenza verificano informazione, provenienza, replay e fattibilità, ma non impongono alla mente di scegliere una specifica azione salvifica.
