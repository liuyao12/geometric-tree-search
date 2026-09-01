import assert from "node:assert/strict";
import { finiteDampedChargeInductionEnergy, incrementalFiniteChargeInduction,
  tangToenniesChargeDamping, tangToenniesDipoleField } from "./finite-charge-induction.mjs";

const close = (actual, expected, tolerance = 1e-10) => assert.ok(
  Math.abs(actual - expected) <= tolerance * Math.max(1, Math.abs(actual), Math.abs(expected)),
  `${actual} != ${expected}`);

close(tangToenniesChargeDamping(0), 0);
assert.ok(tangToenniesChargeDamping(.01) > 0);
assert.ok(tangToenniesChargeDamping(2) > tangToenniesChargeDamping(1));
assert.ok(tangToenniesChargeDamping(30) > .999999);

const sites = [
  { species: "Na", charge: 1, position: [-1.2, 0, 0] },
  { species: "Cl", charge: -1, position: [1.1, .2, 0] },
  { species: "Na", charge: 1, position: [0, 1.7, .4] },
];
const audit = finiteDampedChargeInductionEnergy(sites, {
  polarizabilityAngstrom3: 2,
  dampingLengthAngstrom: .35,
  reachAngstrom: "global",
});
assert.ok(audit.energyElectronVolt < 0);
assert.ok(audit.maximumInducedDipoleElectronAngstrom > 0);
assert.equal(audit.includedDirectedPairs, 6);
assert.equal(audit.mutualDipoleInductionSolved, false);

const transformed = sites.slice().reverse().map((site) => ({ ...site,
  position: [-site.position[1] + 4, site.position[0] - 3, site.position[2] + 2] }));
const transformedAudit = finiteDampedChargeInductionEnergy(transformed, {
  polarizabilityAngstrom3: 2, dampingLengthAngstrom: .35 });
close(transformedAudit.energyElectronVolt, audit.energyElectronVolt);
close(transformedAudit.maximumInducedDipoleElectronAngstrom,
  audit.maximumInducedDipoleElectronAngstrom);
const screenedAudit = finiteDampedChargeInductionEnergy(sites, {
  polarizabilityAngstrom3: 2, dampingLengthAngstrom: .35, relativePermittivity: 4 });
close(screenedAudit.energyElectronVolt, audit.energyElectronVolt / 16);
close(screenedAudit.maximumInducedDipoleElectronAngstrom,
  audit.maximumInducedDipoleElectronAngstrom / 4);

const zero = finiteDampedChargeInductionEnergy(sites, { polarizabilityAngstrom3: 0 });
close(zero.energyElectronVolt, 0);
assert.equal(zero.available, false);
const zeroMutual = incrementalFiniteChargeInduction(sites.slice(0, 2), sites.slice(2), {
  polarizabilityAngstrom3: 0, responseModel: "self-consistent" });
assert.equal(zeroMutual.appliedResponseModel, "off");
assert.equal(zeroMutual.mutualDipoleInductionSolved, false);
assert.equal(zeroMutual.energyIsManyBodyInChargeGeometry, false);

const incremental = incrementalFiniteChargeInduction(sites.slice(0, 2), sites.slice(2), {
  polarizabilityAngstrom3: 2, dampingLengthAngstrom: .35 });
close(incremental.deltaEnergyElectronVolt,
  audit.energyElectronVolt - finiteDampedChargeInductionEnergy(sites.slice(0, 2), {
    polarizabilityAngstrom3: 2, dampingLengthAngstrom: .35 }).energyElectronVolt);
assert.equal(incremental.energyIsManyBodyInChargeGeometry, true);
assert.equal(incremental.polarizationForceEvaluated, false);
assert.equal(incremental.targetUsed, false);

const axialDipoleField = tangToenniesDipoleField([2, 0, 0], [1, 0, 0], .35);
assert.ok(axialDipoleField[0] > 0);
close(axialDipoleField[1], 0);
close(axialDipoleField[2], 0);

const mutual = finiteDampedChargeInductionEnergy(sites, {
  polarizabilityAngstrom3: 2,
  dampingLengthAngstrom: .35,
  responseModel: "self-consistent",
  maximumIterations: 128,
});
assert.equal(mutual.selfConsistentConverged, true);
assert.equal(mutual.mutualDipoleInductionSolved, true);
assert.equal(mutual.appliedResponseModel, "self-consistent");
assert.ok(mutual.convergenceIterations > 1);
assert.ok(mutual.mutualTensorEvaluations > 0);
assert.ok(Math.abs(mutual.energyElectronVolt - audit.energyElectronVolt) > 1e-5);

const mutualTransformed = finiteDampedChargeInductionEnergy(transformed, {
  polarizabilityAngstrom3: 2,
  dampingLengthAngstrom: .35,
  responseModel: "self-consistent",
  maximumIterations: 128,
});
close(mutualTransformed.energyElectronVolt, mutual.energyElectronVolt, 1e-8);
close(mutualTransformed.maximumInducedDipoleElectronAngstrom,
  mutual.maximumInducedDipoleElectronAngstrom, 1e-8);

const mutualIncremental = incrementalFiniteChargeInduction(sites.slice(0, 2), sites.slice(2), {
  polarizabilityAngstrom3: 2,
  dampingLengthAngstrom: .35,
  responseModel: "self-consistent",
  maximumIterations: 128,
});
assert.equal(mutualIncremental.mutualDipoleInductionSolved, true);
assert.equal(mutualIncremental.directFallbackApplied, false);
close(mutualIncremental.deltaEnergyElectronVolt,
  mutual.energyElectronVolt - finiteDampedChargeInductionEnergy(sites.slice(0, 2), {
    polarizabilityAngstrom3: 2,
    dampingLengthAngstrom: .35,
    responseModel: "self-consistent",
    maximumIterations: 128,
  }).energyElectronVolt, 1e-8);

const failedMutual = incrementalFiniteChargeInduction(sites.slice(0, 2), sites.slice(2), {
  polarizabilityAngstrom3: 4,
  dampingLengthAngstrom: .35,
  responseModel: "self-consistent",
  maximumIterations: 1,
  convergenceToleranceElectronAngstrom: 1e-14,
});
assert.equal(failedMutual.directFallbackApplied, true);
assert.equal(failedMutual.appliedResponseModel, "direct");
assert.equal(failedMutual.mutualDipoleInductionSolved, false);
assert.ok(failedMutual.fallbackReason.includes("did not converge"));
close(failedMutual.deltaEnergyElectronVolt,
  incrementalFiniteChargeInduction(sites.slice(0, 2), sites.slice(2), {
    polarizabilityAngstrom3: 4,
    dampingLengthAngstrom: .35,
  }).deltaEnergyElectronVolt);
assert.throws(() => finiteDampedChargeInductionEnergy(sites, {
  polarizabilityAngstrom3: 1, responseModel: "oracle" }), /responseModel/);

const oppositeField = finiteDampedChargeInductionEnergy([
  { charge: 0, position: [0, 0, 0] },
  { charge: 1, position: [-1, 0, 0] },
  { charge: 1, position: [1, 0, 0] },
], { polarizabilityAngstrom3: 1, dampingLengthAngstrom: .2 });
close(oppositeField.electricFieldGeometryPerAngstrom2[0][0], 0);

console.log("finite charge induction tests passed");
