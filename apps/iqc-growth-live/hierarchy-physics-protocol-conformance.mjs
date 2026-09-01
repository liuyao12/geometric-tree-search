import { buildHierarchyPhysicsInvestigation }
  from "./hierarchy-physics-investigation.mjs?v=20260831-402";

const UNIVERSAL = Object.freeze([
  ["protocolFrozenBeforeEvidenceUse", "Protocol frozen before evidence use"],
  ["candidateGeometryFrozen", "Candidate geometry remains frozen"],
  ["targetFreeFitAndSelection", "Evaluation target absent from fit and selection"],
]);

const CHANNEL_REQUIREMENTS = Object.freeze({
  "colored-geometry": Object.freeze([
    ["inputGeometryDigested", "Species-labelled input geometry is digested"],
    ["completeSupportResidualAccounting", "Supports plus residuals cover the observation"],
    ["independentPositionSpeciesHoldout", "Independent position/species holdout is sealed"],
    ["exactHeldoutReplay", "Held-out colored sites replay exactly"],
    ["permutationRigidMetamorphic", "Permutation and proper-rigid controls pass"],
  ]),
  "proper-pose": Object.freeze([
    ["finiteProperPoseVocabulary", "Finite proper-pose vocabulary is observed"],
    ["independentOrientationHoldout", "Independent orientation holdout is sealed"],
    ["permutationRigidMetamorphic", "Permutation and proper-rigid controls pass"],
    ["reflectionControl", "Chiral reflection control remains distinct"],
  ]),
  "connection-topology": Object.freeze([
    ["frozenPortAtlas", "Finite port atlas is frozen"],
    ["boundedIncomingContext", "Incoming connection context is bounded"],
    ["heldoutFrontierCandidateCoverage", "Held-out frontier candidates are covered"],
    ["matchedCandidateAblation", "Compared arms enumerate identical candidates"],
    ["shuffledMarkingControl", "Label-shuffled marking control is executed"],
    ["causalMarkingGain", "Learned marking beats neutral and shuffled controls"],
  ]),
  "steric-exclusion": Object.freeze([
    ["executionHookExercised", "Live hard-closure hook is exercised"],
    ["liveCollisionRecheck", "Occupied-state collisions are rechecked at commit"],
    ["wholeActionRollback", "Failed whole actions roll back atomically"],
    ["adversarialBlockerControl", "Adversarial blocker control passes"],
    ["scheduleInvariantAcceptedUnion", "Equivalent schedules retain the same union"],
    ["zeroUnresolvedColoredCollisions", "No colored collision remains unresolved"],
  ]),
  composition: Object.freeze([
    ["inputGeometryDigested", "Occupancy-aware composition is digested"],
    ["exactSpeciesReplay", "Held-out species replay is exact"],
    ["compositionMutationControl", "Composition-mutation control is rejected"],
  ]),
  residuals: Object.freeze([
    ["completeSupportResidualAccounting", "Supports plus residuals cover the observation"],
    ["literalResidualsNonGenerative", "Literal residual coordinates cannot emit geometry"],
    ["independentResidualReduction", "Residual fraction falls on an independent window"],
  ]),
  "local-response": Object.freeze([
    ["externalPairedResponseEvidence", "External paired response evidence is present"],
    ["crossArchiveFrozenTransfer", "Frozen response model transfers across archives"],
    ["supportAwareAbstention", "Out-of-support candidates cause abstention"],
    ["predictiveGain", "Prediction beats a constant baseline"],
    ["hardGeometryPreserved", "Response ranking preserves hard geometry"],
  ]),
  interface: Object.freeze([
    ["multipleIndependentNuclei", "Multiple independent nuclei are available"],
    ["explicitFrontierMorphology", "Frontier morphology is recomputed explicitly"],
    ["matchedCandidateAblation", "Compared arms enumerate identical candidates"],
    ["disjointNucleusTransfer", "Frozen response transfers to a disjoint nucleus"],
    ["yieldOrWorkGain", "Exact-site yield or search work improves"],
  ]),
  kinetics: Object.freeze([
    ["externalTransitionEvidence", "External transition paths or event counts are present"],
    ["frozenFiniteEventNetwork", "Finite event network is frozen to exact states"],
    ["heldoutPathOrTemperature", "A path, temperature, or material is held out"],
    ["calibratedRatePrediction", "Held-out rate or chronology prediction is calibrated"],
    ["unknownEventMassExplicit", "Unknown-event and missing-exit mass is explicit"],
    ["validatedPhysicalTimeIntegration", "Physical time is integrated only by the validated model"],
  ]),
  nonlocal: Object.freeze([
    ["externalFieldEvidence", "External field solution or measurement is present"],
    ["conservationBoundaryAudit", "Conservation and boundary conditions are audited"],
    ["crossDomainTransfer", "Frozen operator transfers across domain geometry"],
    ["coupledControlGain", "Coupled prediction beats an uncoupled control"],
  ]),
});

