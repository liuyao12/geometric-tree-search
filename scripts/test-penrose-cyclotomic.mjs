import assert from "node:assert/strict";
import { canonical, latticeKey, cycloAdd, cycloMultiply, starMap, residueLayer, embedding, GOLDEN_PORTS, edgePort } from "../assets/cyclotomic-five.js";
import { makeCyclotomicSearch, makePenroseModelSet, pointTotals } from "../assets/penrose-model-set.js";
import { auditGoldenBars, exactlyParallel } from "../assets/penrose-golden-bars.js";
const int = coeff => ({ coeff, denominator: 1 });
const zero = int([0, 0, 0, 0]), one = int([1, 0, 0, 0]), zeta = int([0, 1, 0, 0]);
let power = one, sum = zero;
for (let i = 0; i < 5; i++) { sum = cycloAdd(sum, power); power = cycloMultiply(power, zeta); }
assert.deepEqual(sum, zero); assert.deepEqual(power, one);
assert.deepEqual(canonical(int([7, 8, 9, 10, 7])), int([0, 1, 2, 3]));
assert.equal(latticeKey(int([7, 8, 9, 10, 7])), latticeKey(int([0, 1, 2, 3])));
assert.deepEqual(canonical({ coeff: [2, 4, 6, 8], denominator: 2 }), int([1, 2, 3, 4]));
assert.throws(() => canonical({ coeff: [0, 0, 0, 0], denominator: 0 }));
assert.throws(() => residueLayer({ coeff: [1, 0, 0, 0], denominator: 2 }));
for (const p of [one, zeta, int([3, -2, 5, 7])]) {
  assert.deepEqual(starMap(starMap(starMap(starMap(p)))), p);
  assert.deepEqual(starMap(cycloMultiply(p, zeta)), cycloMultiply(starMap(p), starMap(zeta)));
}
assert.deepEqual(cycloAdd(...GOLDEN_PORTS.map(p => p.value)), one);
assert(Math.abs(embedding(GOLDEN_PORTS[1].value).y + (1 + Math.sqrt(5)) / 4) < 1e-12);
assert.equal(latticeKey(edgePort(one, zeta, GOLDEN_PORTS[0].value)), latticeKey(edgePort(zeta, one, GOLDEN_PORTS[1].value)));
assert(exactlyParallel(one, int([2, 0, 0, 0])));
assert(!exactlyParallel(one, zeta));

const shapeKey = tile => tile.exactPoints.map(latticeKey).sort().join("|");
let tested = 0;
for (const phaseCode of [0, 47, 170, 419, 1000]) {
  const result = makeCyclotomicSearch({ phaseCode, targetCount: 120 });
  assert(result.success); assert.equal(result.solution.length, 120);
  assert.equal(result.model.latticeRank, 4);
  assert.equal(result.stats.proposals, result.trace.filter(e => e.type === "try").length);
  assert.equal(result.stats.backtracks, result.trace.filter(e => e.type === "remove").length);
  const reference = new Set(makePenroseModelSet({ phaseCode, radius: 15 }).tiles.map(shapeKey));
  for (const tile of result.solution) {
    assert(reference.has(shapeKey(tile)), "independent bounded pentagrid enumeration must certify every frontier tile");
    assert(tile.latticePoints.every(p => p.coeff.length === 4 && p.denominator === 1));
  }
  assert([...pointTotals(result.solution).values()].every(n => n <= 10));
  assert.equal(new Set(result.solution.map(shapeKey)).size, 120);
  const seen = new Set();
  for (const tile of result.solution) {
    const edges = tile.vertices.map((v, k) => [v, tile.vertices[(k + 1) % 4]].sort().join("|"));
    if (seen.size) assert(edges.some(e => seen.has(e)), "each new tile attaches to the existing patch");
    edges.forEach(e => seen.add(e));
  }
  const audit = auditGoldenBars(result.solution);
  assert(audit.survivors > 0); assert.equal(audit.families, 5); assert.equal(audit.rediscovered, false);
  const edgeCounts = new Map(), ends = new Map();
  for (const tile of result.solution) for (let k = 0; k < 4; k++) {
    const key = [latticeKey(tile.exactPoints[k]), latticeKey(tile.exactPoints[(k + 1) % 4])].sort().join("|");
    edgeCounts.set(key, (edgeCounts.get(key) || 0) + 1);
  }
  for (const bars of audit.byTile.values()) for (const bar of bars) for (const port of bar.ends) {
    const key = `${latticeKey(port.point)}:${bar.family}`;
    if (!ends.has(key)) ends.set(key, new Set()); ends.get(key).add(bar.tileId);
  }
  for (const bars of audit.byTile.values()) for (const bar of bars) for (const port of bar.ends) {
    if (edgeCounts.get(port.edge) === 2) assert(ends.get(`${latticeKey(port.point)}:${bar.family}`).size >= 2);
  }
  tested += result.solution.length;
}
const limited = makeCyclotomicSearch({ nodeLimit: 1 });
assert(limited.stopped); assert(!limited.success); assert(limited.stats.proposals <= 1);
const empty = makeCyclotomicSearch({ selectedIds: [] });
assert(!empty.success); assert.equal(empty.trace.length, 0);
const partial = makeCyclotomicSearch({ selectedIds: ["p3-thin"], targetCount: 60 });
assert(partial.solution.every(t => t.kind === "thin")); assert(!partial.success);
assert.deepEqual(makeCyclotomicSearch({ targetCount: 20 }).trace, makeCyclotomicSearch({ targetCount: 20 }).trace);
console.log(`ok: ring identities, five phases, ${tested} independently certified frontier rhombs, exact golden-port continuation, bounded and partial searches`);
