const CLAIM_RUNGS = Object.freeze([
  { id: "representation", label: "complete representation" },
  { id: "recurring", label: "recurring local supports" },
  { id: "reencoding", label: "frozen held-out re-encoding" },
  { id: "stationary", label: "stationary scale law" },
  { id: "autonomous", label: "autonomous unseen emission" },
]);

const RECEIPTS = Object.freeze({
  "iqc-reencoding": {
    id: "iqc-reencoding",
    shortLabel: "IQC · sealed re-encoding",
    title: "Ideal icosahedral model · frozen width-five hierarchy",
    subtitle: "Five train patches → three spatially disjoint held-out patches",
    totalAtoms: 1248,
    source: "Frozen benchmark receipt; held-out coordinates are observed only for exact matching and scoring.",
    levels: [
      { level: 1, frozenTypes: 148, activeTypes: 148, occurrences: 1495, coveredAtoms: 1220, residualAtoms: 28, maximumSupportAtoms: 78 },
      { level: 2, frozenTypes: 10, activeTypes: 10, occurrences: 85, coveredAtoms: 1033, residualAtoms: 215, maximumSupportAtoms: 78 },
      { level: 3, frozenTypes: 4, activeTypes: 4, occurrences: 29, coveredAtoms: 925, residualAtoms: 323, maximumSupportAtoms: 110 },
      { level: 4, frozenTypes: 1, activeTypes: 1, occurrences: 9, coveredAtoms: 870, residualAtoms: 378, maximumSupportAtoms: 111 },
    ],
    gates: { representation: true, recurring: true, reencoding: true, stationary: false, autonomous: false },
    stationaryCommonKeys: 0,
    autonomousEmittedAtoms: 0,
    diagnosis: "Every held-out atom remains exactly represented by active macros plus coordinate-bearing residual terminals. Type and production topology nevertheless contracts 148 → 10 → 4 → 1, support amplification never exceeds 1.410×, and no exact production key survives three consecutive levels.",
    boundary: "This is frozen-vocabulary re-encoding of a fully observed held-out cloud—not target-blind generation. Exact residuals certify completeness; they do not count as predicted atoms.",
  },
  "iqc-compression": {
    id: "iqc-compression",
    shortLabel: "IQC · train compression",
    title: "Ideal icosahedral model · history-free reclustering",
    subtitle: "2,064 pooled grown atoms · exact derivations retained separately",
    totalAtoms: 2064,
    source: "Training-corpus compression receipt; no held-out continuation is claimed.",
    levels: [
      { level: 1, frozenTypes: 73, activeTypes: 73, occurrences: 324, coveredAtoms: 2058, residualAtoms: 6, maximumSupportAtoms: 0 },
      { level: 2, frozenTypes: 17, activeTypes: 17, occurrences: 78, coveredAtoms: 2058, residualAtoms: 6, maximumSupportAtoms: 0 },
      { level: 3, frozenTypes: 6, activeTypes: 6, occurrences: 26, coveredAtoms: 2058, residualAtoms: 6, maximumSupportAtoms: 0 },
      { level: 4, frozenTypes: 3, activeTypes: 3, occurrences: 12, coveredAtoms: 2058, residualAtoms: 6, maximumSupportAtoms: 0 },
      { level: 5, frozenTypes: 2, activeTypes: 2, occurrences: 8, coveredAtoms: 2058, residualAtoms: 6, maximumSupportAtoms: 0 },
      { level: 6, frozenTypes: 1, activeTypes: 1, occurrences: 4, coveredAtoms: 2058, residualAtoms: 6, maximumSupportAtoms: 0 },
    ],
    gates: { representation: true, recurring: true, reencoding: false, stationary: false, autonomous: false },
    stationaryCommonKeys: 0,
    autonomousEmittedAtoms: 0,
    diagnosis: "Reclustering removes action history and finds a deep exact-support quotient. Retaining mutually exclusive derivations improves evidence retention, but chemistry, chirality, directed ports, normalized pose, and population substitution still share no three-level stationary production.",
    boundary: "Depth and description-length compression are training evidence. Without a frozen spatial transfer and target-blind executor, neither is a continuation result.",
  },
  "cdyb-transfer": {
    id: "cdyb-transfer",
    shortLabel: "Cd–Yb · partial transfer",
    title: "Published Cd₅.₇Yb model · frozen partial hierarchy",
    subtitle: "Five train windows → two untouched radius-14 windows",
    totalAtoms: 959,
    source: "Published-model held-out re-encoding receipt; all frozen symbols remain in the grammar while absent symbols stay dormant.",
    levels: [
      { level: 1, frozenTypes: 80, activeTypes: 53, occurrences: 92, coveredAtoms: 560, residualAtoms: 399, maximumSupportAtoms: 0 },
      { level: 2, frozenTypes: 36, activeTypes: 20, occurrences: 26, coveredAtoms: 445, residualAtoms: 514, maximumSupportAtoms: 0 },
      { level: 3, frozenTypes: 22, activeTypes: 8, occurrences: 8, coveredAtoms: 314, residualAtoms: 645, maximumSupportAtoms: 0 },
      { level: 4, frozenTypes: 15, activeTypes: 2, occurrences: 2, coveredAtoms: 170, residualAtoms: 789, maximumSupportAtoms: 0 },
      { level: 5, frozenTypes: 8, activeTypes: 0, occurrences: 0, coveredAtoms: 0, residualAtoms: 959, maximumSupportAtoms: 0 },
    ],
    gates: { representation: true, recurring: true, reencoding: true, stationary: false, autonomous: false },
    stationaryCommonKeys: 0,
    autonomousEmittedAtoms: 0,
    diagnosis: "Exact active symbols survive four levels, while dormant train symbols accumulate until level five has no seed occurrence. Residual terminals keep the representation exact, but no production recurs across three scales and a disjoint radius-14 nucleus instantiates no complete level-one promoted macro.",
    boundary: "The hierarchy can explain observed held-out geometry. It cannot yet grow this independent Cd–Yb nucleus without reading atoms outside the seed.",
  },
  "nacl-stationary": {
    id: "nacl-stationary",
    shortLabel: "NaCl · stationary control",
    title: "Rocksalt · learned periodic stationary control",
    subtitle: "Two independent bounded presentations · positions and species only",
    totalAtoms: 4194304,
    source: "Positive-control recurrence receipt; explicit materialization remains O(N).",
    levels: [
      { level: 1, frozenTypes: 1, activeTypes: 1, occurrences: 1478, coveredAtoms: 128, residualAtoms: 0, maximumSupportAtoms: 0 },
      { level: 2, frozenTypes: 1, activeTypes: 1, occurrences: 750, coveredAtoms: 1024, residualAtoms: 0, maximumSupportAtoms: 0 },
      { level: 3, frozenTypes: 1, activeTypes: 1, occurrences: 86, coveredAtoms: 8192, residualAtoms: 0, maximumSupportAtoms: 0 },
    ],
    gates: { representation: true, recurring: true, reencoding: true, stationary: true, autonomous: false },
    stationaryCommonKeys: 1,
    autonomousEmittedAtoms: 0,
    representedAfterSevenActions: 4194304,
    diagnosis: "The learner discovers radix 2 and eight child offsets, then the frozen 29,988-relation port graph independently witnesses the same eight-child production at three learned factors. The scale and population substitution agree, so the stationary representation gate passes.",
    boundary: "This is the crystal positive control. The radix/offset vocabulary is supplied by a positions-only grid learner before port validation, and symbolic representation is not an MD trajectory, physical growth rate, or proof of a generic off-lattice quasicrystal rule.",
  },
});

