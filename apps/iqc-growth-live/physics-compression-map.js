const LANE_DEFINITIONS = Object.freeze([
  Object.freeze({ id: "archive", label: "structural evidence", short: "snapshot → invariants",
    interpretation: "Supplied or derived structural observables constrain the geometric state; they do not become a trajectory.",
    recordIds: Object.freeze(["hypothesis-separation", "local-mismatch-map", "calculation-forces",
      "calculation-stress", "stress-strain-response", "collinear-spin", "relaxation-ensemble", "geometry-calculation-calibration",
      "local-rearrangement", "local-symmetry", "centrosymmetry", "reciprocal-space"]) }),
  Object.freeze({ id: "local", label: "local attachment", short: "fast neighborhood closure",
    interpretation: "Steric, coordination, chemistry, charge, connection, and local projection evidence act on exact candidate geometry.",
    recordIds: Object.freeze(["steric", "local", "constraint-projection", "connection", "score-ledger",
      "chemistry", "charge-geometry", "charge-moment", "ionic-pair", "bond-valence", "robustness"]) }),
  Object.freeze({ id: "interface", label: "interface + morphology", short: "mesoscopic front geometry",
    interpretation: "Surface completion, habit, coherency, front shape, defects, nuclei, and loop closure are represented without an interfacial-energy law.",
    recordIds: Object.freeze(["solute-partition", "surface", "bulk-surface-driving", "attachment-topology",
      "habit-anisotropy", "defect-precursors", "coherency-memory", "front-morphology",
      "capillary-geometry", "microstructure", "multi-nucleus", "loop-closure"]) }),
  Object.freeze({ id: "environment", label: "imposed environment", short: "declared boundary geometry",
    interpretation: "Substrate, loading, directional, thermal, feed-exposure, and path-ensemble controls are counterfactual geometric hypotheses.",
    recordIds: Object.freeze(["epitaxy", "affine", "drive", "thermal-field", "feed-exposure", "path-ensemble"]) }),
  Object.freeze({ id: "open", label: "unresolved physics", short: "dynamics + nonlocal response",
    interpretation: "Barrier crossing, diffusion, heat flow, elapsed time, and collective nonlocal response remain outside the bounded structural grammar.",
    recordIds: Object.freeze(["kinetics", "long-range"]) }),
]);

function evidenceBucket(status) {
  if (["hard", "learned", "explicit", "observed"].includes(status)) return "structural";
  if (["soft", "sampled"].includes(status)) return "hypothesis";
  return "open";
}

function laneState(counts, total) {
  if (!total || counts.open === total) return "open";
  if (counts.structural === total) return "structural";
  if (counts.hypothesis === total) return "declared";
  if (counts.open) return "partial";
  return "hybrid";
}

const HARD_ADMISSION_IDS = new Set(["steric", "local", "connection"]);
const CANDIDATE_GEOMETRY_IDS = new Set(["constraint-projection", "calculation-forces"]);
const INITIAL_STATE_IDS = new Set(["multi-nucleus"]);
const SEARCH_ORDER_IDS = new Set(["path-ensemble"]);
const RANKING_IDS = new Set([
  "hypothesis-separation", "calculation-stress", "stress-strain-response",
  "geometry-calculation-calibration", "connection", "chemistry", "charge-geometry",
  "charge-moment", "ionic-pair", "bond-valence", "solute-partition", "surface",
  "bulk-surface-driving", "attachment-topology", "habit-anisotropy", "defect-precursors",
  "coherency-memory", "front-morphology", "capillary-geometry", "epitaxy", "affine",
  "drive", "thermal-field", "robustness", "microstructure", "loop-closure",
  "feed-exposure", "kinetics",
]);

export const PHYSICS_EFFECT_COLUMNS = Object.freeze([
  Object.freeze({ id: "hardAdmission", label: "admission", property: "hardAdmissionCanChange" }),
  Object.freeze({ id: "candidateGeometry", label: "geometry", property: "candidateGeometryCanChange" }),
  Object.freeze({ id: "initialState", label: "seed", property: "initialStateCanChange" }),
  Object.freeze({ id: "ranking", label: "ranking", property: "rankingCanChange" }),
  Object.freeze({ id: "searchOrder", label: "order", property: "searchOrderCanChange" }),
  Object.freeze({ id: "diagnostic", label: "no hook", property: "diagnosticOnly" }),
]);

