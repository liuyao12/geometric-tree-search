import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { CDYB_BROWSER_FIXTURE } from "../apps/iqc-growth-live/cdyb-browser-fixture.js";

const fixture = CDYB_BROWSER_FIXTURE;
assert.equal(fixture.atoms.length, 506);
assert.equal(fixture.license, "CC-BY-4.0");
assert.equal(fixture.articleDoi, "10.1107/S2053273326006601");
assert.equal(fixture.archiveDoi, "10.5281/zenodo.21470195");
assert.equal(fixture.archiveSha256, "b0de87a489e23b6ceed43c64728b132e20ba5aef971aee210f065ce9774cc222");

const counts = fixture.atoms.reduce((result, [species, x, y, z]) => {
  assert.ok(species === "Cd" || species === "Yb");
  assert.ok([x, y, z].every(Number.isFinite));
  assert.ok(Math.hypot(x, y, z) <= fixture.crop.radiusAngstrom + 1e-8);
  result[species] = (result[species] || 0) + 1;
  return result;
}, {});
assert.deepEqual(counts, { Cd: 431, Yb: 75 });

const digest = createHash("sha256").update(JSON.stringify(fixture.atoms)).digest("hex");
assert.equal(digest, fixture.normalizedAtomsSha256);
assert.ok(!Object.hasOwn(fixture, "sourceSites"));
assert.ok(!Object.hasOwn(fixture, "internalCoordinates"));
assert.ok(!Object.hasOwn(fixture, "occupationDomains"));

console.log("published Cd-Yb browser fixture: passed", { atoms: fixture.atoms.length, counts, digest });
