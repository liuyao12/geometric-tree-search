const clamp = (value, low = -1, high = 1) => Math.max(low, Math.min(high, value));

export const STRUCTURAL_LEAP_AXES = Object.freeze([
  Object.freeze({ id: "inventory", label: "material inventory", filter: "all",
    recordIds: Object.freeze(["atoms", "feedstock"]) }),
  Object.freeze({ id: "local", label: "local environment", filter: "local",
    recordIds: Object.freeze(["coordination", "packing", "void-clearance", "local-order", "centrosymmetry"]) }),
  Object.freeze({ id: "chemistry", label: "composition geometry", filter: "chemistry",
    recordIds: Object.freeze(["composition", "radial-composition"]) }),
  Object.freeze({ id: "mesostructure", label: "shape + connectivity", filter: "mesoscale",
    recordIds: Object.freeze(["void-network", "void-throat", "void-steric", "radius", "anisotropy", "interface"]) }),
  Object.freeze({ id: "reciprocal", label: "reciprocal order", filter: "reciprocal",
    recordIds: Object.freeze(["reciprocal"]) }),
]);

export const UNRESOLVED_DYNAMICAL_QUANTITIES = Object.freeze([
  Object.freeze({ id: "trajectory", label: "intermediate trajectory",
    requirement: "time-resolved coordinates or an explicitly integrated dynamical model" }),
  Object.freeze({ id: "clock", label: "physical time / growth rate",
    requirement: "a calibrated clock, attempt frequency, and transport law" }),
  Object.freeze({ id: "barrier", label: "transition / migration barrier",
    requirement: "a validated energy landscape and transition-path calculation" }),
  Object.freeze({ id: "free-energy", label: "free-energy direction",
    requirement: "energies, entropy, ensemble, and thermodynamic state variables" }),
  Object.freeze({ id: "probability", label: "path probability / branching rate",
    requirement: "a kinetic stochastic model calibrated to physical observations" }),
  Object.freeze({ id: "forces", label: "forces, stress, and heat flow",
    requirement: "force-labelled states plus a constitutive or electronic-structure model" }),
]);

export const DYNAMICAL_EVIDENCE_BRIDGES = Object.freeze({
  trajectory: Object.freeze({
    recordIds: Object.freeze(["relaxation-ensemble", "local-rearrangement", "calculation-forces"]),
    earliestPermittedUse: "posthoc comparison of archived states; never a time-resolved path without an external clock",
  }),
  clock: Object.freeze({
    recordIds: Object.freeze(["kinetics", "feed-exposure", "thermal-field"]),
    earliestPermittedUse: "none until a calibrated external clock and transport law are supplied",
  }),
  barrier: Object.freeze({
    recordIds: Object.freeze(["kinetics", "calculation-forces", "geometry-calculation-calibration", "local-rearrangement"]),
    earliestPermittedUse: "validation of a separately calculated transition path; geometric clearance cannot become a barrier",
  }),
  "free-energy": Object.freeze({
    recordIds: Object.freeze(["relaxation-ensemble", "geometry-calculation-calibration", "configurational-entropy", "thermal-field"]),
    earliestPermittedUse: "posthoc thermodynamic comparison after energies, entropy, ensemble, and state variables are supplied",
  }),
  probability: Object.freeze({
    recordIds: Object.freeze(["path-ensemble", "configurational-entropy", "kinetics"]),
    earliestPermittedUse: "validation of a separately calibrated kinetic model; search multiplicity is not probability",
  }),
  forces: Object.freeze({
    recordIds: Object.freeze(["calculation-forces", "calculation-stress", "stress-strain-response", "constraint-projection"]),
    earliestPermittedUse: "diagnostic first; candidate ranking only after frozen cross-archive transfer validation",
  }),
});

const DIRECT_EVIDENCE_STATES = new Set(["hard", "learned", "explicit", "observed"]);
const PROXY_EVIDENCE_STATES = new Set(["soft", "sampled"]);

export function buildDynamicalEvidencePlan(manifestRecords, options = {}) {
  if (!Array.isArray(manifestRecords)) throw new TypeError("manifestRecords must be an array");
  const byId = new Map(manifestRecords.map((record) => [String(record?.id || ""), record]));
  const quantities = UNRESOLVED_DYNAMICAL_QUANTITIES.map((quantity) => {
    const bridge = DYNAMICAL_EVIDENCE_BRIDGES[quantity.id];
    const records = bridge.recordIds.map((recordId) => byId.get(recordId)).filter(Boolean)
      .map((record) => ({
        id: record.id,
        process: String(record.process || record.id),
        status: String(record.status || "open"),
        role: String(record.role || "unresolved"),
        evidence: String(record.evidence || "No finite evidence recorded."),
        boundary: String(record.boundary || "No claim boundary recorded."),
        controlRouteAvailable: Boolean(record.controlRouteAvailable),
        controlRouteLabel: record.controlRouteLabel || null,
      }));
    const directEvidenceCount = records.filter((record) => DIRECT_EVIDENCE_STATES.has(record.status)).length;
    const proxyEvidenceCount = records.filter((record) => PROXY_EVIDENCE_STATES.has(record.status)).length;
    const unavailableCount = bridge.recordIds.length - directEvidenceCount - proxyEvidenceCount;
    const readiness = directEvidenceCount ? "partial physical evidence"
      : proxyEvidenceCount ? "geometric proxy only" : "no qualifying evidence";
    return {
      ...quantity,
      readiness,
      relatedRecordCount: bridge.recordIds.length,
      directEvidenceCount,
      proxyEvidenceCount,
      unavailableCount,
      records,
      missingRecordIds: bridge.recordIds.filter((recordId) => !byId.has(recordId)),
      earliestPermittedUse: bridge.earliestPermittedUse,
      inferenceResolved: false,
    };
  });
  return {
    schema: 1,
    role: "target-free evidence-acquisition plan for physical quantities omitted by geometric leap-frogging",
    quantities,
    directEvidenceQuantities: quantities.filter((quantity) => quantity.directEvidenceCount).length,
    proxyOnlyQuantities: quantities.filter((quantity) => !quantity.directEvidenceCount && quantity.proxyEvidenceCount).length,
    absentQuantities: quantities.filter((quantity) => !quantity.directEvidenceCount && !quantity.proxyEvidenceCount).length,
    everyInferenceUnresolved: quantities.every((quantity) => !quantity.inferenceResolved),
    manifestRecordCount: manifestRecords.length,
    generatedBeforeActionExecution: options.generatedBeforeActionExecution === true,
    targetUsed: false,
    candidateSetInspected: false,
    physicalTimeIntegrated: false,
  };
}

