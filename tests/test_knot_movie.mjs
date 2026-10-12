import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { parse, canonical, topology, moves, catalog, learnSeamMarkings, pointSearch, solve, verifyMovie, colorDimension, examples, ClusterPolicy } from '../apps/knot-movie/engine.mjs';
import { latticeLoop, gridLoop, regularProjection, project } from '../apps/knot-movie/projection.mjs';
assert.throws(() => parse('O1+ U1-'));
assert.throws(() => parse('O1+ O2- U1+ U2-'), /not a planar/);
for (const text of Object.values(examples)) {
  const w = parse(text); assert.equal(topology(w).genus, 0);
  assert.equal(canonical(w), canonical([...w].reverse()));
  assert.equal(canonical(w), canonical([...w.slice(1), w[0]].filter(Boolean)));
  assert.equal(canonical(w), canonical(w.map(x => ({ ...x, id: x.id + 19 }))));
}
assert.equal(colorDimension(parse(examples.trefoil)), 2);
assert.equal(colorDimension(parse(examples.curl)), 1);
assert.notEqual(canonical(parse(examples.trefoil)), canonical(parse(examples.trefoil).map(x => ({ ...x, sign: -x.sign }))));
let pool = new Map([['', []]]), checkedMoves = 0, triangles = 0;
const independentCertificates = [];
for (let round = 0; round < 3; round++) {
  const next = new Map(pool);
  for (const w of pool.values()) for (const m of moves(w, 4)) {
    assert.equal(colorDimension(m.after), colorDimension(w), m.kind);
    const inverse = { 'I+': 'I−', 'I−': 'I+', 'II+': 'II−', 'II−': 'II+', III: 'III' }[m.kind];
    assert(moves(m.after, 4).some(x => x.kind === inverse && x.key === canonical(w)), `Missing inverse ${m.kind}: ${canonical(w)} -> ${m.key}`);
    checkedMoves++; if (m.kind === 'III') triangles++;
    independentCertificates.push({ version: 'reidemeister-seams-v1', source: canonical(w), target: m.key, crossingCap: 4, steps: [{ kind: m.kind, after: m.key }] });
    next.set(m.key, m.after);
  }
  pool = next;
}
assert(triangles > 0, 'Exercise actual triangular Reidemeister tiles.');
const replay = spawnSync('python3', [fileURLToPath(new URL('../research/knot-classifier/verify_movie.py', import.meta.url)), '-'], { input: JSON.stringify(independentCertificates), encoding: 'utf8' });
assert.equal(replay.status, 0, replay.stderr);
assert.equal(JSON.parse(replay.stdout).length, checkedMoves);
// Independent brute-force path recursion, no point engine or learned guards.
function reachable(w, target, depth, cap) {
  if (canonical(w) === canonical(target)) return true;
  if (!depth) return false;
  return moves(w, cap).some(m => reachable(m.after, target, depth - 1, cap));
}
for (const text of [examples.curl, examples.bigon, 'O1+ U1+ O2- U2-']) for (const depth of [1, 2]) {
  const w = parse(text), cat = catalog(w, [], { depth, crossingCap: 3 }); assert(cat.complete);
  const learned = learnSeamMarkings(cat), a = pointSearch(cat), b = pointSearch(cat, { learned });
  assert.equal(a.status, b.status); assert.equal(a.status === 'equivalent', reachable(w, [], depth, 3));
  // Every excluded seam-state really has no bounded completion.
  for (const f of learned.failures) assert.equal(reachable(parse(f.state), [], depth - f.time, 3), false);
  assert.deepEqual(pointSearch(cat).selected, a.selected, 'Failed branches/learned runs must not mutate the catalog.');
}
assert.equal(solve(parse(examples.curl), [], { depth: 2, crossingCap: 3, stateCap: 1 }).status, 'unknown');
const cat = catalog(parse('O1+ U1+ O2- U2-'), [], { depth: 1, crossingCap: 2 });
assert.equal(pointSearch(cat, { nodeCap: 0 }).status, 'unknown');
assert.equal(solve(parse(examples.trefoil)).status, 'inequivalent');
for (const lane of ['baseline', 'gcts', 'gcts+rl']) {
  const result = solve(parse(examples.curl), [], { lane, depth: 2, crossingCap: 3, episodes: 4 });
  assert.equal(result.status, 'equivalent'); assert(verifyMovie(result.certificate));
  const bad = structuredClone(result.certificate); bad.steps[0].after = examples.trefoil; assert.throws(() => verifyMovie(bad));
}
const policy = new ClusterPolicy(); policy.train(4); const cluster = policy.propose(parse(examples.bigon), 3); assert(cluster.length);
const fixture = tiles => ({ depth: 2, sourceKey: '', targetKey: '', tiles });
const tile = (id, contributions, markings = []) => ({ id, t: new Map(contributions), m: new Map(markings) });
// A distant dead point must outrank a local singleton.
const dead = pointSearch(fixture([tile(0, [[0, 1]])]));
assert.equal(dead.status, 'exhausted-finite-search'); assert.equal(dead.stats.forced, 0);
// One shared candidate, fractional residuals, and mark-only dependencies.
const shared = pointSearch(fixture([tile(0, [[0, 1], [1, 1]])]));
assert.deepEqual(shared.selected, [0]); assert.equal(shared.stats.forced, 1);
const residual = pointSearch(fixture([tile(0, [[0, .5], [1, 1]])]));
assert.equal(residual.status, 'exhausted-finite-search');
const marked = pointSearch(fixture([tile(0, [[0, 1], [1, 1]], [['outside', 1]])]), { learned: { tiles: [tile(0, [[0, 1], [1, 1]], [['outside', 1]])], boundary: new Map([['outside', 0]]) } });
assert.equal(marked.status, 'exhausted-finite-search'); assert.equal(marked.stats.forced, 0);
assert.throws(() => latticeLoop([[0,0,0],[2,0,0],[1,0,0],[1,1,0],[0,1,0]]), /intersects/);
const square = latticeLoop([[0,0,0],[1,0,0],[1,1,0],[0,1,0]]); assert.equal(project(square).word.length, 0);
for (let offset = 1; offset < 5; offset++) {
  const p = gridLoop([0,1,2,3,4], Array.from({ length: 5 }, (_, i) => (i + offset) % 5));
  const d = regularProjection(p); assert.equal(topology(d.word).genus, 0);
  if (offset === 2 || offset === 3) assert.equal(colorDimension(d.word), 2, 'Lattice trefoil projection.');
}
console.log(JSON.stringify({ passed: true, diagrams: pool.size, checkedMoves, triangles }));
