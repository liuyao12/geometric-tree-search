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
  assert.match(document, /value="model-force">Finite interaction −∇U · energy \+ force audit/);
  assert.match(document, /value="model-force-interface">Finite −∇U interface shell/);
  assert.match(document, /RMS\/p90 force residuals/);
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
  "modelForceSeedHeterogeneousDisplacementCaps",
  "modelForceAuditedFreshSites",
  "modelForceAuditedSubstrateSites",
  "modelForceEnergyDescentAvailable",
  "modelForceEnergyDecreased",
  "modelForceEnergyBeforeElectronVolt",
  "modelForceEnergyAfterElectronVolt",
  "modelForceEnergyChangeElectronVolt",
  "modelForceEnergyResponseConsistent",
  "modelForceResidualDecreased",
  "modelForceRmsBeforeEvPerAngstrom",
  "modelForceRmsAfterEvPerAngstrom",
  "modelForceP90BeforeEvPerAngstrom",
  "modelForceP90AfterEvPerAngstrom",
  "modelForceEnergyPairCountBefore",
  "modelForceEnergyPairCountAfter",
  "contactAngleStrainDecreased: strainDecreased",
  "hardExclusionPassed, coordinationCapacityPassed",
  "angularEnvelopePassed, publicBoundaryPassed",
  "exactClusterTopologyRetained: true",
  "exactClusterGeometryRetained: !spec.interfaceShell",
  "discreteClusterSiteIdentityRetained",
  "properPortTopologyRetained: true",
  "forceIntegrated: false",
  "elapsedPhysicalTimeModeled: false",
]) assert.ok(app.includes(token), token);

for (const token of [
  "incrementalFinitePointChargeElectrostatics",
  "auditModelForceRelaxationEnergyDescent",
  "auditModelForceRelaxationOutcome",
  "pairInteractionForceIsNegativeEnergyGradient",
  "forceMagnitudeP90",
  "boundedForceSeedOffset",
  "displacementCaps",
  "heterogeneousDisplacementCaps",
  "candidateGeometryChanged: false",
  "forceIntegratedAsTime: false",
  "energyMinimized: false",
  "targetUsed: false",
  "beforePairCount",
  "afterPairCount",
  "responseConsistent",
  "forceResidualDecreased",
  "rmsForceDecreased",
  "p90ForceDecreased",
]) assert.ok(moduleSource.includes(token), token);

assert.match(readme, /Build 433 · a settling leap must reduce residual force/);
assert.match(benchmark, /Emitted-site force-residual descent \(Build 433\)/);
assert.match(atlas, /"38", "Residual-force descent gate"/);

console.log("model-force relaxation portal contract passed");
