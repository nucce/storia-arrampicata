#!/usr/bin/env python3
"""Genera il sito statico "Storia dell'arrampicata" da content/ nella cartella che contiene il generatore,
cioè la radice del repository (o nella cartella data come argomento).

Ogni file di contenuto ha un'intestazione `chiave: valore`, una riga `---` e il corpo HTML (vedi SPEC.md).
I link interni nel corpo iniziano con `/` e vengono resi relativi, così il sito funziona aperto in locale.
"""
import hashlib
import html
import json
import os
import re
import shutil
import sys
from collections import OrderedDict, defaultdict

SRC = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.dirname(SRC)
SITE = "Storia dell'arrampicata"
BASE_URL = 'https://nucce.github.io/storia-arrampicata/'  # indirizzo pubblico, per canonical, sitemap e anteprime social
GOOGLE_VERIFICATION = 'DVXRftYHFaXoytt9g5nxhEfU9YBXY56ieUA4bgQnM6w'  # Google Search Console, solo in home

PHASES = OrderedDict([
    (1, dict(slug='esplorazione', roman='I', years='1786–1870/80', short="Esplorazione e vie normali", start=1786, end=1869)),
    (2, dict(slug='pareti', roman='II', years='1870–1900/14', short='La salita delle pareti', start=1870, end=1899)),
    (3, dict(slug='epoca-doro', roman='III', years='1900–1945', short="L'epoca d'oro della difficoltà", start=1900, end=1944)),
    (4, dict(slug='dopoguerra', roman='IV', years='1945–1960', short='Dopoguerra e direttissime', start=1945, end=1959)),
    (5, dict(slug='nuovo-mattino', roman='V', years='1960–1980', short='Nuovo Mattino e “Americani”', start=1960, end=1979)),
    (6, dict(slug='no-limits', roman='VI', years='1980–oggi', short='Arrampicata sportiva e “No Limits”', start=1980, end=9999)),
])
PEOPLE_ORDER = {
    1: 'jacques-balmat edward-whymper jean-antoine-carrel quintino-sella',
    2: 'albert-mummery alexander-burgener melchior-anderegg',
    3: 'tita-piaz angelo-dibona paul-preuss hans-dulfer emil-solleder willo-welzenbach emilio-comici mary-varale pierre-allain riccardo-cassin giusto-gervasutti anderl-heckmair',
    4: 'maurice-herzog lionel-terray gaston-rebuffat hermann-buhl walter-bonatti cesare-maestri rene-desmaison',
    5: 'john-gill royal-robbins warren-harding reinhold-messner alessandro-gogna gian-piero-motti john-bachar gian-carlo-grassi',
    6: 'heinz-mariacher luisa-iovane manolo roberto-bassi patrick-edlinger jerry-moffatt renato-casarotto patrick-berhault wolfgang-gullich catherine-destivelle lynn-hill fratelli-huber chris-sharma hansjorg-auer alex-honnold tommy-caldwell adam-ondra margo-hayes',
}
MATERIALI = ['calzature', 'corde', 'protezioni', 'gradi']
DISCIPLINE = ['alpinismo', 'arrampicata-libera', 'sportiva', 'bouldering', 'free-solo', 'cascate']
DISC_LABEL = {'alpinismo': 'Alpinismo', 'arrampicata-libera': 'Arrampicata libera', 'sportiva': 'Sportiva e gare',
              'bouldering': 'Bouldering', 'free-solo': 'Free solo', 'cascate': 'Cascate di ghiaccio'}
MAT_LABEL = {'calzature': 'Calzature', 'corde': 'Corde', 'protezioni': 'Protezioni', 'gradi': 'Gradi'}
# Materiali e tecniche che entrano in scena in ciascuna fase.
PHASE_GEAR = {
    1: [('corde', 'Corde di canapa'), ('calzature', 'Scarponi chiodati'), ('gradi', 'Nessuna scala: si misura la vetta')],
    2: [('corde', 'Canapa e cordata'), ('calzature', 'Pedule di feltro e canapa'), ('gradi', 'Verso il IV grado')],
    3: [('protezioni', 'Chiodo, moschettone, corda doppia'), ('gradi', 'Scala Welzenbach e VI grado'), ('calzature', 'Suola Vibram (1937)')],
    4: [('calzature', 'Diffusione del Vibram'), ('protezioni', 'Chiodi a pressione e artificiale'), ('corde', 'Nylon e kernmantel (1953)')],
    5: [('protezioni', 'Nut, clean climbing, Friend'), ('corde', 'Corde dinamiche'), ('gradi', 'Il VII grado e la scala aperta')],
    6: [('calzature', 'Gomma adesiva (anni \'80)'), ('protezioni', 'Spit e falesia'), ('gradi', 'Scala francese fino al 9c')],
}
NAV = [('epoche/index.html', 'Epoche', 'epoche'), ('protagonisti/index.html', 'Protagonisti', 'protagonisti'),
       ('materiali/index.html', 'Materiali e tecniche', 'materiali'), ('discipline/index.html', 'Discipline', 'discipline'),
       ('linea-del-tempo.html', 'Linea del tempo', 'linea'), ('glossario.html', 'Glossario', 'glossario')]
MESI = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre']

E = lambda s: html.escape(str(s), quote=True)
warnings = []


# ---------- lettura dei contenuti ----------

def parse(path):
    with open(path, encoding='utf-8') as f:
        text = f.read()
    if '\n---\n' not in text:
        raise SystemExit('Manca la riga --- in ' + path)
    head, body = text.split('\n---\n', 1)
    meta = {'event': [], 'source': []}
    for line in head.splitlines():
        line = line.strip()
        if not line or line.startswith('#') or ':' not in line:
            continue
        k, v = line.split(':', 1)
        k, v = k.strip().lower(), v.strip()
        if k in ('event', 'source'):
            meta[k].append(v)
        else:
            meta[k] = v
    meta['body'] = body.strip()
    meta['events'] = [parse_event(e, path) for e in meta.pop('event')]
    meta['events'] = [e for e in meta['events'] if e]
    meta['sources'] = [parse_source(s) for s in meta.pop('source')]
    return meta


def parse_event(s, path):
    parts = [p.strip() for p in s.split('|')]
    date = parts[0]
    m = re.match(r'^(\d{4})(?:-(\d{1,2}))?(?:-(\d{1,2}))?', date)
    if not m or len(parts) < 2:
        warnings.append('Evento non valido in %s: %s' % (os.path.basename(path), s))
        return None
    y, mo, d = int(m.group(1)), m.group(2) and int(m.group(2)), m.group(3) and int(m.group(3))
    disc = parts[2] if len(parts) > 2 and parts[2] in DISCIPLINE else ''
    return dict(y=y, m=mo or 0, d=d or 0, text=parts[1], disc=disc)


def parse_source(s):
    parts = [p.strip() for p in s.split('|')]
    url = parts[1] if len(parts) > 1 and parts[1].startswith('http') else ''
    url = url.replace('/amp/', '/') if 'montagna.tv' in url else url
    return dict(text=parts[0], url=url)


