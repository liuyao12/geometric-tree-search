import { buildHierarchyPhysicsTransport, HIERARCHY_TRANSPORT_STAGES,
  HIERARCHY_TRANSPORT_STATES }
  from "./hierarchy-physics-transport.mjs?v=20260831-407";

const PROGRAMS = Object.freeze({
  "colored-geometry": Object.freeze({
    question: "Does the species-labelled geometry recur without copying the evaluation coordinates?",
    evidence: "Independent position/species observations spanning the intended composition, boundary, and structural variability.",
    encoding: "Colored metric supports, exact residual terminals, and proper-SE(3) occurrence fits.",
    validation: "Fit on spatially disjoint windows; require exact species/position replay, permutation invariance, and proper-rigid equivariance.",
    execution: "Authorize only frozen support occurrences and exact coordinate-bearing alternatives; re-render every accepted union.",
    gate: "Exact unseen support replay with complete support + residual accounting and zero target use during fitting or branch choice.",
    route: Object.freeze({ stage: 0, focusId: "scenarioSelect", label: "Open atomic evidence" }),
    operator: "discrete structural state",
  }),
  "proper-pose": Object.freeze({
    question: "Which symmetry-inequivalent proper rotations are actually required by the observed cover?",
    evidence: "Repeated cluster occurrences in independent orientations, including chiral or mirror-sensitive controls where relevant.",
    encoding: "Right-handed intrinsic frame sets, finite proper-symmetry gauges, and symmetry-quotiented relative poses.",
    validation: "Random proper rotations and atom permutations must preserve the canonical grammar; reflections must remain distinct when the support is chiral.",
    execution: "Enumerate only learned finite pose orbits; use equivariant SO(2)/SO(3) handling when a finite recurrent orbit is not supported.",
    gate: "Every required held-out pose is recognized without raw angle bins, global axes, family labels, or improper rotations.",
    route: Object.freeze({ stage: 1, focusId: "clusterGeometryOptions", label: "Inspect pose discovery" }),
    operator: "proper-pose quotient",
  }),
  "connection-topology": Object.freeze({
    question: "Do local overlap and boundary connections transfer to an unseen frontier?",
    evidence: "Train-witnessed, species-consistent overlaps or boundary adjacencies from multiple independent cluster occurrences.",
    encoding: "Directed finite ports carrying proper relative pose, overlap chemistry, incidence, and already-placed incoming context.",
    validation: "Freeze the port atlas before a guarded spatial holdout; compare marked and shuffled rankings on identical candidate IDs.",
    execution: "Generate geometry from frozen ports, then let a bounded local section rank or abstain without inventing actions.",
    gate: "Held-out candidate coverage plus a causal marking gain over parent-only and label-shuffled controls at matched correct output.",
    route: Object.freeze({ stage: 3, focusId: "connectionCoverageAtlas", label: "Train connection sections" }),
    operator: "finite connection grammar",
  }),
  "steric-exclusion": Object.freeze({
    question: "Does every structural leap remain compatible with the already occupied material?",
    evidence: "Species-labelled prototypes, a declared tolerance, and a minimum-distance/exclusion rule derived from training geometry.",
    encoding: "Exact colored coincidence, unlike-species conflict, minimum-clearance, and whole-cluster inclusion certificates.",
    validation: "Adversarial blockers, pairwise batch conflicts, and candidate-order permutations must fail closed without changing admitted geometry.",
    execution: "Recheck collisions incrementally against the live occupied state before every commit; roll back the entire action on failure.",
    gate: "Zero unresolved colored collisions and byte-stable accepted unions across equivalent candidate schedules.",
    route: Object.freeze({ stage: 4, focusId: "growthPhysicsPreflight", label: "Audit growth admission" }),
    operator: "hard geometric closure",
  }),
  composition: Object.freeze({
    question: "Is chemistry transported as exact population structure rather than a family label?",
    evidence: "Species or occupation-resolved sites, including alternative/disordered occupations when the source supplies them.",
    encoding: "Exact colored populations, reduced role chemistry, and explicit occupational alternatives.",
    validation: "Composition-changing negative controls and independent windows must preserve exact site identity; stationary tests require one repeated integer substitution matrix.",
    execution: "Reject unlike-species coincidences and population-incompatible productions before ranking.",
    gate: "Exact held-out species replay; for scale laws, identical nonnegative-integer population substitution over two adjacent transitions.",
    route: Object.freeze({ stage: 0, focusId: "selectedElements", label: "Inspect composition input" }),
    operator: "colored population map",
  }),
  residuals: Object.freeze({
    question: "Which observed geometry is explained only literally, and can any of it become recurrent without leakage?",
    evidence: "A complete atom-domain audit separating repeated supports from uncovered sites in every training window.",
    encoding: "Exact species/coordinate residual terminals with ownership and support-union digests.",
    validation: "Support plus residuals must reproduce each held-out observation exactly; recurrent promotion is learned on training windows only.",
    execution: "Residuals complete a known representation but never emit novel sites or authorize an attachment.",
    gate: "Residual fraction decreases on independent windows through a recurrent isometry class; literal coordinates never enter a generative rule.",
    route: Object.freeze({ stage: 1, focusId: "clusterGeometryOptions", label: "Inspect cover residuals" }),
    operator: "literal representation terminal",
  }),
  "local-response": Object.freeze({
    question: "Can local relaxation, force, or strain response be predicted from invariant geometry on a different archive?",
    evidence: "Paired atomic geometries with independently computed energies, stresses, forces, or relaxed endpoints and explicit provenance.",
    encoding: "Invariant distance/angle/coordination mismatch, local best-affine residuals, or validated force-projected connection features.",
    validation: "Fit on one calculation archive and freeze before another compatible archive; report support overlap and abstain out of domain.",
    execution: "Use the frozen surrogate only to rank identical exact candidates or seed a bounded projection that must reduce residual and re-pass hard geometry.",
    gate: "Cross-archive predictive gain over a constant baseline, calibrated uncertainty, and no degradation of exact collision/overlap certificates.",
    route: Object.freeze({ stage: 0, focusId: "relaxationCalibrationTitle", label: "Open response calibration" }),
    operator: "externally calibrated local response",
    externalEvidence: true,
  }),
  interface: Object.freeze({
    question: "Which frontier morphology changes attachment preference on a genuinely different nucleus or boundary?",
    evidence: "Multiple independent nuclei or interface snapshots with declared public boundaries and, where available, interfacial calculations.",
    encoding: "Local normals, curvature/concavity, exposed-port density, registry, defect precursors, and finite morphology summaries.",
    validation: "Freeze on whole nuclei, not correlated actions; run a matched ablation over the same candidate set and output budget.",
    execution: "Recompute morphology from the explicit live frontier and use it only at its registered ranking/admission hook.",
    gate: "Transfer on a disjoint nucleus with improved exact-site yield or reduced work versus both neutral and shuffled controls.",
    route: Object.freeze({ stage: 4, focusId: "growthPhysicsPreflight", label: "Compose interface experiment" }),
    operator: "finite frontier response",
  }),
  kinetics: Object.freeze({
    question: "Can structural actions be assigned transferable barriers, reversibility, and physical rates?",
    evidence: "Independent transition paths or trajectory-derived event counts with barriers, prefactors, temperature, and state provenance.",
    encoding: "A finite event network over exact structural states, with uncertainty-bearing rates bound to specific frozen action classes.",
    validation: "Hold out entire paths, temperatures, or materials; verify event coverage, calibrated rate error, detailed-balance assumptions, and missing exits.",
    execution: "Choose among frozen structural events with an externally validated kinetic model; integrate time only inside that declared model.",
    gate: "Held-out chronology or first-passage predictions beat a structural-order baseline with calibrated uncertainty and explicit unknown-event mass.",
    route: Object.freeze({ stage: 4, focusId: "growthPhysicsPreflight", label: "Design kinetic calibration" }),
    operator: "external stochastic event operator",
    externalEvidence: true,
  }),
  nonlocal: Object.freeze({
    question: "How do diffusion, heat, charge, or long-range elastic fields alter the local structural frontier?",
    evidence: "Boundary/initial conditions plus independently solved or measured fields over multiple sizes, shapes, and material states.",
    encoding: "A separately validated reduced field state sampled at exact candidate geometry, with conservation and boundary conditions retained.",
    validation: "Hold out domain size and boundary geometry; verify conservation, operator error, and coupled structural response against the external solver.",
    execution: "Advance the field operator between structural leaps and expose only its registered local features to candidate admission or ranking.",
    gate: "Joint field/structure predictions transfer across a new domain without refitting and beat an uncoupled structural control.",
    route: Object.freeze({ stage: 4, focusId: "growthPhysicsPreflight", label: "Design coupled-field protocol" }),
    operator: "external nonlocal coarse operator",
    externalEvidence: true,
  }),
});

