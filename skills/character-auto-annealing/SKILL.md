---
name: character-auto-annealing
description: Skill per l'auto-evoluzione completamente autonoma e senza intervento umano delle schede personaggio (.agent.md) in risposta agli eventi di simulazione in Newland.
---

# Character Auto-Annealing Skill (Fully Autonomous Character Evolution)

## Scopo
Consentire alle schede agentiche dei personaggi (`character-[nome-cognome-slug].agent.md`) di **evolversi, aggiornarsi e committarsi in modo 100% autonomo senza richiedere approvazione umana**, garantendo che il simulatore vivente di Newland evolva da solo in tempo reale.

## Differenziazione di Governance
- **Direttive di Sistema (`AGENTS.md`, ADR, Skill)** -> Governance Umana Obbligatoria (Pattern Gist originale).
- **Stato dei Personaggi (`.agent.md`)** -> **Auto-Annealing Autonomo (ADR-0004)**.

## Flusso Operativo Autonomo

```
[Evento di Simulazione] 
       │
       ▼
[Reazione Emotiva/Cognitiva del Personaggio] 
       │
       ▼
[Calcolo Auto-Diff (Stato, Lacune Colmate, Versione)] 
       │
       ▼
[Mutazione Automatica del file .agent.md] 
       │
       ▼
[Git Commit & Ingest Karpathy LLM-Wiki Log]
```

### 1. Inneschi di Mutazione Automatica
- Un flashback vissuto vicino a un Nodo di Risonanza.
- Una lacuna emotiva/psicologica colmata attraverso la vita rurale o la comunità.
- La risoluzione di un conflitto primordiale.
- Il passaggio psicologico da *Custode del Presente* a *Cercatore del Modo*.

### 2. Formato del Commit Autonomo
- Incremento automatico di `annealing_version` (es. `v1.0` -> `v1.1`).
- Aggiornamento della sezione `## 5. Registro di Evoluzione (Self-Annealing Log)`.
- Commit Git automatico: `feat(character): auto-annealing character-[nome-cognome] to v1.1`.
