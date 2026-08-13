# CONCETTO: ECONOMIA COGNITIVA MULTI-MODELLO

- **Categoria**: Architettura cognitiva, inferenza e sperimentazione
- **Stato**: concetto candidato; richiede ADR per modifiche al runtime
- **Fonte**: [Brainstorming 09](../sources/src-brainstorming-09-cognitive-economy-and-model-tiers.md)

## Definizione

L'economia cognitiva è il principio secondo cui Newland assegna risorse di inferenza proporzionate alla natura dell'operazione, senza trasformare il router in autore del comportamento. Modelli, provider, budget e code possono differire; l'intenzione, l'interpretazione soggettiva e gli aggiornamenti mentali restano sempre prodotti generativi della mente incaricata.

Non è una gerarchia fissa basata sul numero di parametri. È una policy misurata e revisionabile fondata su capacità osservate nei benchmark di Newland.

## Dimensioni di routing candidate

- [ECO-001] **Rischio canonico**: quanto l'output può modificare corpo, risorse, relazioni o storia persistita.
- [ECO-002] **Profondità cognitiva**: quantità di memoria, ambiguità sociale, pianificazione e revisione del sé coinvolte.
- [ECO-003] **Urgenza**: tempo massimo accettabile prima che una mente riceva una risposta tecnica; urgenza elevata non implica automaticamente reasoning più lungo.
- [ECO-004] **Reversibilità**: il Cronista e gli analyzer producono artefatti derivati ripetibili; una deliberazione committata appartiene invece alla storia canonica.
- [ECO-005] **Privacy**: un provider cloud riceve contesto privato e richiede un confine dati esplicitamente approvato.
- [ECO-006] **Costo e quota**: token input/output, retry, latenza, cache, disponibilità e budget residuo devono essere telemetria operativa, mai percezione diegetica.

## Classi funzionali candidate

| Classe | Esempi | Requisito principale |
|---|---|---|
| Cognizione ordinaria | osservazione locale, azione quotidiana | bassa latenza e alta fattibilità situata |
| Cognizione riflessiva | conflitto, risonanza, revisione profonda di obiettivi o identità | coerenza causale e memoria di lungo periodo |
| Riparazione generativa | schema o riferimenti non validi | correggere la stessa proposta senza introdurre una policy sostitutiva |
| Cronaca derivata | selezione e narrazione di eventi committati | grounding, qualità italiana e nessuna interferenza con le menti |
| Compressione mnemonica | raggruppamento o sintesi di esperienze | fonti conservate, provenienza e assenza di significati inventati |
| Valutazione offline | replay di checkpoint, analisi di emergenza | riproducibilità e zero scritture canoniche |

Queste classi non autorizzano una pipeline in cui un modello economico decide sommariamente e uno costoso ratifica. Ogni deliberazione canonica deve avere una sola provenienza generativa auditabile; validatore e arbitro possono respingere, non riscrivere.

## Invarianti di autonomia

- [AUT-001] Il router sceglie capacità di calcolo, non azione, priorità psicologica o significato dell'esperienza.
- [AUT-002] A parità di attivazione, ogni provider riceve lo stesso confine percettivo e non ottiene conoscenza globale aggiuntiva.
- [AUT-003] Failover e retry restano generativi; nessun tier introduce un comportamento statico.
- [AUT-004] Un errore tecnico o una coda non devono far trascorrere tempo diegetico né peggiorare il corpo.
- [AUT-005] Il routing effettivo, i tentativi, il modello, i token e la latenza devono essere registrati nella provenienza operativa.
- [AUT-006] Le differenze tra modelli non devono essere usate intenzionalmente per fabbricare personalità; la diversità degli abitanti deve emergere da identità, storia, percezione e decisioni proprie.

## Rapporto con il Cronista

Il Cronista è downstream, reversibile e non canonico. ADR-0009 gli assegna già una classe logica distinta, `chronicle`, ma la serve attraverso la stessa ammissione seriale usata dalla classe `agent`. Una generazione narrativa può essere differita o cancellata e ripetuta senza alterare Newland; una deliberazione agente non può essere interrotta dopo l'inizio della transazione cognitiva.

La proposta candidata è più forte della separazione logica esistente: dare al Cronista una corsia d'inferenza o un provider indipendente, così che la prosa derivata non consumi la capacità critica delle menti. Questa modifica estende ADR-0009 e richiede un nuovo ADR con misure di memoria, concorrenza, quota e failure isolation. Non è autorizzata da questa pagina concettuale.

## Programma sperimentale

Ogni candidato deve essere valutato sugli stessi contesti sanitizzati e almeno sulle seguenti metriche:

- conformità JSON e schema;
- riferimenti limitati a percezioni, memorie e affordance realmente disponibili;
- tasso di accettazione da parte dell'arbitro;
- riconoscimento non prescrittivo delle cause corporee;
- coerenza di piani, convinzioni e personalità nel tempo;
- ripetizione, omogeneità tra agenti e conoscenze impossibili;
- token, retry, latenza media/p95 e costo;
- comportamento in indisponibilità senza avanzamento diegetico accidentale.

Una promozione di modello o policy richiede più campioni e scenari; JSON valido o un singolo esito riuscito non bastano.

## Decisioni ancora necessarie

- [ADR-REQ-001] Provider cloud temporaneo, confine dei dati privati, gestione dei segreti, quota e arresto di spesa.
- [ADR-REQ-002] Corsie d'inferenza o provider indipendenti per mente, Cronista e analisi; regole di cancellazione dei soli workload derivati.
- [ADR-REQ-003] Tassonomia minima del routing e criteri misurati di promozione/declassamento dei modelli.
- [ADR-REQ-004] Semantica temporale degli errori tecnici e dei `CognitionDeferred`.

## Collegamenti

- [Contratti del runtime](../../architecture/agent-runtime-contracts.md)
- [Valutazione cognitiva John](../../evaluations/john-model-smoke-2026-08-13.md)
- [ADR-0008](../../adr/adr-0008-zero-static-agent-decisions.md)
- [ADR-0009](../../adr/adr-0009-supervised-runtime-and-inference-priority.md)
- [ADR-0013](../../adr/adr-0013-cognitive-refactoring-and-emergence-analyzer.md)
- [ADR-0016](../../adr/adr-0016-embodied-somatic-perception-and-survival-deliberation.md)