def fmt_date(e, long=False):
    if e['d'] and e['m']:
        return '%d %s %d' % (e['d'], MESI[e['m'] - 1], e['y']) if long else '%d %s' % (e['d'], MESI[e['m'] - 1][:3])
    if e['m']:
        return '%s %d' % (MESI[e['m'] - 1], e['y']) if long else MESI[e['m'] - 1][:3]
    return str(e['y']) if long else ''


def phase_of_year(y):
    for n, p in PHASES.items():
        if p['start'] <= y <= p['end']:
            return n
    return 1


def load(section):
    d = os.path.join(SRC, 'content', section)
    out = {}
    if os.path.isdir(d):
        for fn in sorted(os.listdir(d)):
            if fn.endswith('.html') and not fn.startswith('_'):
                out[fn[:-5]] = parse(os.path.join(d, fn))
    return out


def csv(v):
    return [x.strip() for x in (v or '').split(',') if x.strip()]


# ---------- layout ----------

def rel(path_from, target):
    """Link relativo da una pagina (es. 'protagonisti/x.html') a un percorso del sito ('glossario.html#a')."""
    depth = path_from.count('/')
    return '../' * depth + target


def fix_links(body, page):
    def sub(m):
        attr, target = m.group(1), m.group(2)
        return '%s="%s"' % (attr, rel(page, target))
    return re.sub(r'(href)="/([^"]*)"', sub, body)


def page_url(page):
    """URL pubblico assoluto di una pagina; le index.html diventano la cartella."""
    if page == 'index.html':
        return BASE_URL
    if page.endswith('/index.html'):
        return BASE_URL + page[:-len('index.html')]
    return BASE_URL + page


def jsonld(page, title, desc):
    url = page_url(page)
    if page == 'index.html':
        data = {'@context': 'https://schema.org', '@type': 'WebSite', 'name': SITE, 'url': url,
                'description': desc, 'inLanguage': 'it'}
    else:
        data = {'@context': 'https://schema.org', '@type': 'WebPage', 'name': title, 'url': url,
                'description': desc, 'inLanguage': 'it',
                'isPartOf': {'@type': 'WebSite', 'name': SITE, 'url': BASE_URL}}
        if page.startswith('protagonisti/') and not page.endswith('index.html'):
            data['@type'] = 'ProfilePage'
            data['mainEntity'] = {'@type': 'Person', 'name': title}
    return json.dumps(data, ensure_ascii=False).replace('</', '<\\/')


def head_html(page, title, desc):
    p = rel(page, '')
    full = SITE if title == SITE else '%s · %s' % (title, SITE)
    url = page_url(page)
    verify = '<meta name="google-site-verification" content="%s">\n' % GOOGLE_VERIFICATION if page == 'index.html' else ''
    return f'''<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(full)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{url}">
{verify}<meta property="og:type" content="{'website' if page == 'index.html' else 'article'}">
<meta property="og:site_name" content="{E(SITE)}">
<meta property="og:locale" content="it_IT">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE_URL}assets/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{jsonld(page, title, desc)}</script>
<link rel="icon" href="{p}assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@600;800;900&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="{p}assets/style.css">
<script>try{{var t=localStorage.getItem('tema');if(t==='light'||t==='dark')document.documentElement.setAttribute('data-theme',t);}}catch(e){{}}</script>
</head>
<body id="top">
<a class="skip" href="#contenuto">Vai al contenuto</a>
'''


def nav_html(page, current):
    items = ''.join('<li><a href="%s"%s>%s</a></li>' % (rel(page, href), ' aria-current="page"' if key == current else '', label)
                    for href, label, key in NAV)
    return f'''<header class="nav">
  <div class="wrap">
    <a class="brand" href="{rel(page, 'index.html')}">Storia dell'arrampicata <small>1786 – oggi</small></a>
    <nav aria-label="Sezioni" class="desk"><ul>{items}</ul></nav>
    <details class="menu"><summary>Menu</summary><nav aria-label="Sezioni (mobile)"><ul><li><a href="{rel(page, 'index.html')}">Home</a></li>{items}</ul></nav></details>
    <button class="theme-toggle" type="button" aria-label="Passa al tema scuro" title="Passa al tema scuro"><svg class="ico-moon" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg><svg class="ico-sun" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1" stroke="currentColor" stroke-width="2" stroke-linecap="square"/></svg></button>
  </div>
</header>
'''


def footer_html(page):
    r = lambda t: rel(page, t)
    return f'''<footer>
  <div class="wrap">
    <div>
      <p class="brandline">Storia dell'arrampicata</p>
      <p>Due secoli e mezzo di alpinismo e arrampicata, dal Monte Bianco al 9c: le epoche, le persone, gli attrezzi e le idee.</p>
      <p>La suddivisione in sei fasi riprende la scansione tradizionale della storia dell'alpinismo, come in L. Franceschini ed E. Filippi, <em>Brevi cenni di storia dell'alpinismo</em>.</p>
    </div>
    <div>
      <ul class="foot-links">
        <li><a href="{r('epoche/index.html')}">Epoche</a></li>
        <li><a href="{r('protagonisti/index.html')}">Protagonisti</a></li>
        <li><a href="{r('materiali/index.html')}">Materiali</a></li>
        <li><a href="{r('discipline/index.html')}">Discipline</a></li>
        <li><a href="{r('linea-del-tempo.html')}">Linea del tempo</a></li>
        <li><a href="{r('glossario.html')}">Glossario</a></li>
      </ul>
      <ul class="foot-links">
        <li><a href="{r('fonti.html')}">Fonti</a></li>
        <li><a href="{r('chi-siamo.html')}">Chi siamo</a></li>
        <li><a href="{r('mappa-del-sito.html')}">Mappa del sito</a></li>
      </ul>
    </div>
  </div>
</footer>
<a class="to-top" href="#top" aria-label="Torna in cima" title="Torna in cima"><svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path d="M12 19V5M5 12l7-7 7 7" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="square"/></svg></a>
<script src="{r('assets/site.js')}"></script>
</body>
</html>
'''


def crumbs_html(page, trail):
    lis = ['<li><a href="%s">Home</a></li>' % rel(page, 'index.html')]
    for i, (label, href) in enumerate(trail):
        if href and i < len(trail) - 1:
            lis.append('<li><a href="%s">%s</a></li>' % (rel(page, href), E(label)))
        else:
            lis.append('<li aria-current="page">%s</li>' % E(label))
    return '<nav class="crumbs mono" aria-label="Percorso"><ol>%s</ol></nav>' % ''.join(lis)


def page_seed(page):
    """Seme del disegno delle curve di livello, ricavato dall'indirizzo della pagina:
    aggiungere o spostare una pagina non cambia il disegno delle altre."""
    return int(hashlib.md5(page.encode('utf-8')).hexdigest()[:6], 16) % 1900 / 100


def page_head(page, trail, title, eyebrow='', sub='', lede='', meta='', extra='', seed=0):
    return f'''<section class="page-head">
  <canvas class="contours" data-seed="{seed}" aria-hidden="true"></canvas>
  <div class="wrap">
    {crumbs_html(page, trail)}
    {extra}
    {f'<p class="eyebrow mono">{eyebrow}</p>' if eyebrow else ''}
    <h1>{E(title)}</h1>
    {f'<p class="sub">{E(sub)}</p>' if sub else ''}
    {f'<p class="lede">{lede}</p>' if lede else ''}
    {meta}
  </div>
</section>
'''


