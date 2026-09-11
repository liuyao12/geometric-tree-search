import assert from "node:assert/strict";
import { discover } from "./learning.mjs";
import { samplePatch } from "./samples.mjs";
import { axisAngle, transform, register } from "./geometry.mjs";
function run(atoms, options = {}) {
  const g = discover(atoms, { epsilon: 0.03, ...options });
  let next;
  do {
    next = g.next();
  } while (!next.done);
  return next.value;
}
const atoms = samplePatch("nacl").atoms;
const nacl = run(atoms);
assert.equal(nacl.types.length, 2);
assert.deepEqual(
  nacl.types.map((t) => t.sites.length),
  [7, 7],
);
assert.equal(nacl.discovery.partialObservations.length, 6);
for (const t of nacl.types) {
  assert.equal(t.occurrences.length, 32);
  assert(t.sites.slice(1).every((s) => s.species !== t.sites[0].species));
  const radius = Math.hypot(...t.sites[1].position);
  assert(
    t.sites
      .slice(1)
      .every((s) => Math.abs(Math.hypot(...s.position) - radius) < 1e-8),
  );
}
assert.equal(run(atoms, { boundaryPolicy: "preserve" }).types.length, 8);
assert.equal(run(atoms, { neighbors: 5 }).types.length, 8);
const pose = { r: axisAngle([1, 2, 3], 0.731), t: [4, -7, 2] };
const moved = run(
  atoms.toReversed().map((a, i) => ({
    species: a.species === "Na" ? "opaque-A" : "opaque-B",
    position: transform(pose, a.position).map(
      (x, k) => x + 0.001 * Math.sin(i * 7 + k),
    ),
  })),
);
assert.equal(moved.types.length, 2);
assert(moved.types.every((t) => t.sites.length === 7));
for (const [id, size] of [
  ["copper", 13],
  ["iron", 9],
  ["silicon", 5],
  ["graphene", 4],
]) {
  const g = run(samplePatch(id).atoms);
  assert.equal(g.types.length, 1, id);
  assert.equal(g.types[0].sites.length, size, id);
}
const source = nacl.types[0].sites;
assert(register(source.slice(0, 4), source, 0.03, { subset: true }));
assert.equal(register(source.slice(0, 4), source, 0.03), null);
assert.equal(
  register(
    source.map((s, i) => (i === 0 ? { ...s, species: "wrong" } : s)),
    source,
    0.03,
  ),
  null,
);
console.log(
  "PASS adaptive motifs: NaCl, FCC, BCC, diamond, graphene; crop preservation; rigid motion, permutation, opaque labels and noise; subset registration",
);
