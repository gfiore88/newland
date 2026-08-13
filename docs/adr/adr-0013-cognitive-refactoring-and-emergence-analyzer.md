---
id: adr-0013
title: "Cognitive Refactoring and Emergence Analyzer"
status: "Proposed"
date: "2026-08-13"
authors: ["Agent AI", "Giovanni Fiore"]
tags: ["architecture", "cognition", "emergence"]
---

# ADR-0013: Cognitive Refactoring and Emergence Analyzer

## Context & Problem Statement
Following a strategic brainstorming session, the Newland project has reached a critical juncture. The architecture robustly supports an event-sourced world, subjective perception, and persistent minds. However, the cognition module (`cognition.py`) has grown to ~60KB, encompassing memory appraisal, belief revision, social interpretation, goal management, and LLM orchestration. 
Furthermore, while the simulation supports complex internal cognitive states, there is a risk of developing a theoretically sophisticated system that fails to produce macroscopic, observable social emergence (e.g., spontaneous groups, linguistic conventions, leaders, trade). 
To prove the core thesis of the project, we need to focus on generating genuine social emergence without hardcoding societal structures, and we need specialized tools to observe and measure this emergence a posteriori.

## Decision Drivers
- [DRV-001] **Maintainability & Modularity**: Prevent `cognition.py` from becoming a monolithic "God module" as cognitive processes (memory, affect, planning) increase in complexity.
- [DRV-002] **Cognitive Retrieval Efficiency**: Prevent context window explosion and "artificial amnesia" by ensuring only relevant memories and beliefs enter the LLM prompt.
- [DRV-003] **Verifiable Emergence**: Shift focus from theoretical cognitive architecture to measurable, macro-social outcomes (Milestone: Emergence-1).
- [DRV-004] **Observer Independence**: Analyze emergent behaviors without interfering with the simulation runtime or the agents' subjective realities.

## Considered Alternatives

### Alternative 1: Expand `cognition.py` and Hardcode Social Structures
- **Description**: Continue adding psychological structures to `cognition.py` and explicitly code roles like "leader", "merchant", or "friend" into the runtime logic.
- **Rejection Rationale**: [REJ-001] Directly violates the core philosophy of Newland. Societal constructs must emerge from primitive capabilities (moving, communicating, transferring items) rather than being dictated by the engine.

### Alternative 2: Real-time Emergence Analysis within the Engine Loop
- **Description**: Add real-time analysis of social graphs and cultural conventions directly into the tick loop of the `world.py` or `simulation.py`.
- **Rejection Rationale**: [REJ-002] This would bloat the simulation loop, slow down tick processing, and blur the line between the physical world adjudicator and external observation/analysis.

## Decision Outcome
Chosen Option: **Refactor Cognition, Implement Retrieval, and Build an Offline Emergence Analyzer**

### Detailed Decision Points
- [DEC-001] **Cognitive Refactoring**: Split `cognition.py` into focused sub-modules (e.g., `memory_appraisal.py`, `belief_revision.py`, `social.py`, `goals.py`, `affect.py`, `llm_adapter.py`).
- [DEC-002] **Advanced Cognitive Retrieval**: Implement a structured retrieval mechanism that selects memories and beliefs based on salience, recency, emotional impact, and current context before constructing the prompt.
- [DEC-003] **Emergence Analyzer**: Create a standalone tool (`analyzer/` or similar) that parses the EventStore offline to detect social patterns, group formations, and conventions without touching the simulation loop.
- [DEC-004] **Milestone Emergence-1**: Define and execute an experiment with 10-20 "tabula rasa" agents over thousands of ticks to observe and document organic macro-emergence.

## Consequences

### Positive Consequences
- [POS-001] Improved maintainability of the cognitive engine, facilitating isolated experimentation (e.g., testing different memory retrieval algorithms).
- [POS-002] Clearer separation of concerns, ensuring the LLM is fed high-quality, relevant context, thereby improving agent decision-making and consistency.
- [POS-003] Tangible proof of the project's core thesis through reproducible, data-driven experiments analyzing genuine emergent phenomena.

### Negative Consequences & Risks
- [NEG-001] Short-term overhead in refactoring the central `cognition.py` module, which currently handles critical path execution. - **Mitigation**: Incremental extraction with strict unit testing for each separated subsystem.
- [NEG-002] The offline Emergence Analyzer requires robust data processing logic to infer meaning from raw events. - **Mitigation**: Start with simple metrics (e.g., frequency of interaction, transfer of items) before tackling complex convention detection.

## Compliance & RAG Impact
- [CMP-001] **RAG Files Updated**: `docs/README.md`, `docs/adr/adr-0013-cognitive-refactoring-and-emergence-analyzer.md`
- [CMP-002] **Directives Updated**: Roadmap adjustments will be proposed to focus on Milestone Emergence-1.