PAGES = {}  # percorso -> titolo, per la mappa del sito e il controllo dei link


def write(page, title, desc, current, main):
    PAGES[page] = title
    doc = head_html(page, title, desc) + nav_html(page, current) + '<main id="contenuto">\n' + main + '\n</main>\n' + footer_html(page)
    dest = os.path.join(OUT, page)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, 'w', encoding='utf-8') as f:
        f.write(doc)


def strip_tags(s):
    return re.sub(r'<[^>]+>', '', s)


def steps_html(events, long=True, cls='steps wide'):
    if not events:
        return ''
    lis = ''.join('<li><span class="when">%s</span><span class="what">%s</span></li>' % (E(fmt_date(e, True)), E(e['text']))
                  for e in sorted(events, key=lambda e: (e['y'], e['m'], e['d'])))
    return '<ol class="%s">%s</ol>' % (cls, lis)


def sources_html(sources):
    if not sources:
        return ''
    lis = []
    for s in sources:
        if s['url']:
            lis.append('<li>%s · <a href="%s" rel="noopener">%s</a></li>' % (E(s['text']), E(s['url']), E(short_url(s['url']))))
        else:
            lis.append('<li>%s</li>' % E(s['text']))
    return '<ul class="src-list">%s</ul>' % ''.join(lis)


def short_url(u):
    u = re.sub(r'^https?://(www\.)?', '', u)
    return u if len(u) < 60 else u[:57] + '…'


def pager_html(page, prev, nxt):
    def a(item, cls, lab):
        if not item:
            return '<span class="empty"></span>'
        href, title = item
        return '<a class="%s" href="%s"><span class="lab mono">%s</span><span class="nm">%s</span></a>' % (cls, rel(page, href), lab, E(title))
    return '<nav class="pager" aria-label="Pagine vicine">%s%s</nav>' % (a(prev, 'prev', '← Precedente'), a(nxt, 'next', 'Successivo →'))


# ---------- costruzione ----------

