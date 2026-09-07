import assert from "node:assert/strict";
import {
  MAX_VALUE,
  deriveP2Model,
  makeCyclotomicHost,
  makeP1FrontierSearch,
  makeP1Model,
  makePenroseModelSet,
  makeSelectedTileSearch,
  makeSearchTrace,
  makeUniversalVertexAtlas,
  pointTotals
} from "../assets/penrose-model-set.js";
import {
  benchmarkGCTSPruning,
  learnPenroseGCTS,
  markingForTile
} from "../assets/penrose-gcts-marking.js";

const assertExactPoint = point => {
  assert.deepEqual(Object.keys(point).sort(), ["coeff", "denominator"]);
  assert.equal(point.coeff.length, 5);
  point.coeff.forEach(value => assert(Number.isSafeInteger(value)));
  assert(Number.isSafeInteger(point.denominator));
  assert(point.denominator > 0);
};

const phaseCodes = [47, 181, 293, 419, 557, 673, 811];
const models = phaseCodes.map(phaseCode =>
  makePenroseModelSet({ radius: 11, phaseCode })
);

for (const model of models) {
  assert.equal(model.exact, true);
  assert(model.tiles.length > 400);
  for (const tile of model.tiles) {
    assert(!("points" in tile));
    assert(!("center" in tile));
    assert.equal(tile.exactPoints.length, 4);
    tile.exactPoints.forEach(assertExactPoint);
    assertExactPoint(tile.centerExact);
    tile.center2.forEach(value => assert(Number.isSafeInteger(value)));
  }
  for (const vertex of model.vertices) {
    assert(!("point" in vertex));
    assertExactPoint(vertex.exact);
  }
}

const repeat = makePenroseModelSet({ radius: 11, phaseCode: phaseCodes[0] });
assert.deepEqual(
  repeat.tiles.map(tile => tile.id),
  models[0].tiles.map(tile => tile.id),
  "exact construction must be deterministic"
);

const p1 = makeP1Model();
assert.equal(p1.presentation, "P1");
assert.equal(p1.exact, true);
assert.equal(p1.tiles.length, 241);
assert.equal(p1.vertices.length, 435);
assert.deepEqual([...new Set(p1.tiles.map(tile => tile.kind))].sort(),
  ["boat", "diamond", "p2", "p3", "p5", "star"]);
for (const tile of p1.tiles) {
  tile.exactPoints.forEach(assertExactPoint);
  assertExactPoint(tile.centerExact);
  assert.equal(tile.weights.reduce((sum, weight) => sum + weight, 0),
    5 * (tile.exactPoints.length - 2));
}
assert.equal(Math.max(...pointTotals(p1.tiles).values()), MAX_VALUE);
const p1Search = makeP1FrontierSearch({
  p1Model: p1,
  selectedIds: new Set(["p1-p5", "p1-p3", "p1-p2", "p1-star", "p1-boat", "p1-diamond"]),
  targetCount: 60
});
assert.equal(p1Search.success, true);
assert.equal(p1Search.model.online, true);
assert.equal(p1Search.model.vertices.length, 0);
assert.equal(p1Search.solution.length, 60);
assert(p1Search.trace.some(event => event.type === "remove"));
assert([...pointTotals(p1Search.solution).values()].every(value => value <= MAX_VALUE));
const p1EdgeCounts = new Map();
p1Search.solution.forEach(tile => tile.vertices.forEach((vertex, index) => {
  const next = tile.vertices[(index + 1) % tile.vertices.length];
  const edge = [vertex, next].sort().join("|");
  p1EdgeCounts.set(edge, (p1EdgeCounts.get(edge) || 0) + 1);
}));
const p1BoundaryGraph = new Map();
[...p1EdgeCounts].filter(([, count]) => count === 1).forEach(([edge]) => {
  const [from, to] = edge.split("|");
  if (!p1BoundaryGraph.has(from)) p1BoundaryGraph.set(from, []);
  if (!p1BoundaryGraph.has(to)) p1BoundaryGraph.set(to, []);
  p1BoundaryGraph.get(from).push(to);
  p1BoundaryGraph.get(to).push(from);
});
assert([...p1BoundaryGraph.values()].every(neighbors => neighbors.length === 2));
const p1BoundarySeen = new Set();
const p1BoundaryQueue = [p1BoundaryGraph.keys().next().value];
while (p1BoundaryQueue.length) {
  const vertex = p1BoundaryQueue.pop();
  if (p1BoundarySeen.has(vertex)) continue;
  p1BoundarySeen.add(vertex);
  p1BoundaryQueue.push(...p1BoundaryGraph.get(vertex));
}
assert.equal(p1BoundarySeen.size, p1BoundaryGraph.size, "online P1 growth must have one outer boundary and no holes");

