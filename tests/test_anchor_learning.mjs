import assert from 'node:assert/strict';
import { createModel, objective, trainStep, compileModel, makeProblem, graph, decision, search, verify } from '../assets/anchor-learning.js';

const m = createModel(7), before = objective(m);
// Check the actual analytical gradients, including the norm and centroid terms.
for (let i = 0; i < 4; i++) for (const axis of ['x', 'y', 't', 'm']) {
  const v = m.anchors[i][axis], eps = 1e-6;
  m.anchors[i][axis] = v + eps; const hi = objective(m).loss;
  m.anchors[i][axis] = v - eps; const lo = objective(m).loss;
  m.anchors[i][axis] = v;
  assert.ok(Math.abs((hi - lo) / (2 * eps) - before.grad[i][axis]) < 1e-7, `${i}:${axis}`);
}
assert.equal(compileModel(m).ok, false);
const frozen = structuredClone(m), xy = frozen.anchors.map(p => [p.x, p.y]);
for (let i = 0; i < 300; i++) { trainStep(m); trainStep(frozen, { moveAnchors: false }); }
assert.ok(objective(m).loss < 1e-12);
assert.deepEqual(frozen.anchors.map(p => [p.x, p.y]), xy);
assert.ok(objective(frozen).terms.contact > .01);
assert.equal(compileModel(frozen).ok, false);
for (const seed of [1, 19, 99, 9999]) {
  const model = createModel(seed);
  for (let i = 0; i < 300; i++) trainStep(model);
  assert.equal(compileModel(model).ok, true);
}
const compiled = compileModel(m), problem = makeProblem(compiled);
assert.equal(problem.candidates.length, 32);
const empty = graph(problem, []);
assert.equal(empty.frontier.size, 16);
assert.equal(empty.reverse.size, 32);
assert.ok([...empty.frontier.values()].every(ids => ids.length === 8));
const first = graph(problem, [0]);
assert.ok(first.markingEliminations > 0);
for (const [p, ids] of first.frontier) for (const id of ids)
  assert.ok(first.reverse.get(id).some(q => q.p === p && q.units === 3));
// Complete global checks, including a distant dead point after a forced point.
assert.equal(decision({ frontier: new Map([[0, [1]], [15, []]]) }).kind, 'dead');
assert.equal(decision({ frontier: new Map([[0, [1, 2]], [15, [3]]]) }).kind, 'forced');
assert.equal(decision({ frontier: new Map([[0, [1, 2, 3]], [15, [3, 4]]]) }).point, 15);
const run = options => { const it = search(compiled, options); let step; do { step = it.next(); } while (!step.done); return step.value; };
const result = run();
assert.equal(result.status, 'finite exact tiling on a torus');
assert.equal(result.stats.accepted, 16);
assert.equal(verify(compiled, 4, result.placements), true);
assert.equal(verify(compiled, 4, result.placements.slice(1)), false);
assert.equal(verify(compiled, 4, [...result.placements, result.placements[0]]), false);
const corrupt = structuredClone(result.placements); corrupt[0].phase *= -1;
assert.equal(verify(compiled, 4, corrupt), false);
assert.equal(run({ budget: 0 }).status, 'unknown: budget exhausted');
assert.deepEqual(graph(problem, []), empty); // Child state cannot mutate its parent.
const partial = search(compiled); partial.next(); partial.next(); partial.return();
assert.deepEqual(run(), result); // Cancellation leaves no branch exclusions or stale graph.

// Independent exhaustive oracle. Total required mass is 16 and each placement
// has mass 1. Opposite phases at one origin conflict, so an exact solution must
// use exactly one placement at each of the 16 origins. Enumerate all 2^16 choices.
let solutions = 0;
for (let mask = 0; mask < 65536; mask++) {
  const placements = Array.from({ length: 16 }, (_, i) => ({ x: i % 4, y: Math.floor(i / 4), phase: mask & (1 << i) ? -1 : 1 }));
  if (verify(compiled, 4, placements)) solutions++;
}
assert.equal(solutions, 2);
console.log(JSON.stringify({ passed: true, seeds: 5, exhaustivePhaseAssignments: 65536, exactSolutions: solutions,
  initialLoss: before.loss, trainedLoss: objective(m).loss, frozenLoss: objective(frozen).loss, stats: result.stats }, null, 2));
