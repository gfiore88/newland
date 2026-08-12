---
id: adr-0008
title: "Zero Static Decisions in Autonomous Newlander Cognition"
status: "Accepted"
date: "2026-08-12"
authors: ["Agent AI", "Giovanni Fiore"]
tags: ["agents", "autonomy", "cognition", "llm", "realtime", "architecture"]
---

# ADR-0008: Zero Static Decisions in Autonomous Newlander Cognition

## Context & Problem Statement
The first runtime vertical slice introduced a rule-based decision provider as a production fallback when local LLM inference failed. This made the world technically continuous, but it allowed application code to choose an inhabitant's speech, rest, or social response. That behavior contradicts Newland's central requirement: every Newlander must make its own decisions in real time from its private mind, perceptions, memories, needs, relationships, and goals.

We must distinguish deterministic world mechanics from autonomous cognition. Physics, clocks, event ordering, action validation, persistence, and replay may be deterministic. A Newlander's intentions, choices, speech, priorities, and reflections must never be selected by static behavior trees, scripted responses, hard-coded defaults, or narrative orchestration.

## Decision Drivers
- [DRV-001] **Agent Sovereignty**: Every material action must originate from the activated inhabitant's generative cognitive process.
- [DRV-002] **Real-Time Emergence**: Decisions must be generated from current private state and current perceptions, not replayed from templates.
- [DRV-003] **No Hidden Puppeteer**: Runtime code must not preserve uptime by impersonating an unavailable mind.
- [DRV-004] **World Continuity**: A temporary inference failure must not stop other inhabitants or deterministic environmental processes.
- [DRV-005] **Observable Failure**: Cognitive unavailability must be recorded explicitly instead of concealed behind plausible scripted behavior.

## Considered Alternatives

### Alternative 1: Static Rule-Based Fallback
- **Description**: On invalid JSON or inference failure, choose a predefined action such as speaking, resting, or waiting.
- **Rejection Rationale**: [REJ-001] The code becomes the true decision-maker and the inhabitant only appears autonomous.

### Alternative 2: Central Narrative Model Fallback
- **Description**: Let an omniscient model select actions for any unavailable inhabitant.
- **Rejection Rationale**: [REJ-002] This leaks global knowledge, collapses separate minds into one author, and biases the emerging story.

### Alternative 3: Generative Retry, Model Failover, or Cognitive Deferral
- **Description**: Retry schema repair using the same private cognitive context, optionally route to another generative model, and defer the activation if no model can return a valid intention.
- **Rejection Rationale**: N/A (Selected Option).

## Decision Outcome
Chosen Option: **Alternative 3 (Generative Retry, Model Failover, or Cognitive Deferral)**.

### Detailed Decision Points
- [AUT-001] **No Production Static Cognition**: We will not ship rule-based, scripted, random-table, behavior-tree, or default-action providers for Newlander decisions.
- [AUT-002] **Generative Origin Invariant**: Every `ActionProposed` will include the generative provider, model, prompt version, inference identifier, and attempt metadata that produced it.
- [AUT-003] **Private Context Preservation**: Retries and model failover will receive the same agent-scoped knowledge boundary; failover will not introduce global state.
- [AUT-004] **Invalid Output Repair**: Invalid structured output will trigger a bounded generative repair request, never a locally chosen action.
- [AUT-005] **Cognitive Deferral**: If all generative attempts fail, the runtime will persist `CognitionDeferred`, schedule a later activation, and commit no material agent action.
- [AUT-006] **Independent World Progress**: Other minds and deterministic environmental systems may continue while one mind is deferred.
- [AUT-007] **Test Doubles Only**: Tests may inject scripted cognition providers to assert engine invariants. Such providers must live under `tests/` and cannot be selected by the production CLI.
- [AUT-008] **Mechanics Boundary**: Deterministic code may enforce physical constraints, update physiological processes, order events, and replay history; it may not choose what an inhabitant intends to do about those conditions.
- [AUT-009] **Generative Inner Change**: Subjective appraisal, emotional meaning, belief formation, relationship interpretation, reflection, and goal revision will also originate from the agent's generative cognition. Code may validate bounds, provenance, and referential integrity but will not assign psychological meaning through static heuristics.

## Consequences

### Positive Consequences
- [POS-001] **Authentic Autonomy**: Observable behavior always originates from a generative mind conditioned on private state.
- [POS-002] **Honest Runtime Semantics**: Inference outages appear as cognitive unavailability rather than counterfeit personality.
- [POS-003] **Clean Responsibility Boundary**: The engine determines what is possible; the inhabitant determines what it attempts.

### Negative Consequences & Risks
- [NEG-001] **Temporary Inaction**: An inhabitant may remain inactive during model failure. - **Mitigation**: Retry, route across configured local models, and keep the rest of the world advancing.
- [NEG-002] **Higher Inference Cost**: Repair and failover add model calls. - **Mitigation**: Bound attempts, record failures, and improve schemas/prompts from evidence.
- [NEG-003] **Harder Automated Tests**: Production behavior is intentionally nondeterministic. - **Mitigation**: Test engine invariants with explicit test doubles and evaluate agent behavior statistically or scenario-wise.

## Compliance & RAG Impact
- [CMP-001] **ADR-0007 Refinement**: This ADR supersedes only ADR-0007 statements permitting deterministic cognition fallbacks or deterministic selection of routine agent actions.
- [CMP-002] **Runtime Update**: Remove production `RuleBasedCognition`, static fallback behavior, default cognitive provider, and static action fallback fields.
- [CMP-003] **Approval**: Giovanni Fiore explicitly accepted this invariant on 2026-08-12 by requiring all decisions to remain real-time and autonomous.
