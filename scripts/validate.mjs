// Checks every instrument in data/ against the content rules. Exits non-zero on problems.
import { loadLibrary, validateLibrary } from './lib.mjs';
import { loadExtras, validateExtras } from './related.mjs';

const library = loadLibrary();
const errors = [...validateLibrary(library), ...validateExtras(library, loadExtras())];
if (errors.length) {
  console.error(`Found ${errors.length} problem(s):`);
  for (const e of errors) console.error(`  - ${e}`);
  process.exit(1);
}
const provisions = library.acts.reduce((n, a) => n + a.parts.reduce((m, p) => m + p.sections.length, 0), 0);
console.log(`OK: ${library.acts.length} instruments, ${provisions} provisions.`);
