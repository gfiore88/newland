# NEWLAND // Universo Parallelo Speculare & Framework Agentico

> **Newland** è un progetto a lungo termine dedicato alla concettualizzazione, formalizzazione e simulazione di un universo parallelo speculare nello stato primordiale di *Tabula Rasa* (popolazione = 0), governato da un sistema di regole etiche, fisiche ed agentiche rigorose.

## Primo vertical slice eseguibile

Il repository contiene un runtime Python event-driven con menti persistenti, percezione privata, memoria episodica soggettiva, beliefs, relazioni, affetti, riflessioni, obiettivi, piani, impegni, agenda autonoma e intenzioni generative strutturate. Il mondo canonico comprende un territorio connesso, risorse locali, nodi di risonanza, inventari, consumo, attività fisiche, arrivi atomici, lingue, competenze, famiglie, cooperazioni consensuali e conflitti, arbitrati e persistiti su SQLite. I ruoli sociali e gli eventuali frammenti di anamnesi sono interpretazioni private generate liberamente dalle singole menti, mai classificazioni o flashback assegnati dal runtime. Ollama è obbligatorio per le decisioni dei Newlander: il codice non sostituisce mai una mente con pattern statici. Tutti i cambiamenti psicologici, le azioni materiali, le interpretazioni sociali e il momento della successiva attenzione vengono scelti dalla mente dell'agente e validati contro ciò che ha realmente percepito, ricordato, conosce o può fisicamente raggiungere.

```bash
# Setup e run agentico in tempo reale
uv sync
uv run newland --db data/newland.db run

# Mondo autonomo continuo; Ctrl-C arresta tra transazioni integre
uv run newland --db data/newland.db run --continuous --model qwen3:8b

# Failover fra modelli generativi, senza fallback statico
uv run newland --db data/newland.db run \
  --model qwen3:8b --model qwen3:4b

# Modello riflessivo opzionale per risonanza e conflitti attivi
uv run newland --db data/newland.db run \
  --model qwen3:8b --reflective-model qwen3:30b

# Ispezione della verità canonica
uv run newland --db data/newland.db events
uv run newland --db data/newland.db state

# API locale read-only per l'Observer WebGL
uv run newland --db data/newland.db serve
# http://127.0.0.1:8765/api/snapshot
# http://127.0.0.1:8765/api/stream

# In un secondo terminale: UI WebGL locale
cd ui
npm install
npm run dev
# http://127.0.0.1:5173

# In un terzo terminale: Diario generativo continuo, sempre derivato
uv run newland --db data/newland.db chronicle --model qwen3:8b

# Test degli invarianti
uv run python -m unittest discover -s tests -v
```

---

## 🌟 Architettura e Governance Agentica

Questo repository implementa una governance agentica ferrea basata sui seguenti principi:

1. **Obbligo dell'ADR (Mandatory ADR)**: Nessun task o sviluppo può iniziare senza prima aver redatto ed ottenuto l'approvazione per un Architecture Decision Record in `docs/adr/adr-NNNN-[title-slug].md`.
2. **Nygard Laws & Awesome Copilot**: Tutti gli ADR seguono le leggi di Michael Nygard ed utilizzano la skill [`create-architectural-decision-record`](file:///skills/create-architectural-decision-record/SKILL.md) con coded bullet points (es. `[GOV-001]`, `[DRV-001]`).
3. **RAG Centralizzato in `docs/`**: Tutta la base di conoscenza, la documentazione di dominio e le specifiche risiedono esclusivamente sotto la cartella `docs/`.
4. **Governed Agent Self-Annealing**: Gli agenti perfezionano le proprie direttive tra run successive tramite il pattern di auto-miglioramento di Giovanni Fiore, con approvazione umana obbligatoria.

---

## 📁 Struttura del Repository

```
newland/
├── .agents/
│   └── AGENTS.md                  <-- Regole di governance del workspace
├── AGENTS.md                      <-- Direttive di progetto principali
├── docs/                          <-- Root RAG & Base di Conoscenza
│   ├── README.md                  <-- Indice RAG
│   ├── adr/                       <-- Architecture Decision Records (Nygard Rules)
│   │   ├── 0000-adr-template.md   <-- Template ADR Standard
│   │   └── adr-0001-agentic-governance-and-adr-workflow.md <-- ADR-0001 Approvato
│   ├── domain/                    <-- Specifica del Dominio dell'Universo Parallelo
│   │   └── newland-universe-spec.md
│   ├── architecture/              <-- Documentazione Architetturale
│   └── agents/                    <-- Specifiche degli Agenti
├── engine/newland_engine/         <-- Runtime agentico Python
├── tests/                         <-- Test di replay, percezione e arbitraggio
├── ui/                            <-- Observer Vite + PixiJS WebGL e pannelli DOM
├── pyproject.toml                 <-- Packaging e comando `newland`
└── skills/                        <-- Agent Skills (Standard Addy Osmani)
    ├── create-architectural-decision-record/
    ├── adr-creator/
    └── self-annealing/
```

---

## 📜 Registri ed Indici RAG

- 📄 **[Indice RAG Principal](docs/README.md)**
- 📄 **[ADR-0001: Governance Agentica & Workflow ADR](docs/adr/adr-0001-agentic-governance-and-adr-workflow.md)**
- 📄 **[Specifica Universo Parallelo Newland](docs/domain/newland-universe-spec.md)**
- 📄 **[Contratti del Runtime Agentico](docs/architecture/agent-runtime-contracts.md)**
- 📄 **[Contratto HTTP/SSE dell'Observer](docs/architecture/observer-api-contract.md)**
- 📄 **[Roadmap Implementativa](docs/architecture/implementation-roadmap.md)**
