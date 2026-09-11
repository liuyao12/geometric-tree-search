import assert from "node:assert/strict";
import {
  sampleCatalog,
  sampleFamilies,
  samplesInFamily,
  samplePatch,
} from "./samples.mjs";
import { distance } from "./geometry.mjs";
const ids = sampleCatalog.map((s) => s[0]);
assert.equal(new Set(ids).size, ids.length);
assert.deepEqual(
  sampleFamilies.flatMap((f) => f[2]).sort(),
  [...ids].sort(),
  "Each sample belongs to exactly one browsing family",
);
assert.deepEqual(samplesInFamily("all"), sampleCatalog);
assert.deepEqual(samplesInFamily("missing"), []);
for (const [id, , members] of sampleFamilies)
  assert.deepEqual(
    samplesInFamily(id).map((s) => s[0]),
    members,
  );
for (const id of ids) {
  const s = samplePatch(id);
  assert(s.source && s.name);
  assert(s.atoms.length >= 4 && s.atoms.length <= 600);
  assert(
    s.atoms.every(
      (a) =>
        typeof a.species === "string" &&
        a.position.length === 3 &&
        a.position.every(Number.isFinite),
    ),
    id,
  );
  const copy = samplePatch(id);
  s.atoms[0].position[0] += 100;
  assert.deepEqual(
    samplePatch(id),
    copy,
    "No shared mutable sample coordinates",
  );
}
for (const [id, coordination] of [
  ["hcp", 12],
  ["kagome", 4],
  ["checkerboard", 4],
  ["diamond", 4],
  ["sic", 4],
]) {
  const atoms = samplePatch(id).atoms;
  const center = atoms.reduce((a, b) =>
    Math.hypot(...a.position) < Math.hypot(...b.position) ? a : b,
  );
  const ds = atoms
    .filter((a) => a !== center)
    .map((a) => distance(a.position, center.position))
    .sort((a, b) => a - b);
  assert.equal(
    ds.filter((d) => Math.abs(d - ds[0]) < 1e-6).length,
    coordination,
    id,
  );
}
console.log(
  `${ids.length} sample fixtures, family membership/filtering, copy isolation and new interior coordination checks PASS`,
);
