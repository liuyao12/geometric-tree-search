import { buildHierarchyEvidenceMicroscope }
  from "./hierarchy-evidence-microscope.mjs?v=20260901-414";

export const HIERARCHY_TRANSPORT_STAGES = Object.freeze([
  Object.freeze({ id: "atomic", label: "atomic state", short: "atoms" }),
  Object.freeze({ id: "cluster", label: "primitive cluster", short: "clusters" }),
  Object.freeze({ id: "macro", label: "promoted cluster²", short: "clusters²" }),
  Object.freeze({ id: "stationary", label: "stationary law", short: "scale law" }),
]);

export const HIERARCHY_TRANSPORT_STATES = Object.freeze({
  exact: Object.freeze({ id: "exact", label: "exactly transported", rank: 3 }),
  reevaluated: Object.freeze({ id: "reevaluated", label: "re-evaluated explicitly", rank: 2 }),
  representation: Object.freeze({ id: "representation", label: "representation only", rank: 1 }),
  open: Object.freeze({ id: "open", label: "not transported", rank: 0 }),
});

const EXACT = "exact";
const REEVALUATED = "reevaluated";
const REPRESENTATION = "representation";
const OPEN = "open";

const CHANNELS = Object.freeze([
  Object.freeze({
    id: "colored-geometry", label: "colored coordinates", physical: "Atomic identity and Cartesian geometry",
    statuses: [EXACT, EXACT, EXACT, "stationary"],
    evidence: "Every admitted prototype and occurrence re-renders the full species-labelled point set. Proper fits and exact coordinate/species replay are independently checked.",
    boundary: "Coordinate transport preserves a structural state; it does not establish its energy, stability, probability, or rate.",
  }),
  Object.freeze({
    id: "proper-pose", label: "orientation + chirality", physical: "Rigid orientation, handedness, and finite rotational alternatives",
    statuses: [EXACT, EXACT, EXACT, "stationary"],
    evidence: "Right-handed intrinsic frames and learned proper symmetry gauges quotient translation and rotation without admitting reflections.",
    boundary: "A finite pose class is not an orientational free energy or a rotational kinetic pathway.",
  }),
  Object.freeze({
    id: "connection-topology", label: "connection topology", physical: "Overlap, boundary adjacency, and incident-port compatibility",
    statuses: [REPRESENTATION, EXACT, EXACT, "stationary"],
    evidence: "Primitive and promoted edges retain directed frozen proper-SE(3) port semantics and exact overlap chemistry from witnessed training relations.",
    boundary: "Witnessed ports enumerate structural connections; they do not prove that every physically relevant attachment mechanism was observed.",
  }),
  Object.freeze({
    id: "steric-exclusion", label: "steric + collision closure", physical: "Species-aware coincidence, exclusion distance, and occupied-volume compatibility",
    statuses: [EXACT, EXACT, REEVALUATED, REEVALUATED],
    evidence: "Internal colored unions are exact. Every explicit macro attachment is collision-checked again against the currently occupied state before commitment.",
    boundary: "Symbolic recursion never waives explicit cross-boundary collision checks; materializing N sites remains O(N).",
  }),
  Object.freeze({
    id: "composition", label: "composition + population", physical: "Species counts, occupational alternatives, and population substitution",
    statuses: [EXACT, EXACT, EXACT, "stationary"],
    evidence: "Colored supports preserve exact species populations. A stationary certificate additionally requires the same nonnegative integer population substitution across two adjacent scale transitions.",
    boundary: "Population bookkeeping is not a chemical potential, charge density, redox model, or phase-equilibrium calculation.",
  }),
  Object.freeze({
    id: "residuals", label: "gaps + residual terminals", physical: "Geometry not compressed by a recurring support",
    statuses: [EXACT, REPRESENTATION, REPRESENTATION, OPEN],
    evidence: "Every uncovered coordinate/species site remains an explicit residual terminal, and representation digests require support plus residual union to reproduce the observation exactly.",
    boundary: "Residual completeness explains an observed cloud. A coordinate-bearing residual is not a predicted atom and cannot certify autonomous continuation.",
  }),
  Object.freeze({
    id: "local-response", label: "local strain + response", physical: "Bond-length/angle mismatch, supplied force geometry, and local structural relaxation",
    statuses: [REPRESENTATION, REEVALUATED, REEVALUATED, OPEN],
    evidence: "Available local response is evaluated on explicit sites or exact candidate geometry at the current frontier; it is not silently homogenized into a promoted symbol.",
    boundary: "Without an independently validated scale-transfer rule, a macro carries geometry—not an effective elastic energy, force law, or relaxation trajectory.",
  }),
  Object.freeze({
    id: "interface", label: "interface + defect morphology", physical: "Surface completion, front shape, nuclei, loops, voids, and defect precursors",
    statuses: [REPRESENTATION, REEVALUATED, REEVALUATED, OPEN],
    evidence: "These observables are recomputed from the explicit occupied frontier and public boundary after structural leaps. They can rank the same frozen attachments.",
    boundary: "Local morphology is not an interfacial free energy, capillary time law, defect formation energy, or mesoscale phase-field model.",
  }),
  Object.freeze({
    id: "kinetics", label: "barriers + event kinetics", physical: "Activation barriers, prefactors, reversible events, and finite-state rates",
    statuses: [OPEN, OPEN, OPEN, OPEN],
    evidence: "A separate externally validated finite event catalog can assign rates to exact states and edges, but no hierarchy receipt transports that catalog through recursive promotion.",
    boundary: "Tree-search depth and macro count are not elapsed physical time. Missing mechanisms and exits remain unknown.",
  }),
  Object.freeze({
    id: "nonlocal", label: "nonlocal transport + fields", physical: "Diffusion supply, heat flow, electronic response, long-range elasticity, and collective transport",
    statuses: [OPEN, OPEN, OPEN, OPEN],
    evidence: "The bounded structural grammar contains no certified coarse operator for these nonlocal fields across hierarchy levels.",
    boundary: "These processes require external calculations or a separately validated reduced model before they can influence leap-frogged growth.",
  }),
]);

