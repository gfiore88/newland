---
id: adr-0004
title: "Fully Autonomous Character Auto-Annealing & Self-Evolving World Engine"
status: "Accepted"
date: "2026-08-12"
authors: ["Agent AI", "Giovanni Fiore"]
tags: ["auto-annealing", "character-evolution", "simulation", "adr", "autonomous-agent"]
---

# ADR-0004: Fully Autonomous Character Auto-Annealing & Self-Evolving World Engine

## Context & Problem Statement
In the **Newland** living world engine, multi-agent inhabitants evolve psychologically, emotionally, and epistemologically over time. 

While core system directives (`AGENTS.md`, ADRs) require human governance to preserve project architecture, forcing human approval for every internal character personality shift (e.g., healing a psychological flaw, experiencing a flashback, or shifting from Custodian to Seeker) would halt the continuous, autonomous flow of the simulation. We require a fully automated **Character Auto-Annealing** system where inhabitants mutate and evolve their own `.agent.md` files autonomously.

## Decision Drivers
- [DRV-001] **Uninterrupted Autonomous Life**: The living world simulator must run and evolve continuously without blocking for human review on every individual character mindset update.
- [DRV-002] **Emergent Character Arc**: Inhabitants must autonomously adapt to events (traumas, flashbacks, conflict resolutions, new arrivals) and record their evolution in Git.
- [DRV-003] **Clear Scope Boundary**: Differentiating human-gated system policy changes from fully automated character state mutations.

## Considered Alternatives

### Alternative 1: Human-Gated Approval for Every Character Shift
- **Description**: Requiring human approval via Gist annealing proposals for every single character personality update.
- **Rejection Rationale**: [REJ-001] Destroys the continuous, self-living nature of the simulation engine; creates massive friction for multi-agent evolution.

### Alternative 2: Ephemeral Character Memory (No File Persistence)
- **Description**: Keeping character personality shifts in volatile chat memory without updating `.agent.md` files.
- **Rejection Rationale**: [REJ-002] Memory is lost across simulation sessions; prevents auditability and Karpathy LLM-Wiki RAG indexing.

### Alternative 3: Fully Autonomous Character Auto-Annealing
- **Description**: Allowing character agents to autonomously modify their own `.agent.md` files (bumping `annealing_version`, updating `path_choice`, logging evolutionary milestones) while keeping system directives (`AGENTS.md`, ADRs) human-governed.
- **Rejection Rationale**: N/A (Selected Option).

## Decision Outcome
Chosen Option: **Alternative 3 (Fully Autonomous Character Auto-Annealing)**.

### Detailed Decision Points

- [AUT-001] **Fully Autonomous Character Auto-Annealing**:
  - Inhabitant character profiles (`character-[nome-cognome-slug].agent.md`) shall update automatically upon experiencing in-world events without human intervention.
  - The character agent automatically applies state diffs, increments `annealing_version` (e.g., `v1.0` -> `v1.1`), and records evolutionary logs.
- [AUT-002] **Self-Evolving World Engine**:
  - The simulation lives, updates, and evolves on its own. As characters heal gaps, experience flashbacks, or change roles, their Markdown files self-mutate and commit to Git.
- [GOV-001] **System Directive Distinction**:
  - System-level directives (`AGENTS.md`, `skills/`, ADRs) remain human-governed under the original Gist pattern. Character state files are 100% autonomous.

## Consequences

### Positive Consequences
- [POS-001] **True Self-Living Simulation**: The world of Newland lives, evolves, and updates its inhabitants autonomously 24/7.
- [POS-002] **Persistent History**: Character growth is preserved on disk and Git without requiring manual bookkeeping.
- [POS-003] **Emergent Storytelling**: Character arcs develop organically in response to planetary events.

### Negative Consequences & Risks
- [NEG-001] **Risk of Drift**: A character might mutate into contradictory behavior. - **Mitigation**: Automated linting checks via `skills/llm-wiki-maintainer/SKILL.md` to ensure internal narrative consistency.

## Compliance & RAG Impact
- [CMP-001] **RAG Index Updated**: [docs/README.md](file:///Users/giovannifiore/Desktop/newland/docs/README.md)
- [CMP-002] **Character Skill Created**: [skills/character-auto-annealing/SKILL.md](file:///Users/giovannifiore/Desktop/newland/skills/character-auto-annealing/SKILL.md)
- [CMP-003] **Directives Updated**: [AGENTS.md](file:///Users/giovannifiore/Desktop/newland/AGENTS.md) and [.agents/AGENTS.md](file:///Users/giovannifiore/Desktop/newland/.agents/AGENTS.md)
