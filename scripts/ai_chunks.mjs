// Splits provisions into passages for search by meaning. Shared by the vector maker
// (tools/ai/make_vectors.mjs) and the site build, so both always agree on what a passage is.
import crypto from 'node:crypto';

export const AI_MODEL = 'Xenova/bge-small-en-v1.5';
export const AI_DIMS = 384;
const MAX_CHARS = 1200;

// Offsets into the text: [start, length]. Whole paragraphs where possible, at a sentence or word end otherwise.
export function splitText(text) {
  if (text.length <= MAX_CHARS) return [[0, text.length]];
  const out = [];
  let start = 0;
  while (text.length - start > MAX_CHARS) {
    const win = text.slice(start, start + MAX_CHARS);
    let cut = win.lastIndexOf('\n');
    if (cut < MAX_CHARS / 2) cut = Math.max(win.lastIndexOf('. '), win.lastIndexOf('; '));
    if (cut < MAX_CHARS / 2) cut = win.lastIndexOf(' ');
    if (cut < 1) cut = MAX_CHARS - 1;
    out.push([start, cut + 1]);
    start += cut + 1;
  }
  out.push([start, text.length - start]);
  return out;
}

// What the model reads: where the passage sits, then the passage.
export function passageText(act, p, start, len) {
  const where = p.no ? `${act.unit} ${p.no}${p.title ? ` ${p.title}` : ''}` : p.title;
  return `${act.title}. ${where}.\n${p.text.slice(start, start + len)}`;
}

// Every passage of a built search index, with a key that changes when the wording changes.
export function passages(index) {
  const acts = new Map(index.acts.map((a) => [a.id, a]));
  const out = [];
  index.provisions.forEach((p, prov) => {
    const act = acts.get(p.act);
    if (!act || act.placeholder) return;
    for (const [start, len] of splitText(p.text || '')) {
      const text = passageText(act, p, start, len);
      const hash = crypto.createHash('sha1').update(AI_MODEL).update(text).digest('hex').slice(0, 16);
      out.push({ prov, start, len, text, hash });
    }
  });
  return out;
}
