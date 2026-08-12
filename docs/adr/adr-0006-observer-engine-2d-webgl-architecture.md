---
id: adr-0006
title: "Narrative-First 2.5D WebGL Observer Engine Architecture"
status: "Accepted"
date: "2026-08-12"
authors: ["Agent AI", "Giovanni Fiore"]
tags: ["observer", "webgl", "pixijs", "sse", "event-stream", "architecture"]
---

# ADR-0006: Narrative-First 2.5D WebGL Observer Engine Architecture

## Context & Problem Statement
Newland requires a visual observer that makes its continuous simulation perceptible without turning the project into a conventional controllable videogame. ADR-0003 defines the Silent Chronicler and the Architect Inspector Console, while ADR-0005 selects a local simulation runtime and a web observer. Neither decision defines the visual projection, rendering technology, observer data contract, or boundary between simulation truth and presentation.

The observer must represent a circular and progressively revealed world, inhabitants, arrivals, daily activity, resonance nodes, relationships, and planetary time. It must preserve the non-interference principle: visual interaction may inspect or navigate recorded state, but it must not directly mutate the simulation.

## Decision Drivers
- [DRV-001] **Narrative Primacy**: The Silent Chronicler's prose and atmosphere must remain the primary experience.
- [DRV-002] **Spatial Legibility**: The observer must reveal where inhabitants, settlements, events, and resonance phenomena exist and how they change over time.
- [DRV-003] **Non-Interference**: Camera and inspection actions must not become commands to inhabitants or world state.
- [DRV-004] **Deterministic Replay**: The same persisted event sequence must reconstruct the same observer state independently of LLM output timing.
- [DRV-005] **Local Performance**: The observer must run smoothly on the target Mac while local LLM inference consumes substantial unified memory and GPU resources.
- [DRV-006] **Progressive Complexity**: The first usable observer must not require a 3D asset pipeline, skeletal animation, physics engine, or procedural terrain system.
- [DRV-007] **Required Product Surface**: The WebGL observer is a required part of Newland, even though the autonomous agent runtime has implementation priority.

## Considered Alternatives

### Alternative 1: Full 3D World with Three.js or a Game Engine
- **Description**: Render terrain, buildings, vegetation, inhabitants, lighting, and camera navigation as a continuous 3D environment.
- **Rejection Rationale**: [REJ-001] A full 3D world introduces asset production, animation, level-of-detail, collision, path rendering, and GPU contention before the simulation model is validated. It also encourages direct avatar-style control that conflicts with non-interference.

### Alternative 2: DOM-Only Narrative Journal and Administrative Dashboard
- **Description**: Present the diary, character cards, tables, and charts without a spatial canvas.
- **Rejection Rationale**: [REJ-002] A DOM-only interface cannot adequately express the circular geography, progressive revelation, movement, proximity, or resonance fields that define Newland.

### Alternative 3: Narrative-First 2.5D Observer with a GPU-Accelerated 2D Scene
- **Description**: Render a stylized, zoomable orthographic map with layered terrain, weather, structures, inhabitants, trails, and resonance effects. Use standard HTML for narrative and inspection panels, and reserve true 3D scenes for optional later milestones.
- **Rejection Rationale**: N/A (Selected Option).

## Decision Outcome
Chosen Option: **Alternative 3 (Narrative-First 2.5D Observer with a GPU-Accelerated 2D Scene)**.

