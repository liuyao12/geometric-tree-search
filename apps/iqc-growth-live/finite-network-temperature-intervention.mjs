import { buildFiniteNetworkFirstPassage }
  from "./finite-network-first-passage.mjs?v=20260901-432";
import { buildFiniteNetworkPassageControl }
  from "./finite-network-passage-control.mjs?v=20260901-432";

const BOLTZMANN_ELECTRON_VOLT_PER_KELVIN = 8.617333262145e-5;

function unavailable(reason, extra = {}) {
  return {
    schema: "gcts-finite-network-temperature-intervention-v1",
    available: false,
    reason,
    ...extra,
    targetUsed: false,
    networkMutated: false,
    unauthorizedExtrapolationPerformed: false,
    temperatureDependentBarrierClaimed: false,
    equilibriumClaimed: false,
    claimBoundary: "A temperature intervention is allowed only when every retained observed edge carries an externally authorized common bounded constant-HTST interval, barrier, and prefactor. It reweights one frozen finite mechanism catalog; it does not infer temperature-dependent barriers, free energies, structures, missing mechanisms, phase changes, or equilibrium.",
  };
}

function authorizedApplicability(edge) {
  const value = edge?.temperatureApplicability;
  return value?.scope === "bounded-constant-htst"
    && value.externallyAuthorized === true
    && value.barrierAndPrefactorAssumedConstant === true
    && Number.isFinite(value.minimumKelvin) && Number.isFinite(value.maximumKelvin)
    && value.minimumKelvin >= 1 && value.maximumKelvin <= 5000
    && value.minimumKelvin < value.maximumKelvin ? value : null;
}

function htstLogRate(edge, temperatureKelvin) {
  return Math.log(edge.attemptFrequencyPerSecond)
    - edge.barrierElectronVolt
      / (BOLTZMANN_ELECTRON_VOLT_PER_KELVIN * temperatureKelvin);
}

function logRateUncertainty(edge, temperatureKelvin) {
  return Math.hypot(edge.barrierUncertaintyElectronVolt
      / (BOLTZMANN_ELECTRON_VOLT_PER_KELVIN * temperatureKelvin),
  edge.attemptFrequencyUncertaintyLog10 * Math.LN10);
}

function reweightedNetwork(network, temperatureKelvin) {
  return { ...network, directedEdges: network.directedEdges.map((edge) => ({ ...edge,
    temperatureKelvin,
    logRatePerSecond: htstLogRate(edge, temperatureKelvin),
    logRateUncertainty: logRateUncertainty(edge, temperatureKelvin),
  })) };
}

function temperatureGrid(minimumKelvin, maximumKelvin, nominalKelvin, selectedKelvin,
  sampleCount) {
  const count = Math.max(5, Math.min(81, Math.trunc(sampleCount)));
  const values = Array.from({ length: count }, (_, index) => {
    const fraction = index / (count - 1);
    return minimumKelvin + fraction * (maximumKelvin - minimumKelvin);
  });
  values.push(nominalKelvin, selectedKelvin);
  return [...new Set(values.map((value) => Number(value.toPrecision(14))))]
    .sort((first, second) => first - second);
}

