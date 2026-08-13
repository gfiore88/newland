# FONTE: BRAINSTORMING 11 — ATTENZIONE COGNITIVA SELETTIVA

- **File grezzo**: [raw-brainstorming-11-selective-cognitive-attention.md](../../raw/raw-brainstorming-11-selective-cognitive-attention.md)
- **Data ingest**: 2026-08-13
- **Natura**: direzione architetturale fornita da Giovanni Fiore
- **Decisione candidata**: [ADR-0021 proposto](../../adr/adr-0021-selective-cognitive-attention-and-progressive-deliberation.md)

## Tesi centrale

Il contesto d’inferenza non deve coincidere con la memoria totale del Newlander.
Deve rappresentare la sua attenzione corrente: stato e percezioni locali,
obiettivi attivi, affordance immediatamente pertinenti e soltanto le memorie
richiamate dalla situazione o dalla mente stessa.

## Distinzioni operative

- [DST-001] **Memoria totale**: archivio persistente di ciò che la mente può conoscere; non viene serializzato integralmente.
- [DST-002] **Memoria attiva**: piccolo working set portato nella deliberazione corrente.
- [DST-003] **Percezione**: eventi e affordance accessibili nell’istante, indipendenti da ciò che diventa saliente.
- [DST-004] **Contesto d’inferenza**: intersezione situata fra focus, percezione, memoria recuperata e vincoli applicabili.

## Implicazioni per Newland

- [IMP-001] Il runtime attuale limita già percezioni e affordance al luogo, ma `build_private_context()` include ancora intere collezioni di beliefs, relazioni, ruoli e anamnesi e fino a dodici gruppi di memoria.
- [IMP-002] Il routing `ordinary/reflective` sceglie oggi un tier di modello; non costruisce livelli diversi di attenzione.
- [IMP-003] La selezione del contesto non deve trasformarsi in selezione dell’azione. Il runtime può recuperare e validare conoscenza, ma non decidere comportamento o motivazione.
- [IMP-004] ADR-0008 consente di eseguire deterministicamente la fisica di un’intenzione già generata, ma vieta nuove reazioni comportamentali statiche. Le “reazioni automatiche” richiederebbero quindi una futura decisione esplicita oppure una policy procedurale precedentemente generata dalla mente.
- [IMP-005] L’espansione progressiva può essere richiesta dalla mente con un output generativo non comportamentale, oppure imposta come minimo di sicurezza da segnali canonici quali disputa attiva, risonanza, rischio corporeo e fallimenti ripetuti.

## Formula candidata

```text
contesto = sé minimo stabile
         + trigger di attenzione
         + stato e percezioni locali salienti
         + obiettivi/piani immediatamente attivi
         + memoria attiva recuperata
         + vincoli delle affordance esposte
```

La memoria totale resta disponibile per espansione, non residente nella
coscienza a ogni passo.