export const PHYSICS_READINESS_STATES = Object.freeze([
  Object.freeze({ id: "executing", label: "executing now" }),
  Object.freeze({ id: "configurable", label: "control off" }),
  Object.freeze({ id: "missingEvidence", label: "input needed" }),
  Object.freeze({ id: "evidenceOnly", label: "evidence only" }),
  Object.freeze({ id: "external", label: "external physics" }),
]);

function effectActive(record) {
  if (["open", "unavailable", "observed"].includes(record.status)) return false;
  if (/\b(disabled|ablated|diagnostic|not selected|awaiting)\b/i.test(record.role || "")) return false;
  if (record.status === "explicit" && !INITIAL_STATE_IDS.has(record.id)) return false;
  return true;
}

export function physicsExecutionLineage(record) {
  if (!record?.id || typeof record.status !== "string") {
    throw new Error("physics execution lineage needs a manifest record");
  }
  const active = effectActive(record);
  const hardAdmission = active && HARD_ADMISSION_IDS.has(record.id);
  const candidateGeometry = active && CANDIDATE_GEOMETRY_IDS.has(record.id);
  const initialState = active && INITIAL_STATE_IDS.has(record.id);
  const ranking = active && RANKING_IDS.has(record.id);
  const searchOrder = active && SEARCH_ORDER_IDS.has(record.id);
  const effects = [
    hardAdmission ? "hard admission" : null,
    candidateGeometry ? "bounded candidate geometry" : null,
    initialState ? "initial seed state" : null,
    ranking ? "soft branch ranking" : null,
    searchOrder ? "reproducible branch order" : null,
  ].filter(Boolean);
  return {
    schema: 1,
    recordId: record.id,
    active,
    evidenceStatus: record.status,
    effects,
    hardAdmissionCanChange: hardAdmission,
    candidateGeometryCanChange: candidateGeometry,
    initialStateCanChange: initialState,
    rankingCanChange: ranking,
    searchOrderCanChange: searchOrder,
    diagnosticOnly: effects.length === 0,
    candidateSetInspectedBeforeExecution: false,
    targetUsed: false,
    physicalTimeModeled: false,
    summary: effects.length ? effects.join(" + ") : active
      ? "active structural evidence; no direct execution hook"
      : "diagnostic or unresolved; no execution effect",
  };
}

export function physicsExecutionReadiness(record) {
  const execution = physicsExecutionLineage(record);
  if (!execution.diagnosticOnly) return {
    id: "executing", label: "executing now", actionable: false,
    nextStep: `Inspect the finite response; ${execution.summary}.`,
  };
  if (record.status === "unavailable") return {
    id: "missingEvidence", label: "input needed", actionable: Boolean(record.controlRouteAvailable),
    nextStep: record.controlRouteLabel || "Supply the required measurement or structural evidence.",
  };
  if (record.controlRouteAvailable) return {
    id: "configurable", label: "control off", actionable: true,
    nextStep: record.controlRouteLabel || "Configure this geometric hypothesis.",
  };
  if (["observed", "explicit", "hard", "learned"].includes(record.status)
      || /\b(diagnostic|reported|descriptive|evidence)\b/i.test(record.role || "")) return {
    id: "evidenceOnly", label: "evidence only", actionable: false,
    nextStep: "Inspect the recorded evidence; it currently changes no execution object.",
  };
  return {
    id: "external", label: "external physics", actionable: false,
    nextStep: "Requires an external solver or a new trainable geometric state variable.",
  };
}

export function buildPhysicsLineagePath(record) {
  const execution = physicsExecutionLineage(record);
  return {
    schema: 1,
    recordId: record.id,
    nodes: [
      { id: "evidence", label: "physical evidence", value: `${record.status} · ${record.process}` },
      { id: "encoding", label: "geometric encoding", value: record.encoding },
      { id: "execution", label: "search effect", value: execution.summary },
      { id: "response", label: "finite evidence", value: record.evidence },
      { id: "boundary", label: "claim boundary", value: record.boundary },
    ],
    execution,
    candidateGeometryEmbedded: false,
    coordinatesEmbedded: false,
    targetUsed: false,
  };
}

