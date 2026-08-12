---
id: adr-0007
title: "Autonomous Agent Minds and Event-Driven World Runtime"
status: "Accepted"
date: "2026-08-12"
authors: ["Agent AI", "Giovanni Fiore"]
tags: ["agents", "cognition", "memory", "simulation", "event-sourcing", "ollama", "architecture"]
---

# ADR-0007: Autonomous Agent Minds and Event-Driven World Runtime

## Context & Problem Statement
Newland's primary product is not its observer interface. It is a persistent autonomous society in which every inhabitant behaves as a separate mind situated in the territory: each inhabitant perceives only locally available information, retains an individual and fallible memory, forms intentions, acts under physical and social constraints, and changes over time without human direction.

ADR-0004 allows character profiles to self-evolve, but it does not define cognition, perception boundaries, action arbitration, memory consolidation, concurrency, or canonical state. ADR-0005 selects local LLM inference but does not define how one model safely serves multiple distinct inhabitants. Markdown mutation alone cannot provide transactional world state or deterministic replay when several agents act concurrently.

The architecture must therefore separate each character's persistent mind from the shared LLM inference service, and separate agent intentions from canonical consequences in the world.

## Decision Drivers
- [DRV-001] **Individual Subjectivity**: Every inhabitant must have private beliefs, memories, emotions, relationships, goals, and ignorance.
- [DRV-002] **Grounded Agency**: An inhabitant may perceive and affect only what its location, senses, body, knowledge, and social context allow.
- [DRV-003] **Autonomous Emergence**: Social patterns and stories must arise from individual actions and world consequences rather than from a central narrator's desired plot.
- [DRV-004] **Persistent Identity**: Each mind must remain coherent across process restarts, model changes, and context-window limits.
- [DRV-005] **Physical Consistency**: LLM-generated intentions must not directly rewrite canonical world state or bypass time, distance, inventory, health, or environmental constraints.
- [DRV-006] **Local Resource Efficiency**: The target machine must support a growing population without loading one LLM instance or operating-system process per inhabitant.
- [DRV-007] **Auditability and Replay**: Every perception, decision, attempted action, adjudication, and material state change must be traceable.
- [DRV-008] **Observer Subordination**: The UI and Silent Chronicler must consume simulation records without influencing the inhabitants' decisions.

## Considered Alternatives

### Alternative 1: One Always-On LLM Process per Inhabitant
- **Description**: Give every character a continuously resident model process and free-running conversational loop.
- **Rejection Rationale**: [REJ-001] This duplicates model memory, wastes compute while agents are idle, creates nondeterministic race conditions, and confuses runtime isolation with psychological individuality.

### Alternative 2: One Omniscient LLM Simulates the Entire Society
- **Description**: Prompt one model with the whole world and ask it to narrate all inhabitants and consequences each tick.
- **Rejection Rationale**: [REJ-002] This produces a single author pretending to be many minds, leaks private knowledge between characters, centralizes plot control, and makes individual causal histories difficult to audit.

### Alternative 3: Event-Driven Cognitive Actors with a Deterministic World Adjudicator
- **Description**: Persist one isolated cognitive state per inhabitant, activate minds through a scheduler when meaningful stimuli or needs occur, share a stateless local inference pool, and submit structured intentions to an authoritative world adjudicator.
- **Rejection Rationale**: N/A (Selected Option).

## Decision Outcome
Chosen Option: **Alternative 3 (Event-Driven Cognitive Actors with a Deterministic World Adjudicator)**.

