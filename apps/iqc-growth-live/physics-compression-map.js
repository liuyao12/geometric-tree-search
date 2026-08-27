const LANE_DEFINITIONS = Object.freeze([
  Object.freeze({ id: "archive", label: "structural evidence", short: "snapshot → invariants",
    interpretation: "Supplied or derived structural observables constrain the geometric state; they do not become a trajectory.",
    recordIds: Object.freeze(["hypothesis-separation", "local-mismatch-map", "calculation-forces",
      "collinear-spin", "relaxation-ensemble", "geometry-calculation-calibration",
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
  return {
    schema: 1, lanes, recordCount: records.length,
    assignedRecordCount: records.length - unclassified.length,
    unclassifiedRecordIds: unclassified.map((record) => record.id),
    complete: unclassified.length === 0,
    processOrder: "structural evidence → local attachment → interface/morphology → imposed environment → unresolved physics",
    structuralStatesAreNotPhysicalTime: true,
    hypothesesAreNotLearnedPhysics: true,
    targetUsed: false,
  };
}

