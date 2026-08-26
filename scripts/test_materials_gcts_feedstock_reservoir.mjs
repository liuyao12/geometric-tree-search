import assert from "node:assert/strict";
import { consumeFeedstock, evaluateFeedstockDemand, feedstockReservoirSnapshot,
  initializeFeedstockReservoir } from "../apps/iqc-growth-live/feedstock-reservoir.js";

const open = initializeFeedstockReservoir(["Na", "Cl"], "open");
assert.equal(evaluateFeedstockDemand(open, ["Na", "Na", "Cl"]).admitted, true);

let finite = initializeFeedstockReservoir(["Na", "Cl", "Cl"], "finite-1");
let result = consumeFeedstock(finite, ["Na", "Cl"]); finite = result.reservoir;
assert.deepEqual(finite.remaining, { Cl: 1, Na: 0 });
assert.equal(evaluateFeedstockDemand(finite, ["Na"]).admitted, false);
assert.deepEqual(evaluateFeedstockDemand(finite, ["Na"]).deficits, { Na: 1 });
assert.equal(feedstockReservoirSnapshot(finite).remainingAtoms, 1);

const four = initializeFeedstockReservoir(["A", "B", "B"], "finite-4");
assert.deepEqual(four.initial, { A: 4, B: 8 });
assert.equal(evaluateFeedstockDemand(four, Array(9).fill("B")).admitted, false);
console.log("finite/open feedstock reservoir accounting: passed");