const SCALE_REQUIREMENTS = Object.freeze({
  atomic: Object.freeze([]),
  cluster: Object.freeze([
    ["clusterVocabularyFrozen", "Cluster vocabulary is frozen"],
  ]),
  macro: Object.freeze([
    ["promotedHierarchyPresent", "Promoted cluster-of-clusters hierarchy is present"],
    ["exactMacroReplay", "Promoted alternatives replay exactly"],
  ]),
  stationary: Object.freeze([
    ["threeLevelStationaryWitness", "One production recurs across three consecutive levels"],
    ["repeatedScale", "The learned scale repeats on both transitions"],
    ["populationSubstitutionRepeated", "The exact population substitution repeats"],
    ["independentStationaryHoldout", "Stationary production transfers to an independent holdout"],
  ]),
});

const INSPECTION_ROUTES = Object.freeze({
  universal: Object.freeze({ stage: 4, focusId: "receiptScaleBridgeBinding",
    label: "Run receipt and provenance binding" }),
  "colored-geometry": Object.freeze({ stage: 1, focusId: "clusterGeometryOptions",
    label: "Cluster geometry and complete-cover audit" }),
  "proper-pose": Object.freeze({ stage: 1, focusId: "clusterGeometryOptions",
    label: "Symmetry-reduced pose atlas" }),
  "connection-topology": Object.freeze({ stage: 3, focusId: "connectionCoverageAtlas",
    label: "Frozen cluster-to-port coverage atlas" }),
  "steric-exclusion": Object.freeze({ stage: 4, focusId: "growthSearchOptions",
    label: "Whole-action admission and collision audit" }),
  composition: Object.freeze({ stage: 0, focusId: "activeSamplePassport",
    label: "Species, occupancy, and input provenance" }),
  residuals: Object.freeze({ stage: 1, focusId: "clusterGeometryOptions",
    label: "Complete cover and explicit residual classes" }),
  "local-response": Object.freeze({ stage: 4, focusId: "growthPhysicsPreflightMatrix",
    label: "Response evidence and execution-hook preflight" }),
  interface: Object.freeze({ stage: 4, focusId: "growthPhysicsPreflightMatrix",
    label: "Interface-response and matched-candidate preflight" }),
  kinetics: Object.freeze({ stage: 4, focusId: "growthPhysicsPreflightMatrix",
    label: "External event, barrier, and chronology evidence" }),
  nonlocal: Object.freeze({ stage: 4, focusId: "growthPhysicsPreflightMatrix",
    label: "Coupled-field evidence and boundary audit" }),
  cluster: Object.freeze({ stage: 3, focusId: "connectionCoverageAtlas",
    label: "Frozen cluster vocabulary and ports" }),
  macro: Object.freeze({ stage: 4, focusId: "hierarchyEvidenceMicroscope",
    label: "Promoted cluster-of-clusters evidence" }),
  stationary: Object.freeze({ stage: 4, focusId: "hierarchyEvidenceMicroscope",
    label: "Three-level stationary-production gate" }),
});

const REQUIREMENT_ROUTE_OVERRIDES = Object.freeze({
  protocolFrozenBeforeEvidenceUse: INSPECTION_ROUTES.universal,
  candidateGeometryFrozen: INSPECTION_ROUTES["steric-exclusion"],
  targetFreeFitAndSelection: INSPECTION_ROUTES.universal,
  inputGeometryDigested: INSPECTION_ROUTES.composition,
  completeSupportResidualAccounting: INSPECTION_ROUTES.residuals,
  exactHeldoutReplay: INSPECTION_ROUTES["colored-geometry"],
  exactSpeciesReplay: INSPECTION_ROUTES.composition,
  finiteProperPoseVocabulary: INSPECTION_ROUTES["proper-pose"],
  permutationRigidMetamorphic: INSPECTION_ROUTES["proper-pose"],
  reflectionControl: INSPECTION_ROUTES["proper-pose"],
  frozenPortAtlas: INSPECTION_ROUTES["connection-topology"],
  boundedIncomingContext: INSPECTION_ROUTES["connection-topology"],
  matchedCandidateAblation: INSPECTION_ROUTES["connection-topology"],
  shuffledMarkingControl: INSPECTION_ROUTES["connection-topology"],
  causalMarkingGain: INSPECTION_ROUTES["connection-topology"],
  clusterVocabularyFrozen: INSPECTION_ROUTES.cluster,
  promotedHierarchyPresent: INSPECTION_ROUTES.macro,
  exactMacroReplay: INSPECTION_ROUTES.macro,
  threeLevelStationaryWitness: INSPECTION_ROUTES.stationary,
  repeatedScale: INSPECTION_ROUTES.stationary,
  populationSubstitutionRepeated: INSPECTION_ROUTES.stationary,
  independentStationaryHoldout: INSPECTION_ROUTES.stationary,
});

const uniqueRequirements = (records) => [...new Map(records.map((record) => [record[0], record])).values()];

function publicFacts(facts) {
  if (!facts || typeof facts !== "object" || Array.isArray(facts)) {
    throw new TypeError("Conformance evidence facts are required.");
  }
  return Object.freeze(Object.fromEntries(Object.entries(facts)
    .filter(([, value]) => typeof value === "boolean")
    .sort(([left], [right]) => left.localeCompare(right))));
}

