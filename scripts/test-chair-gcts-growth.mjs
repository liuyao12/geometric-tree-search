import assert from "node:assert/strict";
import {
  buildCollaredCatalog,
  createGrowthState,
  enumerateGrowthCandidates,
  growOne,
  shrinkOne
} from "../3d-reptiles/chair/chair-gcts.js";

const catalog = buildCollaredCatalog(2);
assert.equal(catalog.targetCount, 64);
assert.ok(catalog.variants.length > 1);
assert.ok(catalog.connectorCount > 1);

let state = createGrowthState(2);
while (!state.complete) {
  const candidates = enumerateGrowthCandidates(state);
  assert.ok(candidates.candidates.length > 0, `growth stalled after ${state.placements.length} chairs`);
  state = growOne(state);
}
assert.equal(state.placements.length, 64);
assert.equal(enumerateGrowthCandidates(state).candidates.length, 0);

const occupied = [];
for (const placement of state.placements) {
  const variant = state.catalog.variants[placement.variantId];
  for (const cell of variant.cells) occupied.push(cell.map((value, axis) => value + placement.origin[axis]));
}
const minima = [0, 1, 2].map(axis => Math.min(...occupied.map(cell => cell[axis])));
const normalized = new Set(occupied.map(cell => cell.map((value, axis) => value - minima[axis]).join(",")));
const expected = new Set();
for (let x = 0; x < 8; x += 1) for (let y = 0; y < 8; y += 1) for (let z = 0; z < 8; z += 1) {
  if (x < 4 || y < 4 || z < 4) expected.add([x, y, z].join(","));
}
assert.deepEqual(normalized, expected, "local matches must reconstruct the level-two chair, up to translation");

state = shrinkOne(state);
assert.equal(state.placements.length, 63);
state = growOne(state);
assert.equal(state.placements.length, 64);

console.log("chair GCTS local growth passed", {
  variants: catalog.variants.length,
  connectors: catalog.connectorCount,
  placements: state.placements.length,
  tested: state.tested,
  rejected: state.rejected
});
