#!/usr/bin/env node
// Compares each instrument's edition with the latest edition its regulator lists.
//
//   node scripts/check_updates.mjs                      # print a table
//   node scripts/check_updates.mjs --json data/update-check.json --markdown report.md
//   node scripts/check_updates.mjs --saved sources/saved-pages   # also read pages saved from a browser
//
// Each manifest entry's `watch` names the regulator's listing page and a pattern for the links
// to that law's editions; the "amended / updated up to" date in each link's text (or file name)
// is read and the newest is compared with the entry's `amendedUpTo`. Pages that refuse automated
// access (SECP is behind a bot check) and entries marked `manual` are reported for a manual check.
// For such sites, open the listing page in your own browser, save it ("Save Page As…", HTML only)
// into a folder and pass --saved <folder>: each saved page is matched to its address (the
// "saved from url" note browsers add, or the page's canonical link) and read like a fetched page.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'];

const pad = (n) => String(n).padStart(2, '0');
const iso = (y, m, d) => `${y}-${pad(m)}-${pad(d)}`;
const month = (name) => MONTHS.indexOf(name.slice(0, 3).toLowerCase()) + 1;

/** Dates written in an edition's title: 30.06.2026, 30-06-2026, 30th June, 2026, March 3, 2025, Sep. 2020. */
export function datesIn(text) {
  const t = text.replace(/\s+/g, ' ');
  const out = [];
  for (const m of t.matchAll(/\b(\d{1,2})[.\-/](\d{1,2})[.\-/](20\d\d)\b/g)) {
    if (+m[2] >= 1 && +m[2] <= 12 && +m[1] >= 1 && +m[1] <= 31) out.push(iso(m[3], +m[2], +m[1]));
  }
  for (const m of t.matchAll(/\b(\d{1,2})(?:st|nd|rd|th)?[ -]+([A-Za-z]{3,9})\.?,?[ -]+(20\d\d)\b/g)) {
    if (month(m[2]) > 0) out.push(iso(m[3], month(m[2]), +m[1]));
  }
  for (const m of t.matchAll(/\b([A-Za-z]{3,9})\.? (\d{1,2})(?:st|nd|rd|th)?,? (20\d\d)\b/g)) {
    if (month(m[1]) > 0) out.push(iso(m[3], month(m[1]), +m[2]));
  }
  if (!out.length) {
    // month and year only ("upto Sep. 2020"): the last day of that month
    for (const m of t.matchAll(/\b([A-Za-z]{3,9})\.?,? (20\d\d)\b/g)) {
      const mo = month(m[1]);
      if (mo > 0) out.push(iso(m[2], mo, new Date(Date.UTC(+m[2], mo, 0)).getUTCDate()));
    }
  }
  return out;
}

