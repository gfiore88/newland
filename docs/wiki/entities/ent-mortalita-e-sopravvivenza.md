# ENTITÀ: MORTALITÀ E ISTINTO DI SOPRAVVIVENZA

- **Categoria**: Fisiologia & Psicologia In-Game
- **Stato**: Implementato

## La Condizione Letale (Permadeath)
Newland non è un sandbox narrativo protetto, ma un ambiente spietato sottoposto alle ferree regole dell'Omeostasi.
I parametri vitali degli agenti (Energia, Fame, Sete) vengono erosi deterministicamente dal ciclo fisiologico (`PhysiologySystem`).
Se un bisogno vitale raggiunge la soglia fatale (Energia = 0.0, oppure Fame/Sete = 1.0) e vi permane senza essere soddisfatto per un periodo di stenti prolungato (circa 20 ore simulate in-game), il sistema emette inesorabilmente un evento `AgentDied`.

## Conseguenze Sistemiche
La morte a Newland è **permanente e irreversibile**:
1. L'agente viene contrassegnato con `is_dead = True` e disattivato (`active = False`).
2. Lo scheduler del motore (Adjudicator) esclude per sempre l'agente dal loop cognitivo: non formulerà più pensieri, intenzioni o riflessioni.
3. Le sue spoglie restano nella mappa (nel `MaterialAgentState`), fungendo da monito o potenziale risorsa per la sopravvivenza altrui.

## L'Istinto Primordiale
Per contrastare la morte, gli agenti sono dotati di un profondo istinto di sopravvivenza iniettato a livello di prompt cognitivo fondamentale.
Quando la loro vita è in grave pericolo, l'istinto scavalca forzatamente gli obiettivi sociali, le esplorazioni o le speculazioni filosofiche, costringendo l'LLM a dare priorità assoluta ad azioni vitali come `rest` (riposo), `gather` o `consume` (nutrimento). 
Se il modello sceglie comunque di ignorare l'istinto, il motore fisico non farà sconti e procederà all'eliminazione dell'agente.

## Riferimenti
- ADR: [adr-0008-zero-static-agent-decisions.md](file:///Users/giovannifiore/Desktop/newland/docs/adr/adr-0008-zero-static-agent-decisions.md) (L'istinto è generativo, non imposto via codice python)
- Concetto correlato: [cnc-omeostasi-planetaria.md](file:///Users/giovannifiore/Desktop/newland/docs/wiki/concepts/cnc-omeostasi-planetaria.md)