def main():
    if os.path.isdir(OUT):
        if os.listdir(OUT) and not os.path.exists(os.path.join(OUT, 'index.html')):
            sys.exit(f'{OUT} non è vuota e non contiene il sito (manca index.html): non la svuoto.')
        for name in os.listdir(OUT):
            p = os.path.join(OUT, name)
            if name.startswith(('.', '_')):
                continue  # conserva .git, .gitignore e il generatore stesso (_generatore)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(os.path.join(OUT, 'assets'), exist_ok=True)
    with open(os.path.join(OUT, 'assets', 'style.css'), 'w', encoding='utf-8') as f:
        for part in ('_proto.css', '_extra.css'):
            f.write(open(os.path.join(SRC, 'assets', part), encoding='utf-8').read() + '\n')
    shutil.copy(os.path.join(SRC, 'README-website.md'), os.path.join(OUT, 'README.md'))
    for name in ('site.js', 'favicon.svg', 'og-image.png'):
        shutil.copy(os.path.join(SRC, 'assets', name), os.path.join(OUT, 'assets', name))

    epoche = load('epoche')
    people = load('protagonisti')
    mats = load('materiali')
    discs = load('discipline')
    pagine = load('pagine')

    by_slug_phase = {}
    order = []
    for n, s in PEOPLE_ORDER.items():
        for slug in s.split():
            by_slug_phase[slug] = n
            order.append(slug)
    missing = [s for s in order if s not in people]
    if missing:
        warnings.append('Protagonisti mancanti: ' + ', '.join(missing))
    for slug in people:
        if slug not in by_slug_phase:
            warnings.append('Protagonista non in elenco: ' + slug)
    order = [s for s in order if s in people]
    for slug in order:
        people[slug]['phase'] = by_slug_phase[slug]

    timeline = []  # (evento, pagina, titolo pagina, tag discipline)

    def collect(evs, page, title, discs_default):
        for e in evs:
            tags = [e['disc']] if e['disc'] else discs_default
            timeline.append((e, page, title, tags))

    all_sources = defaultdict(list)  # chiave -> [(fonte, pagina, titolo)]

    def add_sources(srcs, page, title):
        for s in srcs:
            key = s['url'].rstrip('/').lower() or re.sub(r'\W+', ' ', s['text'].lower()).strip()
            all_sources[key].append((s, page, title))

    # --- Protagonisti ---
    for slug in order:
        p = people[slug]
        n = p['phase']
        ph = PHASES[n]
        page = 'protagonisti/%s.html' % slug
        dl = []
        if p.get('fullname'):
            dl.append(('Nome', E(p['fullname'])))
        dl.append(('Anni', '<span class="big">%s</span>' % E(p.get('years', ''))))
        if p.get('born'):
            dl.append(('Nascita', E(p['born'])))
        if p.get('died'):
            dl.append(('Morte', E(p['died'])))
        if p.get('nation'):
            dl.append(('Paese', E(p['nation'])))
        dl.append(('Epoca', '<a href="%s">Fase %s · %s</a>' % (rel(page, 'epoche/%s.html' % ph['slug']), ph['roman'], E(ph['short']))))
        ds = [d for d in csv(p.get('disciplines')) if d in DISCIPLINE]
        if ds:
            dl.append(('Discipline', '<div class="tags">%s</div>' % ''.join(
                '<a class="tag" href="%s">%s</a>' % (rel(page, 'discipline/%s.html' % d), DISC_LABEL[d]) for d in ds)))
        aside = '<aside><div class="facts-box"><h2>Scheda</h2><dl>%s</dl></div></aside>' % ''.join(
            '<dt>%s</dt><dd>%s</dd>' % (k, v) for k, v in dl)
        # contemporanei: stessa fase, anno chiave più vicino
        ky = int(re.sub(r'\D', '', p.get('key_year', '0'))[:4] or 0)
        same = [s for s in order if s != slug and people[s]['phase'] == n]
        same.sort(key=lambda s: abs(int(re.sub(r'\D', '', people[s].get('key_year', '0'))[:4] or 0) - ky))
        near = same[:4]
        if len(near) < 3:  # fasi piccole: aggiungi dalla fase vicina
            extra = [s for s in order if people[s]['phase'] in (n - 1, n + 1) and s not in near]
            extra.sort(key=lambda s: abs(int(re.sub(r'\D', '', people[s].get('key_year', '0'))[:4] or 0) - ky))
            near += extra[:3 - len(near)]
        idx = order.index(slug)
        prev = order[idx - 1] if idx > 0 else None
        nxt = order[idx + 1] if idx < len(order) - 1 else None
        main_html = page_head(page, [('Protagonisti', 'protagonisti/index.html'), (p['title'], None)], p['title'],
                              eyebrow='Fase %s · %s' % (ph['roman'], E(ph['short'])),
                              sub=p.get('years', ''), lede=E(p.get('summary', '')), seed=page_seed(page))
        main_html += '<div class="wrap article"><article class="prose">%s</article>%s</div>' % (fix_links(p['body'], page), aside)
        if p['events']:
            main_html += '<section class="band-sec alt"><div class="wrap"><h2 class="sec-title">Le date</h2>%s</div></section>' % steps_html(p['events'])
        main_html += '<section class="band-sec"><div class="wrap"><h2 class="sec-title">Nella stessa epoca</h2><ul class="cards">%s</ul></div></section>' % ''.join(
            person_card(page, s, people[s]) for s in near)
        if p['sources']:
            main_html += '<section class="band-sec"><div class="wrap"><h2 class="sec-title">Fonti</h2>%s</div></section>' % sources_html(p['sources'])
        main_html += pager_html(page, prev and ('protagonisti/%s.html' % prev, people[prev]['title']),
                                nxt and ('protagonisti/%s.html' % nxt, people[nxt]['title']))
        write(page, p['title'], '%s (%s): %s' % (p['title'], p.get('years', ''), strip_tags(p.get('summary', ''))), 'protagonisti', main_html)
        collect(p['events'], page, p['title'], ds)
        add_sources(p['sources'], page, p['title'])

    # --- Indice protagonisti ---
    page = 'protagonisti/index.html'
    chips = '<button class="chip" data-value="" aria-pressed="true">Tutte</button>' + ''.join(
        '<button class="chip" data-value="%s" aria-pressed="false">%s</button>' % (d, DISC_LABEL[d]) for d in DISCIPLINE)
    groups = ''
    for n, ph in PHASES.items():
        slugs = [s for s in order if people[s]['phase'] == n]
        groups += '<section class="phase-group" id="fase-%d" data-filter-container><header><h2><a href="%s">Fase %s · %s</a></h2><span class="years mono">%s</span></header><ul class="cards">%s</ul></section>' % (
            n, rel(page, 'epoche/%s.html' % ph['slug']), ph['roman'], E(ph['short']), ph['years'],
            ''.join(person_card(page, s, people[s], filt=True) for s in slugs))
    main_html = page_head(page, [('Protagonisti', None)], 'Protagonisti', eyebrow='%d profili' % len(order),
                          lede="Guide e dilettanti, alpinisti e atleti: le persone che hanno spostato il limite, ciascuna collocata nella sua epoca. Filtra per disciplina o cerca un nome.")
    main_html += '''<div class="wrap" style="padding-block: clamp(36px,5vw,60px)">
<div class="filters" data-filter-group="disc"><span class="lab mono">Disciplina</span>%s</div>
<div class="filters"><input class="search" type="search" placeholder="Cerca un nome, una montagna…" aria-label="Cerca tra i protagonisti" data-filter-search></div>
<p class="count mono" data-filter-count data-all="%d profili in sei epoche">%d profili in sei epoche</p>
<div data-filter-scope>%s</div></div>''' % (chips, len(order), len(order), groups)
    write(page, 'Protagonisti', 'I %d protagonisti della storia dell\'arrampicata, epoca per epoca.' % len(order), 'protagonisti', main_html)

    # --- Epoche ---
    for n, ph in PHASES.items():
        ep = epoche.get(ph['slug'])
        page = 'epoche/%s.html' % ph['slug']
        if not ep:
            warnings.append('Epoca mancante: ' + ph['slug'])
            continue
        ph['title'] = ep['title']
        ph['summary'] = ep.get('summary', '')
        ph['grade'] = ep.get('grade', '')
    for n, ph in PHASES.items():
        ep = epoche.get(ph['slug'])
        if not ep:
            continue
        page = 'epoche/%s.html' % ph['slug']
        slugs = [s for s in order if people[s]['phase'] == n]
        gear = ''.join('<li><a href="%s">%s</a></li>' % (rel(page, 'materiali/%s.html' % m), E(t)) for m, t in PHASE_GEAR[n])
        aside = '''<aside><div class="facts-box"><h2>La fase in breve</h2><dl>
<dt>Anni</dt><dd><span class="big">%s</span></dd>
<dt>Grado limite</dt><dd><span class="big">%s</span></dd>
<dt>Materiali e tecniche</dt><dd><ul style="margin:4px 0 0;padding-left:1.1em">%s</ul></dd>
<dt>Protagonisti</dt><dd>%s</dd>
<dt>Cronologia</dt><dd><a href="%s">Gli eventi della fase nella linea del tempo</a></dd>
</dl></div></aside>''' % (E(ph['years']), E(ph['grade']), gear,
                          ', '.join('<a href="%s">%s</a>' % (rel(page, 'protagonisti/%s.html' % s), E(people[s]['title'])) for s in slugs),
                          rel(page, 'linea-del-tempo.html#fase-%d' % n))
        main_html = page_head(page, [('Epoche', 'epoche/index.html'), ('Fase %s' % ph['roman'], None)], ep['title'],
                              eyebrow='Fase %s · %s' % (ph['roman'], E(ph['years'])), lede=E(ep.get('summary', '')),
                              extra='<span class="roman-big" aria-hidden="true">%s</span>' % ph['roman'], seed=n * 1.3)
        main_html += '<div class="wrap article"><article class="prose">%s</article>%s</div>' % (fix_links(ep['body'], page), aside)
        main_html += '<section class="band-sec alt"><div class="wrap"><h2 class="sec-title">I protagonisti della fase %s</h2><ul class="cards">%s</ul></div></section>' % (
            ph['roman'], ''.join(person_card(page, s, people[s]) for s in slugs))
        if ep['events']:
            main_html += '<section class="band-sec"><div class="wrap"><h2 class="sec-title">Le date</h2>%s</div></section>' % steps_html(ep['events'])
        if ep['sources']:
            main_html += '<section class="band-sec"><div class="wrap"><h2 class="sec-title">Fonti</h2>%s</div></section>' % sources_html(ep['sources'])
        pv, nx = PHASES.get(n - 1), PHASES.get(n + 1)
        main_html += pager_html(page, pv and ('epoche/%s.html' % pv['slug'], 'Fase %s · %s' % (pv['roman'], pv.get('title', pv['short']))),
                                nx and ('epoche/%s.html' % nx['slug'], 'Fase %s · %s' % (nx['roman'], nx.get('title', nx['short']))))
        write(page, 'Fase %s · %s' % (ph['roman'], ep['title']), strip_tags(ep.get('summary', '')), 'epoche', main_html)
        collect(ep['events'], page, 'Fase %s' % ph['roman'], [])
        add_sources(ep['sources'], page, 'Fase %s' % ph['roman'])

    # --- Indice epoche ---
    page = 'epoche/index.html'
    main_html = page_head(page, [('Epoche', None)], 'Le sei fasi', eyebrow='1786 – oggi',
                          lede="La storia dell'alpinismo si divide tradizionalmente in sei fasi. Ognuna ha i suoi obiettivi, i suoi attrezzi, la sua etica e un grado limite che la generazione successiva supera.")
    main_html += '<section class="timeline" style="border-top:0"><div class="wrap">' + phases_block(page) + '</div></section>'
    write(page, 'Le sei fasi', "Le sei fasi della storia dell'alpinismo e dell'arrampicata, dal 1786 a oggi.", 'epoche', main_html)

    # --- Materiali e discipline ---
    for section, items, labels, keys, sec_title, cur in (
            ('materiali', mats, MAT_LABEL, MATERIALI, 'Materiali e tecniche', 'materiali'),
            ('discipline', discs, DISC_LABEL, DISCIPLINE, 'Discipline', 'discipline')):
        present = [k for k in keys if k in items]
        for k in keys:
            if k not in items:
                warnings.append('Pagina mancante: %s/%s' % (section, k))
        for i, k in enumerate(present):
            it = items[k]
            page = '%s/%s.html' % (section, k)
            ppl = [s for s in csv(it.get('people')) if s in people]
            phs = [int(x) for x in csv(it.get('phases')) if x.isdigit() and int(x) in PHASES]
            dl = ''
            if phs:
                dl += '<dt>Epoche</dt><dd><div class="tags">%s</div></dd>' % ''.join(
                    '<a class="tag" href="%s">Fase %s</a>' % (rel(page, 'epoche/%s.html' % PHASES[x]['slug']), PHASES[x]['roman']) for x in phs)
            if ppl:
                dl += '<dt>Protagonisti</dt><dd>%s</dd>' % ', '.join(
                    '<a href="%s">%s</a>' % (rel(page, 'protagonisti/%s.html' % s), E(people[s]['title'])) for s in ppl)
            others = ''.join('<li><a href="%s">%s</a></li>' % (rel(page, '%s/%s.html' % (section, o)), E(items[o]['title'])) for o in present if o != k)
            dl += '<dt>Nella stessa sezione</dt><dd><ul style="margin:4px 0 0;padding-left:1.1em">%s</ul></dd>' % others
            if section == 'discipline':
                dl += '<dt>Cronologia</dt><dd><a href="%s">Gli eventi della disciplina</a></dd>' % rel(page, 'linea-del-tempo.html#' + k)
            aside = '<aside><div class="facts-box"><h2>In breve</h2><dl>%s</dl></div></aside>' % dl
            main_html = page_head(page, [(sec_title, '%s/index.html' % section), (it['title'], None)], it['title'],
                                  eyebrow=sec_title, lede=E(it.get('summary', '')), seed=page_seed(page))
            main_html += '<div class="wrap article"><article class="prose">%s</article>%s</div>' % (fix_links(it['body'], page), aside)
            if it['events']:
                main_html += '<section class="band-sec alt"><div class="wrap"><h2 class="sec-title">Le tappe</h2>%s</div></section>' % steps_html(it['events'])
            if ppl:
                main_html += '<section class="band-sec"><div class="wrap"><h2 class="sec-title">Protagonisti</h2><ul class="cards">%s</ul></div></section>' % ''.join(
                    person_card(page, s, people[s]) for s in ppl)
            if it['sources']:
                main_html += '<section class="band-sec"><div class="wrap"><h2 class="sec-title">Fonti</h2>%s</div></section>' % sources_html(it['sources'])
            pv = present[i - 1] if i > 0 else None
            nx = present[i + 1] if i < len(present) - 1 else None
            main_html += pager_html(page, pv and ('%s/%s.html' % (section, pv), items[pv]['title']), nx and ('%s/%s.html' % (section, nx), items[nx]['title']))
            write(page, it['title'], strip_tags(it.get('summary', '')), cur, main_html)
            collect(it['events'], page, it['title'], [k] if section == 'discipline' else [])
            add_sources(it['sources'], page, it['title'])
        # indice di sezione
        page = '%s/index.html' % section
        intro = {'materiali': "Ogni salto di difficoltà ha avuto un attrezzo dietro, e ogni attrezzo ha aperto un dibattito su cosa fosse giusto usare. Scarpe, corde, protezioni e la scala dei gradi, dalle prime invenzioni a oggi.",
                 'discipline': "Dall'alpinismo delle grandi vette al boulder di pochi metri: i modi di arrampicare che sono nati lungo la strada, ciascuno con le sue regole, la sua etica e i suoi protagonisti."}[section]
        rows = ''.join('<li><a href="%s"><h3>%s</h3><p>%s</p></a></li>' % (rel(page, '%s/%s.html' % (section, k)), E(items[k]['title']), E(items[k].get('summary', ''))) for k in present)
        main_html = page_head(page, [(sec_title, None)], sec_title, eyebrow='%d approfondimenti' % len(present), lede=intro, seed=4 if section == 'materiali' else 5)
        main_html += '<div class="wrap" style="padding-block: clamp(40px,6vw,72px)"><ul class="rows">%s</ul></div>' % rows
        write(page, sec_title, intro, cur, main_html)

    # --- Pagine singole: glossario, chi siamo ---
    for k, cur in (('glossario', 'glossario'), ('chi-siamo', '')):
        it = pagine.get(k)
        if not it:
            warnings.append('Pagina mancante: ' + k)
            continue
        page = '%s.html' % k
        body = fix_links(it['body'], page)
        extra_top = ''
        if k == 'glossario':
            body, extra_top = glossary_letters(body)
        main_html = page_head(page, [(it['title'], None)], it['title'], lede=E(it.get('summary', '')), seed=7)
        main_html += '<div class="wrap article single"><article class="prose">%s%s</article></div>' % (extra_top, body)
        write(page, it['title'], strip_tags(it.get('summary', '')), cur, main_html)
        if it['sources']:
            add_sources(it['sources'], page, it['title'])

    # --- Linea del tempo ---
    page = 'linea-del-tempo.html'
    timeline.sort(key=lambda t: (t[0]['y'], t[0]['m'], t[0]['d'], t[1]))
    # Unisci gli eventi uguali citati da più pagine: stessa data e testo simile.
    def words(t):
        return set(w for w in re.findall(r'\w+', t.lower()) if len(w) > 3)
    merged = []
    for e, src_page, title, tags in timeline:
        w = words(e['text'])
        for m in merged:
            me = m['e']
            if me['y'] != e['y'] or (me['m'] and e['m'] and me['m'] != e['m']) or (me['d'] and e['d'] and me['d'] != e['d']):
                continue
            same_date = (me['m'], me['d']) == (e['m'], e['d'])
            inter = len(w & m['w']) / max(1, len(w | m['w']))
            if inter >= (0.3 if (same_date and e['d']) else 0.45):
                if (e['m'], e['d']) > (me['m'], me['d']) and not (me['d'] and not e['d']):
                    m['e'] = dict(me, m=e['m'], d=e['d'])  # tieni la data più precisa
                if src_page not in [o[0] for o in m['origins']]:
                    m['origins'].append((src_page, title))
                m['tags'] |= set(tags)
                if src_page.startswith('protagonisti/') and not m['origins'][0][0].startswith('protagonisti/'):
                    m['e'] = dict(e, m=max(e['m'], m['e']['m']), d=max(e['d'], m['e']['d']))  # testo della scheda protagonista
                break
        else:
            merged.append(dict(e=e, w=w, origins=[(src_page, title)], tags=set(tags)))
    merged.sort(key=lambda m: (m['e']['y'], m['e']['m'] or 13, m['e']['d'] or 32))
    timeline_n = len(merged)
    blocks = OrderedDict()  # fase -> anno -> [righe]
    for m in merged:
        e = m['e']
        ph = phase_of_year(e['y'])
        txt = (e['text'] + ' ' + ' '.join(t for _, t in m['origins'])).lower()
        links = ' · '.join('<a href="%s">%s →</a>' % (rel(page, pg), E(t)) for pg, t in m['origins'])
        blocks.setdefault(ph, OrderedDict()).setdefault(e['y'], []).append(
            '<li class="tl-ev" data-tags="fase-%d %s" data-text="%s"><span class="d">%s</span><span class="t">%s</span><span class="o">%s</span></li>' % (
                ph, ' '.join(sorted(m['tags'])), E(txt), E(fmt_date(e)), E(e['text']), links))
    rows = []
    for ph, years in blocks.items():
        ys = ''.join('<li class="tl-year" data-filter-container><h3>%d</h3><ul>%s</ul></li>' % (y, ''.join(evs)) for y, evs in years.items())
        rows.append('<li class="tl-block" data-filter-container><p class="tl-phase"><a href="%s">Fase %s · %s</a> <span class="mono">%s</span></p><ol class="tl">%s</ol></li>' % (
            rel(page, 'epoche/%s.html' % PHASES[ph]['slug']), PHASES[ph]['roman'], E(PHASES[ph].get('title', PHASES[ph]['short'])), E(PHASES[ph]['years']), ys))
    phase_chips = '<button class="chip" data-value="" aria-pressed="true">Tutte</button>' + ''.join(
        '<button class="chip" data-value="fase-%d" aria-pressed="false">%s</button>' % (n, p['roman']) for n, p in PHASES.items())
    disc_chips = '<button class="chip" data-value="" aria-pressed="true">Tutte</button>' + ''.join(
        '<button class="chip" data-value="%s" aria-pressed="false">%s</button>' % (d, DISC_LABEL[d]) for d in DISCIPLINE)
    n_ev = timeline_n
    main_html = page_head(page, [('Linea del tempo', None)], 'Linea del tempo', eyebrow='%d eventi · 1786 – oggi' % n_ev,
                          lede="Tutti gli eventi citati nel sito, in ordine. Filtra per fase o per disciplina, oppure cerca un nome o una montagna; ogni evento porta alla pagina da cui proviene.", seed=9)
    main_html += '''<div class="wrap" style="padding-block: clamp(36px,5vw,60px)">
<div class="filters" data-filter-group="fase"><span class="lab mono">Fase</span>%s</div>
<div class="filters" data-filter-group="disc"><span class="lab mono">Disciplina</span>%s</div>
<div class="filters"><input class="search" type="search" placeholder="Cerca: Cervino, Comici, 9a…" aria-label="Cerca nella linea del tempo" data-filter-search></div>
<p class="count mono" data-filter-count data-all="%d eventi">%d eventi</p>
<ol class="tl-blocks" data-filter-scope>%s</ol></div>''' % (phase_chips, disc_chips, n_ev, n_ev, ''.join(rows))
    write(page, 'Linea del tempo', "Cronologia della storia dell'alpinismo e dell'arrampicata dal 1786 a oggi.", 'linea', main_html)

    # --- Fonti ---
    page = 'fonti.html'
    general = pagine.get('fonti')
    def src_li(key):
        lst = all_sources[key]
        s = lst[0][0]
        pages_seen = OrderedDict()
        for _, pg, t in lst:
            pages_seen[pg] = t
        where = ', '.join('<a href="%s">%s</a>' % (rel(page, pg), E(t)) for pg, t in pages_seen.items())
        txt = E(s['text']) + (' · <a href="%s" rel="noopener">%s</a>' % (E(s['url']), E(short_url(s['url']))) if s['url'] else '')
        return '<li>%s<span class="where">Citata in: %s</span></li>' % (txt, where)
    web = sorted([k for k in all_sources if all_sources[k][0][0]['url']], key=lambda k: all_sources[k][0][0]['text'].lower())
    books = sorted([k for k in all_sources if not all_sources[k][0][0]['url']], key=lambda k: all_sources[k][0][0]['text'].lower())
    main_html = page_head(page, [('Fonti', None)], 'Fonti', eyebrow='%d fonti' % len(all_sources),
                          lede=E(general.get('summary', '')) if general else "Libri, articoli e siti consultati per scrivere le pagine.", seed=11)
    body = fix_links(general['body'], page) if general else ''
    body += '<h2>Libri e opere a stampa</h2><ul class="src-list">%s</ul>' % ''.join(src_li(k) for k in books)
    body += '<h2>Articoli e siti</h2><ul class="src-list">%s</ul>' % ''.join(src_li(k) for k in web)
    main_html += '<div class="wrap article single"><article class="prose">%s</article></div>' % body
    write(page, 'Fonti', "Bibliografia e fonti online del sito sulla storia dell'arrampicata.", '', main_html)

    # --- Home ---
    page = 'index.html'
    write(page, SITE, "La storia dell'alpinismo e dell'arrampicata dal Monte Bianco (1786) al 9c: sei epoche, 52 protagonisti, materiali, discipline e linea del tempo.", '', home_html(page, people, order))

    # --- Mappa del sito ---
    page = 'mappa-del-sito.html'
    PAGES[page] = 'Mappa del sito'
    write(page, 'Mappa del sito', 'Tutte le pagine del sito, sezione per sezione.', '', sitemap_html(page, people, order, mats, discs))

    check_links()
    write_seo_files()
    print('Pagine generate: %d in %s' % (len(PAGES), OUT))
    for w in warnings:
        print('ATTENZIONE:', w)


