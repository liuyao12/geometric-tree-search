import assert from 'node:assert/strict';
import { writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { parse, solve, verifyMovie, colorDimension } from '../apps/knot-movie/engine.mjs';
import { trefoilIdentification as pair, braidClosure } from '../apps/knot-movie/cases.mjs';

const source = parse(pair.source), target = parse(pair.target);
assert.notEqual(pair.source, pair.target);
assert.equal(colorDimension(source), 2); assert.equal(colorDimension(target), 2);
assert.throws(() => braidClosure([1, 1], 2), /multiple components/);
const bounds = { depth: pair.depth, crossingCap: pair.crossingCap, stateCap: 1500, nodeCap: 10000, episodes: 12, seed: 31 };
const shorter = [1, 2].map(depth => {
  const r = solve(source, target, { ...bounds, depth, lane: 'gcts' });
  assert.equal(r.status, 'exhausted-finite-search');
  return { depth, status: r.status, states: r.states, tiles: r.tiles };
});
const rows = ['baseline', 'gcts', 'gcts+rl'].map(lane => {
  const r = solve(source, target, { ...bounds, lane });
  assert.equal(r.status, 'equivalent'); assert(verifyMovie(r.certificate));
  assert.equal(r.certificate.steps.length, 3);
  assert.deepEqual(new Set(r.certificate.steps.map(s => s.kind)), new Set(['III', 'II−', 'I−']));
  return { lane, ...r };
});
const verifier = fileURLToPath(new URL('../research/knot-classifier/verify_movie.py', import.meta.url));
const replay = spawnSync('python3', [verifier, '-'], { input: JSON.stringify(rows.map(r => r.certificate)), encoding: 'utf8' });
assert.equal(replay.status, 0, replay.stderr);
const corrupted = structuredClone(rows[0].certificate); corrupted.steps[0].kind = 'I−';
assert.notEqual(spawnSync('python3', [verifier, '-'], { input: JSON.stringify(corrupted), encoding: 'utf8' }).status, 0);
const evidence = { case: pair, provenance: { sourceBraid: [1, 1, 2, 1, 2, -1], sourceStrands: 3, targetBraid: [1, 1, 1], targetStrands: 2 }, bounds, shorter, rows, independentReplay: JSON.parse(replay.stdout), corruptedTileRejected: true };
const dest = new URL('../research/knot-classifier/', import.meta.url);
writeFileSync(new URL('trefoil-identification.json', dest), JSON.stringify(evidence, null, 2) + '\n');
writeFileSync(new URL('trefoil-movie.json', dest), JSON.stringify(rows[2].certificate, null, 2) + '\n');
const escape = s => String(s).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
const cert = rows[2].certificate;
const diagrams = [{ kind: 'Source', after: cert.source }, ...cert.steps];
const counts = diagrams.map(s => parse(s.after).length / 2);
writeFileSync(new URL('trefoil-identification.html', dest), String.raw`<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Trefoil identification · GCTS</title>
<script>window.MathJax={tex:{inlineMath:[['\\(','\\)']],displayMath:[['\\[','\\]']]}};</script><script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
<style>body{font:17px/1.65 system-ui,sans-serif;background:#102029;color:#eee9df;max-width:1000px;margin:40px auto;padding:24px}a{color:#a7e7bd}h1,h2{line-height:1.2}code,pre{font:14px/1.6 monospace;overflow-wrap:anywhere}pre{white-space:pre-wrap;background:#223642;padding:16px;border-radius:8px}table{border-collapse:collapse;width:100%;font-size:15px}td,th{padding:10px;text-align:left;border-bottom:1px solid #456}article{border-left:3px solid #a7e7bd;padding-left:20px;margin:24px 0}.scroll{overflow:auto}</style></head><body>
<a href="../../apps/knot-movie/?example=identification">Open this pair in the live tile lab ↗</a><h1>A trefoil recognized in three moves</h1>
<p>The search identifies a six-crossing diagram with the standard three-crossing trefoil. The diagrams are specified independently as braid closures; the solver receives their signed Gauss words and bounds, with no reference move sequence.</p>
<h2>Why these endpoints are known to agree</h2>
<p>The source is the closure of the three-strand braid \(\sigma_1(\sigma_1\sigma_2)^2\sigma_1^{-1}\). Conjugation preserves the closure. The braid relation gives
\[(\sigma_1\sigma_2)^2=\sigma_1(\sigma_2\sigma_1\sigma_2)=\sigma_1^2\sigma_2\sigma_1.\]
Cyclic conjugation gives \(\sigma_1^3\sigma_2\), whose Markov destabilization is the two-strand braid \(\sigma_1^3\), the target trefoil. See <a href="https://sschleimer.warwick.ac.uk/Teach/2010_MA3F2/2009final_exam.pdf">Schleimer's braid and Markov definitions</a> and <a href="https://www.maths.ed.ac.uk/~v1ranick/slides/bloom3.pdf">Ranicki's trefoil braid example</a>. Both endpoints also have Fox coloring dimension \(2\) over \(\mathbb F_3\), whereas the unknot has dimension \(1\).</p>
<h2>The sequence found by the RL lane</h2><p>Crossing labels are canonicalized at each seam. Thus the same number in consecutive words need not name the same physical crossing. Words specify planar signed ribbon diagrams; the lab's connecting curves are schematic.</p>
${diagrams.map((s,i) => `<article><h3>${i ? `Move ${i}: type ${escape(s.kind)}` : 'Source diagram'} · ${counts[i]} crossings</h3><pre>${escape(s.after)}</pre></article>`).join('\n')}
<p><a href="trefoil-movie.json">Download the independently verified movie certificate</a> · <a href="trefoil-identification.json">Full machine-readable evidence</a></p>
<h2>Bounded search evidence</h2><p>All legal base moves up to crossing cap \(6\) are catalogued, with identity padding. Depths \(1\) and \(2\) exhaust without a solution; depth \(3\) succeeds. The certificate is therefore shortest within these bounds. The successful catalog has \(354\) layer-state entries and \(627\) candidate tiles.</p>
<div class="scroll"><table><thead><tr><th>Lane</th><th>Nodes</th><th>Peak incidences</th><th>Catalog ms</th><th>Learning ms</th><th>RL training ms</th><th>Search ms</th><th>Total ms</th></tr></thead><tbody>
${rows.map(r => `<tr><td>${escape(r.lane)}</td><td>${r.stats.nodes}</td><td>${r.stats.peakIncidences}</td>${['catalogMs','learningMs','trainingMs','searchMs','totalMs'].map(k=>`<td>${r[k].toFixed(2)}</td>`).join('')}</tr>`).join('\n')}
</tbody></table></div>
<p>These are single-run timings, including cold synthetic RL training. The failure markings eliminate \(346\) bounded seam states. Peak live incidences fall from \(49\) to \(11\), but node count stays at \(3\). RL selects a different valid move order and costs more time on this small example; this does not establish an RL speedup.</p>
<h2>Verification and algorithm scope</h2><p>The JavaScript move enumerator replays every tile. A separate Python implementation independently checks all three lane certificates, including planar face conditions and endpoints. Changing a type-III tile into a type-I deletion is rejected. The shared point engine is unchanged: full bipartite bookkeeping, global dead-end checks, global forced moves, generation scheduling, and exact rollback use the existing conformance-tested implementation.</p>
<p>Failure guards are proved only for this target, time horizon, and crossing cap. Their synthesis remains the specialized exhaustive seam-reachability control described in the <a href="plan.html">research plan</a>. This test advances the positive-equivalence benchmark; local geometric marking synthesis and collision-free spatial lifts remain open subgoals.</p>
<h2>Reproduce</h2><pre>node scripts/test-trefoil-identification.mjs
python3 research/knot-classifier/verify_movie.py research/knot-classifier/trefoil-movie.json</pre>
</body></html>`);
console.log(JSON.stringify({ passed: true, shorter, lanes: rows.map(r => ({ lane: r.lane, sequence: r.certificate.steps.map(s => s.kind), stats: r.stats, totalMs: r.totalMs })), independentReplay: evidence.independentReplay }, null, 2));