export function buildPhysicsCompressionMap(records) {
  if (!Array.isArray(records)) throw new Error("physics compression map needs manifest records");
  const ids = new Set();
  records.forEach((record) => {
    if (!record?.id || ids.has(record.id) || typeof record.status !== "string") {
      throw new Error("physics manifest records need unique IDs and status");
    }
    ids.add(record.id);
  });
  const byId = new Map(records.map((record) => [record.id, record]));
  const assigned = new Set();
  const summarize = (definition, laneRecords) => {
    const counts = laneRecords.reduce((result, record) => {
      result[evidenceBucket(record.status)] += 1; return result;
    }, { structural: 0, hypothesis: 0, open: 0 });
    return { id: definition.id, label: definition.label, short: definition.short,
      interpretation: definition.interpretation, recordIds: laneRecords.map((record) => record.id),
      recordCount: laneRecords.length, counts, state: laneState(counts, laneRecords.length) };
  };
  const lanes = LANE_DEFINITIONS.map((definition) => {
    const laneRecords = definition.recordIds.filter((id) => byId.has(id)).map((id) => byId.get(id));
    laneRecords.forEach((record) => {
      if (assigned.has(record.id)) throw new Error(`physics record assigned twice: ${record.id}`);
      assigned.add(record.id);
    });
    return summarize(definition, laneRecords);
  });
  const unclassified = records.filter((record) => !assigned.has(record.id));
  if (unclassified.length) lanes.push(summarize({ id: "unclassified", label: "unclassified records",
    short: "manifest update required",
    interpretation: "These records were not silently assigned. Update the process-scale map before making a compression claim." }, unclassified));
  const executionLineages = records.map(physicsExecutionLineage);
  return {
    schema: 1, lanes, recordCount: records.length,
    assignedRecordCount: records.length - unclassified.length,
    unclassifiedRecordIds: unclassified.map((record) => record.id),
    complete: unclassified.length === 0,
    processOrder: "structural evidence → local attachment → interface/morphology → imposed environment → unresolved physics",
    structuralStatesAreNotPhysicalTime: true,
    hypothesesAreNotLearnedPhysics: true,
    executionEffectsComplete: executionLineages.length === records.length,
    effectCounts: {
      hardAdmission: executionLineages.filter((record) => record.hardAdmissionCanChange).length,
      candidateGeometry: executionLineages.filter((record) => record.candidateGeometryCanChange).length,
      initialState: executionLineages.filter((record) => record.initialStateCanChange).length,
      ranking: executionLineages.filter((record) => record.rankingCanChange).length,
      searchOrder: executionLineages.filter((record) => record.searchOrderCanChange).length,
      diagnosticOnly: executionLineages.filter((record) => record.diagnosticOnly).length,
    },
    targetUsed: false,
  };
}

export function buildPhysicsEffectMatrix(records) {
  if (!Array.isArray(records)) throw new Error("physics effect matrix needs manifest records");
  const compression = buildPhysicsCompressionMap(records);
  const laneByRecord = new Map();
  compression.lanes.forEach((lane) => lane.recordIds.forEach((recordId) => laneByRecord.set(recordId, lane.id)));
  const rows = records.map((record) => {
    const execution = physicsExecutionLineage(record);
    const readiness = physicsExecutionReadiness(record);
    const effects = Object.fromEntries(PHYSICS_EFFECT_COLUMNS.map((column) =>
      [column.id, Boolean(execution[column.property])]));
    return {
      recordId: record.id,
      process: record.process,
      status: record.status,
      evidenceBucket: evidenceBucket(record.status),
      laneId: laneByRecord.get(record.id) || "unclassified",
      active: execution.active,
      effects,
      effectCount: PHYSICS_EFFECT_COLUMNS.slice(0, -1)
        .filter((column) => execution[column.property]).length,
      executionSummary: execution.summary,
      readiness,
    };
  });
  const counts = Object.fromEntries(PHYSICS_EFFECT_COLUMNS.map((column) =>
    [column.id, rows.filter((row) => row.effects[column.id]).length]));
  const readinessCounts = Object.fromEntries(PHYSICS_READINESS_STATES.map((state) =>
    [state.id, rows.filter((row) => row.readiness.id === state.id).length]));
  return {
    schema: 1,
    columns: PHYSICS_EFFECT_COLUMNS.map(({ id, label }) => ({ id, label })),
    rows,
    counts,
    readinessCounts,
    recordCount: rows.length,
    everyRecordClassified: compression.complete && rows.every((row) => row.laneId !== "unclassified"),
    mutuallyNonexclusiveEffects: true,
    candidateSetInspected: false,
    targetUsed: false,
    physicalTimeModeled: false,
  };
}
