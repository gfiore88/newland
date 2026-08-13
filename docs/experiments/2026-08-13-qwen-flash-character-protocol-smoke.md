# Qwen Flash Character — protocol smoke test (2026-08-13)

## Scope

Verifica offline e non canonica del percorso Alibaba Model Studio definito da
ADR-0018. Il test usa un unico fixture fittizio e stateless; non legge il
database di Newland e non scrive eventi, memorie o cronache.

## Configuration

- Model: `qwen-flash-character`
- Region: Singapore / International
- API mode: OpenAI-compatible chat completions
- Response mode: `json_object`, con lo schema cognitivo canonico nel prompt
- Maximum output reservation: 2,048 token per richiesta
- Local model cap: 250,000 token
- Generative repair limit: 1
- Remote session cache: disabled

## Observations

1. La connessione e l'autenticazione hanno funzionato.
2. Il primo payload con `json_schema` non ha prodotto la struttura annidata
   richiesta dal contratto.
3. Con `json_object` e schema canonico esplicito, il modello ha prodotto JSON
   strutturalmente valido, ma il primo fixture senza osservazioni ha mostrato
   provenienze mentali inventate.
4. Aggiungendo al fixture un evento corporeo fittizio osservabile, la risposta
   ha attraversato al primo tentativo parser e validatore canonici.
5. L'intenzione finale è stata generata dal modello (`rest`); non è stata
   selezionata o sostituita da un fallback statico.

## Successful Run Metrics

- Requests: 1
- Prompt tokens: 3,350
- Completion tokens: 494
- Reasoning tokens exposed: 0
- Total tokens: 3,844
- Wall time: 4.44 seconds
- Canonical writes: 0

Due dry-run precedenti, volutamente falliti, hanno consumato rispettivamente
3,186 e 7,390 token. Il consumo osservato complessivo di questa sessione di
compatibilità è quindi 14,420 token, oltre alla primissima risposta interrotta
prima della persistenza delle metriche. Il risultato non autorizza un benchmark
ampio né l'uso live del modello.

## Interpretation

`qwen-flash-character` è compatibile con il contratto soltanto quando lo schema
è esplicitato nel prompt e il grounding offre fonti osservabili utilizzabili.
La capacità di seguire il protocollo non dimostra ancora qualità cognitiva,
continuità personale o superiorità rispetto ai modelli locali. Il prossimo
passo ammesso dall'ADR è un corpus piccolo e sanitizzato con scoring dichiarato,
non l'integrazione nel runtime.
