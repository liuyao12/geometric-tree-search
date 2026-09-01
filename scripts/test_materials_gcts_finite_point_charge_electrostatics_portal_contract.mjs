import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const root = new URL("../", import.meta.url);
const read = (path) => readFileSync(new URL(path, root), "utf8");
const app = read("apps/iqc-growth-live/app.js");
const html = read("apps/iqc-growth-live/index.html");
const compatibility = read("iqc-growth-live/index.html");
const moduleSource = read("apps/iqc-growth-live/finite-point-charge-electrostatics.mjs");
const readme = read("apps/iqc-growth-live/README.md");
const benchmark = read("docs/projects/materials-recursive-gcts-benchmark.md");
const atlas = read("apps/iqc-growth-live/evidence-atlas.js");

for (const document of [html, compatibility]) {
  for (const id of ["ionicPairDielectricSelect", "ionicPairTemperatureSelect"]) {
    assert.match(document, new RegExp(`id="${id}"`));
  }
  assert.match(document, /value="coulomb">Finite Coulomb/);
  assert.match(document, /conditional ΔU in eV/);
}

for (const token of [
  "incrementalFinitePointChargeElectrostatics",
  "finitePointChargeReachProfile",
  "ionicPairRelativePermittivity",
  "ionicPairTemperatureKelvin",
  "electrostaticEnergyEvaluated",
  "finiteOpenBoundaryUsed",
  "validatedMaterialEnergy: false",
]) assert.ok(app.includes(token), token);

for (const token of [
  "COULOMB_ENERGY_ELECTRON_VOLT_ANGSTROM",
  "14.3996454784255",
  "deltaEnergyElectronVolt",
  "reducedThermalEnergyPerAddedSite",
  "currentCurrentConstantOmitted: true",
  "periodicImagesUsed: false",
  "ewaldSummationUsed: false",
  "neutralizingBackgroundUsed: false",
  "targetUsed: false",
]) assert.ok(moduleSource.includes(token), token);

assert.match(readme, /Build 422 · finite point-charge electrostatics/);
assert.match(benchmark, /Finite formal-charge electrostatic boundary \(Build 422\)/);
assert.match(atlas, /"27", "Conditional finite electrostatics"/);

console.log("finite point-charge electrostatics portal contract passed");
