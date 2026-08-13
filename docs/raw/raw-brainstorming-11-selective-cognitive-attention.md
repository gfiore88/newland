# BRAINSTORMING 11 — ATTENZIONE COGNITIVA SELETTIVA

> Fonte grezza acquisita da Giovanni Fiore il 2026-08-13. Il contenuto seguente
> esprime la direzione concettuale desiderata e non costituisce da solo una
> decisione architetturale approvata.

Il prompt non dovrebbe rappresentare tutto ciò che il personaggio sa; dovrebbe
rappresentare ciò a cui sta prestando attenzione in quel momento.

Mandare a ogni inferenza un mega-prompt con biografia, ricordi, relazioni,
obiettivi, regole del mondo, inventario, storia recente e possibilità remote
equivale a chiedere a una persona, prima di bere:

> “Considera tutta la tua infanzia, ogni persona conosciuta, le tue ambizioni,
> la situazione geopolitica, ogni oggetto nella stanza e tutti i rischi
> teoricamente possibili. Ora decidi se prendere il bicchiere.”

Non è più intelligenza: è deliberazione indiscriminata.

Un’architettura più credibile separa diversi livelli:

1. **Reazioni automatiche**: azioni semplici e frequenti come bere, camminare,
   sedersi o seguire qualcuno. Spesso non richiedono un’inferenza linguistica.
2. **Routine e competenze**: il personaggio sa già come si beve o come si apre
   una porta. Il modello sceglie eventualmente l’intenzione; il sistema esegue
   il comportamento.
3. **Decisione contestuale**: si inviano soltanto stato locale, obiettivo
   corrente, percezioni rilevanti, poche possibilità d’azione e ricordi
   immediatamente pertinenti.
4. **Ragionamento profondo**: biografia, memoria a lungo termine, relazioni
   complesse e pianificazione entrano nel contesto solo quando la situazione lo
   richiede davvero.

Per bere un bicchiere d’acqua, il contesto potrebbe essere semplicemente:

```text
Bisogno attuale: sete alta
Obiettivo corrente: dissetarsi
Percezione: bicchiere d’acqua raggiungibile sul tavolo
Vincoli rilevanti: nessuno
```

Il personaggio prende il bicchiere e beve. Ma se l’acqua ha un odore strano,
appartiene a un nemico o il personaggio ricorda di essere stato avvelenato,
allora il sistema recupera quei ricordi e promuove la decisione a un livello
cognitivo superiore.

Regola candidata:

> Prima agisci con il minimo contesto sufficiente. Recupera altra conoscenza
> solo quando emergono incertezza, conflitto, rischio o conseguenze importanti.

Distinzioni necessarie:

- **Memoria totale**: tutto ciò che il personaggio potrebbe conoscere.
- **Memoria attiva**: ciò che sta pensando adesso.
- **Percezione**: ciò che può osservare nella situazione corrente.
- **Contesto d’inferenza**: soltanto l’intersezione rilevante tra queste cose.

Il mega-prompt confonde memoria totale e coscienza attiva. Ne risultano più
costo e latenza, ma anche personaggi meno naturali: iperanalitici, incoerenti,
facilmente distratti e inclini a inventare collegamenti tra informazioni che
non avrebbero motivo di considerare.

```text
contesto = stato locale
         + intenzione corrente
         + percezioni rilevanti
         + ricordi recuperati su richiesta
         + vincoli dell’azione
```

Non:

```text
contesto = intera mente + intero mondo + intera storia
```

Il modello dovrebbe essere una parte di un sistema cognitivo con attenzione
selettiva, non un processore al quale riversare l’intero universo a ogni passo.