export function hierarchyPhysicsProtocolConformanceRequirements(channelId, stageId) {
  const channel = CHANNEL_REQUIREMENTS[channelId];
  const scale = SCALE_REQUIREMENTS[stageId];
  if (!channel) throw new TypeError(`Unknown conformance channel: ${channelId}`);
  if (!scale) throw new TypeError(`Unknown conformance scale: ${stageId}`);
  return Object.freeze(uniqueRequirements([...UNIVERSAL, ...channel, ...scale])
    .map(([id, label]) => {
      const scope = UNIVERSAL.some(([candidate]) => candidate === id) ? "universal"
        : scale.some(([candidate]) => candidate === id) ? "scale" : "channel";
      const route = REQUIREMENT_ROUTE_OVERRIDES[id]
        || INSPECTION_ROUTES[scope === "scale" ? stageId : scope === "channel" ? channelId : "universal"];
      return Object.freeze({ id, label, scope, route: Object.freeze({ ...route }) });
    }));
}

export function buildHierarchyPhysicsProtocolConformance(binding, evidence = {}) {
  if (!binding?.schema) throw new TypeError("A scale-bridge execution binding is required.");
  const facts = publicFacts(evidence.facts || {});
  const verified = binding.digestVerified === true && binding.designReferenceBoundToReceipt === true;
  const compatible = verified && binding.currentRunCompatible === true;
  const stageReached = compatible && binding.plannedStageReached === true;
  const selection = binding.selection || null;
  let plan = null;
  let requirements = [];
  if (verified && selection) {
    plan = buildHierarchyPhysicsInvestigation(selection.receiptId,
      selection.channelId, selection.stageId);
    requirements = hierarchyPhysicsProtocolConformanceRequirements(
      selection.channelId, selection.stageId).map((requirement) => {
      const reported = Object.prototype.hasOwnProperty.call(facts, requirement.id);
      const met = facts[requirement.id] === true;
      return Object.freeze({ ...requirement, met, reported,
        evidenceState: met ? "evidenced" : reported ? "not-evidenced" : "unreported" });
    });
  }
  const metCount = requirements.filter((requirement) => requirement.met).length;
  const missing = requirements.filter((requirement) => !requirement.met);
  const gate = evidence.gateEvaluation || null;
  if (gate && (typeof gate !== "object" || typeof gate.passed !== "boolean"
      || gate.preregistered !== true || gate.metricDenominatorsFrozen !== true
      || !/^[0-9a-f]{64}$/.test(gate.receiptSha256 || ""))) {
    throw new TypeError("A gate evaluation must be preregistered, denominator-frozen, hashed, and boolean.");
  }
  const gateEvaluated = Boolean(gate);
  const gateSatisfied = gateEvaluated ? gate.passed : null;
  const allRequirementsMet = requirements.length > 0 && missing.length === 0;
  const status = !verified ? "no-verified-design"
    : !compatible ? "incompatible-design"
      : !stageReached ? "design-stage-pending"
        : !allRequirementsMet ? "evidence-incomplete"
          : !gateEvaluated ? "ready-for-sealed-gate"
            : gateSatisfied ? "sealed-gate-passed" : "sealed-gate-failed";
  const claimUpgradeAllowed = status === "sealed-gate-passed";
  return Object.freeze({
    schema: "gcts-hierarchy-physics-protocol-conformance-v1", status,
    selection, packetSha256: verified ? binding.verifiedPacketSha256 : null,
    currentRunCompatible: compatible, plannedStageReached: stageReached,
    plan: plan ? Object.freeze({ question: plan.question, operator: plan.operator,
      executionHook: plan.execution, greenGate: plan.greenGate,
      externalEvidenceRequired: plan.externalEvidenceRequired }) : null,
    evidenceFacts: facts, requirements: Object.freeze(requirements),
    metRequirements: metCount, totalRequirements: requirements.length,
    missingRequirementIds: Object.freeze(missing.map((requirement) => requirement.id)),
    nextMissingRequirement: missing[0]?.label || null,
    allRequirementsMet, gateEvaluated, gateSatisfied,
    gateReceiptSha256: gate?.receiptSha256 || null,
    claimUpgradeAllowed, executionConformanceClaimed: claimUpgradeAllowed,
    outcomeClaimUpgraded: claimUpgradeAllowed,
    physicalTimeClaimed: selection?.channelId === "kinetics" ? claimUpgradeAllowed : false,
    targetUsedForFitOrSelection: false, coordinatesEmbedded: false,
    candidateActionsEmbedded: false,
    claimBoundary: claimUpgradeAllowed
      ? "Every declared execution and validation requirement is present and the preregistered sealed gate passed; the upgraded claim is limited to that packet and receipt."
      : "Citing or partially executing a design does not establish conformance, satisfy its green gate, or upgrade a physical claim.",
  });
}

export function hierarchyPhysicsProtocolConformanceChannels() {
  return Object.freeze(Object.keys(CHANNEL_REQUIREMENTS));
}
