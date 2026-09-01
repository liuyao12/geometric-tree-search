import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const model = fs.readFileSync(
  "apps/iqc-growth-live/finite-network-conditioned-arrival.mjs", "utf8");
const style = fs.readFileSync("apps/iqc-growth-live/style.css", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /finiteNetworkConditionedArrivalPlot/);
  assert.match(document, /Successful-arrival distribution/);
  assert.match(document, /app\.js\?v=20260901-415/);
}
assert.match(app, /finite-network-conditioned-arrival\.mjs\?v=20260901-415/);
assert.match(app, /buildFiniteNetworkConditionedArrival/);
assert.match(app, /finiteNetworkConditionedArrival,/);
assert.match(app, /finite-network-conditioned-arrival/);
assert.match(model, /segmented uniformization/);
assert.match(model, /cumulativeArrivalProbability/);
assert.match(model, /normalizedHazardPerMeanTime/);
assert.match(model, /centralNinetyPercentTimeRatio/);
assert.match(model, /trajectoryEnsembleSampled: false/);
assert.match(model, /rateUncertaintyPropagated: false/);
assert.match(style, /finite-network-conditioned-arrival/);
assert.match(readme, /Build 384/);
assert.match(benchmark, /Exact successful-arrival distribution \(Build 384\)/);

console.log("finite-network conditioned-arrival portal contract passed");
