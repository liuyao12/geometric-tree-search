import assert from "node:assert/strict";
import {
  BOLTZMANN_ELECTRON_VOLT_PER_KELVIN,
  COULOMB_ENERGY_ELECTRON_VOLT_ANGSTROM,
  TANG_TOENNIES_DISPERSION_ORDER,
  finitePointChargeReachProfile,
  incrementalFinitePointChargeElectrostatics,
  tangToenniesDamping,
  tangToenniesDampingDerivative,
} from "./finite-point-charge-electrostatics.mjs";
import { buildBornMayerPairMatrix } from "./born-mayer-pair-matrix.mjs";

const pair = incrementalFinitePointChargeElectrostatics(
  [{ position: [0, 0, 0], charge: 1 }],
  [{ position: [2.82, 0, 0], charge: -1 }],
  { relativePermittivity: 1, temperatureKelvin: 300 });
assert.equal(pair.available, true);
assert.equal(pair.pairCount, 1);
assert.ok(Math.abs(pair.deltaEnergyElectronVolt
  + COULOMB_ENERGY_ELECTRON_VOLT_ANGSTROM / 2.82) < 1e-12);
assert.equal(pair.attractiveEnergyElectronVolt, -pair.deltaEnergyElectronVolt);
assert.equal(pair.repulsiveEnergyElectronVolt, 0);
assert.ok(pair.score > 0 && pair.score < 1);
assert.ok(Math.abs(pair.addedForceVectorsElectronVoltPerAngstrom[0][0]
  + COULOMB_ENERGY_ELECTRON_VOLT_ANGSTROM / 2.82 ** 2) < 1e-12);
assert.deepEqual(pair.addedForceVectorsElectronVoltPerAngstrom[0].slice(1), [0, 0]);
assert.equal(pair.currentIncrementalPairForceRecords.length, 1);
assert.equal(pair.currentIncrementalPairForceRecords[0].currentIndex, 0);
assert.ok(Math.abs(pair.currentIncrementalPairForceRecords[0]
  .pairForceVectorElectronVoltPerAngstrom[0]
  + pair.addedPairForceVectorsElectronVoltPerAngstrom[0][0]) < 1e-12);
assert.ok(pair.pairActionReactionResidualMagnitudeElectronVoltPerAngstrom < 1e-12);
assert.equal(pair.currentIncrementalPairForceFieldResolved, true);
assert.equal(pair.currentCurrentForceFieldOmittedAsConstant, true);
assert.equal(pair.currentInductionForceFieldResolved, false);
assert.equal(pair.configurationalPairVirialResolved, true);
assert.equal(pair.pairVirialDividedByVolume, false);
assert.equal(pair.pairVirialReportedAsStress, false);
assert.ok(pair.pairVirialTraceElectronVolt < 0);
assert.ok(Math.abs(pair.pairVirialTensorElectronVolt[0][0]
  - 2.82 * pair.addedPairForceVectorsElectronVoltPerAngstrom[0][0]) < 1e-12);
assert.equal(pair.pairVirialTensorElectronVolt[1][1], 0);
assert.ok(pair.pairVirialAntisymmetricFrobeniusElectronVolt < 1e-12);
assert.equal(pair.rmsAddedForceElectronVoltPerAngstrom,
  pair.maximumAddedForceElectronVoltPerAngstrom);
assert.equal(pair.netAddedForceMagnitudeElectronVoltPerAngstrom,
  pair.maximumAddedForceElectronVoltPerAngstrom);
assert.equal(pair.electrostaticTorqueMagnitudeElectronVolt, 0);
assert.equal(pair.electrostaticForceEvaluated, true);
assert.equal(pair.totalMechanicalForceInferred, false);
assert.equal(pair.thermalEnergyElectronVolt,
  BOLTZMANN_ELECTRON_VOLT_PER_KELVIN * 300);

const forceRanked = incrementalFinitePointChargeElectrostatics(
  [{ position: [0, 0, 0], charge: 1 }],
  [{ position: [2.82, 0, 0], charge: -1 }],
  { relativePermittivity: 1, temperatureKelvin: 300,
    forceReferenceLengthAngstrom: 2.82, rankingObservable: "force-cancellation" });
assert.equal(forceRanked.score, forceRanked.forceCancellationScore);
assert.notEqual(forceRanked.score, forceRanked.energyScore);
const combined = incrementalFinitePointChargeElectrostatics(
  [{ position: [0, 0, 0], charge: 1 }],
  [{ position: [2.82, 0, 0], charge: -1 }],
  { relativePermittivity: 1, temperatureKelvin: 300,
    forceReferenceLengthAngstrom: 2.82, rankingObservable: "combined" });
