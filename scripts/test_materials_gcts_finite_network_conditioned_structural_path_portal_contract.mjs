import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const model = fs.readFileSync(
  "apps/iqc-growth-live/finite-network-conditioned-structural-path.mjs", "utf8");
const arrival = fs.readFileSync(
  "apps/iqc-growth-live/finite-network-conditioned-arrival.mjs", "utf8");
const style = fs.readFileSync("apps/iqc-growth-live/style.css", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /finiteNetworkConditionedStructuralPathPlot/);
  assert.match(document, /Successful-path structure/);
  assert.match(document, /app\.js\?v=20260901-448/);
}
assert.match(app, /finite-network-conditioned-structural-path\.mjs\?v=20260901-448/);
assert.match(app, /buildFiniteNetworkConditionedStructuralPath/);
assert.match(app, /finiteNetworkConditionedStructuralPath,/);
assert.match(app, /finite-network-conditioned-structural-path/);
assert.match(arrival, /conditionedStateProbabilities/);
assert.match(model, /survivingExpectedAtomCount/);
assert.match(model, /survivorStateProbabilities/);
assert.match(model, /descriptorConsistencyCertified: true/);
assert.match(model, /phaseClassified: false/);
assert.match(model, /thermodynamicOrderParameterClaimed: false/);
assert.match(style, /finite-network-conditioned-structural-path/);
assert.match(readme, /Build 385/);
assert.match(benchmark, /Time-resolved successful-path structure \(Build 385\)/);

console.log("finite-network conditioned-structural-path portal contract passed");
