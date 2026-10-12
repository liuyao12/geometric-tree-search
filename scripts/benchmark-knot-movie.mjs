import { writeFileSync } from 'node:fs';
import { parse, solve, examples, canonical } from '../apps/knot-movie/engine.mjs';
const rows = [], certificates = [];
for (const [name, text] of Object.entries({ curl: examples.curl, bigon: examples.bigon, doubleCurl: 'O1+ U1+ O2- U2-', trefoil: examples.trefoil }))
  for (const lane of ['baseline', 'gcts', 'gcts+rl']) {
    const r = solve(parse(text), [], { lane, depth: 2, crossingCap: 3, stateCap: 1500, episodes: 12, seed: 31 });
    rows.push({ name, lane, status: r.status, knotEquivalence: r.knotEquivalence, states: r.states, tiles: r.tiles,
      failures: r.learnedFailures, stats: r.stats, catalogMs: r.catalogMs, learningMs: r.learningMs, trainingMs: r.trainingMs, searchMs: r.searchMs, totalMs: r.totalMs });
    if (r.certificate) certificates.push(r.certificate);
  }
console.log(JSON.stringify({ version: 'reidemeister-seams-v1', cold: true, training: 'fresh synthetic scrambles; all legal move types; tabular Q features', evaluation: 'explicit curl/bigon controls, not a held-out corpus', rows }, null, 2));
const output = process.argv.find(x => x.startsWith('--certificates='));
if (output) writeFileSync(output.slice('--certificates='.length), JSON.stringify(certificates, null, 2));
