# WIKI SCHEMA & OPERATING DIRECTIVE (KARPATHY LLM-WIKI PATTERN)

> [!IMPORTANT]
> Questo documento definisce le regole operative che gli agenti AI DEVONO seguire per ingerire fonti grezze, aggiornare la wiki, rispondere a query e mantenere sana la base di conoscenza del progetto **Newland**.

---

## 1. Struttura del RAG & Karpathy LLM-Wiki

```
docs/
├── raw/                                     <-- Fonti grezze immutabili (PDF, TXT, note, trascrizioni)
├── index.md                                 <-- Catalogo sintetico ragionato di tutte le pagine della wiki
├── log.md                                   <-- Registro cronologico append-only (Ingest, Query, Lint)
├── wiki-schema.md                           <-- Questa direttiva di manutenzione
└── wiki/                                    <-- Pagine compilate ed interconnesse dalla LLM
    ├── sources/                             <-- Sintesi analitiche delle fonti grezze ingerite
    ├── entities/                            <-- Pagine di entità (Concetti, biomi, leggi, parametri)
    ├── concepts/                            <-- Approfondimenti teorici e modelli sistemici
    └── synthesis/                           <-- Analisi complesse e risposte a query persistenti
```

---

## 2. Flusso di Ingestione (`INGEST`)

Quando una nuova fonte grezza viene inserita in `docs/raw/`:

1. **Lettura & Estrazione**: L'agente legge la fonte grezza e ne discute i punti chiave.
2. **Pagina Fonte (`docs/wiki/sources/src-[slug].md`)**: L'agente crea una pagina di sintesi della fonte indicando titolo, data, autore, punti chiave e link alla fonte in `docs/raw/`.
3. **Aggiornamento Entità & Concetti**: L'agente aggiorna o crea le pagine rilevanti in `docs/wiki/entities/` e `docs/wiki/concepts/` inserendo riferimenti incrociati (wiki links markdown `[Titolo](file:///...)`).
4. **Aggiornamento dell'Indice (`docs/index.md`)**: L'agente aggiunge la nuova fonte e le nuove pagine entità al catalogo `docs/index.md`.
5. **Registro Cronologico (`docs/log.md`)**: L'agente append una riga nel formato:
   `## [YYYY-MM-DD] ingest | Titolo della Fonte`

---

## 3. Flusso di Interrogazione (`QUERY`)

Quando l'utente pone una domanda complessa sul sistema:

1. L'agente consulta `docs/index.md` ed i file pertinenti in `docs/wiki/`.
2. L'agente sintetizza la risposta citando le pagine wiki rilevanti.
3. **Persistenza della Risposta**: Se la query produce un'analisi o una sintesi di valore duraturo, l'agente la salva in `docs/wiki/synthesis/syn-[slug].md` e la registra in `docs/index.md` e `docs/log.md`.

---

## 4. Flusso di Manutenzione (`LINT`)

Periodicamente l'agente esegue un `LINT` della wiki per:
- Rilevare e risolvere contraddizioni tra fonti diverse.
- Identificare pagine orfane (senza link in ingresso).
- Segnalare affermazioni obsolete superate da fonti più recenti.
- Aggiornare i link incrociati mancanti.
- Registrare il pass nel log: `## [YYYY-MM-DD] lint | Health Check Wiki OK`.
