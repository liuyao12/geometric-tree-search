import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const root = new URL("../", import.meta.url);
const read = (path) => readFileSync(new URL(path, root), "utf8");
const app = read("apps/iqc-growth-live/app.js");
const html = read("apps/iqc-growth-live/index.html");
const compatibility = read("iqc-growth-live/index.html");
const style = read("apps/iqc-growth-live/style.css");
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
  assert.match(document, /Embedded Simpson work must close endpoint ΔU globally, within each five-image quarter-path panel, at every eligible five-point force-versus-energy tangent, and independently for active Coulomb, Born–Mayer, dispersion, and induction channels/);
  for (const id of ["modelForceResponseDiagnostic", "modelForceResponseComponent",
    "modelForceResponsePlot", "modelForceResponsePointState"]) {
    assert.match(document, new RegExp(`id="${id}"`));
  }
}
for (const id of ["modelForceCartesianGradientState",
  "modelForceCartesianGradientGrid", "modelForceCartesianGradientPointState"]) {
  assert.match(html, new RegExp(`id="${id}"`));
}
assert.match(html, /worst normalized residual by direction/);

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
  "modelForceSmoothBranchPassed",
  "modelForceStateStableAcrossImages",
  "modelForceAnalyticReachTopologyPassed",
  "modelForceComponentWorkEnergyClosuresPassed",
  "modelForceComponentWorkEnergyClosures",
  "modelForceActiveWorkEnergyComponentCount",
  "modelForcePanelWorkEnergyClosurePassed",
  "modelForcePanelWorkEnergyClosure",
  "modelForceWorkEnergyPanelCount",
  "modelForceFailedWorkEnergyPanelIndices",
  "modelForceInteriorGradientConsistencyPassed",
  "modelForceInteriorGradientConsistency",
  "modelForceInteriorGradientEligibleImageCount",
  "modelForceFailedInteriorGradientImageIndices",
  "modelForceEndpointCartesianGradientPassed",
  "modelForceEndpointCartesianGradientAudit",
  "modelForceCartesianGradientEndpointCount",
  "modelForceCartesianGradientCoordinateCount",
  "modelForceCartesianGradientProbeEvaluationCount",
  "modelForceFailedCartesianGradientEndpointImageIndices",
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
  "renderModelForceResponseDiagnostic",
  "modelForceCartesianSelectedKey",
  "model-force-cartesian-cell",
  "energyProfileElectronVolt",
  "response-tangent-point",
]) assert.ok(app.includes(token), token);

for (const token of [".model-force-response-diagnostic",
  ".model-force-response-legend", ".response-tangent-point",
  ".model-force-cartesian-grid", ".model-force-cartesian-cell"]) {
  assert.ok(style.includes(token), token);
}

for (const token of [
  "incrementalFinitePointChargeElectrostatics",
  "auditModelForceRelaxationEnergyDescent",
  "auditModelForceRelaxationOutcome",
  "auditPanelResolvedForceEnergyPathClosure",
  "auditInteriorForceEnergyGradientConsistency",
  "auditCartesianForceEnergyGradient",
  "energyProbeForceMode: \"omitted\"",
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
  "auditFiniteReachPathTopology",
  "auditComponentForceEnergyPathClosures",
  "componentWorkEnergyClosuresPassed",
  "inductionForceWorkNumericalUncertaintyElectronVolt",
  "smoothModelBranchPassed",
  "analyticReachTopologyPassed",
  "modelStateStableAcrossImages",
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
assert.match(atlas, /"48", "Continuous finite-model branch"/);
assert.match(atlas, /"49", "Component-resolved work closure"/);
assert.match(atlas, /"50", "Panel-resolved work closure"/);
assert.match(atlas, /"51", "Interior force–energy tangent"/);
assert.match(atlas, /"52", "Interactive local-response microscope"/);
assert.match(atlas, /"53", "Endpoint Cartesian-gradient audit"/);
assert.match(atlas, /"54", "Interactive Cartesian force compass"/);
assert.match(readme, /Build 437 · force-residual redistribution gate/);
assert.match(readme, /Build 438 · population force-resultant and torque gate/);
assert.match(readme, /Build 439 · intermediate response-path certificate/);
assert.match(readme, /Build 440 · affine force-moment redistribution gate/);
assert.match(readme, /Build 441 · finite-path work–energy closure/);
assert.match(readme, /Build 442 · nested work-quadrature convergence/);
assert.match(readme, /Build 443 · continuous finite-model branch certificate/);
assert.match(readme, /Build 444 · component-resolved work–energy closure/);
assert.match(readme, /Build 445 · panel-resolved work–energy closure/);
assert.match(readme, /Build 446 · interior force–energy tangent consistency/);
assert.match(readme, /Build 447 · interactive local-response microscope/);
assert.match(readme, /Build 448 · endpoint Cartesian-gradient closure/);
assert.match(benchmark, /Build 448: Endpoint Cartesian-gradient closure/);
assert.match(readme, /Build 449 · interactive Cartesian force compass/);
assert.match(benchmark, /Build 449: Interactive Cartesian force compass/);

console.log("model-force relaxation portal contract passed");
