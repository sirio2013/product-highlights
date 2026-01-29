# Product Highlights — Guida per il Marketing

## Che cos'è questo strumento?

Questo strumento è stato creato per la **categoria antiparassitari** e ha lo scopo di arricchire automaticamente le descrizioni prodotto con i product highlights più pertinenti.

Per ciascun prodotto antiparassitario, lo strumento:

1. **Seleziona i 3 product highlights più pertinenti** tra quelli predefiniti, uno per ciascun gruppo (efficacia, durata, formato)
2. **Integra i 3 highlights nella descrizione originale**, riscrivendo il testo in modo naturale e in formato HTML

La selezione e l'integrazione sono eseguite dall'intelligenza artificiale (Google Gemini), che analizza il contenuto della descrizione e sceglie gli highlights più coerenti con il prodotto specifico.

---

## Highlights disponibili

L'AI sceglie un highlight per ciascuno dei tre gruppi seguenti:

**Gruppo 1 — Efficacia / Azione**
- Azione repellente contro le zanzare
- Elimina efficacemente pulci e zecche
- Inibisce lo sviluppo di uova e larve proteggendo l'ambiente
- Protegge dai flebotomi riducendo il rischio Leishmaniosi
- Protezione efficace contro i parassiti

**Gruppo 2 — Durata / Protezione**
- Protezione a lungo termine (fino a 8-12 mesi)
- Protezione duratura e affidabile
- Resistente all'acqua (efficace anche dopo bagni occasionali)
- Una singola applicazione protegge per 4 settimane

**Gruppo 3 — Formato applicazione**
- Collare a rilascio graduale e controllato
- Compressa masticabile appetibile facile da somministrare
- Facile da applicare
- Formato Spray per un'applicazione immediata
- Pipette Spot-On pratiche e veloci da applicare

---

## Esempio

**Prodotto:** Vectra 3D 3 pipette per cani - 4-10 Kg

**Highlights selezionati dall'AI:**
- Gruppo 1 (efficacia): *Protegge dai flebotomi riducendo il rischio Leishmaniosi*
- Gruppo 2 (durata): *Una singola applicazione protegge per 4 settimane*
- Gruppo 3 (formato): *Pipette Spot-On pratiche e veloci da applicare*

**Descrizione originale (estratto):**
> Pipetta innovativa contro pulci, zecche, zanzare, flebotomi e mosche. Una singola applicazione dura 1 mese*.

**Descrizione con highlights integrati (estratto):**
> Queste Pipette Spot-On pratiche e veloci da applicare sono innovative contro pulci, zecche, zanzare, flebotomi e mosche. Una singola applicazione protegge per 4 settimane. [...] protegge dai flebotomi riducendo il rischio Leishmaniosi.

---

## Come funziona

1. Lo strumento legge l'elenco dei prodotti antiparassitari dal file CSV di partenza
2. Per ogni prodotto, invia la descrizione e tutti gli highlights disponibili a Gemini AI
3. Gemini analizza il testo, classifica gli highlights per pertinenza, ne seleziona uno per gruppo e li integra nella descrizione
4. I risultati vengono salvati in due formati: JSON e **Excel**

Lo strumento salta automaticamente i prodotti già elaborati, quindi può essere interrotto e ripreso senza perdere il lavoro fatto.

---

## File di output

Il risultato finale è disponibile nel file Excel allegato:

**[results.xlsx](results.xlsx)**

Colonne presenti nel file:

- **id** — ID prodotto
- **titolo** — nome del prodotto
- **descrizione-iniziale** — descrizione originale, senza modifiche
- **product-highlights-1** — highlight selezionato per efficacia/azione
- **product-highlights-2** — highlight selezionato per durata/protezione
- **product-highlights-3** — highlight selezionato per formato applicazione
- **descrizione** — descrizione riscritta con i 3 highlights integrati (HTML)