def person_card(page, slug, p, filt=False):
    ph = PHASES[p['phase']]
    attrs = ''
    if filt:
        tags = ' '.join(['fase-%d' % p['phase']] + csv(p.get('disciplines')))
        text = ' '.join([p['title'], p.get('fullname', ''), strip_tags(p.get('summary', '')), p.get('nation', '')]).lower()
        attrs = ' data-tags="%s" data-text="%s"' % (E(tags), E(text))
    return '<li%s><a class="card" href="%s"><span class="yr mono">%s · Fase %s</span><span class="nm">%s</span><span class="nt">%s</span></a></li>' % (
        attrs, rel(page, 'protagonisti/%s.html' % slug), E(p.get('key_year', '')), ph['roman'], E(p['title']), E(p.get('summary', '')))


def phases_block(page, home=False):
    flex = {1: 84, 2: 30, 3: 45, 4: 15, 5: 20, 6: 46}
    bands = ''.join('<button class="band" data-phase="%d" style="flex: %d" aria-pressed="false" title="Fase %s · %s">%s</button>' % (
        n, flex[n], p['roman'], E(p['years']), p['roman']) for n, p in PHASES.items())
    cards = ''
    for n, p in PHASES.items():
        cards += '''<li class="phase" id="fase-%d">
  <div class="phase-top"><span class="roman">%s</span><span class="years mono">%s</span></div>
  <h3>%s</h3>
  <p>%s</p>
  <div class="phase-foot"><span class="grade">Grado limite<b>%s</b></span><a class="more" href="%s">Leggi →</a></div>
</li>''' % (n, p['roman'], E(p['years'].replace('–', ' – ')), E(p.get('title', p['short'])), E(p.get('summary', '')), E(p.get('grade', '')),
            rel(page, 'epoche/%s.html' % p['slug']))
    return '''<div class="axis">
  <div class="bands" role="group" aria-label="Seleziona una fase">%s</div>
  <div class="ticks" aria-hidden="true">
    <span style="left: 0%%">1786</span><span class="t-opt" style="left: 5.83%%">1800</span><span style="left: 26.67%%">1850</span>
    <span style="left: 47.5%%">1900</span><span style="left: 68.33%%">1950</span><span class="t-opt" style="left: 89.17%%">2000</span><span style="left: 100%%">oggi</span>
  </div>
  <p class="axis-note mono">Larghezza delle fasce in scala con la durata</p>
</div>
<ol class="phases">%s</ol>''' % (bands, cards)