/** Links on a page as { text, href }. */
export function linksIn(html, baseUrl) {
  const out = [];
  for (const m of html.matchAll(/<a\b[^>]*?href\s*=\s*["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi)) {
    const text = m[2].replace(/<[^>]+>/g, ' ').replace(/&nbsp;|&#160;/g, ' ').replace(/&amp;/g, '&').replace(/\s+/g, ' ').trim();
    let href = m[1].replace(/&amp;/g, '&');
    try {
      href = new URL(href, baseUrl).href;
    } catch {
      continue;
    }
    out.push({ text, href });
  }
  return out;
}

/** Table rows on a listing page (SECP lists editions as rows: date, title, download link) as { text, href }. */
export function rowsIn(html, baseUrl) {
  const out = [];
  for (const m of html.matchAll(/<tr\b[^>]*>([\s\S]*?)<\/tr>/gi)) {
    // The posting date has a cell of its own; only the title carries the edition date.
    const text = [...m[1].matchAll(/<t[dh]\b[^>]*>([\s\S]*?)<\/t[dh]>/gi)]
      .map((c) => c[1].replace(/<[^>]+>/g, ' ').replace(/&nbsp;|&#160;/g, ' ').replace(/&amp;/g, '&').replace(/&#8211;|&ndash;/g, '–').replace(/\s+/g, ' ').trim())
      .filter((c) => c && !/^\d{1,2}[./-]\d{1,2}[./-]\d{4}$/.test(c))
      .join(' ');
    const href = m[1].match(/href\s*=\s*["']([^"']+)["']/i);
    if (!text || !href) continue;
    try {
      out.push({ text: text.replace(/\bDownload\b/gi, '').trim(), href: new URL(href[1].replace(/&amp;/g, '&'), baseUrl).href });
    } catch {
      /* ignore */
    }
  }
  return out;
}

/** The address a saved page came from: the browser's "saved from url" note, or its canonical link. */
export function savedFrom(html) {
  const m =
    html.match(/<!--\s*saved from url=\(\d+\)(\S+?)\s*-->/i) ||
    html.match(/<link[^>]+rel=["']canonical["'][^>]*href=["']([^"']+)["']/i) ||
    html.match(/<link[^>]+href=["']([^"']+)["'][^>]*rel=["']canonical["']/i) ||
    html.match(/<meta[^>]+property=["']og:url["'][^>]*content=["']([^"']+)["']/i);
  return m ? m[1] : null;
}

const samePage = (a, b) => {
  const n = (u) => u.replace(/^https?:\/\/(www\.)?/i, '').replace(/[?#].*$/, '').replace(/\/+$/, '').toLowerCase();
  return n(a) === n(b);
};

/** Pages saved from a browser, as a Map of address to HTML. */
export function loadSaved(dir) {
  const pages = new Map();
  for (const f of fs.readdirSync(dir)) {
    if (!/\.html?$/i.test(f)) continue;
    const html = fs.readFileSync(path.join(dir, f), 'utf8');
    const url = savedFrom(html);
    if (url) pages.set(url, { html, file: f });
  }
  return pages;
}

/** The newest dated edition among the links that match the law. */
export function latestEdition(links, pattern) {
  const re = new RegExp(pattern, 'i');
  let best = null;
  for (const l of links) {
    const name = decodeURIComponent(l.href.split('/').pop() || '');
    if (!re.test(l.text) && !re.test(name.replace(/[-_]+/g, ' ')) && !re.test(name)) continue;
    for (const d of [...datesIn(l.text), ...datesIn(name.replace(/[-_]+/g, ' '))]) {
      if (!best || d > best.date) best = { date: d, title: l.text || name, url: l.href };
    }
  }
  return best;
}

async function fetchPage(url) {
  const res = await fetch(url, {
    headers: { 'user-agent': 'Mozilla/5.0 (compatible; LegalDatabank update check)', accept: 'text/html' },
    redirect: 'follow',
    signal: AbortSignal.timeout(45000),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.text();
}

export async function check(manifest, { saved = new Map() } = {}) {
  const pages = new Map();
  const savedPage = (url) => [...saved.entries()].find(([u]) => samePage(u, url))?.[1];
  const results = [];
  for (const e of manifest) {
    const w = e.watch;
    const row = { id: e.id, title: e.title, edition: e.amendedUpTo || e.enacted || null, editionLabel: e.amendedUpToLabel || null, page: w?.page || e.source?.url };
    if (!w || w.manual) {
      results.push({ ...row, status: 'manual', note: 'No dated editions to compare: check the page by hand.' });
      continue;
    }
    if (!pages.has(w.page)) {
      const copy = savedPage(w.page);
      pages.set(w.page, copy ? Promise.resolve({ html: copy.html, saved: copy.file }) : fetchPage(w.page).then((html) => ({ html }), (err) => ({ err })));
    }
    const page = await pages.get(w.page);
    if (page.err) {
      results.push({ ...row, status: 'manual', note: `The page could not be read automatically (${page.err.message}): check it by hand.` });
      continue;
    }
    const latest = latestEdition([...linksIn(page.html, w.page), ...rowsIn(page.html, w.page)], w.match);
    if (!latest) {
      results.push({ ...row, status: 'manual', note: 'No dated edition found on the page: check it by hand.' });
    } else if (!row.edition || latest.date > row.edition) {
      results.push({ ...row, status: 'newer', latest, ...(page.saved ? { from: `saved page ${page.saved}` } : {}) });
    } else {
      results.push({ ...row, status: 'current', latest, ...(page.saved ? { from: `saved page ${page.saved}` } : {}) });
    }
  }
  return results;
}

const LABEL = { newer: 'Newer edition', current: 'Up to date', manual: 'Check manually' };

export function toMarkdown(results, checkedAt) {
  const rows = results.map(
    (r) =>
      `| ${r.title} | ${r.editionLabel || r.edition || '—'} | ${LABEL[r.status]}${r.latest && r.status === 'newer' ? `: [${r.latest.title}](${r.latest.url}) (${r.latest.date})` : ''} | [source](${r.page}) |`
  );
  return [
    `Checked ${checkedAt}.`,
    '',
    `- **${results.filter((r) => r.status === 'newer').length}** with a newer edition on the regulator's website`,
    `- **${results.filter((r) => r.status === 'manual').length}** to check by hand`,
    `- **${results.filter((r) => r.status === 'current').length}** up to date`,
    '',
    '| Instrument | Edition in the library | Status | Regulator page |',
    '|---|---|---|---|',
    ...rows,
    '',
  ].join('\n');
}

async function main() {
  const args = process.argv.slice(2);
  const opt = (name) => (args.includes(name) ? args[args.indexOf(name) + 1] : null);
  const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, 'sources', 'manifest.json'), 'utf8'));
  const saved = opt('--saved') ? loadSaved(path.resolve(opt('--saved'))) : new Map();
  if (saved.size) console.log(`Read ${saved.size} saved page(s): ${[...saved.keys()].join(', ')}`);
  const results = await check(manifest, { saved });
  const checkedAt = new Date().toISOString().slice(0, 10);
  for (const r of results) {
    const extra = r.status === 'newer' ? ` -> ${r.latest.date} ${r.latest.title}` : r.status === 'manual' ? ` (${r.note})` : '';
    console.log(`${LABEL[r.status].padEnd(15)} ${r.id.padEnd(40)} ${String(r.edition || '—').padEnd(10)}${extra}`);
  }
  if (opt('--json')) fs.writeFileSync(path.resolve(opt('--json')), JSON.stringify({ checkedAt, results }, null, 1) + '\n');
  if (opt('--markdown')) fs.writeFileSync(path.resolve(opt('--markdown')), toMarkdown(results, checkedAt));
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => {
    console.error(err);
    process.exit(1);
  });
}
