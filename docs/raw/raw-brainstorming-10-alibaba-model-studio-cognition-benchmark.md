# BRAINSTORMING 10 — ALIBABA MODEL STUDIO E BENCHMARK COGNITIVO CLOUD

> Fonte grezza acquisita il 2026-08-13. Il contenuto seguente è conservato come proposta e non costituisce una decisione architetturale approvata. Prezzi, modelli e quote sono informazioni temporanee da riverificare prima dell'uso.

Sì. **Per Newland il free tier ufficiale Qwen/Alibaba Model Studio è particolarmente interessante**, forse più di quanto ti dicevo prima su Groq, perché puoi confrontare modelli Qwen molto grandi con il Qwen locale mantenendo la stessa “famiglia” di modello.

Ho controllato le condizioni attuali: per i nuovi utenti, nella regione **Singapore / International**, Alibaba Model Studio assegna quote gratuite per vari modelli.

### Quelli che proverei su Newland

In particolare hai questi candidati:

| Modello | Modalità | Free quota |
|---|---|---:|
| **Qwen3-8B** | Thinking + normale | 1M token |
| **Qwen3-14B** | Thinking + normale | 1M token |
| **Qwen3-32B** | Thinking + normale | 1M token |
| **Qwen3-30B-A3B** | Thinking + normale | 1M token |
| **Qwen3-30B-A3B-Thinking** | solo reasoning | 1M token |
| **Qwen3-235B-A22B-Thinking** | solo reasoning | **1M token** |
| **Qwen3-Next-80B-A3B-Thinking** | solo reasoning | **1M token** |

Sono quote **per modello**, non un singolo milione condiviso fra tutti questi modelli.

Ed è questo che lo rende molto appetibile per il tuo caso.

### Io proverei immediatamente il 235B

`qwen3-235b-a22b-thinking-2507`

Perché qui stiamo parlando di un modello **235B MoE**, in modalità thinking, che ovviamente non potresti ragionevolmente far girare sulla normale macchina sulla quale stai eseguendo Newland.

E hai **1 milione di token gratuiti** per sperimentare.

Non lo userei per tutti i Newlander.

Lo userei come **upper bound cognitivo**.

In pratica:

```text
             STESSO NEWLANDER
                    │
             CognitionContext
                    │
       ┌────────────┴────────────┐
       ↓                         ↓

 Qwen2.5 3B locale       Qwen3 235B Thinking
      Ollama                Alibaba Cloud
       │                         │
       ↓                         ↓

 CognitionResult          CognitionResult

       └────────────┬────────────┘
                    ↓

                 CONFRONTO
```

E qui secondo me potresti avere risultati estremamente interessanti.

Immagina una situazione:

> Alessio ricorda che Luca gli aveva promesso delle bacche.
> Luca non gliele ha portate.
> Alessio ha però osservato Luca aiutare Maria.
> Alessio ha fame.
> Luca è presente nello stesso luogo.

Il 3B potrebbe semplicemente fare:

> “Chiedo a Luca le bacche.”

Il **235B thinking** potrebbe invece decidere:

> “Non lo accuso immediatamente. Il fatto che abbia aiutato Maria potrebbe significare che è stato occupato. Gli ricordo la promessa e osservo la sua reazione prima di modificare la mia fiducia nei suoi confronti.”

E quindi produrre aggiornamenti differenti di:

```text
belief
trust
tension
goal
plan
intention
```

**Questa differenza è esattamente ciò che dobbiamo misurare.**

### Ma c'è un modello che mi incuriosisce ancora di più

Per Newland proverei anche:

**`qwen3-next-80b-a3b-thinking`**

È un 80B MoE con circa 3B parametri attivi. Anche questo ha **1M token gratuiti** nel deployment International.

Concettualmente è interessantissimo per te perché rappresenta proprio la filosofia che potrebbe servire a Newland:

> **modello enorme come capacità complessiva, ma pochi parametri attivi per inferenza.**

Se la qualità cognitiva fosse vicina al 235B ma il costo/velocità molto migliori, potrebbe essere un candidato fantastico per una futura popolazione numerosa.

### E sì: hanno Thinking Mode

La documentazione Alibaba distingue esplicitamente output normale e **Thinking mode / chain of thought + answer** per i modelli che lo supportano.

Ma ribadisco quello che dicevo prima: **non salverei la chain-of-thought come memoria del Newlander**.

Farei:

```text
PRIVATE MODEL REASONING
        ↓
        ↓
CognitionResult strutturato
        ↓
 ┌──────┼────────┐
 ↓      ↓        ↓
belief memory  intention
 ↓      ↓        ↓
       Newland
```

Il ragionamento serve al modello per **pensare meglio**.

La coscienza persistente di Newland rimane invece quella che hai progettato tu.

### C'è anche una funzione molto utile

Alibaba permette di abilitare **“Free Quota Only”**.

Quando finisci la quota gratuita, invece di iniziare a fatturarti le chiamate, l'API si ferma e restituisce un `403 AllocationQuota.FreeTierOnly`.

**La attiverei assolutamente durante lo sviluppo di Newland.**

Così puoi lasciare girare esperimenti senza rischiare:

> 40 Newlander × 8 ore → 💸💸💸

😄

---

Quindi sì: **io lo integrerei.**

E anzi farei una cosa precisa nel progetto:

```text
CognitionProvider
│
├── OllamaProvider
│    └── qwen2.5:3b
│
└── DashScopeProvider
     ├── qwen3-8b
     ├── qwen3-32b
     ├── qwen3-next-80b-a3b-thinking
     └── qwen3-235b-a22b-thinking
```

Poi aggiungerei una modalità:

```bash
newland benchmark-cognition
```

che prende **gli stessi 50-100 stati mentali reali di Newland** e li sottopone a tutti i modelli.

Secondo me questo esperimento va fatto **prima di decidere quale modello cloud integrare stabilmente**.

Perché potrebbe rispondere alla domanda più importante che abbiamo appena individuato:

> **Quanto migliora realmente un Newlander passando da un 3B locale a un 32B, 80B o 235B con reasoning?**

Se il salto 3B → 235B fosse enorme, sappiamo che la cognition è attualmente model-limited. Se invece fosse sorprendentemente piccolo, sarebbe un risultato ancora più interessante: significherebbe che **l'architettura cognitiva di Newland riesce a ottenere comportamenti complessi anche da modelli piccoli**.

E per il tuo progetto, questa seconda eventualità sarebbe una gran bella notizia.
