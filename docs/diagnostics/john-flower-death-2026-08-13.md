# Incident Review: morte di John Flower

- [INC-001] **Data dell'analisi**: 2026-08-13.
- [INC-002] **Fonte canonica**: `data/newland.db`.
- [INC-003] **Agente**: John Flower (`nwl-736332`).
- [INC-004] **Modello cognitivo osservato**: `qwen2.5:3b`, prompt `agent-cognition-v4`, provider `ollama`.
- [INC-005] **Esito**: `AgentDied` alla sequence `88`, tick `246`, con ragione generica `starvation or dehydration`.

## Sintesi causale

John non ha formulato un'intenzione consapevole di rinunciare alla sopravvivenza. Il registro mostra un loop cognitivo auto-rinforzante: la prima scelta di riposare è stata reinterpretata come obiettivo di creare un ambiente confortevole; ogni nuovo riposo o cambiamento corporeo è poi diventato una memoria quasi identica, con salienza e confidenza massime; quelle memorie hanno dominato il contesto delle deliberazioni successive.

Il runtime ha accettato tutte le intenzioni perché `rest` era fisicamente valido. Il riposo ha ripristinato l'energia, ma non ha ridotto fame o sete. John non ha mai proposto `move`, `gather` o `consume`, e il contatore letale ha continuato ad accumularsi.

Questa morte dimostra una carenza sistemica di rappresentazione, memoria e temporizzazione. Non dimostra, da sola, che `qwen2.5:3b` sia incapace di sostenere Newland e non giustifica una sostituzione del modello senza una valutazione comparativa.

## Traccia canonica essenziale

| Sequence | Tick | Evento | Evidenza |
|---:|---:|---|---|
| 2 | 0 | `AgentRegistered` | energia `0.8`, fame `0.1`, sete `0.1`, inventario vuoto |
| 7 | 1 | `ActionProposed` | prima intenzione `rest`; la motivazione dichiara erroneamente energia minima |
| 20 | 41 | `NeedsChanged` | energia `0.8`, fame `0.715`, sete `0.92`; attraversata `thirst_high` |
| 29 | 61 | `NeedsChanged` | energia `0.8`, fame `1.0`, sete `1.0`; inizia la condizione materiale fatale |
| 74 | 166 | `AttentionScheduled` | John rinvia la successiva attenzione al tick `226`, dieci ore simulate dopo |
| 78 | 226 | `NeedsChanged` | energia `0.4`, fame `1.0`, sete `1.0`, salto di `60` tick |
| 85 | 226 | `ActionProposed` | decima intenzione `rest`, ancora motivata dal recupero di energia |
| 88 | 246 | `AgentDied` | morte per `starvation or dehydration` |
| 89 | 246 | `NeedsChanged` | energia `0.8`, fame `1.0`, sete `1.0` dopo il riposo |

## Evidenze quantitative

- [EVD-001] John ha prodotto `10` eventi `ActionProposed`; tutti avevano `action_type = rest`.
- [EVD-002] Il mondo ha prodotto `10` `ActionAccepted` e `10` `AgentRested`; non esistono `ActionRejected` in questa esecuzione.
- [EVD-003] Non esistono eventi `AgentMoved`, `ResourceGathered` o `ResourceConsumed` per John.
- [EVD-004] Esistono `12` eventi `MemoryEncoded`. Undici contengono la stessa sintesi, o una copia sostanzialmente identica, sull'ambiente confortevole e il recupero di energia.
- [EVD-005] Le memorie duplicate hanno `salience = 1.0` e `confidence = 1.0`; il retrieval per salienza e recenza le ha quindi riproposte insieme.
- [EVD-006] Il contatore interno ha raggiunto `205` tick perché la fisiologia aggiunge l'intero intervallo quando lo stato alla fine dell'intervallo è fatale. La permanenza osservabile fra il primo stato fatale al tick `61` e la morte al tick `246` è invece di `185` tick.
- [EVD-007] Un tick vale dieci minuti. La soglia implementata di oltre `200` tick equivale a oltre 33 ore e 20 minuti, non alle circa 20 ore dichiarate nella documentazione.

