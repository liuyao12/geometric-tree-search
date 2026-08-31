import assert from "node:assert/strict";
import { appendCommittedTransition, auditMicroscopicInversePair,
  normalizedCommittedTransition } from "../apps/iqc-growth-live/reversible-transition-lineage.mjs";

const digest = (letter) => letter.repeat(64);
const thermalEnergy = 8.617333262145e-5 * 600;
const base = {
  eventId: "attach-event", candidateId: "attach:1", requestSha256: digest("a"),
  responseSha256: digest("b"), eventDirection: "attach",
  initialGeometrySha256: digest("c"), finalGeometrySha256: digest("d"),
  committedStateSha256: digest("d"), exactFinalGeometryReproduced: true,
  barrierElectronVolt: .8, barrierUncertaintyElectronVolt: .02,
  energyDeltaElectronVolt: .3, energyDeltaUncertaintyElectronVolt: .01,
  attemptFrequencyPerSecond: 1e13, attemptFrequencyUncertaintyLog10: .1,
  logRatePerSecond: 4, temperatureKelvin: 600,
  methodSettingsSha256: digest("e"), prefactorSettingsSha256: digest("f"),
  speciesDelta: { Na: 1 }, thermodynamicEvidenceSha256: digest("3"),
  freeEnergySettingsSha256: digest("4"), chemicalPotentialSettingsSha256: digest("5"),
  thermodynamicTemperatureKelvin: 600,
  systemFreeEnergyDeltaElectronVolt: -3 * thermalEnergy - .2,
  systemFreeEnergyDeltaUncertaintyElectronVolt: .008,
  reservoirChemicalWorkElectronVolt: -.2,
  reservoirChemicalWorkUncertaintyElectronVolt: .006,
  grandPotentialDeltaElectronVolt: -3 * thermalEnergy,
  grandPotentialDeltaUncertaintyElectronVolt: .01,
};
const reverse = { ...base, eventId: "detach-event", candidateId: "detach:1",
  requestSha256: digest("1"), responseSha256: digest("2"), eventDirection: "detach",
  initialGeometrySha256: digest("d"), finalGeometrySha256: digest("c"),
  committedStateSha256: digest("c"), barrierElectronVolt: .5,
  energyDeltaElectronVolt: -.3, logRatePerSecond: 1,
  speciesDelta: { Na: -1 }, thermodynamicEvidenceSha256: digest("6"),
  systemFreeEnergyDeltaElectronVolt: 3 * thermalEnergy + .2,
  reservoirChemicalWorkElectronVolt: .2,
  grandPotentialDeltaElectronVolt: 3 * thermalEnergy,
};

const audit = auditMicroscopicInversePair(base, reverse);
assert.equal(audit.geometryCycleClosed, true);
assert.equal(audit.oppositeDirections, true);
assert.equal(audit.energyDeltaCycleResidualElectronVolt, 0);
assert.ok(Math.abs(audit.transitionStateClosureResidualElectronVolt) < 1e-12);
assert.equal(audit.microscopicPathClosurePassed, true);
assert.equal(audit.logRateRatio, 3);
assert.equal(audit.thermodynamicDetailedBalanceCertified, false);
assert.equal(audit.reservoirChemicalPotentialUsed, true);
assert.equal(audit.grandCanonicalEvidenceComplete, true);
assert.equal(audit.speciesTransferReversed, true);
assert.ok(Math.abs(audit.localBalanceLogResidual) < 1e-12);
assert.ok(Math.abs(audit.localBalancePredictedLogRateRatio - 3) < 1e-12);
assert.equal(audit.grandPotentialCyclePassed, true);
assert.equal(audit.localBalanceResidualPassed, true);
assert.equal(audit.finitePairLocalBalancePassed, true);
assert.equal(audit.globalDetailedBalanceCertified, false);

let ledger = appendCommittedTransition([], base);
assert.equal(ledger.inverseAudit, null);
ledger = appendCommittedTransition(ledger.history, reverse);
assert.equal(ledger.inverseEventId, "attach-event");
assert.equal(ledger.exactInversePairCount, 1);
assert.equal(ledger.inverseAudit.microscopicPathClosurePassed, true);

const inconsistent = auditMicroscopicInversePair(base, { ...reverse,
  energyDeltaElectronVolt: -.1, barrierElectronVolt: .7 });
assert.equal(inconsistent.geometryCycleClosed, true);
assert.equal(inconsistent.energyDeltaCyclePassed, false);
assert.equal(inconsistent.transitionStateClosurePassed, false);
assert.equal(inconsistent.microscopicPathClosurePassed, false);
assert.equal(inconsistent.finitePairLocalBalancePassed, false);

const reservoirMismatch = auditMicroscopicInversePair(base, { ...reverse,
  chemicalPotentialSettingsSha256: digest("7") });
assert.equal(reservoirMismatch.sameThermodynamicSettings, false);
assert.equal(reservoirMismatch.finitePairLocalBalancePassed, false);
assert.equal(auditMicroscopicInversePair(base, { ...reverse,
  speciesDelta: { Na: -2 } }).finitePairLocalBalancePassed, false);

const geometryOnly = auditMicroscopicInversePair({ ...base,
  energyDeltaElectronVolt: null, energyDeltaUncertaintyElectronVolt: null }, { ...reverse,
  energyDeltaElectronVolt: null, energyDeltaUncertaintyElectronVolt: null });
assert.equal(geometryOnly.geometryCycleClosed, true);
assert.equal(geometryOnly.energyEvidenceComplete, false);
assert.equal(geometryOnly.microscopicPathClosurePassed, false);

assert.throws(() => normalizedCommittedTransition({ ...base,
  energyDeltaUncertaintyElectronVolt: null }), /supplied together/);
assert.throws(() => appendCommittedTransition([base], base), /duplicate/);
assert.equal(auditMicroscopicInversePair(base, { ...reverse,
  committedStateSha256: digest("9"), exactFinalGeometryReproduced: true })
  .microscopicPathClosurePassed, false);

const exchangeForward = { ...base, eventId: "exchange-forward",
  candidateId: "exchange:Na->Cl", eventDirection: "exchange",
  speciesDelta: { Cl: 1, Na: -1 }, initialAtomCount: 12, finalAtomCount: 12 };
const exchangeReverse = { ...reverse, eventId: "exchange-reverse",
  candidateId: "exchange:Cl->Na", eventDirection: "exchange",
  speciesDelta: { Cl: -1, Na: 1 }, initialAtomCount: 12, finalAtomCount: 12 };
const exchangeAudit = auditMicroscopicInversePair(exchangeForward, exchangeReverse);
assert.equal(exchangeAudit.geometryCycleClosed, true);
assert.equal(exchangeAudit.oppositeDirections, false);
assert.equal(exchangeAudit.directionPairCanReverse, true);
assert.equal(exchangeAudit.speciesTransferReversed, true);
const exchangeLedger = appendCommittedTransition(
  appendCommittedTransition([], exchangeForward).history, exchangeReverse);
assert.equal(exchangeLedger.inverseEventId, "exchange-forward");

console.log("reversible transition lineage: passed");
