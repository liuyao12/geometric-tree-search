import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const root = new URL("../", import.meta.url);
const read = (path) => readFileSync(new URL(path, root), "utf8");
const app = read("apps/iqc-growth-live/app.js");
const html = read("apps/iqc-growth-live/index.html");
const compatibility = read("iqc-growth-live/index.html");
const moduleSource = read("apps/iqc-growth-live/finite-point-charge-electrostatics.mjs");
const pairMatrixSource = read("apps/iqc-growth-live/born-mayer-pair-matrix.mjs");
const readme = read("apps/iqc-growth-live/README.md");
const benchmark = read("docs/projects/materials-recursive-gcts-benchmark.md");
const atlas = read("apps/iqc-growth-live/evidence-atlas.js");

for (const document of [html, compatibility]) {
  for (const id of ["ionicPairDielectricSelect", "ionicPairTemperatureSelect",
    "ionicPairObservableSelect", "ionicPairBornAmplitudeSelect", "ionicPairBornDecaySelect",
    "ionicPairBornPolicySelect", "ionicPairMatrixInspector", "ionicPairMatrixRows",
    "electrostaticForceToggle", "electrostaticForceToggleLabel"]) {
    assert.match(document, new RegExp(`id="${id}"`));
  }
  assert.match(document, /value="coulomb">Finite Coulomb/);
  assert.match(document, /value="coulomb-born-mayer">Coulomb \+ Born–Mayer/);
  assert.match(document, /conditional ΔU in eV/);
}

for (const token of [
  "incrementalFinitePointChargeElectrostatics",
  "finitePointChargeReachProfile",
  "ionicPairRelativePermittivity",
  "ionicPairTemperatureKelvin",
  "ionicPairObservable",
  "const CUSTOM_EXPERIMENT_SCHEMA_VERSION = 4",
  "migrateCustomExperimentManifest",
  "migratedFromSchemaVersion",
  "electrostaticEnergyEvaluated",
  "electrostaticForceEvaluated",
  "electrostaticForceGlyphAudit",
  "ionicPairBornAmplitudeElectronVolt",
  "ionicPairBornDecayAngstrom",
  "ionicPairBornPolicy",
  "activeBornMayerPairMatrix",
  "renderBornMayerPairMatrix",
  "electrostaticForceSites",
  "vectorDirectionsPhysical: true",
  "arrowLengthsPhysical: false",
  "displayLengthIsPhysical = false",
  "finiteOpenBoundaryUsed",
  "validatedMaterialEnergy: false",
]) assert.ok(app.includes(token), token);

for (const token of [
  "COULOMB_ENERGY_ELECTRON_VOLT_ANGSTROM",
  "14.3996454784255",
  "deltaEnergyElectronVolt",
  "reducedThermalEnergyPerAddedSite",
  "addedForceVectorsElectronVoltPerAngstrom",
  "addedBornMayerForceVectorsElectronVoltPerAngstrom",
  "bornMayerRepulsiveEnergyElectronVolt",
  "bornMayerRepulsionApplied",
  "rmsAddedForceElectronVoltPerAngstrom",
  "netAddedForceMagnitudeElectronVoltPerAngstrom",
  "electrostaticTorqueMagnitudeElectronVolt",
  "forceCancellationScore",
  "totalMechanicalForceInferred: false",
  "currentCurrentConstantOmitted: true",
  "periodicImagesUsed: false",
  "ewaldSummationUsed: false",
  "neutralizingBackgroundUsed: false",
  "targetUsed: false",
]) assert.ok(moduleSource.includes(token), token);

for (const token of [
  "buildBornMayerPairMatrix",
  "canonicalSpeciesPairKey",
  "contact-scaled",
  "geometryConditionedPairs",
  "uniformFallbackPairs",
  "energyOrForceFitted: false",
  "targetUsed: false",
]) assert.ok(pairMatrixSource.includes(token), token);

assert.match(readme, /Build 422 · finite point-charge electrostatics/);
assert.match(readme, /Build 423 · electrostatic energy becomes force geometry/);
assert.match(readme, /Build 424 · electrostatic force vectors become inspectable 3D sections/);
assert.match(readme, /Build 425 · Coulomb acquires an explicit short-range core/);
assert.match(readme, /Build 426 · short-range repulsion becomes a visible species-pair matrix/);
assert.match(benchmark, /Finite formal-charge electrostatic boundary \(Build 422\)/);
assert.match(benchmark, /Finite electrostatic force geometry \(Build 423\)/);
assert.match(benchmark, /Candidate-bound electrostatic force glyphs \(Build 424\)/);
assert.match(benchmark, /Conditional Coulomb \+ Born–Mayer pair hypothesis \(Build 425\)/);
assert.match(benchmark, /Geometry-conditioned Born–Mayer pair matrix \(Build 426\)/);
assert.match(atlas, /"27", "Conditional finite electrostatics"/);
assert.match(atlas, /"28", "Electrostatic force geometry"/);
assert.match(atlas, /"29", "Candidate-bound Coulomb force glyphs"/);
assert.match(atlas, /"30", "Finite Coulomb \+ Born–Mayer hypothesis"/);
assert.match(atlas, /"31", "Geometry-conditioned species-pair core"/);

console.log("finite point-charge electrostatics portal contract passed");