assert.equal(combined.score, (combined.energyScore + combined.forceCancellationScore) / 2);

const bornAmplitude = 1000;
const bornDecay = .3;
const bornPair = incrementalFinitePointChargeElectrostatics(
  [{ position: [0, 0, 0], charge: 1 }],
  [{ position: [2.82, 0, 0], charge: -1 }],
  { relativePermittivity: 1, temperatureKelvin: 300,
    bornMayerAmplitudeElectronVolt: bornAmplitude,
    bornMayerDecayAngstrom: bornDecay });
const expectedBornEnergy = bornAmplitude * Math.exp(-2.82 / bornDecay);
assert.ok(Math.abs(bornPair.bornMayerRepulsiveEnergyElectronVolt - expectedBornEnergy) < 1e-12);
assert.ok(Math.abs(bornPair.deltaEnergyElectronVolt
  - (pair.deltaEnergyElectronVolt + expectedBornEnergy)) < 1e-12);
assert.ok(Math.abs(bornPair.addedBornMayerForceVectorsElectronVoltPerAngstrom[0][0]
  - expectedBornEnergy / bornDecay) < 1e-12);
assert.ok(Math.abs(bornPair.addedForceVectorsElectronVoltPerAngstrom[0][0]
  - (pair.addedForceVectorsElectronVoltPerAngstrom[0][0] + expectedBornEnergy / bornDecay)) < 1e-12);
assert.equal(bornPair.pairInteractionModel, "Coulomb + Born–Mayer");
assert.equal(bornPair.bornMayerRepulsionApplied, true);

assert.equal(TANG_TOENNIES_DISPERSION_ORDER, 6);
assert.equal(tangToenniesDamping(6, 0), 0);
assert.ok(tangToenniesDamping(6, .01) > 0);
assert.ok(tangToenniesDamping(6, 20) > .99);
assert.ok(tangToenniesDampingDerivative(6, 2) > 0);
const dispersionC6 = 100;
const dispersionPair = incrementalFinitePointChargeElectrostatics(
  [{ position: [0, 0, 0], charge: 1 }],
  [{ position: [2.82, 0, 0], charge: -1 }],
  { relativePermittivity: 1, temperatureKelvin: 300,
    bornMayerAmplitudeElectronVolt: bornAmplitude,
    bornMayerDecayAngstrom: bornDecay,
    dispersionC6ElectronVoltAngstrom6: dispersionC6,
    dispersionDampingLengthAngstrom: bornDecay });
const expectedDispersionEnergy = -dispersionC6
  * tangToenniesDamping(6, 2.82 / bornDecay) / 2.82 ** 6;
assert.ok(Math.abs(dispersionPair.dampedDispersionEnergyElectronVolt
  - expectedDispersionEnergy) < 1e-12);
assert.equal(dispersionPair.dispersionApplied, true);
assert.equal(dispersionPair.dispersionParametersFitted, false);
assert.match(dispersionPair.pairInteractionModel, /damped dispersion/);
const dispersionEnergyAt = (x) => incrementalFinitePointChargeElectrostatics(
  [{ position: [0, 0, 0], charge: 1 }], [{ position: [x, 0, 0], charge: -1 }],
  { relativePermittivity: 4, temperatureKelvin: 300,
    bornMayerAmplitudeElectronVolt: bornAmplitude, bornMayerDecayAngstrom: bornDecay,
    dispersionC6ElectronVoltAngstrom6: dispersionC6,
    dispersionDampingLengthAngstrom: bornDecay }).deltaEnergyElectronVolt;
const dispersionFiniteDifferenceForce = -(dispersionEnergyAt(2.82 + 1e-5)
  - dispersionEnergyAt(2.82 - 1e-5)) / 2e-5;
const dispersionAnalyticForce = incrementalFinitePointChargeElectrostatics(
  [{ position: [0, 0, 0], charge: 1 }], [{ position: [2.82, 0, 0], charge: -1 }],
  { relativePermittivity: 4, temperatureKelvin: 300,
    bornMayerAmplitudeElectronVolt: bornAmplitude, bornMayerDecayAngstrom: bornDecay,
    dispersionC6ElectronVoltAngstrom6: dispersionC6,
    dispersionDampingLengthAngstrom: bornDecay })
  .addedForceVectorsElectronVoltPerAngstrom[0][0];
