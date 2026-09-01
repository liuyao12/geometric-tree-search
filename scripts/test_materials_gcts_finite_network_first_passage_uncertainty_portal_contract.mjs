import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const model = fs.readFileSync("apps/iqc-growth-live/finite-network-first-passage-uncertainty.mjs", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /finiteNetworkFirstPassageUncertaintyPlot/);
  assert.match(document, /First-passage uncertainty ensemble/);
  assert.match(document, /app\.js\?v=20260901-431/);
}
assert.match(app, /finite-network-first-passage-uncertainty\.mjs\?v=20260901-431/);
assert.match(app, /buildFiniteNetworkFirstPassageUncertainty/);
assert.match(app, /finiteNetworkFirstPassageUncertainty,/);
assert.match(model, /deterministic antithetic Halton sequence/);
assert.match(model, /uncertaintyAssumption: "independent Gaussian one-sigma errors/);
assert.match(model, /confidenceIntervalClaimed: false/);
assert.match(model, /edgeTopologyChanged: false/);
assert.match(model, /omittedMechanismsSampled: false/);
assert.match(readme, /Build 378/);
assert.match(readme, /uncertainty-aware first-passage leap/i);
assert.match(benchmark, /Uncertainty-aware first-passage leap \(Build 378\)/);

console.log("finite-network first-passage uncertainty portal contract passed");
