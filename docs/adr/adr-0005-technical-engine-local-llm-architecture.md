---
id: adr-0005
title: "Technical Engine & Hybrid Local-LLM Runtime Architecture"
status: "Accepted"
date: "2026-08-12"
authors: ["Agent AI", "Giovanni Fiore"]
tags: ["technical-stack", "ollama", "m1-max-64gb", "local-llm", "architecture", "adr", "web-app"]
---

# ADR-0005: Technical Engine & Hybrid Local-LLM Runtime Architecture

## Context & Problem Statement
The **Newland** living world simulator requires a continuous, real-time execution engine to drive character ticks, dialogue, event generation, and autonomous auto-annealing. 

Relying exclusively on commercial cloud LLM APIs for continuous tick loops would lead to high API token costs, rate limits, and latency bottlenecks. We require a clear technical stack specification that defines how local LLM inference engines (e.g., Ollama / vLLM) interact with a Python/Node simulation runtime and a modern Web UI.

## Hardware Profile Target
- **Machine**: Apple MacBook Pro M1 Max (10 CPU Cores / 32 GPU Cores)
- **Unified Memory**: 64 GB RAM
- **Inference Capability**: Excellent local throughput for 14B, 27B, 32B, and 70B (4-bit/8-bit quantized) models via Metal GPU acceleration.

## Decision Drivers
- [DRV-001] **Zero API Token Cost for Continuous Loops**: Character daily ticks and routine interactions must run endlessly without financial or quota limitations.
- [DRV-002] **High-Level Reasoning & Literary Quality**: Leveraging 64GB Unified Memory to run medium-to-large local models (e.g., `qwen2.5:32b`, `gemma2:27b`, `llama3.3:70b-q4`) for rich narrative depth and psychological nuance.
- [DRV-003] **Real-Time Web UI Streaming**: The frontend must receive live narrative updates from the Silent Chronicler via Server-Sent Events (SSE) or WebSockets.

## Considered Alternatives

### Alternative 1: 100% Cloud LLM API Stack
- **Description**: Running every character tick and dialogue through commercial cloud APIs.
- **Rejection Rationale**: [REJ-001] Prohibitively expensive for continuous 24/7 simulation loops; subject to external rate limits and API deprecations.

### Alternative 2: Pure Offline Static File Generation
- **Description**: Generating character stories manually via batch scripts without a real-time web application.
- **Rejection Rationale**: [REJ-002] Lacks real-time interactivity, live inspection console, and observer UI experience.

### Alternative 3: Hybrid Technical Stack (Local LLM Simulation Engine + Web UI Observer)
- **Description**: 
  - **Hardware Engine Target**: Apple Silicon M1 Max with 64GB RAM (Metal acceleration).
  - **Backend Runtime**: Python/Node.js orchestration loop managing ticks, event triggers, and Git auto-commits.
  - **Inference Engine**: Ollama (`localhost:11434`) running local 32B/70B models (`qwen2.5:32b`, `llama3.3:70b-q4_K_M`) for character daily ticks and auto-annealing.
  - **Frontend UI**: Web Application (Vite / HTML5 / Vanilla CSS with Glassmorphism and Dark Mode) streaming the Silent Chronicler's journal via SSE and hosting the Architect Inspector Console.
- **Rejection Rationale**: N/A (Selected Option).

## Decision Outcome
Chosen Option: **Alternative 3 (Hybrid Technical Stack: Local LLM Engine + Web UI Observer)**.

### Detailed Technical Component Specifications

- [ENG-001] **Simulation Runtime Engine (`engine/`)**:
  - Python/Node.js daemon orchestrating the planetary time ticks (Giorno 1, Giorno 2...).
  - Communicates with Ollama API (`localhost:11434`) to execute character prompt loops and trigger `character-auto-annealing`.
- [LLM-001] **Local Inference Stack (Ollama - M1 Max 64GB Target)**:
  - Utilizes 32B to 70B open-weights models (`qwen2.5:32b`, `llama3.3:70b-instruct-q4_K_M`, `gemma2:27b`) for high-precision local reasoning, Italian literary prose for the Chronicler, and deep character psychology.
- [WEB-001] **Web UI Observer (`ui/`)**:
  - Modern web interface built with HTML5, Vanilla CSS (Rich Aesthetics, Glassmorphism, Dark Palette), and JS.
  - Features real-time SSE stream for "Il Diario del Cronista" and interactive modals for the "Architect Inspector Console".
- [GIT-001] **Persistence & Karpathy LLM-Wiki Integration**:
  - Automatically updates `docs/log.md`, `docs/wiki/`, and `.agent.md` files, committing changes to Git upon major world milestones.

## Consequences

### Positive Consequences
- [POS-001] **Infinite Zero-Cost Runs**: The simulator can run continuously without incurring API fees.
- [POS-002] **Ultra-Fast Metal GPU Throughput**: M1 Max 64GB provides blazing fast token generation for 32B models.
- [POS-003] **Complete Privacy & Local Independence**: The entire Newland universe runs offline on the user's Mac.

## Compliance & RAG Impact
- [CMP-001] **RAG Index Updated**: [docs/README.md](file:///Users/giovannifiore/Desktop/newland/docs/README.md)
- [CMP-002] **Directives Updated**: [AGENTS.md](file:///Users/giovannifiore/Desktop/newland/AGENTS.md) and [.agents/AGENTS.md](file:///Users/giovannifiore/Desktop/newland/.agents/AGENTS.md)
