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
│   └── adr-0005-technical-engine-local-llm-architecture.md  <-- ADR-0005 (Stack Tecnico & Modelli LLM Locali Ollama)
├── agents/                                  <-- Specifiche ed Agenti
│   └── templates/                           <-- Template Schede Personaggio (.agent.md)
│       └── character-template.agent.md
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
| **Governance ADR-0005** | [adr-0005-technical-engine-local-llm-architecture.md](file:///Users/giovannifiore/Desktop/newland/docs/adr/adr-0005-technical-engine-local-llm-architecture.md) | ADR Nygard: Stack Tecnico Ibrido e Modelli LLM Locali (Ollama / Llama 3 / Qwen) per cicli a costo zero. |
| **Template Personaggi** | [character-template.agent.md](file:///Users/giovannifiore/Desktop/newland/docs/agents/templates/character-template.agent.md) | Template di base per la scheda agentica (.agent.md) di ogni Newlander. |
| **Skill Auto-Annealing** | [character-auto-annealing/SKILL.md](file:///Users/giovannifiore/Desktop/newland/skills/character-auto-annealing/SKILL.md) | Skill Addy Osmani per l'evoluzione ed auto-commit dei personaggi. |
