import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const model = fs.readFileSync(
  "apps/iqc-growth-live/finite-network-conditioned-structural-dispersion.mjs", "utf8");
const structuralPath = fs.readFileSync(
  "apps/iqc-growth-live/finite-network-conditioned-structural-path.mjs", "utf8");
const style = fs.readFileSync("apps/iqc-growth-live/style.css", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /finiteNetworkConditionedStructuralDispersionPlot/);
  assert.match(document, /Successful-path structural spread/);
  assert.match(document, /app\.js\?v=20260901-440/);
}
assert.match(app, /finite-network-conditioned-structural-dispersion\.mjs\?v=20260901-440/);
assert.match(app, /buildFiniteNetworkConditionedStructuralDispersion/);
assert.match(app, /finiteNetworkConditionedStructuralDispersion,/);
assert.match(app, /finite-network-conditioned-structural-dispersion/);
assert.match(structuralPath, /conditionedStateProbabilities/);
assert.match(model, /weightedMoments/);
assert.match(model, /effectiveStateCount/);
assert.match(model, /maximumMeanConsistencyResidual/);
assert.match(model, /trajectorySampled: false/);
assert.match(model, /thermalFluctuationClaimed: false/);
assert.match(model, /bulkVarianceClaimed: false/);
assert.match(style, /finite-network-conditioned-structural-dispersion/);
assert.match(readme, /Build 386/);
assert.match(benchmark, /Exact structural spread along successful paths \(Build 386\)/);

console.log("finite-network conditioned-structural-dispersion portal contract passed");
