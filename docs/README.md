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
│   └── adr-0003-silent-chronicler-observer-architecture.md <-- ADR-0003 (Architettura dell'Osservatore)
├── domain/                                  <-- Documenti di Dominio Grezzi / Capitolato
│   └── newland-universe-spec.md             <-- Specifica Primordiale Universo Parallelo
├── raw/                                     <-- Deposito Fonti Grezze Immutabili
└── wiki/                                    <-- Compilazione Interconnessa Mantenuta dalla LLM
    ├── sources/                             <-- Sintesi Analitiche delle Fonti Ingerite
    ├── entities/                            <-- Pagine Entità (Leggi, biomi, cronista, parametri)
    ├── concepts/                            <-- Modelli teorici e sistemi (Console architetto, ecc.)
    └── synthesis/                           <-- Analisi complesse e risposte a query persistenti
```

---

## Indice dei File RAG & Wiki principali

| Categoria | File RAG / Wiki | Descrizione |
|---|---|---|
| **Governance ADR-0001** | [adr-0001-agentic-governance-and-adr-workflow.md](file:///Users/giovannifiore/Desktop/newland/docs/adr/adr-0001-agentic-governance-and-adr-workflow.md) | ADR Nygard: Regola dell'ADR obbligatorio, RAG in `docs/`, Self-Annealing. |
| **Governance ADR-0002** | [adr-0002-karpathy-llm-wiki-rag-architecture.md](file:///Users/giovannifiore/Desktop/newland/docs/adr/adr-0002-karpathy-llm-wiki-rag-architecture.md) | ADR Nygard: Karpathy LLM-Wiki Pattern per la gestione del RAG. |
| **Governance ADR-0003** | [adr-0003-silent-chronicler-observer-architecture.md](file:///Users/giovannifiore/Desktop/newland/docs/adr/adr-0003-silent-chronicler-observer-architecture.md) | ADR Nygard: Architettura dell'Osservatore Integrato (Diario del Cronista + Console Architetto). |
| **Catalogo Wiki** | [index.md](file:///Users/giovannifiore/Desktop/newland/docs/index.md) | Indice di tutte le pagine fonti, entità e concetti compilati dalla LLM. |
| **Registro Attività** | [log.md](file:///Users/giovannifiore/Desktop/newland/docs/log.md) | Log append-only degli Ingest, Query e Lint. |
| **Direttiva Wiki** | [wiki-schema.md](file:///Users/giovannifiore/Desktop/newland/docs/wiki-schema.md) | Direttiva operativa per Ingest, Query e Lint. |
| **Skill Wiki** | [llm-wiki-maintainer/SKILL.md](file:///Users/giovannifiore/Desktop/newland/skills/llm-wiki-maintainer/SKILL.md) | Skill Addy Osmani per l'esecuzione dei flussi Wiki. |
