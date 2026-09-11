import assert from "node:assert/strict";
import { discover, learnSections } from "./learning.mjs";
import { samplePatch } from "./samples.mjs";
import { MaterialExperiment } from "./material.mjs";
import { acceptsOverlap } from "./overlap-rules.mjs";
const drain = (g) => {
  let r;
  do {
    r = g.next();
  } while (!r.done);
  return r.value;
};
for (const id of ["nacl", "ice"]) {
  const g = drain(discover(samplePatch(id).atoms, { epsilon: 0.03 }));
  const m = drain(learnSections(g));
  assert.equal(m.connectionPolicy, "observed-only");
  const obs = g.types.flatMap((t) =>
    t.occurrences.map((o) => ({
      type: t.id,
      anchor: o.anchor,
      sites: o.mapping.map((k) => ({ id: o.ids[k], ...g.atoms[o.ids[k]] })),
    })),
  );
  let positives = 0;
  for (const a of obs)
    for (const b of obs) {
      if (
        a === b ||
        a.anchor === b.anchor ||
        !a.sites.some((s) => b.sites.some((t) => t.id === s.id))
      )
        continue;
      positives++;
      assert(acceptsOverlap(m.overlapRules, a.type, b.type, a.sites, b.sites));
    }
  assert.equal(positives, m.overlapRules.pairs);
  const e = new MaterialExperiment(g, m, {
    maximumPoints: 20000,
    maximumCandidates: 40000,
  });
  for (let i = 0; i < 30; i++) {
    const ev = e.step();
    assert(e.snapshot(false).overlapValidation.legal);
    if (["unknown", "budget", "complete", "exhausted"].includes(ev.kind)) break;
  }
  const s = e.snapshot(false);
  assert(s.validation.legal);
  if (id === "nacl") assert.equal(s.atoms.length, 30);
  if (id === "ice") assert(s.overlapChecks.rejections > 0);
  console.log(
    JSON.stringify({
      sample: id,
      positivePairs: positives,
      classes: m.overlapRules.classes,
      atoms: s.atoms.length,
      overlapAudit: s.overlapValidation,
      checks: s.overlapChecks,
      status: s.status,
    }),
  );
}
