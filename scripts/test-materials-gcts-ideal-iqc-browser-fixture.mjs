import assert from "node:assert/strict";
import crypto from "node:crypto";
import { IDEAL_IQC_BROWSER_FIXTURE as fixture }
  from "../apps/iqc-growth-live/ideal-iqc-browser-fixture.js";

assert.equal(fixture.kind, "algorithmic cut-and-project control");
assert.equal(fixture.fixtureClass, "algorithmic");
assert.equal(fixture.materialClaim, "none");
assert.match(fixture.name, /Exact 6D/);
assert.match(fixture.sourceUrl, /materials_gcts_icosahedral_modelset\.py/);
assert.equal(fixture.atomCount, 507);
assert.equal(fixture.atoms.length, fixture.atomCount);
assert.equal(fixture.liftBound, 3);
assert.equal(fixture.physicalRadius, 9);
assert.ok(Math.abs(fixture.quadraticUnit - (1 + Math.sqrt(5)) / 2) < 1e-14);
assert.ok(fixture.rawMinimumDistance > 1);

const counts = new Map();
for (const [species, x, y, z] of fixture.atoms) {
  assert.ok(["Al", "Cu", "Fe"].includes(species));
  assert.ok([x, y, z].every(Number.isFinite));
  counts.set(species, (counts.get(species) || 0) + 1);
}
assert.deepEqual(Object.fromEntries(counts), { Al: 63, Cu: 150, Fe: 294 });
const payload = fixture.atoms.map(([species, x, y, z]) =>
  `${species},${x.toFixed(10)},${y.toFixed(10)},${z.toFixed(10)}`).join("\n");
assert.equal(crypto.createHash("sha256").update(payload).digest("hex"), fixture.coordinateSpeciesSha256);

console.log("ideal IQC browser fixture: pass");
