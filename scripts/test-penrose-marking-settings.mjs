import assert from "node:assert/strict";
import { createPenroseGrowth } from "../assets/penrose-growth.js";
import { ammannStates } from "../assets/penrose-ammann.js";

for (const useMarkings of [false, true]) {
  for (const markingDirections of [0, 1, 3, 6]) assert.throws(() => createPenroseGrowth({ useMarkings, markingDirections }), /all five/);
  const growth = createPenroseGrowth({ useMarkings, targetCount: 40, nodeLimit: 1000, seed: 17 });
  while (!growth.next().done) {}
  const snapshot = growth.snapshot(), orientations = new Map(snapshot.orientations), edges = new Map();
  assert.equal(snapshot.markingDirections, 5);
  assert.equal(snapshot.stats[useMarkings ? "edgeChecks" : "markingChecks"], 0);
  for (const tile of snapshot.tiles) {
    const state = ammannStates(tile).find(s => s.start === orientations.get(tile.id));
    assert(state); assert.equal(state.bars.length, 5);
    for (const [edge, signature] of state.signatures) {
      if (edges.has(edge)) assert.equal(signature, edges.get(edge)); else edges.set(edge, signature);
    }
  }
}
console.log("ok: both modes preserve full local compatibility; partial enforcement rejected; only the selected predicate is called");
