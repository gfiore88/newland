# ENTITÀ: MORTALITÀ E ISTINTO DI SOPRAVVIVENZA

- **Categoria**: Fisiologia & Psicologia In-Game
- **Stato**: Implementato

## La Condizione Letale (Permadeath)
Newland non è un sandbox narrativo protetto, ma un ambiente spietato sottoposto alle ferree regole dell'Omeostasi.
I parametri vitali degli agenti (Energia, Fame, Sete) evolvono deterministicamente nel ciclo fisiologico (`PhysiologySystem`).
Quando un bisogno raggiunge la soglia fatale (Energia = 0.0, oppure Fame/Sete = 1.0), il runtime comincia a contare soltanto il tempo realmente trascorso oltre quella soglia. Esaurimento, inedia e disidratazione hanno contatori separati e replayable. Superato il limite configurato, `AgentDied` registra le cause precise che hanno maturato l'esposizione.

## Conseguenze Sistemiche
La morte a Newland è **permanente e irreversibile**:
1. L'agente viene contrassegnato con `is_dead = True` e disattivato (`active = False`).
2. Lo scheduler del motore (Adjudicator) esclude per sempre l'agente dal loop cognitivo: non formulerà più pensieri, intenzioni o riflessioni.
3. Le sue spoglie restano nella mappa (nel `MaterialAgentState`), fungendo da monito o potenziale risorsa per la sopravvivenza altrui.

## Percezione somatica e autonomia
Il runtime non possiede un istinto statico e non scavalca gli obiettivi dell'agente. La mente riceve una proiezione privata del corpo che esplicita condizione, direzione, durata e cause del pericolo senza prescrivere `rest`, `gather`, `consume` o qualsiasi altra azione.

Finché una condizione critica persiste, lo scheduler richiama più spesso l'attenzione dell'agente. Ogni risposta resta però un'intenzione generata in tempo reale dal modello e attraversa il normale arbitraggio del mondo. Un agente informato può quindi scegliere male, perseverare in altri fini, rischiare o morire: il motore garantisce coerenza causale, non sopravvivenza.

Le azioni hanno inoltre durata canonica. Il corpo continua a evolvere mentre l'azione è in corso; gli effetti materiali vengono applicati solo al completamento e un decesso o la perdita di una precondizione interrompe l'azione senza attribuirle un risultato mai avvenuto.

## Riferimenti
- ADR: [adr-0008-zero-static-agent-decisions.md](../../adr/adr-0008-zero-static-agent-decisions.md)
- ADR: [adr-0016-embodied-somatic-perception-and-survival-deliberation.md](../../adr/adr-0016-embodied-somatic-perception-and-survival-deliberation.md)
- Concetto correlato: [cnc-omeostasi-planetaria.md](file:///Users/giovannifiore/Desktop/newland/docs/wiki/concepts/cnc-omeostasi-planetaria.md)
