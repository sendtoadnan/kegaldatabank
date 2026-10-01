// Builds the static website into dist/ from the JSON library in data/.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
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

const slug = (s) => String(s).toLowerCase().replace(/[^a-z0-9]+/g, '-');

export function build({ outDir = path.join(ROOT, 'dist'), dataDir } = {}) {
  const library = loadLibrary(dataDir);
  const errors = validateLibrary(library);
  if (errors.length) throw new Error(`Library is invalid:\n  - ${errors.join('\n  - ')}`);

  const { catalog, acts } = library;
  const site = catalog.site;
  const byId = new Map(acts.map((a) => [a.id, a]));
  const children = (id) => acts.filter((a) => a.parent === id);
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
    <a href="${base}shelf.html"${page === 'shelf' ? ' aria-current="page"' : ''}>My shelf</a>
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
  <p>${e(site.name)} · ${e(site.jurisdiction)}</p>
</footer>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<script src="${base}assets/app.js" defer></script>
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
  const noteList = (notes, label) =>
    notes && notes.length
      ? `<details class="prov-fns"><summary>${label} (${notes.length})</summary><ol>${notes
          .map((f) => `<li><span class="fn-no">${e(fnLabel(f.n))}</span> ${e(f.text)}</li>`)
          .join('')}</ol></details>`
      : '';

  const provisionCount = (act) => act.parts.reduce((n, p) => n + p.sections.length, 0);
  // Large editions are linked at the regulator's own URL instead of being republished (sourcePdfUrl).
  const pdfHref = (act, base) => act.sourcePdfUrl || `${base}sources/${act.id}.pdf`;

  const actRow = (act, base) => {
    const count = provisionCount(act);
    const size = act.pdfOnly ? 'Official PDF' : `${count} ${act.unit.toLowerCase()}${count === 1 ? '' : 's'}`;
    const upto = act.amendedUpToLabel ? ` · to ${e(act.amendedUpToLabel.replace(/\s*\(.*\)$/, ''))}` : '';
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
    const cats = catalog.categories
      .map((c) => {
        const list = acts.filter((a) => a.categories.includes(c.id));
        const principal = list.filter((a) => !a.parent);
        const rows = principal
          .map((a) => actRow(a, base) + children(a.id).filter((k) => list.includes(k)).map((k) => actRow(k, base).replace('class="act-row"', 'class="act-row child"')).join(''))
          .join('');
        const orphans = list.filter((a) => a.parent && !list.includes(byId.get(a.parent))).map((a) => actRow(a, base)).join('');
        return `
    <section class="category" id="cat-${c.id}">
      <h2>${e(c.name)} <span class="count">${list.length}</span></h2>
      <p class="muted">${e(c.description)}</p>
      <ul class="act-list">${rows}${orphans || ''}</ul>
    </section>`;
      })
      .join('');

    const total = acts.reduce((n, a) => n + provisionCount(a), 0);
    const body = `
  <section class="hero">
    <h1>${e(site.name)}</h1>
    <p class="lede">${e(site.tagline)}</p>
    <form class="searchbar" action="search.html" method="get" role="search">
      <label class="sr-only" for="q">Search the library</label>
      <input id="q" name="q" type="search" placeholder="Search, or jump: s 3 STA" autocomplete="off">
      <button type="submit">Search</button>
    </form>
    <p class="stats">${acts.length} instruments · ${total.toLocaleString('en')} provisions · ${catalog.categories.length} practice areas</p>
  </section>
  <div id="shelf-preview"></div>
  <nav class="chips" aria-label="Practice areas">
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

    const toc = act.parts
      .map(
        (p) => `
        <li><span class="toc-part">${e(p.heading)}</span>
          <ol>${p.sections.map((s) => `<li><a href="#${provisionAnchor(s.no)}"><span class="toc-no">${e(displayNo(s.no))}</span> ${e(s.title || '—')}</a></li>`).join('')}</ol>
        </li>`
      )
      .join('');

    const parts = act.parts
      .map(
        (p) => `
      <section class="part">
        <h2 class="part-heading">${e(p.heading)}</h2>
        ${noteList(p.fn, 'Amendment notes on this heading')}
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
      ['Source', `<a href="${e(act.source.url)}" rel="noopener" target="_blank">${e(act.source.name)}</a>`],
      pdf ? ['Official PDF', `<a href="${pdf}" target="_blank" rel="noopener">Open the source PDF</a>`] : null,
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
      ? `<section class="schedules"><h2>Schedules and annexures</h2><p class="muted small">Schedules are mostly tables, so they are shown as published in the official PDF.</p><ul class="act-list">${act.schedules
          .map((x) => `<li class="act-row"><a href="${pdf}#page=${x.page}" target="_blank" rel="noopener"><span class="act-title">${e(x.title)}</span><span class="act-meta">Official PDF, page ${x.page}</span></a></li>`)
          .join('')}</ul></section>`
      : '';

    const subsidiary = kids.length
      ? `<section class="subsidiary"><h2>Made under this ${typeLabel(act.type)}</h2><ul class="act-list">${kids.map((k) => actRow(k, base)).join('')}</ul></section>`
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
        <label class="sr-only" for="toc-filter">Filter contents</label>
        <input id="toc-filter" class="toc-filter" type="search" placeholder="Filter ${e(act.unit.toLowerCase())}s…">
        <ol class="toc-list">${toc}</ol>
      </details>
    </aside>` : ''}
    <article class="act">
      <p class="crumbs"><a href="${base}index.html">Library</a>${parent ? ` / <a href="../${parent.id}/index.html">${e(parent.title)}</a>` : ''}</p>
      <h1>${e(act.title)} ${verificationBadge(act)}</h1>
      ${act.preamble ? `<p class="preamble">${e(stripMarkers(act.preamble))}</p>` : ''}
      ${noteList(act.frontNotes, 'Amendment notes on the title and enacting text')}
      <dl class="meta">${meta}</dl>
      ${verification}
      ${caution}
      ${sourceNotes}
      ${pdfOnly}
      ${act.parts.length ? `<div class="act-actions"><button type="button" class="btn" onclick="window.print()">Print</button></div>` : ''}
      ${parts}
      ${schedules}
      ${subsidiary}
    </article>
  </div>`;

    write(
      `acts/${act.id}/index.html`,
      layout({ title: `${act.title} — ${site.name}`, description: `${act.title} (${act.number}): full text with contents, citations and related rules.`, base, body, page: 'act' })
    );
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
    <p class="muted small">Tips: use quotes for an exact phrase (<code>"proceeds of crime"</code>). All words must match.</p>
    <div id="results" aria-live="polite"></div>
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
    <p>Every instrument carries a verification status. <span class="badge ok">Verified</span> means an editor has checked the text against the named official source on the stated date. <span class="badge warn">Unverified</span> text has not yet been checked and should not be quoted without confirming it.</p>
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
      verified: a.verification.status === 'verified',
      placeholder: !!a.placeholder,
    })),
    provisions: acts.flatMap((a) =>
      a.pdfOnly
        ? [{ act: a.id, no: '', title: a.title, part: 'Official PDF', anchor: '', text: a.summary || '' }]
        : a.parts.flatMap((p) =>
            p.sections.map((s) => ({
              act: a.id,
              no: displayNo(s.no),
              title: stripMarkers(s.title),
              part: p.heading,
              anchor: provisionAnchor(s.no),
              text: plainText(s),
            }))
          )
    ),
  };
  write('search-index.json', JSON.stringify(index));

  // ---------- official source PDFs (served as /sources/<id>.pdf) ----------
  for (const a of acts) {
    if (a.sourcePdf && !a.sourcePdfUrl) write(`sources/${a.id}.pdf`, fs.readFileSync(path.join(ROOT, 'sources', 'pdf', a.sourcePdf)));
  }

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
  const precache = written.filter((f) => f !== 'sw.js' && !f.startsWith('acts/') && !f.startsWith('sources/'));
  const version = crypto.createHash('sha256').update(precache.map((f) => f + fs.statSync(path.join(outDir, f)).size).join('|')).update(JSON.stringify(index)).digest('hex').slice(0, 12);
  const sw = fs.readFileSync(path.join(ROOT, 'src', 'sw.template.js'), 'utf8').replace('__VERSION__', version).replace('__PRECACHE__', JSON.stringify(precache.map((f) => `./${f}`)));
  write('sw.js', sw);

  return { outDir, files: written, index };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const { outDir, files, index } = build();
  console.log(`Built ${files.length} files into ${path.relative(ROOT, outDir)}/ (${index.acts.length} instruments, ${index.provisions.length} provisions).`);
}
