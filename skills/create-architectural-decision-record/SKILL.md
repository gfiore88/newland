---
name: create-architectural-decision-record
description: Create an Architectural Decision Record (ADR) document for AI-optimized decision documentation under Nygard rules.
---

# Create Architectural Decision Record (ADR)

Create an ADR document for `${input:DecisionTitle}` using structured formatting optimized for AI consumption and human readability, adhering strictly to Michael Nygard's ADR laws.

## Inputs
- **Context**: `${input:Context}`
- **Decision**: `${input:Decision}`
- **Alternatives**: `${input:Alternatives}`
- **Stakeholders**: `${input:Stakeholders}`

## Input Validation
If any required inputs are not provided or cannot be determined from context, prompt the user for missing details before proceeding.

## Requirements & Nygard Rules
1. **Naming Convention**: File MUST be saved in `docs/adr/` as `adr-NNNN-[title-slug].md` (e.g., `adr-0001-agentic-governance.md`).
2. **Front Matter**: Include YAML front matter with `id`, `title`, `status`, `date`, `authors`, and `tags`.
3. **Structured Coded Points**: Use coded bullet points (3-letter category prefix + 3-digit number, e.g. `[GOV-001]`, `[RAG-001]`) for multi-item sections for deterministic AI parsing.
4. **Active Voice**: Write decisions in active voice ("We will...").
5. **Alternatives & Rejection Rationale**: Every alternative considered must include explicit technical rejection reasons.
6. **Balanced Consequences**: Document both positive and negative consequences/risks with mitigation strategies.

## Standard ADR Template Structure

```markdown
---
id: adr-NNNN
title: "[Decision Title]"
status: "Proposed | Accepted | Rejected | Superseded"
date: "YYYY-MM-DD"
authors: ["Agent AI", "Giovanni Fiore"]
tags: ["governance", "architecture"]
---

# ADR-NNNN: [Decision Title]

## Context & Problem Statement
[Description of context, business/technical drivers, and constraints according to Nygard rules]

## Decision Drivers
- [DRV-001] [Driver 1]
- [DRV-002] [Driver 2]

## Considered Alternatives

### Alternative 1: [Name]
- **Description**: [Details]
- **Rejection Rationale**: [REJ-001] [Why this option was rejected]

### Alternative 2: [Name]
- **Description**: [Details]
- **Rejection Rationale**: [REJ-002] [Why this option was rejected]

## Decision Outcome
Chosen Option: **[Selected Option Name]**

### Detailed Decision Points
- [DEC-001] [Decision Point 1]
- [DEC-002] [Decision Point 2]

## Consequences

### Positive Consequences
- [POS-001] [Positive impact 1]
- [POS-002] [Positive impact 2]

### Negative Consequences & Risks
- [NEG-001] [Risk or cost 1] - **Mitigation**: [Mitigation strategy]
- [NEG-002] [Risk or cost 2] - **Mitigation**: [Mitigation strategy]

## Compliance & RAG Impact
- [CMP-001] **RAG Files Updated**: `docs/...`
- [CMP-002] **Directives Updated**: `AGENTS.md` / `skills/...`
```
