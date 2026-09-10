import assert from "node:assert/strict";
import { discover, learnSections } from "./learning.mjs";
import { MaterialExperiment } from "./material.mjs";
import { fitRigid, transform, axisAngle, distance } from "./geometry.mjs";
import { samplePatch } from "../iqc-growth-live/continuous-samples.mjs";
import {
  iceViiiUnitCellSites,
  ICE_VIII_BROWSER_FIXTURE,
} from "../iqc-growth-live/ice-viii-browser-fixture.js";
const drain = (g) => {
  let r;
  while (!(r = g.next()).done) {}
  return r.value;
};
const p = [
    [0, 0, 0],
    [1, 0, 0],
    [0, 2, 0],
    [0, 0, 3],
  ],
  pose = { r: axisAngle([1, 2, 3], 0.371), t: [0.7, 1.1, -2.3] },
  q = p.map((x) => transform(pose, x)),
  fit = fitRigid(p, q);
assert.ok(p.every((x, i) => distance(transform(fit, x), q[i]) < 1e-8));
for (const id of ["nacl", "ice"]) {
  const g = drain(
    discover(samplePatch(id).atoms, {
      epsilon: 0.03,
      neighbors: id === "ice" ? 5 : 6,
    }),
  );
  const m = drain(learnSections(g));
  const experiment = new MaterialExperiment(g, m, { maximumPoints: 20000 });
  for (let i = 0; i < 400; i++) {
    const e = experiment.step();
    if (["unknown", "complete", "exhausted", "budget"].includes(e.kind)) {
      console.log(e.kind, e.message || "");
      break;
    }
  }
  const s = experiment.snapshot();
  assert.ok(s.validation.legal);
  experiment.engine.auditGraph();
  assert.equal(s.stats.forced, 0);
  assert.equal(s.seedCovered, g.atoms.length);
  assert.ok(s.atoms.length > g.atoms.length);
  const novel = s.atoms.slice(g.atoms.length),
    labels = Object.fromEntries(
      [...new Set(novel.map((a) => a.species))].map((label) => [
        label,
        novel.filter((a) => a.species === label).length,
      ]),
    );
  assert.equal(Object.keys(labels).length, 2);
  console.log(
    id,
    JSON.stringify({
      types: g.types.length,
      connections: g.connections.length,
      atoms: s.atoms.length,
      covered: s.seedCovered,
      novelLabels: labels,
      frontier: s.frontier.length,
      status: s.status,
    }),
  );
  if (id === "ice") {
    // Evaluation only: the search never sees this unit cell or held-out extension.
    const cell = ICE_VIII_BROWSER_FIXTURE.cellAngstrom,
      unit = iceViiiUnitCellSites();
    const correct = novel.filter((a) =>
      unit.some(
        (b) =>
          a.species === b.species &&
          Math.hypot(
            ...a.position.map((v, k) => {
              const d = v - b.fractional[k] * cell[k];
              return d - Math.round(d / cell[k]) * cell[k];
            }),
          ) < 0.03,
      ),
    ).length;
    console.log(
      "ice held-out periodic extension agreement",
      correct,
      "/",
      novel.length,
      "(diagnostic, not a success assertion)",
    );
  }
}
// Proper registration and discovery are label-agnostic and not locked to axes.
const original = samplePatch("nacl").atoms;
const moved = original.map((a) => ({
  species: a.species === "Na" ? "opaque-A" : "opaque-B",
  position: transform(pose, a.position),
}));
const a = drain(discover(original, { epsilon: 0.03, neighbors: 6 })),
  b = drain(discover(moved, { epsilon: 0.03, neighbors: 6 }));
assert.deepEqual(
  a.types.map((t) => t.occurrences.length).sort((a, b) => a - b),
  b.types.map((t) => t.occurrences.length).sort((a, b) => a - b),
);
const zero = drain(learnSections(a, { error: 0 }));
assert.ok(
  zero.sections.every((s) =>
    s.sites.every((p) =>
      p.intervals.every(([lo, hi]) => lo === hi && (lo === 0 || lo === 1)),
    ),
  ),
);
console.log(
  "arbitrary proper rotation, opaque relabeling, zero-error calibration PASS",
);
