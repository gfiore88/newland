---
id: adr-0009
title: "Supervised Runtime and Agent-First Inference Priority"
status: "Accepted"
date: "2026-08-12"
authors: ["Agent AI", "Giovanni Fiore"]
tags: ["runtime", "supervision", "ollama", "inference", "priority", "observer"]
---

# ADR-0009: Supervised Runtime and Agent-First Inference Priority

## Context & Problem Statement

Newland now has four independently executable surfaces: the continuous agent runtime, the generative Silent Chronicler, the read-only Observer API, and the Vite/PixiJS interface. Running them manually in separate terminals is useful during development but does not satisfy prolonged autonomous operation, unified health reporting, coordinated shutdown, or predictable recovery.

The agent minds and the Silent Chronicler also share the same local Ollama installation and GPU memory. Naively executing both workloads concurrently can let downstream narrative generation delay inhabitant cognition. Conversely, reserving all inference capacity for an always-ready continuous scheduler can starve the Chronicle indefinitely. We need an explicit local supervision and inference scheduling boundary that preserves the inhabitants as the primary workload without turning the scheduler into a behavioral author.

## Decision Drivers

- [DRV-001] **Agent Primacy**: Inhabitant perception and deliberation must receive most inference capacity; UI and narration remain downstream.
- [DRV-002] **Zero Behavioral Fallback**: Supervision failures must never select an intention, utterance, mental mutation, role, or narrative template.
- [DRV-003] **Operational Simplicity**: One command should start, monitor, and stop the continuous world, Chronicle, Observer API, and built WebGL UI.
- [DRV-004] **Atomic Lifecycle**: Shutdown and restart must occur between committed cognitive activations and preserve replayable state.
- [DRV-005] **Resource Awareness**: The M1 Max target must not load redundant models or allow uncontrolled concurrent GPU inference.
- [DRV-006] **Non-Interference**: Process health, queue state, view navigation, and Chronicle lag must remain operational metadata outside Newlander perception.
- [DRV-007] **Failure Isolation**: The Chronicle, API, or static UI may restart or defer without stopping autonomous inhabitants.
- [DRV-008] **Auditability**: The operator must distinguish live process health, cognition deferral, Chronicle backlog, and canonical progress.

## Considered Alternatives

### Alternative 1: Independent Manual Processes

- **Description**: Continue launching `run --continuous`, `chronicle`, `serve`, and Vite independently.
- **Rejection Rationale**: [REJ-001] This has no shared health model, dependency ordering, coordinated shutdown, restart policy, or inference admission control.

### Alternative 2: Unrestricted Concurrent Workers

- **Description**: A supervisor starts every component in parallel and lets Ollama schedule requests internally.
- **Rejection Rationale**: [REJ-002] Ollama does not express Newland's agent-first priority, can increase unified-memory pressure, and makes Chronicle-induced cognition latency difficult to audit.

### Alternative 3: Single Local Supervisor with Weighted Agent-First Inference Admission

- **Description**: A `newland live` supervisor owns lifecycle and sends all LLM jobs through an application-level admission queue. Inhabitant cognition receives a larger weighted share and wins ties; the Chronicle receives bounded opportunities so it cannot starve.
- **Rejection Rationale**: N/A (Selected Option).

### Alternative 4: Permanently Separate Models or Hardware for the Chronicle

- **Description**: Pin inhabitant cognition and narration to distinct always-loaded models or devices.
- **Rejection Rationale**: [REJ-003] This increases GPU memory pressure and configuration complexity before measurements prove separate capacity is required.

## Decision Outcome

Chosen Option: **Alternative 3 (Single Local Supervisor with Weighted Agent-First Inference Admission)**.

### Detailed Decision Points

- [SUP-001] **Unified Command**: We will add `newland live` to supervise the continuous runtime, Chronicle worker, Observer API, and static built UI.
- [SUP-002] **Agent-First Queue**: We will admit local inference in weighted rounds with an initial target of at least eight inhabitant jobs for every Chronicle job when both queues remain non-empty. Inhabitant work wins ties.
- [SUP-003] **No Mid-Request Preemption**: We will not terminate an in-flight Ollama request to switch workloads because partial generations are not safe transaction boundaries.
- [SUP-004] **One Inference at a Time by Default**: We will serialize Ollama calls initially to bound GPU memory. Concurrency may become configurable only after a measured soak test.
- [SUP-005] **Bounded Chronicle Lag**: We will expose Chronicle backlog and last narrated canonical sequence. Weighted admission prevents indefinite starvation without granting equal priority.
- [SUP-006] **Independent Failure Domains**: Chronicle failure leaves retryable derived backlog; Observer or UI failure triggers service restart; neither creates a world event nor stops the agent loop.
- [SUP-007] **Static UI Serving**: The Observer server will serve prebuilt `ui/dist/` assets locally. Development may still use Vite separately; production will not require a Node process.
- [SUP-008] **Operational Health**: The supervisor will expose process state, queue depths, in-flight workload class, successful activations, Chronicle cursor, and failure summaries through a local non-canonical endpoint.
- [SUP-009] **Graceful Shutdown**: Ctrl-C will stop admission, let the active transaction finish or reach its existing timeout, then close resources without emitting diegetic stop events.
- [SUP-010] **Model Hygiene**: The supervisor will record configured Newland models and may unload only models it started. It will never stop an unrelated local model based solely on resource pressure.
- [SUP-011] **No Scheduling Semantics Leak**: Queue weights and process health will never enter a Newlander's context, memories, beliefs, or perception.
- [SUP-012] **Measured Revision**: The initial `8:1` weight is an operational parameter, not a behavioral rule, and will be revised only from soak-test evidence.

## Consequences

### Positive Consequences

- [POS-001] One command can operate the autonomous world and its complete observer surface.
- [POS-002] Inhabitant cognition retains explicit priority while the Diary still progresses.
- [POS-003] Serial inference bounds model memory and makes latency attributable to a known workload.
- [POS-004] Failure domains and health data become observable without polluting canonical history.
- [POS-005] Coordinated shutdown preserves atomic event and mind persistence.

### Negative Consequences & Risks

- [NEG-001] **Queue Complexity**: Weighted admission, cancellation, and shutdown introduce concurrency complexity. - **Mitigation**: Start with one inference worker, deterministic queue tests, and no mid-request preemption.
- [NEG-002] **Agent Delay Still Exists**: An admitted Chronicle request can delay the next cognition call. - **Mitigation**: Bound Chronicle generations, admit them only at weighted boundaries, measure p95 wait, and allow narration to be disabled.
- [NEG-003] **Chronicle Backlog**: Heavy activity may outpace the lower-priority narrator. - **Mitigation**: Expose lag, batch committed events, and let the model select significant events.
- [NEG-004] **Supervisor Centrality**: A supervisor bug can affect multiple services. - **Mitigation**: Keep canonical persistence inside existing transactional components and test component restart independently.
- [NEG-005] **Static Asset Build Step**: `newland live` depends on a current `ui/dist/`. - **Mitigation**: Fail clearly with `npm run build --prefix ui` and never silently serve missing assets.

## Compliance & RAG Impact

- [CMP-001] **Related Decisions**: ADR-0003, ADR-0005, ADR-0006, ADR-0007, and ADR-0008.
- [CMP-002] **Implementation Contracts After Approval**: We will add supervisor and inference-admission contracts, deterministic lifecycle tests, then a bounded real Ollama soak test.
- [CMP-003] **Approval**: Giovanni Fiore accepted this decision on 2026-08-12 and authorized implementation.
