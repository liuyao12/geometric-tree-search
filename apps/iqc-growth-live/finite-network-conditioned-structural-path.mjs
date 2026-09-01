import { buildFiniteNetworkConditionedArrival }
  from "./finite-network-conditioned-arrival.mjs?v=20260901-439";

const NUMERIC_FIELDS = Object.freeze([
  "medianNearestNeighborAngstrom", "contactCount", "meanCoordination",
  "coordinationStandardDeviation", "minimumCoordination", "maximumCoordination",
  "sameSpeciesContactFraction", "steinhardtQ4", "steinhardtQ6",
]);

function unavailable(reason, extra = {}) {
  return {
    schema: "gcts-finite-network-conditioned-structural-path-v1",
    available: false,
    reason,
    ...extra,
    targetUsed: false,
    phaseClassified: false,
    thermodynamicOrderParameterClaimed: false,
    mechanismCatalogComplete: false,
    claimBoundary: "A conditioned structural path requires repeated exact-state geometric descriptors to agree under one finite-window contact definition. The resulting atom-count, coordination, and Q4/Q6 curves are path-conditioned geometry, not phase labels, thermodynamic order parameters, bulk observables, or a complete growth mechanism.",
  };
}

function mapEqual(first, second, tolerance = 1e-10) {
  const keys = [...new Set([...Object.keys(first || {}), ...Object.keys(second || {})])].sort();
  return keys.every((key) => Object.hasOwn(first || {}, key)
    && Object.hasOwn(second || {}, key)
    && (typeof first[key] === "number" ? Math.abs(first[key] - second[key]) <= tolerance
      : first[key] === second[key]));
}

function descriptorsEqual(first, second) {
  return first.atomCount === second.atomCount
    && first.contactReach === second.contactReach
    && NUMERIC_FIELDS.every((field) => first[field] == null && second[field] == null
      || Number.isFinite(first[field]) && Number.isFinite(second[field])
        && Math.abs(first[field] - second[field]) <= 1e-8)
    && mapEqual(first.speciesCounts, second.speciesCounts, 0)
    && mapEqual(first.speciesPairContactFractions, second.speciesPairContactFractions);
}