function normalizedDifference(record) {
  if (!Number.isFinite(record?.before) || !Number.isFinite(record?.after)) return null;
  if (Array.isArray(record.domain) && record.domain.length === 2) {
    const span = Number(record.domain[1]) - Number(record.domain[0]);
    return span > 0 ? clamp((record.after - record.before) / span) : 0;
  }
  const scale = Math.max(Math.abs(record.before), Math.abs(record.after), 1e-12);
  return clamp((record.after - record.before) / scale);
}

export function buildDimensionlessLeapConsequence(records, operation = {}) {
  if (!Array.isArray(records)) throw new TypeError("records must be an array");
  const normalizedRecords = records.map((record) => ({
    id: String(record?.id || ""),
    label: String(record?.label || record?.id || "unlabelled"),
    group: String(record?.group || "unclassified"),
    before: Number.isFinite(record?.before) ? record.before : null,
    after: Number.isFinite(record?.after) ? record.after : null,
    normalizedDelta: normalizedDifference(record),
  }));
  const axes = STRUCTURAL_LEAP_AXES.map((definition) => {
    const fields = definition.recordIds.map((id) => normalizedRecords.find((record) => record.id === id))
      .filter((record) => Number.isFinite(record?.normalizedDelta));
    const signedMean = fields.length
      ? fields.reduce((sum, field) => sum + field.normalizedDelta, 0) / fields.length : null;
    const rmsMagnitude = fields.length
      ? Math.sqrt(fields.reduce((sum, field) => sum + field.normalizedDelta ** 2, 0) / fields.length) : null;
    const dominant = [...fields].sort((first, second) => Math.abs(second.normalizedDelta)
      - Math.abs(first.normalizedDelta) || first.id.localeCompare(second.id))[0] || null;
    return {
      ...definition,
      recordIds: [...definition.recordIds],
      resolvedFields: fields.length,
      requestedFields: definition.recordIds.length,
      signedMean: Number.isFinite(signedMean) ? signedMean : null,
      rmsMagnitude: Number.isFinite(rmsMagnitude) ? rmsMagnitude : null,
      dominantField: dominant ? { id: dominant.id, label: dominant.label,
        normalizedDelta: dominant.normalizedDelta } : null,
    };
  });
  const resolved = normalizedRecords.filter((record) => Number.isFinite(record.normalizedDelta));
  const changed = resolved.filter((record) => Math.abs(record.normalizedDelta) > 1e-12);
  const atomsBefore = Number.isFinite(operation.atomsBefore) ? operation.atomsBefore : null;
  const atomsAfter = Number.isFinite(operation.atomsAfter) ? operation.atomsAfter : null;
  return {
    schema: 1,
    role: "dimensionless structural endpoint difference across one discrete GCTS leap",
    axes,
    resolvedObservableCount: resolved.length,
    requestedObservableCount: normalizedRecords.length,
    changedObservableCount: changed.length,
    operation: {
      component: String(operation.component || "total"),
      acceptedActions: Number.isFinite(operation.acceptedActions) ? operation.acceptedActions : null,
      rejectedActions: Number.isFinite(operation.rejectedActions) ? operation.rejectedActions : null,
      atomsBefore,
      atomsAfter,
      emittedSites: atomsBefore !== null && atomsAfter !== null ? atomsAfter - atomsBefore : null,
      settledGeometry: Boolean(operation.settledGeometry),
    },
    normalization: {
      boundedFields: "after-minus-before divided by the declared dimensionless domain span",
      adaptiveFields: "after-minus-before divided by the larger absolute endpoint magnitude",
      aggregation: "per-axis signed arithmetic mean plus RMS magnitude; axes are never summed",
      favorableDirectionAssigned: false,
    },
    unresolvedDynamics: UNRESOLVED_DYNAMICAL_QUANTITIES.map((quantity) => ({
      ...quantity, status: "not inferred",
    })),
    dynamicalBridge: "The two certified endpoint geometries are connected by one discrete search update. Intermediate configurations, physical duration, and path likelihood are not represented.",
    targetUsed: false,
    physicalTimeIntegrated: false,
    energyOrFreeEnergyInferred: false,
    kineticsInferred: false,
  };
}