## Carenze dimostrate

- [DEF-001] **Semantica corporea insufficiente**: il contesto espone numeri grezzi per energia, fame e sete, senza esplicitare direzione, gravità, trend o causa del pericolo. Per fame e sete `1.0` è fatale, mentre per energia è fatale `0.0`; il modello deve dedurre due scale opposte.
- [DEF-002] **Prompt prescrittivo e incompleto**: il prompt impone `rest` quando l'energia è zero, ma non rappresenta con pari chiarezza la gravità di fame e sete. In questo modo privilegia una risposta specifica anziché presentare fedelmente il corpo alla mente.
- [DEF-003] **Contratto fisico incoerente**: il prompt afferma che a energia zero `move` e `gather` falliscono sempre, ma il `WorldAdjudicator` applica attualmente il controllo energetico soltanto a `perform_activity`.
- [DEF-004] **Eco mnemonica**: il divieto di duplicazione introdotto dall'ADR-0012 riguarda `reflections`, ma il loop osservato passa attraverso `memory_appraisals`. `AgentMind.remember()` deduplica l'evento sorgente e non il contenuto semantico.
- [DEF-005] **Agenda non somatica**: attraversare una soglia durante l'attivazione non sostituisce la vecchia ragione di attivazione. La mente può quindi vedere il cambiamento corporeo ma deliberare sotto una ragione ormai obsoleta.
- [DEF-006] **Salti temporali pericolosi**: `attention_schedule` può rinviare la prossima attivazione fino a 144 tick. Non esiste un interrupt corporeo periodico durante una condizione critica già attraversata.
- [DEF-007] **Durata scissa dal tempo**: `duration_minutes` produce immediatamente l'effetto materiale dell'azione, mentre il tempo effettivamente trascorso dipende separatamente dall'agenda generata.
- [DEF-008] **Esposizione letale non replayable**: `starvation_ticks` viene mutato nella memoria del processo ma non è contenuto in un evento riducibile; un riavvio può quindi ricostruire bisogni identici con una diversa distanza dalla morte.
- [DEF-009] **Causa di morte conflata**: energia esaurita, fame e sete alimentano un unico contatore e producono la stessa ragione generica, impedendo una diagnosi causale precisa.
- [DEF-010] **Conoscenza territoriale limitata**: alla partenza John vede le destinazioni adiacenti ma nessuna risorsa locale e nessuna conoscenza acquisita sulla posizione di acqua o cibo. Il sistema non deve renderlo onnisciente, ma deve distinguere chiaramente ciò che percepisce, ciò che ricorda e ciò che ignora.

## Query di verifica

```sql
SELECT event_type, count(*)
FROM events
WHERE actor_ids = '["nwl-736332"]'
GROUP BY event_type
ORDER BY count(*) DESC;
```

```sql
SELECT sequence, world_tick, event_type,
       json_extract(payload, '$.action_type') AS action,
       json_extract(payload, '$.current.energy') AS energy,
       json_extract(payload, '$.current.hunger') AS hunger,
       json_extract(payload, '$.current.thirst') AS thirst
FROM events
WHERE actor_ids = '["nwl-736332"]'
ORDER BY sequence;
```

## Interpretazione architetturale

- [ARC-001] Il motore deve continuare a determinare condizioni, conseguenze e impossibilità fisiche, senza scegliere la risposta dell'agente.
- [ARC-002] La mente deve ricevere una percezione corporea semanticamente coerente e temporalmente attendibile, non un comando comportamentale.
- [ARC-003] La memoria deve conservare la soggettività senza permettere che copie accidentali monopolizzino il contesto.
- [ARC-004] La qualificazione di un modello deve usare replay e scenari agentici di Newland; i benchmark generici di ragionamento non sono prova sufficiente.

