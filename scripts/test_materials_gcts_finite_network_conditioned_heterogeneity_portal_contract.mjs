import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const model = fs.readFileSync(
  "apps/iqc-growth-live/finite-network-conditioned-heterogeneity.mjs", "utf8");
const style = fs.readFileSync("apps/iqc-growth-live/style.css", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /finiteNetworkConditionedHeterogeneityPlot/);
  assert.match(document, /Successful-path heterogeneity/);
  assert.match(document, /app\.js\?v=20260901-439/);
}
assert.match(app, /finite-network-conditioned-heterogeneity\.mjs\?v=20260901-439/);
assert.match(app, /buildFiniteNetworkConditionedHeterogeneity/);
assert.match(app, /finiteNetworkConditionedHeterogeneity,/);
assert.match(app, /finite-network-conditioned-heterogeneity/);
assert.match(model, /secondRawMoment/);
assert.match(model, /probabilityEverUsed/);
assert.match(model, /expectedTraversalsConditionalOnUse/);
assert.match(model, /atomCountTelescopeVariancePassed/);
assert.match(model, /trajectoryEnsembleSampled: false/);
assert.match(model, /rateUncertaintyPropagated: false/);
assert.match(style, /finite-network-conditioned-heterogeneity/);
assert.match(readme, /Build 383/);
assert.match(benchmark, /Exact successful-path heterogeneity \(Build 383\)/);

console.log("finite-network conditioned-heterogeneity portal contract passed");
