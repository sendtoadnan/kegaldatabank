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
    var re = new RegExp('(' + t.map(reEscape).sort(function (a, b) { return b.length - a.length; }).join('|') + ')', 'ig');
    return raw
      .split(re)
      .map(function (piece, i) {
        return i % 2 ? '<mark>' + esc(piece) + '</mark>' : esc(piece);
      })
      .join('');
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
      var ok = parsed.terms.every(function (t) {
        var inTitle = title.indexOf(t) !== -1;
        var inText = text.indexOf(t) !== -1;
        var inAct = actHay.indexOf(t) !== -1;
        if (inTitle) score += 10;
        if (inText) score += 2 + Math.min(text.split(t).length - 2, 5);
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
      at = lower.indexOf(t);
      return at !== -1;
    });
    var start = Math.max(0, at - 90);
    var s = text.slice(start, start + 260).replace(/\n/g, ' ');
    return (start > 0 ? '… ' : '') + s + (start + 260 < text.length ? ' …' : '');
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
    var acts = {};
    index.acts.forEach(function (a) { acts[a.id] = a; });
    var out = [];
    notes.forEach(function (n) {
      var a = acts[n.a];
      if (!a || (cat && a.categories.indexOf(cat) === -1) || (type && a.type !== type)) return;
      var text = n.t.toLowerCase();
      var actHay = (a.title + ' ' + a.aliases.join(' ')).toLowerCase();
      var score = 0;
      var ok = parsed.terms.every(function (t) {
        var inText = text.indexOf(t) !== -1;
        if (inText) score += 2;
        return inText || actHay.indexOf(t) !== -1;
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

  if (PAGE === 'search') {
    var form = document.getElementById('search-form');
    var input = document.getElementById('q');
    var fCat = document.getElementById('f-cat');
    var fType = document.getElementById('f-type');
    var inText = document.getElementById('in-text');
    var inNotes = document.getElementById('in-notes');
    var results = document.getElementById('results');
    var params = new URLSearchParams(location.search);
    input.value = params.get('q') || '';
    fCat.value = params.get('cat') || '';
    fType.value = params.get('type') || '';
    inText.checked = params.get('text') !== '0';
    inNotes.checked = params.get('notes') === '1';

    var render = function () {
      var q = input.value.trim();
      var url = new URL(location.href);
      ['q', 'cat', 'type', 'text', 'notes'].forEach(function (k) { url.searchParams.delete(k); });
      if (q) url.searchParams.set('q', q);
      if (fCat.value) url.searchParams.set('cat', fCat.value);
      if (fType.value) url.searchParams.set('type', fType.value);
      if (!inText.checked) url.searchParams.set('text', '0');
      if (inNotes.checked) url.searchParams.set('notes', '1');
      history.replaceState(null, '', url);
      if (!q) {
        results.innerHTML = '';
        return;
      }
      if (!inText.checked && !inNotes.checked) {
        results.innerHTML = '<p class="empty">Tick at least one of “Provision text” or “Amendment notes”.</p>';
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