def glossary_letters(body):
    """Inserisce i separatori per lettera prima delle voci e restituisce l'indice alfabetico."""
    letters = []

    def first_letter(term):
        t = strip_tags(term).strip().upper()
        t = t.translate(str.maketrans('ÀÁÈÉÌÒÙÜÖÄ', 'AAEEIOUUOA'))
        return t[:1] if t[:1].isalpha() else '#'
    out, last = [], None
    for m in re.finditer(r'(<dt\b[^>]*>(.*?)</dt>)|((?s:.)+?(?=<dt\b|$))', body):
        if m.group(1):
            L = first_letter(m.group(2))
            if L != last:
                out.append('</dl><p class="letter" id="lettera-%s">%s</p><dl>' % (L.lower(), L))
                letters.append(L)
                last = L
            out.append(m.group(1))
        else:
            out.append(m.group(0))
    body = ''.join(out)
    # pulizia di eventuali <dl></dl> vuoti creati dai separatori
    body = re.sub(r'<dl>\s*</dl>', '', body)
    idx = '<nav class="gloss-index" aria-label="Lettere">%s</nav>' % ''.join('<a href="#lettera-%s">%s</a>' % (L.lower(), L) for L in letters)
    return body, idx


def home_html(page, people, order):
    r = lambda t: rel(page, t)
    feat = ['paul-preuss', 'emilio-comici', 'walter-bonatti', 'reinhold-messner', 'manolo', 'wolfgang-gullich', 'lynn-hill', 'alex-honnold']
    feat = [s for s in feat if s in people]
    gear_cols = [
        ('calzature', 'Calzature', 'Dagli scarponi chiodati alla gomma che si incolla alla roccia.',
         [('Anni \'30', 'Scarponi chiodati per il ghiaccio, pedule di canapa per la roccia'), ('1937', 'Vitale Bramani inventa la suola Vibram "Carrarmato"'), ('Inizio anni \'80', 'Boreal Firé, la prima scarpetta in gomma adesiva')]),
        ('corde', 'Corde', 'Dalla canapa ritorta, pesante e fragile, al nylon che assorbe la caduta.',
         [('Fino al 1940', 'Corde di canapa ritorta, che marciscono e si spezzano'), ('1953', 'Edelrid presenta la prima corda kernmantel, anima e calza'), ('1964', 'Le prime corde dinamiche che reggono più cadute')]),
        ('protezioni', 'Protezioni', 'Dal chiodo piantato a martellate alle protezioni che non lasciano traccia.',
         [('1910 circa', 'Il moschettone entra in arrampicata con Otto Herzog e Hans Dülfer'), ('1967', 'Robbins sale Nutcracker solo con i nut: nasce il clean climbing'), ('1978', 'Il Friend di Ray Jardine protegge le fessure parallele')]),
        ('gradi', 'Gradi', "Una scala nata chiusa al sesto grado e poi aperta verso l'alto.",
         [('1925–26', 'Welzenbach e Rudatis codificano la prima scala delle difficoltà'), ('1977', 'La UIAA apre la scala al settimo grado'), ('Oggi', 'La scala francese, aperta per natura, arriva al 9c')]),
    ]
    gear = ''
    for slug, t, d, steps in gear_cols:
        gear += '<li class="gear-col"><h3>%s</h3><p>%s</p><ol class="steps">%s</ol><a class="more" href="%s">%s →</a></li>' % (
            t, d, ''.join('<li><span class="when">%s</span><span class="what">%s</span></li>' % (E(w), E(x)) for w, x in steps), r('materiali/%s.html' % slug), t)
    ppl = ''.join('<li><a class="card" href="%s"><span class="yr mono">%s · Fase %s</span><span class="nm">%s</span><span class="nt">%s</span></a></li>' % (
        r('protagonisti/%s.html' % s), E(people[s].get('key_year', '')), PHASES[people[s]['phase']]['roman'], E(people[s]['title']), E(people[s].get('summary', ''))) for s in feat)
    return f'''<section class="hero" aria-labelledby="hero-title">
  <canvas class="contours" aria-hidden="true"></canvas>
  <div class="wrap">
    <div>
      <p class="eyebrow mono">Due secoli di verticale</p>
      <h1 id="hero-title">Dal Monte Bianco <span class="thin">al</span> 9c</h1>
      <p class="lede">L'8 agosto 1786 Paccard e Balmat raggiungono la vetta del Monte Bianco. Da allora ogni generazione ha spostato più in alto il limite di ciò che sembrava impossibile. Questa è la storia di come ci siamo arrivati: le vie, le persone, gli attrezzi e le idee.</p>
      <div class="ctas">
        <a class="btn primary" href="#fasi">Percorri le sei fasi <span aria-hidden="true">↓</span></a>
        <a class="btn" href="{r('protagonisti/index.html')}">Incontra i protagonisti</a>
      </div>
    </div>
    <div class="ladder-box">
      <ol class="ladder" aria-label="Il limite della difficoltà nel tempo">
        <li><span class="g">III</span><span class="bar">1786 · Monte Bianco</span></li>
        <li><span class="g">IV+</span><span class="bar">1881 · Grépon</span></li>
        <li><span class="g">V</span><span class="bar">1911 · Preuss, Dülfer</span></li>
        <li><span class="g">VI</span><span class="bar">1925 · Civetta</span></li>
        <li><span class="g">VII</span><span class="bar">1977 · Pumprisse</span></li>
        <li><span class="g">9a</span><span class="bar">1991 · Action Directe</span></li>
        <li><span class="g">9c</span><span class="bar">2017 · Silence</span></li>
      </ol>
      <p class="ladder-cap mono">Il grado limite, anno per anno</p>
    </div>
  </div>
</section>

<section class="intro" aria-labelledby="intro-title">
  <div class="wrap">
    <h2 class="kicker" id="intro-title">Una storia di limiti superati</h2>
    <div>
      <p>Per quasi un secolo l'obiettivo è la vetta, raggiunta per la via più facile. Poi l'attenzione si sposta sulle pareti, sulla difficoltà, sullo stile. Il chiodo, il moschettone, la suola Vibram, i nut e infine lo spit cambiano ciò che si può salire, e ogni attrezzo apre un dibattito su ciò che è giusto salire.</p>
      <p>Per decenni la scala delle difficoltà resta chiusa al sesto grado, considerato il limite umano. Nel 1977 la UIAA riconosce il settimo e la scala si apre verso l'alto. Oggi l'arrampicata è uno sport autonomo, con le sue falesie, le sue gare e il suo 9c, ma porta ancora con sé le domande di Mummery e di Preuss.</p>
      <div class="facts mono">
        <span><b>6</b> fasi storiche</span>
        <span><b>{len(order)}</b> protagonisti</span>
        <span><b>240</b> anni di salite</span>
      </div>
      <div class="home-link-row">
        <a class="btn" href="{r('linea-del-tempo.html')}">La linea del tempo</a>
        <a class="btn" href="{r('discipline/index.html')}">Le discipline</a>
        <a class="btn" href="{r('glossario.html')}">Il glossario</a>
      </div>
    </div>
  </div>
</section>

<section class="timeline" id="fasi" aria-labelledby="fasi-title">
  <div class="wrap">
    <div class="sec-head">
      <h2 id="fasi-title">Le sei fasi</h2>
      <p>La storia dell'alpinismo si divide tradizionalmente in sei fasi, dalla prima salita del Monte Bianco all'arrampicata sportiva di oggi.</p>
    </div>
    {phases_block(page)}
  </div>
</section>

<section class="gear" id="materiali" aria-labelledby="gear-title">
  <div class="wrap">
    <div class="sec-head">
      <h2 id="gear-title">Materiali e tecniche</h2>
      <p>Ogni salto di difficoltà ha avuto un attrezzo dietro. Scarpe, corde, protezioni e la scala dei gradi, dalle prime invenzioni a oggi.</p>
    </div>
    <ul class="gear-grid">{gear}</ul>
  </div>
</section>

<section class="people" id="protagonisti" aria-labelledby="people-title">
  <div class="wrap">
    <div class="sec-head">
      <h2 id="people-title">Protagonisti</h2>
      <p>Cinquantadue profili, ciascuno collocato nella sua fase. Qualche nome per cominciare.</p>
    </div>
    <ul class="cards">{ppl}</ul>
    <div class="all"><a class="btn" href="{r('protagonisti/index.html')}">Tutti i {len(order)} profili →</a></div>
  </div>
</section>
'''