export function buildFiniteNetworkTemperatureIntervention(network, {
  sourceStateSha256 = null,
  targetStateSha256 = null,
  temperatureKelvin = null,
  sampleCount = 17,
} = {}) {
  const edges = Array.isArray(network?.directedEdges) ? network.directedEdges : [];
  if (!edges.length) return unavailable("At least one observed directed edge is required.");
  if (edges.some((edge) => !Number.isFinite(edge.barrierElectronVolt)
      || edge.barrierElectronVolt < 0
      || !Number.isFinite(edge.barrierUncertaintyElectronVolt)
      || edge.barrierUncertaintyElectronVolt < 0
      || !(edge.attemptFrequencyPerSecond > 0)
      || !Number.isFinite(edge.attemptFrequencyUncertaintyLog10)
      || edge.attemptFrequencyUncertaintyLog10 < 0)) {
    return unavailable("Every retained edge needs a finite HTST barrier, prefactor, and both uncertainties.");
  }
  const applicability = edges.map(authorizedApplicability);
  if (applicability.some((value) => !value)) {
    return unavailable("Every retained edge needs an externally authorized bounded constant-HTST applicability declaration.");
  }
  const minimumKelvin = Math.max(...applicability.map((value) => value.minimumKelvin));
  const maximumKelvin = Math.min(...applicability.map((value) => value.maximumKelvin));
  if (!(minimumKelvin < maximumKelvin)) {
    return unavailable("The retained edges have no common authorized temperature interval.");
  }
  const nominalTemperatures = [...new Set(edges.map((edge) => edge.temperatureKelvin))];
  const methodSettings = new Set(edges.map((edge) => edge.methodSettingsSha256));
  const prefactorSettings = new Set(edges.map((edge) => edge.prefactorSettingsSha256));
  if (nominalTemperatures.length !== 1 || !Number.isFinite(nominalTemperatures[0])
      || methodSettings.size !== 1 || prefactorSettings.size !== 1
      || [...prefactorSettings].some((value) => typeof value !== "string" || !value)) {
    return unavailable("Every edge must share one nominal temperature, barrier method, and prefactor settings digest.");
  }
  const nominalTemperatureKelvin = nominalTemperatures[0];
  if (nominalTemperatureKelvin < minimumKelvin
      || nominalTemperatureKelvin > maximumKelvin) {
    return unavailable("The nominal network temperature lies outside the common authorized interval.");
  }
  const sourceRateResiduals = edges.map((edge) => edge.logRatePerSecond
    - htstLogRate(edge, nominalTemperatureKelvin));
  const maximumSourceRateResidual = Math.max(...sourceRateResiduals.map(Math.abs));
  if (!(maximumSourceRateResidual <= 1e-8)) {
    return unavailable("At least one supplied nominal edge rate is inconsistent with its retained HTST barrier and prefactor.",
      { maximumSourceRateResidual });
  }
  const selectedTemperatureKelvin = Number(temperatureKelvin ?? nominalTemperatureKelvin);
  if (!Number.isFinite(selectedTemperatureKelvin)
      || selectedTemperatureKelvin < minimumKelvin
      || selectedTemperatureKelvin > maximumKelvin) {
    return unavailable(`Choose a temperature within the common authorized ${minimumKelvin}–${maximumKelvin} K interval.`);
  }
  const nominal = buildFiniteNetworkFirstPassage(network,
    { sourceStateSha256, targetStateSha256 });
  const control = buildFiniteNetworkPassageControl(network,
    { sourceStateSha256, targetStateSha256 });
  if (!nominal.available || !control.available
      || !(nominal.sourceTargetHittingProbability > 0)
      || !Number.isFinite(nominal.sourceConditionalMeanFirstPassageLogSeconds)) {
    return unavailable(nominal.reason || control.reason
      || "A solvable nominal target passage is required.", { nominal, control });
  }
  const controlByEdge = new Map(control.edgeSensitivities.map((edge) =>
    [edge.edgeKey, edge]));
  const samples = [];
  for (const sampleTemperatureKelvin of temperatureGrid(minimumKelvin, maximumKelvin,
    nominalTemperatureKelvin, selectedTemperatureKelvin, sampleCount)) {
    const shifted = reweightedNetwork(network, sampleTemperatureKelvin);
    const solved = buildFiniteNetworkFirstPassage(shifted,
      { sourceStateSha256, targetStateSha256 });
    if (!solved.available
        || !Number.isFinite(solved.sourceConditionalMeanFirstPassageLogSeconds)) {
      return unavailable(`The finite catalog is not solvable at ${sampleTemperatureKelvin} K.`);
    }
    const edgeRateShifts = shifted.directedEdges.map((edge, index) => ({
      edgeKey: edge.key,
      logarithmicRateChange: edge.logRatePerSecond - edges[index].logRatePerSecond,
    }));
    const localControlProjectedLogPassageChange = edgeRateShifts.reduce((sum, edge) =>
      sum + edge.logarithmicRateChange
        * controlByEdge.get(edge.edgeKey).logPassageTimeElasticity, 0);
    const localControlProjectedTargetProbabilityChange = edgeRateShifts.reduce((sum, edge) =>
      sum + edge.logarithmicRateChange
        * controlByEdge.get(edge.edgeKey).targetProbabilityElasticity, 0);
    const exactLogPassageTimeChange = solved.sourceConditionalMeanFirstPassageLogSeconds
      - nominal.sourceConditionalMeanFirstPassageLogSeconds;
    samples.push({
      temperatureKelvin: sampleTemperatureKelvin,
      inverseTemperaturePerKilokelvin: 1000 / sampleTemperatureKelvin,
      targetHittingProbability: solved.sourceTargetHittingProbability,
      targetHittingProbabilityChange: solved.sourceTargetHittingProbability
        - nominal.sourceTargetHittingProbability,
      conditionalMeanFirstPassageLogSeconds: solved.sourceConditionalMeanFirstPassageLogSeconds,
      exactLogPassageTimeChange,
      exactConditionalPassageTimeRatio: Math.exp(exactLogPassageTimeChange),
      conditionalExpectedObservedJumps: solved.sourceConditionalExpectedObservedJumps,
      localControlProjectedLogPassageChange,
      localControlProjectedTargetProbabilityChange,
      nonlinearLogTimeDepartureFromLocalProjection: exactLogPassageTimeChange
        - localControlProjectedLogPassageChange,
      edgeRateShifts,
    });
  }
  const selectedResponse = samples.reduce((closest, sample) =>
    Math.abs(sample.temperatureKelvin - selectedTemperatureKelvin)
      < Math.abs(closest.temperatureKelvin - selectedTemperatureKelvin) ? sample : closest);
  const edgeTemperatureLeverages = edges.map((edge) => ({
    edgeKey: edge.key,
    fromStateSha256: edge.fromStateSha256,
    toStateSha256: edge.toStateSha256,
    eventDirection: edge.eventDirection,
    barrierElectronVolt: edge.barrierElectronVolt,
    logarithmicRateDerivativePerKelvin: edge.barrierElectronVolt
      / (BOLTZMANN_ELECTRON_VOLT_PER_KELVIN * nominalTemperatureKelvin ** 2),
    localLogPassageTimeDerivativePerKelvin:
      controlByEdge.get(edge.key).logPassageTimeElasticity * edge.barrierElectronVolt
        / (BOLTZMANN_ELECTRON_VOLT_PER_KELVIN * nominalTemperatureKelvin ** 2),
    geometricCharacter: edge.geometricPathObservable?.geometricCharacter || null,
  })).sort((first, second) => Math.abs(second.localLogPassageTimeDerivativePerKelvin)
    - Math.abs(first.localLogPassageTimeDerivativePerKelvin)
    || first.edgeKey.localeCompare(second.edgeKey));
  return {
    schema: "gcts-finite-network-temperature-intervention-v1",
    available: true,
    model: "externally authorized constant-HTST reweighting of every edge in a frozen finite passage network",
    sourceStateSha256,
    targetStateSha256,
    nominalTemperatureKelvin,
    selectedTemperatureKelvin: selectedResponse.temperatureKelvin,
    commonAuthorizedMinimumKelvin: minimumKelvin,
    commonAuthorizedMaximumKelvin: maximumKelvin,
    methodSettingsSha256: [...methodSettings][0],
    prefactorSettingsSha256: [...prefactorSettings][0],
    maximumSourceRateResidual,
    directedEdgeCount: edges.length,
    geometryResolvedEdgeCount: edges.filter((edge) =>
      edge.geometricPathObservable?.geometricCharacter).length,
    samples,
    selectedResponse,
    edgeTemperatureLeverages,
    dominantTemperatureControlEdge: edgeTemperatureLeverages[0] || null,
    exactStatesChanged: false,
    edgeTopologyChanged: false,
    geometryChanged: false,
    candidateCatalogChanged: false,
    networkMutated: false,
    targetUsed: false,
    unauthorizedExtrapolationPerformed: false,
    temperatureDependentBarrierClaimed: false,
    equilibriumClaimed: false,
    claimBoundary: "Every supplied HTST barrier and prefactor is held constant while all retained observed rates are coherently reevaluated inside their common externally authorized temperature interval. The calculation preserves the exact finite state graph and path geometry. It does not model thermal expansion, relaxation, temperature-dependent free energies or barriers, anharmonicity, recrossing, phase changes, missing mechanisms, or equilibrium.",
  };
}
