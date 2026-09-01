import assert from "node:assert/strict";
import { relaxLocalContactGeometry } from "../apps/iqc-growth-live/local-constraint-relaxation.js";

const record = Object.freeze({
  key: "A|A", species: ["A", "A"], typicalContact: 1,
  upperContact: 1.15, contactScale: .08, exclusion: .7,
});
const model = Object.freeze({ byKey: Object.freeze({ "A|A": record }) });
const sites = [
  { species: "A", position: [0, 0, 0], movable: false },
  { species: "A", position: [2, 0, 0], movable: false },
  { species: "A", position: [1.2, .35, 0], movable: true },
];
const result = relaxLocalContactGeometry(sites, model, {
  displacementCap: .5, maximumIterations: 16,
});
assert.equal(result.accepted, true);
assert.equal(result.contactTerms, 2);
assert(result.finalContactObjective < result.initialContactObjective);
assert(result.maximumDisplacement <= .5 + 1e-12);
assert.equal(result.positions[0][0], 0);
assert.equal(result.positions[1][0], 2);
assert(result.positions[2][1] < .35);

const repeat = relaxLocalContactGeometry(sites, model, {
  displacementCap: .5, maximumIterations: 16,
});
assert.deepEqual(repeat, result);

const observedSeed = relaxLocalContactGeometry(sites, model, {
  displacementCap: .5, maximumIterations: 1,
  initialOffsets: [[0, 0, 0], [0, 0, 0], [0, -.1, 0]],
});
assert.equal(observedSeed.accepted, true);
assert.equal(observedSeed.observedSeedSupplied, true);
assert.equal(observedSeed.observedSeedAccepted, true);
assert.equal(observedSeed.observedSeedSites, 1);
assert.equal(observedSeed.initialSeedAccepted, true);
assert.equal(observedSeed.initialSeedSites, 1);
assert.equal(observedSeed.initialSeedContactObjective, observedSeed.observedSeedContactObjective);
assert(observedSeed.observedSeedContactObjective < observedSeed.initialContactObjective);
assert(observedSeed.maximumDisplacement <= .5 + 1e-12);

const misleadingSeed = relaxLocalContactGeometry(sites, model, {
  displacementCap: .5, maximumIterations: 16,
  initialOffsets: [[0, 0, 0], [0, 0, 0], [0, .5, 0]],
});
assert.equal(misleadingSeed.accepted, true);
assert.equal(misleadingSeed.observedSeedSupplied, true);
assert.equal(misleadingSeed.observedSeedAccepted, false,
  "an archived vector that worsens the bounded objective must be ignored");
assert.equal(misleadingSeed.initialSeedAccepted, false);
assert(misleadingSeed.positions[2][1] < .35);

const shellCoupled = relaxLocalContactGeometry([
  { ...sites[0], movable: true, displacementCap: .05 },
  sites[1],
  { ...sites[2], displacementCap: .5 },
], model, { displacementCap: .5, maximumIterations: 16 });
assert.equal(shellCoupled.accepted, true);
const shellShift = Math.hypot(...shellCoupled.positions[0].map((value, axis) =>
  value - sites[0].position[axis]));
assert(shellShift > 0);
assert(shellShift <= .05 + 1e-12);
assert.equal(shellCoupled.maximumSiteCap, .5);
assert.throws(() => relaxLocalContactGeometry([
  { ...sites[0], movable: true, displacementCap: .6 }, sites[1], sites[2],
], model, { displacementCap: .5 }), /movable-site displacement cap/);

const noMovable = relaxLocalContactGeometry(sites.map((site) => ({ ...site, movable: false })), model, {
  displacementCap: .5,
});
assert.equal(noMovable.accepted, false);
assert.equal(noMovable.reason, "no movable sites");

assert.throws(() => relaxLocalContactGeometry(sites, model, { displacementCap: 0 }), /positive displacement cap/);

console.log("bounded local contact-constraint relaxation: passed");
