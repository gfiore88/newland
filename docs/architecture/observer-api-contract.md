# NEWLAND OBSERVER: CONTRATTO HTTP E SSE

## Scopo

Questo documento specifica il read model locale introdotto da [ADR-0006](../adr/adr-0006-observer-engine-2d-webgl-architecture.md). L'Observer espone la verità canonica persistita necessaria alla mappa WebGL, al Diario del Cronista Silenzioso e alla Console dell'Architetto, senza partecipare alla simulazione.

## Confine di non-interferenza

- [OBS-001] L'Observer apre SQLite in modalità `mode=ro`; nessun endpoint può creare, modificare o eliminare eventi, snapshot mentali o stato materiale.
- [OBS-002] Ogni snapshot del log e delle menti viene letto dentro un'unica transazione SQLite coerente.
- [OBS-003] L'Observer non viene inserito nelle percezioni dei Newlander e non produce eventi canonici.
- [OBS-004] Pausa, selezione, navigazione temporale e replay futuri riguarderanno esclusivamente la proiezione visiva; il runtime agentico continuerà ad avanzare autonomamente.
- [OBS-005] La UI ricostruisce la propria rappresentazione da snapshot ed eventi; animazioni o testi di presentazione non diventano mai stato canonico.

## Confine di riservatezza

- [SEC-001] La Console dell'Architetto è una superficie privilegiata: snapshot e stream includono anche menti ed eventi privati.
- [SEC-002] Il server ascolta per default soltanto su `127.0.0.1:8765`.
- [SEC-003] CORS autorizza esclusivamente origini HTTP(S) loopback (`localhost`, `127.0.0.1`, `::1`); una pagina web esterna non può leggere la risposta.
- [SEC-004] Esporre esplicitamente `--host 0.0.0.0` rende dati mentali privati raggiungibili dalla rete locale e richiederà un livello di autenticazione prima di un uso non sperimentale.

## Avvio

```bash
uv run newland --db data/newland.db serve

# Porta alternativa, sempre locale
uv run newland --db data/newland.db serve --port 9000
```

## Endpoint

### `GET /api/health`

Conferma che il database è leggibile e restituisce l'ultima sequenza canonica.

```json
{"last_sequence": 42, "status": "ok"}
```

### `GET /api/snapshot`

Restituisce una proiezione puntuale composta da:

- [SNP-001] `schema_version`, `observer_scope` e `last_sequence`;
- [SNP-002] `world`: tempo, grafo dei luoghi, corpi, risorse, attività, nodi di risonanza, famiglie, cooperazioni e dispute;
- [SNP-003] `minds`: snapshot privati completi indicizzati per `agent_id`.

`last_sequence` è il cursore da passare allo stream dopo aver materializzato lo snapshot, evitando una finestra persa fra bootstrap e aggiornamenti live.

Con `GET /api/snapshot?at_sequence=N` il server esegue il replay materiale fino alla sequenza richiesta. La risposta aggiunge `latest_sequence` e `is_live`, consentendo alla UI di mostrare contemporaneamente il punto osservato e la testa corrente. Gli snapshot mentali storici vengono restituiti vuoti: non sono ricostruibili dal solo log materiale e non vengono inventati.

### `GET /api/events?after_sequence=N&limit=L`

Restituisce fino a `L` eventi con `sequence > N`, ordinati per sequenza. Il limite ammesso è `1..5000`; il default è `500`.

- [EVT-001] L'envelope contiene `event_id`, `sequence`, `schema_version`, `world_tick`, `world_time`, `event_type`, `actor_ids`, `location`, `payload`, `visibility`, `recipient_ids` e `causation_id`.
- [EVT-002] Il payload viene trasmesso senza reinterpretazione narrativa.
- [EVT-003] Eventi privati e locali conservano visibilità e destinatari originali.

### `GET /api/stream?after_sequence=N`

Mantiene uno stream Server-Sent Events unidirezionale. Ogni blocco usa:

```text
id: 43
event: newland-event
data: {"sequence":43,"event_type":"AgentMoved",...}
```

- [SSE-001] `id` coincide con la sequenza canonica e abilita la ripresa senza buchi.
- [SSE-002] `event` usa il canale stabile `newland-event`; il tipo canonico rimane nel campo `event_type` dell'envelope, così nuovi tipi non richiedono nuovi listener browser.
- [SSE-003] `data` contiene l'intero envelope dell'evento.
- [SSE-004] Il server accetta sia `after_sequence` sia l'header standard `Last-Event-ID`, scegliendo il cursore più avanzato per evitare duplicazioni alla riconnessione.
- [SSE-005] In assenza di nuovi eventi vengono inviati heartbeat commentati, che non modificano lo stato dell'Observer.

### `GET /api/chronicle?after_sequence=N&limit=L`

Restituisce voci generate del Cronista da un archivio derivato separato. Ogni voce include prosa, range delle sequenze canoniche osservate, `source_event_ids`, modello, inference id, numero di tentativi e versione del prompt.

- [CHR-001] Una voce non è un evento del mondo e non compare nelle percezioni dei Newlander.
- [CHR-002] L'assenza o il fallimento del Cronista non rallenta e non modifica la simulazione.
- [CHR-003] Il testo viene prodotto in tempo reale da un modello generativo; il frontend non usa template narrativi.
- [CHR-004] Ogni passaggio richiede provenienza verso eventi canonici del batch e supera una revisione generativa di aderenza prima della persistenza.
- [CHR-005] L'archivio predefinito è `data/newland.chronicle.db`, distinto da `data/newland.db`.

### `GET /api/chronicle-stream?after_sequence=N`

Stream SSE delle nuove voci sul canale stabile `chronicle-entry`. Il suo cursore è indipendente dalla sequenza degli eventi canonici e supporta `Last-Event-ID`.

## Bootstrap del client

1. Richiedere `/api/snapshot`.
2. Materializzare mappa, pannelli e cursore da `last_sequence`.
3. Aprire `/api/stream?after_sequence=<last_sequence>`.
4. Applicare in ordine soltanto eventi con sequenza maggiore del cursore locale.
5. In caso di discontinuità o incompatibilità di schema, richiedere un nuovo snapshot.
6. Caricare `/api/chronicle` e aprire `/api/chronicle-stream` usando il cursore dell'ultima voce.

## Navigazione temporale

- [TIM-001] La pausa è soltanto una modalità dello store UI: gli stream restano aperti e `liveSequence` continua ad avanzare.
- [TIM-002] Scrub e replay richiedono snapshot canonici `at_sequence`; non ricostruiscono lo stato da frame o animazioni.
- [TIM-003] Il registro degli eventi e il Diario sono filtrati fino alla sequenza osservata.
- [TIM-004] Il replay visuale avanza una sequenza alla volta e non invia alcun comando al runtime.
- [TIM-005] `Torna al presente` sostituisce la proiezione storica con l'ultimo snapshot live già ricevuto e poi lo riallinea via HTTP.

## Verifica

- [TST-001] Snapshot e query incrementali conservano envelope, ordinamento e contenuti privati.
- [TST-002] Lo stream SSE riprende da query string o `Last-Event-ID`.
- [TST-003] Eventi e menti prima e dopo ogni lettura risultano identici.
- [TST-004] Origini loopback ricevono il consenso CORS; origini esterne no.
- [TST-005] Replay dello snapshot materiale deriva esclusivamente dal log persistito.
