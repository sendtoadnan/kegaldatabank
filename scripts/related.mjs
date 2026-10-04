// Hand checks of regulator websites (data/manual-checks.json) and registers of the instruments
// made under an Act (data/related/<act id>.json).
import fs from 'node:fs';
import path from 'node:path';
import { DATA_DIR, ROOT, plainText } from './lib.mjs';
import { datesIn } from './check_updates.mjs';

export const EVIDENCE_DIR = path.join(ROOT, 'sources', 'evidence');

export function loadExtras(dataDir = DATA_DIR) {
  const checksPath = path.join(dataDir, 'manual-checks.json');
  const checks = fs.existsSync(checksPath) ? JSON.parse(fs.readFileSync(checksPath, 'utf8')).checks : [];
  const relatedDir = path.join(dataDir, 'related');
  const registers = fs.existsSync(relatedDir)
    ? fs.readdirSync(relatedDir).filter((f) => f.endsWith('.json')).sort().map((f) => ({ ...JSON.parse(fs.readFileSync(path.join(relatedDir, f), 'utf8')), _file: f }))
    : [];
  return { checks, registers };
}

export function validateExtras({ acts }, { checks, registers }, evidenceDir = EVIDENCE_DIR) {
  const errors = [];
  const byId = new Map(acts.map((a) => [a.id, a]));
  for (const c of checks) {
    const where = `manual-checks.json (${c.page} on ${c.date})`;
    if (!/^\d{4}-\d\d-\d\d$/.test(c.date || '')) errors.push(`${where}: date must be YYYY-MM-DD`);
    if (!/^https:\/\//.test(c.page || '')) errors.push(`${where}: page must be an https URL`);
    if (!c.screenshot || !fs.existsSync(path.join(evidenceDir, c.screenshot))) errors.push(`${where}: screenshot "${c.screenshot}" not found in sources/evidence/`);
    for (const [id, entry] of Object.entries(c.covers || {})) {
      if (!byId.has(id)) errors.push(`${where}: unknown instrument "${id}"`);
      if (!entry.listed) errors.push(`${where}: "${id}" needs the "listed" title`);
      if (entry.status && !['current', 'newer'].includes(entry.status)) errors.push(`${where}: "${id}" status must be current or newer`);
    }
  }
  for (const r of registers) {
    const where = `related/${r._file}`;
    const act = byId.get(r.act);
    if (!act) {
      errors.push(`${where}: unknown act "${r.act}"`);
      continue;
    }
    const nos = new Set(act.parts.flatMap((p) => p.sections.map((s) => s.no)));
    for (const i of r.instruments || []) {
      if (!i.title) errors.push(`${where}: an instrument has no title`);
      if (!['in-force', 'repealed'].includes(i.status)) errors.push(`${where}: "${i.title}" status must be in-force or repealed`);
      for (const k of ['library', 'replacedBy']) if (i[k] && !byId.has(i[k])) errors.push(`${where}: "${i.title}" ${k} "${i[k]}" is not in the library`);
      for (const s of i.sections || []) if (!nos.has(s)) errors.push(`${where}: "${i.title}" cites section ${s}, which the Act does not have`);
      if (i.secpPage && !r.secpPages?.[i.secpPage]) errors.push(`${where}: "${i.title}" secpPage "${i.secpPage}" is not listed in secpPages`);
      if (i.url && !/^https:\/\//.test(i.url)) errors.push(`${where}: "${i.title}" url must be https`);
      if (i.found && !['search-index', 'screenshot', 'instrument'].includes(i.found.how)) errors.push(`${where}: "${i.title}" found.how must be search-index, screenshot or instrument`);
      if (i.seen?.screenshot && !fs.existsSync(path.join(evidenceDir, i.seen.screenshot))) errors.push(`${where}: "${i.title}" screenshot "${i.seen.screenshot}" not found`);
    }
  }
  return errors;
}

/** Section numbers in phrases such as "section 199 of the Act" or "sections 83 and 83A of the Act". */
export function sectionRefs(text) {
  const out = [];
  const re = /\bsections?\s+(\d+[A-Z]{0,2}(?:\s*(?:,|and|or|to)\s*\d+[A-Z]{0,2})*)\s+of\s+the\s+(?:Companies\s+)?Act\b/g;
  for (const m of text.replace(/\s+/g, ' ').matchAll(re)) out.push(...m[1].match(/\d+[A-Z]{0,2}/g));
  return out;
}

/** For each section of `act`, the provisions of instruments made under it that cite that section. */
export function citedSections(act, kids) {
  const nos = new Set(act.parts.flatMap((p) => p.sections.map((s) => s.no)));
  const map = new Map();
  for (const kid of kids) {
    for (const p of kid.parts) {
      for (const s of p.sections) {
        for (const no of new Set(sectionRefs(plainText(s)))) {
          if (!nos.has(no)) continue;
          if (!map.has(no)) map.set(no, new Map());
          const byKid = map.get(no);
          if (!byKid.has(kid.id)) byKid.set(kid.id, { kid, provisions: [] });
          byKid.get(kid.id).provisions.push(s.no);
        }
      }
    }
  }
  return map;
}

/** Words in a section that leave details to rules, regulations or the Commission. */
export function delegation(section) {
  const t = plainText(section).replace(/\s+/g, ' ');
  const m = t.match(/[^.;:]{0,70}\b(?:as may be specified|as may be prescribed|specified by the Commission|regulations specified|prescribed (?:through|by) rules|make (?:such )?regulations|make rules|as may be notified)\b[^.;:]{0,40}/i);
  return m ? m[0].trim() : null;
}

/** The newest hand check covering an instrument, with the status it shows. */
export function handCheck(act, checks) {
  const found = checks
    .filter((c) => c.covers?.[act.id])
    .sort((a, b) => b.date.localeCompare(a.date))[0];
  if (!found) return null;
  const entry = found.covers[act.id];
  const edition = act.lastAmended || act.enacted || null;
  let status = entry.status;
  if (!status) {
    const listed = datesIn(entry.listed).sort().pop();
    status = listed && edition && listed > edition ? 'newer' : 'current';
  }
  return { ...found, entry, status };
}
