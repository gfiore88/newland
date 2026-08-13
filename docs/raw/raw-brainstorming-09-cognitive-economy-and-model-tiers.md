# BRAINSTORMING 09 — ECONOMIA COGNITIVA E LIVELLI DI MODELLO

> Fonte grezza acquisita il 2026-08-13. Il contenuto seguente è conservato come brainstorming e non costituisce una decisione architetturale approvata.

Sì, **oggi il collo di bottiglia più concreto è proprio la qualità/velocità dei modelli locali**, ma il rischio vero è più ampio: **Newland deve far emergere comportamento interessante senza diventare computazionalmente ingestibile**.

Nel repo hai impostato Ollama come requisito per le decisioni dei Newlander e nel README usi esempi con `qwen2.5:3b` e `qwen2.5:7b`. Ollama oggi espone quei modelli rispettivamente attorno a 1,9 GB e 4,7 GB, con contesto dichiarato di 32K nelle build distribuite. Per un singolo agente funzionano bene come proof of concept, ma con decine di agenti il problema diventa presto evidente.

La questione è questa: **un 3B può essere abbastanza bravo a produrre JSON valido e decisioni semplici, ma potrebbe non essere abbastanza sofisticato da mantenere personalità, memoria causale, ambiguità sociale e strategie di lungo periodo in modo convincente**. Un 7B migliora, ma costa di più per ogni attivazione. Se poi avessi 50 Newlander che effettuano molte attivazioni cognitive, non stai facendo una chat: stai facendo potenzialmente **migliaia di inferenze LLM per giorno simulato**.

Quindi io vedo questi rischi, in ordine di importanza:

1. **Emergenza apparente invece di emergenza reale.**
   Questo per me è il rischio numero uno. Potresti osservare dialoghi diversi e comportamenti apparentemente complessi, ma scoprire che gli agenti stanno semplicemente reagendo localmente al prompt. Se le decisioni non producono strutture persistenti — reputazioni, strategie, convenzioni, cultura, specializzazione — Newland rischia di diventare un sofisticato generatore di roleplay.

2. **Qualità cognitiva dei piccoli modelli locali.**
   Qui sì, hai individuato un punto serio. Un agente deve contemporaneamente interpretare osservazioni, recuperare ricordi, aggiornare beliefs, relazioni, affetti, goal, piani e scegliere un'azione. Nel tuo `CognitionResult` stai chiedendo parecchio al modello. Con modelli piccoli aumentano incoerenze, dimenticanze, reasoning superficiale e tendenza a ripetere pattern.

3. **Scalabilità dell'inferenza.**
   Anche se un 7B fosse perfetto, 100 agenti × molte attivazioni diventano costosi. Il tuo `AttentionSchedule` è quindi **molto più importante di quanto sembri**: non deve pensare tutta la popolazione ogni tick. Gli agenti devono “svegliarsi” cognitivamente solo quando serve.

4. **Crescita del contesto mentale.**
   Questo secondo me ti esploderà prima del limite nominale dei 32K token. Non vuoi mettere 32K token nella mente di ogni agente a ogni inferenza. Anche se tecnicamente puoi, sarebbe lento e soprattutto cognitivamente sbagliato. Un essere umano non consulta tutta la propria autobiografia prima di scegliere se bere acqua. Devi arrivare a un retrieval della memoria molto selettivo.

5. **Omogeneità delle menti.**
   Questo è un rischio sottile ma enorme. Se tutti i Newlander usano lo stesso modello, con prompt molto simili, potrebbero diventare varianti della stessa persona. Anche dando loro beliefs e memorie differenti, il “motore cognitivo” sottostante tende agli stessi schemi linguistici e decisionali. Potresti ottenere 20 individui che sembrano distinti nei dati ma si comportano culturalmente in maniera troppo simile.

Ed è qui che secondo me c'è una soluzione architetturale interessante.

**Non fare dipendere la qualità di Newland dalla grandezza del modello.**

Il modello dovrebbe essere la parte che interpreta e decide, ma il sistema dovrebbe aiutarlo con una sorta di **cognitive economy**:

- piccoli modelli per decisioni quotidiane;
- modelli più grandi solo per eventi cognitivamente importanti;
- retrieval mirato della memoria;
- riflessione rara;
- compressione periodica delle esperienze;
- scheduling intelligente;
- magari batch/concorrenza controllata.

Tu hai già iniziato questa direzione con il `--reflective-model`: modello normale per la vita quotidiana e modello più grande per risonanza/conflitti. Quella idea, secondo me, va **generalizzata**.

Potresti avere qualcosa concettualmente del genere:

```text
percezione banale
    ↓
3B

decisione sociale normale
    ↓
7B

conflitto importante / cambio belief profondo
    ↓
14B

riflessione autobiografica rara
    ↓
32B
```

Non necessariamente con quei numeri precisi, ma con **livelli cognitivi**.

E c'è un'altra cosa che farei quasi subito: costruirei un **benchmark interno di Newland**.

Prendi la stessa situazione cognitiva e falla risolvere a 3B, 7B, 14B e magari a un modello cloud forte. Poi confronti:

```text
validità JSON
coerenza con percezioni
uso corretto della memoria
assenza di conoscenza impossibile
qualità del piano
stabilità della personalità
originalità
costo
latenza
```

Questo ti permetterebbe di sapere scientificamente se davvero **il 3B è troppo piccolo**, invece di dedurlo guardando la UI.

Perché potrebbe anche emergere una sorpresa: magari per il **90% della vita quotidiana di Newland un 3B è sufficiente**, e hai bisogno di un modello grande solo nel 10% degli eventi cognitivamente significativi.

Se riuscissi a dimostrarlo, avresti risolto uno dei problemi più grossi dell'intero progetto.

Per questo, se mi chiedi **“qual è oggi il rischio concreto di Newland?”**, la mia risposta è:

> **Non che i modelli locali siano troppo piccoli.**
>
> Il rischio è che per ottenere vera emergenza tu abbia bisogno di una qualità cognitiva che, moltiplicata per centinaia di agenti e migliaia di decisioni, renda la simulazione troppo lenta o costosa.

La grande sfida architetturale di Newland diventa quindi **ottenere intelligenza sociale macroscopica da molte cognizioni locali relativamente economiche**.

E, paradossalmente, se ci riesci, è forse proprio la parte scientificamente più interessante del progetto.
