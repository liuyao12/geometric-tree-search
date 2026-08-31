import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const lineage = fs.readFileSync("apps/iqc-growth-live/reversible-transition-lineage.mjs", "utf8");
const stateDescriptor = fs.readFileSync("apps/iqc-growth-live/geometric-state-descriptor.mjs", "utf8");
const model = fs.readFileSync("apps/iqc-growth-live/finite-network-global-order.mjs", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /finiteNetworkGlobalOrderPlot/);
  assert.match(document, /Global geometric order trajectory/);
  assert.match(document, /app\.js\?v=20260831-387/);
}
assert.match(app, /geometric-state-descriptor\.mjs\?v=20260831-387/);
assert.match(app, /finite-network-global-order\.mjs\?v=20260831-387/);
assert.match(app, /materialEndpointSites\(barrier\.pathGeometry, "initial"\)/);
assert.match(lineage, /initialStateGeometricDescriptor/);
assert.match(lineage, /finalStateGeometricDescriptor/);
assert.match(stateDescriptor, /steinhardtQ4/);
assert.match(stateDescriptor, /steinhardtQ6/);
assert.match(stateDescriptor, /periodicImagesAdded: false/);
assert.match(model, /orderCurrentIdentityResidual/);
assert.match(model, /thermodynamicOrderParameterClaimed: false/);
assert.match(model, /phaseClassified: false/);
assert.match(readme, /Build 376/);
assert.match(readme, /observation-wide global geometric order/i);
assert.match(benchmark, /Observation-wide global geometric order \(Build 376\)/);

console.log("finite-network global-order portal contract passed");