function assertInteger(value, label, minimum = 0) {
  if (!Number.isInteger(value) || value < minimum) throw new TypeError(`${label} must be an integer ≥ ${minimum}.`);
}

function validateReceipt(receipt) {
  if (!receipt || !RECEIPTS[receipt.id]) throw new TypeError("Unknown hierarchy evidence receipt.");
  assertInteger(receipt.totalAtoms, "totalAtoms", 1);
  if (!Array.isArray(receipt.levels) || receipt.levels.length < 1) throw new TypeError("A receipt needs at least one level.");
  receipt.levels.forEach((level, index) => {
    assertInteger(level.level, `levels[${index}].level`, 1);
    ["frozenTypes", "activeTypes", "occurrences", "coveredAtoms", "residualAtoms", "maximumSupportAtoms"]
      .forEach((field) => assertInteger(level[field], `levels[${index}].${field}`));
    if (level.activeTypes > level.frozenTypes) throw new RangeError("activeTypes cannot exceed frozenTypes.");
    if (level.coveredAtoms + level.residualAtoms !== receipt.totalAtoms
      && receipt.id !== "nacl-stationary") throw new RangeError("coveredAtoms + residualAtoms must equal totalAtoms.");
  });
  if (receipt.gates.stationary && (receipt.levels.length < 3 || receipt.stationaryCommonKeys < 1))
    throw new RangeError("Stationarity requires three levels and a common production key.");
  if (receipt.gates.autonomous && receipt.autonomousEmittedAtoms < 1)
    throw new RangeError("Autonomous emission requires at least one emitted atom.");
  return receipt;
}

