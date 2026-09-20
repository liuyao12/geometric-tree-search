// Run the existing geometry-free engine without changing its scheduler.
import fs from 'node:fs';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
const [poolPath, kernelPath, out, mode] = process.argv.slice(2);
const pool = JSON.parse(fs.readFileSync(poolPath, 'utf8'));
const { PointSearch, verify } = await import(pathToFileURL(kernelPath));
const hash = p => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const rows = [];
for (const frame of pool.frames) for (const marked of mode === 'marked-only' ? [true] : [false, true]) {
  if (!frame.complete) {
    rows.push({ configuration: frame.configuration, marked, status: 'unknown-proposal-domain', selected: [], stats: null });
    continue;
  }
  const model = { capacity: frame.capacity, required: frame.required, complete: true,
    candidates: frame.candidates.map(c => ({ ...c, m: marked ? c.m : [] })) };
  const search = new PointSearch(model);
  const trace = [];
  let event;
  for (let steps = 0; steps < 100000; steps++) {
    search.auditGraph();
    event = search.advance();
    trace.push(event);
    if (['complete', 'exhausted', 'unknown'].includes(event.kind)) break;
  }
  search.auditGraph();
  const selected = [...search.placed.keys()];
  const obligations = [...new Set([...model.required, ...selected.flatMap(id => search.candidates.get(id).t.map(t => t.point))])];
  const checked = verify(model, selected, obligations);
  if (event.kind === 'complete' && !checked.complete) throw Error('False completion');
  rows.push({ configuration: frame.configuration, marked,
    status: event.kind === 'complete' ? 'verified-finite-point-model' :
      event.kind === 'exhausted' ? 'exhausted-declared-finite-pool' : 'unknown-budget-or-domain',
    selected, stats: search.stats, trace, verification: checked });
}
const result = { poolHash: hash(poolPath), kernelHash: hash(kernelPath), runnerHash: hash(process.argv[1]), rows,
  limits: 'Reference engine on a target-conditioned finite pool. Markings are enclosing scalar intervals, not Euclidean balls; positive marked results require independent ball replay. Source latent points derive from prior successful assemblies. No blind growth, continuous completeness or performance claim. All points are generation-zero finite-target roots.' };
fs.writeFileSync(out, JSON.stringify(result, null, 2), { flag: 'wx' });
console.log(JSON.stringify(rows.map(({ configuration, marked, status, selected, stats }) => ({ configuration, marked, status, selected, stats }))));