export function buildFiniteNetworkConditionedStructuralPath(network, {
  sourceStateSha256 = null,
  targetStateSha256 = null,
} = {}) {
  const arrival = buildFiniteNetworkConditionedArrival(network,
    { sourceStateSha256, targetStateSha256 });
  if (!arrival.available) return unavailable(arrival.reason, { arrival });
  const nodes = Array.isArray(network?.nodes) ? network.nodes : [];
  const edges = Array.isArray(network?.directedEdges) ? network.directedEdges : [];
  const relevant = new Set(arrival.timeline.flatMap((sample) =>
    sample.conditionedStateProbabilities.map((state) => state.stateSha256)));
  const observations = new Map([...relevant].map((stateSha256) => [stateSha256, []]));
  edges.forEach((edge) => {
    if (relevant.has(edge.fromStateSha256) && edge.initialStateGeometricDescriptor) {
      observations.get(edge.fromStateSha256).push(edge.initialStateGeometricDescriptor);
    }
    if (relevant.has(edge.toStateSha256) && edge.finalStateGeometricDescriptor) {
      observations.get(edge.toStateSha256).push(edge.finalStateGeometricDescriptor);
    }
  });
  const missingStateSha256 = [...relevant].filter((stateSha256) =>
    !observations.get(stateSha256)?.length);
  if (missingStateSha256.length) return unavailable(
    `${missingStateSha256.length} successful-passage states lack a geometric descriptor.`,
  { arrival, missingStateSha256, descriptorCoveredStateCount: relevant.size
    - missingStateSha256.length });
  const inconsistentStateSha256 = [...relevant].filter((stateSha256) => {
    const records = observations.get(stateSha256);
    return records.slice(1).some((descriptor) => !descriptorsEqual(records[0], descriptor));
  });
  if (inconsistentStateSha256.length) return unavailable(
    `${inconsistentStateSha256.length} successful-passage state hashes have inconsistent geometric descriptors.`,
  { arrival, inconsistentStateSha256 });
  const descriptorByState = new Map([...relevant].map((stateSha256) =>
    [stateSha256, observations.get(stateSha256)[0]]));
  const reaches = new Set([...descriptorByState.values()].map((descriptor) =>
    descriptor.contactReach));
  if (reaches.size !== 1) return unavailable(
    "Successful-passage states use different global contact reaches.", { arrival });
  const fields = ["atomCount", "meanCoordination", "steinhardtQ4", "steinhardtQ6"];
  if ([...descriptorByState.values()].some((descriptor) => fields.some((field) =>
    !Number.isFinite(descriptor[field])))) {
    return unavailable("Every successful-passage state needs finite atom count, coordination, and Q4/Q6.",
      { arrival });
  }
  const edgeCountMismatch = edges.some((edge) => relevant.has(edge.fromStateSha256)
    && relevant.has(edge.toStateSha256)
    && (descriptorByState.get(edge.fromStateSha256).atomCount !== edge.initialAtomCount
      || descriptorByState.get(edge.toStateSha256).atomCount !== edge.finalAtomCount));
  if (edgeCountMismatch) return unavailable(
    "One retained edge atom count disagrees with its exact-state geometric descriptor.", { arrival });
  const sourceDescriptor = descriptorByState.get(sourceStateSha256);
  const targetDescriptor = descriptorByState.get(targetStateSha256);
  const timeline = arrival.timeline.map((sample) => {
    const stateProbabilities = sample.conditionedStateProbabilities.map((state) => ({
      ...state,
      descriptor: descriptorByState.get(state.stateSha256),
    }));
    const transient = stateProbabilities.filter((state) => !state.absorbedTarget);
    const survivalProbability = transient.reduce((sum, state) => sum + state.probability, 0);
    const expected = Object.fromEntries(fields.map((field) => [field,
      stateProbabilities.reduce((sum, state) =>
        sum + state.probability * state.descriptor[field], 0)]));
    const survivingExpected = Object.fromEntries(fields.map((field) => [field,
      survivalProbability > 1e-15 ? transient.reduce((sum, state) =>
        sum + state.probability * state.descriptor[field], 0) / survivalProbability : null]));
    const survivorStateProbabilities = transient.map((state) => ({
      stateId: state.stateId,
      stateSha256: state.stateSha256,
      probabilityGivenNotArrived: survivalProbability > 1e-15
        ? state.probability / survivalProbability : 0,
    })).sort((first, second) => second.probabilityGivenNotArrived
      - first.probabilityGivenNotArrived || first.stateId.localeCompare(second.stateId));
    const atomDenominator = targetDescriptor.atomCount - sourceDescriptor.atomCount;
    return {
      relativeToConditionalMean: sample.relativeToConditionalMean,
      logElapsedSeconds: sample.logElapsedSeconds,
      elapsedSeconds: sample.elapsedSeconds,
      cumulativeArrivalProbability: sample.cumulativeArrivalProbability,
      survivalProbability,
      expectedAtomCount: expected.atomCount,
      expectedMeanCoordination: expected.meanCoordination,
      expectedSteinhardtQ4: expected.steinhardtQ4,
      expectedSteinhardtQ6: expected.steinhardtQ6,
      survivingExpectedAtomCount: survivingExpected.atomCount,
      survivingExpectedMeanCoordination: survivingExpected.meanCoordination,
      survivingExpectedSteinhardtQ4: survivingExpected.steinhardtQ4,
      survivingExpectedSteinhardtQ6: survivingExpected.steinhardtQ6,
      expectedAtomProgressFraction: atomDenominator
        ? (expected.atomCount - sourceDescriptor.atomCount) / atomDenominator : null,
      survivorStateProbabilities,
      dominantSurvivingState: survivorStateProbabilities[0] || null,
      stateProbabilityNormalizationResidual: stateProbabilities.reduce((sum, state) =>
        sum + state.probability, 0) - 1,
      survivorProbabilityNormalizationResidual: survivalProbability > 1e-15
        ? survivorStateProbabilities.reduce((sum, state) =>
          sum + state.probabilityGivenNotArrived, 0) - 1 : 0,
    };
  });
  const medianRegion = timeline.reduce((best, sample) =>
    Math.abs(sample.cumulativeArrivalProbability - .5)
      < Math.abs(best.cumulativeArrivalProbability - .5) ? sample : best);
  const maximumStateProbabilityNormalizationResidual = Math.max(...timeline.map((sample) =>
    Math.abs(sample.stateProbabilityNormalizationResidual)));
  const maximumSurvivorProbabilityNormalizationResidual = Math.max(...timeline.map((sample) =>
    Math.abs(sample.survivorProbabilityNormalizationResidual)));
  const initialIdentityResidual = Math.max(...fields.map((field) => Math.abs(
    timeline[0][field === "atomCount" ? "expectedAtomCount"
      : field === "meanCoordination" ? "expectedMeanCoordination"
        : field === "steinhardtQ4" ? "expectedSteinhardtQ4" : "expectedSteinhardtQ6"]
      - sourceDescriptor[field])));
  const finalSample = timeline.at(-1);
  const finalTargetConvergenceResidual = Math.max(...fields.map((field) => {
    const key = field === "atomCount" ? "expectedAtomCount"
      : field === "meanCoordination" ? "expectedMeanCoordination"
        : field === "steinhardtQ4" ? "expectedSteinhardtQ4" : "expectedSteinhardtQ6";
    return Math.abs(finalSample[key] - targetDescriptor[field]);
  }));
  const identitiesPassed = maximumStateProbabilityNormalizationResidual <= 1e-10
    && maximumSurvivorProbabilityNormalizationResidual <= 1e-10
    && initialIdentityResidual <= 1e-10
    && arrival.identitiesPassed;
  return {
    schema: "gcts-finite-network-conditioned-structural-path-v1",
    available: true,
    model: "Doob-conditioned phase-type state occupancy projected onto exact finite-window structural descriptors",
    sourceStateSha256,
    targetStateSha256,
    temperatureKelvin: arrival.temperatureKelvin,
    methodSettingsSha256: arrival.methodSettingsSha256,
    contactReach: [...reaches][0],
    relevantStateCount: relevant.size,
    descriptorConsistencyCertified: true,
    stateDescriptors: nodes.filter((node) => relevant.has(node.stateSha256)).map((node) => ({
      stateId: node.stateId,
      stateSha256: node.stateSha256,
      observationCount: observations.get(node.stateSha256).length,
      descriptor: descriptorByState.get(node.stateSha256),
    })),
    sourceDescriptor,
    targetDescriptor,
    timeline,
    medianRegion,
    maximumStateProbabilityNormalizationResidual,
    maximumSurvivorProbabilityNormalizationResidual,
    initialIdentityResidual,
    finalTargetConvergenceResidual,
    identitiesPassed,
    arrival,
    finiteObservationBoundaryIncluded: true,
    periodicImagesAdded: false,
    exactStatesChanged: false,
    targetUsed: false,
    chemicalBondClaimed: false,
    phaseClassified: false,
    thermodynamicOrderParameterClaimed: false,
    mechanismCatalogComplete: false,
    claimBoundary: "Exact successful-passage state probabilities are projected onto consistent finite-window atom count, coordination, and rotationally invariant Q4/Q6 descriptors. Survivor-conditioned curves describe paths not yet absorbed; target-inclusive curves retain already arrived paths. Observation-boundary undercoordination remains. These are not phase labels, thermodynamic order parameters, bulk averages, sampled trajectories, or a complete material-growth mechanism.",
  };
}
