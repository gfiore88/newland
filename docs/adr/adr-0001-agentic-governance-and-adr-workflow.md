---
id: adr-0001
title: "Agentic Governance, Mandatory ADR Workflow, RAG Knowledge Base Location, and Governed Self-Annealing"
status: "Accepted"
date: "2026-08-12"
authors: ["Agent AI", "Giovanni Fiore"]
tags: ["governance", "adr", "rag", "self-annealing", "awesome-copilot"]
---

# ADR-0001: Agentic Governance, Mandatory ADR Workflow, RAG Knowledge Base Location, and Governed Self-Annealing

## Context & Problem Statement
The **Newland** project is a vast, long-term endeavor to conceptualize, formalize, and simulate a pristine parallel universe (physical matrix, natural laws, governance, and simulation engine). 

Without strict governance, AI agents risk taking arbitrary implementation shortcuts, bypassing architecture research, producing fragmented documentation, and repeating operating errors. We require a formal governance framework based on Michael Nygard's ADR laws, Awesome Copilot skill standards, Addy Osmani Agent Skills, and Giovanni Fiore's Governed Agent Self-Annealing pattern.

## Decision Drivers
- [DRV-001] **Traceability & Auditability**: Every technical or methodological decision must be recorded before execution.
- [DRV-002] **RAG Knowledge Centralization**: All project knowledge and context must reside exclusively under `docs/`.
- [DRV-003] **Standardized Agent Skills**: Skill definitions must follow `addyosmani/agent-skills` format and `github/awesome-copilot` patterns.
- [DRV-004] **Self-Improving Agent Directive**: Agents must learn from execution friction via human-gated prompt self-annealing.

## Considered Alternatives

### Alternative 1: Informal Ad-Hoc Execution (No ADRs)
- **Description**: Proceeding with code and world simulation without formal decision records.
- **Rejection Rationale**: [REJ-001] High risk of architectural drift, undocumented assumptions, and recurring agent errors.

### Alternative 2: Nygard-Based Mandatory ADR Workflow with Awesome Copilot & Self-Annealing
- **Description**: Requiring an approved Nygard ADR under `docs/adr/adr-NNNN-[title-slug].md` before any task begins, centralizing RAG in `docs/`, using Addy Osmani skill structures, and implementing Giovanni Fiore's human-gated self-annealing loop.
- **Rejection Rationale**: N/A (Selected Option).

## Decision Outcome
Chosen Option: **Alternative 2 (Nygard-Based Mandatory ADR Workflow & Governed Agentic Architecture)**.

### Detailed Decision Points

- [GOV-001] **Mandatory ADR Prior to Execution**: NO task shall be launched or executed without an approved ADR saved in `docs/adr/adr-NNNN-[title-slug].md`.
- [GOV-002] **Awesome Copilot ADR Skill Compliance**: All ADRs must be authored using the `create-architectural-decision-record` skill, adhering to Michael Nygard's laws, YAML front matter, coded bullet points (e.g., `[GOV-001]`), and balanced consequences.
- [RAG-001] **Centralized Knowledge Location**: All project RAG documentation, specifications, and architecture records must reside under `docs/` in the root of the project.
- [SKL-001] **Addy Osmani Agent Skills Format**: Skills must be stored in `skills/<skill_name>/SKILL.md` with YAML frontmatter and markdown instructions.
- [SEL-001] **Governed Agent Self-Annealing (Giovanni Fiore Pattern)**: When an agent encounters a reusable method friction during a run, it shall formulate an `Annealing Proposal` diff. Persistent updates to `AGENTS.md` or skills require explicit human approval.

## Consequences

### Positive Consequences
- [POS-001] **Zero Architectural Ambiguity**: Every decision is justified, diffable, and tracked in Git.
- [POS-002] **AI Machine Readability**: Coded bullet points allow AI agents to deterministically parse and cross-reference rules.
- [POS-003] **Continuous Agent Improvement**: Cross-run annealing reduces step counts, retries, and token spend over time.

### Negative Consequences & Risks
- [NEG-001] **Initial Overhead**: Requires drafting an ADR before initiating new technical tasks. - **Mitigation**: Automated via `skills/create-architectural-decision-record/SKILL.md`.

## Compliance & RAG Impact
- [CMP-001] **RAG Index Updated**: [docs/README.md](file:///Users/giovannifiore/.gemini/antigravity-ide/scratch/newland/docs/README.md)
- [CMP-002] **Directives Updated**: [AGENTS.md](file:///Users/giovannifiore/.gemini/antigravity-ide/scratch/newland/AGENTS.md) and [.agents/AGENTS.md](file:///Users/giovannifiore/.gemini/antigravity-ide/scratch/newland/.agents/AGENTS.md)
