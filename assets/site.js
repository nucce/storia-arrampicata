(function () {
  'use strict';
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Curve di livello: una carta topografica discreta dietro le testate.
  function noise(x, y) {
    return Math.sin(x * 1.7 + Math.cos(y * 1.3)) * 0.5 +
           Math.sin(y * 2.3 + x * 0.6) * 0.3 +
           Math.cos((x - y) * 3.1) * 0.15 +
           Math.sin(x * 5.2 + y * 4.7) * 0.05;
  }
  function drawContours(canvas) {
    var box = canvas.parentElement;
    var seed = parseFloat(canvas.getAttribute('data-seed') || '0');
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var w = box.clientWidth, h = box.clientHeight;
    if (!w || !h) return;
    canvas.width = w * dpr; canvas.height = h * dpr;
    var ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    ctx.strokeStyle = getComputedStyle(document.documentElement).getPropertyValue('--contour').trim();
    ctx.lineWidth = 1;
    var step = 7, cols = Math.ceil(w / step) + 1, rows = Math.ceil(h / step) + 1;
    var field = new Float32Array(cols * rows);
    for (var j = 0; j < rows; j++) for (var i = 0; i < cols; i++) {
      var x = i * step / 260 + seed, y = j * step / 260 + seed * 0.7;
      field[j * cols + i] = noise(x, y) + (i / cols) * 1.2 - (j / rows) * 0.9;
    }
    for (var level = -1.6; level < 2.4; level += 0.12) {
      ctx.beginPath();
      for (var j2 = 0; j2 < rows - 1; j2++) for (var i2 = 0; i2 < cols - 1; i2++) {
        var a = field[j2 * cols + i2], b = field[j2 * cols + i2 + 1],
            c = field[(j2 + 1) * cols + i2 + 1], d = field[(j2 + 1) * cols + i2];
        var x0 = i2 * step, y0 = j2 * step, pts = [];
        if ((a < level) !== (b < level)) pts.push([x0 + step * (level - a) / (b - a), y0]);
        if ((b < level) !== (c < level)) pts.push([x0 + step, y0 + step * (level - b) / (c - b)]);
        if ((c < level) !== (d < level)) pts.push([x0 + step * (level - d) / (c - d), y0 + step]);
        if ((d < level) !== (a < level)) pts.push([x0, y0 + step * (level - a) / (d - a)]);
        if (pts.length >= 2) { ctx.moveTo(pts[0][0], pts[0][1]); ctx.lineTo(pts[1][0], pts[1][1]); }
        if (pts.length === 4) { ctx.moveTo(pts[2][0], pts[2][1]); ctx.lineTo(pts[3][0], pts[3][1]); }
      }
      ctx.stroke();
    }
  }
  var canvases = document.querySelectorAll('canvas.contours');
  function drawAll() { canvases.forEach(drawContours); }
  if (canvases.length) {
    drawAll();
    var t; window.addEventListener('resize', function () { clearTimeout(t); t = setTimeout(drawAll, 150); });
  }

  // Tema chiaro/scuro: di base segue il sistema; la scelta dell'utente resta salvata.
  // Se la scelta coincide con il tema di sistema, si torna a seguire il sistema.
  var root = document.documentElement;
  var mq = window.matchMedia('(prefers-color-scheme: dark)');
  var themeBtn = document.querySelector('.theme-toggle');
  function isDark() {
    var t = root.getAttribute('data-theme');
    return t ? t === 'dark' : mq.matches;
  }
  function syncThemeBtn() {
    if (!themeBtn) return;
    var label = isDark() ? 'Passa al tema chiaro' : 'Passa al tema scuro';
    themeBtn.setAttribute('aria-label', label);
    themeBtn.title = label;
    themeBtn.classList.toggle('is-dark', isDark());
  }
  if (themeBtn) {
    themeBtn.addEventListener('click', function () {
      var next = isDark() ? 'light' : 'dark';
      var followSystem = (next === 'dark') === mq.matches;
      if (followSystem) root.removeAttribute('data-theme'); else root.setAttribute('data-theme', next);
      try { if (followSystem) localStorage.removeItem('tema'); else localStorage.setItem('tema', next); } catch (e) {}
      syncThemeBtn();
      drawAll();
    });
    syncThemeBtn();
  }
  function onSystemChange() { syncThemeBtn(); drawAll(); }
  if (mq.addEventListener) mq.addEventListener('change', onSystemChange);
  else if (mq.addListener) mq.addListener(onSystemChange);

  // Pulsante "torna in cima": compare dopo un po' di scorrimento.
  var toTop = document.querySelector('.to-top');
  if (toTop) {
    var onScroll = function () { toTop.classList.toggle('is-visible', window.scrollY > 400); };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    toTop.addEventListener('click', function (e) {
      e.preventDefault();
      window.scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' });
      var skip = document.querySelector('.brand');
      if (skip) skip.focus({ preventScroll: true });
    });
  }

  // Menu mobile: chiudi con Esc o cliccando fuori.
  var menu = document.querySelector('.menu');
  if (menu) {
    document.addEventListener('click', function (e) { if (menu.open && !menu.contains(e.target)) menu.open = false; });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') menu.open = false; });
  }

  // Fasce della linea del tempo in home e nell'indice delle epoche.
  var bands = document.querySelectorAll('.band');
  bands.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var n = btn.getAttribute('data-phase');
      bands.forEach(function (b) { b.setAttribute('aria-pressed', b === btn ? 'true' : 'false'); });
      document.querySelectorAll('.phase').forEach(function (p) { p.classList.toggle('is-active', p.id === 'fase-' + n); });
      var card = document.getElementById('fase-' + n);
      if (!card) return;
      var r = card.getBoundingClientRect();
      if (r.top < 60 || r.bottom > window.innerHeight) card.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'center' });
    });
  });

  // Filtri generici: gruppi di pulsanti [data-filter-group] e casella di ricerca [data-filter-search].
  // Ogni elemento filtrabile ha data-tags="fase-3 alpinismo ..." e data-text="testo in minuscolo".
  var scope = document.querySelector('[data-filter-scope]');
  if (scope) {
    var items = scope.querySelectorAll('[data-tags]');
    var groups = document.querySelectorAll('[data-filter-group]');
    var search = document.querySelector('[data-filter-search]');
    var counter = document.querySelector('[data-filter-count]');
    var state = {};
    function apply() {
      var q = search ? search.value.trim().toLowerCase() : '';
      var shown = 0;
      items.forEach(function (it) {
        var tags = ' ' + it.getAttribute('data-tags') + ' ';
        var ok = true;
        Object.keys(state).forEach(function (g) { if (state[g] && tags.indexOf(' ' + state[g] + ' ') < 0) ok = false; });
        if (ok && q) ok = (it.getAttribute('data-text') || it.textContent.toLowerCase()).indexOf(q) >= 0;
        it.hidden = !ok;
        if (ok) shown++;
      });
      // Nascondi i contenitori rimasti vuoti.
      scope.querySelectorAll('[data-filter-container]').forEach(function (c) {
        c.hidden = !c.querySelector('[data-tags]:not([hidden])');
      });
      if (counter) counter.textContent = shown === items.length ? counter.getAttribute('data-all') : shown + ' risultati su ' + items.length;
    }
    groups.forEach(function (g) {
      var name = g.getAttribute('data-filter-group');
      g.querySelectorAll('.chip').forEach(function (chip) {
        chip.addEventListener('click', function () {
          var v = chip.getAttribute('data-value') || '';
          state[name] = v;
          g.querySelectorAll('.chip').forEach(function (c) { c.setAttribute('aria-pressed', c === chip ? 'true' : 'false'); });
          apply();
        });
      });
    });
    if (search) search.addEventListener('input', apply);
    // Filtro iniziale da indirizzo, es. linea-del-tempo.html#fase-3 o #bouldering
    var h = location.hash.slice(1);
    if (h) {
      var pre = document.querySelector('.chip[data-value="' + h.replace(/[^a-z0-9-]/g, '') + '"]');
      if (pre) pre.click();
    }
    apply();
  }
})();
