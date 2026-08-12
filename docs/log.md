# REGISTRO ATTIVITÀ WIKI (KARPATHY LLM-WIKI LOG)

Registro cronologico append-only delle attività di Ingest, Query e Lint della wiki.

---

## [2026-08-12] init | Inizializzazione Karpathy LLM-Wiki RAG Architecture (ADR-0002)
- Creata la struttura a 3 livelli: `docs/raw/`, `docs/wiki/`, `docs/wiki-schema.md`.
- Inizializzato il catalogo `docs/index.md` e la direttiva di manutenzione `docs/wiki-schema.md`.

## [2026-08-12] ingest | Specifica Primordiale Universo Parallelo Newland
- Ingerito documento di dominio `docs/domain/newland-universe-spec.md`.

## [2026-08-12] adr | Registrazione ADR-0003 - Architettura dell'Osservatore Integrato
- Registrato ADR-0003 `docs/adr/adr-0003-silent-chronicler-observer-architecture.md`.

## [2026-08-12] adr | Registrazione ADR-0004 - Auto-Annealing Personaggi 100% Autonomo
- Registrato ADR-0004 `docs/adr/adr-0004-autonomous-character-auto-annealing.md`.

## [2026-08-12] adr | Registrazione ADR-0005 - Stack Tecnico & Modelli LLM Locali (Ollama)
- Registrato ADR-0005 `docs/adr/adr-0005-technical-engine-local-llm-architecture.md`.
- Definizione dello stack tecnico: Runtime Python/Node per la simulazione continua dei tick, Ollama (`localhost:11434` con Llama 3 / Qwen 2.5) per l'inferenza locale a costo zero token, e Web Application (Vite / HTML5 / Glassmorphism) per lo streaming SSE del Diario del Cronista e la Console dell'Architetto.
