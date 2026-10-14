# Specifica dei contenuti — sito "Storia dell'arrampicata"

Il sito è statico. Ogni pagina è un file di contenuto in `_generatore/content/<sezione>/<slug>.html`.
Un generatore (build.py) avvolge il contenuto nel layout comune (menu, briciole di pane, piè di pagina),
costruisce indici, linea del tempo, fonti e mappa del sito. Chi scrive i contenuti NON scrive layout, CSS, <html>, <head>, menu o footer.

## Regole editoriali (obbligatorie)

- Lingua: italiano, tono divulgativo da opera di consultazione (come una buona enciclopedia o una rivista di montagna). Frasi chiare, niente gergo burocratico, niente elenchi puntati fini a sé stessi: prosa, con qualche elenco dove serve.
- Il sito è un riferimento generale sulla storia dell'arrampicata e dell'alpinismo. **Mai** menzionare syllabus, esami, candidati, relazioni d'esame, dispense, materiale di studio, corsi o istruttori CAI, "questa serie di profili", "trattato in un altro profilo". Fatti storici come la fondazione del CAI (1863) o le scuole di alpinismo intitolate a qualcuno vanno bene.
- I testi di partenza (i file Word originali, che non stanno nel repository) sono materiale grezzo: vanno riscritti, non copiati. Togli intestazioni come "Relazione per esame teorico…", note numeriche `^([1])`, frasi autoreferenziali.
- Accuratezza prima di tutto. Correggi gli errori noti elencati nell'inventario dei testi sorgente, fuori dal repository (sezione "Incongruenze ed errori da verificare") e controlla ogni data, grado, compagno di cordata con la tua conoscenza. Se un dato è incerto o le fonti non concordano, scrivilo ("secondo alcune fonti…") oppure omettilo. Non inventare citazioni: le citazioni tra virgolette solo se le conosci con sicurezza (quelle presenti nei file sorgente si possono riusare).
- Nessuna figura ha più peso di un'altra: niente etichette "nuovo", "fuori programma", "minore".
- Usa le forme corrette dei nomi: Dülfer, Güllich, Hansjörg Auer, Rébuffat, Gian Carlo Grassi, Luisa Iovane, Sass dla Crusc, Mauerhakenstreit.
- Gradi: scala UIAA in numeri romani (VI, VII+), scala francese per la falesia (8a, 9c), scala boulder Font (8A) o V (V15). Non mescolare a caso.

## Formato del file di contenuto

Il file inizia con un'intestazione di righe `chiave: valore`, poi una riga con soli tre trattini `---`, poi il corpo in HTML.
Le chiavi `event` e `source` si possono ripetere. Le liste usano virgole.

```
title: Emilio Comici
summary: Il triestino che trattava l'arrampicata come un'arte e tracciò la via della "goccia d'acqua" sulla Nord della Cima Grande.
...
event: 1933-08-13 | Prima salita della parete Nord della Cima Grande di Lavaredo, con Antonio e Giuseppe Dimai | alpinismo
event: 1933 | Apre lo Spigolo Giallo sulla Cima Piccola di Lavaredo
source: Severino Casara, L'arte di arrampicare di Emilio Comici, Hoepli, 1957
source: Montagna.tv, "La leggenda di Emilio Comici" | https://www.montagna.tv/156278/emilio-comici/
---
<p>Corpo della pagina…</p>
```

