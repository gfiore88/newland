# WORKSPACE AGENTIC DIRECTIVES & GOVERNANCE RULES

> [!CRITICAL]
> **RELAZIONE DI GOVERNANCE OBBLIGATORIA PER TUTTE LE INTERAZIONI**
> Questo file stabilisce le regole inviolabili per tutti gli agenti operanti nel progetto Newland.

---

## 1. Regola Inviolabile: ADR Obbligatorio (Nygard Rules & Awesome Copilot Skill)
- **TUTTE le decisioni architetturali, metodologiche o tecniche DEVONO diventare un ADR.**
- **NESSUN TASK può essere avviato o eseguito se prima non è stato studiato, formalizzato e approvato in un ADR presente in `docs/adr/`.**
- **Skill Obbligatoria**: Usare sempre la skill `create-architectural-decision-record` ([skills/create-architectural-decision-record/SKILL.md](file:///Users/giovannifiore/.gemini/antigravity-ide/scratch/newland/skills/create-architectural-decision-record/SKILL.md)).
- **Convenzione Naming Nygard**: I file ADR devono essere salvati come `docs/adr/adr-NNNN-[title-slug].md` (es. `adr-0001-agentic-governance-and-adr-workflow.md`).
- **Formattazione Coded Points**: Includere sempre i coded bullet points (es. `[GOV-001]`, `[DRV-001]`, `[POS-001]`) per garantire la leggibilità sia umana che automatizzata dagli agenti AI.

---

## 2. Struttura del RAG e della Conoscenza
- **TUTTA la conoscenza, la documentazione e il RAG del progetto risiedono esclusivamente sotto la cartella `docs/` nella root di progetto.**
- Consultare sempre l'indice RAG in [docs/README.md](file:///Users/giovannifiore/.gemini/antigravity-ide/scratch/newland/docs/README.md).

---

## 3. Pattern degli Agenti e delle Skill
- **Prompting & Ruoli Agenti**: Seguire rigorosamente gli standard di [Awesome Copilot](https://github.com/github/awesome-copilot).
- **Skill Specification**: Tutte le skill devono seguire il formato di [Addy Osmani Agent Skills](https://github.com/addyosmani/agent-skills) (`skills/<skill-name>/SKILL.md`).

---

## 4. Governed Agent Self-Annealing (Pattern Giovanni Fiore)
Gli agenti devono imparare dai propri errori e perfezionare le proprie istruzioni tra run successive secondo il pattern [Governed Agent Self-Annealing](https://gist.github.com/gfiore88/c0dff64209c0e8d94a0654dd1b74399e):
- Formulare una `Annealing Proposal` in formato diff minimale.
- Attendere l'approvazione umana prima di applicare modifiche permanenti alle direttive.
