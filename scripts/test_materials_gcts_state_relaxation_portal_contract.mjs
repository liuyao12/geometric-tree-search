import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const moduleText = fs.readFileSync("apps/iqc-growth-live/external-state-relaxation.mjs", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  for (const id of ["stateRelaxationPanel", "stateRelaxationBadge", "stateRelaxationFreeze",
    "stateRelaxationCellPolicy",
    "stateRelaxationDownload", "stateRelaxationResponse", "stateRelaxationAdopt",
    "stateRelaxationRelease", "stateRelaxationSummary"]) {
    assert.match(document, new RegExp(`id="${id}"`));
  }
  assert.match(document, /Post-leap relaxation handoff/);
  assert.match(document, /Adopt as next observation/);
  assert.match(document, /app\.js\?v=20260901-418/);
}
assert.match(app, /external-state-relaxation\.mjs\?v=20260901-418/);
assert.match(app, /async function freezeExternalStateRelaxation/);
assert.match(app, /async function adoptExternalRelaxedState/);
assert.match(app, /maximumAtoms: 12000/);
assert.match(app, /variable-isotropic-pressure/);
assert.match(app, /currentStateRelaxationStateSha256/);
assert.match(app, /postLeapExternalRelaxation: stateRelaxationReceipt\(\)/);
assert.match(moduleText, /gcts-external-state-relaxation-request-v2/);
assert.match(moduleText, /gcts-external-state-relaxation-response-v2/);
assert.match(moduleText, /greenLagrangeStrain/);
assert.match(moduleText, /maximumStressResidualGPa/);
assert.match(moduleText, /topologyAndSpeciesMustBePreserved: true/);
assert.match(moduleText, /browserRelaxationUsed: false/);
assert.match(moduleText, /adoptionRequiresNewObservationRound: true/);
assert.match(readme, /Build 363/);
assert.match(readme, /Build 364/);
assert.match(readme, /exact geometry → external relaxation/);
assert.match(benchmark, /External post-leap relaxation loop \(Build 363\)/);
assert.match(benchmark, /Periodic pressure-and-strain relaxation \(Build 364\)/);
assert.match(benchmark, /No pre-relaxation\s+cluster or production is silently retained/);

console.log("external post-leap relaxation portal contract passed");
