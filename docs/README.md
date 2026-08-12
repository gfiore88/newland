# INDEX RAG: KNOWLEDGE BASE PROGETTO NEWLAND

> [!IMPORTANT]
> Tutta la conoscenza, il RAG e le decisioni del progetto Newland sono organizzate ed accessibili esclusivamente sotto questa cartella `docs/`.

---

## Struttura della Conoscenza (RAG Tree)

```
docs/
├── adr/                                     <-- Architecture Decision Records (ADR Nygard Rules)
│   ├── 0000-adr-template.md                 <-- Template Nygard Standard
│   └── adr-0001-agentic-governance-and-adr-workflow.md <-- ADR-0001 (Governance, RAG, Self-Annealing)
├── domain/                                  <-- Conoscenza di Dominio (Universo Parallelo)
│   └── newland-universe-spec.md             <-- Matrice Fisica, Assiomi, Costituzione
├── architecture/                            <-- Documentazione Architetturale Sistemi
└── agents/                                  <-- Specifiche Agenti (Awesome Copilot & Addy Osmani)
```

---

## Indice dei File RAG

| Categoria | File RAG | Descrizione |
|---|---|---|
| **Governance** | [adr-0001-agentic-governance-and-adr-workflow.md](file:///Users/giovannifiore/.gemini/antigravity-ide/scratch/newland/docs/adr/adr-0001-agentic-governance-and-adr-workflow.md) | Nygard ADR-0001: Regola dell'ADR obbligatorio, struttura `docs/` RAG, Self-Annealing. |
| **Dominio** | [newland-universe-spec.md](file:///Users/giovannifiore/.gemini/antigravity-ide/scratch/newland/docs/domain/newland-universe-spec.md) | Specifica del nuovo universo parallelo (Fisica, Diritto, Tabula Rasa). |
| **Skill ADR** | [create-architectural-decision-record/SKILL.md](file:///Users/giovannifiore/.gemini/antigravity-ide/scratch/newland/skills/create-architectural-decision-record/SKILL.md) | Skill Awesome Copilot per la stesura degli ADR secondo le leggi di Nygard. |
| **Direttiva Workspace** | [AGENTS.md](file:///Users/giovannifiore/.gemini/antigravity-ide/scratch/newland/AGENTS.md) | Direttiva di progetto da seguire SEMPRE ad ogni messaggio in chat. |

---

## Regole di Stesura ADR
1. **Skill Obbligatoria**: Usare `create-architectural-decision-record` ([skills/create-architectural-decision-record/SKILL.md](file:///Users/giovannifiore/.gemini/antigravity-ide/scratch/newland/skills/create-architectural-decision-record/SKILL.md)).
2. **Convenzione Naming**: Salvataggio in `docs/adr/adr-NNNN-[title-slug].md`.
3. **Leggi di Nygard**: Titolo, Stato, Contesto, Decisione (voce attiva), Conseguenze bilanciate (positive e rischi con mitigazione).
4. **Coded Points**: Usare codici per i bullet point (`[GOV-001]`, `[DRV-001]`, `[POS-001]`) per l'ispezione automatizzata degli agenti AI.
