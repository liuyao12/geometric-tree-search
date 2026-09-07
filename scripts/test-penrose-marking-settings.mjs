import assert from "node:assert/strict";
import { createPenroseGrowth } from "../assets/penrose-growth.js";
import { ammannStates, ammannSignature, solveAmmannDecorations } from "../assets/penrose-ammann.js";

for (const markingDirections of [1, 3, 5]) {
  const growth = createPenroseGrowth({ useMarkings: true, markingDirections, targetCount: 40, nodeLimit: 1000, seed: 17 });
  while (!growth.next().done) {}
  const snapshot = growth.snapshot(), orientations = new Map(snapshot.orientations), shared = new Map();
  assert.equal(snapshot.markingDirections, markingDirections);
  assert(snapshot.stats.markingPrunes > 0);
  for (const tile of snapshot.tiles) {
    const state = ammannStates(tile).find(s => s.start === orientations.get(tile.id));
    assert(state); assert.equal(state.bars.length, 5, "weakening enforcement must not remove stripes");
    for (const edge of state.signatures.keys()) {
      const signature = ammannSignature(state, edge, markingDirections);
      if (shared.has(edge)) assert.equal(signature, shared.get(edge)); else shared.set(edge, signature);
    }
  }
  assert(solveAmmannDecorations(snapshot.tiles, { directionCount: markingDirections }).success);
}
const runPlain = markingDirections => {
  const growth = createPenroseGrowth({ useMarkings: false, markingDirections, targetCount: 40, seed: 17 });
  const trace = []; let step; while (!(step = growth.next()).done) trace.push(step.value);
  return trace;
};
assert.deepEqual(runPlain(1), runPlain(5), "inactive marking settings must not affect unmarked search");
assert.throws(() => createPenroseGrowth({ markingDirections: 0 }));
assert.throws(() => solveAmmannDecorations([], { directionCount: 6 }));
console.log("ok: 1/3/5-direction enforcement, complete fixed templates, inactive-rule independence, and invalid settings");
