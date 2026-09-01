import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const model = fs.readFileSync("apps/iqc-growth-live/finite-network-rate-intervention.mjs", "utf8");
const style = fs.readFileSync("apps/iqc-growth-live/style.css", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /finiteNetworkRateInterventionPlot/);
  assert.match(document, /Geometric rate what-if/);
  assert.match(document, /data-rate-factor="0\.25"/);
  assert.match(document, /data-rate-factor="4"/);
  assert.match(document, /app\.js\?v=20260901-450/);
}
assert.match(app, /finite-network-rate-intervention\.mjs\?v=20260901-450/);
assert.match(app, /buildFiniteNetworkRateIntervention/);
assert.match(app, /finiteNetworkRateIntervention,/);
assert.match(app, /finite-network-rate-intervention/);
assert.match(model, /exactConditionalPassageTimeRatio/);
assert.match(model, /nonlinearLogTimeDepartureFromLocalTangent/);
assert.match(model, /networkMutated: false/);
assert.match(model, /physicalInterventionClaimed: false/);
assert.match(style, /finite-network-rate-intervention/);
assert.match(readme, /Build 380/);
assert.match(readme, /exact geometric rate what-if/i);
assert.match(benchmark, /Exact finite-rate intervention explorer \(Build 380\)/);

console.log("finite-network rate-intervention portal contract passed");
