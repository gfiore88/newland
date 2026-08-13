# ADR-0017: Visual Agent State System — Marker Distinzione e Animazione Movimento

**Data**: 2026-08-13  
**Stato**: Accettato  
**Autore**: Architetto (Newland Observer)

---

## Contesto

La mappa WebGL dell'Observer mostrare luoghi e agenti con lo stesso tipo di marker (cerchio), rendendo impossibile distinguere a colpo d'occhio:

- Un luogo geografico da un agente
- Un agente vivo da uno dormiente o morto
- Un agente che si sta muovendo da uno statico

Questo limita la leggibilità dell'Observer come strumento di analisi del mondo vivo.

---

## Forze in campo

- `[DRV-001]` L'Observer è uno strumento di osservazione scientifica: la mappa deve comunicare lo stato del mondo **senza richiedere lettura di testo**.
- `[DRV-002]` Il cambio di location di un agente tra due tick è un evento semanticamente importante (azione fisica nel mondo).
- `[DRV-003]` I luoghi sono entità **statiche e geografiche**; gli agenti sono entità **dinamiche e cognitive**. Devono avere forme diverse.
- `[DRV-004]` PixiJS gestisce il ticker a 30 FPS: possiamo eseguire animazioni lerp senza overhead significativo.

---

## Decisione

### [GOV-001] Distinzione visiva luoghi / agenti

I **luoghi** sono rappresentati con un **diamante rotato** (`◆`, un rettangolo 10×10 px ruotato di 45°), colore muschio, bordato. Questa forma trasmette "punto fisso del territorio" e non viene mai confusa con un agente.

Gli **agenti** mantengono la forma circolare, ma con layer visivi che ne comunicano lo stato.

### [GOV-002] Stato cromatico degli agenti sulla mappa

| Stato | Colore corpo | Indicatore aggiuntivo |
| ------- | ------------- | ---------------------- |
| Vivo / attivo | `#eae7da` (pergamena) con glow muschio | Ring doppio |
| A riposo / dormiente | `#5a6055` (grigio-verde scuro) | Glyph `💤` animato (bob sinusoidale) |
| Critico (energia < 10%) | `#c88168` (terra) | Glow arancione pulsante |
| Inattivo / morto | `#3a2a2a` (grigio rosso scuro) | `✕` interno, alpha 0.5 |

### [GOV-003] Animazione movimento

Quando `agent.location` cambia tra due render consecutivi:

- `[POS-001]` Registriamo la posizione precedente (`prevPos`) e quella attuale (`currPos`)
- `[POS-002]` Il ticker lerpa linearmente da `prevPos` a `currPos` in 600ms (`t: 0 → 1`)
- `[POS-003]` Durante il lerp, 3 ghost dots sfumati (alpha: 0.35, 0.2, 0.08) sono disegnati lungo la traiettoria precedente per indicare la direzione di provenienza
- `[POS-004]` Il ghost trail è **visibile per un solo ciclo render** (un solo cambio di location). Non si accumula nel replay.

### [GOV-004] Status badge nella UI

Nella lista presenze e nell'inspector, i badge di stato usano emoji + label e seguono la stessa logica cromatica:

| Condizione (priorità decrescente) | Badge |
| ---------------------------------- | ------- |
| `active === false` | `💀 morto` |
| `energy < 0.1` | `⚡ critico` |
| `current_action` contiene `"rest"` o `"sleep"` | `💤 dormiente` |
| `current_action` contiene `"move"` o `"travel"` | `🚶 in cammino` |
| default | nessun badge |

---

## Conseguenze

### Positive

- La mappa diventa un pannello di controllo leggibile senza testo aggiuntivo
- L'animazione del movimento rende tangibile il concetto di "agente che si sposta nel mondo fisico"
- La distinzione forma/colore migliora l'accessibilità cognitiva dell'Observer

### Negative / Trade-off

- `[RISK-001]` L'animazione lerp richiede che `map-scene.ts` mantenga stato tra render (posizioni precedenti). Questo introduce un piccolo accoppiamento temporale.
- `[RISK-002]` Se due agenti si trovano nella stessa location, i ghost trail si sovrappongono. Accettabile: è raro e comunica correttamente che entrambi sono in movimento.

---

## Riferimenti

- `ui/src/map-scene.ts` — implementazione PixiJS
- `ui/src/main.ts` — renderInhabitants, renderInspector
- ADR-0014: Observer UI Architecture and Aesthetics
- ADR-0015: Procedural Biome Rendering Engine
