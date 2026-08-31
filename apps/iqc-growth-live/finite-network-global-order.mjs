const NUMERIC_FIELDS = Object.freeze([
  "medianNearestNeighborAngstrom", "contactCount", "meanCoordination",
  "coordinationStandardDeviation", "minimumCoordination", "maximumCoordination",
  "sameSpeciesContactFraction", "steinhardtQ4", "steinhardtQ6",
]);

function unavailable(reason, extra = {}) {
  return {
    schema: "gcts-finite-network-global-order-v1",
    available: false,
    reason,
    ...extra,
    targetUsed: false,
    thermodynamicOrderParameterClaimed: false,
    claimBoundary: "Global coordination and Steinhardt descriptors must be reproducible for every exact state under one contact definition before their master-equation expectation is reported. The finite observation boundary is retained; no periodic images or phase labels are invented. These are geometric descriptors, not thermodynamic order parameters.",
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

function expected(sample, descriptorByState, field) {
  return sample.stateProbabilities.reduce((sum, state) =>
    sum + state.probability * descriptorByState.get(state.stateSha256)[field], 0);
}

export function buildFiniteNetworkGlobalOrder(network, dynamics, geometricFlux) {
  if (!dynamics?.available) return unavailable(dynamics?.reason
    || "Finite-network population dynamics are unavailable.");
  if (!geometricFlux?.available) return unavailable(geometricFlux?.reason
    || "Finite-network geometric flux is unavailable.");
  const nodes = Array.isArray(network?.nodes) ? network.nodes : [];
  const edges = Array.isArray(network?.directedEdges) ? network.directedEdges : [];
  const observations = new Map(nodes.map((node) => [node.stateSha256, []]));
  edges.forEach((edge) => {
    if (edge.initialStateGeometricDescriptor) observations.get(edge.fromStateSha256)
      ?.push(edge.initialStateGeometricDescriptor);
    if (edge.finalStateGeometricDescriptor) observations.get(edge.toStateSha256)
      ?.push(edge.finalStateGeometricDescriptor);
  });
  const missingStateSha256 = nodes.filter((node) => !observations.get(node.stateSha256)?.length)
    .map((node) => node.stateSha256);
  if (missingStateSha256.length) return unavailable(
    `${missingStateSha256.length} exact states lack a complete observation-wide descriptor.`,
    { stateCount: nodes.length, descriptorCoveredStateCount: nodes.length - missingStateSha256.length,
      missingStateSha256 });
  const inconsistentStateSha256 = nodes.filter((node) => {
    const records = observations.get(node.stateSha256);
    return records.slice(1).some((descriptor) => !descriptorsEqual(records[0], descriptor));
  }).map((node) => node.stateSha256);
  if (inconsistentStateSha256.length) return unavailable(
    `${inconsistentStateSha256.length} exact state hashes have inconsistent geometric descriptors across incident edges.`,
    { stateCount: nodes.length, inconsistentStateSha256 });
  const descriptorByState = new Map(nodes.map((node) =>
    [node.stateSha256, observations.get(node.stateSha256)[0]]));
  const reaches = new Set([...descriptorByState.values()].map((descriptor) =>
    descriptor.contactReach));
  if (reaches.size !== 1) return unavailable(
    "Exact states use different global contact reaches and cannot share one order trajectory.");
  const fields = ["meanCoordination", "steinhardtQ4", "steinhardtQ6"];
  if ([...descriptorByState.values()].some((descriptor) => fields.some((field) =>
    !Number.isFinite(descriptor[field])))) {
    return unavailable("Every exact state needs finite coordination and Q4/Q6 values.");
  }
  const initialDescriptor = descriptorByState.get(dynamics.initialStateSha256);
  const timeline = dynamics.timeline.map((sample) => {
    const values = Object.fromEntries(fields.map((field) =>
      [field, expected(sample, descriptorByState, field)]));
    return {
      observedTimescaleMultiplier: sample.observedTimescaleMultiplier,
      elapsedSeconds: sample.elapsedSeconds,
      logElapsedSeconds: sample.logElapsedSeconds,
      ...values,
      meanCoordinationChange: values.meanCoordination - initialDescriptor.meanCoordination,
      steinhardtQ4Change: values.steinhardtQ4 - initialDescriptor.steinhardtQ4,
      steinhardtQ6Change: values.steinhardtQ6 - initialDescriptor.steinhardtQ6,
    };
  });
  const directedByKey = new Map(geometricFlux.directedFluxes.map((flux) =>
    [flux.edgeKey, flux]));
  const derivative = (field) => edges.reduce((sum, edge) => {
    const traffic = directedByKey.get(edge.key)?.probabilityTrafficPerObservedTimescale;
    return sum + (Number.isFinite(traffic) ? traffic * (
      descriptorByState.get(edge.toStateSha256)[field]
        - descriptorByState.get(edge.fromStateSha256)[field]) : 0);
  }, 0);
  const stateDerivative = new Map(geometricFlux.stateProbabilityDerivativesPerObservedTimescale
    .map((state) => [state.stateSha256, state.derivative]));
  const derivativeFromStateMoment = (field) => nodes.reduce((sum, node) =>
    sum + stateDerivative.get(node.stateSha256)
      * descriptorByState.get(node.stateSha256)[field], 0);
  const instantaneousOrderCurrent = Object.fromEntries(fields.map((field) =>
    [field, derivative(field)]));
  const orderCurrentIdentityResidual = Object.fromEntries(fields.map((field) =>
    [field, instantaneousOrderCurrent[field] - derivativeFromStateMoment(field)]));
  return {
    schema: "gcts-finite-network-global-order-v1",
    available: true,
    model: "master-equation expectation of exact-state global geometric descriptors",
    initialStateSha256: dynamics.initialStateSha256,
    observedTimescaleMultiplier: geometricFlux.observedTimescaleMultiplier,
    contactReach: [...reaches][0],
    stateCount: nodes.length,
    descriptorCoveredStateCount: nodes.length,
    descriptorConsistencyCertified: true,
    stateDescriptors: nodes.map((node) => ({ stateId: node.stateId,
      stateSha256: node.stateSha256, observationCount: observations.get(node.stateSha256).length,
      descriptor: descriptorByState.get(node.stateSha256) })),
    timeline,
    instantaneousOrderCurrent,
    orderCurrentIdentityResidual,
    finiteObservationBoundaryIncluded: true,
    periodicImagesAdded: false,
    exactStateGeometryChanged: false,
    targetUsed: false,
    chemicalBondClaimed: false,
    phaseClassified: false,
    thermodynamicOrderParameterClaimed: false,
    mechanismCatalogComplete: false,
    claimBoundary: "Every exact state's finite colored point set is reduced to a rotationally invariant global mean coordination and Steinhardt Q4/Q6 under one shared reach, then averaged with the conditional master-equation population. Repeated observations of one state hash must reproduce the same descriptor. Finite-boundary undercoordination is retained and no periodic images are added. The trajectories are not phase classifications, thermodynamic order parameters, infinite-system averages, or mechanism-complete ordering kinetics.",
  };
}

