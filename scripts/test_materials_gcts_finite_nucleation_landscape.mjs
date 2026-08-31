import assert from "node:assert/strict";
import { buildFiniteNucleationLandscape }
  from "../apps/iqc-growth-live/finite-nucleation-landscape.mjs";

const states = ["a".repeat(64), "b".repeat(64), "c".repeat(64)];
const directed = (from, to, fromCount, toCount, omega) => ({
  key: `${from}->${to}`, fromStateSha256: from, toStateSha256: to,
  initialAtomCount: fromCount, finalAtomCount: toCount,
  grandPotentialDeltaElectronVolt: omega,
  grandPotentialDeltaUncertaintyElectronVolt: .01,
  temperatureKelvin: 600,
  freeEnergySettingsSha256: "1".repeat(64),
  chemicalPotentialSettingsSha256: "2".repeat(64),
});
const pair = (low, high, omega) => ({
  key: `${low}<->${high}`, lowStateSha256: low, highStateSha256: high,
  grandPotentialDeltaElectronVolt: omega,
  grandPotentialDeltaUncertaintyElectronVolt: .01,
  pairAudit: { grandCanonicalEvidenceComplete: true, grandPotentialCyclePassed: true },
});
const network = {
  schema: "gcts-finite-transition-network-v1",
  nodes: states.map((stateSha256, index) => ({ stateSha256, stateId: `S${index + 1}` })),
  directedEdges: [
    directed(states[0], states[1], 10, 11, .08),
    directed(states[1], states[0], 11, 10, -.08),
    directed(states[1], states[2], 11, 12, -.11),
    directed(states[2], states[1], 12, 11, .11),
    directed(states[0], states[2], 10, 12, -.03),
    directed(states[2], states[0], 12, 10, .03),
  ],
  pairedEdges: [pair(states[0], states[1], .08), pair(states[1], states[2], -.11),
    pair(states[0], states[2], -.03)],
};

const landscape = buildFiniteNucleationLandscape(network);
assert.equal(landscape.evidenceAvailable, true);
assert.equal(landscape.states.length, 3);
assert.equal(landscape.finiteProfileConsistencyPassed, true);
assert.equal(landscape.criticalSizeCandidateObserved, true);
assert.equal(landscape.criticalAtomCount, 11);
assert.ok(Math.abs(landscape.observedFormationBarrierElectronVolt - .08) < 1e-12);
assert.equal(landscape.nucleationRateInferred, false);
assert.equal(landscape.classicalNucleationTheoryFit, false);
assert.equal(landscape.targetUsed, false);

const permuted = buildFiniteNucleationLandscape({ ...network,
  nodes: [...network.nodes].reverse(), directedEdges: [...network.directedEdges].reverse(),
  pairedEdges: [...network.pairedEdges].reverse() });
assert.deepEqual(permuted.states.map((state) => state.atomCount), [10, 11, 12]);
assert.equal(permuted.criticalAtomCount, 11);

const inconsistentCycle = buildFiniteNucleationLandscape({ ...network,
  pairedEdges: network.pairedEdges.map((entry) => entry.key.includes(`${states[0]}<->${states[2]}`)
    ? { ...entry, grandPotentialDeltaElectronVolt: .2 } : entry) });
assert.equal(inconsistentCycle.finiteProfileConsistencyPassed, false);

const inconsistentCount = buildFiniteNucleationLandscape({ ...network,
  directedEdges: network.directedEdges.map((entry) => entry.key === `${states[1]}->${states[2]}`
    ? { ...entry, initialAtomCount: 99 } : entry) });
assert.equal(inconsistentCount.evidenceAvailable, false);

const absent = buildFiniteNucleationLandscape({ ...network, pairedEdges: [] });
assert.equal(absent.evidenceAvailable, false);
assert.equal(absent.criticalSizeCandidateObserved, false);

console.log("finite nucleation grand-potential landscape: passed");