function resolvedStatus(status, hierarchy, stageIndex) {
  if (stageIndex === HIERARCHY_TRANSPORT_STAGES.length - 1
      && hierarchy.stationaryCommonKeys < 1) return OPEN;
  if (status !== "stationary") return status;
  return hierarchy.stationaryCommonKeys > 0 ? EXACT : OPEN;
}

function validateRows(rows) {
  if (rows.length !== CHANNELS.length) throw new Error("Every physics channel must be represented once.");
  const ids = new Set();
  rows.forEach((row) => {
    if (ids.has(row.id)) throw new Error("Physics transport channel IDs must be unique.");
    ids.add(row.id);
    if (row.stages.length !== HIERARCHY_TRANSPORT_STAGES.length) {
      throw new Error("Every physics transport row needs one state per hierarchy stage.");
    }
    row.stages.forEach((stage) => {
      if (!HIERARCHY_TRANSPORT_STATES[stage.status]) throw new Error("Unknown physics transport state.");
    });
  });
}

export function buildHierarchyPhysicsTransport(receiptId = "iqc-reencoding") {
  const hierarchy = buildHierarchyEvidenceMicroscope(receiptId);
  const rows = CHANNELS.map((channel) => {
    const stages = channel.statuses.map((status, index) => {
      const resolved = resolvedStatus(status, hierarchy, index);
      return { ...HIERARCHY_TRANSPORT_STAGES[index], status: resolved,
        statusLabel: HIERARCHY_TRANSPORT_STATES[resolved].label,
        causalTransport: resolved === EXACT || resolved === REEVALUATED };
    });
    const lastTransportedIndex = stages.reduce((last, stage, index) =>
      stage.causalTransport ? index : last, -1);
    return { id: channel.id, label: channel.label, physical: channel.physical,
      stages, evidence: channel.evidence, boundary: channel.boundary,
      lastTransportedStage: lastTransportedIndex >= 0
        ? HIERARCHY_TRANSPORT_STAGES[lastTransportedIndex] : null,
      stationaryTransported: stages.at(-1).status === EXACT };
  });
  validateRows(rows);
  const stageSummaries = HIERARCHY_TRANSPORT_STAGES.map((stage, stageIndex) => {
    const counts = Object.fromEntries(Object.keys(HIERARCHY_TRANSPORT_STATES).map((state) =>
      [state, rows.filter((row) => row.stages[stageIndex].status === state).length]));
    return { ...stage, counts, causalCount: counts.exact + counts.reevaluated,
      exactCount: counts.exact, openCount: counts.open, total: rows.length };
  });
  return {
    schema: "gcts-hierarchy-physics-transport-v1",
    receiptId,
    title: hierarchy.title,
    options: hierarchy.options,
    hierarchy,
    rows,
    stageSummaries,
    stationaryPhysicsChannels: rows.filter((row) => row.stationaryTransported).map((row) => row.id),
    exactMacroChannels: rows.filter((row) => row.stages[2].status === EXACT).map((row) => row.id),
    representationOnlyMacroChannels: rows.filter((row) => row.stages[2].status === REPRESENTATION).map((row) => row.id),
    openMacroChannels: rows.filter((row) => row.stages[2].status === OPEN).map((row) => row.id),
    targetUsed: false,
    candidateGeometryChanged: false,
    physicalTimeIntegrated: false,
    coarsePhysicsInferredFromHierarchyDepth: false,
    claimBoundary: "The matrix audits what each frozen hierarchy receipt actually transports. Exact means coordinate/species or discrete port/population semantics are preserved; re-evaluated means explicit geometry is checked again at execution; representation-only means observed atoms remain accountably encoded but are not generated; open means no cross-scale operator is certified. No status is upgraded merely because the hierarchy is deep.",
  };
}
