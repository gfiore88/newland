# NEWLAND AGENT RUNTIME: CONTRATTI E INVARIANTI

> Stato: baseline implementativa di ADR-0007.

## 1. Confini del sistema

- [BND-001] Il database degli eventi rappresenta la verità canonica della simulazione.
- [BND-002] Ogni `AgentMind` possiede stato cognitivo e memoria privati.
- [BND-003] Il servizio LLM è stateless: riceve un contesto privato e restituisce una proposta d'azione.
- [BND-004] Il `WorldAdjudicator` è l'unico componente autorizzato a produrre conseguenze canoniche delle azioni.
- [BND-005] Cronista e UI sono proiezioni downstream e non partecipano alla deliberazione.

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

Salienza soggettiva, tono emotivo, convinzioni, interpretazione delle relazioni e riflessioni sono output generativi della mente. Il runtime ne valida intervalli e riferimenti agli eventi percepiti, ma non li assegna con tabelle o euristiche statiche.

### Aggiornamenti mentali generativi

Ogni risposta cognitiva può includere, oltre all'intenzione:

- [GEN-001] `memory_appraisals`: interpretazioni soggettive di eventi effettivamente percepiti;
- [GEN-002] `beliefs`: revisioni di convinzioni con confidenza e fonti;
- [GEN-003] `relationships`: variazioni di familiarità, fiducia, calore e tensione scelte dalla mente;
- [GEN-004] `affect`: variazioni emotive motivate;
- [GEN-005] `reflections`: sintesi sostenute da memorie esistenti;
- [GEN-006] `goals`: aggiunte o rimozioni motivate degli obiettivi.
- [GEN-007] `plans`: creazione, revisione, completamento o abbandono di piani con passi espliciti.
- [GEN-008] `commitments`: impegni autonomi con scadenza e persone conosciute coinvolte.
- [GEN-009] `attention_schedule`: momento e ragione della prossima riattivazione spontanea.

Il runtime limita i delta numerici, impedisce riferimenti a persone o memorie sconosciute e persiste ogni mutazione come evento privato con provenienza del modello. Non decide se o come uno stato mentale debba cambiare.

La mente non contiene lo stato globale e non può leggere direttamente il database canonico.

## 4. Percezione

`PerceptionService` riceve eventi canonici e lo stato pubblico strettamente necessario dell'agente.

- [PER-001] Un evento `public` è percepibile da tutti.
- [PER-002] Un evento `local` è percepibile solo dagli agenti presenti nel luogo dell'evento.
- [PER-003] Un evento `private` è percepibile solo dai `recipient_ids`.
- [PER-004] Un agente non riceve prompt, memorie, motivazioni private o deliberazioni di un altro agente.
- [PER-005] La percezione può generare una memoria soggettiva, ma non modifica il fatto canonico.

## 5. Intenzione e arbitraggio

Un'intenzione contiene `action_type`, `target_id`, `destination`, `duration_minutes`, `spoken_content`, `motivation_summary` e `confidence`.

- [ACT-001] Il runtime rifiuta output non conformi allo schema.
- [ACT-002] Il mondo verifica esistenza, posizione, tempo, risorse e target.
- [ACT-003] La proposta e il suo esito vengono persistiti nello stesso commit transazionale.
- [ACT-004] Il testo libero può diventare dialogo o motivazione, ma non una mutazione arbitraria dello stato.

## 6. Scheduling

- [SCH-001] Gli agenti vengono attivati da stimoli, soglie di bisogno, incontri, impegni o riflessioni pianificate.
- [SCH-002] I processi fisici e fisiologici deterministici avanzano senza chiamate LLM; nessun processo deterministico sceglie un'intenzione per un abitante.
- [SCH-003] A parità di tick e priorità, l'ordine è stabile per `agent_id`.
- [SCH-004] Un errore di inferenza attiva riparazione generativa, eventuale failover generativo e infine `CognitionDeferred`; non produce mai un'azione statica sostitutiva.
- [SCH-005] Ogni `ActionProposed` registra provider, modello, inference ID, versione prompt e numero di tentativi.
- [SCH-006] Il runtime persiste `AttentionScheduled` e riattiva la mente al tick scelto dal modello, senza prescrivere il contenuto della deliberazione.
- [SCH-007] Gli impegni attivi producono un richiamo alla scadenza scelta dalla mente; il richiamo non implica alcuna azione automatica.
- [SCH-008] Al riavvio, l'agenda viene ricostruita da eventi non ancora percepiti, prossima attenzione persistita e impegni attivi.

### Bisogni corporei

- [BDY-001] Energia, fame e sete appartengono allo stato materiale canonico, non alla narrazione del modello.
- [BDY-002] Il tempo modifica questi valori attraverso `NeedsChanged`, evento privato percepibile esclusivamente dall'abitante interessato.
- [BDY-003] Il superamento di una soglia può interrompere e riattivare la cognizione, ma non seleziona riposo, cibo, movimento o alcuna altra risposta.
- [BDY-004] La risposta al corpo resta un'intenzione generativa dell'agente e attraversa il normale arbitraggio del mondo.

## 7. Replay e test

- [TST-001] Riducendo gli eventi dall'inizio si deve ricostruire lo stesso stato materiale.
- [TST-002] Un evento privato non deve comparire nella percezione di un altro agente.
- [TST-003] Un'azione fisicamente impossibile deve generare `ActionRejected` e nessuna conseguenza materiale.
- [TST-004] Il replay usa decisioni già committate; una nuova inferenza genera un ramo distinto.
