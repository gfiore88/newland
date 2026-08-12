---
name: self-annealing
description: Skill per il perfezionamento continuo delle direttive e dei prompt degli agenti basato sulle evidenze d'esecuzione (Pattern Giovanni Fiore).
---

# Governed Agent Self-Annealing Skill

## Scopo
Consentire agli agenti di apprendere dai propri errori metodologici incontrati durante un run, formulando **Proposte di Annealing** trasparenti e minimali che vengono sottoposte a revisione ed approvazione umana prima di essere applicate alle direttive (`AGENTS.md` o `skills/`).

## Fasi del Workflow

```
[Ostacolo nel Run] -> [Recovery Immediato] -> [Completamento Task] -> [Post-Run Retrospective] -> [Proposta Annealing] -> [Approvazione Umana] -> [Git Versioning]
```

### 1. Classificazione del Problema
Decidere la destinazione corretta dell'apprendimento:
- *Fatto o dato di dominio mancante* -> Aggiornare `docs/` (RAG Knowledge Base).
- *Nuova decisione o cambio architetturale* -> Creare un ADR in `docs/adr/`.
- *Metodo operativo dell'agente debole o ambiguo* -> Proposta di Annealing su `AGENTS.md` o `SKILL.md`.
- *Bug nel codice* -> Fix nel codice di produzione + test.

### 2. Struttura della Proposta di Annealing
```markdown
## Annealing Proposal

**Run evidence**: [Quali errori, retry o passaggi ridondanti sono emersi nel run?]
**Root cause**: [Perché la direttiva attuale ha consentito questo comportamento inefficiente?]
**Classification**: [Method / Knowledge / Decision / Bug]
**Target**: [File della direttiva interessato, es. AGENTS.md]
**Minimal diff**:
```diff
- vecchia direttiva
+ nuova direttiva perfezionata
```
**Expected effect**: [Quale miglioramento ci si aspetta nei run futuri?]
```

### 3. Governance Umana Inviolabile
- **L'agente propone, l'utente approva.**
- Nessuna modifica permanente ai file di istruzioni viene applicata senza la conferma esplicita dell'utente.
