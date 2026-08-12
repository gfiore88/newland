---
name: llm-wiki-maintainer
description: Skill per la gestione ed il mantenimento dell'LLM Wiki RAG secondo il pattern di Andrej Karpathy (Ingest, Query, Lint e Log).
---

# LLM Wiki Maintainer Skill (Karpathy Pattern)

## Scopo
Consentire all'agente di ingerire fonti grezze da `docs/raw/`, compilare e mantenere interconnesse le pagine markdown della wiki in `docs/wiki/`, mantenere aggiornati `docs/index.md` e `docs/log.md`, ed eseguire cicli di `LINT` per garantire l'assenza di contraddizioni o link orfani.

## Flussi di Lavoro

### 1. Ingest di una Fonte Grezza (`docs/raw/`)
1. Inserire il file grezzo in `docs/raw/`.
2. Creare la sintesi fonte in `docs/wiki/sources/src-[slug].md`.
3. Estrarre o aggiornare le entità in `docs/wiki/entities/` ed i concetti in `docs/wiki/concepts/`.
4. Inserire link incrociati markdown tra le pagine.
5. Aggiornare l'indice generale in `docs/index.md`.
6. Registrare l'evento in `docs/log.md`: `## [YYYY-MM-DD] ingest | Titolo Fonte`.

### 2. Risposta a Query & Persistenza
1. Consultare `docs/index.md` ed i file della wiki per formulare risposte.
2. Se la risposta produce un'analisi sistemica o una sintesi riutilizzabile, salvarla in `docs/wiki/synthesis/syn-[slug].md` e registrarla in `docs/index.md` e `docs/log.md`.

### 3. Health-Check (`LINT`)
1. Verificare l'assenza di pagine orfane o link rotti.
2. Verificare che non vi siano contraddizioni tra fonti recenti e datate.
3. Registrare l'esito nel log: `## [YYYY-MM-DD] lint | Health Check OK`.
