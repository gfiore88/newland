# FONTE: BRAINSTORMING 09 — ECONOMIA COGNITIVA E LIVELLI DI MODELLO

- **File grezzo**: [raw-brainstorming-09-cognitive-economy-and-model-tiers.md](../../raw/raw-brainstorming-09-cognitive-economy-and-model-tiers.md)
- **Data ingest**: 2026-08-13
- **Natura**: brainstorming strategico, non decisione approvata
- **Argomenti**: routing multi-modello, costo cognitivo, scheduling, retrieval, emergenza verificabile, omogeneità delle menti

## Tesi centrale

Il rischio di Newland non è soltanto che i modelli locali siano piccoli o lenti. La difficoltà scientifica è ottenere strutture sociali macroscopiche credibili da molte cognizioni locali senza rendere il mondo economicamente o computazionalmente ingestibile.

La fonte propone una **economia cognitiva**: usare capacità differenti per operazioni differenti, limitare le attivazioni superflue, recuperare soltanto memoria pertinente e misurare la qualità su scenari riproducibili.

## Elementi acquisiti

- [SRC-001] JSON valido non equivale a deliberazione coerente, situata o materialmente fattibile.
- [SRC-002] Il costo complessivo dipende da popolazione, frequenza delle attivazioni, dimensione del contesto, retry e profondità richiesta, non soltanto dai parametri del modello.
- [SRC-003] `AttentionSchedule` e retrieval selettivo sono parti centrali della scalabilità cognitiva.
- [SRC-004] Usare lo stesso modello e prompt per tutti può introdurre omogeneità comportamentale anche quando identità e memorie differiscono.
- [SRC-005] I modelli devono essere confrontati sugli stessi checkpoint per validità, conoscenza situata, memoria, piano, personalità, originalità, costo e latenza.
- [SRC-006] Il modello più grande non deve diventare automaticamente il modello universale: va impiegato soltanto dove misure ripetute mostrano un vantaggio.

## Correzioni e qualificazioni

- [QLF-001] La sequenza `3B → 7B → 14B → 32B` è un esempio illustrativo, non una tassonomia canonica. Parametri, quantizzazione e nome del modello non provano da soli una capacità.
- [QLF-002] La classificazione di “importanza” non può scegliere o correggere l'intenzione dell'abitante. Può selezionare provider, modello, budget e coda mantenendo invariati contesto privato e autonomia.
- [QLF-003] Emergenza, qualità psicologica e differenziazione devono essere valutate a posteriori; non vanno codificate come comportamenti desiderati nel runtime.
- [QLF-004] Compressione e sintesi delle esperienze sono operazioni semantiche: se modificano la mente richiedono provenienza generativa, verificabilità e conservazione delle fonti originali.
- [QLF-005] Un'integrazione cloud temporanea modifica privacy, dipendenza esterna, budgeting e failure model; richiede un ADR prima di entrare nel runtime.
- [QLF-006] Le misure attuali sul caso John supportano il problema generale, ma un singolo incidente non basta a stabilire percentuali come “90% quotidiano / 10% profondo”.

## Evidenza già disponibile

Il benchmark introdotto da ADR-0016 ha già confrontato Qwen 2.5 3B, Qwen 3 4B/8B e Phi su checkpoint reali. Ha mostrato che conformità JSON e fattibilità divergono nettamente. I risultati sono documentati in [Valutazione cognitiva John](../../evaluations/john-model-smoke-2026-08-13.md).

## Pagine derivate e correlate

- [Economia cognitiva multi-modello](../concepts/cnc-economia-cognitiva-multi-modello.md)
- [Cronista Silenzioso](../entities/ent-cronista-silenzioso.md)
- [ADR-0008 — Zero decisioni statiche](../../adr/adr-0008-zero-static-agent-decisions.md)
- [ADR-0009 — Priorità inferenza agent-first](../../adr/adr-0009-supervised-runtime-and-inference-priority.md)
- [ADR-0013 — Refactoring cognitivo ed emergenza](../../adr/adr-0013-cognitive-refactoring-and-emergence-analyzer.md)
- [ADR-0016 — Percezione somatica e valutazione](../../adr/adr-0016-embodied-somatic-perception-and-survival-deliberation.md)
