// Search by meaning. Runs on the reader's own device, in a background thread: the model and
// library code download once from public hosts, and nothing the reader types leaves the device.
import { pipeline, env } from 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@4.3.2/dist/transformers.min.js';

const EMBED_MODEL = 'Xenova/bge-small-en-v1.5';
const EMBED_REVISION = 'ea104dacec62c0de699686887e3f920caeb4f3e3';
const QUERY_PREFIX = 'Represent this sentence for searching relevant passages: ';
const MIN_SCORE = 0.6;
env.allowLocalModels = false;

let embedder;
function loadEmbedder() {
  embedder = embedder || pipeline('feature-extraction', EMBED_MODEL, {
    revision: EMBED_REVISION,
    dtype: 'q8',
    device: 'wasm',
    progress_callback: (p) => {
      if (p.status === 'progress' && p.total > 1e6) postMessage({ type: 'progress', loaded: p.loaded, total: p.total });
    },
  });
  return embedder;
}

let library;
function loadLibrary(base) {
  library = library || Promise.all([
    fetch(base + 'ai-passages.json').then((r) => { if (!r.ok) throw new Error('passages'); return r.json(); }),
    fetch(base + 'ai-vectors.bin').then((r) => { if (!r.ok) throw new Error('vectors'); return r.arrayBuffer(); }),
  ]).then(([meta, buf]) => ({ meta, vec: new Int8Array(buf) }));
  return library;
}

// The best passage of each provision, closest first.
async function search(q, base, limit) {
  const [embed, { meta, vec }] = await Promise.all([loadEmbedder(), loadLibrary(base)]);
  const out = await embed(QUERY_PREFIX + q, { pooling: 'cls', normalize: true });
  const q8 = out.data;
  const dims = meta.dims;
  const n = meta.prov.length;
  const best = new Map();
  for (let i = 0; i < n; i++) {
    let dot = 0;
    const at = i * dims;
    for (let d = 0; d < dims; d++) dot += q8[d] * vec[at + d];
    const score = dot / 254;
    if (score < MIN_SCORE) continue;
    const had = best.get(meta.prov[i]);
    if (!had || score > had.score) best.set(meta.prov[i], { prov: meta.prov[i], start: meta.start[i], len: meta.len[i], score });
  }
  return [...best.values()].sort((a, b) => b.score - a.score).slice(0, limit);
}

self.onmessage = async ({ data }) => {
  try {
    if (data.type === 'search') {
      postMessage({ type: 'results', id: data.id, hits: await search(data.q, data.base, data.limit || 60) });
    }
  } catch (err) {
    postMessage({ type: 'error', id: data.id, message: String((err && err.message) || err) });
  }
};