const STATUS_DIRECTIVES = Object.freeze({
  exact: Object.freeze({ label: "stress-test preserved semantics", action: "Keep the encoding frozen and challenge it with an independent spatial/material holdout plus metamorphic controls.", claimAllowed: true }),
  reevaluated: Object.freeze({ label: "validate the explicit recheck", action: "Register the execution hook and compare it with a neutral arm on the identical frozen candidate set.", claimAllowed: true }),
  representation: Object.freeze({ label: "convert accounting into recurrence", action: "Mine a train-recurrent isometry or operator; keep every unmatched site explicit and prohibit it from emitting geometry.", claimAllowed: false }),
  open: Object.freeze({ label: "supply and validate a missing operator", action: "Add independent physical evidence, freeze the operator before evaluation, and fail closed outside its support.", claimAllowed: false }),
});

const RECEIPT_SCENARIOS = Object.freeze({
  "iqc-reencoding": "iqc", "iqc-compression": "iqc", "cdyb-transfer": "cdyb", "nacl-stationary": "competition",
});

export function buildHierarchyPhysicsInvestigation(receiptId = "iqc-reencoding",
  channelId = "colored-geometry", stageId = "macro") {
  const transport = buildHierarchyPhysicsTransport(receiptId);
  const row = transport.rows.find((candidate) => candidate.id === channelId);
  if (!row) throw new Error(`Unknown hierarchy physics channel: ${channelId}`);
  const stageIndex = HIERARCHY_TRANSPORT_STAGES.findIndex((stage) => stage.id === stageId);
  if (stageIndex < 0) throw new Error(`Unknown hierarchy transport stage: ${stageId}`);
  const program = PROGRAMS[channelId];
  if (!program) throw new Error(`Missing hierarchy investigation program: ${channelId}`);
  const stage = row.stages[stageIndex];
  const directive = STATUS_DIRECTIVES[stage.status];
  const result = {
    schema: "gcts-hierarchy-physics-investigation-v1",
    receiptId, title: transport.title, channelId, channelLabel: row.label,
    physical: row.physical, stageId, stageLabel: stage.label, stageShort: stage.short,
    status: stage.status, statusLabel: HIERARCHY_TRANSPORT_STATES[stage.status].label,
    question: program.question, evidence: program.evidence, encoding: program.encoding,
    validation: program.validation, execution: program.execution, greenGate: program.gate,
    operator: program.operator, externalEvidenceRequired: program.externalEvidence === true,
    directive: directive.label, nextAction: directive.action, claimAllowed: directive.claimAllowed,
    route: { ...program.route, scenario: RECEIPT_SCENARIOS[receiptId] },
    candidateGeometryFrozenDuringAblation: true, targetUsedForFitOrSelection: false,
    physicalTimeClaimed: channelId === "kinetics" ? false : null,
    claimBoundary: `${row.boundary} ${transport.claimBoundary}`,
  };
  if (!result.route.scenario) throw new Error(`Missing workflow scenario for receipt: ${receiptId}`);
  return Object.freeze(result);
}

export function hierarchyPhysicsInvestigationPrograms() {
  return Object.freeze(Object.keys(PROGRAMS));
}
