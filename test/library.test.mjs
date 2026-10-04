import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { loadLibrary, validateLibrary, citation, parseParagraph, provisionAnchor } from '../scripts/lib.mjs';
import { build } from '../scripts/build.mjs';
import { parseStatute } from '../scripts/import-text.mjs';
import { datesIn, linksIn, latestEdition, toMarkdown } from '../scripts/check_updates.mjs';
import { loadExtras, validateExtras, sectionRefs, handCheck } from '../scripts/related.mjs';

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
  assert.doesNotMatch(aml, /Placeholder, not official text/, 'the AML Act is loaded from the FMU edition');
  assert.match(aml, /id="s-7a"/);
  assert.match(aml, /Schedule I — Predicate offences/, 'AML schedules link to the official PDF');
  const fer = fs.readFileSync(path.join(outDir, 'acts/federal-excise-rules-2005/index.html'), 'utf8');
  assert.match(fer, /id="s-93"/);
  assert.match(fer, /printed as a scanned image in the source edition/, 'image-only rules point to the PDF');
  const fea = fs.readFileSync(path.join(outDir, 'acts/federal-excise-act-2005/index.html'), 'utf8');
  assert.match(fea, /Federal Excise Rules, 2005/, 'the FED Act page lists its Rules');
  const benami = fs.readFileSync(path.join(outDir, 'acts/benami-transactions-act-2017/index.html'), 'utf8');
  assert.match(benami, /data-cite="Section 24 of the Benami Transactions \(Prohibition\) Act, 2017 \(Act No\. V of 2017\)"/);
  assert.match(benami, /Adjudication of Benami property/, 'words in separate font runs keep their spaces');
  const third = fs.readFileSync(path.join(outDir, 'acts/companies-act-2017-third-schedule/index.html'), 'utf8');
  assert.match(third, /<iframe src="\.\.\/\.\.\/sources\/companies-act-2017-third-schedule\.pdf"/, 'PDF-only instruments embed the official PDF');
  assert.ok(acts.every((a) => !a.placeholder), 'no placeholder pages remain');

  assert.ok(index.provisions.some((p) => p.act === 'aml-act-2010' && p.no === '3' && p.text.includes('proceeds of crime')));
  assert.ok(index.provisions.every((p) => !/\{fn:/.test(p.text + p.title)), 'search text has no markers');
  const notes = JSON.parse(fs.readFileSync(path.join(outDir, 'search-notes.json'), 'utf8'));
  assert.ok(notes.some((n) => n.a === 'sales-tax-act-1990' && n.k === 's-3' && /seventeen/.test(n.t)), 'amendment notes are searchable');
  assert.ok(notes.every((n) => n.id && n.t), 'every searchable note links to its place on the page');
  const search = fs.readFileSync(path.join(outDir, 'search.html'), 'utf8');
  assert.match(search, /id="in-text" checked/);
  assert.match(search, /id="in-notes"/);
  assert.match(ito, /id="show-notes"/, 'instrument pages can show all amendment notes');
  const sources = fs.readFileSync(path.join(outDir, 'sources.html'), 'utf8');
  assert.match(sources, /Sources and updates/);
  assert.match(sources, /fbr\.gov\.pk/);
  assert.match(sources, /Checked by hand/);
  assert.match(sources, /evidence\/secp-acts-2026-10-04\.png/);
  assert.ok(fs.existsSync(path.join(outDir, 'evidence', 'secp-acts-2026-10-04.png')));
  const related = fs.readFileSync(path.join(outDir, 'acts', 'companies-act-2017', 'related.html'), 'utf8');
  assert.match(related, /Companies \(Investment in Associated Companies or Associated Undertakings\) Regulations, 2017/);
  assert.match(related, /still to identify/);
  const caPage = fs.readFileSync(path.join(outDir, 'acts', 'companies-act-2017', 'index.html'), 'utf8');
  assert.match(caPage, /Checked on regulator website/);
  const s199 = caPage.slice(caPage.indexOf('id="s-199"'), caPage.indexOf('id="s-200"'));
  assert.match(s199, /prov-related[\s\S]*Investment in Associated Companies/, 'section 199 lists its regulations');
  const sw = fs.readFileSync(path.join(outDir, 'sw.js'), 'utf8');
  assert.doesNotMatch(sw, /search-notes\.json/, 'the notes index is cached on first use, not precached');
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

test('amendment notes are cited by their provision or read as amendment notes', () => {
  // A note no marker cites is kept only when it reads like an amendment note; table and form cells
  // picked up from page bottoms must not appear as notes.
  const amendment = /substitut|insert|omit|add(ed|ition)|renumber|amend|delet|re-?lettered|corrigendum|repeal|S\.?\s?R\.?\s?O|Finance|Ordinance|\bAct\b|Notification|Gazette|PTCL|w\.e\.f/i;
  const { acts } = loadLibrary();
  for (const a of acts) {
    for (const p of a.parts) {
      for (const s of p.sections) {
        const cited = new Set([...(s.title + ' ' + s.text.join(' ')).matchAll(/\{fn:([^}]+)\}/g)].map((m) => m[1]));
        for (const f of s.fn || []) {
          assert.ok(cited.has(f.n) || amendment.test(f.text), `${a.id} ${s.no}: note ${f.n} is neither cited nor an amendment note: ${f.text.slice(0, 60)}`);
        }
      }
    }
  }
  const str = acts.find((a) => a.id === 'sales-tax-rules-2006');
  assert.ok(str.frontNotes.length > 0, 'notes on the enacting notification are kept');
  assert.ok(str.parts.some((p) => (p.fn || []).length), 'notes on chapter headings are kept');
});

