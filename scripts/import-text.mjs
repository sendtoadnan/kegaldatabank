// Converts the plain text of a statute (copied from an official PDF) into a draft JSON instrument.
//
//   npm run import -- path/to/act.txt --id companies-act-2017 --title "Companies Act, 2017" \
//     --number "Act No. XIX of 2017" --type act --category corporate > data/acts/companies-act-2017.json
//
// Recognises "PART I" / "CHAPTER II" headings and provisions written as
// "12. Heading.—(1) Text..." (em dash, en dash or hyphens). Always proof-read the output.
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

const HEADING = /^(PART|CHAPTER)\s+([IVXLC]+|\d+[A-Z]?)\b\.?\s*[—–-]*\s*(.*)$/i;
const PROVISION = /^(\d+[A-Z]{0,2})\.\s+(.+?)\.?\s*(?:—|–|--|-\s)\s*(.*)$/;
const ROMAN = /^\((?:i|ii|iii|iv|v|vi|vii|viii|ix|x|xi|xii|xiii|xiv|xv|xvi|xvii|xviii|xix|xx)\)/;
const LETTER = /^\([a-z]{1,2}\)/;
const SUBSECTION = /^\(\d+[A-Z]?\)/;

function titleCase(s) {
  return s.toLowerCase().replace(/\b([a-z])/g, (c) => c.toUpperCase());
}

// Picks the indent marker for a clause, treating "(i)" as a letter when it follows "(h)".
function indent(line, state) {
  if (SUBSECTION.test(line)) return '';
  const isRoman = ROMAN.test(line);
  const isLetter = LETTER.test(line);
  if (isRoman && !(line.startsWith('(i)') && state.lastLetter === 'h') && !(line.startsWith('(v)') && state.lastLetter === 'u') && !(line.startsWith('(x)') && state.lastLetter === 'w')) {
    return '>>';
  }
  if (isLetter) {
    state.lastLetter = line.slice(1, line.indexOf(')'));
    return '>';
  }
  return null;
}

export function parseStatute(text, meta = {}) {
  const lines = text.replace(/\r/g, '').split('\n').map((l) => l.trim()).filter(Boolean);
  const parts = [];
  let part = null;
  let section = null;
  const state = { lastLetter: null };

  const ensurePart = () => {
    if (!part) {
      part = { heading: 'Preliminary', sections: [] };
      parts.push(part);
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const h = HEADING.exec(line);
    if (h) {
      let name = h[3];
      if (!name && lines[i + 1] && lines[i + 1] === lines[i + 1].toUpperCase() && !PROVISION.test(lines[i + 1])) name = lines[++i];
      part = { heading: `${titleCase(h[1])} ${h[2].toUpperCase()}${name ? ' — ' + titleCase(name) : ''}`, sections: [] };
      parts.push(part);
      section = null;
      continue;
    }
    const p = PROVISION.exec(line);
    if (p) {
      ensurePart();
      state.lastLetter = null;
      section = { no: p[1], title: p[2].replace(/\.$/, ''), text: [] };
      if (p[3]) section.text.push(p[3]);
      part.sections.push(section);
      continue;
    }
    if (!section) continue; // preamble or front matter
    const marker = indent(line, state);
    if (marker === null && section.text.length) {
      // Continuation of a wrapped line from the PDF.
      section.text[section.text.length - 1] += ' ' + line;
    } else {
      section.text.push((marker || '') + line);
    }
  }

  return {
    id: meta.id || 'new-instrument',
    title: meta.title || 'Untitled',
    number: meta.number || '',
    type: meta.type || 'act',
    unit: meta.unit || (meta.type === 'rules' ? 'Rule' : meta.type === 'regulations' ? 'Regulation' : 'Section'),
    ...(meta.parent ? { parent: meta.parent } : {}),
    categories: meta.category ? [meta.category] : [],
    aliases: [],
    enacted: null,
    lastAmended: null,
    status: 'in-force',
    source: { name: meta.sourceName || '', url: meta.sourceUrl || '' },
    verification: { status: 'unverified', note: 'Imported automatically; proof-read against the Gazette before marking verified.' },
    preamble: '',
    parts,
  };
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  const file = args.find((a) => !a.startsWith('--') && !args[args.indexOf(a) - 1]?.startsWith('--'));
  if (!file) {
    console.error('Usage: npm run import -- <file.txt> [--id x] [--title x] [--number x] [--type act|rules|...] [--category x] [--parent x]');
    process.exit(1);
  }
  const meta = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith('--')) meta[args[i].slice(2).replace(/-([a-z])/g, (_, c) => c.toUpperCase())] = args[++i];
  }
  process.stdout.write(JSON.stringify(parseStatute(fs.readFileSync(file, 'utf8'), meta), null, 2) + '\n');
}
