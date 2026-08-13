# INDEX RAG: KNOWLEDGE BASE PROGETTO NEWLAND (KARPATHY LLM-WIKI)

> [!IMPORTANT]
> Tutta la conoscenza, il RAG e le decisioni del progetto Newland sono organizzate ed accessibili esclusivamente sotto questa cartella `docs/` seguendo il pattern **Karpathy LLM-Wiki**.

---

## Struttura della Conoscenza (RAG & Wiki Tree)

```
docs/
├── README.md                                <-- Indice RAG Principale del Progetto
├── index.md                                 <-- Catalogo Sintetico Ragionato della Wiki
├── log.md                                   <-- Registro Cronologico Append-Only (Ingest, Query, Lint)
├── wiki-schema.md                           <-- Direttiva Operativa di Manutenzione Wiki
├── adr/                                     <-- Architecture Decision Records (Nygard Rules)
│   ├── 0000-adr-template.md                 <-- Template Nygard Standard
│   ├── adr-0001-agentic-governance-and-adr-workflow.md <-- ADR-0001 (Governance & Self-Annealing)
│   ├── adr-0002-karpathy-llm-wiki-rag-architecture.md  <-- ADR-0002 (Karpathy LLM-Wiki Pattern)
│   ├── adr-0003-silent-chronicler-observer-architecture.md <-- ADR-0003 (Architettura dell'Osservatore)
│   ├── adr-0004-autonomous-character-auto-annealing.md     <-- ADR-0004 (Auto-Annealing Personaggi 100% Autonomo)
│   ├── adr-0005-technical-engine-local-llm-architecture.md  <-- ADR-0005 (Stack Tecnico & Modelli LLM Locali Ollama)
│   ├── adr-0006-observer-engine-2d-webgl-architecture.md   <-- ADR-0006 (Engine Grafico 2.5D WebGL / PixiJS)
│   ├── adr-0007-autonomous-agent-mind-and-world-runtime.md <-- ADR-0007 (Runtime Agenti Autonomi & World Adjudicator)
│   ├── adr-0008-zero-static-agent-decisions.md             <-- ADR-0008 (Zero Decisioni Statiche)
│   ├── adr-0009-supervised-runtime-and-inference-priority.md <-- ADR-0009 (Supervisore & Priorità LLM)
│   ├── adr-0010-dynamic-embodied-carrying-capacity.md        <-- ADR-0010 proposto (Capacità corporea dinamica)
│   ├── adr-0011-generative-arrival-identity.md             <-- ADR-0011 (Generative Arrival Identity)
│   ├── adr-0012-cognitive-stalemate-resolution.md          <-- ADR-0012 (Cognitive Stalemate & Reflection Loop)
│   ├── adr-0013-cognitive-refactoring-and-emergence-analyzer.md <-- ADR-0013 (Cognitive Refactoring & Emergence)
│   ├── adr-0014-observer-ui-architecture-and-aesthetics.md <-- ADR-0014 (Observer UI Architecture)
│   ├── adr-0015-procedural-biome-rendering-engine.md       <-- ADR-0015 (Procedural Biome Rendering Engine)
│   ├── adr-0016-embodied-somatic-perception-and-survival-deliberation.md <-- ADR-0016 (Embodied Somatic Perception)
│   ├── adr-0017-visual-agent-state-system.md               <-- ADR-0017 (Visual Agent State System)
│   ├── adr-0018-bounded-cloud-cognition-benchmark.md       <-- ADR-0018 accettato (Cloud Cognition Benchmark)
│   └── adr-0019-live-cloud-cognition-with-persistent-budget.md <-- ADR-0019 proposto (Alibaba nella live)
├── agents/                                  <-- Specifiche ed Agenti
│   └── templates/                           <-- Template Schede Personaggio (.agent.md)
│       └── character-template.agent.md
├── architecture/                            <-- Contratti eseguibili e roadmap
│   ├── agent-runtime-contracts.md            <-- Eventi, mente, percezione, azioni e scheduler
│   ├── observer-api-contract.md               <-- Snapshot HTTP, SSE e confine read-only
│   └── implementation-roadmap.md             <-- Milestone engine, società e UI WebGL
├── domain/                                  <-- Documenti di Dominio Grezzi / Capitolato
│   └── newland-universe-spec.md             <-- Specifica Primordiale Universo Parallelo
├── raw/                                     <-- Deposito Fonti Grezze Immutabili
└── wiki/                                    <-- Compilazione Interconnessa Mantenuta dalla LLM
```

