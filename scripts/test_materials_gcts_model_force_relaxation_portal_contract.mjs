import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const root = new URL("../", import.meta.url);
const read = (path) => readFileSync(new URL(path, root), "utf8");
const app = read("apps/iqc-growth-live/app.js");
const html = read("apps/iqc-growth-live/index.html");
const compatibility = read("iqc-growth-live/index.html");
const moduleSource = read("apps/iqc-growth-live/model-force-relaxation-seed.mjs");
const readme = read("apps/iqc-growth-live/README.md");
const benchmark = read("docs/projects/materials-recursive-gcts-benchmark.md");
const atlas = read("apps/iqc-growth-live/evidence-atlas.js");

for (const document of [html, compatibility]) {
  assert.match(document, /value="model-force">Finite interaction −∇U seed/);
  assert.match(document, /complete selected-model energy gradient/);
}

for (const token of [
  "buildModelForceRelaxationSeed",
  '"model-force": Object.freeze',
  "finiteInteractionModelForceSeed",
  "modelForceSeedEnergyGradientComplete",
  "modelForceSeedInductionEnergyEvaluations",
  "modelForceSeedInductionRichardsonErrorElectronVoltPerAngstrom",
  "modelForceSeedAvailable",
  "modelForceSeedAccepted",
  "contactAngleStrainDecreased: strainDecreased",
  "hardExclusionPassed, coordinationCapacityPassed",
  "angularEnvelopePassed, publicBoundaryPassed",
  "exactClusterTopologyRetained: true",
  "properPortTopologyRetained: true",
  "forceIntegrated: false",
  "elapsedPhysicalTimeModeled: false",
]) assert.ok(app.includes(token), token);

for (const token of [
  "incrementalFinitePointChargeElectrostatics",
  "pairInteractionForceIsNegativeEnergyGradient",
  "forceMagnitudeP90",
  "boundedForceSeedOffset",
  "candidateGeometryChanged: false",
  "forceIntegratedAsTime: false",
  "energyMinimized: false",
  "targetUsed: false",
]) assert.ok(moduleSource.includes(token), token);

assert.match(readme, /Build 431 · interaction forces can seed certified geometric settling/);
assert.match(benchmark, /Force-seeded certified geometric settling \(Build 431\)/);
assert.match(atlas, /"36", "Force-seeded certified geometry leap"/);

console.log("model-force relaxation portal contract passed");
