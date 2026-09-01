import assert from "node:assert/strict";
import fs from "node:fs";

const root = new URL("../", import.meta.url);
const read = (path) => fs.readFileSync(new URL(path, root), "utf8");
const app = read("apps/iqc-growth-live/app.js");
const html = read("apps/iqc-growth-live/index.html");
const css = read("apps/iqc-growth-live/style.css");
const moduleSource = read("apps/iqc-growth-live/classical-nucleation-kinetics.mjs");
const atlas = read("apps/iqc-growth-live/evidence-atlas.js");
const readme = read("apps/iqc-growth-live/README.md");
const methods = read("docs/projects/materials-recursive-gcts-benchmark.md");

for (const token of ["buildClassicalNucleationKineticsRequest",
  "validateClassicalNucleationKineticsResponse", "buildConditionalClassicalNucleationRate",
  "evaluatePoissonNucleationWindow", "J = rho_site * Z * f_plus",
  "barrierAloneCannotProduceARate", "three sigma", "candidateSetChanged: false",
  "growthRankingChanged: false", "physicalClockIntegrated: false", "targetUsed: false"])
  assert.ok(moduleSource.includes(token), token);

for (const token of ["id=\"classicalNucleationKineticsEvidence\"",
  "Conditional nucleation-rate density", "id=\"downloadNucleationKineticsRequest\"",
  "id=\"importNucleationKineticsResponse\"", "id=\"nucleationObservationLengthSelect\"",
  "id=\"nucleationExposureSelect\"", "id=\"classicalNucleationKineticsMetrics\"",
  "A barrier alone is not a rate"])
  assert.ok(html.includes(token), token);

for (const token of ["classical-nucleation-kinetics.mjs?v=20260901-451",
  "function renderClassicalNucleationKineticsEvidence()",
  "downloadClassicalNucleationKineticsEvidenceRequest",
  "validateClassicalNucleationKineticsFile", "evaluatePoissonNucleationWindow(",
  "barrierAloneCannotProduceARate: true", "physicalClockIntegrated: false",
  "conditionalNucleationRateValidated"])
  assert.ok(app.includes(token), token);

assert.ok(css.includes(".classical-nucleation-kinetics"));
assert.ok(atlas.includes("Conditional classical nucleation rate"));
assert.ok(atlas.includes("J=ρsite Z f⁺ exp(−ΔG*/kBT)"));
assert.ok(readme.includes("Build 412 · a barrier becomes a rate only through independent kinetics"));
assert.ok(methods.includes("Work-bound conditional nucleation kinetics (Build 412)"));

console.log("classical nucleation kinetics portal contract: passed");
