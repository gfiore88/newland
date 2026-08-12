---
id: adr-0012
title: "Cognitive Stalemate Resolution for Small LLMs"
status: "Proposed"
date: "2026-08-12"
authors: ["Agent AI", "Giovanni Fiore"]
tags: ["cognition", "prompting", "bugfix"]
---

# ADR-0012: Cognitive Stalemate Resolution for Small LLMs

## Context & Problem Statement
L'agente John è bloccato da molti tick di simulazione con energia a `0.0`. Il World Adjudicator rifiuta sistematicamente l'azione `perform_activity` (es. `esaminare_edifici`) per mancanza di energia, come da contratti di sistema. Tuttavia, i modelli Small LLM (es. Qwen 2.5:3b) tendono ad allucinare che un'azione energivora possa risolvere la crisi di fame/sete/energia ("ricercare cibo in fretta"), finendo in un loop infinito. Inoltre, l'agente continua a generare cloni esatti della stessa riflessione ("Ho bisogno di dedicare più tempo allo sviluppo del ruolo..."), saturando la memoria cognitiva senza compiere alcun progresso logico.

## Decision Drivers
- [DRV-001] Prevenire il deadlock cognitivo degli agenti con energia esaurita.
- [DRV-002] Evitare la saturazione della memoria con riflessioni duplicate.
- [DRV-003] Rispettare rigorosamente l'ADR-0008 (Zero Static Agent Decisions): il sistema non deve forzare un'azione `rest` statica nel codice, ma deve portare il LLM a sceglierla consapevolmente.

## Considered Alternatives

### Alternative 1: Fallback statico nel codice (Hardcoded Rest)
- **Description**: Modificare l'engine per sostituire forzatamente l'azione dell'agente con `rest` quando l'energia è `0.0`.
- **Rejection Rationale**: [REJ-001] Violazione diretta dell'ADR-0008. L'azione deve essere sempre scelta generativamente dal modello.

### Alternative 2: Espansione dei Guardrail di Prompting (Cognition Prompt)
- **Description**: Modificare il system prompt in `engine/newland_engine/cognition.py` per esplicitare chiaramente l'impossibilità fisica di eseguire azioni non-rest a energia 0.0, e aggiungere un vincolo stringente contro la copia pedissequa di riflessioni passate.
- **Rejection Rationale**: N/A - Opzione selezionata.

## Decision Outcome
Chosen Option: **Alternative 2: Espansione dei Guardrail di Prompting**

### Detailed Decision Points
- [DEC-001] **Strict Energy Guardrail**: Aggiornare il prompt in `cognition.py` per istruire il modello che a energia `0.0` *qualsiasi* azione tranne `rest` (o `consume` se il cibo è già in inventario) fallirà miseramente.
- [DEC-002] **Anti-Repetition Guardrail**: Aggiungere un vincolo al prompt cognitivo per impedire la generazione di `reflections` identiche a quelle già presenti nella memoria episodica dell'agente.

## Consequences

### Positive Consequences
- [POS-001] Gli agenti esausti si fermeranno per riposare (`rest`), recuperando energia e sbloccando il loop.
- [POS-002] La memoria dell'agente rimarrà pulita e le riflessioni evolveranno logicamente nel tempo anziché impantanarsi.

### Negative Consequences & Risks
- [NEG-001] L'aggiunta di nuove direttive allunga il system prompt, consumando marginalmente più context window per i modelli Small LLM.
  - **Mitigation**: Scrivere le nuove regole in modo estremamente conciso e perentorio.

## Compliance & RAG Impact
- [CMP-001] **RAG Files Updated**: `docs/adr/adr-0012-cognitive-stalemate-resolution.md`, `docs/README.md`.
- [CMP-002] **Directives Updated**: Modifica al prompt in `engine/newland_engine/cognition.py`.