- `event: DATA | TESTO | disciplina` — DATA è `AAAA` oppure `AAAA-MM-GG` (oppure `AAAA-MM`). TESTO è una frase breve (max ~20 parole) che ha senso anche fuori dalla pagina (nomina il protagonista se non è ovvio: "Comici apre lo Spigolo Giallo…"). La disciplina (facoltativa) è uno slug di disciplina. Tutti gli eventi confluiscono nella Linea del tempo con un link alla pagina d'origine. Metti 5–12 eventi per pagina protagonista, i più importanti.
- `source: TESTO | URL` — URL facoltativo. Libri, articoli, siti. Riusa le fonti dei file sorgente quando pertinenti (togli `/amp/` dagli URL di Montagna.tv). Per le pagine scritte da zero cita opere e siti affidabili che conosci davvero (libri dei protagonisti, Alpinist, American Alpine Journal, Planetmountain, Treccani, Wikipedia…); niente URL inventati: se non sei sicuro dell'URL esatto, cita solo il titolo.
- Nel corpo, i link interni si scrivono con percorso che inizia da `/` e termina in `.html`, per esempio `<a href="/protagonisti/paul-preuss.html">Paul Preuss</a>`, `<a href="/glossario.html#moschettone">moschettone</a>`. Il generatore li trasforma in link relativi. Usa SOLO gli indirizzi elencati più sotto. Il primo uso di un termine tecnico in una pagina linka il glossario (solo il primo uso, e senza esagerare: 3–8 link al glossario per pagina).
- Collega generosamente le altre pagine quando citi un protagonista, un'epoca, un materiale o una disciplina presenti nel sito (solo alla prima menzione).
- HTML consentito nel corpo: `<p> <h2> <h3> <blockquote><p>…</p><cite>…</cite></blockquote> <ul> <ol> <li> <a> <em> <strong> <abbr>`. Niente `<h1>`, niente classi, niente stili, niente immagini. Un `<h2>` per ogni sezione.

### Pagina protagonista (`content/protagonisti/<slug>.html`)

Chiavi:
- `title:` nome come va mostrato (es. `Emilio Comici`, `Manolo`, `Fratelli Huber`)
- `fullname:` facoltativo, nome completo se diverso (es. `Maurizio Zanolla`)
- `years:` es. `1901–1940` oppure `1993–` per i viventi (trattino lungo –)
- `born:` luogo e data di nascita, es. `Trieste, 21 febbraio 1901` (facoltativo se ignoto)
- `died:` luogo e data di morte (solo se deceduto)
- `nation:` es. `Italia`, `Francia`, `Stati Uniti`
- `phase:` numero 1–6
- `key_year:` l'anno simbolo usato nelle schede indice (es. `1933`)
- `disciplines:` slug separati da virgola (vedi elenco)
- `summary:` "in una frase", max ~30 parole, senza ripetere il nome all'inizio se si può
- `event:` e `source:` come sopra

Corpo (lunghezza indicativa 600–1000 parole; per figure con meno documentazione anche 450):
1. Un paragrafo d'apertura (senza titolo) che dice chi era e perché conta.
2. `<h2>La vita</h2>` origini, formazione, professione, morte.
3. `<h2>Le salite</h2>` (o un titolo più specifico) le imprese, in ordine cronologico, raccontate.
4. Una o due sezioni tematiche con titolo proprio (es. `<h2>La "goccia d'acqua"</h2>`, `<h2>Il caso K2</h2>`, `<h2>Lo stile e le idee</h2>`), eventualmente con una citazione in `<blockquote>`.
5. `<h2>L'eredità</h2>` perché è ricordato oggi, cosa ha cambiato.

NON scrivere la sezione Fonti né l'elenco delle imprese: il generatore li costruisce da `source:` ed `event:`. NON scrivere la sezione "Nella stessa epoca": la genera il layout.

### Pagina epoca (`content/epoche/<slug>.html`)

Chiavi: `title:` (es. `L'esplorazione e le vie normali`), `phase:` 1–6, `years:` (es. `1786–1870/80`), `grade:` grado limite raggiunto (es. `III`), `summary:` sintesi in 2–3 righe, `event:`, `source:`.
Corpo: apertura, `<h2>Il contesto</h2>`, `<h2>Le imprese</h2>`, `<h2>Tecnica e materiali</h2>`, `<h2>Come finisce</h2>` (o titoli simili). 900–1400 parole. Il generatore aggiunge l'elenco dei protagonisti della fase e i link a fase precedente e successiva.

### Approfondimento (`content/materiali/<slug>.html`, `content/discipline/<slug>.html`)

Chiavi: `title:`, `summary:`, `phases:` numeri separati da virgola (fasi coinvolte), `people:` slug dei protagonisti collegati, `event:`, `source:`.
Corpo: apertura, tappe in ordine cronologico con `<h2>` per periodo, `<h2>Perché ha cambiato tutto</h2>` in chiusura. 900–1500 parole.

