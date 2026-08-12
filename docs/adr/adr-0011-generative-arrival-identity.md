---
id: adr-0011
title: "Generative Arrival Identity: Zero Static Profiles for Newlander Arrivals"
status: "Proposed"
date: "2026-08-12"
authors: ["Agent AI", "Giovanni Fiore"]
tags: ["arrivals", "cognition", "llm", "autonomy", "identity", "zero-static"]
---

# ADR-0011: Generative Arrival Identity — Zero Static Profiles for Newlander Arrivals

## Context & Problem Statement

The `arrive` CLI command and `DEFAULT_INITIAL_PROFILES` in `simulation.py` currently supply hardcoded values, temperament, goals, skills, and an identical arrival memory for every new inhabitant. This violates:

- **ADR-0008 [AUT-001]**: *"No Production Static Cognition"* — no hardcoded data may shape an inhabitant's identity or decisions in production.
- **ADR-0007 [MND-001]**: *"Persistent Mind Boundary"* — each inhabitant must own an isolated `AgentMind` containing its own identity, values, temperament, goals, and memories.
- **ADR-0007 [DRV-001]**: *"Individual Subjectivity"* — every inhabitant must have private beliefs, memories, emotions, and goals.
- **Raw Brainstorming 03**: The arrival memory is *"l'unica ed esplicita memoria"* preserved through the Primordial Amnesia — it must be personal and unique to each individual.
- **Raw Brainstorming 06**: The transition is a quotidian, gradual, individual experience (driving, walking, cycling) — never a copy-paste template.

### Current Violations

| Component | Violation |
|---|---|
| `DEFAULT_INITIAL_PROFILES` (simulation.py L36-69) | Hardcoded Elia Moretti, Amina Haddad with static values, temperament, goals, memories |
| CLI `arrive` defaults (cli.py L130-153) | Same static `values`, `temperament`, `goals`, `memory` for every inhabitant |
| `arrive.sh` / `newland.sh` | Only pass name — all identity is static fallback |

The consequence: every inhabitant arrives with identical personality traits and the same arrival memory, making the Chronicler write near-identical diary entries and destroying individual subjectivity.

## Decision Drivers
- [DRV-001] **ADR-0008 Compliance**: Zero static data in production agent identity formation.
- [DRV-002] **Individual Subjectivity**: Each arrival must have a unique, generative identity born from Ollama inference.
- [DRV-003] **Narrative Authenticity**: The arrival memory is the founding myth of each Newlander — it must be personal.
- [DRV-004] **User Simplicity**: The user provides only a name (and optionally language/sex); the system generates everything else.

## Considered Alternatives

### Alternative 1: Keep Static Defaults, Encourage Manual Override
- **Description**: Keep hardcoded defaults but expose CLI flags (`--values`, `--temperament`, `--memory`) for manual customization.
- **Rejection Rationale**: [REJ-001] This shifts the authoring burden to the human operator, violating ADR-0008's principle that no static cognition source — including a human typing CLI flags — should define an inhabitant's private psychological identity. The personality must emerge from the generative model.

### Alternative 2: Randomized Static Templates
- **Description**: Maintain a pool of pre-written profiles and randomly select one per arrival.
- **Rejection Rationale**: [REJ-002] The pool is finite and authored by the developer, making it a disguised static provider. It violates ADR-0008 [AUT-001] and cannot produce genuinely individual identities.

### Alternative 3: Generative Arrival Identity via Ollama
- **Description**: When `arrive` is called with only a name (and optionally language), invoke Ollama to generate the full `ArrivalProfile`: values, temperament, goals, skills, and a unique arrival memory. The LLM receives the universe context (Primordial Amnesia, Invisible Transition, Initial Settlement) and the inhabitant's name/language, and produces a complete, private, individual identity.
- **Rejection Rationale**: N/A (Selected Option).

## Decision Outcome
Chosen Option: **Alternative 3 (Generative Arrival Identity via Ollama)**.

### Detailed Decision Points

- [GEN-001] **Generative Profile Factory**: A new `GenerativeArrivalFactory` class will invoke Ollama to produce a complete `ArrivalProfile` from minimal seed data (name, native language). The prompt will include Newland universe rules (Primordial Amnesia, Invisible Transition) as context.
- [GEN-002] **Arrival Memory Is Sacred**: The `arrival_memory` field represents the sole memory surviving the Primordial Amnesia (Raw Brainstorming 03). It must be generated as a vivid, personal, first-person recollection of the transition — never shared across inhabitants.
- [GEN-003] **Structured Output Schema**: The factory will request JSON structured output with a validation schema matching `ArrivalProfile` fields, with generative retry on schema failure (consistent with ADR-0008 [AUT-004]).
- [GEN-004] **CLI Simplification**: The `arrive` subparser will remove `--values`, `--temperament`, `--goals`, `--memory` flags. The user provides only `--name` and optionally `--language`. Identity generation is Ollama's responsibility.
- [GEN-005] **Provenance Tracking**: The generated profile will be logged with model, inference ID, and prompt version for auditability (consistent with ADR-0008 [AUT-002]).
- [GEN-006] **DEFAULT_INITIAL_PROFILES Removal**: The `DEFAULT_INITIAL_PROFILES` constant in `simulation.py` will be removed from production code. Tests that need fixture profiles will use explicit `ArrivalProfile` construction within `tests/`.
- [GEN-007] **Test Doubles Preserved**: Tests may continue to construct `ArrivalProfile` with explicit static data under `tests/` (consistent with ADR-0008 [AUT-007]).

## Consequences

### Positive Consequences
- [POS-001] **Authentic Individuality**: Every Newlander arrives with a unique personality, goals, and arrival memory generated by generative cognition.
- [POS-002] **ADR-0008 Full Compliance**: Zero static identity data in the production CLI or runtime.
- [POS-003] **Richer Chronicler Output**: The Silent Chronicler receives genuinely different source material per inhabitant, producing varied and authentic diary entries.
- [POS-004] **User Simplicity**: The operator provides a name; everything else emerges from the generative model, aligned with the Newland philosophy that inhabitants shape themselves.

### Negative Consequences & Risks
- [NEG-001] **Arrival Latency**: Generating a profile requires one Ollama call (~3-8 seconds on M1 Max). - **Mitigation**: This is a one-time cost per arrival, acceptable given the significance of the identity generation event.
- [NEG-002] **Generation Failure**: Ollama may be unavailable or produce invalid output. - **Mitigation**: Apply ADR-0008 [AUT-004] (generative retry) and [AUT-005] (deferral). If generation fails after retries, the arrival is deferred — never filled with static data.

## Compliance & RAG Impact
- [CMP-001] **ADR-0008 Enforcement**: This ADR extends [AUT-001] from agent *decisions* to agent *identity formation*. Static profiles in production code violate the zero-static invariant.
- [CMP-002] **RAG Updated**: `docs/README.md` index updated with ADR-0011.
- [CMP-003] **Files Modified**: `engine/newland_engine/cli.py`, `engine/newland_engine/simulation.py`, new `engine/newland_engine/arrival_factory.py`.
- [CMP-004] **Approval**: Pending Giovanni Fiore review.
