// Makes data/ai/vectors.bin and data/ai/hashes.json from dist/search-index.json.
// Run after `npm run build` whenever text changes; unchanged passages are reused, so it is quick after the first run.
//   cd tools/ai && npm install && node make_vectors.mjs
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { pipeline } from '@huggingface/transformers';
import { passages, AI_MODEL, AI_DIMS } from '../../scripts/ai_chunks.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const dir = path.join(ROOT, 'data', 'ai');
fs.mkdirSync(dir, { recursive: true });
const index = JSON.parse(fs.readFileSync(path.join(ROOT, 'dist', 'search-index.json'), 'utf8'));
const items = passages(index);

const old = new Map();
if (fs.existsSync(path.join(dir, 'hashes.json'))) {
  const prev = JSON.parse(fs.readFileSync(path.join(dir, 'hashes.json'), 'utf8'));
  const bin = fs.readFileSync(path.join(dir, 'vectors.bin'));
  if (prev.model === AI_MODEL) prev.hashes.forEach((h, i) => old.set(h, bin.subarray(i * AI_DIMS, (i + 1) * AI_DIMS)));
}

const out = Buffer.alloc(items.length * AI_DIMS);
const todo = [];
items.forEach((it, i) => {
  const had = old.get(it.hash);
  if (had) had.copy(out, i * AI_DIMS);
  else todo.push(i);
});
console.log(`${items.length} passages, ${todo.length} to embed`);

if (todo.length) {
  const embed = await pipeline('feature-extraction', AI_MODEL, { dtype: 'q8' });
  const t0 = Date.now();
  for (let b = 0; b < todo.length; b += 16) {
    const batch = todo.slice(b, b + 16);
    const res = await embed(batch.map((i) => items[i].text), { pooling: 'cls', normalize: true });
    batch.forEach((i, j) => {
      for (let d = 0; d < AI_DIMS; d++) {
        out.writeInt8(Math.max(-127, Math.min(127, Math.round(res.data[j * AI_DIMS + d] * 254))), i * AI_DIMS + d);
      }
    });
    if ((b / 16) % 25 === 0) console.log(`${b + batch.length}/${todo.length} in ${Math.round((Date.now() - t0) / 1000)}s`);
  }
}
fs.writeFileSync(path.join(dir, 'vectors.bin'), out);
fs.writeFileSync(path.join(dir, 'hashes.json'), JSON.stringify({ model: AI_MODEL, dims: AI_DIMS, hashes: items.map((i) => i.hash) }));
console.log(`Wrote ${items.length} vectors (${(out.length / 1e6).toFixed(1)} MB)`);