### Detailed Decision Points
- [VIS-001] **Visual Projection**: We will use a top-down or shallow isometric 2.5D projection with semantic zoom. The view will communicate spatial state without creating a controllable player avatar.
- [REN-001] **Rendering Layer**: We will use PixiJS as the initial WebGL/WebGPU-backed 2D scene renderer inside a Vite web application. Standard DOM and CSS will render the diary, inspector, accessibility content, and controls.
- [REN-002] **Optional 3D Boundary**: We will not require Three.js for the first observer. We may add isolated Three.js scenes later for exceptional phenomena, such as a resonance vision or a global topology view, without replacing the canonical 2.5D map.
- [DAT-001] **Event-Sourced Observer Model**: The simulation engine will append immutable domain events and periodic world snapshots. The observer will project those records into renderable state; it will never infer canonical state from animation frames or generated prose.
- [DAT-002] **Canonical Event Envelope**: Every observer event will include `event_id`, `world_tick`, `world_time`, `event_type`, `actor_ids`, `location`, `payload`, `visibility`, and `causation_id`.
- [STR-001] **Live Transport**: The backend will expose an initial snapshot over HTTP and ordered live deltas over Server-Sent Events. Client commands will use separate read-only query endpoints. WebSockets remain deferred until bidirectional real-time control is demonstrably required.
- [ARC-001] **Read Model Separation**: The renderer will consume an observer-specific read model rather than raw character prompts, LLM context, or mutable Markdown files.
- [ARC-002] **Visual Layers**: The scene will separate terrain and revealed regions, settlement structures, inhabitants, paths and recent movement, environmental state, resonance fields, and event annotations.
- [UX-001] **Observer Composition**: The map will occupy the spatial stage; the Silent Chronicler will remain continuously readable; selecting a visual entity will open the Architect Inspector without pausing or controlling the world.
- [UX-002] **Time Navigation**: The observer will support live mode plus deterministic pause, scrub, and replay over persisted events. Pausing the view will not pause the simulation engine.
- [PER-001] **Performance Isolation**: The client will animate interpolated visual state at display rate while applying simulation changes only at domain-event boundaries. Rendering quality will degrade gracefully before reducing simulation correctness.
- [PRI-001] **Implementation Priority**: We will implement the agentic engine and canonical event contract first, then build the required WebGL UI against those stable records. This ordering defers UI construction; it does not make the UI optional.

## Consequences

### Positive Consequences
- [POS-001] **Fast Vertical Slice**: A small team can visualize a living settlement without first building a full 3D content pipeline.
- [POS-002] **Lore Alignment**: The user observes traces, rhythms, and relationships instead of controlling an avatar.
- [POS-003] **Replayability**: Event-sourced projections support debugging, narrative review, time travel, and reproducible visual tests.
- [POS-004] **Extensibility**: GPU-rendered layers can later add weather, density fields, procedural vegetation, and resonance shaders without changing canonical world state.

### Negative Consequences & Risks
- [NEG-001] **Reduced Physical Immersion**: A 2.5D map cannot provide the embodied presence of a full 3D environment. - **Mitigation**: Use sound, lighting, particles, camera drift, environmental motion, and selective later 3D vignettes.
- [NEG-002] **Dual UI Technology**: Canvas rendering and DOM panels require synchronization and two accessibility strategies. - **Mitigation**: Keep one observer store and expose every selectable canvas entity through an equivalent DOM inspector path.
- [NEG-003] **Event Schema Commitment**: Replay depends on stable event contracts and migration rules. - **Mitigation**: Version event envelopes and test old fixtures against every projection change.
- [NEG-004] **SSE Connection Constraints**: One-way streams do not support future direct bidirectional interaction. - **Mitigation**: Preserve transport-neutral domain events and adopt WebSockets only if an approved interaction model requires them.

## Compliance & RAG Impact
- [CMP-001] **Related Decisions**: `docs/adr/adr-0003-silent-chronicler-observer-architecture.md`, `docs/adr/adr-0005-technical-engine-local-llm-architecture.md`.
- [CMP-002] **RAG Updated on Approval**: Updated `docs/README.md`, `docs/index.md`, and `docs/log.md`; the observer event contract will be added under `docs/architecture/` before UI implementation.
- [CMP-003] **Approval**: Giovanni Fiore accepted this decision on 2026-08-12 and confirmed that the WebGL UI is required.
