import assert from "node:assert/strict";
import {
  compositionBalanceDelta,
  compositionDrift,
  learnCompositionTarget,
} from "../apps/iqc-growth-live/composition-balance.js";

const nacl = learnCompositionTarget(["Na", "Cl", "Na", "Cl"]);
assert.deepEqual(nacl.reducedRatio, { Cl: 1, Na: 1 });
assert.ok(compositionBalanceDelta(["Na", "Na", "Cl"], ["Cl"], nacl).delta < 0,
  "adding the deficient component must reduce NaCl reservoir drift");
assert.ok(compositionBalanceDelta(["Na", "Na", "Cl"], ["Na"], nacl).delta > 0,
  "adding an already excessive component must increase NaCl reservoir drift");

const water = learnCompositionTarget(["H", "O", "H", "H", "O", "H"]);
assert.deepEqual(water.reducedRatio, { H: 2, O: 1 });
assert.equal(compositionDrift(["O", "H", "H"], water).totalVariation, 0);

const ternarySpecies = ["A", "B", "B", "C", "C", "C", "A", "B", "B", "C", "C", "C"];
const ternary = learnCompositionTarget(ternarySpecies);
assert.deepEqual(ternary.reducedRatio, { A: 1, B: 2, C: 3 });
assert.deepEqual(learnCompositionTarget(ternarySpecies.slice().reverse()), ternary,
  "multicomponent targets must be atom-order invariant");
const balanced = compositionBalanceDelta(["A", "B", "B", "C", "C"], ["C"], ternary);
assert.ok(balanced.delta < 0, "a ternary candidate that completes the reduced ratio must be preferred");
const foreign = compositionBalanceDelta(["A", "B", "B", "C", "C", "C"], ["X"], ternary);
assert.ok(foreign.delta > 0 && foreign.projectedFractions.X > 0,
  "an unknown emitted species must not disappear from the balance audit");

console.log("multicomponent composition reservoir balance: passed", {
  nacl: nacl.reducedRatio,
  water: water.reducedRatio,
  ternary: ternary.reducedRatio,
});