def sitemap_html(page, people, order, mats, discs):
    r = lambda t: rel(page, t)

    def li(href, label, cls=''):
        return '<li%s><a href="%s">%s</a><span class="url">%s</span></li>' % (' class="%s"' % cls if cls else '', r(href), E(label), E(href))
    ep = li('epoche/index.html', 'Le sei fasi', 'idx') + ''.join(
        li('epoche/%s.html' % p['slug'], '%s · %s' % (p['roman'], p.get('title', p['short']))) for p in PHASES.values())
    mt = li('materiali/index.html', 'Materiali e tecniche', 'idx') + ''.join(li('materiali/%s.html' % k, mats[k]['title']) for k in MATERIALI if k in mats)
    dc = li('discipline/index.html', 'Discipline', 'idx') + ''.join(li('discipline/%s.html' % k, discs[k]['title']) for k in DISCIPLINE if k in discs)
    sv = li('index.html', 'Home', 'idx') + li('linea-del-tempo.html', 'Linea del tempo') + li('glossario.html', 'Glossario') + \
        li('fonti.html', 'Fonti') + li('chi-siamo.html', 'Chi siamo') + li('mappa-del-sito.html', 'Mappa del sito')
    pm = ''
    for n, p in PHASES.items():
        pm += '<div><h3>Fase %s · %s</h3><ul class="map-list">%s</ul></div>' % (p['roman'], E(p['years']), ''.join(
            '<li><a href="%s">%s</a></li>' % (r('protagonisti/%s.html' % s), E(people[s]['title'])) for s in order if people[s]['phase'] == n))
    total = len(PAGES) + 1
    head = page_head(page, [('Mappa del sito', None)], 'Mappa del sito',
                     lede='Tutte le pagine del sito, sezione per sezione: le sei epoche, %d protagonisti, quattro approfondimenti su materiali e tecniche, sei discipline e le pagine di servizio.' % len(order), seed=13)
    return head + f'''<div class="wrap map-body">
  <div class="map-row">
    <section class="map-sec"><h2>Epoche <span class="n">7 pagine</span></h2><ul class="map-list">{ep}</ul></section>
    <section class="map-sec"><h2>Materiali e tecniche <span class="n">5 pagine</span></h2><ul class="map-list">{mt}</ul></section>
    <section class="map-sec"><h2>Discipline <span class="n">7 pagine</span></h2><ul class="map-list">{dc}</ul></section>
    <section class="map-sec"><h2>Home e servizio <span class="n">6 pagine</span></h2><ul class="map-list">{sv}</ul></section>
  </div>
  <section class="map-sec">
    <h2>Protagonisti <span class="n">{len(order) + 1} pagine</span></h2>
    <ul class="map-list" style="margin-bottom:8px">{li('protagonisti/index.html', 'Tutti i protagonisti', 'idx')}</ul>
    <div class="people-map">{pm}</div>
  </section>
</div>'''