## Indirizzi del sito (usare solo questi)

- `/index.html` Home · `/linea-del-tempo.html` · `/glossario.html` · `/fonti.html` · `/chi-siamo.html` · `/mappa-del-sito.html`
- `/epoche/index.html` e le sei fasi:
  1 `/epoche/esplorazione.html` (1786–1870/80) · 2 `/epoche/pareti.html` (1870–1900/14) · 3 `/epoche/epoca-doro.html` (1900–1945) · 4 `/epoche/dopoguerra.html` (1945–1960) · 5 `/epoche/nuovo-mattino.html` (1960–1980) · 6 `/epoche/no-limits.html` (1980–oggi)
- `/materiali/index.html` · `/materiali/calzature.html` · `/materiali/corde.html` · `/materiali/protezioni.html` · `/materiali/gradi.html`
- `/discipline/index.html` · `/discipline/alpinismo.html` · `/discipline/arrampicata-libera.html` · `/discipline/sportiva.html` · `/discipline/bouldering.html` · `/discipline/free-solo.html` · `/discipline/cascate.html`
  (slug di disciplina per `disciplines:` ed `event:`: alpinismo, arrampicata-libera, sportiva, bouldering, free-solo, cascate)
- `/protagonisti/index.html` e le 52 schede `/protagonisti/<slug>.html`:
  - Fase I: jacques-balmat, edward-whymper, jean-antoine-carrel, quintino-sella
  - Fase II: albert-mummery, alexander-burgener, melchior-anderegg
  - Fase III: tita-piaz, angelo-dibona, paul-preuss, hans-dulfer, emil-solleder, willo-welzenbach, emilio-comici, mary-varale, pierre-allain, riccardo-cassin, giusto-gervasutti, anderl-heckmair
  - Fase IV: maurice-herzog, lionel-terray, gaston-rebuffat, hermann-buhl, walter-bonatti, cesare-maestri, rene-desmaison
  - Fase V: john-gill, royal-robbins, warren-harding, reinhold-messner, alessandro-gogna, gian-piero-motti, john-bachar, gian-carlo-grassi
  - Fase VI: heinz-mariacher, luisa-iovane, manolo, roberto-bassi, patrick-edlinger, jerry-moffatt, renato-casarotto, patrick-berhault, wolfgang-gullich, catherine-destivelle, lynn-hill, fratelli-huber, chris-sharma, hansjorg-auer, alex-honnold, tommy-caldwell, adam-ondra, margo-hayes

## Voci del glossario (ancore `/glossario.html#<id>`)

alpinismo-senza-guida, arrampicata-artificiale, arrampicata-libera, a-vista, assicurazione, big-wall, bivacco, boulder, by-fair-means, campus-board, chiodo, chiodo-a-espansione, clean-climbing, concatenamento, corda-doppia, corda-dinamica, cordata, crash-pad, deep-water-solo, diedro, direttissima, dry-tooling, dulfersitz, falesia, fessura, flash, free-solo, friend, gara-lead, grado, guida-alpina, kernmantel, lay-back, magnesite, mauerhakenstreit, misto, moschettone, nut, ottomila, piolet-traction, placca, prima-invernale, prima-libera, prima-salita, rinvio, risanatura, rotpunkt, scala-francese, scala-uiaa, scarpetta, sesto-grado, settimo-grado, solitaria, spit, staffa, stile-alpino, strapiombo, top-rope, via-normale, vibram

## SEO
- `BASE_URL` in build.py è l'indirizzo pubblico del sito: serve per `canonical`, anteprime social (Open Graph) e `sitemap.xml`. Se il sito cambia indirizzo (es. dominio proprio), va aggiornato lì.
- Ogni pagina riceve title, description (dal `summary`), canonical, tag Open Graph con l'immagine `assets/og-image.png` e dati strutturati JSON-LD (WebSite in home, ProfilePage/Person per i protagonisti, WebPage altrove).
- `sitemap.xml` è generata a ogni build con tutte le pagine.