assert.ok(Math.abs(dispersionFiniteDifferenceForce - dispersionAnalyticForce) < 1e-9);

const induced = incrementalFinitePointChargeElectrostatics(
  [{ position: [-1, 0, 0], charge: 1 }, { position: [1, 0, 0], charge: -1 }],
  [{ position: [0, 1.5, 0], charge: 1 }],
  { relativePermittivity: 4, temperatureKelvin: 300,
    bornMayerAmplitudeElectronVolt: bornAmplitude, bornMayerDecayAngstrom: bornDecay,
    dispersionC6ElectronVoltAngstrom6: dispersionC6,
    dispersionDampingLengthAngstrom: bornDecay,
    inductionPolarizabilityAngstrom3: 2,
    inductionDampingLengthAngstrom: bornDecay });
assert.notEqual(induced.chargeInductionDeltaEnergyElectronVolt, 0);
assert.equal(induced.chargeInductionApplied, true);
assert.equal(induced.chargeInductionEnergyIsManyBodyInChargeGeometry, true);
assert.equal(induced.mutualDipoleInductionSolved, false);
assert.equal(induced.polarizationForceEvaluated, false);
assert.equal(induced.pairInteractionForceIsNegativeEnergyGradient, false);
assert.match(induced.pairInteractionModel, /charge induction/);
assert.ok(induced.maximumInducedDipoleElectronAngstrom > 0);

const inducedWithForce = incrementalFinitePointChargeElectrostatics(
  [{ position: [-1, 0, 0], charge: 1 }, { position: [1, 0, 0], charge: -1 }],
  [{ position: [0, 1.5, 0], charge: 1 }],
  { relativePermittivity: 4, temperatureKelvin: 300,
    inductionPolarizabilityAngstrom3: 2, inductionDampingLengthAngstrom: bornDecay,
    inductionForceMode: "finite-difference" });
assert.equal(inducedWithForce.polarizationForceEvaluated, true);
assert.equal(inducedWithForce.inductionForceAvailable, true);
assert.equal(inducedWithForce.inductionForceEnergyEvaluations, 12);
assert.equal(inducedWithForce.pairInteractionForceIsNegativeEnergyGradient, true);
assert.ok(inducedWithForce.addedInductionForceVectorsElectronVoltPerAngstrom[0]
  .some((value) => Math.abs(value) > 1e-9));
assert.ok(inducedWithForce.inductionForceMaximumRichardsonErrorElectronVoltPerAngstrom < 1e-7);
const inducedEnergyAt = (y) => incrementalFinitePointChargeElectrostatics(
  [{ position: [-1, 0, 0], charge: 1 }, { position: [1, 0, 0], charge: -1 }],
  [{ position: [0, y, 0], charge: 1 }],
  { relativePermittivity: 4, temperatureKelvin: 300,
    inductionPolarizabilityAngstrom3: 2, inductionDampingLengthAngstrom: bornDecay })
  .deltaEnergyElectronVolt;
const inducedTotalGradient = -(inducedEnergyAt(1.50001) - inducedEnergyAt(1.49999)) / 2e-5;
assert.ok(Math.abs(inducedWithForce.addedForceVectorsElectronVoltPerAngstrom[0][1]
  - inducedTotalGradient) < 1e-7);

const mutuallyInduced = incrementalFinitePointChargeElectrostatics(
  [{ position: [-1, 0, 0], charge: 1 }, { position: [1, 0, 0], charge: -1 }],
  [{ position: [0, 1.5, 0], charge: 1 }],
  { relativePermittivity: 4, temperatureKelvin: 300,
    bornMayerAmplitudeElectronVolt: bornAmplitude, bornMayerDecayAngstrom: bornDecay,
    dispersionC6ElectronVoltAngstrom6: dispersionC6,
    dispersionDampingLengthAngstrom: bornDecay,
    inductionPolarizabilityAngstrom3: 2,
    inductionDampingLengthAngstrom: bornDecay,
    inductionResponseModel: "self-consistent",
    inductionMaximumIterations: 128,
    inductionConvergenceToleranceElectronAngstrom: 1e-6 });
