# ADR-0014: Architettura e Design System dell'Observer UI

- **Stato**: Approvato
- **Data**: 2026-08-13
- **Autori**: Antigravity (Agent) / Giovanni Fiore
- **Riferimento Task**: Integrazione Proposal Visuale (docs/raw/newland-ui-proposal.md)

---

## 1. Contesto e Problema
L'utente ha fornito un dettagliato design proposal (con mockup visivi ad alta fedeltà) in `docs/raw/newland-ui-proposal.md`. Questo design stabilisce un'estetica premium e una chiara gerarchia dell'informazione strutturata su 3 livelli: Mondo Vivo (WebGL), Mente Privata (DOM) e Cronaca (DOM).

Attualmente la directory `ui/` possiede un'infrastruttura minimale che non riflette i design tokens (colori, tipografia) né il layering previsto (Canvas per il WebGL affiancato da pannelli sovrapposti DOM). È necessario standardizzare come implementare la nuova UI senza compromettere le performance dell'engine PixiJS né la leggibilità dei pannelli narrativi.

## 2. Opzioni Considerate
1. **Puro PixiJS (Canvas Only)**: 
   - Disegnare tutta l'interfaccia utente (testi, finestre, cronaca) dentro il canvas WebGL.
2. **Framework JS (React / Vue) + PixiJS**: 
   - Introdurre un framework frontend moderno per gestire lo stato della UI sovrapponendolo al canvas PixiJS.
3. **Vanilla JS DOM Overlay + PixiJS (Opzione Scelta)**:
   - Mantenere l'applicazione leggera in HTML/Vanilla JS, definendo un `div` contenitore per il canvas WebGL in *z-index* inferiore, sovrastato da una griglia CSS (Grid/Flexbox) per i pannelli DOM interattivi.

## 3. Decisione
Adottiamo l'opzione 3 (**Vanilla JS DOM Overlay + PixiJS**) rispettando l'estetica delineata nel `newland-ui-proposal.md`.
- **WebGL**: Il `MapScene` (PixiJS) gestirà esclusivamente gli aspetti del *Mondo vivo* (territorio, agenti in movimento, nodi di risonanza).
- **DOM Overlay**: Le schermate *Mente Privata* e *Cronaca* verranno renderizzate tramite normali elementi HTML posizionati in overlay (sfruttando flexbox/grid), garantendo massima leggibilità per la tipografia editoriale (Serif) ed elasticità del layout.
- **Design Tokens**: I token CSS (`--color-ink`, `--color-moss`, ecc.) definiti nella proposta saranno inseriti nel file `ui/src/style.css` come variabili globali e usati rigorosamente in tutti i componenti.

Questo approccio si allinea con la filosofia locale, leggera e indipendente dalle mode framework-specifiche, in coerenza con la natura di *strumento scientifico* dell'Observer.

## 4. Conseguenze
### Positive
- Rispetto totale della proposta visiva senza sovraccaricare il rendering loop di WebGL per il testo formattato.
- Accessibilità del testo (selezione, scorrimento, copia) nelle sezioni narrative (Cronaca e Memoria).
- Separazione logica netta tra codice di rendering del mondo (`map-scene.ts`) e codice della UI analitica.

### Negative / Rischi
- **Sincronizzazione Stato**: Occorrerà un robusto meccanismo di state-binding tra gli eventi SSE del backend, gli sprite PixiJS (per l'agente selezionato) e l'aggiornamento dei pannelli DOM.
- **Mitigazione**: Utilizzeremo architetture ad eventi in Vanilla JS (es. EventTarget locale o callback centralizzate per l'app state).

## 5. Compliance & RAG Impact
- **File RAG Interessati**: `docs/raw/newland-ui-proposal.md`, `docs/README.md`.
- **Direttive Interessate**: Aggiorna lo stack architetturale dell'Observer, rendendolo conforme al paradigma "Strumento Scientifico + Atlante Vivo".
