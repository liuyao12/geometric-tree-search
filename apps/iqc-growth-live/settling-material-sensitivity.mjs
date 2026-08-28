const finiteDifference = (after, before) => Number.isFinite(after) && Number.isFinite(before)
  ? after - before : null;

export const SETTLING_MATERIAL_FIELDS = Object.freeze([
  Object.freeze({ id: "coordinationDeficit", label: "coordination deficit" }),
  Object.freeze({ id: "packingDensity", label: "local packing" }),
  Object.freeze({ id: "localOrder", label: "local q6 / |psi6|" }),
  Object.freeze({ id: "centrosymmetry", label: "inversion asymmetry" }),
  Object.freeze({ id: "peakProminence", label: "S(q) peak prominence" }),
  Object.freeze({ id: "radiusOfGyrationAngstrom", label: "radius of gyration" }),
  Object.freeze({ id: "maximumExtentAngstrom", label: "maximum extent" }),
  Object.freeze({ id: "relativeShapeAnisotropy", label: "shape anisotropy" }),
]);

export function compareSettlingMaterialFingerprints(asPlaced, projected, tolerance = 1e-9) {
  if (!asPlaced || !projected) throw new Error("settling material comparison requires two fingerprints");
  const deltas = Object.fromEntries(SETTLING_MATERIAL_FIELDS.map(({ id }) =>
    [id, finiteDifference(projected[id], asPlaced[id])]));
  const phenotypeChanged = asPlaced.phenotype !== projected.phenotype;
  const intrinsicDimensionChanged = asPlaced.intrinsicDimension !== projected.intrinsicDimension;
  const changedFields = [
    ...(phenotypeChanged ? ["phenotype"] : []),
    ...(intrinsicDimensionChanged ? ["intrinsicDimension"] : []),
    ...SETTLING_MATERIAL_FIELDS.filter(({ id }) =>
      Number.isFinite(deltas[id]) && Math.abs(deltas[id]) > tolerance).map(({ id }) => id),
  ];
  return {
    changedFields,
    changedFieldCount: changedFields.length,
    deltas,
    phenotypeChanged,
    intrinsicDimensionChanged,
    atomCountInvariant: asPlaced.atomCount === projected.atomCount,
    chemistryInvariant: asPlaced.chemistryDigest === projected.chemistryDigest,
    coordinatesEmbedded: false,
    targetUsed: false,
    usedForAdmission: false,
    usedForRanking: false,
    executed: false,
    physicalPotentialUsed: false,
    energyInferred: false,
    kineticsInferred: false,
    physicalTimeModeled: false,
  };
}
