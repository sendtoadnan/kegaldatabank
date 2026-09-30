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
  assert.match(ca, /Companies \(General Provisions and Forms\) Regulations, 2018/, 'parent page lists subsidiary instruments');
  assert.match(ca, /Unverified/);

  assert.ok(index.provisions.some((p) => p.act === 'aml-act-2010' && p.no === '3' && p.text.includes('proceeds of crime')));
  const sw = fs.readFileSync(path.join(outDir, 'sw.js'), 'utf8');
  assert.match(sw, /"\.\/acts\/income-tax-ordinance-2001\/index\.html"/);
  assert.doesNotMatch(sw, /__VERSION__|__PRECACHE__/);
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
