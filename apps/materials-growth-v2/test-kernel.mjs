import assert from "node:assert/strict";
import { PointSearch, verify } from "./kernel.mjs";
const tile = (id, points, m = []) => ({
  id,
  t: points.map((point) => ({ point, value: 1 })),
  m,
});
let k = new PointSearch({
  required: ["early", "late"],
  candidates: [tile("a", ["early"])],
});
assert.equal(k.decision().kind, "dead");
assert.equal(k.decision().point, "late");
k = new PointSearch({
  required: ["a", "b"],
  candidates: [tile("shared", ["a", "b"])],
});
assert.equal(k.decision().kind, "forced");
k.advance();
assert.equal(k.placed.size, 1);
assert.equal(k.decision().kind, "complete");
k.auditGraph();
k = new PointSearch({
  required: ["p"],
  capacity: 3,
  candidates: [{ id: "half", t: [{ point: "p", value: 2 }] }],
});
k.advance();
assert.equal(k.decision().kind, "dead");
k.advance();
assert.equal(k.points.get("p").total, 0);
const marks = (point, lo, hi) => [{ point, channel: "a", lo, hi }];
k = new PointSearch({
  required: ["p", "q"],
  fixedMarks: marks("outside", 0, 0),
  candidates: [
    tile("bad", ["p"], marks("outside", 1, 1)),
    tile("ok", ["p"]),
    tile("q", ["q"]),
  ],
});
assert.equal(k.reasons.get("bad"), "marking");
assert.equal(k.graph.get("p").size, 1);
k = new PointSearch({
  required: ["p", "q", "r"],
  candidates: [
    tile("p", ["p"], marks("m", 0, 1)),
    tile("q", ["q"], marks("m", 0.8, 1.8)),
    tile("r", ["r"], marks("m", 1.6, 2.6)),
  ],
});
k.apply("p");
k.apply("q");
assert.equal(k.reasons.get("r"), "marking");
// Generation outranks degree after global propagation. Later point gets its
// generation from a placed tile, rather than artificially assigning an index.
k = new PointSearch({
  required: ["early", "s"],
  candidates: [
    ...["a", "b", "c"].map((id) => tile(id, ["early"])),
    { ...tile("seed", ["s"]), activate: ["later"] },
    tile("x", ["later"]),
    tile("y", ["later"]),
  ],
});
k.apply("seed");
assert.equal(k.points.get("later").generation, 1);
assert.equal(k.decision().point, "early");
// Failed branch: selecting a excludes both alternatives at b through a mark-only point.
const model = {
  required: ["a", "b"],
  candidates: [
    tile("a-bad", ["a"], marks("z", 0, 0)),
    tile("a-good", ["a"], marks("z", 1, 1)),
    tile("b1", ["b"], marks("z", 1, 1)),
    tile("b2", ["b"], marks("z", 1, 1)),
  ],
};
k = new PointSearch(model);
const original = JSON.stringify(k.semanticState());
const cp = k.apply("a-bad");
assert.equal(k.decision().kind, "dead");
k.undo(cp);
assert.equal(JSON.stringify(k.semanticState()), original);
k.auditGraph();
for (let i = 0; i < 20 && k.decision().kind !== "complete"; i++) {
  k.advance();
  k.auditGraph();
}
assert.ok(k.stats.backtracks);
assert.ok(verify(model, [...k.placed.keys()]).complete);
// Independent exhaustive subset enumeration agrees with DFS on tiny models.
for (let seed = 0; seed < 32; seed++) {
  const model = {
    required: ["0", "1", "2"],
    candidates: Array.from({ length: 5 }, (_, i) =>
      tile(
        "t" + i,
        [0, 1, 2]
          .filter((j) => (((seed + 1) * (i + 3)) >> (j + 1)) & 1)
          .map(String),
      ),
    ).filter((c) => c.t.length),
  };
  const has = Array.from({ length: 2 ** model.candidates.length }, (_, mask) =>
    model.candidates.filter((_, i) => (mask >> i) & 1).map((c) => c.id),
  ).some((ids) => verify(model, ids).complete);
  const s = new PointSearch(model);
  for (
    let n = 0;
    n < 500 &&
    !["complete"].includes(s.decision().kind) &&
    s.status !== "exhausted";
    n++
  )
    s.advance();
  assert.equal(s.decision().kind === "complete", has);
}
k = new PointSearch({
  required: [{ id: "x", complete: false }],
  complete: false,
  candidates: [],
});
assert.equal(k.decision().kind, "unknown");
k.addCandidate(tile("one", ["x"]));
assert.equal(k.decision().kind, "branch");
// A failed expansion is atomic; a retained cache must not leave active state.
k = new PointSearch({
  required: ["a"],
  candidates: [{ ...tile("a", ["a"]), activate: ["new"] }],
  expand: () => {
    throw Error("budget");
  },
});
const before = JSON.stringify(k.semanticState());
assert.throws(() => k.apply("a"), /budget/);
assert.equal(JSON.stringify(k.semanticState()), before);
k.auditGraph();
console.log(
  "point kernel: dead/forced/generation, fractions, interval intersection, mark-only dependencies, rollback, 32 exhaustive controls, incomplete domains PASS",
);
