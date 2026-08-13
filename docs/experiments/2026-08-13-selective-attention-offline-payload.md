# Selective attention — offline payload measurement (2026-08-13)

## Scope

Misura offline e non canonica del primo vertical slice di ADR-0021. Il fixture
contiene due beliefs, due relazioni, due obiettivi, due piani, un impegno, due
memorie riferite a persone diverse, un ruolo interpretato, un frammento di
anamnesi e una riflessione. Non vengono effettuate chiamate Ollama o Alibaba.

## Comparison

| Componente | Full context v4 | Focal progressive | Riduzione |
|---|---:|---:|---:|
| Contesto privato JSON | 2.992 caratteri | 1.267 caratteri | 57,7% |
| Contratto risposta DashScope | 7.225 caratteri | 3.007 caratteri | 58,4% |
| Payload stimato `system + contract + context` | 14.052 caratteri | 8.458 caratteri | 39,8% |

Il contratto compatto è generato deterministicamente dallo stesso JSON Schema;
parser e validatore canonici non cambiano. La stima in caratteri non sostituisce
il conteggio tokenizer del provider e non prova qualità cognitiva.

## Behavioral checks

- [CHK-001] L1 conserva identità, valori, temperamento, corpo, percezioni e affordance locali ma non include collezioni mentali globali.
- [CHK-002] Una richiesta L2 ancorata a Bruno recupera relazione, memoria e piano di Bruno senza includere gli elementi riferiti a Cora o al bosco.
- [CHK-003] L3 rende nuovamente disponibile l'intera mente privata del fixture.
- [CHK-004] Anchor invisibili e richieste oltre L3 differiscono la cognizione senza produrre azioni statiche.
- [CHK-005] Il percorso resta disabilitato senza `--selective-attention` durante il canary.

## Outcome

Il gate statico di ADR-0021 è superato sul fixture: la riduzione del contesto L1
è maggiore del 40% e la riduzione del payload complessivo stimato è maggiore del
25%. Restano da misurare token reali, repair e continuità personale in un canary
esplicitamente autorizzato.
