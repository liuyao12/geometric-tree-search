import assert from "node:assert/strict";
import { fitAdditiveContactEnvelope } from "../apps/iqc-growth-live/contact-envelope-fit.js";

const prior = { H: .31, O: .66, Na: 1.66, Cl: 1.02, A: 1, B: 1.4, C: .8 };
const model = (records) => ({ records: records.map(([key, species, lowerContact, observations = 16]) => ({
  key, species, lowerContact, typicalContact: lowerContact, nearestObservations: observations,
})) });

const elemental = fitAdditiveContactEnvelope(model([["A|A", ["A", "A"], 2.4]]), { priorRadiiAngstrom: prior });
assert.equal(elemental.available, true);
assert.ok(Math.abs(elemental.radiiAngstrom.A - 1.2) < 1e-12);
assert.equal(elemental.dataRank, 1);
assert.equal(elemental.priorDependentParameterCount, 0);

const nacl = fitAdditiveContactEnvelope(model([
  ["Cl|Na", ["Cl", "Na"], 2.82, 100],
  ["Na|Na", ["Na", "Na"], 3.99, 50],
  ["Cl|Cl", ["Cl", "Cl"], 3.99, 50],
]), { priorRadiiAngstrom: prior });
assert.deepEqual(nacl.selectedPairs.map((record) => record.key), ["Cl|Na"]);
assert.ok(Math.abs(nacl.radiiAngstrom.Na + nacl.radiiAngstrom.Cl - 2.82) < .01);
assert.ok(nacl.radiiAngstrom.Na > nacl.radiiAngstrom.Cl, "underdetermined cross-only fit must retain prior size ordering");
assert.equal(nacl.dataRank, 1);
assert.equal(nacl.priorDependentParameterCount, 1);

const water = fitAdditiveContactEnvelope(model([
  ["H|O", ["H", "O"], .96, 30], ["H|H", ["H", "H"], 1.51, 30], ["O|O", ["O", "O"], 2.76, 30],
]), { priorRadiiAngstrom: prior });
assert.deepEqual(water.selectedPairs.map((record) => record.key), ["H|O"]);
assert.ok(Math.abs(water.radiiAngstrom.H + water.radiiAngstrom.O - .96) < .01);

const ternary = fitAdditiveContactEnvelope(model([
  ["A|A", ["A", "A"], 2], ["A|B", ["A", "B"], 2.4],
  ["A|C", ["A", "C"], 1.8], ["B|C", ["B", "C"], 2.2],
]), { priorRadiiAngstrom: prior, leadingShellRatio: 1.5, ridgeFraction: 1e-6 });
assert.equal(ternary.dataRank, 3);
assert.ok(Math.abs(ternary.radiiAngstrom.A - 1) < 1e-5);
assert.ok(Math.abs(ternary.radiiAngstrom.B - 1.4) < 1e-5);
assert.ok(Math.abs(ternary.radiiAngstrom.C - .8) < 1e-5);
assert.ok(ternary.rmsResidualAngstrom < 1e-5);

const reversed = fitAdditiveContactEnvelope(model([
  ["Cl|Cl", ["Cl", "Cl"], 3.99, 50], ["Na|Na", ["Na", "Na"], 3.99, 50],
  ["Cl|Na", ["Cl", "Na"], 2.82, 100],
]), { priorRadiiAngstrom: prior });
assert.deepEqual(reversed, nacl, "record ordering must not change the fitted envelope");

const scaled = fitAdditiveContactEnvelope(model([["A|A", ["A", "A"], 1.2]]), {
  priorRadiiAngstrom: prior, sceneToAngstrom: 2,
});
assert.ok(Math.abs(scaled.radiiAngstrom.A - elemental.radiiAngstrom.A) < 1e-12);
assert.ok(Math.abs(scaled.radiiScene.A * 2 - scaled.radiiAngstrom.A) < 1e-12);
assert.equal(scaled.targetUsed, false);
assert.equal(scaled.usedAsGrowthInput, false);
assert.equal(scaled.physicalRadiusIdentityInferred, false);

console.log("contact-envelope fit regression passed");
