import assert from "node:assert/strict";
import {
  BOLTZMANN_ELECTRON_VOLT_PER_KELVIN,
  COULOMB_ENERGY_ELECTRON_VOLT_ANGSTROM,
  finitePointChargeReachProfile,
  incrementalFinitePointChargeElectrostatics,
} from "./finite-point-charge-electrostatics.mjs";

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
assert.equal(pair.thermalEnergyElectronVolt,
  BOLTZMANN_ELECTRON_VOLT_PER_KELVIN * 300);

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

const profile = finitePointChargeReachProfile(
  [{ position: [0, 0, 0], charge: 1 }],
  [{ position: [3, 0, 0], charge: -1 }],
  { nearestNeighborAngstrom: 1, relativePermittivity: 5, temperatureKelvin: 500 });
assert.deepEqual(profile.reaches, [2, 4, 8, "global"]);
assert.equal(profile.samples[0].available, false);
assert.equal(profile.samples[1].available, true);
assert.equal(profile.samples.at(-1).reachAngstrom, "global");
assert.equal(profile.targetUsed, false);

assert.throws(() => incrementalFinitePointChargeElectrostatics(
  [{ position: [0, 0, 0], charge: 1 }], [{ position: [0, 0, 0], charge: -1 }]),
/singular/);
assert.throws(() => incrementalFinitePointChargeElectrostatics(
  [{ position: [0, 0, 0], charge: 1 }], [{ position: [1, 0, 0], charge: -1 }],
  { relativePermittivity: .5 }), /relativePermittivity/);

console.log("finite point-charge electrostatics tests passed");
