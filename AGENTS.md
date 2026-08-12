# AGENTS.md - DIRECTIVE & OPERATING POLICY FOR NEWLAND PROJECT

> [!IMPORTANT]
> Questo file è la direttiva principale per tutti gli agenti operanti nella root del progetto `newland`.

## Principi Guida

1. **ADR Prima di Qualsiasi Task (Mandatory ADR - Nygard Laws & Awesome Copilot)**
   Prima di iniziare qualsiasi attività di sviluppo, refactoring, o modellazione:
   - Utilizzare la skill `create-architectural-decision-record` ([skills/create-architectural-decision-record/SKILL.md](file:///Users/giovannifiore/.gemini/antigravity-ide/scratch/newland/skills/create-architectural-decision-record/SKILL.md)).
   - Redigere l'ADR in `docs/adr/adr-NNNN-[title-slug].md` secondo le leggi di Nygard.
   - Usare punti elenco codificati (`[GOV-001]`, `[DRV-001]`, `[POS-001]`) per il parsing deterministico degli agenti.
   - Richiedere approvazione prima dell'esecuzione del task.

2. **RAG Centrato su `docs/`**
   Tutti i file di contesto, documentazione architetturale, capitolati e guide devono risiedere sotto `docs/` (Indice RAG: [docs/README.md](file:///Users/giovannifiore/.gemini/antigravity-ide/scratch/newland/docs/README.md)).

3. **Pattern Awesome Copilot & Agent Skills**
   - Agenti strutturati secondo gli standard [Awesome Copilot](https://github.com/github/awesome-copilot).
   - Skills definite in `skills/<skill_name>/SKILL.md` secondo [Addy Osmani Agent Skills](https://github.com/addyosmani/agent-skills).

4. **Self-Annealing (Giovanni Fiore Pattern)**
   Al termine di ogni task in cui si sia incontrato un ostacolo metodologico, formulare una **Proposta di Annealing** e attendere approvazione umana prima di aggiornare le direttive.
