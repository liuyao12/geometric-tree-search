import assert from "node:assert/strict";
import { identifyClusters, trainMarking } from "./continuous-learning.mjs";
import { ContinuousSearch } from "./continuous-search.mjs";
import { samplePatch } from "./continuous-samples.mjs";
import {
  I,
  keySites,
  canonicalSupport,
  rotate,
  add,
} from "./continuous-geometry.mjs";
const drain = (g) => {
  let r;
  while (!(r = g.next()).done) {}
  return r.value;
};
const grammar = drain(identifyClusters(samplePatch("nacl").atoms));
assert.equal(grammar.audit.completeAtomicCover, true);
assert.ok(grammar.types.length);
assert.ok(grammar.ports.length);
assert.equal(
  grammar.types.filter(
    (t) => t.sites.length === 7 && t.symmetries.length === 24,
  ).length,
  2,
  "both NaCl octahedral stabilizers",
);
assert.ok(
  grammar.types
    .filter((t) => t.symmetries.length === 24)
    .every((t) => t.observedOrientationClasses === 1),
  "one orientation modulo octahedral symmetry",
);
const atomKeys = keySites(grammar.atoms);
const search = new ContinuousSearch(grammar, { maximumAtoms: 250 });
for (let i = 0; i < 20000 && !search.status.endsWith("limit"); i++)
  search.advance();
assert.ok(search.stats.bestAtoms > 216, "must emit beyond full observed seed");
for (const a of search.spatial.records) {
  const xyz = a.position.map((v) => v / 2.8201 + 2.5);
  assert.ok(xyz.every((v) => Math.abs(v - Math.round(v)) < 1e-6));
  assert.equal(
    a.species,
    xyz.reduce((s, v) => s + Math.round(v), 0) % 2 === 0 ? "Na" : "Cl",
  );
}
assert.equal(
  keySites(search.spatial.records.slice(0, 216)),
  atomKeys,
  "seed immutable",
);
assert.equal(search.receipt().targetUsed, false);
const g = grammar.types.find((t) => t.sites.length === 7),
  r = [
    [0, -1, 0],
    [1, 0, 0],
    [0, 0, 1],
  ];
assert.equal(
  canonicalSupport(g.sites).key,
  canonicalSupport(
    g.sites.map((s) => ({
      species: s.species,
      position: add(rotate(r, s.position), [3.12, -0.29, 7.1]),
    })),
  ).key,
);
const chiral = [
  { species: "A", position: [0, 0, 0] },
  { species: "B", position: [1, 0, 0] },
  { species: "C", position: [0, 2, 0] },
  { species: "D", position: [0, 0, 3] },
];
assert.notEqual(
  canonicalSupport(chiral).key,
  canonicalSupport(
    chiral.map((s) => ({
      ...s,
      position: [-s.position[0], ...s.position.slice(1)],
    })),
  ).key,
);
const mark = drain(trainMarking(grammar, { channels: 4 }));
assert.ok(mark.curve.at(-1) < mark.curve[0]);
assert.throws(
  () =>
    new ContinuousSearch(grammar, {
      marking: { ...mark, grammarKey: "other" },
    }),
);
// A finite search must really undo every placement and restore its exact seed.
const bounded = new ContinuousSearch(grammar, {
  boundary: (p) => p.every((v) => Math.abs(v) < 8),
  maximumAtoms: 240,
});
for (
  let i = 0;
  i < 5000 &&
  bounded.status !== "exhausted" &&
  !bounded.status.endsWith("limit");
  i++
)
  bounded.advance();
assert.equal(bounded.status, "exhausted");
assert.equal(keySites(bounded.spatial.records), atomKeys);
// Synthetic finite two-arm port grammar exhausts alternatives with rollback.
const tri = [
  { species: "A", position: [0, 0, 0] },
  { species: "A", position: [1, 0, 0] },
  { species: "A", position: [0, 1, 0] },
];
const fixture = {
  atoms: tri,
  types: [{ sites: tri, symmetries: [I], key: "triangle" }],
  occurrences: [{ type: 0, pose: { r: I, t: [0, 0, 0] } }],
  ports: [
    { id: 0, parent: 0, child: 0, pose: { r: I, t: [1, 0, 0] }, count: 1 },
    { id: 1, parent: 0, child: 0, pose: { r: I, t: [0, 1, 0] }, count: 1 },
  ],
  tolerance: 1e-4,
  minimum: 1,
};
const tree = new ContinuousSearch(fixture, {
  boundary: (p) => p[0] <= 2 && p[1] <= 2,
});
for (let i = 0; i < 10000 && tree.status !== "exhausted"; i++) tree.advance();
assert.equal(tree.status, "exhausted");
assert.ok(tree.stats.backtracks > 0);
assert.equal(keySites(tree.spatial.records), keySites(tri));
assert.ok(tree.best.length > tri.length);
const suspended = new ContinuousSearch(fixture, {
  maximumAtoms: 3,
  boundary: (p) => p[0] <= 2 && p[1] <= 2,
});
suspended.advance();
assert.equal(suspended.status, "atom memory limit");
const suspendedIndex = suspended.frames.at(-1).index;
suspended.setAtomBudget(20);
suspended.advance();
assert.ok(suspended.spatial.records.length > 3);
assert.equal(suspended.frames.at(-1).index, suspendedIndex + 1);
const ice = drain(identifyClusters(samplePatch("ice").atoms));
assert.ok(
  ice.types.some(
    (t) =>
      t.sites
        .map((s) => s.species)
        .sort()
        .join() === "D,D,O",
  ),
);
assert.equal(ice.audit.completeAtomicCover, true);
const promotedIce = drain(
  identifyClusters(samplePatch("ice").atoms, { hierarchy: true }),
);
assert.equal(promotedIce.audit.hierarchyLevels, 2);
assert.ok(promotedIce.types.some((t) => t.level === 1));
assert.equal(promotedIce.audit.completeAtomicCover, true);
const promotedSearch = new ContinuousSearch(promotedIce);
let promotedEvent;
do {
  promotedEvent = promotedSearch.advance();
} while (promotedEvent.type === "evaluating");
assert.equal(promotedEvent.type, "accept");
assert.ok(promotedSearch.spatial.records.length > promotedIce.atoms.length);
const glass = drain(identifyClusters(samplePatch("glass").atoms));
assert.equal(glass.types.length, 0);
assert.equal(glass.residuals.length, glass.atoms.length);
const sheet = drain(identifyClusters(samplePatch("graphene").atoms));
assert.ok(sheet.ports.length);
assert.equal(sheet.residuals.length, 0);
const reverse = drain(identifyClusters([...grammar.atoms].reverse()));
assert.deepEqual(
  reverse.types.map((t) => t.key).sort(),
  grammar.types.map((t) => t.key).sort(),
);
assert.equal(reverse.ports.length, grammar.ports.length);
console.log(
  JSON.stringify({
    pass: true,
    types: grammar.types.length,
    ports: grammar.ports.length,
    grown: search.stats.bestAtoms,
    rollback: tree.stats.backtracks,
    iceMolecule: true,
    amorphousRejected: true,
    budgetResumed: true,
  }),
);
