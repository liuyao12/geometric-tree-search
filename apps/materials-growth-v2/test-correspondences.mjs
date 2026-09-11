import assert from "node:assert/strict";
import { PointRegistry, I, distance, transform } from "./geometry.mjs";
import { MaterialExperiment } from "./material.mjs";
import { discover, learnSections } from "./learning.mjs";
import { samplePatch } from "./samples.mjs";
const drain = (g) => {
  let r;
  do {
    r = g.next();
  } while (!r.done);
  return r.value;
};
const r = new PointRegistry(0.03);
const a = r.intern([-0.02, 0, 0]),
  b = r.intern([0.02, 0, 0]);
assert.deepEqual(
  r.matches([0, 0, 0]).map((p) => p.id),
  [a, b],
);
assert.throws(() => r.intern([0, 0, 0]), /Ambiguous/);
const g = drain(discover(samplePatch("nacl").atoms, { epsilon: 0.03 }));
const e = new MaterialExperiment(g, drain(learnSections(g)), {
  maximumPoints: 40000,
  maximumCandidates: 80000,
});
const type = g.types[0],
  pose = { r: I, t: [100, 100, 100] };
const p = transform(pose, type.sites[1].position);
const left = e.point(p.map((v, k) => v + (k === 0 ? -0.02 : 0))),
  right = e.point(p.map((v, k) => v + (k === 0 ? 0.02 : 0)));
e.emit(type, pose);
const alternatives = [...e.engine.candidates.values()].filter(
  (c) => c.meta.pose === pose,
);
assert.equal(alternatives.length, 2);
assert.deepEqual(
  new Set(alternatives.map((c) => c.meta.sites[1])),
  new Set([left, right]),
);
for (const c of alternatives) {
  assert.equal(new Set(c.meta.sites).size, type.sites.length);
  c.meta.sites.forEach((id, i) =>
    assert(
      distance(
        e.registry.points[Number(id.slice(1))].position,
        transform(pose, type.sites[i].position),
      ) <= 0.03,
    ),
  );
  const checkpoint = e.engine.trail.length;
  e.engine.apply(c.id);
  assert(e.snapshot(false).validation.legal);
  e.engine.auditGraph();
  e.engine.undo(checkpoint);
  assert(!e.engine.placed.has(c.id));
  e.engine.auditGraph();
}
for (const id of ["cdyb", "asi"]) {
  const grammar = drain(discover(samplePatch(id).atoms, { epsilon: 0.03 }));
  const experiment = new MaterialExperiment(
    grammar,
    drain(learnSections(grammar)),
    { maximumPoints: 40000, maximumCandidates: 80000, softMemory: true },
  );
  for (let i = 0; i < 50; i++) {
    const event = experiment.step();
    assert(!/Ambiguous point correspondence/.test(event.message || ""));
    if (event.kind === "budget") {
      assert(event.resumable);
      experiment.continueWithMoreMemory();
    } else if (["unknown", "complete", "exhausted"].includes(event.kind)) break;
  }
  const s = experiment.snapshot(false);
  assert(s.correspondences.ambiguousSites > 0);
  assert(s.validation.legal && s.overlapValidation.legal);
  experiment.engine.auditGraph();
  console.log(id, s.atoms.length, s.status, s.correspondences);
}
console.log(
  "Correspondence alternatives, tolerance bounds, strict legality, rollback and nonfatal ambiguous proposals PASS",
);
