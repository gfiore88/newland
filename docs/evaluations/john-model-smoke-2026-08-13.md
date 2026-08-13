# Valutazione cognitiva sul secondo incidente John — 2026-08-13

> Stato: smoke test comparativo non canonico. Nessuna scrittura è stata eseguita nel mondo.

## Contesto

Il replay usa il database `data/newland.db` dopo l'arresto del runtime al tick 82. I checkpoint sono le sequence 7, 34, 44, 75 e 85 previste da ADR-0016; nel registro corrente gli ultimi due ricostruiscono lo stesso stato disponibile al tick 82. Ogni configurazione ha ricevuto lo stesso prompt `agent-cognition-v4`, schema, temperatura e contesto di 8192 token.

Questo è uno smoke test con un campione per checkpoint, sufficiente a eliminare configurazioni chiaramente incompatibili ma non a promuovere da solo un nuovo default.

## Risultati agente

| Configurazione | JSON/schema | Azioni materialmente fattibili | Cause critiche riconosciute | Tempo medio |
|---|---:|---:|---:|---:|
| `qwen2.5:3b`, think off | 5/5 | 0/5 | 0/4 | 13.25 s |
| `qwen3:4b`, think off | 5/5 | 1/5 | 0/4 | 20.69 s |
| `phi4-mini-reasoning`, think off | 5/5 | 1/5 | 2/4 | 20.26 s |
| `phi4-mini-reasoning`, think on | 0/5 | 0/5 | 0/4 | n/d |
| `qwen3:8b`, think off | 5/5 | 2/5 | 0/4 | 30.00 s |

La fattibilità è stata verificata contro lo stato ricostruito e gli stessi vincoli del `WorldAdjudicator`: inventario vuoto, nessuna risorsa nella cittadina, destinazioni adiacenti `bosco_est` e `campo_nord`, attività locale soggetta a competenza minima.

### Osservazioni

- `qwen2.5:3b` ha inventato risorse in tutti i checkpoint; nei due stati finali ha proposto `consume resource_1234` con inventario vuoto.
- `qwen3:4b` ha prodotto una sola azione fattibile: movimento verso `bosco_est`.
- Phi senza reasoning ha riconosciuto più spesso fame e sete, ma ha mescolato italiano, inglese e caratteri estranei e ha continuato a inventare consumabili.
- Phi con `think=true` e output strutturato è stato respinto da Ollama con HTTP 400 in tutti i casi; questa configurazione non è integrabile con l'adapter corrente.
- `qwen3:8b` è stato il candidato migliore: negli ultimi due checkpoint critici ha scelto autonomamente un movimento valido verso `bosco_est`. Nei primi tre ha comunque proposto due attività non compatibili con le skill e un consumo impossibile.

## Prova del Cronista leggero

È stata eseguita una generazione reale e isolata con `qwen3:4b`, database derivato temporaneo, batch 12 e nessuna scrittura canonica.

Esito: `chronicle_deferred`, zero voci persistite. Il modello ha prima citato `eco_della_sorgente` come se fosse un event ID; i tentativi successivi sono stati respinti dal controllo generativo di grounding. Il revisore ha anche classificato come non sostenute alcune frasi direttamente presenti negli eventi e si è contraddetto sulla frase relativa ai 30 kg di bacche. La richiesta ha richiesto più di un minuto prima del differimento.

`qwen3:4b` non è quindi approvabile come Cronista corrente soltanto sulla base della minore dimensione. I retry annullerebbero parte del vantaggio prestazionale e continuerebbero a occupare la singola inferenza condivisa.

## Decisione proposta

- Non promuovere nessuno dei modelli testati a default definitivo.
- Considerare `qwen3:8b` soltanto per una ripresa provvisoria e sorvegliata della mente di John, perché è l'unico ad aver prodotto coerentemente un'azione fattibile nei due snapshot finali.
- Non assegnare per ora `qwen3:4b` al Cronista.
- Prima di riattivare il Cronista nel percorso condiviso, proporre una revisione di ADR-0009 che consenta di cancellare in sicurezza una generazione narrativa derivata quando una mente entra in coda, senza interrompere transazioni canoniche.
- Qualificare successivamente candidati più capaci sui soli checkpoint critici con più campioni prima di cambiare il default permanente.

## Artefatti

- `john-cognition-smoke-2026-08-13.json`: Qwen 2.5 3B, Qwen 3 4B, Phi con reasoning off/on.
- `john-cognition-smoke-qwen3-8b-2026-08-13.json`: Qwen 3 8B.
