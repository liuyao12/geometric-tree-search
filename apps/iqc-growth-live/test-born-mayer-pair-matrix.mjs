import assert from "node:assert/strict";
import {
  bornMayerPairParameter,
  buildBornMayerPairMatrix,
  canonicalSpeciesPairKey,
} from "./born-mayer-pair-matrix.mjs";

const envelope = {
  available: true,
  radiiAngstrom: { Na: 1.1, Cl: 1.7, O: .7 },
  selectedPairCount: 3,
  rmsResidualAngstrom: .04,
};

assert.equal(canonicalSpeciesPairKey("Na", "Cl"), canonicalSpeciesPairKey("Cl", "Na"));
const uniform = buildBornMayerPairMatrix(["Na", "Cl", "Na"], envelope, {
  policy: "uniform", amplitudeElectronVolt: 800, decayAngstrom: .25,
});
assert.equal(uniform.pairCount, 3);
assert.equal(uniform.geometryConditionedPairs, 0);
assert.ok(uniform.records.every((record) => record.decayAngstrom === .25));

const scaled = buildBornMayerPairMatrix(["Na", "Cl", "O"], envelope, {
  policy: "contact-scaled", amplitudeElectronVolt: 1000, decayAngstrom: .3,
});
assert.equal(scaled.pairCount, 6);
assert.equal(scaled.geometryConditionedPairs, 6);
assert.equal(scaled.energyOrForceFitted, false);
assert.equal(scaled.targetUsed, false);
assert.equal(bornMayerPairParameter(scaled, "Cl", "Na").observedContactAngstrom, 2.8);
assert.ok(bornMayerPairParameter(scaled, "O", "O").decayAngstrom
  < bornMayerPairParameter(scaled, "Cl", "Cl").decayAngstrom);

const fallback = buildBornMayerPairMatrix(["Na", "Xx"], { available: false }, {
  policy: "contact-scaled", amplitudeElectronVolt: 500, decayAngstrom: .4,
});
assert.equal(fallback.geometryConditionedPairs, 0);
assert.equal(fallback.uniformFallbackPairs, 3);
assert.ok(fallback.records.every((record) => record.parameterSource.includes("fallback")));

assert.throws(() => buildBornMayerPairMatrix(["Na"], envelope, { policy: "invented" }), RangeError);
console.log("Born-Mayer pair matrix tests passed");
