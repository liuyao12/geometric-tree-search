import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const model = fs.readFileSync(
  "apps/iqc-growth-live/finite-network-population-dynamics.mjs", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync(
  "docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /finiteNetworkPopulationPlot/);
  assert.match(document, /State-population leap/);
  assert.match(document, /app\.js\?v=20260831-377/);
}
assert.match(app, /finite-network-population-dynamics\.mjs\?v=20260831-377/);
assert.match(app, /currentFiniteNetworkPopulationDynamics/);
assert.match(app, /finite-network-population-dynamics/);
assert.match(model, /continuous-time Markov master equation by uniformization/);
assert.match(model, /missingExitRatesAssumedZeroForConditionalProjection: true/);
assert.match(model, /equilibriumClaimed: false/);
assert.match(model, /mechanismCatalogComplete: false/);
assert.match(model, /targetUsed: false/);
assert.match(readme, /Build 373/);
assert.match(readme, /master-equation leap/i);
assert.match(benchmark, /Observed-network master-equation leap \(Build 373\)/);

console.log("finite-network population-dynamics portal contract passed");
