// Shared helpers for loading, validating and formatting the legal library.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const DATA_DIR = path.join(ROOT, 'data');

export const INSTRUMENT_TYPES = ['act', 'ordinance', 'rules', 'regulations', 'order', 'notification', 'schedule'];
export const STATUSES = ['in-force', 'repealed', 'partly-in-force', 'not-yet-in-force'];
export const VERIFICATION = ['verified', 'unverified'];

const TYPE_LABELS = {
  act: 'Act',
  ordinance: 'Ordinance',
  rules: 'Rules',
  regulations: 'Regulations',
  order: 'Order',
  notification: 'Notification',
  schedule: 'Schedule',
};

export function typeLabel(type) {
  return TYPE_LABELS[type] || type;
}

export function loadLibrary(dataDir = DATA_DIR) {
  const catalog = JSON.parse(fs.readFileSync(path.join(dataDir, 'catalog.json'), 'utf8'));
  const actsDir = path.join(dataDir, 'acts');
  const acts = fs
    .readdirSync(actsDir)
    .filter((f) => f.endsWith('.json'))
    .sort()
    .map((f) => {
      const act = JSON.parse(fs.readFileSync(path.join(actsDir, f), 'utf8'));
      act._file = f;
      return act;
    });
  return { catalog, acts };
}

// Returns a list of human-readable problems; empty means the library is valid.
export function validateLibrary({ catalog, acts }, dataDir = DATA_DIR) {
  const errors = [];
  const categoryIds = new Set((catalog.categories || []).map((c) => c.id));
  const ids = new Set();

  for (const act of acts) {
    const where = act._file || act.id || '(unknown)';
    for (const key of ['id', 'title', 'type', 'unit', 'categories', 'status', 'source', 'verification', 'parts']) {
      if (act[key] === undefined || act[key] === null || act[key] === '') errors.push(`${where}: missing "${key}"`);
    }
    if (typeof act.number !== 'string') errors.push(`${where}: "number" must be a string (use "" when the source gives none)`);
    if (act.sourcePdf && !fs.existsSync(path.join(dataDir, '..', 'sources', 'pdf', act.sourcePdf))) {
      errors.push(`${where}: sourcePdf "${act.sourcePdf}" not found in sources/pdf/`);
    }
    if (!act.pdfOnly && Array.isArray(act.parts) && act.parts.length === 0) errors.push(`${where}: no parts (set "pdfOnly": true for PDF-only items)`);
    if (act.id && !/^[a-z0-9]+(-[a-z0-9]+)*$/.test(act.id)) errors.push(`${where}: id "${act.id}" must be lowercase-kebab-case`);
    if (act._file && act.id && act._file !== `${act.id}.json`) errors.push(`${where}: file name must be "${act.id}.json"`);
    if (ids.has(act.id)) errors.push(`${where}: duplicate id "${act.id}"`);
    ids.add(act.id);
    if (act.type && !INSTRUMENT_TYPES.includes(act.type)) errors.push(`${where}: unknown type "${act.type}"`);
    if (act.status && !STATUSES.includes(act.status)) errors.push(`${where}: unknown status "${act.status}"`);
    if (act.verification && !VERIFICATION.includes(act.verification.status)) {
      errors.push(`${where}: verification.status must be one of ${VERIFICATION.join(', ')}`);
    }
    if (act.verification?.status === 'verified') {
      for (const key of ['verifiedBy', 'verifiedOn', 'against']) {
        if (!act.verification[key]) errors.push(`${where}: verified instruments need verification.${key}`);
      }
    }
    for (const c of act.categories || []) {
      if (!categoryIds.has(c)) errors.push(`${where}: unknown category "${c}"`);
    }
    for (const key of ['enacted', 'lastAmended']) {
      if (act[key] && !/^\d{4}-\d{2}-\d{2}$/.test(act[key])) errors.push(`${where}: ${key} must be YYYY-MM-DD`);
    }

    const numbers = new Set();
    for (const part of act.parts || []) {
      if (!part.heading) errors.push(`${where}: a part is missing "heading"`);
      for (const sec of part.sections || []) {
        if (!sec.no) errors.push(`${where}: a provision is missing "no"`);
        if (typeof sec.title !== 'string') errors.push(`${where}: provision ${sec.no} is missing "title"`);
        for (const fn of sec.fn || []) {
          if (!fn.n || typeof fn.text !== 'string') errors.push(`${where}: provision ${sec.no} has a malformed footnote`);
        }
        if (!Array.isArray(sec.text) || sec.text.length === 0) errors.push(`${where}: provision ${sec.no} has no text`);
        if (numbers.has(sec.no)) errors.push(`${where}: duplicate provision number "${sec.no}"`);
        numbers.add(sec.no);
      }
    }
  }

  for (const act of acts) {
    if (act.parent && !ids.has(act.parent)) errors.push(`${act._file}: parent "${act.parent}" does not exist`);
  }
  return errors;
}

export function provisionAnchor(no) {
  return `s-${String(no).toLowerCase().replace(/[^a-z0-9]+/g, '-')}`;
}

// "Section 111 of the Income Tax Ordinance, 2001 (Ordinance No. XLIX of 2001)"
export function citation(act, no, section) {
  if (section && section.cite) return section.cite;
  const num = act.number && !/^updated/i.test(act.number) ? ` (${act.number})` : '';
  return `${act.unit} ${displayNo(no)} of the ${act.title}${num}`;
}

// Duplicate numbers get a suffix ("12-2") for uniqueness; readers see the printed number.
export function displayNo(no) {
  return String(no).replace(/-\d+$/, '');
}

export const FN_RE = /\{fn:([^}]+)\}/g;

export function stripMarkers(s) {
  return String(s).replace(FN_RE, '').replace(/[ \t]{2,}/g, ' ').trim();
}

// Footnote keys are "<page>-<number>" (or "n<block>-<number>" for endnotes); readers see the number.
export function fnLabel(key) {
  return String(key).replace(/^[^-]+-/, '');
}

export function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// Paragraph strings may start with ">" markers to indent clauses: ">(a) ..." or ">>(i) ...".
export function parseParagraph(p) {
  const m = /^(>*)\s*/.exec(p);
  return { level: Math.min(m[1].length, 3), text: p.slice(m[0].length) };
}

export function plainText(section) {
  return section.text.map((p) => stripMarkers(parseParagraph(p).text)).join('\n');
}
