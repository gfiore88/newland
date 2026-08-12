---
name: adr-creator
description: Skill per la ricerca, analisi e formalizzazione di Architecture Decision Records (ADR) in docs/adr/ prima di avviare qualsiasi task di sviluppo o modellazione.
---

# ADR Creator Skill

## Scopo
Garantire che **ogni decisione architetturale o metodologica** sia preceduta da un ADR formale salvato in `docs/adr/`. Nessun task viene eseguito se non è legato a un ADR approvato.

## Requisiti di Input
1. Descrizione del task o della decisione da prendere.
2. Contesto tecnico e vincoli di progetto.

## Procedura Operativa

1. **Ricerca Preventiva (RAG)**:
   - Ispezionare `docs/adr/` per verificare la presenza di ADR precedenti correlati.
   - Consultare la documentazione RAG in `docs/` per assicurare allineamento.

2. **Assegnazione Numero Sequenziale**:
   - Identificare il numero dell'ultimo ADR in `docs/adr/` (es. `0001`).
   - Incrementare il progressivo (es. `0002`).

3. **Stesura dell'ADR**:
   - Compilare il file usando il formato Nygard definito in `docs/adr/0000-adr-template.md`.
   - Sezioni obbligatorie:
     - Titolo e Metadati (Stato, Data, Autori, Ref Task).
     - Contesto e Problema.
     - Opzioni Considerate (almeno 2 alternative).
     - Decisione e Motivazione.
     - Conseguenze Positive e Negative/Rischi.
     - Compliance & RAG Impact.

4. **Sottomissione per Approvazione**:
   - Presentare l'ADR all'utente per la revisione ed attendere l'approvazione formale.

## Output Prodotto
- Nuovo file `docs/adr/XXXX-titolo-decisione.md`.
