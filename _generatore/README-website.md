# Storia dell'arrampicata

Sito statico in italiano sulla storia dell'alpinismo e dell'arrampicata: sei epoche, 52 protagonisti, materiali e tecniche, discipline, linea del tempo, glossario e fonti.

## Come aprirlo

Apri `index.html` nel browser. Tutti i link sono relativi, quindi il sito funziona sia aperto in locale sia pubblicato così com'è (per esempio con GitHub Pages, Netlify o qualsiasi hosting statico). I caratteri tipografici vengono caricati da Google Fonts; senza connessione il sito usa caratteri di riserva.

## Struttura

- `index.html` home
- `epoche/` le sei fasi storiche
- `protagonisti/` indice e 52 schede
- `materiali/` calzature, corde, protezioni, gradi
- `discipline/` alpinismo, arrampicata libera, sportiva, bouldering, free solo, cascate
- `linea-del-tempo.html`, `glossario.html`, `fonti.html`, `chi-siamo.html`, `mappa-del-sito.html`
- `assets/` foglio di stile, script e icona
- `_generatore/` il generatore che produce tutte le pagine qui sopra (non viene pubblicato: GitHub Pages ignora le cartelle che iniziano con `_`)

## Come modificare il sito

Le pagine HTML nella radice sono generate: non vanno modificate a mano, perché la rigenerazione successiva cancellerebbe la modifica. Si modificano i sorgenti in `_generatore/` e poi si rigenera.

- Testi: `_generatore/content/<sezione>/<pagina>.html`. Ogni file ha in testa alcune righe `chiave: valore` (nome, anni, epoca, riassunto, eventi della linea del tempo, fonti), poi una riga `---` e sotto il testo in HTML. Il formato e le regole di stile sono in `_generatore/SPEC.md`.
- Grafica e comportamento: `_generatore/assets/` (`_proto.css` e `_extra.css` diventano insieme `assets/style.css`; `site.js`, `favicon.svg` e `og-image.png` vengono copiati così come sono).
- Struttura, menu, indici, linea del tempo, mappa del sito: `_generatore/build.py`.
- Questo README: `_generatore/README-website.md`.

## Come rigenerare

Serve Python 3, senza librerie aggiuntive. Dalla cartella del repository:

```
python3 _generatore/build.py
```

Il comando svuota la cartella del repository, tranne i file e le cartelle che iniziano con `.` o `_` (quindi `.git` e il generatore restano), riscrive tutte le pagine e alla fine controlla che nessun link interno sia rotto. Con `python3 _generatore/build.py <cartella>` scrive il sito in un'altra cartella, per esempio per un'anteprima. Poi si controllano le differenze con `git diff` e si fa il commit.
