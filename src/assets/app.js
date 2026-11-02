// Legal Databank client: theme, citation tools, My shelf, contents filter, search and offline support.
(function () {
  'use strict';

  var BASE = document.body.dataset.base || '';
  var PAGE = document.body.dataset.page;
  var SHELF_KEY = 'ldb-shelf';

  // ---------- small utilities ----------
  function store(key, value) {
    try {
      if (value === undefined) return JSON.parse(localStorage.getItem(key) || 'null');
      localStorage.setItem(key, JSON.stringify(value));
    } catch (_) {
      return null;
    }
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function reEscape(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  var toastTimer;
  function toast(msg) {
    var el = document.getElementById('toast');
    if (!el) return;
    el.textContent = msg;
    el.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
      el.classList.remove('show');
    }, 2200);
  }

  function copy(text, label) {
    function fallback() {
      var ta = document.createElement('textarea');
      ta.value = text;
      ta.setAttribute('readonly', '');
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      try {
        document.execCommand('copy');
        toast(label + ' copied');
      } catch (_) {
        toast('Copy failed. Select the text manually.');
      }
      document.body.removeChild(ta);
    }
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(function () {
        toast(label + ' copied');
      }, fallback);
    } else {
      fallback();
    }
  }

  // Wraps each match of `terms` in <mark>, escaping everything else.
  function highlight(raw, terms) {
    var t = terms.filter(Boolean);
    if (!t.length) return esc(raw);
    var re = new RegExp('(^|[^a-z0-9])(' + t.map(reEscape).sort(function (a, b) { return b.length - a.length; }).join('|') + ')', 'ig');
    var out = '';
    var last = 0;
    var m;
    while ((m = re.exec(raw))) {
      var at = m.index + m[1].length;
      out += esc(raw.slice(last, at)) + '<mark>' + esc(m[2]) + '</mark>';
      last = at + m[2].length;
      if (!m[0].length) re.lastIndex++;
    }
    return out + esc(raw.slice(last));
  }

  // Search words match only at the start of a word, so "gst" does not find "amongst" and "ITO" not "monitoring".
  function wordStart(t) {
    return new RegExp('(?:^|[^a-z0-9])' + reEscape(t), 'g');
  }
  function countWord(re, text) {
    re.lastIndex = 0;
    var n = 0;
    while (re.exec(text)) n++;
    return n;
  }
  function hasWord(re, text) {
    re.lastIndex = 0;
    return re.test(text);
  }

  // ---------- theme ----------
  var themeBtn = document.getElementById('theme-toggle');
  if (themeBtn) {
    themeBtn.addEventListener('click', function () {
      var root = document.documentElement;
      var current = root.dataset.theme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
      var next = current === 'dark' ? 'light' : 'dark';
      root.dataset.theme = next;
      try {
        localStorage.setItem('ldb-theme', next);
      } catch (_) {}
    });
  }

  // ---------- My shelf ----------
  function shelf() {
    return store(SHELF_KEY) || [];
  }
  function shelfKey(item) {
    return item.act + '#' + item.no;
  }
  function isSaved(act, no) {
    return shelf().some(function (s) {
      return s.act === act && s.no === no;
    });
  }
  function toggleSaved(item) {
    var list = shelf();
    var k = shelfKey(item);
    var exists = list.some(function (s) { return shelfKey(s) === k; });
    list = exists ? list.filter(function (s) { return shelfKey(s) !== k; }) : [item].concat(list);
    store(SHELF_KEY, list);
    return !exists;
  }

  function shelfItemHtml(s) {
    return (
      '<li class="shelf-item"><a href="' + BASE + 'acts/' + esc(s.act) + '/index.html#' + esc(s.anchor) + '">' +
      '<span class="act-title">' + esc(s.unit + ' ' + s.no + ' — ' + s.title) + '</span>' +
      '<span class="act-meta">' + esc(s.actTitle) + '</span></a>' +
      '<button type="button" class="linkish" data-remove="' + esc(shelfKey(s)) + '">Remove</button></li>'
    );
  }

  function renderShelf(el, limit) {
    var list = shelf();
    if (limit && !list.length) {
      el.innerHTML = '';
      return;
    }
    if (!list.length) {
      el.innerHTML = '<p class="empty">Nothing saved yet. Open an instrument and press <em>Save</em> on a provision.</p>';
      return;
    }
    var shown = limit ? list.slice(0, limit) : list;
    el.innerHTML =
      (limit ? '<h2 class="shelf-heading">My shelf</h2>' : '') +
      '<ul class="act-list">' + shown.map(shelfItemHtml).join('') + '</ul>' +
      (limit && list.length > limit ? '<p><a href="' + BASE + 'shelf.html">See all ' + list.length + ' saved provisions</a></p>' : '') +
      (!limit ? '<p><button type="button" class="btn" id="copy-shelf">Copy all citations</button></p>' : '');
    el.querySelectorAll('[data-remove]').forEach(function (b) {
      b.addEventListener('click', function () {
        store(SHELF_KEY, shelf().filter(function (s) { return shelfKey(s) !== b.dataset.remove; }));
        renderShelf(el, limit);
      });
    });
    var all = el.querySelector('#copy-shelf');
    if (all) {
      all.addEventListener('click', function () {
        copy(list.map(function (s) { return s.cite; }).join('\n'), 'Citations');
      });
    }
  }

  // ---------- instrument page ----------
  var actEl = document.querySelector('.act-layout');
  if (actEl) {
    var actId = actEl.dataset.act;
    var actTitle = actEl.dataset.actTitle;
    var unit = actEl.dataset.unit;

    document.querySelectorAll('.provision').forEach(function (prov) {
      var no = prov.dataset.no;
      var pin = prov.querySelector('[data-action="pin"]');
      function syncPin() {
        var on = isSaved(actId, no);
        pin.setAttribute('aria-pressed', on ? 'true' : 'false');
        pin.textContent = on ? 'Saved' : 'Save';
      }
      syncPin();

      prov.querySelector('.prov-tools').addEventListener('click', function (ev) {
        var btn = ev.target.closest('button');
        if (!btn) return;
        var cite = prov.dataset.cite;
        var url = location.href.split('#')[0].split('?')[0] + '#' + prov.id;
        var action = btn.dataset.action;
        if (action === 'cite') copy(cite, 'Citation');
        if (action === 'link') copy(url, 'Link');
        if (action === 'quote') {
          var body = Array.prototype.map
            .call(prov.querySelectorAll('.prov-body p'), function (p) {
              var level = Number((p.className.match(/l(\d)/) || [0, 0])[1]);
              var clean = p.cloneNode(true);
              clean.querySelectorAll('.fnref').forEach(function (x) { x.remove(); });
              return new Array(level + 1).join('    ') + clean.textContent.replace(/\s{2,}/g, ' ').trim();
            })
            .join('\n');
          copy(no + '. ' + prov.dataset.title + '.—\n' + body + '\n\n— ' + cite, 'Quotation');
        }
        if (action === 'pin') {
          var added = toggleSaved({
            act: actId,
            actTitle: actTitle,
            unit: unit,
            no: no,
            title: prov.dataset.title,
            anchor: prov.id,
            cite: cite,
            savedAt: new Date().toISOString(),
          });
          syncPin();
          toast(added ? 'Saved to My shelf' : 'Removed from My shelf');
        }
      });
    });

    // Contents filter
    var filter = document.getElementById('toc-filter');
    if (filter) {
      filter.addEventListener('input', function () {
        var q = filter.value.trim().toLowerCase();
        document.querySelectorAll('.toc-list > li').forEach(function (part) {
          var any = false;
          part.querySelectorAll('ol li').forEach(function (li) {
            var hit = !q || li.textContent.toLowerCase().indexOf(q) !== -1;
            li.hidden = !hit;
            any = any || hit;
          });
          part.hidden = !any;
        });
      });
    }

    // "Show amendment notes" opens every notes list on the page; the choice is remembered.
    var showNotes = document.getElementById('show-notes');
    var NOTES_KEY = 'ldb-show-notes';
    function setNotes(open) {
      document.querySelectorAll('details.prov-fns').forEach(function (d) { d.open = open; });
    }
    if (showNotes) {
      showNotes.checked = store(NOTES_KEY) === true;
      if (showNotes.checked) setNotes(true);
      showNotes.addEventListener('change', function () {
        setNotes(showNotes.checked);
        store(NOTES_KEY, showNotes.checked);
      });
    }

    // A link to a note (#s-2-fn-9-14) opens the notes list that holds it.
    function revealHash() {
      var el = location.hash && document.getElementById(decodeURIComponent(location.hash.slice(1)));
      if (!el) return null;
      var d = el.closest('details');
      if (d) d.open = true;
      return el;
    }
    window.addEventListener('hashchange', revealHash);

    // Highlight search terms passed from the search page (?hl=...)
    var hl = new URLSearchParams(location.search).get('hl');
    var target = revealHash();
    if (hl && target) {
      var terms = parseQuery(hl).terms;
      var blocks = target.matches('li') ? [target] : target.querySelectorAll('.prov-body p');
      Array.prototype.forEach.call(blocks, function (p) {
        p.innerHTML = highlight(p.textContent, terms);
      });
      target.classList.add('flash');
      target.scrollIntoView({ block: 'center' });
    }
  }

  // ---------- search ----------
  function norm(s) {
    return String(s).toLowerCase().replace(/[^a-z0-9]+/g, '');
  }

  function parseQuery(q) {
    var phrases = [];
    var rest = q.replace(/"([^"]+)"/g, function (_, p) {
      phrases.push(p.trim().toLowerCase());
      return ' ';
    });
    var words = rest.toLowerCase().split(/\s+/).filter(function (w) { return w.length > 1 || /\d/.test(w); });
    return { phrases: phrases, words: words, terms: phrases.concat(words) };
  }

  function findAct(index, text) {
    var n = norm(text);
    if (!n) return null;
    var best = null;
    index.acts.forEach(function (a) {
      var names = [a.title, a.id].concat(a.aliases).map(norm);
      if (names.indexOf(n) !== -1) best = best || a;
    });
    if (best) return best;
    index.acts.forEach(function (a) {
      if (!best && norm(a.title).indexOf(n) === 0) best = a;
    });
    return best;
  }

  // "s 111 ITO", "section 3 AMLA", "rule 1 ITR", "ITO s. 111", "CA 2017 204"
  function jump(index, q) {
    var m =
      /^\s*(?:s|sec|section|r|rule|reg|regulation)\.?\s*(\d+[a-z]*)\s+(?:of\s+(?:the\s+)?)?(.+)$/i.exec(q) ||
      null;
    var no, actText;
    if (m) {
      no = m[1];
      actText = m[2];
    } else {
      m = /^\s*(.+?)\s+(?:s|sec|section|r|rule|reg|regulation)?\.?\s*(\d+[a-z]*)\s*$/i.exec(q);
      if (!m) return null;
      actText = m[1];
      no = m[2];
    }
    var act = findAct(index, actText);
    if (!act) return null;
    var prov = index.provisions.find(function (p) {
      return p.act === act.id && p.no && p.no.toLowerCase() === no.toLowerCase();
    });
    return prov ? { act: act, prov: prov } : null;
  }

  function runSearch(index, q, cat, type) {
    var parsed = parseQuery(q);
    if (!parsed.terms.length) return [];
    var res = parsed.terms.map(wordStart);
    var acts = {};
    index.acts.forEach(function (a) { acts[a.id] = a; });
    var out = [];
    index.provisions.forEach(function (p) {
      var a = acts[p.act];
      if (cat && a.categories.indexOf(cat) === -1) return;
      if (type && a.type !== type) return;
      var title = p.title.toLowerCase();
      var text = p.text.toLowerCase();
      var actHay = (a.title + ' ' + a.aliases.join(' ')).toLowerCase();
      var score = 0;
      var ok = res.every(function (re) {
        var inTitle = hasWord(re, title);
        var hits = countWord(re, text);
        var inText = hits > 0;
        var inAct = hasWord(re, actHay);
        if (inTitle) score += 10;
        if (inText) score += 2 + Math.min(hits - 1, 5);
        if (inAct) score += 1;
        return inTitle || inText || inAct;
      });
      if (!ok) return;
      parsed.phrases.forEach(function () { score += 3; });
      out.push({ p: p, a: a, score: score });
    });
    out.sort(function (x, y) { return y.score - x.score; });
    return out;
  }

  function snippet(text, terms) {
    var lower = text.toLowerCase();
    var at = -1;
    terms.some(function (t) {
      var m = wordStart(t).exec(lower);
      at = m ? m.index + m[0].length - t.length : -1;
      return at !== -1;
    });
    var start = Math.max(0, at - 90);
    var s = text.slice(start, start + 260).replace(/\n/g, ' ');
    return (start > 0 ? '… ' : '') + s + (start + 260 < text.length ? ' …' : '');
  }

  // Laws and rules whose title, short names or topics (search guide) contain every word searched for.
  function findInstruments(index, q, cat, type) {
    var parsed = parseQuery(q);
    if (!parsed.terms.length) return [];
    var whole = q.trim().toLowerCase();
    var res = parsed.terms.map(wordStart);
    var matches = function (text) { return res.every(function (re) { return hasWord(re, text); }); };
    var out = [];
    index.acts.forEach(function (a) {
      if (cat && a.categories.indexOf(cat) === -1) return;
      if (type && a.type !== type) return;
      var names = [a.title].concat(a.aliases, a.terms || []);
      var hay = names.join(' | ').toLowerCase();
      if (!matches(hay)) return;
      var exact = names.some(function (n) { return n.toLowerCase() === whole; });
      var hit = (a.terms || []).concat(a.aliases).filter(function (n) {
        return matches(n.toLowerCase());
      })[0];
      out.push({ act: a, score: (exact ? 10 : 0) + (a.title.toLowerCase().indexOf(whole) !== -1 ? 5 : 0), hit: hit });
    });
    return out.sort(function (x, y) { return y.score - x.score; });
  }

  function resultHtml(r, terms, hl) {
    var url = BASE + 'acts/' + r.a.id + '/index.html' + (r.p.anchor ? (hl ? '?hl=' + encodeURIComponent(hl) : '') + '#' + r.p.anchor : '');
    var heading = r.p.no ? r.a.unit + ' ' + r.p.no + (r.p.title ? ' — ' + r.p.title : '') : r.p.title;
    var badge = r.a.placeholder ? ' · <span class="badge bad">Placeholder</span>' : r.a.verified ? '' : ' · <span class="badge warn">Unverified</span>';
    return (
      '<li class="result"><a href="' + url + '">' +
      '<span class="result-title">' + highlight(heading, terms) + '</span>' +
      '<span class="act-meta">' + esc(r.a.title) + ' · ' + esc(r.p.part) + badge + '</span>' +
      '<span class="result-snippet">' + highlight(snippet(r.p.text, terms), terms) + '</span></a></li>'
    );
  }

  var indexPromise;
  function loadIndex() {
    indexPromise = indexPromise || fetch(BASE + 'search-index.json').then(function (r) { return r.json(); });
    return indexPromise;
  }

  // Amendment notes are a separate file, fetched the first time a reader searches them.
  var notesPromise;
  function loadNotes() {
    notesPromise = notesPromise || fetch(BASE + 'search-notes.json').then(function (r) { return r.json(); });
    return notesPromise;
  }

  function searchNotes(index, notes, q, cat, type) {
    var parsed = parseQuery(q);
    if (!parsed.terms.length) return [];
    var res = parsed.terms.map(wordStart);
    var acts = {};
    index.acts.forEach(function (a) { acts[a.id] = a; });
    var out = [];
    notes.forEach(function (n) {
      var a = acts[n.a];
      if (!a || (cat && a.categories.indexOf(cat) === -1) || (type && a.type !== type)) return;
      var text = n.t.toLowerCase();
      var actHay = (a.title + ' ' + a.aliases.join(' ')).toLowerCase();
      var score = 0;
      var ok = res.every(function (re) {
        var inText = hasWord(re, text);
        if (inText) score += 2;
        return inText || hasWord(re, actHay);
      });
      if (ok && score) out.push({ n: n, a: a, score: score });
    });
    out.sort(function (x, y) { return y.score - x.score; });
    return out;
  }

  function noteResultHtml(r, terms, hl) {
    var n = r.n;
    var url = BASE + 'acts/' + r.a.id + '/index.html?hl=' + encodeURIComponent(hl) + '#' + n.id;
    var where = n.no ? r.a.unit + ' ' + n.no + (n.h ? ' — ' + n.h : '') : n.h;
    return (
      '<li class="result note-result"><a href="' + url + '">' +
      '<span class="result-title">' + esc(where) + ' · <span class="badge">Note ' + esc(n.n) + '</span></span>' +
      '<span class="act-meta">' + esc(r.a.title) + '</span>' +
      '<span class="result-snippet">' + highlight(snippet(n.t, terms), terms) + '</span></a></li>'
    );
  }

  // ---------- search by meaning: runs in a worker on the reader's device ----------
  var aiWorker;
  var aiSeq = 0;
  var aiPending = {};
  var aiOnProgress = function () {};
  function startAi() {
    if (aiWorker) return aiWorker;
    aiWorker = new Worker(BASE + 'assets/ai-worker.js', { type: 'module' });
    aiWorker.onmessage = function (ev) {
      var m = ev.data;
      if (m.type === 'progress') return aiOnProgress(m);
      var cb = aiPending[m.id];
      delete aiPending[m.id];
      if (cb) cb(m);
    };
    aiWorker.onerror = function () {
      var waiting = aiPending;
      aiPending = {};
      aiWorker = null;
      Object.keys(waiting).forEach(function (id) { waiting[id]({ type: 'error', message: 'worker' }); });
    };
    return aiWorker;
  }
  function aiSearch(q, cb) {
    var id = ++aiSeq;
    aiPending[id] = cb;
    startAi().postMessage({ type: 'search', id: id, q: q, base: new URL(BASE || './', location.href).href });
  }

  function meaningHtml(hits, index, cat, type) {
    var acts = {};
    index.acts.forEach(function (a) { acts[a.id] = a; });
    var rows = hits.map(function (h) {
      var p = index.provisions[h.prov];
      return { h: h, p: p, a: acts[p.act] };
    }).filter(function (r) {
      return !(cat && r.a.categories.indexOf(cat) === -1) && !(type && r.a.type !== type);
    }).slice(0, 15);
    var head = '<h2 class="result-head">Closest in meaning <span class="count">' + rows.length + '</span></h2>';
    if (!rows.length) return head + '<p class="empty">Nothing in the library is close to that in meaning. Try rewording it.</p>';
    return head + '<p class="muted small">Picked by AI and ranked by closeness, not by exact words. The text shown is the law\u2019s own; read the whole section and check nothing relevant was missed.</p><ol class="result-list">' +
      rows.map(function (r) {
        var url = BASE + 'acts/' + r.a.id + '/index.html' + (r.p.anchor ? '#' + r.p.anchor : '');
        var heading = r.p.no ? r.a.unit + ' ' + r.p.no + (r.p.title ? ' \u2014 ' + r.p.title : '') : r.p.title;
        var badge = r.a.placeholder ? ' \u00b7 <span class="badge bad">Placeholder</span>' : r.a.verified ? '' : ' \u00b7 <span class="badge warn">Unverified</span>';
        var text = r.p.text.slice(r.h.start, r.h.start + r.h.len).trim();
        return '<li class="result"><a href="' + url + '"><span class="result-title">' + esc(heading) + '</span>' +
          '<span class="act-meta">' + esc(r.a.title) + ' \u00b7 ' + esc(r.p.part) + badge + '</span>' +
          '<span class="result-snippet">' + esc(text.length > 300 ? text.slice(0, 300) + '\u2026' : text) + '</span></a></li>';
      }).join('') + '</ol>';
  }

  if (PAGE === 'search') {
    var form = document.getElementById('search-form');
    var input = document.getElementById('q');
    var fCat = document.getElementById('f-cat');
    var fType = document.getElementById('f-type');
    var inText = document.getElementById('in-text');
    var inNotes = document.getElementById('in-notes');
    var inMeaning = document.getElementById('in-meaning');
    var results = document.getElementById('results');
    var help = document.getElementById('search-help');
    var params = new URLSearchParams(location.search);
    input.value = params.get('q') || '';
    fCat.value = params.get('cat') || '';
    fType.value = params.get('type') || '';
    inText.checked = params.get('text') !== '0';
    inNotes.checked = params.get('notes') === '1';
    inMeaning.checked = params.has('ai') ? params.get('ai') === '1' : store('ldb-ai-search') === true;
    var meaningBox = document.createElement('div');
    meaningBox.id = 'meaning-results';
    var meaningTimer;
    var meaningFor;
    aiOnProgress = function (m) {
      var bar = document.getElementById('meaning-status');
      if (bar) bar.textContent = 'Downloading the AI model, once only: ' + Math.round(m.loaded / 1e6) + ' of ' + Math.round(m.total / 1e6) + ' MB\u2026';
    };
    // Waits for a pause in typing: working out the meaning takes longer than matching words.
    var renderMeaning = function (index, q) {
      clearTimeout(meaningTimer);
      var mine = meaningFor = {};
      meaningBox.innerHTML = '<h2 class="result-head">Closest in meaning</h2><p class="muted small" id="meaning-status">Working\u2026</p>';
      meaningTimer = setTimeout(function () {
        aiSearch(q, function (m) {
          if (mine !== meaningFor) return;
          meaningBox.innerHTML = m.type === 'results'
            ? meaningHtml(m.hits, index, fCat.value, fType.value)
            : '<h2 class="result-head">Closest in meaning</h2><p class="empty">Search by meaning could not start: it needs an internet connection the first time, and a recent browser. Ordinary search still works.</p>';
        });
      }, 500);
    };

    var render = function () {
      var q = input.value.trim();
      var url = new URL(location.href);
      ['q', 'cat', 'type', 'text', 'notes', 'ai'].forEach(function (k) { url.searchParams.delete(k); });
      if (q) url.searchParams.set('q', q);
      if (fCat.value) url.searchParams.set('cat', fCat.value);
      if (fType.value) url.searchParams.set('type', fType.value);
      if (!inText.checked) url.searchParams.set('text', '0');
      if (inNotes.checked) url.searchParams.set('notes', '1');
      if (inMeaning.checked) url.searchParams.set('ai', '1');
      history.replaceState(null, '', url);
      if (help) help.hidden = !!q;
      if (!q) {
        results.innerHTML = '';
        return;
      }
      if (!inText.checked && !inNotes.checked && !inMeaning.checked) {
        results.innerHTML = '<p class="empty">Tick at least one of “Provision text”, “Amendment notes” or “Search by meaning”.</p>';
        return;
      }
      Promise.all([loadIndex(), inNotes.checked ? loadNotes() : null]).then(function (loaded) {
        var index = loaded[0];
        var html = '';
        var j = jump(index, q);
        if (j) {
          html +=
            '<div class="jump"><span class="muted small">Go directly to</span> <a href="' + BASE + 'acts/' + j.act.id + '/index.html#' + j.prov.anchor + '">' +
            esc(j.act.unit + ' ' + j.prov.no + ' — ' + j.prov.title) + ', ' + esc(j.act.title) + '</a></div>';
        }
        var terms = parseQuery(q).terms;
        var found = findInstruments(index, q, fCat.value, fType.value);
        if (found.length) {
          html += '<h2 class="result-head">Laws and rules <span class="count">' + found.length + '</span></h2><ul class="instrument-hits">' +
            found.slice(0, 8).map(function (r) {
              return '<li><a href="' + BASE + 'acts/' + r.act.id + '/index.html">' + esc(r.act.title) + '</a>' +
                (r.hit ? ' <span class="muted small">found by “' + esc(r.hit) + '”</span>' : '') + '</li>';
            }).join('') + '</ul>';
        }
        if (inText.checked) {
          var hits = runSearch(index, q, fCat.value, fType.value);
          html += '<h2 class="result-head">Provisions <span class="count">' + hits.length + '</span></h2>';
          html += hits.length
            ? '<ol class="result-list">' + hits.slice(0, 100).map(function (r) { return resultHtml(r, terms, q); }).join('') + '</ol>'
            : '<p class="empty">No provisions match all of those words. Try fewer words or remove a filter.</p>';
        }
        if (inNotes.checked) {
          var noteHits = searchNotes(index, loaded[1], q, fCat.value, fType.value);
          html += '<h2 class="result-head">Amendment notes <span class="count">' + noteHits.length + '</span></h2>';
          html += noteHits.length
            ? '<ol class="result-list">' + noteHits.slice(0, 100).map(function (r) { return noteResultHtml(r, terms, q); }).join('') + '</ol>'
            : '<p class="empty">No amendment notes match all of those words.</p>';
        }
        results.innerHTML = html;
        if (inMeaning.checked) {
          // After "Laws and rules", before the word matches.
          var heads = results.querySelectorAll('h2.result-head');
          results.insertBefore(meaningBox, heads[found.length ? 1 : 0] || null);
          renderMeaning(index, q);
        }
      }, function () {
        results.innerHTML = '<p class="empty">The search index could not be loaded.</p>';
      });
    };

    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      render();
    });
    var debounce;
    input.addEventListener('input', function () {
      clearTimeout(debounce);
      debounce = setTimeout(render, 180);
    });
    fCat.addEventListener('change', render);
    fType.addEventListener('change', render);
    inText.addEventListener('change', render);
    inNotes.addEventListener('change', render);
    inMeaning.addEventListener('change', function () {
      store('ldb-ai-search', inMeaning.checked);
      render();
    });
    render();
  }

  // Home page: a jump query goes straight to the provision.
  if (PAGE === 'home') {
    var homeForm = document.querySelector('.searchbar');
    if (homeForm) {
      homeForm.addEventListener('submit', function (ev) {
        var q = homeForm.querySelector('input').value.trim();
        if (!q) return;
        ev.preventDefault();
        loadIndex()
          .then(function (index) {
            var j = jump(index, q);
            location.href = j
              ? BASE + 'acts/' + j.act.id + '/index.html#' + j.prov.anchor
              : BASE + 'search.html?q=' + encodeURIComponent(q);
          })
          .catch(function () {
            location.href = BASE + 'search.html?q=' + encodeURIComponent(q);
          });
      });
    }
    var preview = document.getElementById('shelf-preview');
    if (preview) renderShelf(preview, 5);
  }

  if (PAGE === 'shelf') renderShelf(document.getElementById('shelf'));

  // Keyboard: "/" focuses search.
  document.addEventListener('keydown', function (ev) {
    if (ev.key !== '/' || /input|textarea|select/i.test(document.activeElement.tagName)) return;
    var box = document.querySelector('.searchbar input');
    if (box) {
      ev.preventDefault();
      box.focus();
    } else {
      location.href = BASE + 'search.html';
    }
  });

  // ---------- register of related instruments: show only the sections still to identify ----------
  var onlyOpen = document.getElementById('only-open');
  if (onlyOpen) {
    onlyOpen.addEventListener('change', function () {
      document.querySelectorAll('.related-sections tr[data-open="0"]').forEach(function (tr) {
        tr.hidden = onlyOpen.checked;
      });
    });
    if (location.hash === '#to-identify') {
      onlyOpen.checked = true;
      onlyOpen.dispatchEvent(new Event('change'));
    }
  }

  // ---------- offline ----------
  if ('serviceWorker' in navigator && location.protocol !== 'file:') {
    window.addEventListener('load', function () {
      navigator.serviceWorker.register(BASE + 'sw.js').catch(function () {});
    });
  }
})();
