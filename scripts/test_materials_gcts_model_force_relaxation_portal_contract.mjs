import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const root = new URL("../", import.meta.url);
const read = (path) => readFileSync(new URL(path, root), "utf8");
const app = read("apps/iqc-growth-live/app.js");
const html = read("apps/iqc-growth-live/index.html");
const compatibility = read("iqc-growth-live/index.html");
const moduleSource = read("apps/iqc-growth-live/model-force-relaxation-seed.mjs");
const shellSource = read("apps/iqc-growth-live/anchored-interface-shells.mjs");
const sweptSource = read("apps/iqc-growth-live/linear-swept-exclusion.mjs");
const readme = read("apps/iqc-growth-live/README.md");
const benchmark = read("docs/projects/materials-recursive-gcts-benchmark.md");
const atlas = read("apps/iqc-growth-live/evidence-atlas.js");

for (const document of [html, compatibility]) {
  assert.match(document, /value="model-force">Finite interaction −∇U · energy \+ force audit/);
  assert.match(document, /value="model-force-interface">Finite −∇U interface shell/);
  assert.match(document, /value="model-force-layered-interface">Finite −∇U two-shell response/);
  assert.match(document, /energy, force, population, resultant, torque, and centered symmetric force-moment descent across thirteen/);
}

for (const token of [
  "buildModelForceRelaxationSeed",
  '"model-force": Object.freeze',
  '"model-force-layered-interface": Object.freeze',
  "finiteInteractionModelForceSeed",
  "modelForceSeedEnergyGradientComplete",
  "modelForceSeedInductionEnergyEvaluations",
  "modelForceSeedInductionRichardsonErrorElectronVoltPerAngstrom",
  "modelForceSeedAvailable",
  "modelForceSeedAccepted",
  "modelForceSeedHeterogeneousDisplacementCaps",
  "modelForceAuditedFreshSites",
  "modelForceAuditedSubstrateSites",
  "substrateShellCount",
  "substrateShellPopulations",
  "substrateShellDisplacementCapsAngstrom",
  "substrateShellMaximumDisplacementsAngstrom",
  "anchoredInterfaceResponsePassed",
  "continuumElasticityClaimed: false",
  "mechanicalEquilibriumClaimed: false",
  "modelForceEnergyDescentAvailable",
  "modelForceEnergyDecreased",
  "modelForceEnergyBeforeElectronVolt",
  "modelForceEnergyAfterElectronVolt",
  "modelForceEnergyChangeElectronVolt",
  "modelForceEnergyResponseConsistent",
  "modelForceResidualDecreased",
  "modelForceResidualRedistributionPassed",
  "modelForceResultantRedistributionPassed",
  "modelForceSymmetricMomentRedistributionPassed",
  "modelForceGroupSymmetricMomentsAvailable",
  "modelForceGroupResultantsAvailable",
  "modelForceGroupResiduals",
  "modelForceGroupCount",
  "modelForceGroupLabelsFrozenBeforeProposal",
  "modelForceResponsePathAccepted",
  "modelForceResponsePathImageCount",
  "modelForceResponsePathSegments",
  "modelForceWorkEnergyClosurePassed",
  "modelForceWorkSimpsonElectronVolt",
  "modelForceWorkEnergyClosureResidualElectronVolt",
  "modelForceWorkEnergyClosureToleranceElectronVolt",
  "modelForceWorkCoarseSimpsonElectronVolt",
  "modelForceWorkEnergyRichardsonErrorElectronVolt",
  "sweptHardExclusionPassed",
  "sweptHardExclusionMinimumMargin",
  "modelForceRmsBeforeEvPerAngstrom",
  "modelForceRmsAfterEvPerAngstrom",
  "modelForceP90BeforeEvPerAngstrom",
  "modelForceP90AfterEvPerAngstrom",
  "modelForceEnergyPairCountBefore",
  "modelForceEnergyPairCountAfter",
  "contactAngleStrainDecreased: strainDecreased",
  "hardExclusionPassed, sweptHardExclusionPassed",
  "coordinationCapacityPassed",
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
  "auditGroupedForceResiduals",
  "forceResidualRedistributionPassed",
  "forceResultantRedistributionPassed",
  "symmetricForceMomentRedistributionPassed",
  "forceGroupSymmetricMomentsAvailable",
  "centeredSymmetricForceMoment",
  "hydrostaticFrobeniusElectronVolt",
  "deviatoricFrobeniusElectronVolt",
  "forceGroupResultantsAvailable",
  "forceGroupResiduals",
  "forceGroupLabels",
  "auditModelForceRelaxationPath",
  "auditForceEnergyPathClosure",
  "simpsonWorkElectronVolt",
  "trapezoidWorkElectronVolt",
  "closureResidualElectronVolt",
  "quadratureDiscrepancyElectronVolt",
  "coarseSimpsonWorkElectronVolt",
  "richardsonErrorEstimateElectronVolt",
  "nestedSimpsonConvergenceAvailable: true",
  "pathParameterIsPhysicalTime: false",
]) assert.ok(moduleSource.includes(token), token);

for (const token of [
  "auditAnchoredInterfaceShells",
  "every interface-response site has a contact path to the fixed outer anchors",
  "danglingByLayer",
  "targetUsed: false",
  "not an elastic Green function",
]) assert.ok(shellSource.includes(token), token);

for (const token of [
  "auditLinearSweptExclusion",
  "analyticLinearClosestApproach: true",
  "conservativeDirectionalExclusionUpperBound: true",
  "sampledOnly: false",
  "targetUsed: false",
]) assert.ok(sweptSource.includes(token), token);

assert.match(readme, /Build 433 · a settling leap must reduce residual force/);
assert.match(benchmark, /Emitted-site force-residual descent \(Build 433\)/);
assert.match(atlas, /"38", "Residual-force descent gate"/);
assert.match(atlas, /"41", "Anchored two-shell interface response"/);
assert.match(atlas, /"42", "Force-residual redistribution gate"/);
assert.match(atlas, /"43", "Population force-resultant and torque gate"/);
assert.match(atlas, /"44", "Intermediate response-path certificate"/);
assert.match(atlas, /"45", "Centered symmetric force-moment gate"/);
assert.match(atlas, /"46", "Finite-path work–energy closure"/);
assert.match(atlas, /"47", "Nested work-quadrature convergence"/);
assert.match(readme, /Build 437 · force-residual redistribution gate/);
assert.match(readme, /Build 438 · population force-resultant and torque gate/);
assert.match(readme, /Build 439 · intermediate response-path certificate/);
assert.match(readme, /Build 440 · affine force-moment redistribution gate/);
assert.match(readme, /Build 441 · finite-path work–energy closure/);
assert.match(readme, /Build 442 · nested work-quadrature convergence/);

console.log("model-force relaxation portal contract passed");