### Detailed Decision Points
- [MND-001] **Persistent Mind Boundary**: Each inhabitant will own an isolated `AgentMind` state containing identity, values, temperament, needs, affect, beliefs, relationships, goals, commitments, skills, memories, and current attention.
- [MND-002] **Shared Inference, Separate Minds**: Ollama-hosted models will be stateless reasoning workers. The runtime will assemble a private context for one inhabitant per inference request; no hidden chat session or model process will constitute the character's identity.
- [PER-001] **Situated Perception**: A perception service will derive an agent-specific observation from canonical world state using location, line of sight or hearing, language, attention, familiarity, and epistemic access. Agents will never receive the global world state.
- [MEM-001] **Layered Memory**: Each mind will maintain working memory, episodic memory, semantic beliefs, relationship memory, and embodied or emotional traces. Memories will store provenance, subjective interpretation, salience, confidence, and last-access time.
- [MEM-002] **Retrieval and Consolidation**: Decision context will retrieve memories by relevance, recency, salience, goal alignment, and relationship. Scheduled consolidation will create reflections and beliefs while preserving links to supporting episodes.
- [MEM-003] **Fallibility**: Forgetting, distortion, contradiction, and uncertain belief will be first-class state. Canonical facts and an inhabitant's beliefs about those facts will remain separate.
- [COG-001] **Cognitive Cycle**: Each meaningful activation will run `perceive -> appraise -> retrieve -> deliberate -> form intention -> propose action -> observe consequence -> learn`.
- [COG-002] **Structured Intentions**: The LLM will return a schema-validated intention containing action type, target, location, estimated duration, spoken content when applicable, motivation summary, confidence, and fallback. Free prose will not mutate world state.
- [WRL-001] **Authoritative World Adjudicator**: A non-character world service will validate proposed actions against physical laws, geography, time, resources, health, permissions, and simultaneous actions. It will commit consequences as canonical domain events.
- [WRL-002] **No Narrative Game Master**: The adjudicator will enforce constraints and resolve outcomes; it will not choose a preferred storyline, implant goals, or optimize drama.
- [SCH-001] **Discrete-Event Scheduling**: The runtime will not ask every inhabitant to think on every clock tick. It will activate an agent for material stimuli, need thresholds, commitments, encounters, interrupts, and scheduled reflection.
- [SCH-002] **Temporal Resolution**: Deterministic systems will advance routine processes in batches. LLM cognition will be reserved for ambiguous, social, novel, or identity-relevant decisions.
- [SOC-001] **Interaction Protocol**: Conversations and cooperation will occur through world-mediated events. An agent perceives another's observable words and actions, not the other agent's prompt, private memory, or internal reasoning.
- [ACT-001] **Two-Phase Action Commit**: The runtime will persist `ActionProposed`, then either `ActionAccepted`, `ActionModified`, or `ActionRejected`, followed by resulting world events. Agents will perceive outcomes and may revise their plans.
- [STA-001] **Canonical Persistence**: A transactional event store and materialized state database will be canonical. SQLite will be the initial single-machine implementation; event payloads will be schema-versioned.
- [STA-002] **Markdown as Projection**: Character `.agent.md` files, `docs/log.md`, and wiki pages will become human-readable projections and milestone records, not the transactional source of truth for moment-to-moment simulation.
- [OBS-001] **Downstream Observer**: The Silent Chronicler and any WebGL interface will subscribe to committed world events. They will never appear in agent perception unless represented by an explicit diegetic entity.
- [MOD-001] **Model Routing**: Cheap or deterministic code will handle routine needs and movement; a faster local model will handle ordinary cognition; a stronger local model may handle reflection, high-stakes conflict, or rare anamnesis events.
- [TST-001] **Behavioral Evaluation**: The engine will test invariants, knowledge boundaries, replay, personality consistency, memory provenance, action validity, and scenario-level emergent behavior rather than asserting exact generated prose.

## Consequences

### Positive Consequences
- [POS-001] **Real Multiplicity**: Characters remain distinct because their inputs, memories, beliefs, and histories are isolated even when they share one inference model.
- [POS-002] **Grounded Emergence**: Stories arise from constrained intentions and consequences rather than omniscient narration.
- [POS-003] **Scalability**: Event-driven activation avoids spending an LLM call on every character during every world tick.
- [POS-004] **Debuggability**: The system can explain what an inhabitant perceived, remembered, intended, attempted, and learned without exposing hidden model chain-of-thought.
- [POS-005] **Replaceable Presentation**: A terminal log, 2.5D map, or future 3D observer can visualize the same canonical history.

### Negative Consequences & Risks
- [NEG-001] **Higher Domain-Model Complexity**: Cognition, belief, memory, and world truth require distinct schemas. - **Mitigation**: Implement one small vertical slice with two inhabitants, one location, and a narrow action vocabulary before expanding the ontology.
- [NEG-002] **LLM Behavioral Instability**: Model outputs may vary or violate character constraints. - **Mitigation**: Use structured output validation, bounded retries, deterministic fallbacks, invariant checks, and recorded model/prompt versions.
- [NEG-003] **Adjudicator Centrality**: A poorly designed adjudicator can become an implicit omniscient author. - **Mitigation**: Restrict it to explicit simulation rules and stochastic outcome models; keep narrative interpretation downstream.
- [NEG-004] **Memory Growth**: Episodic histories will grow indefinitely. - **Mitigation**: Retain immutable events in archive storage while consolidating the active retrieval index and enforcing context budgets.
- [NEG-005] **Replay Limits with LLM Calls**: Re-running inference may not reproduce the same intention exactly. - **Mitigation**: Replay committed decisions from the event log; treat fresh counterfactual simulation as a new branch with its own identifier.

## Compliance & RAG Impact
- [CMP-001] **Related Decisions**: `docs/adr/adr-0003-silent-chronicler-observer-architecture.md`, `docs/adr/adr-0004-autonomous-character-auto-annealing.md`, `docs/adr/adr-0005-technical-engine-local-llm-architecture.md`, and proposed `docs/adr/adr-0006-observer-engine-2d-webgl-architecture.md`.
- [CMP-002] **ADR-0004 Refinement After Approval**: Autonomous character evolution remains valid, but `.agent.md` self-mutation becomes a durable projection of canonical events rather than the primary runtime state transition mechanism.
- [CMP-003] **ADR-0005 Refinement After Approval**: We will resolve the runtime ambiguity in favor of a Python-first simulation core; the web observer remains a separate downstream application.
- [CMP-004] **RAG Updated on Approval**: Updated `docs/README.md`, `docs/index.md`, and `docs/log.md`; specifications for the world event envelope, `AgentMind`, perception boundary, action schema, and scheduler will be created under `docs/architecture/` before engine implementation.
- [CMP-005] **Approval**: Giovanni Fiore accepted this decision on 2026-08-12 and established the autonomous agent runtime as the first implementation priority.