---

## Indice dei File RAG & Wiki principali

| Categoria | File RAG / Wiki | Descrizione |
|---|---|---|
| **Governance ADR-0001** | [adr-0001-agentic-governance-and-adr-workflow.md](file:///Users/giovannifiore/Desktop/newland/docs/adr/adr-0001-agentic-governance-and-adr-workflow.md) | ADR Nygard: Regola dell'ADR obbligatorio, RAG in `docs/`, Self-Annealing di Sistema. |
| **Governance ADR-0002** | [adr-0002-karpathy-llm-wiki-rag-architecture.md](file:///Users/giovannifiore/Desktop/newland/docs/adr/adr-0002-karpathy-llm-wiki-rag-architecture.md) | ADR Nygard: Karpathy LLM-Wiki Pattern per la gestione del RAG. |
| **Governance ADR-0003** | [adr-0003-silent-chronicler-observer-architecture.md](file:///Users/giovannifiore/Desktop/newland/docs/adr/adr-0003-silent-chronicler-observer-architecture.md) | ADR Nygard: Architettura dell'Osservatore Integrato (Diario del Cronista + Console Architetto). |
| **Governance ADR-0004** | [adr-0004-autonomous-character-auto-annealing.md](file:///Users/giovannifiore/Desktop/newland/docs/adr/adr-0004-autonomous-character-auto-annealing.md) | ADR Nygard: Auto-Annealing Personaggi 100% Autonomo senza approvazione umana. |
| **Governance ADR-0005** | [adr-0005-technical-engine-local-llm-architecture.md](file:///Users/giovannifiore/Desktop/newland/docs/adr/adr-0005-technical-engine-local-llm-architecture.md) | ADR Nygard: Stack Tecnico Ibrido e Modelli LLM Locali (Ollama / Llama 3 / Qwen) su M1 Max 64GB. |
| **Governance ADR-0006** | [adr-0006-observer-engine-2d-webgl-architecture.md](file:///Users/giovannifiore/Desktop/newland/docs/adr/adr-0006-observer-engine-2d-webgl-architecture.md) | ADR Nygard: Visual Observer Engine 2.5D WebGL (PixiJS) con mappa interattiva zoomabile e SSE. |
| **Governance ADR-0007** | [adr-0007-autonomous-agent-mind-and-world-runtime.md](file:///Users/giovannifiore/Desktop/newland/docs/adr/adr-0007-autonomous-agent-mind-and-world-runtime.md) | ADR Nygard: Cognizione Agenti (`AgentMind`), Event-Driven Architecture, SQLite Adjudicator. |
| **Governance ADR-0008** | [adr-0008-zero-static-agent-decisions.md](file:///Users/giovannifiore/Desktop/newland/docs/adr/adr-0008-zero-static-agent-decisions.md) | ADR Nygard: nessuna decisione statica o fallback comportamentale; retry/failover generativo o differimento cognitivo. |
| **Governance ADR-0009** | [adr-0009-supervised-runtime-and-inference-priority.md](file:///Users/giovannifiore/Desktop/newland/docs/adr/adr-0009-supervised-runtime-and-inference-priority.md) | Supervisore unico e ammissione Ollama agent-first pesata per runtime e Cronista. |
| **Proposta ADR-0010** | [adr-0010-dynamic-embodied-carrying-capacity.md](file:///Users/giovannifiore/Desktop/newland/docs/adr/adr-0010-dynamic-embodied-carrying-capacity.md) | Capacità di carico derivata da profilo corporeo, salute ed evoluzione fisica event-sourced. |
| **Governance ADR-0011** | [adr-0011-generative-arrival-identity.md](file:///Users/giovannifiore/Desktop/newland/docs/adr/adr-0011-generative-arrival-identity.md) | ADR Nygard: Generative Arrival Identity. |
| **Governance ADR-0012** | [adr-0012-cognitive-stalemate-resolution.md](file:///Users/giovannifiore/Desktop/newland/docs/adr/adr-0012-cognitive-stalemate-resolution.md) | ADR Nygard: Cognitive Stalemate Resolution (Energy Deadlock & Duplicate Reflections). |
| **Governance ADR-0013** | [adr-0013-cognitive-refactoring-and-emergence-analyzer.md](file:///Users/giovannifiore/Desktop/newland/docs/adr/adr-0013-cognitive-refactoring-and-emergence-analyzer.md) | ADR Nygard: Refactoring Cognition, Emergence Analyzer, and Milestone Emergence-1. |
| **Contratti Runtime** | [agent-runtime-contracts.md](file:///Users/giovannifiore/Desktop/newland/docs/architecture/agent-runtime-contracts.md) | Contratti implementativi per eventi canonici, `AgentMind`, percezione, intenzioni, arbitraggio, scheduling e replay. |
| **Contratto Observer** | [observer-api-contract.md](file:///Users/giovannifiore/Desktop/newland/docs/architecture/observer-api-contract.md) | Read model privilegiato, snapshot HTTP, stream SSE, sicurezza locale e non-interferenza. |
| **Roadmap Engine** | [implementation-roadmap.md](file:///Users/giovannifiore/Desktop/newland/docs/architecture/implementation-roadmap.md) | Milestone dal vertical slice agentico alla UI WebGL obbligatoria. |
| **Template Personaggi** | [character-template.agent.md](file:///Users/giovannifiore/Desktop/newland/docs/agents/templates/character-template.agent.md) | Template di base per la scheda agentica (.agent.md) di ogni Newlander. |
| **Skill Auto-Annealing** | [character-auto-annealing/SKILL.md](file:///Users/giovannifiore/Desktop/newland/skills/character-auto-annealing/SKILL.md) | Skill Addy Osmani per l'evoluzione ed auto-commit dei personaggi. |
| **Governance ADR-0014** | [adr-0014-observer-ui-architecture-and-aesthetics.md](file:///Users/giovannifiore/Desktop/newland/docs/adr/adr-0014-observer-ui-architecture-and-aesthetics.md) | ADR Nygard: Architettura e Design System dell'Observer UI |
| **Governance ADR-0018** | [adr-0018-bounded-cloud-cognition-benchmark.md](file:///Users/giovannifiore/Desktop/newland/docs/adr/adr-0018-bounded-cloud-cognition-benchmark.md) | Benchmark cloud offline con opt-in, sanitizzazione, limiti locali e nessun effetto canonico. |
| **Proposta ADR-0019** | [adr-0019-live-cloud-cognition-with-persistent-budget.md](file:///Users/giovannifiore/Desktop/newland/docs/adr/adr-0019-live-cloud-cognition-with-persistent-budget.md) | Cognition Alibaba live con provider qualificati, budget persistente e continuità solo generativa. |
| **Esperimento Qwen Character** | [2026-08-13-qwen-flash-character-protocol-smoke.md](file:///Users/giovannifiore/Desktop/newland/docs/experiments/2026-08-13-qwen-flash-character-protocol-smoke.md) | Esito, consumo e limiti del primo smoke test offline del protocollo Alibaba. |

## Wiki RAG: Fonti Aggiuntive
- [Proposta UI dell'Observer](file:///Users/giovannifiore/Desktop/newland/docs/wiki/sources/src-newland-ui-proposal.md)
- [Alibaba Model Studio e benchmark cognitivo cloud](file:///Users/giovannifiore/Desktop/newland/docs/wiki/sources/src-brainstorming-10-alibaba-model-studio-cognition-benchmark.md)
- [Idoneità dei modelli Qwen Character](file:///Users/giovannifiore/Desktop/newland/docs/wiki/synthesis/syn-qwen-character-model-fit.md)