assert.equal(mutuallyInduced.inductionRequestedResponseModel, "self-consistent");
assert.equal(mutuallyInduced.inductionAppliedResponseModel, "self-consistent");
assert.equal(mutuallyInduced.inductionSelfConsistentConverged, true);
assert.equal(mutuallyInduced.mutualDipoleInductionSolved, true);
assert.equal(mutuallyInduced.inductionDirectFallbackApplied, false);
assert.ok(mutuallyInduced.inductionMutualTensorEvaluations > 0);
assert.ok(mutuallyInduced.inductionConvergenceIterations > 0);
assert.notEqual(mutuallyInduced.chargeInductionDeltaEnergyElectronVolt,
  induced.chargeInductionDeltaEnergyElectronVolt);
const mutuallyInducedWithForce = incrementalFinitePointChargeElectrostatics(
  [{ position: [-1, 0, 0], charge: 1 }, { position: [1, 0, 0], charge: -1 }],
  [{ position: [0, 1.5, 0], charge: 1 }],
  { relativePermittivity: 4, temperatureKelvin: 300,
    inductionPolarizabilityAngstrom3: 2, inductionDampingLengthAngstrom: bornDecay,
    inductionResponseModel: "self-consistent", inductionForceMode: "finite-difference",
    inductionMaximumIterations: 128, inductionConvergenceToleranceElectronAngstrom: 1e-6 });
assert.equal(mutuallyInducedWithForce.mutualDipoleInductionSolved, true);
assert.equal(mutuallyInducedWithForce.inductionForceAvailable, true);
assert.equal(mutuallyInducedWithForce.inductionForceResponseConsistent, true);

const speciesPairMatrix = buildBornMayerPairMatrix(["Na", "Cl"], {
  available: true, radiiAngstrom: { Na: 1.1, Cl: 1.7 },
  selectedPairCount: 2, rmsResidualAngstrom: .02,
}, { policy: "contact-scaled", amplitudeElectronVolt: 1000, decayAngstrom: .3 });
const matrixPair = incrementalFinitePointChargeElectrostatics(
  [{ position: [0, 0, 0], charge: 1, species: "Na" }],
  [{ position: [2.82, 0, 0], charge: -1, species: "Cl" }],
  { relativePermittivity: 1, temperatureKelvin: 300,
    bornMayerAmplitudeElectronVolt: 1000, bornMayerDecayAngstrom: .3,
    bornMayerPairMatrix: speciesPairMatrix });
const naClParameter = speciesPairMatrix.records.find((record) => record.species.join("-") === "Cl-Na");
const expectedMatrixBornEnergy = naClParameter.amplitudeElectronVolt
  * Math.exp(-2.82 / naClParameter.decayAngstrom);
assert.ok(Math.abs(matrixPair.bornMayerRepulsiveEnergyElectronVolt
  - expectedMatrixBornEnergy) < 1e-12);
assert.equal(matrixPair.bornMayerPairMatrixApplied, true);
assert.equal(matrixPair.bornMayerPairPolicy, "contact-scaled");
assert.equal(matrixPair.bornMayerPairMatrixFallbackCount, 0);
assert.equal(matrixPair.bornMayerPairParameterUsage[0].key, naClParameter.key);
assert.equal(matrixPair.pairInteractionModel, "Coulomb + Born–Mayer species-pair matrix");
const matrixEnergyAt = (x) => incrementalFinitePointChargeElectrostatics(
  [{ position: [0, 0, 0], charge: 1, species: "Na" }],
  [{ position: [x, 0, 0], charge: -1, species: "Cl" }],
  { relativePermittivity: 4, temperatureKelvin: 300,
    bornMayerAmplitudeElectronVolt: 1000, bornMayerDecayAngstrom: .3,
    bornMayerPairMatrix: speciesPairMatrix }).deltaEnergyElectronVolt;
const matrixFiniteDifferenceForce = -(matrixEnergyAt(2.82 + 1e-5) - matrixEnergyAt(2.82 - 1e-5)) / 2e-5;
const matrixAnalyticForce = incrementalFinitePointChargeElectrostatics(
  [{ position: [0, 0, 0], charge: 1, species: "Na" }],
  [{ position: [2.82, 0, 0], charge: -1, species: "Cl" }],
  { relativePermittivity: 4, temperatureKelvin: 300,
    bornMayerAmplitudeElectronVolt: 1000, bornMayerDecayAngstrom: .3,
    bornMayerPairMatrix: speciesPairMatrix }).addedForceVectorsElectronVoltPerAngstrom[0][0];
assert.ok(Math.abs(matrixFiniteDifferenceForce - matrixAnalyticForce) < 1e-9);
assert.throws(() => incrementalFinitePointChargeElectrostatics(
  [{ position: [0, 0, 0], charge: 1 }],
  [{ position: [2.82, 0, 0], charge: -1 }],
  { bornMayerPairMatrix: speciesPairMatrix }), /species tokens/);

