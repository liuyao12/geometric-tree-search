const CHARACTERS = Object.freeze([
  "contact-forming", "contact-breaking", "contact exchange / reconstructive",
  "displacive at this contact reach",
]);

function unavailable(reason) {
  return {
    schema: "gcts-finite-network-structural-flux-v1",
    available: false,
    reason,
    targetUsed: false,
    chemicalBondClaimed: false,
    claimBoundary: "Structural current is a traffic-weighted sum of threshold-explicit geometric path observables. Missing path or contact evidence remains unresolved rather than zero. Contacts are not chemical bonds, and this finite observed-network derivative is not a bulk order-parameter kinetics law.",
  };
}

function physicalRate(valuePerObservedTimescale, logUniformizationRatePerSecond) {
  if (valuePerObservedTimescale === 0) return { valuePerSecond: 0, logAbsolutePerSecond: null };
  const logAbsolutePerSecond = Math.log(Math.abs(valuePerObservedTimescale))
    + logUniformizationRatePerSecond;
  return { valuePerSecond: logAbsolutePerSecond > 709 || logAbsolutePerSecond < -745
    ? null : Math.sign(valuePerObservedTimescale) * Math.exp(logAbsolutePerSecond),
  logAbsolutePerSecond };
}

export function buildFiniteNetworkStructuralFlux(network, dynamics, geometricFlux) {
  if (!dynamics?.available) return unavailable(dynamics?.reason
    || "Finite-network population dynamics are unavailable.");
  if (!geometricFlux?.available) return unavailable(geometricFlux?.reason
    || "Finite-network geometric flux is unavailable.");
  const edgeByKey = new Map((Array.isArray(network?.directedEdges)
    ? network.directedEdges : []).map((edge) => [edge.key, edge]));
  const traffic = geometricFlux.directedFluxes.map((flux) => ({
    flux, observable: edgeByKey.get(flux.edgeKey)?.geometricPathObservable || null,
  }));
  const geometryObserved = traffic.filter(({ observable }) => observable != null);
  if (!geometryObserved.length) {
    return unavailable("No committed directed edge retains a geometric path observable.");
  }
  const totalActivity = geometricFlux.totalTransitionActivityPerObservedTimescale;
  const geometryObservedActivity = geometryObserved.reduce((sum, { flux }) =>
    sum + flux.probabilityTrafficPerObservedTimescale, 0);
  const contactResolved = geometryObserved.filter(({ observable }) =>
    observable.contactResolved === true);
  const contactReaches = new Set(contactResolved.map(({ observable }) =>
    Number(observable.contactReach)));
  if (contactReaches.size > 1) {
    return unavailable("Resolved committed edges use different contact-reach definitions and cannot be aggregated.");
  }
  const contactResolvedActivity = contactResolved.reduce((sum, { flux }) =>
    sum + flux.probabilityTrafficPerObservedTimescale, 0);
  const weighted = (records, field) => records.reduce((sum, { flux, observable }) =>
    sum + flux.probabilityTrafficPerObservedTimescale * Number(observable[field]), 0);
  const observedNetContactDriftPerObservedTimescale = weighted(contactResolved,
    "netContactDelta");
  const observedMeanDynamicCoordinationDriftPerObservedTimescale = weighted(contactResolved,
    "meanDynamicCoordinationDelta");
  const expectedMaximumAdjacentDisplacementActivityAngstromPerObservedTimescale = weighted(
    geometryObserved, "maximumAdjacentDisplacementAngstrom");
  const characterActivityPerObservedTimescale = Object.fromEntries(CHARACTERS.map((character) =>
    [character, contactResolved.filter(({ observable }) =>
      observable.geometricCharacter === character).reduce((sum, { flux }) =>
      sum + flux.probabilityTrafficPerObservedTimescale, 0)]));
  const contactRate = physicalRate(observedNetContactDriftPerObservedTimescale,
    dynamics.logUniformizationRatePerSecond);
  const coordinationRate = physicalRate(observedMeanDynamicCoordinationDriftPerObservedTimescale,
    dynamics.logUniformizationRatePerSecond);
  const displacementRate = physicalRate(
    expectedMaximumAdjacentDisplacementActivityAngstromPerObservedTimescale,
    dynamics.logUniformizationRatePerSecond);
  const referenceLengths = contactResolved.map(({ observable }) =>
    observable.referenceLengthAngstrom);
  const paired = Array.isArray(network?.pairedEdges) ? network.pairedEdges : [];
  const inversePairsWithComparableGeometry = paired.filter((edge) =>
    edge.pairAudit?.sameGeometricContactDefinition === true);
  const inversePairsWithClosedGeometry = inversePairsWithComparableGeometry.filter((edge) =>
    edge.pairAudit?.geometricPathObservableClosurePassed === true);
  return {
    schema: "gcts-finite-network-structural-flux-v1",
    available: true,
    model: "traffic-weighted exact-path geometric observable current",
    observedTimescaleMultiplier: geometricFlux.observedTimescaleMultiplier,
    elapsedSeconds: geometricFlux.elapsedSeconds,
    contactReach: contactResolved.length ? [...contactReaches][0] : null,
    referenceLengthRangeAngstrom: referenceLengths.length
      ? [Math.min(...referenceLengths), Math.max(...referenceLengths)] : null,
    totalTransitionActivityPerObservedTimescale: totalActivity,
    geometryObservedActivityPerObservedTimescale: geometryObservedActivity,
    geometryObservedActivityFraction: totalActivity > 0
      ? geometryObservedActivity / totalActivity : 0,
    contactResolvedActivityPerObservedTimescale: contactResolvedActivity,
    contactResolvedActivityFraction: totalActivity > 0
      ? contactResolvedActivity / totalActivity : 0,
    observedNetContactDriftPerObservedTimescale,
    observedNetContactDriftPerSecond: contactRate.valuePerSecond,
    logAbsoluteObservedNetContactDriftPerSecond: contactRate.logAbsolutePerSecond,
    conditionalExpectedNetContactDeltaPerResolvedTransition: contactResolvedActivity > 0
      ? observedNetContactDriftPerObservedTimescale / contactResolvedActivity : null,
    observedMeanDynamicCoordinationDriftPerObservedTimescale,
    observedMeanDynamicCoordinationDriftPerSecond: coordinationRate.valuePerSecond,
    logAbsoluteObservedMeanDynamicCoordinationDriftPerSecond:
      coordinationRate.logAbsolutePerSecond,
    conditionalExpectedMeanDynamicCoordinationDeltaPerResolvedTransition:
      contactResolvedActivity > 0
        ? observedMeanDynamicCoordinationDriftPerObservedTimescale
          / contactResolvedActivity : null,
    expectedMaximumAdjacentDisplacementActivityAngstromPerObservedTimescale,
    expectedMaximumAdjacentDisplacementActivityAngstromPerSecond:
      displacementRate.valuePerSecond,
    logExpectedMaximumAdjacentDisplacementActivityAngstromPerSecond:
      displacementRate.logAbsolutePerSecond,
    characterActivityPerObservedTimescale,
    characterActivityFractionOfResolved: Object.fromEntries(CHARACTERS.map((character) =>
      [character, contactResolvedActivity > 0
        ? characterActivityPerObservedTimescale[character] / contactResolvedActivity : 0])),
    dominantResolvedGeometricCharacter: contactResolvedActivity > 0
      ? [...CHARACTERS].sort((first, second) =>
        characterActivityPerObservedTimescale[second]
          - characterActivityPerObservedTimescale[first] || first.localeCompare(second))[0]
      : null,
    inversePairGeometryAudit: {
      observedPairCount: paired.length,
      comparableContactDefinitionCount: inversePairsWithComparableGeometry.length,
      closedObservableCycleCount: inversePairsWithClosedGeometry.length,
      everyComparablePairClosed: inversePairsWithComparableGeometry.length > 0
        && inversePairsWithComparableGeometry.length === inversePairsWithClosedGeometry.length,
    },
    unresolvedActivityRetainedAsMissing: geometryObservedActivity < totalActivity
      || contactResolvedActivity < totalActivity,
    targetUsed: false,
    chemicalBondClaimed: false,
    physicalTrajectoryIntegrated: false,
    bulkOrderParameterKineticsClaimed: false,
    mechanismCatalogComplete: false,
    claimBoundary: "Each committed exact edge contributes its validated path-local contact-count change, dynamic-coordination change, and maximum adjacent-image displacement weighted by p_i k_ij. Contact sums include only traffic with one shared explicit reach; unresolved traffic is reported, never set to zero. These geometric contacts are not chemical bonds, and the conditional finite-network current is not a bulk order parameter, relaxation trajectory, transport coefficient, or mechanism-complete structural kinetics law.",
  };
}

