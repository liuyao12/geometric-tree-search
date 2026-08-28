const finiteDifference = (after, before) => Number.isFinite(after) && Number.isFinite(before)
  ? after - before : null;

export const SHADOW_MATERIAL_CONSEQUENCE_FIELDS = Object.freeze([
  Object.freeze({ id: "atomCount", label: "whole-state atoms", unit: "atoms" }),
  Object.freeze({ id: "radiusOfGyrationAngstrom", label: "whole-state Rg", unit: "angstrom" }),
  Object.freeze({ id: "maximumExtentAngstrom", label: "whole-state extent", unit: "angstrom" }),
  Object.freeze({ id: "relativeShapeAnisotropy", label: "shape anisotropy", unit: "kappa squared" }),
  Object.freeze({ id: "compositionDrift", label: "composition drift", unit: "total variation" }),
  Object.freeze({ id: "surfaceIntegrity", label: "interface completion", unit: "dimensionless" }),
]);

export function compareShadowMaterialFingerprints(baseline, omitted) {
  if (!baseline || !omitted) throw new Error("shadow material comparison requires two fingerprints");
  const deltas = Object.fromEntries(SHADOW_MATERIAL_CONSEQUENCE_FIELDS.map(({ id }) =>
    [id, finiteDifference(omitted[id], baseline[id])]));
  return {
    baselinePhenotype: baseline.phenotype || "unresolved",
    omittedPhenotype: omitted.phenotype || "unresolved",
    phenotypeChanged: baseline.phenotype !== omitted.phenotype,
    baselineIntrinsicDimension: baseline.intrinsicDimension ?? null,
    omittedIntrinsicDimension: omitted.intrinsicDimension ?? null,
    intrinsicDimensionChanged: baseline.intrinsicDimension !== omitted.intrinsicDimension,
    deltas,
    coordinatesEmbedded: false,
    targetUsed: false,
    executed: false,
    usedForAdmission: false,
    usedForRanking: false,
    physicalTimeModeled: false,
    energyInferred: false,
    causalEffectIdentified: false,
  };
}
