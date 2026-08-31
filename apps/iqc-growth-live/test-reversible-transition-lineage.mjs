import assert from "node:assert/strict";
import { appendCommittedTransition, auditMicroscopicInversePair }
  from "./reversible-transition-lineage.mjs";

const sha = (character) => character.repeat(64);
const temperatureKelvin = 600;
const inverseThermalEnergy = 1 / (8.617333262145e-5 * temperatureKelvin);
const base = {
  requestSha256: sha("1"), responseSha256: sha("2"), eventDirection: "hop",
  exactFinalGeometryReproduced: true, barrierUncertaintyElectronVolt: .01,
  energyDeltaUncertaintyElectronVolt: .01, attemptFrequencyPerSecond: 1e12,
  attemptFrequencyUncertaintyLog10: .02, temperatureKelvin,
  methodSettingsSha256: sha("3"), prefactorSettingsSha256: sha("4"),
  speciesDelta: {}, initialAtomCount: 20, finalAtomCount: 20,
  thermodynamicEvidenceSha256: sha("5"), freeEnergySettingsSha256: sha("6"),
  chemicalPotentialSettingsSha256: sha("7"), thermodynamicTemperatureKelvin: temperatureKelvin,
  systemFreeEnergyDeltaUncertaintyElectronVolt: .01,
  reservoirChemicalWorkElectronVolt: 0,
  reservoirChemicalWorkUncertaintyElectronVolt: 0,
  grandPotentialDeltaUncertaintyElectronVolt: .01,
};
const forward = { ...base, eventId: "hop-forward", candidateId: "a-to-b",
  initialGeometrySha256: sha("a"), finalGeometrySha256: sha("b"),
  committedStateSha256: sha("b"), barrierElectronVolt: .5,
  energyDeltaElectronVolt: .1, logRatePerSecond: 0,
  systemFreeEnergyDeltaElectronVolt: .1, grandPotentialDeltaElectronVolt: .1 };
const reverse = { ...base, eventId: "hop-reverse", candidateId: "b-to-a",
  initialGeometrySha256: sha("b"), finalGeometrySha256: sha("a"),
  committedStateSha256: sha("a"), barrierElectronVolt: .4,
  energyDeltaElectronVolt: -.1, logRatePerSecond: .1 * inverseThermalEnergy,
  systemFreeEnergyDeltaElectronVolt: -.1, grandPotentialDeltaElectronVolt: -.1 };

const audit = auditMicroscopicInversePair(forward, reverse);
assert.equal(audit.oppositeDirections, false);
assert.equal(audit.massConservingHopPair, true);
assert.equal(audit.directionPairCanReverse, true);
assert.equal(audit.geometryCycleClosed, true);
assert.equal(audit.speciesTransferReversed, true);
assert.equal(audit.microscopicPathClosurePassed, true);
assert.equal(audit.finitePairLocalBalancePassed, true);

const first = appendCommittedTransition([], forward);
const second = appendCommittedTransition(first.history, reverse);
assert.equal(second.inverseEventId, "hop-forward");
assert.equal(second.exactInversePairCount, 1);
assert.equal(second.inverseAudit.massConservingHopPair, true);

console.log("mass-conserving inverse surface-hop lineage tests passed");