const bornDisplacedEnergy = (x) => incrementalFinitePointChargeElectrostatics(
  [{ position: [0, 0, 0], charge: 1 }], [{ position: [x, 0, 0], charge: -1 }],
  { relativePermittivity: 4, temperatureKelvin: 300,
    bornMayerAmplitudeElectronVolt: bornAmplitude, bornMayerDecayAngstrom: bornDecay })
  .deltaEnergyElectronVolt;
const bornFiniteDifferenceStep = 1e-5;
const bornFiniteDifferenceForce = -(bornDisplacedEnergy(2.82 + bornFiniteDifferenceStep)
  - bornDisplacedEnergy(2.82 - bornFiniteDifferenceStep)) / (2 * bornFiniteDifferenceStep);
const bornAnalyticForce = incrementalFinitePointChargeElectrostatics(
  [{ position: [0, 0, 0], charge: 1 }], [{ position: [2.82, 0, 0], charge: -1 }],
  { relativePermittivity: 4, temperatureKelvin: 300,
    bornMayerAmplitudeElectronVolt: bornAmplitude, bornMayerDecayAngstrom: bornDecay })
  .addedForceVectorsElectronVoltPerAngstrom[0][0];
assert.ok(Math.abs(bornFiniteDifferenceForce - bornAnalyticForce) < 1e-9);

const finiteDifferenceStep = 1e-5;
const displacedEnergy = (x) => incrementalFinitePointChargeElectrostatics(
  [{ position: [0, 0, 0], charge: 1 }], [{ position: [x, 0, 0], charge: -1 }],
  { relativePermittivity: 4, temperatureKelvin: 300 }).deltaEnergyElectronVolt;
const finiteDifferenceForce = -(displacedEnergy(2.82 + finiteDifferenceStep)
  - displacedEnergy(2.82 - finiteDifferenceStep)) / (2 * finiteDifferenceStep);
const analyticForce = incrementalFinitePointChargeElectrostatics(
  [{ position: [0, 0, 0], charge: 1 }], [{ position: [2.82, 0, 0], charge: -1 }],
  { relativePermittivity: 4, temperatureKelvin: 300 })
  .addedForceVectorsElectronVoltPerAngstrom[0][0];
assert.ok(Math.abs(finiteDifferenceForce - analyticForce) < 1e-9);

const transformed = incrementalFinitePointChargeElectrostatics(
  [{ position: [4, -2, 7], charge: 1 }], [{ position: [4, .82, 7], charge: -1 }],
  { relativePermittivity: 1, temperatureKelvin: 300 });
assert.ok(Math.abs(transformed.deltaEnergyElectronVolt - pair.deltaEnergyElectronVolt) < 1e-12);
assert.ok(Math.abs(transformed.addedForceVectorsElectronVoltPerAngstrom[0][1]
  - pair.addedForceVectorsElectronVoltPerAngstrom[0][0]) < 1e-12);
assert.ok(Math.abs(transformed.pairVirialTensorElectronVolt[1][1]
  - pair.pairVirialTensorElectronVolt[0][0]) < 1e-12);
assert.ok(Math.abs(transformed.pairVirialTraceElectronVolt
  - pair.pairVirialTraceElectronVolt) < 1e-12);

const screened = incrementalFinitePointChargeElectrostatics(
  [{ position: [0, 0, 0], charge: 1 }],
  [{ position: [2.82, 0, 0], charge: -1 }],
  { relativePermittivity: 10, temperatureKelvin: 600 });
assert.ok(Math.abs(screened.deltaEnergyElectronVolt - pair.deltaEnergyElectronVolt / 10) < 1e-12);
assert.ok(Math.abs(screened.reducedThermalEnergyPerAddedSite
  - pair.reducedThermalEnergyPerAddedSite / 20) < 1e-12);

const addedPair = incrementalFinitePointChargeElectrostatics(
  [{ position: [0, 0, 0], charge: 1 }],
  [{ position: [2, 0, 0], charge: -1 }, { position: [4, 0, 0], charge: 1 }],
  { relativePermittivity: 4, temperatureKelvin: 300, reachAngstrom: 3 });
assert.equal(addedPair.pairCount, 2);
assert.equal(addedPair.currentCurrentConstantOmitted, true);
assert.equal(addedPair.periodicImagesUsed, false);
assert.equal(addedPair.electrostaticEnergyEvaluated, true);
assert.equal(addedPair.targetUsed, false);

