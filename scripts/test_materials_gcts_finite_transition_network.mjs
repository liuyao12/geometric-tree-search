import assert from "node:assert/strict";
import { buildFiniteTransitionNetwork }
  from "../apps/iqc-growth-live/finite-transition-network.mjs";

const kbt = 8.617333262145e-5 * 600;
const sha = (letter) => letter.repeat(64);
const states = { A: sha("a"), B: sha("b"), C: sha("c") };
const energies = { A: 0, B: .12, C: -.04 };
const grand = { A: 0, B: .08, C: -.03 };
const counts = { A: 10, B: 11, C: 12 };
const transfer = { "A->B": { Na: 1 }, "B->A": { Na: -1 },
  "B->C": { Na: 1 }, "C->B": { Na: -1 },
  "C->A": { Na: -2 }, "A->C": { Na: 2 } };

function transition(from, to, index) {
  const energyDelta = energies[to] - energies[from];
  const grandDelta = grand[to] - grand[from];
  const transitionStateEnergy = 1.2 + .05 * [from, to].sort().join("").charCodeAt(0) / 100;
  const barrier = transitionStateEnergy - energies[from];
  const logRate = 12 - grandDelta / (2 * kbt);
  return {
    eventId: `${from}-${to}`, candidateId: `${from}->${to}`,
    requestSha256: sha((index % 8 + 1).toString()),
    responseSha256: sha(((index + 3) % 8 + 1).toString()),
    eventDirection: index % 2 ? "detach" : "attach",
    initialGeometrySha256: states[from], finalGeometrySha256: states[to],
    committedStateSha256: states[to], exactFinalGeometryReproduced: true,
    initialAtomCount: counts[from], finalAtomCount: counts[to],
    barrierElectronVolt: barrier, barrierUncertaintyElectronVolt: .001,
    energyDeltaElectronVolt: energyDelta, energyDeltaUncertaintyElectronVolt: .001,
    attemptFrequencyPerSecond: Math.exp(logRate + barrier / kbt),
    attemptFrequencyUncertaintyLog10: .001,
    logRatePerSecond: logRate, temperatureKelvin: 600,
    methodSettingsSha256: sha("d"), prefactorSettingsSha256: sha("e"),
    speciesDelta: transfer[`${from}->${to}`],
    thermodynamicEvidenceSha256: sha("f"),
    freeEnergySettingsSha256: sha("1"), chemicalPotentialSettingsSha256: sha("2"),
    thermodynamicTemperatureKelvin: 600,
    systemFreeEnergyDeltaElectronVolt: grandDelta,
    systemFreeEnergyDeltaUncertaintyElectronVolt: .0008,
    reservoirChemicalWorkElectronVolt: 0,
    reservoirChemicalWorkUncertaintyElectronVolt: .0006,
    grandPotentialDeltaElectronVolt: grandDelta,
    grandPotentialDeltaUncertaintyElectronVolt: .001,
  };
}

const history = [transition("A", "B", 0), transition("B", "A", 1),
  transition("B", "C", 2), transition("C", "B", 3),
  transition("C", "A", 4), transition("A", "C", 5)];
const network = buildFiniteTransitionNetwork(history);
assert.equal(network.nodes.length, 3);
assert.equal(network.directedEdges.length, 6);
assert.equal(network.directedEdges.every((edge) => Number.isFinite(edge.logRatePerSecond)), true);
assert.equal(network.activeObservationPolicy,
  "latest exact committed observation per directed edge");
assert.equal(network.pairedEdgeCount, 3);
assert.equal(network.unpairedEdgeCount, 0);
assert.equal(network.independentCycleCount, 1);
assert.equal(network.cycles[0].kineticKolmogorovCyclePassed, true);
assert.equal(network.cycles[0].grandPotentialIntegrabilityPassed, true);
assert.ok(Math.abs(network.cycles[0].rateCycleAffinityLog) < 1e-10);
assert.ok(Math.abs(network.cycles[0].grandPotentialCycleResidualElectronVolt) < 1e-12);
assert.equal(network.everyPairLocallyBalanced, true);
assert.equal(network.finiteObservedNetworkCycleConsistencyPassed, true);
assert.equal(network.globalDetailedBalanceCertified, false);
assert.equal(network.networkCompletenessCertified, false);

const permuted = buildFiniteTransitionNetwork([...history].reverse());
assert.equal(permuted.pairedEdgeCount, network.pairedEdgeCount);
assert.equal(permuted.independentCycleCount, network.independentCycleCount);
assert.ok(Math.abs(permuted.cycles[0].rateCycleAffinityLog) < 1e-10);

const inconsistent = buildFiniteTransitionNetwork(history.map((record) =>
  record.eventId === "A-B" ? { ...record, logRatePerSecond: record.logRatePerSecond + 5 } : record));
assert.equal(inconsistent.cycles[0].kineticKolmogorovCyclePassed, false);
assert.equal(inconsistent.finiteObservedNetworkCycleConsistencyPassed, false);

const unpaired = buildFiniteTransitionNetwork(history.filter((record) => record.eventId !== "A-C"));
assert.equal(unpaired.unpairedEdgeCount, 1);
assert.equal(unpaired.independentCycleCount, 0);
assert.equal(unpaired.finiteObservedNetworkCycleConsistencyPassed, false);

const diverged = buildFiniteTransitionNetwork([...history, { ...transition("A", "B", 6),
  eventId: "diverged", committedStateSha256: states.C,
  exactFinalGeometryReproduced: false }]);
assert.equal(diverged.excludedPostStateDivergenceCount, 1);
assert.equal(diverged.pairedEdgeCount, 3);

console.log("finite transition network: passed");
