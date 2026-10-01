import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { loadLibrary, validateLibrary, citation, parseParagraph, provisionAnchor } from '../scripts/lib.mjs';
import { build } from '../scripts/build.mjs';
import { parseStatute } from '../scripts/import-text.mjs';

test('library data is valid', () => {
  const errors = validateLibrary(loadLibrary());
  assert.deepEqual(errors, []);
});

test('validation catches broken instruments', () => {
  const { catalog, acts } = loadLibrary();
  const bad = structuredClone(acts[0]);
  bad.categories = ['nope'];
  bad.parent = 'missing-act';
  bad.verification = { status: 'verified' };
  bad.parts[0].sections.push({ ...bad.parts[0].sections[0] });
  const errors = validateLibrary({ catalog, acts: [bad] });
  assert.ok(errors.some((e) => e.includes('unknown category')));
  assert.ok(errors.some((e) => e.includes('parent "missing-act"')));
  assert.ok(errors.some((e) => e.includes('verification.verifiedBy')));
  assert.ok(errors.some((e) => e.includes('duplicate provision number')));
});

test('citation and anchors', () => {
  const act = { unit: 'Section', title: 'Income Tax Ordinance, 2001', number: 'Ordinance No. XLIX of 2001' };
  assert.equal(citation(act, '111'), 'Section 111 of the Income Tax Ordinance, 2001 (Ordinance No. XLIX of 2001)');
  assert.equal(provisionAnchor('7A'), 's-7a');
  assert.deepEqual(parseParagraph('>>(i) text'), { level: 2, text: '(i) text' });
  assert.deepEqual(parseParagraph('(1) text'), { level: 0, text: '(1) text' });
});

test('build writes pages, search index and offline cache', () => {
  const outDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ldb-'));
  const { files, index } = build({ outDir });
  for (const f of ['index.html', 'search.html', 'shelf.html', 'about.html', 'search-index.json', 'sw.js', 'manifest.webmanifest', 'assets/app.js', 'assets/styles.css']) {
    assert.ok(files.includes(f), `missing ${f}`);
  }
  const { acts } = loadLibrary();
  for (const a of acts) assert.ok(files.includes(`acts/${a.id}/index.html`));

  const ca = fs.readFileSync(path.join(outDir, 'acts/companies-act-2017/index.html'), 'utf8');
  assert.match(ca, /id="s-183"/);
  assert.match(ca, /data-cite="Section 183 of the Companies Act, 2017 \(Act No\. XIX of 2017\)"/);
  assert.match(ca, /Companies Regulations, 2024/, 'parent page lists subsidiary instruments');
  assert.match(ca, /Unverified/);
  assert.match(ca, /href="\.\.\/\.\.\/sources\/companies-act-2017\.pdf#page=\d+"/, 'provisions link to the official PDF page');

  const sta = fs.readFileSync(path.join(outDir, 'acts/sales-tax-act-1990/index.html'), 'utf8');
  assert.match(sta, /<sup class="fnref"><a href="#s-3-fn-/, 'amendment markers link to their notes');
  assert.match(sta, /id="s-3-fn-[^"]+"><span class="fn-no">142<\/span> Substituted for seventeen/, 'note text is attached to its section');
  assert.doesNotMatch(sta, /\{fn:/, 'no raw markers leak into pages');
  assert.ok(fs.existsSync(path.join(outDir, 'sources/sales-tax-act-1990.pdf')), 'source PDF is published');

  const ito = fs.readFileSync(path.join(outDir, 'acts/income-tax-ordinance-2001/index.html'), 'utf8');
  assert.doesNotMatch(ito, /Placeholder, not official text/, 'the ITO is loaded from the FBR edition');
  assert.match(ito, /id="s-111"/);
  assert.match(ito, /data-cite="Section 111 of the Income Tax Ordinance, 2001 \(Ordinance No\. XLIX of 2001\)"/);
  assert.match(ito, /Income Tax Rules, 2002/, 'the ITO page lists the Rules made under it');
  assert.ok(fs.existsSync(path.join(outDir, 'sources/income-tax-ordinance-2001.pdf')), 'ITO source PDF is published');
  const itr = fs.readFileSync(path.join(outDir, 'acts/income-tax-rules-2002/index.html'), 'utf8');
  assert.match(itr, /id="s-231fa"/);
  assert.match(itr, /First Schedule, Part I/, 'schedules link to the official PDF');
  const aml = fs.readFileSync(path.join(outDir, 'acts/aml-act-2010/index.html'), 'utf8');
  assert.match(aml, /Placeholder, not official text/, 'placeholder instruments are clearly marked');

  assert.ok(index.provisions.some((p) => p.act === 'aml-act-2010' && p.no === '3' && p.text.includes('proceeds of crime')));
  assert.ok(index.provisions.every((p) => !/\{fn:/.test(p.text + p.title)), 'search text has no markers');
  const sw = fs.readFileSync(path.join(outDir, 'sw.js'), 'utf8');
  assert.doesNotMatch(sw, /__VERSION__|__PRECACHE__/);
  assert.match(sw, /"\.\/search-index\.json"/);
  fs.rmSync(outDir, { recursive: true, force: true });
});

test('importer turns statute text into provisions', () => {
  const text = `THE SAMPLE ACT, 2024
PART I
PRELIMINARY
1. Short title and commencement.—(1) This Act may be called the Sample Act, 2024.
(2) It shall come into force at once.
2. Definitions.— In this Act,—
(a) "board" means the board of directors;
(b) "company" means a company registered
under this Act;
(i) including a foreign company; and
CHAPTER II — OFFENCES
3. Penalty.—Whoever contravenes this Act shall be punishable with fine.`;
  const act = parseStatute(text, { id: 'sample-act-2024', title: 'Sample Act, 2024', category: 'corporate' });
  assert.equal(act.parts.length, 2);
  assert.equal(act.parts[0].heading, 'Part I — Preliminary');
  assert.equal(act.parts[1].heading, 'Chapter II — Offences');
  const [s1, s2] = act.parts[0].sections;
  assert.equal(s1.no, '1');
  assert.equal(s1.title, 'Short title and commencement');
  assert.deepEqual(s1.text, ['(1) This Act may be called the Sample Act, 2024.', '(2) It shall come into force at once.']);
  assert.equal(s2.text[1], '>(a) "board" means the board of directors;');
  assert.equal(s2.text[2], '>(b) "company" means a company registered under this Act;');
  assert.equal(s2.text[3], '>>(i) including a foreign company; and');
  assert.equal(act.parts[1].sections[0].title, 'Penalty');
  assert.equal(act.verification.status, 'unverified');
});

test('extracted instruments have complete, ordered numbering', () => {
  const { acts } = loadLibrary();
  for (const a of acts.filter((x) => x.sourcePdf && !x.pdfOnly)) {
    const nos = a.parts.flatMap((p) => p.sections.map((s) => s.no));
    const base = nos.map((n) => parseInt(n, 10));
    for (let i = 1; i < base.length; i++) assert.ok(base[i] >= base[i - 1], `${a.id}: ${nos[i]} follows ${nos[i - 1]}`);
    const have = new Set(base);
    const gaps = [];
    const documented = new Set(a.numberingGaps || []);
    for (let n = 1; n <= Math.max(...base); n++) if (!have.has(n) && !documented.has(n)) gaps.push(n);
    assert.deepEqual(gaps, [], `${a.id}: numbering gaps`);
    assert.equal(new Set(nos).size, nos.length, `${a.id}: duplicate provision numbers`);
  }
});
