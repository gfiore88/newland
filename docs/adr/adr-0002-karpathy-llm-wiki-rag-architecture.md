---
id: adr-0002
title: "Karpathy LLM-Wiki Pattern for RAG Knowledge Management"
status: "Accepted"
date: "2026-08-12"
authors: ["Agent AI", "Giovanni Fiore"]
tags: ["rag", "wiki", "karpathy", "knowledge-management", "adr"]
---

# ADR-0002: Karpathy LLM-Wiki Pattern for RAG Knowledge Management

## Context & Problem Statement
As the **Newland** project grows, we will ingest numerous raw sources (philosophical texts, physical parameters, environmental models, jurisprudence notes, and architectural specifications). 

Relying on traditional ad-hoc RAG—which re-reads and re-derives context from raw documents on every query—causes high latency, token waste, and fragmented reasoning. We require a persistent, compounding knowledge architecture based on Andrej Karpathy's LLM-Wiki pattern.

## Decision Drivers
- [DRV-001] **Compounding Knowledge**: Raw sources must be ingested once and synthesized into a persistent, interlinked wiki.
- [DRV-002] **Reduced Query Cost & Latency**: LLMs should query compiled, structured markdown pages rather than searching through noisy raw documents.
- [DRV-003] **Contradiction & Health Management**: The knowledge base must track cross-references, detect stale claims, and flag contradictions.
- [DRV-004] **Traceability**: All wiki entries must trace back to raw sources in `docs/raw/` and append chronological logs in `docs/log.md`.

## Considered Alternatives

### Alternative 1: Ad-Hoc Vector RAG over Raw Documents
- **Description**: Storing raw text/PDF files and running vector embeddings/search on every query without compiling a wiki.
- **Rejection Rationale**: [REJ-001] Fails to synthesize cross-document connections; re-derives knowledge on every query; lacks explicit entity/concept cross-linking.

### Alternative 2: Manual Human-Maintained Wiki
- **Description**: Relying on humans to manually write and maintain all wiki pages.
- **Rejection Rationale**: [REJ-002] High human maintenance burden leads to stale links and incomplete bookkeeping as raw sources accumulate.

### Alternative 3: Karpathy LLM-Wiki Pattern under `docs/`
- **Description**: Storing raw sources in `docs/raw/`, having the LLM incrementally compile and maintain a structured markdown wiki in `docs/wiki/` (with `index.md`, `log.md`, entity/concept pages), and enforcing linting/ingest workflows.
- **Rejection Rationale**: N/A (Selected Option).

## Decision Outcome
Chosen Option: **Alternative 3 (Karpathy LLM-Wiki Pattern under `docs/`)**.

### Detailed Decision Points

- [WKI-001] **Three-Tier `docs/` Knowledge Hierarchy**:
  - `docs/raw/`: Immutable raw source materials.
  - `docs/wiki/`: Interlinked markdown pages compiled and maintained by the LLM (Entities, Concepts, Systems, Synthesis).
  - `docs/wiki-schema.md`: Operational directives for Ingest, Query, and Lint workflows.
- [ING-001] **Incremental Ingest Workflow**:
  - Upon adding a file to `docs/raw/`, the LLM extracts key entities/concepts, creates a source summary in `docs/wiki/sources/`, updates relevant entity pages in `docs/wiki/entities/`, updates `docs/index.md`, and appends an entry to `docs/log.md`.
- [QRY-001] **Query & Synthesis Persistence**:
  - Queries read compiled wiki pages via `docs/index.md`. Valuable answers, trade-off analyses, or new connections are saved back into `docs/wiki/synthesis/` as persistent knowledge.
- [LNT-001] **Periodic Wiki Linting**:
  - The LLM runs health checks to identify orphan pages, missing cross-links, obsolete claims, and data gaps.
- [LOG-001] **Chronological Activity Log**:
  - All ingests, queries, and lint passes are recorded in `docs/log.md` with unix-parseable headers (`## [YYYY-MM-DD] ingest | Title`).

## Consequences

### Positive Consequences
- [POS-001] **Compounding Knowledge Base**: Information becomes richer over time; cross-references are pre-computed.
- [POS-002] **Deterministic Navigation**: `docs/index.md` and `docs/log.md` provide clear entry points for both humans and AI agents.
- [POS-003] **Zero-Cost Bookkeeping**: The LLM handles cross-linking and summary updates automatically.

### Negative Consequences & Risks
- [NEG-001] **Ingest Overhead**: Ingesting a raw file touches multiple wiki pages. - **Mitigation**: Automated via script/skill workflows and verified during lint passes.

## Compliance & RAG Impact
- [CMP-001] **RAG Index Updated**: [docs/README.md](file:///Users/giovannifiore/Desktop/newland/docs/README.md)
- [CMP-002] **Wiki Schema Created**: [docs/wiki-schema.md](file:///Users/giovannifiore/Desktop/newland/docs/wiki-schema.md)
- [CMP-003] **Directives Updated**: [AGENTS.md](file:///Users/giovannifiore/Desktop/newland/AGENTS.md) and [.agents/AGENTS.md](file:///Users/giovannifiore/Desktop/newland/.agents/AGENTS.md)