const symmetric = incrementalFinitePointChargeElectrostatics(
  [{ position: [-1, 0, 0], charge: 1 }, { position: [1, 0, 0], charge: 1 }],
  [{ position: [0, 0, 0], charge: -1 }],
  { relativePermittivity: 1, temperatureKelvin: 300,
    forceReferenceLengthAngstrom: 1, rankingObservable: "force-cancellation" });
assert.ok(symmetric.rmsAddedForceElectronVoltPerAngstrom < 1e-12);
assert.ok(Math.abs(symmetric.forceCancellationScore - 1) < 1e-12);

const internalPair = incrementalFinitePointChargeElectrostatics(
  [{ position: [100, 0, 0], charge: 0 }],
  [{ position: [-1, 0, 0], charge: 1 }, { position: [1, 0, 0], charge: 1 }],
  { relativePermittivity: 1, temperatureKelvin: 300, reachAngstrom: 5 });
assert.equal(internalPair.pairCount, 1);
assert.ok(internalPair.addedForceVectorsElectronVoltPerAngstrom[0][0] < 0);
assert.ok(internalPair.addedForceVectorsElectronVoltPerAngstrom[1][0] > 0);
assert.ok(internalPair.netAddedForceMagnitudeElectronVoltPerAngstrom < 1e-12);

const profile = finitePointChargeReachProfile(
  [{ position: [0, 0, 0], charge: 1 }],
  [{ position: [3, 0, 0], charge: -1 }],
  { nearestNeighborAngstrom: 1, relativePermittivity: 5, temperatureKelvin: 500 });
assert.deepEqual(profile.reaches, [2, 4, 8, "global"]);
assert.equal(profile.samples[0].available, false);
assert.equal(profile.samples[1].available, true);
assert.equal(profile.samples.at(-1).reachAngstrom, "global");
assert.equal(profile.targetUsed, false);

const mutualProfile = finitePointChargeReachProfile(
  [{ position: [0, 0, 0], charge: 1 }, { position: [2, 0, 0], charge: -1 }],
  [{ position: [1, 1.5, 0], charge: 1 }],
  { nearestNeighborAngstrom: 1, relativePermittivity: 4, temperatureKelvin: 500,
    inductionPolarizabilityAngstrom3: 1,
    inductionResponseModel: "self-consistent",
    inductionMaximumIterations: 128,
    inductionConvergenceToleranceElectronAngstrom: 1e-6 });
assert.equal(mutualProfile.mutualDipoleInductionSolved, true);
assert.equal(mutualProfile.inductionDirectFallbackSamples, 0);
assert.ok(mutualProfile.inductionMutualTensorEvaluations > 0);
const forceProfile = finitePointChargeReachProfile(
  [{ position: [0, 0, 0], charge: 1 }, { position: [2, 0, 0], charge: -1 }],
  [{ position: [1, 1.5, 0], charge: 1 }],
  { nearestNeighborAngstrom: 1, relativePermittivity: 4, temperatureKelvin: 500,
    inductionPolarizabilityAngstrom3: 1, inductionForceMode: "finite-difference" });
assert.equal(forceProfile.polarizationForceEvaluated, true);
assert.ok(forceProfile.inductionForceEnergyEvaluations > 0);
assert.equal(forceProfile.inductionForceUnavailableSamples, 0);

assert.throws(() => incrementalFinitePointChargeElectrostatics(
  [{ position: [0, 0, 0], charge: 1 }], [{ position: [0, 0, 0], charge: -1 }]),
/singular/);
assert.throws(() => incrementalFinitePointChargeElectrostatics(
  [{ position: [0, 0, 0], charge: 1 }], [{ position: [1, 0, 0], charge: -1 }],
  { relativePermittivity: .5 }), /relativePermittivity/);
assert.throws(() => incrementalFinitePointChargeElectrostatics(
  [{ position: [0, 0, 0], charge: 1 }], [{ position: [1, 0, 0], charge: -1 }],
  { rankingObservable: "force-field" }), /rankingObservable/);
assert.throws(() => incrementalFinitePointChargeElectrostatics(
  [{ position: [0, 0, 0], charge: 1 }], [{ position: [1, 0, 0], charge: -1 }],
  { bornMayerAmplitudeElectronVolt: -1 }), /bornMayerAmplitudeElectronVolt/);

console.log("finite point-charge electrostatics tests passed");