test('update check reads edition dates from regulator pages', () => {
  assert.deepEqual(datesIn('Income Tax Ordinance, 2001 Amended upto 30.06.2026'), ['2026-06-30']);
  assert.deepEqual(datesIn('Sales Tax Act 1990 amended upto 30-06-2026'), ['2026-06-30']);
  assert.deepEqual(datesIn('The Sales Tax Rules, 2006 updated upto 31st July, 2026'), ['2026-07-31']);
  assert.deepEqual(datesIn('Insurance Rules 2017- Updated as of March 3, 2025'), ['2025-03-03']);
  assert.deepEqual(datesIn('Anti-Money-Laundering-Act-2010-amended-upto-Sep. 2020.pdf'.replace(/-/g, ' ')), ['2020-09-30']);
  const html = `<a href="/Docs/a.pdf">Customs Act, 1969 as amended up to 30th June, 2025</a>
    <a href="https://download1.fbr.gov.pk/Docs/b.pdf" target="_blank">Customs Act, 1969 as amended up to 30th June, 2026</a>
    <a href="/Docs/c.pdf">Customs Rules, 2001 (Updated Up to 30.06.2027)</a>`;
  const latest = latestEdition(linksIn(html, 'https://www.fbr.gov.pk/categ/customs-act-1969/130'), 'Customs Act');
  assert.equal(latest.date, '2026-06-30');
  assert.equal(latest.url, 'https://download1.fbr.gov.pk/Docs/b.pdf');
  const md = toMarkdown([{ id: 'x', title: 'X Act', edition: '2025-06-30', page: 'https://example.org', status: 'newer', latest }], '2026-10-01');
  assert.match(md, /\*\*1\*\* with a newer edition/);
});


test('related instruments and hand checks', () => {
  const library = loadLibrary();
  const extras = loadExtras();
  assert.deepEqual(validateExtras(library, extras), []);
  assert.deepEqual(sectionRefs('under sub-section (1) of section 512 of the Act'), ['512']);
  assert.deepEqual(sectionRefs('sections 83 and 83A of the Companies Act, 2017'), ['83', '83A']);
  assert.deepEqual(sectionRefs('section 3 of the Ordinance'), []);
  const ca = library.acts.find((a) => a.id === 'companies-act-2017');
  assert.equal(handCheck(ca, extras.checks).status, 'current');
  const old = { ...ca, lastAmended: '2020-01-01' };
  assert.equal(handCheck(old, extras.checks).status, 'newer', 'a listing dated after the edition means a newer edition');
  const bad = structuredClone(extras);
  bad.checks[0].covers['no-such-law'] = { listed: 'x' };
  bad.registers[0].instruments.push({ title: 'X', status: 'in-force', sections: ['9999'] });
  const errors = validateExtras(library, bad);
  assert.ok(errors.some((e) => e.includes('unknown instrument "no-such-law"')));
  assert.ok(errors.some((e) => e.includes('section 9999')));
});
