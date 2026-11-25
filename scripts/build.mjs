// Builds the static website into dist/ from the JSON library in data/.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { passages, AI_MODEL, AI_DIMS } from './ai_chunks.mjs';
import {
  ROOT,
  loadLibrary,
  validateLibrary,
  citation,
  escapeHtml as e,
  displayNo,
  fnLabel,
  FN_RE,
  stripMarkers,
  parseParagraph,
  plainText,
  provisionAnchor,
  typeLabel,
} from './lib.mjs';
import { loadExtras, validateExtras, citedSections, delegation, handCheck, EVIDENCE_DIR } from './related.mjs';

const slug = (s) => String(s).toLowerCase().replace(/[^a-z0-9]+/g, '-');

export function build({ outDir = path.join(ROOT, 'dist'), dataDir } = {}) {
  const library = loadLibrary(dataDir);
  const errors = validateLibrary(library);
  const extras = loadExtras(dataDir);
  errors.push(...validateExtras(library, extras));
  if (errors.length) throw new Error(`Library is invalid:\n  - ${errors.join('\n  - ')}`);

  const { catalog, acts } = library;
  const site = catalog.site;
  // Words of schedules, annexures and forms taken from the official PDFs (scripts/extract_schedule_text.py):
  // they are shown only as PDF links, so this is what lets search and the filter box find them.
  const scheduleDir = path.join(dataDir || path.join(ROOT, 'data'), 'schedule-text');
  const scheduleText = new Map();
  if (fs.existsSync(scheduleDir)) {
    for (const f of fs.readdirSync(scheduleDir).filter((n) => n.endsWith('.json'))) {
      const j = JSON.parse(fs.readFileSync(path.join(scheduleDir, f), 'utf8'));
      scheduleText.set(j.id, j);
    }
  }
  const byId = new Map(acts.map((a) => [a.id, a]));
  const children = (id) => acts.filter((a) => a.parent === id);
  const registerFor = (id) => extras.registers.find((r) => r.act === id);
  // Short names (manifest aliases) and everyday search words (data/search-terms.json), without repeats.
  const searchTermsFor = (a) => {
    const seen = new Set();
    return [...(a.aliases || []), ...(extras.searchTerms[a.id] || [])].filter((t) => !seen.has(t.toLowerCase()) && seen.add(t.toLowerCase()));
  };
  const dateLabel = (d) => new Date(`${d}T00:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });
  const evidenceLink = (base, file, text = 'Screenshot') => `<a href="${base}evidence/${e(file)}" target="_blank" rel="noopener">${text}</a>`;
  const written = [];

  fs.rmSync(outDir, { recursive: true, force: true });
  const write = (rel, content) => {
    const file = path.join(outDir, rel);
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, content);
    written.push(rel);
  };

  // ---------- shared chrome ----------
  const layout = ({ title, description, base, body, page }) => `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${e(title)}</title>
<meta name="description" content="${e(description || site.tagline)}">
<meta name="theme-color" content="#1f3a5f">
<link rel="manifest" href="${base}manifest.webmanifest">
<link rel="icon" href="${base}assets/icon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">
<link rel="stylesheet" href="${base}assets/styles.css">
<script>try{var t=localStorage.getItem('ldb-theme');if(t)document.documentElement.dataset.theme=t;}catch(_){}</script>
</head>
<body data-page="${page}" data-base="${base}">
<a class="skip" href="#main">Skip to content</a>
<header class="topbar">
  <a class="brand" href="${base}index.html">
    <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24"><path fill="currentColor" d="M12 2 3 6v2h18V6l-9-4Zm-7 8v8h2v-8H5Zm4 0v8h2v-8H9Zm4 0v8h2v-8h-2Zm4 0v8h2v-8h-2ZM3 20v2h18v-2H3Z"/></svg>
    <span>${e(site.name)}</span>
  </a>
  <nav class="nav" aria-label="Main">
    <a href="${base}index.html"${page === 'home' ? ' aria-current="page"' : ''}>Library</a>
    <a href="${base}search.html"${page === 'search' ? ' aria-current="page"' : ''}>Search</a>
    <a href="${base}contents.html"${page === 'contents' ? ' aria-current="page"' : ''}>Index</a>
    <a href="${base}shelf.html"${page === 'shelf' ? ' aria-current="page"' : ''}>My shelf</a>
    <a href="${base}laws.html"${page === 'laws' ? ' aria-current="page"' : ''}>SECP laws</a>
    <a href="${base}sources.html"${page === 'sources' ? ' aria-current="page"' : ''}>Sources</a>
    <a href="${base}about.html"${page === 'about' ? ' aria-current="page"' : ''}>About</a>
  </nav>
  <button class="icon-btn" id="theme-toggle" type="button" aria-label="Toggle dark mode" title="Toggle dark mode">
    <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24"><path fill="currentColor" d="M12 3a9 9 0 1 0 9 9 7 7 0 0 1-9-9Z"/></svg>
  </button>
</header>
<main id="main">
${body}
</main>
<footer class="footer">
  <p><strong>Disclaimer.</strong> Reference text is provided for convenience. Always confirm against the official Gazette or the issuing authority before relying on it in advice, pleadings or filings. Each instrument shows its verification status.</p>
  <p>${e(site.name)} · ${e(site.jurisdiction)} · <a href="${base}search-guide.html">Search guide</a></p>
</footer>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<script src="${base}assets/app.js" defer></script>
<div class="read-progress" aria-hidden="true"></div>
<a class="fab-top" href="#" aria-label="Back to top" onclick="window.scrollTo({top:0,behavior:'smooth'});return false">↑</a>
</body>
</html>
`;

  const verificationBadge = (act) =>
    act.placeholder
      ? `<span class="badge bad" title="${e(act.verification.note)}">Placeholder</span>`
      : act.verification.status === 'verified'
        ? `<span class="badge ok" title="Checked against ${e(act.verification.against)} by ${e(act.verification.verifiedBy)} on ${e(act.verification.verifiedOn)}">Verified</span>`
        : `<span class="badge warn" title="${e(act.verification.note || 'Not yet checked against an official source')}">Unverified</span>`;

  // Amendment notes that belong to a heading or to the title and enacting text rather than to a provision.
  const noteList = (notes, label, idPrefix) =>
    notes && notes.length
      ? `<details class="prov-fns" id="${idPrefix}"><summary>${label} (${notes.length})</summary><ol>${notes
          .map((f) => `<li id="${idPrefix}-fn-${slug(f.n)}"><span class="fn-no">${e(fnLabel(f.n))}</span> ${e(f.text)}</li>`)
          .join('')}</ol></details>`
      : '';

  const hasNotes = (act) =>
    (act.frontNotes || []).length > 0 || act.parts.some((p) => (p.fn || []).length || p.sections.some((s) => (s.fn || []).length));

  const provisionCount = (act) => act.parts.reduce((n, p) => n + p.sections.length, 0);
  // Large editions are linked at the regulator's own URL instead of being republished (sourcePdfUrl).
  const pdfHref = (act, base) => act.sourcePdfUrl || `${base}sources/${act.id}.pdf`;

  const actRow = (act, base) => {
    const count = provisionCount(act);
    const size = act.pdfOnly ? 'Official PDF' : `${count} ${act.unit.toLowerCase()}${count === 1 ? '' : 's'}`;
    const lbl = act.amendedUpToLabel ? act.amendedUpToLabel.replace(/\s*\(.*\)$/, '') : '';
    const upto = /^(\d|(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d)/i.test(lbl) && lbl.length < 30 ? ` · to ${e(lbl)}` : '';
    return `
      <li class="act-row">
        <a href="${base}acts/${act.id}/index.html">
          <span class="act-title">${e(act.title)}</span>
          <span class="act-meta">${act.number ? `${e(act.number)} · ` : ''}${typeLabel(act.type)} · ${size}${upto}</span>
        </a>
        ${verificationBadge(act)}
      </li>`;
  };

  // Escapes provision text and turns {fn:key} markers into links to the amendment notes.
  const renderText = (text, anchor, known) =>
    e(text).replace(FN_RE, (_, key) =>
      known.has(key)
        ? `<sup class="fnref"><a href="#${anchor}-fn-${slug(key)}" aria-label="Amendment note ${e(fnLabel(key))}">${e(fnLabel(key))}</a></sup>`
        : `<sup class="fnref missing" title="Amendment note not captured. See the official PDF page.">${e(fnLabel(key))}</sup>`
    );

  // ---------- home ----------
  {
    const base = '';
    const verifiedCount = acts.filter((a) => a.verification.status === 'verified').length;
    const catData = catalog.categories.map((c) => {
      const list = acts.filter((a) => a.categories.includes(c.id));
      const principal = list.filter((a) => !a.parent || !list.includes(byId.get(a.parent)));
      return { c, list, principal };
    });
    // Practice-area cards: one tile per area with a count and its first few principal instruments.
    const cards = catData
      .map(
        ({ c, list, principal }) => `
      <a class="area-card" href="#cat-${c.id}">
        <span class="area-count">${list.length}</span>
        <span class="area-name">${e(c.name)}</span>
        <span class="area-desc">${e(c.description)}</span>
        <span class="area-eg">${principal.slice(0, 3).map((a) => e(a.title.replace(/,?\s*\d{4}$/, ''))).join(' · ')}</span>
      </a>`
      )
      .join('');
    const groupsAll = JSON.parse(fs.readFileSync(path.join(dataDir || path.join(ROOT, 'data'), 'contents-groups.json'), 'utf8')).groups;
    const rowFor = (a, list) => {
      const kids = children(a.id).filter((k) => list.includes(k));
      const head = actRow(a, base);
      if (!kids.length) return head;
      return `${head}
      <li class="act-kids"><details><summary>${kids.length} rule${kids.length === 1 ? '' : 's'} and regulations made under it</summary><ul class="act-list">${kids
        .map((k) => actRow(k, base).replace('class="act-row"', 'class="act-row child"'))
        .join('')}</ul></details></li>`;
    };
    const cats = catData
      .map(({ c, list, principal }) => {
        let inner;
        if (list.length > 25) {
          // A large area is split by our own subject groups (contents-groups.json) so it reads as short lists.
          const used = new Set();
          inner = groupsAll
            .map((g) => {
              const items = g.items.map((id) => byId.get(id)).filter((a) => a && principal.includes(a) && !used.has(a.id));
              items.forEach((a) => used.add(a.id));
              if (!items.length) return '';
              const n = items.reduce((t, a) => t + 1 + children(a.id).filter((k) => list.includes(k)).length, 0);
              return `<h3 class="sub-label">${e(g.name)} <span class="count">${n}</span></h3><ul class="act-list">${items.map((a) => rowFor(a, list)).join('')}</ul>`;
            })
            .join('');
          const rest = principal.filter((a) => !used.has(a.id));
          if (rest.length) inner += `<h3 class="sub-label">Other</h3><ul class="act-list">${rest.map((a) => rowFor(a, list)).join('')}</ul>`;
        } else {
          inner = `<ul class="act-list">${principal.map((a) => rowFor(a, list)).join('')}</ul>`;
        }
        return `
    <section class="category" id="cat-${c.id}">
      <h2>${e(c.name)} <span class="count">${list.length}</span> <a class="to-top" href="#top">Top ↑</a></h2>
      <p class="muted">${e(c.description)}</p>
      ${inner}
    </section>`;
      })
      .join('');

    const total = acts.reduce((n, a) => n + provisionCount(a), 0);
    const body = `
  <section class="hero" id="top">
    <h1>${e(site.name)}</h1>
    <p class="lede">${e(site.tagline)}</p>
    <form class="searchbar" action="search.html" method="get" role="search">
      <label class="sr-only" for="q">Search the library</label>
      <input id="q" name="q" type="search" placeholder="Search, or jump: s 3 STA" autocomplete="off">
      <button type="submit">Search</button>
    </form>
    <p class="hint">Try <a href="search.html?q=withholding%20tax">withholding tax</a>, <a href="search.html?q=GST">GST</a>, <a href="search.html?q=related%20party">related party</a> or <a href="search.html?q=KYC">KYC</a> · <a href="search-guide.html">Search guide</a></p>
    <ul class="stat-tiles">
      <li><strong>${acts.length}</strong><span>laws, rules and regulations</span></li>
      <li><strong>${total.toLocaleString('en')}</strong><span>provisions</span></li>
      <li><strong>${catalog.categories.length}</strong><span>practice areas</span></li>
      <li><a href="about.html#verification"><strong>${verifiedCount}</strong><span>converted from the regulator's own PDF (editor-declared)</span></a></li>
    </ul>
    <p class="stats small"><a href="contents.html">Index by subject</a> · <a href="laws.html">What SECP administers and what the library covers</a> · <a href="sources.html">Editions checked against the regulators' websites</a></p>
  </section>
  <div id="shelf-preview"></div>
  <h2 class="section-label">Browse by practice area</h2>
  <div class="area-grid">${cards}</div>
  <nav class="chips sticky-chips" aria-label="Practice areas">
    ${catalog.categories.map((c) => `<a class="chip" href="#cat-${c.id}">${e(c.name)}</a>`).join('')}
  </nav>
  ${cats}`;
    write('index.html', layout({ title: `${site.name} — ${site.tagline}`, base, body, page: 'home' }));
  }

  // ---------- one page per instrument ----------
  for (const act of acts) {
    const base = '../../';
    const parent = act.parent ? byId.get(act.parent) : null;
    const kids = children(act.id);
    const pdf = act.sourcePdf ? pdfHref(act, base) : null;
    const register = registerFor(act.id);
    const cited = register ? citedSections(act, kids, extras.formMaps) : new Map();
    // Register entries made under another law (e.g. the Securities Act) that do what a section leaves to be specified.
    const otherLaw = (i) => (i.madeUnder ? ` <span class="badge other">Other law</span> <span class="muted small">made under ${e(i.madeUnder)}</span>` : '');
    // Section of the law this Act replaced that deals with the same matter, from data/comparison/.
    const cmp = (extras.comparisons || []).find((x) => x.act === act.id);
    const cmpMap = new Map((cmp?.pairs || []).map((p) => [p.a, p]));
    const cmpOtherAct = cmp?.otherId && acts.find((x) => x.id === cmp.otherId);
    const cmpOther = new Set(cmpOtherAct ? cmpOtherAct.parts.flatMap((p) => p.sections.map((s) => s.no)) : []);
    const ordLine = (no) => (cmp && cmpMap.has(no)
      ? `<p class="prov-ord muted small">${e(cmp.otherTitle)}: ${cmpMap.get(no).o.length ? `section ${cmpMap.get(no).o.map((n) => (cmpOther.has(n) ? `<a href="../${cmp.otherId}/index.html#${provisionAnchor(n)}">${e(n)}</a>` : e(n))).join(', ')}` : (cmp.noneText || 'no corresponding section')}${cmpMap.get(no).src === 'probable' ? ' (probable match by subject)' : ''}${cmpMap.get(no).alt ? ` (the other comparison lists ${cmpMap.get(no).alt.length ? cmpMap.get(no).alt.map(e).join(', ') : 'none'})` : ''} · <a href="${cmp.id}.html#s-${no}">comparison</a></p>` : '');
    // Instruments related to each section: those in the library that cite it, then the register's entries.
    const relatedTo = (no) => {
      const out = [...(cited.get(no)?.values() || [])].map(
        ({ kid, provisions }) => `<li><a href="../${kid.id}/index.html#${provisionAnchor(provisions[0])}">${e(kid.title)}</a> <span class="muted">— ${e(kid.unit.toLowerCase())}${provisions.length > 1 ? 's' : ''} ${provisions.map((n) => `<a href="../${kid.id}/index.html#${provisionAnchor(n)}">${e(displayNo(n))}</a>`).join(', ')}</span></li>`
      );
      for (const i of register?.instruments || []) {
        if (!(i.sections || []).includes(no) || (i.library && cited.get(no)?.has(i.library))) continue;
        const name = i.library ? `<a href="../${i.library}/index.html">${e(i.title)}</a>` : i.url ? `<a href="${e(i.url)}" target="_blank" rel="noopener">${e(i.title)}</a>` : e(i.title);
        const tag = i.status === 'repealed' ? '<span class="badge bad">Repealed</span>' : i.library ? '' : '<span class="badge warn">Not in library yet</span>';
        out.push(`<li>${name} ${tag}${otherLaw(i)}</li>`);
      }
      return out.length ? `<aside class="prov-related"><h4>Rules, regulations and notifications</h4><ul>${out.join('')}</ul></aside>` : '';
    };
    const hand = handCheck(act, extras.checks);

    const schedAnchor = (k) => `sched-${k + 1}`;
    const inlineScheds = (act.schedules || []).map((x, k) => [x, k]).filter(([x]) => x.text);
    const pdfScheds = (act.schedules || []).filter((x) => !x.text);
    const toc = act.parts
      .map(
        (p) => `
        <li><span class="toc-part">${e(p.heading)}</span>
          <ol>${p.sections.map((s) => `<li><a href="#${provisionAnchor(s.no)}"><span class="toc-no">${e(displayNo(s.no))}</span> ${e(s.title || '—')}</a></li>`).join('')}</ol>
        </li>`
      )
      .join('') + (inlineScheds.length ? `<li><span class="toc-part"><a href="#schedules">Schedules, annexures and forms</a></span><ol>${inlineScheds.map(([x, k]) => `<li><a href="#${schedAnchor(k)}">${e(x.title)}</a></li>`).join('')}</ol></li>` : '');

    const parts = act.parts
      .map(
        (p, pi) => `
      <section class="part">
        <h2 class="part-heading">${e(p.heading)}</h2>
        ${noteList(p.fn, 'Amendment notes on this heading', `part-${pi + 1}`)}
        ${p.sections
          .map((s) => {
            const anchor = provisionAnchor(s.no);
            const known = new Set((s.fn || []).map((f) => f.n));
            const paras = s.text
              .map((raw) => {
                const { level, text } = parseParagraph(raw);
                return `<p class="l${level}">${renderText(text, anchor, known)}</p>`;
              })
              .join('');
            const notes = (s.notes || []).map((n) => `<li>${e(n)}</li>`).join('');
            const fns = (s.fn || [])
              .map((f) => `<li id="${anchor}-fn-${slug(f.n)}"><span class="fn-no">${e(fnLabel(f.n))}</span> ${e(f.text)}</li>`)
              .join('');
            const title = stripMarkers(s.title);
            return `
        <article class="provision" id="${anchor}" data-no="${e(displayNo(s.no))}" data-title="${e(title)}" data-cite="${e(citation(act, s.no, s))}">
          <header class="prov-head">
            <h3><a class="prov-link" href="#${anchor}"><span class="prov-no">${e(displayNo(s.no))}.</span> ${title ? `${e(title)}.` : ''}</a></h3>
            <div class="prov-tools" role="group" aria-label="Tools for ${e(act.unit)} ${e(displayNo(s.no))}">
              <button type="button" data-action="cite" title="Copy citation">Cite</button>
              <button type="button" data-action="quote" title="Copy text with citation">Quote</button>
              <button type="button" data-action="link" title="Copy link to this provision">Link</button>
              <button type="button" data-action="pin" title="Save to My shelf" aria-pressed="false">Save</button>
              ${pdf && s.page ? `<a class="tool-link" href="${pdf}#page=${s.page}" target="_blank" rel="noopener" title="Open the official PDF at this page">PDF p.${s.page}</a>` : ''}
            </div>
          </header>
          <div class="prov-body">${paras}</div>
          ${fns ? `<details class="prov-fns"><summary>Amendment notes (${(s.fn || []).length})</summary><ol>${fns}</ol></details>` : ''}
          ${notes ? `<aside class="prov-notes"><h4>Notes</h4><ul>${notes}</ul></aside>` : ''}
          ${ordLine(s.no)}
          ${register ? relatedTo(s.no) : ''}
        </article>`;
          })
          .join('')}
      </section>`
      )
      .join('');

    const meta = [
      act.number ? ['Number', e(act.number)] : null,
      ['Type', typeLabel(act.type)],
      ['Status', e(act.status.replace(/-/g, ' '))],
      act.enacted ? ['Enacted / notified', e(act.enacted)] : null,
      ['Amended up to', act.amendedUpToLabel ? e(act.amendedUpToLabel) : 'Not stated'],
      parent ? ['Made under', `<a href="../${parent.id}/index.html">${e(parent.title)}</a>`] : null,
      searchTermsFor(act).length ? ['Also found by', `${searchTermsFor(act).map(e).join(' · ')} <a class="small" href="../../search-guide.html">Search guide</a>`] : null,
      ['Source', `<a href="${e(act.source.url)}" rel="noopener" target="_blank">${e(act.source.name)}</a>`],
      pdf ? ['Official PDF', `<a href="${pdf}" target="_blank" rel="noopener">Open the source PDF</a>`] : null,
      hand
        ? ['Checked on regulator website', `${dateLabel(hand.date)}: ${hand.status === 'current' ? 'no newer edition listed' : '<strong>a newer edition is listed</strong>'} (“${e(hand.entry.listed)}”). ${evidenceLink(base, hand.screenshot, 'View screenshot')}`]
        : null,
    ]
      .filter(Boolean)
      .map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`)
      .join('');

    const verification = act.placeholder
      ? `<div class="notice bad"><strong>Placeholder, not official text.</strong> ${e(act.verification.note)}</div>`
      : act.verification.status === 'verified'
        ? `<div class="notice ok"><strong>Verified</strong> against ${e(act.verification.against)} by ${e(act.verification.verifiedBy)} on ${e(act.verification.verifiedOn)}.</div>`
        : `<div class="notice warn"><strong>Unverified text.</strong> ${e(act.verification.note || 'This text has not yet been checked against an official source.')}</div>`;
    const caution = act.caution ? `<div class="notice warn"><strong>Note on this edition.</strong> ${e(act.caution)}</div>` : '';
    const sourceNotes = act.sourceNotes ? `<p class="muted small source-notes">${e(act.sourceNotes)}</p>` : '';

    const schedules = act.schedules?.length
      ? `<section class="schedules" id="schedules"><h2>Schedules, annexures and forms</h2>${pdfScheds.length ? `<p class="muted small">Schedules are mostly tables, so they are shown as published in the official PDF.</p><ul class="act-list">${act.schedules
          .map((x, k) => (x.text ? '' : `<li class="act-row" data-sched="${k}"><a href="${x.pdf ? `${base}sources/${x.pdf}` : pdf}#page=${x.page}" target="_blank" rel="noopener"><span class="act-title">${e(x.title)}</span><span class="act-meta">Official PDF, page ${x.page}</span></a></li>`))
          .join('')}</ul>` : ''}${inlineScheds.length && act.schedulesNote ? `<p class="muted small">${e(act.schedulesNote)}</p>` : ''}${inlineScheds
          .map(([x, k]) => {
            const paras = x.text.map((raw) => { const { level, text } = parseParagraph(raw); return `<p class="l${level}">${e(text)}</p>`; }).join('');
            return `<article class="provision schedule" id="${schedAnchor(k)}" data-no="" data-title="${e(x.title)}" data-cite="${e(x.title)}, ${e(act.title)}"><header class="prov-head"><h3><a class="prov-link" href="#${schedAnchor(k)}">${e(x.title)}</a></h3><div class="prov-tools" role="group" aria-label="Tools for ${e(x.title)}"><button type="button" data-action="link" title="Copy link to this schedule">Link</button></div></header><div class="prov-body">${paras}</div></article>`;
          })
          .join('')}</section>`
      : '';

    // Instruments recorded in the register whose text is not in the library yet.
    const outside = (register?.instruments || []).filter((i) => !i.library);
    const outsideList = outside.length
      ? `<details class="register-more"><summary>${outside.length} more instruments recorded under this ${typeLabel(act.type)}, not yet in the library</summary><ul>${outside
          .map((i) => {
            const name = i.url ? `<a href="${e(i.url)}" target="_blank" rel="noopener">${e(i.title)}</a>` : e(i.title);
            const tag = i.status === 'repealed' ? ' <span class="badge bad">Repealed</span>' : '';
            const other = i.madeUnder ? ` <span class="badge other">Other law</span>` : '';
            const secs = (i.sections || []).length ? ` <span class="muted small">s. ${i.sections.slice(0, 6).map(displayNo).join(', ')}${i.sections.length > 6 ? ', …' : ''}</span>` : '';
            return `<li>${name}${tag}${other}${secs}</li>`;
          })
          .join('')}</ul><p class="small"><a href="related.html">Details, sources and what is still to confirm</a></p></details>`
      : '';
    const subsidiary = kids.length || outside.length
      ? `<section class="subsidiary"><h2>Made under this ${typeLabel(act.type)}</h2>${register ? `<p><a class="btn" href="related.html">All rules, regulations and notifications, section by section</a> <a href="related.html#to-identify">Sections still to identify</a></p>` : ''}${cmp ? `<p><a href="${cmp.id}.html">Compared with the ${e(cmp.otherTitle)}, section by section</a></p>` : ''}<ul class="act-list">${kids.map((k) => actRow(k, base)).join('')}</ul>${outsideList}</section>`
      : '';

    const pdfOnly = act.pdfOnly
      ? `${act.summary ? `<p class="lede">${e(act.summary)}</p>` : ''}
      <div class="pdf-frame"><iframe src="${pdf}" title="${e(act.title)} (official PDF)" loading="lazy"></iframe></div>
      <p><a class="btn" href="${pdf}" target="_blank" rel="noopener">Open the PDF in a new tab</a></p>`
      : '';

    const body = `
  <div class="act-layout${act.pdfOnly || !act.parts.length ? ' no-toc' : ''}" data-act="${act.id}" data-act-title="${e(act.title)}" data-unit="${e(act.unit)}">
    ${act.parts.length ? `<aside class="toc" aria-label="Contents">
      <details open>
        <summary>Contents</summary>
        <label class="sr-only" for="toc-filter">Search the text of this instrument</label>
        <input id="toc-filter" class="toc-filter" type="search" placeholder="Search in the ${e(act.unit.toLowerCase())}s’ text…">
        <p id="toc-status" class="toc-status muted small" aria-live="polite"></p>
        <ol class="toc-list">${toc}</ol>
      </details>
    </aside>` : ''}
    <article class="act">
      <p class="crumbs"><a href="${base}index.html">Library</a>${parent ? ` / <a href="../${parent.id}/index.html">${e(parent.title)}</a>` : ''}</p>
      <h1>${e(act.title)} ${verificationBadge(act)}</h1>
      ${act.preamble ? `<p class="preamble">${e(stripMarkers(act.preamble))}</p>` : ''}
      ${noteList(act.frontNotes, 'Amendment notes on the title and enacting text', 'front')}
      <details class="meta-wrap" open><summary>Details of this instrument</summary><dl class="meta">${meta}</dl></details>
      ${verification}
      ${caution}
      ${sourceNotes}
      ${pdfOnly}
      ${act.parts.length ? `<div class="act-actions"><button type="button" class="btn" onclick="window.print()">Print</button>${hasNotes(act) ? `
        <label class="toggle"><input type="checkbox" id="show-notes"> Show amendment notes</label>` : ''}</div>` : ''}
      ${parts}
      ${schedules}
      ${subsidiary}
    </article>
  </div>`;

    write(
      `acts/${act.id}/index.html`,
      layout({ title: `${act.title} — ${site.name}`, description: `${act.title} (${act.number}): full text with contents, citations and related rules.`, base, body, page: 'act' })
    );

    // ---------- register of rules, regulations and notifications made under the Act ----------
    if (register) {
      const pageLink = (key) => (register.secpPages?.[key] ? `<a href="${e(register.secpPages[key])}" target="_blank" rel="noopener">SECP ${e(key)}</a>` : '');
      const instrumentRows = register.instruments
        .slice()
        .sort((x, y) => (x.status === 'repealed') - (y.status === 'repealed') || !!y.library - !!x.library)
        .map((i) => {
          const name = i.library ? `<a href="../${i.library}/index.html">${e(i.title)}</a>` : i.url ? `<a href="${e(i.url)}" target="_blank" rel="noopener">${e(i.title)}</a>` : e(i.title);
          const state = i.status === 'repealed'
            ? `<span class="badge bad">Repealed</span>${i.replacedBy ? ` <span class="muted small">replaced by <a href="../${i.replacedBy}/index.html">${e(byId.get(i.replacedBy).title)}</a></span>` : ''}`
            : i.library ? '<span class="badge ok">In library</span>' : '<span class="badge warn">Not in library yet</span>'
          const other = otherLaw(i);
          const secs = (i.sections || []).map((n) => `<a href="index.html#${provisionAnchor(n)}">${e(displayNo(n))}</a>`).join(', ') || '<span class="muted">to confirm</span>';
          const latest = [i.latest ? e(i.latest) : '', i.seen ? `<span class="muted small">seen ${dateLabel(i.seen.date)} · ${evidenceLink(base, i.seen.screenshot)}</span>` : '', pageLink(i.secpPage)].filter(Boolean).join('<br>');
          const amends = i.amendments?.length ? `<br><span class="muted small">Amended by ${i.amendments.map(e).join(', ')}</span>` : '';
          const found = i.found?.how === 'search-index' ? `<br><span class="muted small">Found ${dateLabel(i.found.date)} through a search engine's index of SECP's website; confirm against the instrument.</span>` : '';
          const confirm = i.confirm?.length ? `<br><span class="muted small">To confirm: ${i.confirm.map(e).join('; ')}</span>` : '';
          const fm = i.formsMap && extras.formMaps.find((m) => m.id === i.formsMap);
          const formsLink = fm ? `<br><a class="small" href="forms-${fm.id}.html">How its ${fm.forms.length} forms match this Act's sections</a>` : '';
          return `<tr><td>${name}${i.number ? `<br><span class="muted small">${e(i.number)}</span>` : ''}</td><td>${secs}</td><td>${state}${other}</td><td>${latest || '<span class="muted">—</span>'}</td><td class="small">${e(i.basis || '')}${amends}${found}${confirm}${formsLink}</td></tr>`;
        })
        .join('');
      let covered = 0;
      let open = 0;
      let byOrder = 0;
      const sectionRows = act.parts
        .flatMap((p) => p.sections)
        .map((s) => {
          const words = delegation(s);
          const fromLibrary = [...(cited.get(s.no)?.values() || [])].map(({ kid, provisions }) => `<a href="../${kid.id}/index.html#${provisionAnchor(provisions[0])}">${e(kid.title)}</a> <span class="muted small">(${provisions.map(displayNo).join(', ')})</span>`);
          const fromRegister = register.instruments
            .filter((i) => (i.sections || []).includes(s.no) && !(i.library && cited.get(s.no)?.has(i.library)))
            .map((i) => (i.library ? `<a href="../${i.library}/index.html">${e(i.title)}</a>` : `${e(i.title)}${i.status === 'repealed' ? ' <span class="badge bad">Repealed</span>' : ' <span class="badge warn">Not in library yet</span>'}${otherLaw(i)}`));
          const found = [...fromLibrary, ...fromRegister];
          if (!words && !found.length) return '';
          // Sections whose details are fixed in each order or notice need no rule or regulation.
          const inOrder = !found.length && register.setInOrder?.[s.no];
          if (found.length) covered++;
          else if (inOrder) byOrder++;
          else open++;
          return `<tr data-open="${found.length || inOrder ? 0 : 1}"><td><a href="index.html#${provisionAnchor(s.no)}">${e(displayNo(s.no))}</a></td><td>${e(stripMarkers(s.title || ''))}</td><td class="small">${words ? `“…${e(words)}…”` : '<span class="muted">—</span>'}</td><td>${found.length ? found.join('<br>') : inOrder ? `<span class="badge other">Set in each order</span> <span class="muted small">${e(inOrder)}</span>` : '<span class="badge warn">To identify</span>'}</td></tr>`;
        })
        .join('');
      write(
        `acts/${act.id}/related.html`,
        layout({
          title: `Rules, regulations and notifications under the ${act.title} — ${site.name}`,
          description: `Instruments made under the ${act.title}, section by section, with the latest editions on the regulator's website.`,
          base,
          page: 'act',
          body: `
  <section class="prose related-page">
    <p class="crumbs"><a href="${base}index.html">Library</a> / <a href="index.html">${e(act.title)}</a></p>
    <h1>Rules, regulations and notifications under the ${e(act.title)}</h1>
    <p>This register tracks the instruments made under the Act, so each one can be kept up to date with the editions published by the regulator. Links from instruments in the library are found automatically from the sections they cite; the others are recorded by hand with the basis for each link.</p>
    <p class="muted small">Check the regulator's lists: ${Object.keys(register.secpPages || {}).map(pageLink).join(' · ')}. SECP's website blocks automated access, so editions are confirmed by hand and the screenshot of each check is kept.</p>
    <h2>Instruments</h2>
    <div class="table-wrap"><table class="sources-table related-table">
      <thead><tr><th>Instrument</th><th>Sections</th><th>Library</th><th>Latest edition on the regulator's website</th><th>Basis</th></tr></thead>
      <tbody>${instrumentRows}</tbody>
    </table></div>
    <h2>Section by section</h2>
    <p>Sections that leave details to be specified, prescribed or made by regulations or rules, and the instruments that carry them out: <strong>${covered}</strong> with an instrument identified, <strong>${byOrder}</strong> set case by case in an order or notice (no instrument expected), <strong>${open}</strong> still to identify.</p>
    <label class="toggle" id="to-identify"><input type="checkbox" id="only-open"> Show only sections still to identify</label>
    <div class="table-wrap"><table class="sources-table related-sections">
      <thead><tr><th>Section</th><th>Heading</th><th>What the Act leaves to rules or regulations</th><th>Instruments</th></tr></thead>
      <tbody>${sectionRows}</tbody>
    </table></div>
  </section>`,
        })
      );

      // ---------- forms of older rules matched to this Act's sections ----------
      for (const m of extras.formMaps.filter((x) => x.act === act.id)) {
        const secLink = (n) => `<a href="index.html#${provisionAnchor(n)}">${e(displayNo(n))}</a>`;
        // One heading row per subject, then its forms.
        const rows = m.forms
          .map((f, i) => {
            const head = i === 0 || m.forms[i - 1].subject !== f.subject
              ? `<tr class="group-row"><th colspan="5" scope="rowgroup">${e(f.subject)}${f.note ? ` — <span class="muted small">${e(f.note)}</span>` : ''}</th></tr>`
              : '';
            return `${head}<tr><td>${f.form}</td><td>${e(f.rule || '')}</td><td>${e(f.title)}</td><td>${f.ordinance1984.length ? f.ordinance1984.map(e).join(', ') : '<span class="muted">—</span>'}</td><td>${f.act2017.map(secLink).join(', ')}</td></tr>`;
          })
          .join('');
        write(
          `acts/${act.id}/forms-${m.id}.html`,
          layout({
            title: `Forms of the ${m.instrument} and the ${act.title} — ${site.name}`,
            description: `Each form of the ${m.instrument} with the section of the ${act.title} on the same subject.`,
            base,
            page: 'act',
            body: `
  <section class="prose related-page">
    <p class="crumbs"><a href="${base}index.html">Library</a> / <a href="index.html">${e(act.title)}</a> / <a href="related.html">Rules, regulations and notifications</a></p>
    <h1>Forms of the ${e(m.instrument)} and the ${e(act.title)}</h1>
    <p>${e(m._about)}</p>
    <p class="muted small">Matched on ${dateLabel(m.matched)}. ${m.forms.length} forms.</p>
    <div class="table-wrap"><table class="sources-table related-table">
      <thead><tr><th>Form</th><th>Rule</th><th>Title</th><th>Companies Ordinance, 1984</th><th>${e(act.title)}</th></tr></thead>
      <tbody>${rows}</tbody>
    </table></div>
  </section>`,
          })
        );
      }
    }

    // ---------- comparison with the law this Act replaced ----------
    for (const c of (extras.comparisons || []).filter((x) => x.act === act.id)) {
      const byNo = new Map(act.parts.flatMap((p) => p.sections).map((s) => [s.no, s]));
      const secLink = (n) => `<a href="index.html#${provisionAnchor(n)}">${e(displayNo(n))}</a>`;
      const other = c.otherId && acts.find((x) => x.id === c.otherId);
      const otherNos = new Set(other ? other.parts.flatMap((p) => p.sections.map((s) => s.no)) : []);
      const ordLink = (n) => (otherNos.has(n) ? `<a href="../${c.otherId}/index.html#${provisionAnchor(n)}">${e(n)}</a>` : e(n));
      const ord = (n) => `${ordLink(n)}${c.titles?.[n] ? ` <span class="muted small">${e(c.titles[n])}</span>` : ''}`;
      const rows = c.pairs
        .map((p) => `<tr id="s-${p.a}"${p.src === 'differs' ? ' class="differs"' : ''}><td>${secLink(p.a)}</td><td>${e(byNo.get(p.a)?.title || '')}</td><td>${p.o.length ? p.o.map(ord).join('<br>') : `<span class="muted">— (${c.newText || 'new section'})</span>`}${p.src === 'probable' ? ' <span class="badge warn">probable, matched by subject</span>' : ''}${p.alt ? `<br><span class="badge warn">The two comparisons differ</span> <span class="muted small">the other lists: ${p.alt.length ? p.alt.map(ordLink).join(', ') : 'none'}</span>` : ''}${p.note ? `<br><span class="muted small">${e(p.note)}</span>` : ''}</td></tr>`)
        .join('');
      const nDiff = c.pairs.filter((p) => p.src === 'differs').length;
      write(
        `acts/${act.id}/${c.id}.html`,
        layout({
          title: `${act.title} compared with the ${c.otherTitle} — ${site.name}`,
          description: `For each section of the ${act.title}, the section of the ${c.otherTitle} on the same matter.`,
          base,
          page: 'act',
          body: `
<section class="prose related-page">
  <p class="crumbs"><a href="${base}index.html">Library</a> / <a href="index.html">${e(act.title)}</a></p>
  <h1>${e(act.title)} compared with the ${e(c.otherTitle)}</h1>
  <p>${e(c._about)}</p>
  <p class="note-box"><strong>Unverified.</strong> ${c.note ? e(c.note) : `${c.pairs.length} sections of the Act. ${nDiff} are marked where the two comparisons differ. ${e(c.missing)}`}</p>
  <div class="table-wrap"><table class="sources-table related-table">
    <thead><tr><th>${e(act.title)}</th><th>Heading</th><th>${e(c.otherTitle)}, section</th></tr></thead>
    <tbody>${rows}</tbody>
  </table></div>
  ${c.unmatchedOrdinance?.length ? `<h2>Sections of the ${e(c.otherWord || 'Ordinance')} not matched to a section of the ${e(c.actWord || 'Act')}</h2><p class="muted small">Omitted, or merged into another section: ${c.unmatchedOrdinance.map((n) => ord(n)).join('; ')}.</p>` : ''}
</section>`,
        })
      );
    }

  }

  // ---------- search ----------
  write(
    'search.html',
    layout({
      title: `Search — ${site.name}`,
      base: '',
      page: 'search',
      body: `
  <section class="search-page">
    <h1>Search the library</h1>
    <form class="searchbar" id="search-form" role="search">
      <label class="sr-only" for="q">Search</label>
      <input id="q" name="q" type="search" placeholder="Words or phrases, or jump: &ldquo;s 204 CA 2017&rdquo;" autocomplete="off" autofocus>
      <button type="submit">Search</button>
    </form>
    <div class="filters">
      <label>Practice area
        <select id="f-cat"><option value="">All</option>${catalog.categories.map((c) => `<option value="${c.id}">${e(c.name)}</option>`).join('')}</select>
      </label>
      <label>Instrument type
        <select id="f-type"><option value="">All</option>${[...new Set(acts.map((a) => a.type))].map((t) => `<option value="${t}">${typeLabel(t)}</option>`).join('')}</select>
      </label>
    </div>
    <fieldset class="search-in">
      <legend>Search in</legend>
      <label><input type="checkbox" id="in-text" checked> Provision text and headings</label>
      <label><input type="checkbox" id="in-notes"> Amendment notes (footnotes)</label>
      <label><input type="checkbox" id="in-meaning"> Search by meaning (AI)</label>
    </fieldset>
    <p class="muted small">Search by meaning finds sections on your topic even when the words differ: try a plain question such as <em>can a director borrow money from the company?</em> It runs on your own device, so what you type is not sent anywhere. The first use downloads about 35&nbsp;MB. It shows only the law's own text, but can miss sections, so do not rely on it alone.</p>
    <p class="muted small">Tips: use quotes for an exact phrase (<code>"proceeds of crime"</code>). All words must match. Laws and rules can be found by short names and topics too: see the <a href="search-guide.html">Search guide</a>.</p>
    <div id="results" aria-live="polite"></div>
    <section id="search-help" class="search-help">
      <h2>How to search</h2>
      <div class="help-grid">
        <div><h3>Words</h3><p>Every word must appear. Words match from their start, so <a href="search.html?q=deprec">deprec</a> finds depreciation but <em>gst</em> does not find “amongst”.</p></div>
        <div><h3>Exact phrase</h3><p>Put a phrase in quotes: <a href="search.html?q=%22proceeds%20of%20crime%22">"proceeds of crime"</a>, <a href="search.html?q=%22related%20party%22">"related party"</a>.</p></div>
        <div><h3>Go straight to a provision</h3><p>Type the unit, number and short name: <a href="search.html?q=s%20149%20ITO">s 149 ITO</a>, <a href="search.html?q=section%20204%20CA%202017">section 204 CA 2017</a>, <a href="search.html?q=rule%2044%20ITR">rule 44 ITR</a>, <a href="search.html?q=reg%2048%20CR%202024">reg 48 CR 2024</a>.</p></div>
        <div><h3>Short names and topics</h3><p>Abbreviations and everyday terms find the law itself: <a href="search.html?q=WHT">WHT</a>, <a href="search.html?q=GST">GST</a>, <a href="search.html?q=KYC">KYC</a>, <a href="search.html?q=e-voting">e-voting</a>. Every term is listed in the <a href="search-guide.html">Search guide</a>.</p></div>
        <div><h3>Narrow down</h3><p>Choose a practice area or instrument type above, combine words (<a href="search.html?q=penalty%20return%20default">penalty return default</a>), or add a law's short name (<a href="search.html?q=penalty%20STA">penalty STA</a>).</p></div>
        <div><h3>Amendment history</h3><p>Tick <em>Amendment notes</em> to search the footnotes, for example a Finance Act or an S.R.O. number (<a href="search.html?q=%22Finance%20Act%2C%202024%22&notes=1">"Finance Act, 2024"</a>).</p></div>
      </div>
      <h3>Short names for jumping</h3>
      <p class="small">${acts.filter((a) => (a.aliases || []).length).map((a) => `<span class="nowrap"><code>${e(a.aliases[0])}</code> ${e(a.title)}</span>`).join(' · ')}</p>
      <p class="muted small">Results show provisions with your words in the heading first. Text marked <span class="badge warn">Unverified</span> has not yet been checked word for word against the official PDF; confirm it there before quoting.</p>
    </section>
  </section>`,
    })
  );

  // ---------- shelf ----------
  write(
    'shelf.html',
    layout({
      title: `My shelf — ${site.name}`,
      base: '',
      page: 'shelf',
      body: `
  <section>
    <h1>My shelf</h1>
    <p class="muted">Provisions you save with the <em>Save</em> button are kept in this browser, so they are there when you go back to a matter.</p>
    <div id="shelf"></div>
  </section>`,
    })
  );

  // ---------- sources & updates ----------
  {
    // data/update-check.json is written by scripts/check_updates.mjs (run weekly by CI).
    const reportPath = path.join(ROOT, 'data', 'update-check.json');
    const report = fs.existsSync(reportPath) ? JSON.parse(fs.readFileSync(reportPath, 'utf8')) : { checkedAt: null, results: [] };
    const byId = new Map(report.results.map((r) => [r.id, r]));
    const STATUS = {
      newer: ['bad', 'Newer edition published'],
      current: ['ok', 'Latest edition'],
      manual: ['warn', 'Check on the website'],
    };
    const order = { newer: 0, manual: 1, current: 2 };
    // Where the automated check could not read the page, a hand check (with its screenshot) decides.
    const statusOf = (a) => {
      const r = byId.get(a.id);
      const hand = handCheck(a, extras.checks);
      if (hand && (!r || r.status === 'manual' || hand.date > (report.checkedAt || ''))) return { ...r, status: hand.status, hand };
      return r;
    };
    const rows = acts
      .map((a) => ({ a, r: statusOf(a) }))
      .sort((x, y) => (order[x.r?.status] ?? 1) - (order[y.r?.status] ?? 1) || x.a.title.localeCompare(y.a.title))
      .map(({ a, r }) => {
        const [cls, label] = STATUS[r?.status] || STATUS.manual;
        const latest = r?.hand
          ? `<br><span class="muted small">Checked by hand ${dateLabel(r.hand.date)}: listed as “${e(r.hand.entry.listed)}”.${r.hand.entry.note ? ` ${e(r.hand.entry.note)}` : ''} ${evidenceLink('', r.hand.screenshot)}</span>`
          : r?.status === 'newer' && r.latest
            ? `<br><a href="${e(r.latest.url)}" target="_blank" rel="noopener">${e(r.latest.title)}</a>`
            : r?.status === 'manual' ? `<br><span class="muted small">${e(r.note)}</span>` : '';
        const page = r?.page || a.source.url;
        return `
        <tr data-status="${r?.status || 'manual'}" data-ver="${a.verification.status}" data-text="${e((a.title + ' ' + (a.number || '')).toLowerCase())}">
          <td><a href="acts/${a.id}/index.html">${e(a.title)}</a></td>
          <td>${a.amendedUpToLabel ? e(a.amendedUpToLabel) : a.enacted ? `As enacted (${e(a.enacted)})` : 'Not stated'}</td>
          <td><span class="badge ${cls}">${label}</span>${latest}</td>
          <td>${verificationBadge(a)}</td>
          <td><a href="${e(page)}" target="_blank" rel="noopener">${e(new URL(page).hostname.replace(/^www\./, ''))}</a></td>
        </tr>`;
      })
      .join('');
    const statuses = acts.map((a) => statusOf(a)?.status || 'manual');
    const count = (st) => statuses.filter((x) => x === st).length;
    const gallery = extras.checks
      .slice()
      .sort((x, y) => y.date.localeCompare(x.date))
      .map(
        (c) => `
        <figure class="evidence">
          <a href="evidence/${e(c.screenshot)}" target="_blank" rel="noopener"><img src="evidence/${e(c.screenshot)}" alt="Screenshot of ${e(c.listing)} taken ${dateLabel(c.date)}" loading="lazy"></a>
          <figcaption><strong>${e(c.listing)}</strong>, ${dateLabel(c.date)}. <a href="${e(c.page)}" target="_blank" rel="noopener">Open the page</a><br>
          <span class="muted small">Covers: ${Object.keys(c.covers).map((id) => `<a href="acts/${id}/index.html">${e(acts.find((a) => a.id === id).title)}</a>`).join(', ')}</span></figcaption>
        </figure>`
      )
      .join('');
    write(
      'sources.html',
      layout({
        title: `Sources and updates — ${site.name}`,
        base: '',
        page: 'sources',
        body: `
  <section class="prose sources-page">
    <h1>Sources and updates</h1>
    <p>Each instrument is taken from the regulator's own consolidated edition. This page compares the edition in the library with the latest edition listed on the regulator's website, so you can see which laws need checking.</p>
    ${report.checkedAt
      ? `<p><strong>Status:</strong> ${count('newer')} with a newer edition, ${count('manual')} to check on the website, ${count('current')} the latest edition. <span class="muted small">Automated check ${e(report.checkedAt)}${extras.checks.length ? `; latest hand check ${e(extras.checks.map((c) => c.date).sort().pop())}` : ''}.</span></p>`
      : '<p>No automated check has been run yet.</p>'}
    <div class="note-box"><strong>Two different checks.</strong> <em>Edition status</em> says whether the library holds the latest edition the regulator lists (<span class="badge ok">Latest edition</span>). <em>Text checked</em> says whether a person has compared the library's text word for word with that PDF (<span class="badge ok">Verified</span>); until then it is <span class="badge warn">Unverified</span> and should be confirmed against the PDF before it is quoted. An instrument can be the latest edition and still unverified.</div>
    <p class="muted small">The check runs every week. FBR and FMU pages are read automatically. SECP's website blocks automated access and Pakistan Code lists no edition dates, so those laws are checked by hand and a screenshot of each check is kept below.</p>
    <div class="src-cards" role="group" aria-label="Filter the table">
      <button type="button" class="src-card is-on" data-src-filter="all"><strong>${acts.length}</strong><span>all instruments</span></button>
      <button type="button" class="src-card" data-src-filter="status:current"><strong>${count('current')}</strong><span>latest edition confirmed</span></button>
      <button type="button" class="src-card" data-src-filter="status:manual"><strong>${count('manual')}</strong><span>to check on the website</span></button>
      <button type="button" class="src-card" data-src-filter="status:newer"><strong>${count('newer')}</strong><span>newer edition listed</span></button>
      <button type="button" class="src-card" data-src-filter="ver:verified"><strong>${acts.filter((a) => a.verification.status === 'verified').length}</strong><span>text marked verified</span></button>
      <button type="button" class="src-card" data-src-filter="ver:unverified"><strong>${acts.filter((a) => a.verification.status !== 'verified').length}</strong><span>text unverified</span></button>
    </div>
    <input id="src-filter" class="src-filter" type="search" placeholder="Filter by title or number" autocomplete="off" aria-label="Filter instruments by title or number">
    <p id="src-count" class="muted small" aria-live="polite"></p>
    <div class="table-wrap">
      <table class="sources-table" id="sources-table">
        <thead><tr><th>Instrument</th><th>Edition in the library</th><th>Edition status</th><th>Text checked</th><th>Regulator page</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
    ${gallery ? `<h2>Screenshots of the regulator's listings</h2><p>Each screenshot shows the regulator's own list of editions on the day it was checked, so you can see that the edition in the library is the latest one published.</p><div class="evidence-grid">${gallery}</div>` : ''}
  </section>`,
      })
    );
  }

  // ---------- catalogue of what a regulator administers, and what the library covers ----------
  for (const cat of extras.catalogues) {
    const all = cat.categories.flatMap((g) => g.items);
    const state = (x) =>
      x.library ? '<span class="badge ok">In library</span>'
      : x.register ? '<span class="badge other">In register</span>'
      : x.status === 'repealed' ? '<span class="badge bad">Repealed</span>'
      : '<span class="badge warn">Not in library yet</span>';
    const name = (x) =>
      x.library ? `<a href="acts/${x.library}/index.html">${e(x.title)}</a>`
      : x.register ? `<a href="acts/${x.register}/related.html">${e(x.title)}</a>`
      : x.url ? `<a href="${e(x.url)}" target="_blank" rel="noopener">${e(x.title)}</a>` : e(x.title);
    const sections = cat.categories
      .map((g) => `<h2 id="${g.id}">${e(g.name)}</h2><div class="table-wrap"><table class="sources-table"><thead><tr><th>Instrument</th><th>Type</th><th>Coverage</th><th>Notes</th></tr></thead><tbody>${g.items
        .map((x) => `<tr><td>${name(x)}${x.number ? `<br><span class="muted small">${e(x.number)}</span>` : ''}</td><td>${typeLabel(x.type === 'register' ? 'regulations' : x.type)}</td><td>${state(x)}${x.saved ? ' <span class="muted small">PDF saved</span>' : ''}</td><td class="small">${e(x.note || '')}${x.found ? `${x.note ? '<br>' : ''}<span class="muted">Found ${dateLabel(x.found.date)} through a search engine's index of SECP's website; confirm the edition.</span>` : ''}</td></tr>`)
        .join('')}</tbody></table></div>`)
      .join('');
    write(
      cat.id === 'secp' ? 'laws.html' : `laws-${cat.id}.html`,
      layout({
        title: `SECP laws and regulations — ${site.name}`,
        description: 'Acts, rules and regulations administered by the Securities and Exchange Commission of Pakistan, and which of them are in the library.',
        base: '',
        page: 'laws',
        body: `
  <section class="prose related-page">
    <h1>Laws and regulations administered by SECP</h1>
    <p>What the Securities and Exchange Commission of Pakistan administers, sector by sector, and how much of it the library already holds: <strong>${all.filter((x) => x.library).length}</strong> in the library, <strong>${all.filter((x) => x.register && !x.library).length}</strong> recorded in a register, <strong>${all.filter((x) => !x.library && !x.register && x.status !== 'repealed').length}</strong> not in the library yet.</p>
    <p class="muted small">${e(cat.intro || '')}</p>
    <nav class="chips" aria-label="Sectors">${cat.categories.map((g) => `<a class="chip" href="#${g.id}">${e(g.name)}</a>`).join('')}</nav>
    ${sections}
  </section>`,
      })
    );
  }

  // ---------- index of the whole library, by subject, with a link to each instrument ----------
  {
    const groups = JSON.parse(fs.readFileSync(path.join(dataDir || path.join(ROOT, 'data'), 'contents-groups.json'), 'utf8')).groups;
    const byId = new Map(acts.map((a) => [a.id, a]));
    const seen = new Map();
    for (const g of groups) for (const id of g.items) {
      if (!byId.has(id)) throw new Error(`contents-groups.json lists unknown instrument ${id}`);
      if (seen.has(id)) throw new Error(`contents-groups.json lists ${id} twice (${seen.get(id)} and ${g.id})`);
      seen.set(id, g.id);
    }
    const missing = acts.filter((a) => !seen.has(a.id)).map((a) => a.id);
    if (missing.length) throw new Error(`contents-groups.json lacks: ${missing.join(', ')}`);
    const nProv = (a) => a.parts.reduce((n, p) => n + p.sections.length, 0);
    const row = (a) => `<li class="idx-item" data-q="${e((a.title + ' ' + (a.number || '') + ' ' + (a.aliases || []).join(' ')).toLowerCase())}">
        <a href="acts/${a.id}/index.html"><span class="idx-title">${e(a.title)}</span></a>
        <span class="idx-meta">${a.number ? e(a.number) + ' · ' : ''}${e(typeLabel(a.type))}${a.status === 'repealed' ? ' <span class="badge bad">Repealed</span>' : ''}${a.pdfOnly || !nProv(a) ? ' · text in the official PDF' : ` · ${nProv(a)} ${a.unit.toLowerCase()}${nProv(a) === 1 ? '' : 's'}`}${a.amendedUpToLabel ? ' · ' + e(a.amendedUpToLabel) : ''}${a.verification.status === 'verified' ? ' <span class="badge ok">Checked</span>' : ''}</span>
        ${a.id === 'companies-act-2017' ? '<span class="idx-meta"><a href="acts/companies-act-2017/related.html">Rules, regulations and notifications by section</a></span>' : ''}
      </li>`;
    const body = groups
      .map((g) => `<section class="idx-group" id="${g.id}"><h2>${e(g.name)} <span class="muted small">${g.items.length}</span></h2><p class="muted small">${e(g.intro)}</p><ol class="idx-list">${g.items.map((id) => row(byId.get(id))).join('')}</ol></section>`)
      .join('');
    write(
      'contents.html',
      layout({
        title: `Index — ${site.name}`,
        description: 'Every law, rule and regulation in the library, by subject, with a link to each.',
        base: '',
        page: 'contents',
        body: `
  <section class="prose contents-page wide">
    <h1>Index of laws, rules and regulations</h1>
    <p>All ${acts.length} instruments in the library, by subject: the Act first, then the rules and regulations made under it. Each title opens the instrument. For laws SECP administers that are not here yet, see <a href="laws.html">SECP laws</a>.</p>
    <input class="idx-filter" id="idx-filter" type="search" placeholder="Filter by title, number or short name" aria-label="Filter the index" autocomplete="off">
    <nav class="chips" aria-label="Subjects">${groups.map((g) => `<a class="chip" href="#${g.id}">${e(g.name)}</a>`).join('')}</nav>
    <p class="muted small" id="idx-empty" hidden>Nothing matches.</p>
    ${body}
  </section>
  <script>(function(){var f=document.getElementById('idx-filter');if(!f)return;f.addEventListener('input',function(){var q=f.value.trim().toLowerCase(),n=0;document.querySelectorAll('.idx-item').forEach(function(li){var ok=!q||li.getAttribute('data-q').indexOf(q)>-1;li.hidden=!ok;if(ok)n++;});document.querySelectorAll('.idx-group').forEach(function(g){g.hidden=!!q&&!g.querySelector('.idx-item:not([hidden])');});document.getElementById('idx-empty').hidden=n>0;});})();</script>`,
      })
    );
  }

  // Search guide extras: common starting points and an A-Z of terms (every term -> the laws it finds).
  const actById = new Map(acts.map((a) => [a.id, a]));
  const taskFile = path.join(dataDir || path.join(ROOT, 'data'), 'search-guide-tasks.json');
  const taskList = fs.existsSync(taskFile) ? JSON.parse(fs.readFileSync(taskFile, 'utf8')).tasks || [] : [];
  const actLink = (a) => `<a href="acts/${a.id}/index.html">${e(a.title)}</a>`;
  const guideTasks = taskList.length
    ? `<section class="guide-cat" id="tasks"><h2>Common starting points <span class="count">${taskList.length}</span></h2><p class="muted small">Where to look first for a common job. These open whole laws and rules, not particular provisions.</p><dl class="term-list">${taskList
        .map((t) => {
          const laws = t.laws.map((id) => actById.get(id)).filter(Boolean);
          return laws.length ? `<div data-q="${e((t.task + ' ' + laws.map((a) => a.title).join(' ')).toLowerCase())}"><dt>${e(t.task)}</dt><dd class="task-laws">${laws.map(actLink).join(' ')}</dd></div>` : '';
        })
        .join('')}</dl></section>`
    : '';
  const azMap = new Map();
  for (const a of acts) {
    for (const t of searchTermsFor(a)) {
      const key = t.toLowerCase();
      if (!azMap.has(key)) azMap.set(key, { label: t, laws: [] });
      azMap.get(key).laws.push(a);
    }
  }
  const azLetters = new Map();
  [...azMap.values()]
    .sort((x, y) => x.label.toLowerCase().localeCompare(y.label.toLowerCase()))
    .forEach((t) => {
      const ch = /^[a-z]/i.test(t.label) ? t.label[0].toUpperCase() : '#';
      if (!azLetters.has(ch)) azLetters.set(ch, []);
      azLetters.get(ch).push(t);
    });
  const guideAz = `<section id="az"><h2>A–Z of terms <span class="count">${azMap.size}</span></h2><p class="muted small">Every name and topic, with the laws it finds. Select a term to search for it.</p><nav class="chips az-nav" aria-label="Letters">${[...azLetters.keys()].map((l) => `<a class="chip" href="#az-${l === '#' ? 'num' : l}">${l}</a>`).join('')}</nav>${[...azLetters.entries()]
    .map(
      ([l, list]) =>
        `<section class="guide-cat az-letter"><h3 id="az-${l === '#' ? 'num' : l}">${l}</h3><ul class="az-list">${list
          .map((t) => `<li data-q="${e((t.label + ' ' + t.laws.map((a) => a.title).join(' ')).toLowerCase())}"><a class="az-term" href="search.html?q=${encodeURIComponent(t.label)}">${e(t.label)}</a> <span class="muted small">${t.laws.map(actLink).join(' · ')}</span></li>`)
          .join('')}</ul></section>`
    )
    .join('')}</section>`;

  // ---------- search guide: every instrument with the names and topics it can be found by ----------
  write(
    'search-guide.html',
    layout({
      title: `Search guide — ${site.name}`,
      description: 'Short names, abbreviations and topics that find each law, rule and regulation in the library.',
      base: '',
      page: 'search-guide',
      body: `
  <section class="prose search-guide wide">
    <h1>Search guide</h1>
    <p>Type any of these in the search box. A short name or topic lists the matching law or rule above the provision results; a short name also works for jumping to a provision, for example <a href="search.html?q=s%20149%20ITO"><code>s 149 ITO</code></a> or <a href="search.html?q=s%20204%20CA%202017"><code>s 204 CA 2017</code></a>.</p>
    <p class="muted small">Topics point to a whole law or rule, not to a particular provision. Use the provision search for the words of the law itself.</p>
    <input class="idx-filter" id="guide-filter" type="search" placeholder="Filter by law, number or topic" aria-label="Filter the search guide" autocomplete="off">
    <nav class="chips" aria-label="Jump to">${[['tasks', 'Common starting points'], ['az', 'A–Z of terms'], ...catalog.categories.map((c) => ['cat-' + c.id, c.name])].map(([h, n]) => `<a class="chip" href="#${h}">${e(n)}</a>`).join('')}</nav>
    ${guideTasks}
    ${guideAz}
    ${catalog.categories
      .map((c) => {
        const list = acts.filter((a) => a.categories.includes(c.id));
        if (!list.length) return '';
        const withTerms = list.filter((a) => searchTermsFor(a).length);
        const without = list.filter((a) => !searchTermsFor(a).length);
        return `<section class="guide-cat"><h2 id="cat-${c.id}">${e(c.name)} <span class="count">${withTerms.length}</span></h2><dl class="term-list">${withTerms
          .map((a) => `<div data-q="${e((a.title + ' ' + (a.number || '') + ' ' + searchTermsFor(a).join(' ')).toLowerCase())}"><dt><a href="acts/${a.id}/index.html">${e(a.title)}</a>${a.number ? ` <span class="muted small">${e(a.number)}</span>` : ''}</dt><dd>${searchTermsFor(a).map((t) => `<a class="chip" href="search.html?q=${encodeURIComponent(t)}">${e(t)}</a>`).join(' ')}</dd></div>`)
          .join('')}</dl>${without.length ? `<details class="no-terms"><summary>${without.length} more with no everyday names recorded yet</summary><p class="muted small">Search finds these by their title and number. Names and topics can be added to <code>data/search-terms.json</code>.</p><ul>${without.map((a) => `<li data-q="${e((a.title + ' ' + (a.number || '')).toLowerCase())}"><a href="acts/${a.id}/index.html">${e(a.title)}</a></li>`).join('')}</ul></details>` : ''}</section>`;
      })
      .join('')}
  </section>`,
    })
  );

  // ---------- about ----------
  write(
    'about.html',
    layout({
      title: `About — ${site.name}`,
      base: '',
      page: 'about',
      body: `
  <section class="prose">
    <h1>About ${e(site.name)}</h1>
    <p>${e(site.name)} is a reference library of bare acts and the rules and regulations made under them, laid out for fast reading, searching and quoting.</p>
    <h2>How to use it</h2>
    <ul>
      <li><strong>Cite</strong> copies a formal citation, for example <em>Section 111 of the Income Tax Ordinance, 2001 (Ordinance No. XLIX of 2001)</em>.</li>
      <li><strong>Quote</strong> copies the provision text followed by its citation, ready for an opinion or pleading.</li>
      <li><strong>Link</strong> copies a permanent link to the provision.</li>
      <li><strong>Save</strong> keeps the provision on <a href="shelf.html">My shelf</a>.</li>
      <li>Search accepts words, exact phrases in quotes, or a direct jump such as <code>s 3 AMLA</code>.</li>
      <li><strong>PDF p.</strong> opens the official source PDF at the page where the provision is printed, so you can check the text before relying on it.</li>
      <li>Superscript numbers mark amendments; open <em>Amendment notes</em> under a provision to see what changed and by which Finance Act or S.R.O.</li>
      <li>Search and every instrument you have opened keep working offline. The site can be installed on a phone or desktop from the browser menu.</li>
    </ul>
    <h2>Verification</h2>
    <p id="verification">Every instrument carries a verification status. <span class="badge ok">Verified</span> means the editor has accepted the text against the named official source on the stated date. Most instruments are marked verified because the text was converted directly from the regulator\'s own PDF, which the editor declared reliable; that is not a line-by-line proofread, so quote a provision only after opening its <em>PDF p.</em> link. <span class="badge warn">Unverified</span> text has not yet been checked and should not be quoted without confirming it.</p>
    <h2>Search by meaning (AI)</h2>
    <p>Search can also find sections by meaning, using an open-source model (BGE small, MIT licence) that runs on your own device. There is no account or usage limit, and what you type is not sent anywhere. The model downloads once from public hosts (Hugging Face and jsDelivr). It only ranks sections: it writes no text, and it can miss sections, so check the law itself.</p>
    <h2>Disclaimer</h2>
    <p>This library is a research aid and not a substitute for the official Gazette. It does not constitute legal advice.</p>
  </section>`,
    })
  );

  // ---------- search index ----------
  const index = {
    acts: acts.map((a) => ({
      id: a.id,
      title: a.title,
      number: a.number,
      type: a.type,
      unit: a.unit,
      categories: a.categories,
      aliases: a.aliases || [],
      terms: extras.searchTerms[a.id] || [],
      verified: a.verification.status === 'verified',
      placeholder: !!a.placeholder,
    })),
    provisions: acts.flatMap((a) => {
      const pdf = a.sourcePdfUrl || `sources/${a.id}.pdf`;
      const st = scheduleText.get(a.id);
      const schedRows = st
        ? st.schedules
            .filter((x) => x.text)
            .map((x) => ({ act: a.id, no: '', title: x.title, part: st.pdfOnly ? 'Official PDF' : 'Schedules and annexures', anchor: '', pdf: x.pdf ? `sources/${x.pdf}` : pdf, pdfPage: x.page, text: x.text }))
        : [];
      if (a.pdfOnly) return schedRows.length ? schedRows : [{ act: a.id, no: '', title: a.title, part: 'Official PDF', anchor: '', text: a.summary || '' }];
      return [
        ...a.parts.flatMap((p) =>
          p.sections.map((s) => ({
            act: a.id,
            no: displayNo(s.no),
            title: stripMarkers(s.title),
            part: p.heading,
            anchor: provisionAnchor(s.no),
            text: plainText(s),
          }))
        ),
        ...schedRows,
        ...(a.schedules || []).map((x, k) => (x.text ? { act: a.id, no: '', title: x.title, part: 'Schedules, annexures and forms', anchor: `sched-${k + 1}`, sched: 1, text: x.text.map((t) => stripMarkers(t.replace(/^>+/, ''))).join('\n') } : null)).filter(Boolean),
      ];
    }),
  };
  write('search-index.json', JSON.stringify(index));

  // Search by meaning: vectors are made on a local machine (tools/ai) and committed, so builds need no model.
  // A passage whose wording has changed has no vector until make_vectors is run again.
  const aiDir = path.join(ROOT, 'data', 'ai');
  let aiMissing = 0;
  if (fs.existsSync(path.join(aiDir, 'hashes.json'))) {
    const stored = JSON.parse(fs.readFileSync(path.join(aiDir, 'hashes.json'), 'utf8'));
    const bin = fs.readFileSync(path.join(aiDir, 'vectors.bin'));
    const where = new Map(stored.hashes.map((h, i) => [h, i]));
    const all = passages(index);
    const kept = all.filter((p) => where.has(p.hash));
    aiMissing = all.length - kept.length;
    write('ai-passages.json', JSON.stringify({ model: AI_MODEL, dims: AI_DIMS, prov: kept.map((p) => p.prov), start: kept.map((p) => p.start), len: kept.map((p) => p.len) }));
    write('ai-vectors.bin', Buffer.concat(kept.map((p) => bin.subarray(where.get(p.hash) * AI_DIMS, (where.get(p.hash) + 1) * AI_DIMS))));
  }

  // Amendment notes are searched only when the reader asks for them, so they live in their own file.
  const noteRows = acts.flatMap((a) => [
    ...(a.frontNotes || []).map((f) => ({ a: a.id, k: 'front', no: '', h: 'Title and enacting text', n: fnLabel(f.n), id: `front-fn-${slug(f.n)}`, t: f.text })),
    ...a.parts.flatMap((p, pi) => [
      ...(p.fn || []).map((f) => ({ a: a.id, k: `part-${pi + 1}`, no: '', h: p.heading, n: fnLabel(f.n), id: `part-${pi + 1}-fn-${slug(f.n)}`, t: f.text })),
      ...p.sections.flatMap((s) =>
        (s.fn || []).map((f) => ({
          a: a.id,
          k: provisionAnchor(s.no),
          no: displayNo(s.no),
          h: stripMarkers(s.title),
          n: fnLabel(f.n),
          id: `${provisionAnchor(s.no)}-fn-${slug(f.n)}`,
          t: f.text,
        }))
      ),
    ]),
  ]);
  write('search-notes.json', JSON.stringify(noteRows));

  // ---------- schedule text for the filter box on instrument pages (served as /schedule-text/<id>.json) ----------
  for (const [id, j] of scheduleText) {
    if (byId.has(id)) write(`schedule-text/${id}.json`, JSON.stringify({ s: j.schedules.map((x) => ({ t: x.title, p: x.page, x: x.text, ...(x.pdf ? { f: x.pdf } : {}) })) }));
  }

  // ---------- official source PDFs (served as /sources/<id>.pdf) ----------
  for (const a of acts) {
    if (a.sourcePdf && !a.sourcePdfUrl) write(`sources/${a.id}.pdf`, fs.readFileSync(path.join(ROOT, 'sources', 'pdf', a.sourcePdf)));
    for (const f of new Set((a.schedules || []).map((x) => x.pdf).filter(Boolean))) write(`sources/${f}`, fs.readFileSync(path.join(ROOT, 'sources', 'pdf', f)));
  }

  // ---------- screenshots of hand checks (served as /evidence/<file>) ----------
  for (const c of extras.checks) write(`evidence/${c.screenshot}`, fs.readFileSync(path.join(EVIDENCE_DIR, c.screenshot)));

  // ---------- static assets ----------
  const assetsDir = path.join(ROOT, 'src', 'assets');
  for (const f of fs.readdirSync(assetsDir)) write(`assets/${f}`, fs.readFileSync(path.join(assetsDir, f)));

  write(
    'manifest.webmanifest',
    JSON.stringify(
      {
        name: site.name,
        short_name: site.name,
        description: site.tagline,
        start_url: './index.html',
        scope: './',
        display: 'standalone',
        background_color: '#f7f5f0',
        theme_color: '#1f3a5f',
        icons: [{ src: 'assets/icon.svg', sizes: 'any', type: 'image/svg+xml', purpose: 'any' }],
      },
      null,
      2
    )
  );

  // The service worker precaches the app shell and search index; instrument pages and PDFs
  // are cached as they are opened, so everything a reader has used stays available offline.
  const precache = written.filter((f) => f !== 'sw.js' && f !== 'search-notes.json' && !f.startsWith('ai-') && f !== 'assets/ai-worker.js' && !f.startsWith('acts/') && !f.startsWith('schedule-text/') && !f.startsWith('sources/') && !f.startsWith('evidence/'));
  const version = crypto.createHash('sha256').update(precache.map((f) => f + fs.statSync(path.join(outDir, f)).size).join('|')).update(JSON.stringify(index)).digest('hex').slice(0, 12);
  const sw = fs.readFileSync(path.join(ROOT, 'src', 'sw.template.js'), 'utf8').replace('__VERSION__', version).replace('__PRECACHE__', JSON.stringify(precache.map((f) => `./${f}`)));
  write('sw.js', sw);

  return { outDir, files: written, index, aiMissing };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const { outDir, files, index, aiMissing } = build();
  console.log(`Built ${files.length} files into ${path.relative(ROOT, outDir)}/ (${index.acts.length} instruments, ${index.provisions.length} provisions).`);
  if (aiMissing) console.warn(`${aiMissing} passages have no AI search vector: run tools/ai/make_vectors.mjs`);
}
