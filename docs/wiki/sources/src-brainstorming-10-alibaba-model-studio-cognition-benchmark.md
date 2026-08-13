# FONTE: BRAINSTORMING 10 — ALIBABA MODEL STUDIO E BENCHMARK COGNITIVO CLOUD

- **File grezzo**: [raw-brainstorming-10-alibaba-model-studio-cognition-benchmark.md](../../raw/raw-brainstorming-10-alibaba-model-studio-cognition-benchmark.md)
- **Data ingest e verifica**: 2026-08-13
- **Natura**: proposta sperimentale con dati commerciali temporanei
- **Decisione derivata**: [ADR-0018 proposto](../../adr/adr-0018-bounded-cloud-cognition-benchmark.md)

## Tesi centrale

Alibaba Model Studio può fornire un upper bound cloud della capacità cognitiva mantenendo la famiglia Qwen. Il confronto utile non consiste nel sostituire subito la mente locale, ma nel sottoporre gli stessi snapshot privati, non canonici e sanitizzati a modelli differenti, misurando il vantaggio effettivo rispetto a costo e latenza.

## Elementi verificati su fonti ufficiali

- [VRF-001] Il free tier per nuovi utenti riguarda la regione Singapore e il deployment International; le quote e la loro validità devono essere ricontrollate al momento dell'esperimento.
- [VRF-002] Al 2026-08-13 la tabella ufficiale riporta 1 milione di token per ciascuno dei candidati citati, inclusi `qwen3-8b`, `qwen3-14b`, `qwen3-32b`, `qwen3-30b-a3b`, `qwen3-next-80b-a3b-thinking` e `qwen3-235b-a22b-thinking-2507`.
- [VRF-003] `qwen3-next-80b-a3b-thinking` e `qwen3-235b-a22b-thinking-2507` sono modelli thinking-only; altri Qwen3 elencati supportano modalità normale e thinking.
- [VRF-004] `Free Quota Only`, quando abilitato, arresta le invocazioni alla fine della quota e restituisce `403 AllocationQuota.FreeTierOnly`.
- [VRF-005] La documentazione generale indica una validità variabile da 30 a 90 giorni e annuncia 90 giorni per le nuove attivazioni dal 2026-09-08. Alla data dell'ingest, la console dell'account resta quindi la fonte operativa per residuo e scadenza effettivi.
- [VRF-006] La pagina del `qwen3-235b-a22b-thinking-2507` dichiara non supportati structured outputs e function calling: ottenere un `CognitionResult` JSON valido deve essere misurato, non presunto.

## Correzioni e qualificazioni

- [QLF-001] Un milione di token non equivale a un milione di decisioni. Input, output, reasoning e retry consumano la quota; un benchmark da 50–100 snapshot con più campioni può superarla.
- [QLF-002] Il pilot deve partire con 10–20 snapshot e limiti locali di richieste/token, poi espandersi soltanto dopo aver misurato il consumo reale.
- [QLF-003] I conteggi parametrici e MoE non sono proxy sufficienti di qualità o velocità. Sono proprietà del candidato da verificare sul contratto cognitivo di Newland.
- [QLF-004] Nessun chain-of-thought deve diventare memoria, evento o motivazione canonica. Si persistono soltanto risposta finale strutturata, metadati di provenienza e metriche consentite.
- [QLF-005] Gli snapshot possono contenere identità o biografie fornite dall'utente. L'uso cloud richiede sanitizzazione, minimizzazione e consenso architetturale esplicito.
- [QLF-006] Il free tier è adatto alla qualificazione offline, non dimostra sostenibilità economica del mondo live dopo scadenza o esaurimento.

## Fonti ufficiali verificate

- [Free quota per nuovi utenti](https://www.alibabacloud.com/help/en/model-studio/new-free-quota)
- [Prezzi e quote dei modelli](https://www.alibabacloud.com/help/en/model-studio/model-pricing)
- [Uso dei modelli deep-thinking](https://www.alibabacloud.com/help/en/model-studio/deep-thinking)
- [Scheda qwen3-235b-a22b-thinking-2507](https://www.alibabacloud.com/help/en/model-studio/qwen3-235b-a22b-thinking-2507)

## Pagine correlate

- [Economia cognitiva multi-modello](../concepts/cnc-economia-cognitiva-multi-modello.md)
- [Valutazione cognitiva John](../../evaluations/john-model-smoke-2026-08-13.md)
- [ADR-0008 — Zero decisioni statiche](../../adr/adr-0008-zero-static-agent-decisions.md)
- [ADR-0009 — Inferenza agent-first](../../adr/adr-0009-supervised-runtime-and-inference-priority.md)
- [ADR-0016 — Valutazione cognitiva](../../adr/adr-0016-embodied-somatic-perception-and-survival-deliberation.md)
