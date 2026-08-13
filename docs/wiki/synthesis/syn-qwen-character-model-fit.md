# SINTESI: IDONEITÀ DEI MODELLI QWEN CHARACTER PER NEWLAND

- **Data verifica**: 2026-08-13
- **Stato**: valutazione candidata; nessun uso runtime approvato
- **Decisione correlata**: [ADR-0018 accettato](../../adr/adr-0018-bounded-cloud-cognition-benchmark.md)
- **Concetto**: [Economia cognitiva multi-modello](../concepts/cnc-economia-cognitiva-multi-modello.md)

## Verdetto

`qwen-flash-character` merita di entrare nel primo stadio del benchmark prima dei modelli thinking molto grandi. La specializzazione dichiarata per coerenza del personaggio, progressione tematica ed ascolto empatico coincide con alcune difficoltà centrali di Newland: continuità personale, interpretazione sociale e stabilità relazionale.

Non è però automaticamente una mente completa. I modelli Character non supportano structured output, function calling o thinking secondo il catalogo Alibaba. Possono quindi produrre dialoghi convincenti ma fallire schema, grounding materiale, pianificazione o aggiornamenti mentali. Devono essere valutati sull'intero `CognitionResult`, non soltanto sulla qualità della prosa.

## Confronto operativo verificato

| Candidato | Specializzazione dichiarata | Singapore: prezzo per 1M token input/output | Free quota indicata | Limite rilevante |
|---|---|---:|---:|---|
| `qwen-flash-character` | role-play, coerenza, progressione, empatia | `$0.05 / $0.40` | `1M` | nessuno structured output; nessun thinking |
| `qwen-plus-character` | stessa famiglia Character, capacità superiore da misurare | `$0.50 / $1.40` | `1M` | nessuno structured output; nessun thinking |
| `qwen3-32b` | generalista, normale o thinking | `$0.16 / $0.64` normale; `$0.64` thinking output | `1M` | non specializzato per continuità del personaggio |
| `qwen3-next-80b-a3b-thinking` | reasoning-only MoE | `$0.15 / $1.20` | `1M` | costo di reasoning e JSON da misurare |
| `qwen3-235b-a22b-thinking-2507` | upper bound reasoning-only | `$0.23 / $2.30` | `1M` | output thinking costoso; structured output non supportato |

Prezzi e quote sono fotografie del 2026-08-13 e devono essere ricontrollati nella console prima di ogni prova.

## Parametri, token e impatto reale

Il numero di parametri non moltiplica direttamente i token sottratti alla quota: una richiesta da 4.000 token input resta tale sia per Flash Character sia per 235B. Il 235B pesa indirettamente perché è thinking-only, può generare molti più token di reasoning/output, ha latenza maggiore e ha un prezzo post-quota molto più alto. Per questo il controllo deve agire sia sul numero di richieste sia sul totale `input + output + reasoning` riportato dal provider.

## Aspetti utili a Newland

- [FIT-001] **Continuità personale**: verificare se valori, temperamento e biografia influenzano decisioni successive senza trasformarsi in caricatura ripetitiva.
- [FIT-002] **Relazioni**: misurare promesse, fiducia, tensione, ambivalenza e interpretazioni alternative di uno stesso gesto.
- [FIT-003] **Conversazione situata**: valutare se una risposta porta avanti il tema sociale senza inventare conoscenze o fatti esterni alla percezione.
- [FIT-004] **Empatia non prescrittiva**: distinguere comprensione dello stato altrui da comportamento obbligatoriamente gentile o accomodante.
- [FIT-005] **Italiano**: la pagina ufficiale non stabilisce una garanzia specifica per la qualità italiana; deve essere una metrica esplicita.

## Rischi specifici

- [RSK-001] **Role-play apparente**: prosa credibile può mascherare intenzioni materialmente impossibili o aggiornamenti mentali incoerenti.
- [RSK-002] **Coaching del personaggio**: il formato raccomandato da Alibaba descrive dettagli, personalità, stile e scenario. Newland deve fornire identità e fatti, non istruzioni su come il personaggio dovrebbe comportarsi.
- [RSK-003] **Schema fragile**: l'assenza di structured output può aumentare repair e consumi. Nessuna estrazione deterministica deve inventare campi mancanti.
- [RSK-004] **Memoria duplicata**: la session cache migliora latenza e costo, ma non deve diventare memoria nascosta del Newlander. La mente canonica resta nel database e nel contesto esplicito.
- [RSK-005] **Documentazione incoerente sul contesto**: la pagina dedicata indica, per Singapore, `131072` token per Plus e `32768` per Flash; il catalogo generale mostra rispettivamente `32k` e `8k`. Il benchmark userà al massimo `8192` token e registrerà il limite effettivo restituito dal servizio.

## Strategia di consumo progressiva

Il milione di token è separato per modello, ma non va comunque consumato senza una domanda precisa.

1. **Compatibilità**: due snapshot per candidato, un campione, per provare accesso, italiano, JSON, usage accounting e sanitizzazione.
2. **Character-first**: baseline locale e `qwen-flash-character` su 10–20 snapshot sociali e corporei, massimo due campioni.
3. **Qualità incrementale**: `qwen-plus-character` e `qwen3-32b` soltanto sugli stessi casi se Flash mostra un segnale utile o un limite misurabile.
4. **Disagreement set**: 80B e 235B soltanto su 5–10 casi difficili nei quali candidati più economici divergono, falliscono il contratto o producono differenze psicologiche sostanziali.

Il 235B non funge da giudice né da risposta corretta. Resta un comparatore raro per stimare l'upper bound.

## Budget iniziale candidato

- [BGT-001] `qwen-flash-character`: massimo `250k` token nel pilot.
- [BGT-002] `qwen-plus-character`: massimo `200k` token, attivato dopo il gate Character-first.
- [BGT-003] `qwen3-32b`: massimo `200k` token come controllo generalista.
- [BGT-004] `qwen3-next-80b-a3b-thinking`: massimo `100k` token sul disagreement set.
- [BGT-005] `qwen3-235b-a22b-thinking-2507`: massimo `75k` token sul disagreement set.

Questi sono tetti locali inferiori alla quota, non obiettivi di consumo. Ogni stadio può fermarsi prima non appena la domanda sperimentale riceve una risposta sufficiente.

A titolo di ordine di grandezza, `75k` token permettono circa nove chiamate da `4k` input più `4k` output/reasoning; se il reasoning medio sale, le chiamate disponibili scendono. Il runner deve controllare il consumo dopo ogni risposta e non avviare una richiesta che potrebbe superare il residuo locale secondo il massimo output configurato.

## Session cache

La session cache sarà disabilitata nella prima valutazione di qualità per evitare stato remoto implicito e preservare la comparabilità dei replay. Potrà essere misurata successivamente soltanto come ottimizzazione di costo/latenza, con session ID espliciti e senza sostituire retrieval o memoria canonica.

## Fonti ufficiali

- [Qwen Character: capacità, contesti e uso](https://www.alibabacloud.com/help/en/model-studio/role-play)
- [Catalogo delle capacità dei modelli](https://www.alibabacloud.com/help/en/model-studio/text-generation-model)
- [Prezzi e quote](https://www.alibabacloud.com/help/en/model-studio/model-pricing)
- [Regole del free tier](https://www.alibabacloud.com/help/en/model-studio/new-free-quota)
