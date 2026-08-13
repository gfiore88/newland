---
id: adr-0015
title: "Procedural Biome Rendering Engine per Mappa WebGL"
status: "Proposed"
date: "2026-08-13"
authors: ["Agent AI", "Giovanni Fiore"]
tags: ["architecture", "webgl", "procedural-generation", "ui"]
---

# ADR-0015: Procedural Biome Rendering Engine per Mappa WebGL

## Context & Problem Statement
Nei mockup della UI (ADR-0014), la mappa WebGL di PixiJS viene rappresentata come un dipinto 2D dettagliato (foreste, campi aperti, specchi d'acqua, radure) che identifica in maniera naturalistica i diversi biomi del mondo. Tuttavia, poiché Newland è un mondo emergente in cui i territori verranno scoperti o generati dinamicamente durante la simulazione, non è scalabile o possibile disegnare "a mano" sfondi statici (PNG) per l'intera mappa. 

Per risolvere questo limite, è necessario sviluppare un **Procedural Biome Rendering Engine** in `map-scene.ts` (o classe dedicata) capace di prendere l'elenco dei nodi forniti dal backend e renderizzare un bioma grafico proceduralmente in base alla tipologia semantica o morfologica del luogo, sfruttando geometrie, noise, e particelle/pattern su PixiJS.

## Decision Drivers
- [DRV-001] **Allineamento Visivo ai Mockup**: L'utente richiede esplicitamente che il mondo vivo assomigli ai file grafici di riferimento.
- [DRV-002] **Scalabilità ed Emergenza**: Il sistema non ha una mappa pre-impostata statica. Il mondo verrà generato progressivamente dalle azioni degli agenti o dall'Engine Python.
- [DRV-003] **Performance**: La mappa PixiJS deve rimanere fluida (60 FPS) anche se la foresta è composta da migliaia di alberi.

## Considered Alternatives

### Alternative 1: Texture statiche pre-generate (Tileset Mappato)
- **Description**: Assegnare un'immagine (sprite pre-renderizzato in PNG) per ogni tipologia di terreno (es. `forest.png`, `field.png`) sovrapposta alla mappa.
- **Rejection Rationale**: [REJ-001] Manca di organicità. Le congiunzioni tra zone diverse (es. bosco che sfuma in un campo) sarebbero nette e squadrate o difficili da raccordare (tileset 2D classico), tradendo il design vettoriale/organico.

### Alternative 2: Rendering Procedurale Server-Side
- **Description**: Generare un'immagine in Python (es. Pillow/Noise) sul backend per ogni regione e inviarla al frontend come texture base64.
- **Rejection Rationale**: [REJ-002] Costoso in termini di I/O. Interrompe il paradigma "read-only event sourcing" del frontend, aggiungendo pesantezza ai payload HTTP/SSE e rendendo lento lo zoom/pan in WebGL.

## Decision Outcome
Chosen Option: **Motore di Rendering Procedurale Client-Side (PixiJS)**

### Detailed Decision Points
- [DEC-001] **Layering Strutturale**: `map-scene.ts` introdurrà una fase di renderizzazione del *Bioma* basata su attributi inferiti dal nome o dai metadati del luogo (es. `bosco_*` = foresta, `campo_*` = radura, `sorgente_*` = specchio d'acqua).
- [DEC-002] **Disegno Basato su Particle/Shape**: Invece di caricare immagini esterne, useremo le primitive di Pixi (es. `Graphics`) e algoritmi matematici leggeri (Distribuzione Random Uniforme o Poisson Disk Sampling semplificato) per generare "alberi" (cerchietti scuri raggruppati), "fili d'erba" o "specchi d'acqua" (poligoni irregolari).
- [DEC-003] **Caching su Texture**: Per preservare le performance, le Graphics procedurali per l'intero bioma di un nodo verranno modellate una sola volta in un `Container` o su un `RenderTexture` (Caching), evitando che PixiJS ricalcoli ogni frame migliaia di vertici.

## Consequences

### Positive Consequences
- [POS-001] Il mondo apparirà organico e pittorico, allineandosi alle aspettative visive.
- [POS-002] Completa scalabilità: nuovi nodi genereranno automaticamente il proprio bioma in tempo reale.
- [POS-003] Animazioni locali possibili (es. acqua che ondeggia lievemente) sfruttando shader o oscillazioni, se desiderato.

### Negative Consequences & Risks
- [NEG-001] Aumento della complessità architetturale del frontend (`map-scene.ts` diventerà corposo). - **Mitigation**: Estrarre il motore in un modulo a sé stante (`biome-generator.ts`).
- [NEG-002] Rischio di cali prestazionali se non usiamo le ottimizzazioni corrette di PixiJS. - **Mitigation**: Utilizzare fortemente la generazione statica e l'impostazione `cacheAsBitmap = true` per i blocchi di bosco e terreno.

## Compliance & RAG Impact
- [CMP-001] **RAG Files Updated**: `docs/adr/adr-0015-procedural-biome-rendering-engine.md`, `docs/README.md`.
- [CMP-002] **Directives Updated**: N/A, segue gli standard architetturali definiti.
