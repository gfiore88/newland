# CONCETTO: ATTENZIONE COGNITIVA SELETTIVA

- **Stato**: concetto candidato
- **Fonte**: [Brainstorming 11](../sources/src-brainstorming-11-selective-cognitive-attention.md)
- **ADR candidata**: [ADR-0021](../../adr/adr-0021-selective-cognitive-attention-and-progressive-deliberation.md)

## Definizione

L’attenzione cognitiva selettiva è la costruzione di un working set privato e
situato per una singola attivazione. Non cancella conoscenza e non sceglie il
comportamento: determina quale porzione accessibile della mente e del mondo è
portata alla deliberazione generativa.

## Invarianti

- [INV-001] Nessuna informazione viene resa accessibile a un agente che non la possiede o non può percepirla.
- [INV-002] La mancata inclusione nel working set non cancella né modifica memoria, relazione, belief o piano persistente.
- [INV-003] Il selettore non assegna azioni, motivazioni, interpretazioni o priorità psicologiche.
- [INV-004] La mente può chiedere più contesto quando riconosce incertezza, conflitto, rischio o conseguenze rilevanti.
- [INV-005] I segnali canonici critici impongono un livello minimo di contesto, ma non una risposta comportamentale.
- [INV-006] Ogni inferenza registra livello, ragioni di promozione e identificatori delle fonti incluse senza persistere prompt privati.

## Livelli candidati

- [LVL-000] **Procedurale**: il runtime completa fisica e durata di un’intenzione già scelta; nessuna nuova scelta.
- [LVL-001] **Focale**: sé minimo, trigger, stato locale saliente, percezioni nuove e affordance immediate.
- [LVL-002] **Contestuale**: aggiunge obiettivi, piani, impegni, relazioni e memorie direttamente pertinenti.
- [LVL-003] **Riflessivo**: amplia memoria a lungo termine, contraddizioni, biografia soggettiva e dinamiche sociali complesse.

## Promozione

La promozione può derivare da segnali canonici non comportamentali o da una
richiesta generativa della mente. Il runtime recupera soltanto categorie e fonti
accessibili, ripresenta la decisione e non suggerisce quale azione scegliere.