def write_seo_files():
    """sitemap.xml per i motori di ricerca (va inviata da Google Search Console).

    Niente robots.txt: su nucce.github.io/storia-arrampicata/ i motori lo cercherebbero solo alla radice del dominio.
    """
    urls = ''.join('  <url><loc>%s</loc></url>\n' % E(page_url(pg)) for pg in sorted(PAGES))
    with open(os.path.join(OUT, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s</urlset>\n' % urls)


def check_links():
    bad = []
    ids_cache = {}
    for root, dirs, files in os.walk(OUT):
        dirs[:] = [d for d in dirs if not d.startswith(('.', '_'))]  # solo le pagine del sito, non il generatore
        for fn in files:
            if not fn.endswith('.html'):
                continue
            path = os.path.join(root, fn)
            src = open(path, encoding='utf-8').read()
            for href in re.findall(r'href="([^"]+)"', src):
                if href.startswith(('http', 'mailto:')):
                    continue
                target, _, frag = href.partition('#')
                tpath = os.path.normpath(os.path.join(root, target)) if target else path
                if not os.path.exists(tpath):
                    bad.append('%s → %s' % (os.path.relpath(path, OUT), href))
                    continue
                if frag and tpath.endswith('.html'):
                    if tpath not in ids_cache:
                        ids_cache[tpath] = set(re.findall(r'id="([^"]+)"', open(tpath, encoding='utf-8').read()))
                    known_js = frag.startswith('fase-') or frag in DISCIPLINE
                    if frag not in ids_cache[tpath] and not known_js:
                        bad.append('%s → %s (ancora mancante)' % (os.path.relpath(path, OUT), href))
    for b in sorted(set(bad)):
        warnings.append('Link rotto: ' + b)


if __name__ == '__main__':
    main()