export function hierarchyEvidenceReceiptIds() {
  return Object.keys(RECEIPTS);
}

export function buildHierarchyEvidenceMicroscope(receiptId = "iqc-reencoding") {
  const receipt = validateReceipt(RECEIPTS[receiptId]);
  const levels = receipt.levels.map((level, index) => {
    const previous = receipt.levels[index - 1];
    return {
      ...level,
      activeFraction: level.frozenTypes ? level.activeTypes / level.frozenTypes : 0,
      coverageFraction: level.coveredAtoms / receipt.totalAtoms,
      residualFraction: level.residualAtoms / receipt.totalAtoms,
      typeRetentionFromPrevious: previous?.activeTypes ? level.activeTypes / previous.activeTypes : 1,
      occurrenceRetentionFromPrevious: previous?.occurrences ? level.occurrences / previous.occurrences : 1,
      supportAmplificationFromPrevious: previous?.maximumSupportAtoms
        ? level.maximumSupportAtoms / previous.maximumSupportAtoms : 1,
    };
  });
  const highestClaimIndex = CLAIM_RUNGS.reduce((highest, rung, index) =>
    receipt.gates[rung.id] ? index : highest, -1);
  return {
    schema: "gcts-hierarchy-evidence-microscope-v1",
    receiptId,
    options: hierarchyEvidenceReceiptIds().map((id) => ({ id, label: RECEIPTS[id].shortLabel })),
    title: receipt.title,
    subtitle: receipt.subtitle,
    source: receipt.source,
    totalAtoms: receipt.totalAtoms,
    levels,
    claimLadder: CLAIM_RUNGS.map((rung, index) => ({ ...rung,
      passed: Boolean(receipt.gates[rung.id]),
      highestProven: index === highestClaimIndex })),
    highestProvenClaim: highestClaimIndex >= 0 ? CLAIM_RUNGS[highestClaimIndex] : null,
    stationaryCommonKeys: receipt.stationaryCommonKeys,
    autonomousEmittedAtoms: receipt.autonomousEmittedAtoms,
    representedAfterSevenActions: receipt.representedAfterSevenActions || null,
    diagnosis: receipt.diagnosis,
    boundary: receipt.boundary,
    targetUsedForTraining: false,
    heldoutCoordinatesObservedForMatching: receiptId.includes("reencoding") || receiptId === "cdyb-transfer",
    physicalTimeIntegrated: false,
    exponentialClaimed: receipt.gates.stationary && receiptId === "nacl-stationary",
  };
}