const marking = learnPenroseGCTS(models);
assert.equal(marking.rank, 5);
assert.equal(marking.vertexStars.length, 7);
assert.equal(marking.validationMismatches, 0);
assert.deepEqual(marking.tensor.shape, [2, 10, 4, 5]);
assert.equal(marking.tensor.values.length, 400);
assert.equal(marking.tensor.activeSlots, 40);
assert(marking.tensor.values instanceof Float64Array);
assert.equal(marking.ammannAudit.rediscovered, false);
assert.equal(marking.ammannAudit.exactStraightContinuation, false);
assert.equal(marking.ammannAudit.falseAccepts, 48);

const comparison = benchmarkGCTSPruning(models.slice(0, 5), models.slice(5));
assert.equal(comparison.contacts, 1770);
assert.equal(comparison.methods.compatibility.falsePrunes, 0);
assert(comparison.methods.compatibility.examined < comparison.methods.capacity.examined);
assert(comparison.methods.compatibility.backtracks < comparison.methods.capacity.backtracks);

const markedTile = markingForTile(models[0].tiles[0], marking);
markedTile.edges.forEach(edge => assertExactPoint(edge.port));
markedTile.bars.forEach(bar => {
  assertExactPoint(bar.from);
  assertExactPoint(bar.to);
});

const fixed = makeUniversalVertexAtlas({
  radius: 12,
  phaseCode: 170,
  samples: 1
});
const p2 = deriveP2Model(fixed.base);
assert.equal(p2.presentation, "P2");
assert(p2.tiles.some(tile => tile.kind === "kite"));
assert(p2.tiles.some(tile => tile.kind === "dart"));
for (const tile of p2.tiles) {
  assert.equal(tile.exactPoints.length, 4);
  tile.exactPoints.forEach(assertExactPoint);
  assertExactPoint(tile.centerExact);
  assert.equal(tile.weights.reduce((sum, weight) => sum + weight, 0), 10);
  if (tile.kind === "kite") {
    assert.deepEqual([...new Set(tile.weights)].sort(), [2, 4]);
  } else {
    assert.deepEqual([...new Set(tile.weights)].sort(), [1, 2, 6]);
  }
}
assert([...pointTotals(p2.tiles).values()].every(value => value <= MAX_VALUE));
const p2Search = makeSelectedTileSearch({
  p3Model: fixed.base,
  p2Model: p2,
  selectedIds: new Set(["p2-kite", "p2-dart"]),
  preferredFamily: "P2",
  targetCount: 80
});
assert.equal(p2Search.success, true);
assert.equal(p2Search.solution.length, 80);
const mixedSearch = makeSelectedTileSearch({
  p3Model: fixed.base,
  p2Model: p2,
  selectedIds: new Set(["p2-kite", "p2-dart", "p3-thick", "p3-thin"]),
  preferredFamily: "P2",
  targetCount: 80
});
assert.equal(mixedSearch.success, true);
assert.equal(mixedSearch.model.presentation, "P2+P3");
assert(mixedSearch.model.tiles.some(tile => tile.presentation === "P2"));
assert(mixedSearch.model.tiles.some(tile => tile.presentation === "P3"));
const forcedMixedSearch = makeSelectedTileSearch({
  p3Model: fixed.base,
  p2Model: p2,
  selectedIds: new Set(["p2-kite", "p3-thick", "p3-thin"]),
  preferredFamily: "P2",
  targetCount: 80
});
assert.equal(forcedMixedSearch.success, true);
assert(forcedMixedSearch.solution.some(tile => tile.presentation === "P2"));
assert(forcedMixedSearch.solution.some(tile => tile.presentation === "P3"));
assert([...pointTotals(forcedMixedSearch.solution).values()].every(value => value <= MAX_VALUE));
const host = makeCyclotomicHost({
  radius: 12,
  height: 3,
  seed: fixed.seed
});
host.points.forEach(site => {
  assert(!("point" in site));
  assertExactPoint(site.exact);
});

const trace = makeSearchTrace(fixed.base, 100);
assert(trace.some(event => event.type === "remove"));
const totals = pointTotals(trace.filter(event => event.type === "add" && !event.speculative).map(event => event.tile));
assert([...totals.values()].every(value => Number.isSafeInteger(value) && value <= MAX_VALUE));

console.log(
  `ok: ${models.reduce((sum, model) => sum + model.tiles.length, 0)} exact tiles, ` +
  `${marking.positiveContacts} contacts, ${marking.tensor.activeSlots}/${marking.tensor.denseSlots} tensor slots`
);
