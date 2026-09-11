import assert from "node:assert/strict";
import { discover, learnSections } from "./learning.mjs";
import { samplePatch } from "./samples.mjs";
import { MaterialExperiment } from "./material.mjs";
import { axisAngle, transform } from "./geometry.mjs";
import {
  ICE_VIII_BROWSER_FIXTURE,
  iceViiiUnitCellSites,
} from "../iqc-growth-live/ice-viii-browser-fixture.js";
const drain = (g) => {
  let r;
  do {
    r = g.next();
  } while (!r.done);
  return r.value;
};
const atoms = samplePatch("ice").atoms;
const g = drain(discover(atoms, { epsilon: 0.03 }));
assert(g.types.some((t) => t.role === "local" && t.sites.length === 3));
assert(g.types.some((t) => t.role === "connector" && t.sites.length > 3));
assert(
  g.discovery.coverage.anchoredAtoms >
    g.discovery.initialCoverage.anchoredAtoms,
);
assert(
  g.discovery.coverage.supportComponents <
    g.discovery.initialCoverage.supportComponents,
);
assert.equal(g.discovery.coverage.missingAnchors.length, 0);
assert(g.discovery.contextCompletion.classes > 0);
assert(g.types.some((t) => t.role === "context"));
assert(g.connections.length > 0);
for (const t of g.types)
  for (const o of t.occurrences) {
    assert.equal(new Set(o.ids).size, o.ids.length);
    assert(o.residual <= g.epsilon);
    for (let k = 0; k < t.sites.length; k++) {
      const actual = atoms[o.ids[o.mapping[k]]];
      const p = transform(o.pose, t.sites[k].position);
      assert.equal(t.sites[k].species, actual.species);
      assert(
        Math.hypot(...p.map((x, j) => x - actual.position[j])) <=
          g.epsilon + 1e-9,
      );
    }
  }
const pose = { r: axisAngle([2, -1, 3], 0.631), t: [10, -3, 7] };
const moved = drain(
  discover(
    atoms.toReversed().map((a) => ({
      species: a.species === "O" ? "label-X" : "label-Y",
      position: transform(pose, a.position),
    })),
    { epsilon: 0.03 },
  ),
);
assert.deepEqual(
  moved.types.map((t) => t.sites.length).sort((a, b) => a - b),
  g.types.map((t) => t.sites.length).sort((a, b) => a - b),
);
const e = new MaterialExperiment(
  g,
  drain(learnSections(g, { observedOnly: false })),
  {
    // Historical connector-only control.
    maximumPoints: 20000,
    maximumCandidates: 40000,
  },
);
for (let i = 0; i < 100; i++) {
  const event = e.step();
  assert(
    !["unknown", "budget", "complete", "exhausted"].includes(event.kind),
    JSON.stringify(event),
  );
}
const s = e.snapshot();
assert.equal(s.atoms.length, 100);
assert(s.validation.legal);
assert(s.atoms.some((a) => a.species === "O"));
assert(s.atoms.some((a) => a.species === "D"));
// Independent evaluation only. Neither cell nor extension enters discovery/search.
const unit = iceViiiUnitCellSites(),
  cell = ICE_VIII_BROWSER_FIXTURE.cellAngstrom;
const matched = s.atoms.filter((a) =>
  unit.some(
    (b) =>
      a.species === b.species &&
      Math.hypot(
        ...a.position.map((v, k) => {
          const d = v + s.seedOrigin.origin[k] - b.fractional[k] * cell[k];
          return d - Math.round(d / cell[k]) * cell[k];
        }),
      ) < 0.03,
  ),
).length;
console.log(
  JSON.stringify({
    result: "PASS",
    motifs: g.types.map((t) => ({ role: t.role, sites: t.sites.length })),
    coverage: g.discovery.coverage,
    grownAtoms: s.atoms.length,
    periodicReferenceMatches: matched,
    scope:
      "point legality and geometric observation replay; periodic match is diagnostic, not a success assertion",
  }),
);
