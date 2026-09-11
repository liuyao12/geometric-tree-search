import assert from "node:assert/strict";
import {
  learnOverlapRules,
  acceptsOverlap,
  overlapConstraint,
  verifyOverlaps,
} from "./overlap-rules.mjs";
import { PointSearch } from "./kernel.mjs";
import { axisAngle, transform, sub, add } from "./geometry.mjs";
const drain = (g) => {
  let r;
  do {
    r = g.next();
  } while (!r.done);
  return r.value;
};
const atoms = [
  [0, 0, 0],
  [1, 0, 0],
  [0, 1, 0],
  [0, 0, 1],
].map((position) => ({ species: "opaque", position }));
const ids = [
  [0, 1, 2],
  [3, 1, 2],
];
const grammar = {
  atoms,
  epsilon: 0.01,
  types: ids.map((list, id) => ({
    id,
    sites: list.map((i) => atoms[i]),
    occurrences: [{ anchor: list[0], ids: list, mapping: [0, 1, 2] }],
  })),
};
const rules = drain(learnOverlapRules(grammar));
const [a, b] = ids.map((list) =>
  list.map((i) => ({ id: `p${i}`, ...atoms[i] })),
);
assert.equal(rules.pairs, 2);
assert(acceptsOverlap(rules, 0, 1, a, b));
const pivot = [1, 0, 0],
  rotation = axisAngle([-1, 1, 0], 0.47);
const bad = b.map((s) => ({
  ...s,
  position: add(
    pivot,
    transform({ r: rotation, t: [0, 0, 0] }, sub(s.position, pivot)),
  ),
}));
assert(!acceptsOverlap(rules, 0, 1, a, bad));
const global = { r: axisAngle([2, 1, -3], 0.63), t: [10, 4, -2] };
assert(
  acceptsOverlap(
    rules,
    0,
    1,
    a.map((s) => ({ ...s, position: transform(global, s.position) })),
    b.map((s) => ({ ...s, position: transform(global, s.position) })),
  ),
);
const registry = {
  points: [...atoms, { species: "opaque", position: bad[0].position }],
};
const candidate = (id, type, points) => ({
  id,
  t: [{ point: points[0], value: 1 }],
  m: points.map((point) => ({ point, channel: "label", lo: 1, hi: 1 })),
  meta: { type, sites: points },
});
const filter = overlapConstraint(grammar, rules, registry);
const k = new PointSearch({
  required: ["p0", "p3", "p4"],
  constraint: filter,
  candidates: [
    candidate("a", 0, ["p0", "p1", "p2"]),
    candidate("good", 1, ["p3", "p1", "p2"]),
    candidate("bad", 1, ["p4", "p1", "p2"]),
  ],
});
assert(k.graph.get("p4").has("bad"));
const checkpoint = k.trail.length;
k.apply("a");
assert.equal(k.reasons.get("bad"), "unobserved-overlap");
assert.equal(k.graph.get("p4").size, 0);
assert(k.graph.get("p3").has("good"));
assert.equal(k.decision().kind, "dead"); // Global dead still outranks forced.
k.auditGraph();
k.apply("good");
assert(
  verifyOverlaps(grammar, rules, registry, k.candidates, ["a", "good"]).legal,
);
assert(
  !verifyOverlaps(grammar, rules, registry, k.candidates, ["a", "bad"]).legal,
);
k.undo(checkpoint);
assert(k.graph.get("p4").has("bad"));
k.auditGraph();
// The unchanged occupancy-only baseline admits the same wrong connection.
const baseline = new PointSearch({
  required: ["p0", "p4"],
  candidates: [
    candidate("a", 0, ["p0", "p1", "p2"]),
    candidate("bad", 1, ["p4", "p1", "p2"]),
  ],
});
baseline.apply("a");
assert(baseline.graph.get("p4").has("bad"));
console.log(
  "PASS observed overlap replay, unseen rigid hinge rejection with identical labels, global rotation, mark-only graph pruning, global-dead order, rollback and independent selected-pair verification",
);
