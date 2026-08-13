# Qwen Flash Character — canary cognition live (2026-08-13)

## Scope

Verifica canonica finita del percorso live Alibaba Model Studio definito da
ADR-0019. Ogni esecuzione ha usato il mondo persistente reale, un solo agente
registrato (John Flower), una sola attivazione e arresto automatico fra
transazioni complete. Il Cronista è rimasto locale.

## Configuration

- Model spec: `dashscope:qwen-flash-character`
- Modalità: `newland live --max-activations 1`
- Opt-in: `--allow-cloud-live`
- Cap locale cumulativo: 100.000 token
- Ledger non canonico: `data/newland.cloud-runtime.db`
- Generative repair limit: 1
- Remote session cache: disabled
- Static action fallback: absent

## Contract hardening

Quattro attivazioni iniziali sono state differite integralmente, senza azioni
materiali, perché il risultato non superava il contratto canonico:

1. `source_ids` improprio in una `MemoryAppraisal`;
2. intenzione `consume` priva del `resource_id` trasportato dall'agente;
3. provenienza mentale mancante e metadato di retrieval `occurrence_count`;
4. provenienza mentale mancante e metadato estraneo `status` in una revisione
   di piano.

Le correzioni hanno chiarito grounding e provenienza nel prompt e reso il
confine di parsing tollerante ai soli metadati estranei. Non selezionano,
riscrivono o sostituiscono l'intenzione generata. Campi semantici, sorgenti e
vincoli materiali continuano a essere validati normalmente.

## Successful canonical activation

La quinta attivazione ha superato parser e validatore al primo tentativo:

- inference ID: `6162f628-92c2-4c9e-a1ef-a727aa84665e`
- `MemoryEncoded`: sequenze 62–63
- aggiornamenti mentali generativi: sequenze 64–70
- `ActionProposed`: sequenza 71
- azione scelta: `rest`, durata 30 minuti
- `ActionAccepted`: sequenza 72
- `ActionStarted`: sequenza 73, completamento previsto al tick 85
- provider canonico: `dashscope`
- modello canonico: `qwen-flash-character`
- tentativi della risposta riuscita: 1

La motivazione persistita è stata generata dalla stessa inferenza insieme agli
aggiornamenti mentali. Il runtime ha soltanto verificato l'intenzione contro i
contratti materiali e l'ha arbitrata.

## Usage and privacy audit

- Chiamate DashScope contabilizzate: 9
- Token complessivi addebitati dal ledger: 57.579
- Prompt token: 47.140
- Completion token: 10.439
- Reasoning token: 0
- Ultima chiamata riuscita: 6.626 token
- Budget residuo sotto il cap locale: 42.421 token
- Credenziale: file `.env` ignorato da Git, permessi `0600`
- Chiave, authorization header, prompt e reasoning nell'evento 71: assenti

Il costo sperimentale include otto richieste dei quattro canary differiti. Il
dato conferma che anche Flash Character consuma circa 6–7 mila token per
richiesta con il contratto corrente: la modalità continua va quindi avviata
soltanto con monitoraggio del budget e fallback generativi esplicitamente
configurati.

## Outcome

Il criterio live di ADR-0019 è soddisfatto: una mente Alibaba selezionata
esplicitamente ha prodotto un `ActionProposed` canonico e autonomo nel mondo
reale, con provenienza verificabile e senza credenziali o chain-of-thought
persistiti. Il risultato prova il percorso operativo, non ancora la qualità
longitudinale delle decisioni né la sostenibilità di una simulazione lunga.
