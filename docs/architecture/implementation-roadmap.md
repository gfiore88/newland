# NEWLAND ENGINE: ROADMAP IMPLEMENTATIVA

## Milestone 1 — Vertical slice agentico

- [M01-001] Event store SQLite e replay dello stato.
- [M01-002] Due Newlander, un luogo iniziale e percezioni isolate.
- [M01-003] Ciclo cognitivo interamente generativo con Ollama, riparazione, failover fra modelli e differimento esplicito in caso di indisponibilità.
- [M01-004] Intenzioni strutturate e arbitraggio delle azioni.
- [M01-005] Conversazione autonoma persistita e verificabile da CLI.

## Milestone 2 — Mente persistente

- [M02-001] Consolidamento episodico, beliefs e riflessioni generative. **Implementato.**
- [M02-002] Emozioni e relazioni dinamiche generate dalla mente. **Implementato.**
- [M02-002A] Energia, fame e sete come stimoli corporei canonici non prescrittivi. **Implementato.**
- [M02-003] Piani, impegni, agenda autonoma persistente e ricostruzione dopo il riavvio. **Implementato.**
- [M02-004] Routing fra modello rapido e modello riflessivo.

## Milestone 3 — Territorio e società

- [M03-001] Grafo spaziale, movimento, risorse e attività. **Implementato.**
- [M03-002] Arrivi, lingue, competenze e gruppi familiari. **Implementato.**
- [M03-003] Cooperazione, conflitti e ruoli emergenti. **Implementato.**
- [M03-004] Nodi di risonanza, flashback e anamnesi. **Implementato.**

## Milestone 4 — Observer WebGL obbligatorio

- [M04-001] Snapshot HTTP e stream SSE degli eventi canonici.
- [M04-002] Mappa 2.5D PixiJS con terreno, luoghi e Newlander.
- [M04-003] Diario del Cronista Silenzioso e Console dell'Architetto.
- [M04-004] Pausa visiva, scrub e replay senza fermare il motore.

## Definition of Done globale

Newland è funzionante quando il runtime può avanzare autonomamente per periodi prolungati, preservare menti distinte e vincoli fisici, riavviarsi senza perdita di identità, spiegare gli eventi tramite audit trail e alimentare la UI WebGL esclusivamente da stato canonico persistito.
