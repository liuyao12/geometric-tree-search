import {
  Worker,
  isMainThread,
  parentPort,
  workerData,
} from "node:worker_threads";
import { writeFileSync } from "node:fs";
import { sampleCatalog, samplePatch } from "./samples.mjs";
import { discover, learnSections } from "./learning.mjs";
import { MaterialExperiment } from "./material.mjs";
import { CoronaCheckpoints } from "./coronas.mjs";
import { compareStructure } from "./metrics.mjs";
import { checkPeriodicReference } from "./reference-check.mjs";
const drain = (g) => {
  let r;
  do {
    r = g.next();
  } while (!r.done);
  return r.value;
};
if (!isMainThread) {
  const { id, neighbors, epsilon = 0.03 } = workerData;
  const start = performance.now();
  const sample = samplePatch(id);
  const grammar = drain(discover(sample.atoms, { epsilon, neighbors }));
  const result = {
    id,
    neighbors,
    epsilon,
    inputAtoms: sample.atoms.length,
    types: grammar.types.length,
  };
  if (!grammar.types.length)
    parentPort.postMessage({
      ...result,
      outcome: "unsupported",
      status: "no recurring supports",
      atoms: 1,
    });
  else {
    const marking = drain(learnSections(grammar));
    const e = new MaterialExperiment(grammar, marking, {
      maximumPoints: 40000,
      maximumCandidates: 80000,
    });
    let event,
      steps = 0;
    const until = performance.now() + 12000;
    for (; steps < 400 && performance.now() < until; steps++) {
      event = e.step();
      if (["unknown", "complete", "exhausted", "budget"].includes(event.kind))
        break;
    }
    const state = e.snapshot();
    e.engine.auditGraph();
    const reference = sample.atoms.map((a) => ({
      ...a,
      position: a.position.map((v, k) => v - state.seedOrigin.origin[k]),
    }));
    const metrics = compareStructure(reference, state.atoms);
    const labels = [...new Set(sample.atoms.map((a) => a.species))];
    const composition = Object.fromEntries(
      labels.map((label) => [
        label,
        state.atoms.filter((a) => a.species === label).length,
      ]),
    );
    parentPort.postMessage({
      ...result,
      outcome:
        state.atoms.length >= 64 &&
        labels.every((l) => composition[l] > 0) &&
        state.validation.legal &&
        state.overlapValidation?.legal
          ? "finite growth verified"
          : "unresolved",
      status: state.status,
      stop: event?.kind,
      message: event?.message,
      atoms: state.atoms.length,
      steps,
      composition,
      periodicReference: checkPeriodicReference(sample, e, state),
      completedCorona: new CoronaCheckpoints().progress(e.engine).completed,
      beyondInputCount: state.atoms.length > sample.atoms.length,
      metrics: {
        status: metrics.status,
        rdfError: metrics.rdfError,
        compositionTV: metrics.compositionTV,
        angleTV: metrics.angleTV,
      },
      legal: state.validation.legal,
      overlapsLegal: state.overlapValidation?.legal,
      seconds: (performance.now() - start) / 1000,
    });
  }
} else {
  const results = [];
  for (const [id] of sampleCatalog)
    for (const neighbors of [0]) {
      const row = await new Promise((resolve) => {
        const w = new Worker(new URL(import.meta.url), {
          workerData: { id, neighbors },
        });
        const timer = setTimeout(() => {
          w.terminate();
          resolve({ id, neighbors, status: "wall-time limit" });
        }, 45000);
        w.once("message", (r) => {
          clearTimeout(timer);
          resolve(r);
        });
        w.once("error", (e) => {
          clearTimeout(timer);
          resolve({ id, neighbors, status: "error", error: e.message });
        });
      });
      results.push(row);
      console.log(JSON.stringify(row));
    }
  if (process.argv[2])
    writeFileSync(
      process.argv[2],
      JSON.stringify(
        {
          schema: "strict-sample-audit/1",
          protocol: {
            epsilon: 0.03,
            observedOnly: true,
            maximumSteps: 400,
            growthSeconds: 12,
            caseWallSeconds: 45,
            maximumPoints: 40000,
            maximumCandidates: 80000,
            minimumAtoms: 64,
            caveat:
              "Finite growth verified means >=64 actual atoms, all input labels represented, independent point and overlap legality, and graph consistency. It is NOT proof of reconstruction, corona completion or indefinite extendability. RDF/composition/angular comparisons use the training crop, not held-out data. Default adaptive discovery includes disclosed broader contexts for disconnected supports.",
          },
          results,
        },
        null,
        2,
      ) + "\n",
    );
  const regressions = results.filter(
    (r) =>
      !["cdyb", "asi", "glass"].includes(r.id) &&
      (r.outcome !== "finite growth verified" ||
        (r.periodicReference && r.periodicReference.fraction !== 1)),
  );
  if (regressions.length) {
    console.error("Growth/reference regressions", regressions);
    process.exitCode = 1;
  }
  console.log(
    `${results.filter((r) => r.outcome === "finite growth verified").length}/${results.length} finite-growth checks passed; unresolved cases are not successes.`,
  );
}
