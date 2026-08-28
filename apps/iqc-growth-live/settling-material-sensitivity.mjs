const finiteDifference = (after, before) => Number.isFinite(after) && Number.isFinite(before)
  ? after - before : null;

export const SETTLING_MATERIAL_FIELDS = Object.freeze([
  Object.freeze({ id: "coordinationDeficit", label: "coordination deficit", unit: "fraction" }),
  Object.freeze({ id: "packingDensity", label: "local packing", unit: "relative density" }),
  Object.freeze({ id: "localOrder", label: "local q6 / |psi6|", unit: "magnitude" }),
  Object.freeze({ id: "centrosymmetry", label: "inversion asymmetry", unit: "amplitude" }),
  Object.freeze({ id: "peakProminence", label: "S(q) peak prominence", unit: "contrast" }),
  Object.freeze({ id: "radiusOfGyrationAngstrom", label: "radius of gyration", unit: "angstrom" }),
  Object.freeze({ id: "maximumExtentAngstrom", label: "maximum extent", unit: "angstrom" }),
  Object.freeze({ id: "relativeShapeAnisotropy", label: "shape anisotropy", unit: "kappa squared" }),
]);

export const SETTLING_CATEGORICAL_FIELDS = Object.freeze([
  Object.freeze({ id: "phenotype", label: "shape phenotype", unit: "category" }),
  Object.freeze({ id: "intrinsicDimension", label: "structural dimension", unit: "category" }),
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

const armChanged = (arm, fieldId, tolerance) => SETTLING_CATEGORICAL_FIELDS
  .some((field) => field.id === fieldId)
  ? fieldId === "phenotype" ? arm.materialConsequence.phenotypeChanged
    : arm.materialConsequence.intrinsicDimensionChanged
  : Number.isFinite(arm.materialConsequence.deltas[fieldId])
    && Math.abs(arm.materialConsequence.deltas[fieldId]) > tolerance;

function numericTrend(cells, tolerance) {
  const certified = cells.filter((cell) => cell.certified);
  if (!certified.length) return "projection-inactive";
  const changed = certified.filter((cell) => cell.changed);
  if (!changed.length) return "invariant-across-certified";
  if (certified.length < 2) return "single-certified-change";
  const signs = new Set(changed.map((cell) => Math.sign(cell.delta)));
  if (signs.size > 1) return "direction-changing";
  const magnitudes = certified.map((cell) => Math.abs(cell.delta || 0));
  const monotone = magnitudes.every((value, index) => index === 0
    || value >= magnitudes[index - 1] - tolerance);
  return monotone ? "monotone-with-allowance" : "same-direction-nonmonotone";
}

function categoricalTrend(cells) {
  const certified = cells.filter((cell) => cell.certified);
  if (!certified.length) return "projection-inactive";
  const changed = certified.filter((cell) => cell.changed).length;
  if (!changed) return "invariant-across-certified";
  return changed === certified.length ? "categorical-shift" : "threshold-categorical-shift";
}

export function buildSettlingMaterialResponseMatrix(arms, tolerance = 1e-9) {
  if (!Array.isArray(arms) || arms.length < 2) throw new Error("settling response matrix requires arm records");
  const modes = arms.map((arm) => arm.mode);
  if (new Set(modes).size !== modes.length) throw new Error("settling response matrix modes must be unique");
  const fieldDefinitions = [...SETTLING_CATEGORICAL_FIELDS, ...SETTLING_MATERIAL_FIELDS];
  const rows = fieldDefinitions.map((field) => {
    const categorical = field.unit === "category";
    const cells = arms.map((arm) => {
      const delta = categorical ? null : arm.materialConsequence.deltas[field.id];
      return {
        mode: arm.mode,
        attempted: Boolean(arm.attempted),
        certified: Boolean(arm.attempted && arm.accepted),
        changed: armChanged(arm, field.id, tolerance),
        delta: Number.isFinite(delta) ? delta : null,
      };
    });
    const maximumMagnitude = categorical ? null : Math.max(0,
      ...cells.filter((cell) => Number.isFinite(cell.delta)).map((cell) => Math.abs(cell.delta)));
    cells.forEach((cell) => { cell.normalizedMagnitude = categorical
      ? cell.changed ? 1 : 0
      : maximumMagnitude > tolerance && Number.isFinite(cell.delta)
        ? Math.abs(cell.delta) / maximumMagnitude : 0; });
    const changedModes = cells.filter((cell) => cell.changed).map((cell) => cell.mode);
    return {
      ...field,
      categorical,
      cells,
      maximumMagnitude,
      changedModes,
      sensitive: changedModes.length > 0,
      trend: categorical ? categoricalTrend(cells) : numericTrend(cells, tolerance),
    };
  });
  const projected = arms.filter((arm) => arm.attempted);
  const acceptedModes = projected.filter((arm) => arm.accepted).map((arm) => arm.mode);
  const acceptanceBits = projected.map((arm) => Boolean(arm.accepted));
  const firstAccepted = acceptanceBits.indexOf(true);
  const thresholdLike = firstAccepted >= 0 && acceptanceBits.slice(firstAccepted).every(Boolean)
    && acceptanceBits.slice(0, firstAccepted).every((value) => !value);
  const gatePattern = !acceptedModes.length ? "no-projected-arm-certified"
    : acceptedModes.length === projected.length ? "all-projected-arms-certified"
      : thresholdLike ? "allowance-threshold" : "non-nested-certification";
  return {
    modes,
    rows,
    sensitiveFieldCount: rows.filter((row) => row.sensitive).length,
    invariantFieldCount: rows.filter((row) => !row.sensitive).length,
    acceptedModes,
    gatePattern,
    normalization: "within-field maximum absolute delta only; no cross-unit scalar",
    coordinatesEmbedded: false,
    targetUsed: false,
    usedForAdmission: false,
    usedForRanking: false,
    physicalPotentialUsed: false,
    energyInferred: false,
    physicalTimeModeled: false,
  };
}

function historyPattern(field, leapRows, tolerance) {
  const compatible = leapRows.filter((entry) => entry.cells.some((cell) =>
    cell.mode !== "off" && cell.certified));
  if (!compatible.length) return "no-compatible-projections";
  const sensitive = compatible.filter((entry) => entry.sensitive);
  if (!sensitive.length) return "robust-invariant";
  if (field.unit === "category") return sensitive.length === compatible.length
    ? "persistent-categorical-shift" : "intermittent-categorical-shift";
  const changed = sensitive.flatMap((entry) => entry.cells.filter((cell) =>
    cell.mode !== "off" && cell.certified && cell.changed && Number.isFinite(cell.delta)));
  const signs = new Set(changed.filter((cell) => Math.abs(cell.delta) > tolerance)
    .map((cell) => Math.sign(cell.delta)));
  if (signs.size > 1) return "direction-reversing-across-leaps";
  return sensitive.length === compatible.length
    ? "consistent-direction-across-leaps" : "intermittent-sensitivity";
}

export function buildSettlingMaterialResponseHistory(leaps, tolerance = 1e-9) {
  if (!Array.isArray(leaps)) throw new Error("settling response history requires leap records");
  const retained = leaps.map((leap, retainedIndex) => {
    const audit = leap?.settlingSensitivity;
    if (!audit?.arms?.length) return null;
    const matrix = audit.materialResponseMatrix
      || buildSettlingMaterialResponseMatrix(audit.arms, tolerance);
    return {
      leapIndex: leap.index ?? retainedIndex + 1,
      retainedIndex,
      status: leap.status || "unknown",
      selectedMode: audit.selectedMode,
      selectedExecutionMatchesPreview: audit.selectedExecutionMatchesPreview,
      matrix,
    };
  }).filter(Boolean);
  const fieldDefinitions = [...SETTLING_CATEGORICAL_FIELDS, ...SETTLING_MATERIAL_FIELDS];
  const fields = fieldDefinitions.map((field) => {
    const leapRows = retained.map((leap) => {
      const row = leap.matrix.rows.find((entry) => entry.id === field.id);
      if (!row) return null;
      return {
        leapIndex: leap.leapIndex,
        retainedIndex: leap.retainedIndex,
        status: leap.status,
        selectedMode: leap.selectedMode,
        selectedExecutionMatchesPreview: leap.selectedExecutionMatchesPreview,
        sensitive: row.sensitive,
        trend: row.trend,
        cells: row.cells.map((cell) => ({ ...cell })),
      };
    }).filter(Boolean);
    const categorical = field.unit === "category";
    const maximumMagnitude = categorical ? null : Math.max(0,
      ...leapRows.flatMap((entry) => entry.cells)
        .filter((cell) => cell.mode !== "off" && cell.certified && Number.isFinite(cell.delta))
        .map((cell) => Math.abs(cell.delta)));
    leapRows.forEach((entry) => entry.cells.forEach((cell) => {
      cell.normalizedHistoryMagnitude = categorical ? cell.changed ? 1 : 0
        : maximumMagnitude > tolerance && cell.certified && Number.isFinite(cell.delta)
          ? Math.abs(cell.delta) / maximumMagnitude : 0;
    }));
    const compatibleLeapCount = leapRows.filter((entry) => entry.cells.some((cell) =>
      cell.mode !== "off" && cell.certified)).length;
    const sensitiveLeapCount = leapRows.filter((entry) => entry.sensitive).length;
    return {
      ...field,
      categorical,
      maximumMagnitude,
      leaps: leapRows,
      compatibleLeapCount,
      sensitiveLeapCount,
      pattern: historyPattern(field, leapRows, tolerance),
    };
  });
  return {
    retainedLeapCount: retained.length,
    retainedLeapIndices: retained.map((entry) => entry.leapIndex),
    fields,
    sensitiveFieldCount: fields.filter((field) => field.sensitiveLeapCount > 0).length,
    normalization: "within one material field across retained leaps and certified arms only; no cross-unit scalar",
    sequenceMeaning: "discrete retained GCTS search order; not independent specimens or physical time",
    retainedWindowOnly: true,
    coordinatesEmbedded: false,
    targetUsed: false,
    usedForAdmission: false,
    usedForRanking: false,
    physicalPotentialUsed: false,
    energyInferred: false,
    kineticsInferred: false,
    physicalTimeModeled: false,
  };
}
