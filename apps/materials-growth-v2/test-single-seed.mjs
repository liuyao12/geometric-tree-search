import assert from "node:assert/strict";
import { writeFileSync } from "node:fs";
import { discover, learnSections } from "./learning.mjs";
import { MaterialExperiment } from "./material.mjs";
import { sampleCatalog, samplePatch } from "./samples.mjs";
import { centralSeed } from "./seed.mjs";
import { compareStructure } from "./metrics.mjs";
const drain = (g) => {
  let r;
  while (!(r = g.next()).done) {}
  return r.value;
};
const results = [];
for (const [id, name] of sampleCatalog) {
  const start = performance.now(),
    atoms = samplePatch(id).atoms,
    origin = centralSeed(atoms).origin;
  const reference = atoms.map((a) => ({
    ...a,
    position: a.position.map((v, k) => v - origin[k]),
  }));
  const grammar = drain(discover(atoms, { epsilon: 0.03, neighbors: 5 }));
  const row = {
    id,
    name,
    trainingAtoms: atoms.length,
    types: grammar.types.length,
    uncovered: grammar.residuals.length,
  };
  if (!grammar.types.length) {
    results.push({
      ...row,
      status: "no recurring supports",
      atoms: 1,
      seconds: (performance.now() - start) / 1000,
    });
    console.log(results.at(-1));
    continue;
  }
  const marking = drain(learnSections(grammar)),
    e = new MaterialExperiment(grammar, marking, {
      maximumPoints: 8000,
      maximumCandidates: 20000,
    });
  const initial = e.snapshot();
  assert.equal(initial.atoms.length, 1);
  assert.deepEqual(initial.atoms[0].position, [0, 0, 0]);
  assert.equal(initial.seedAtoms, 1);
  assert.equal(initial.options.completeCrop, false);
  assert.equal(e.observation.length, 1);
  assert.ok(initial.model.fixedMarks.every((m) => m.point === "p0"));
  if (id === "nacl") {
    // Freeze the learned library, radically alter the observation coordinates:
    // the single-seed candidate problem must remain unchanged.
    const altered = {
      ...grammar,
      atoms: grammar.atoms.map((a) => ({
        ...a,
        position: a.position.map((v) => v * 100),
      })),
    };
    const other = new MaterialExperiment(altered, marking, {
      maximumPoints: 8000,
      maximumCandidates: 20000,
    });
    assert.deepEqual(e.engine.semanticState(), other.engine.semanticState());
    assert.deepEqual(e.registry.points, other.registry.points);
  }
  const growStart = performance.now();
  let event,
    steps = 0;
  for (; steps < 160 && performance.now() - growStart < 10000; steps++) {
    event = e.step();
    if (["unknown", "complete", "exhausted", "budget"].includes(event.kind))
      break;
  }
  const state = e.snapshot();
  assert.ok(state.validation.legal);
  assert.equal(state.stats.forced, 0);
  e.engine.auditGraph();
  const checkStart = performance.now(),
    metrics = compareStructure(reference, state.atoms);
  results.push({
    ...row,
    status: state.status,
    stop: event?.kind,
    atoms: state.atoms.length,
    steps,
    seconds: (performance.now() - start) / 1000,
    initializationSeconds: (growStart - start) / 1000,
    metricSeconds: (performance.now() - checkStart) / 1000,
    metricsStatus: metrics.status,
    rdfError: metrics.rdfError,
    compositionTV: metrics.compositionTV,
    angleTV: metrics.angleTV,
    referenceWindow: metrics.reference?.atoms,
    grownWindow: metrics.generated?.atoms,
    dimension: metrics.dimension,
    legal: state.validation.legal,
    branches: state.stats.branches,
    backtracks: state.stats.backtracks,
  });
  console.log(results.at(-1));
}
const report = {
  schema: "single-seed-benchmark/1",
  protocol: {
    neighbors: 5,
    epsilon: 0.03,
    markingError: 0.05,
    maximumSteps: 160,
    searchSeconds: 10,
    maximumPoints: 8000,
    maximumCandidates: 20000,
    minimumMetricAtoms: 24,
    description:
      "One central atom, no hidden observation constraints; comparisons use the training patch, not held-out validation. Time limits are cooperative.",
  },
  results,
};
if (process.argv[2])
  writeFileSync(process.argv[2], JSON.stringify(report, null, 2) + "\n");
console.log(
  "Single-origin, no hidden patch constraints, independent legality and graph checks PASS",
);
