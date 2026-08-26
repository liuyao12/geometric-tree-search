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

const noMovable = relaxLocalContactGeometry(sites.map((site) => ({ ...site, movable: false })), model, {
  displacementCap: .5,
});
assert.equal(noMovable.accepted, false);
assert.equal(noMovable.reason, "no movable sites");

assert.throws(() => relaxLocalContactGeometry(sites, model, { displacementCap: 0 }), /positive displacement cap/);

console.log("bounded local contact-constraint relaxation: passed");
