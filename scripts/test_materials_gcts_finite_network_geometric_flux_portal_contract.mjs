import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const model = fs.readFileSync("apps/iqc-growth-live/finite-network-geometric-flux.mjs", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /finiteNetworkFluxPlot/);
  assert.match(document, /Geometric probability current/);
  assert.match(document, /app\.js\?v=20260831-386/);
}
assert.match(app, /finite-network-geometric-flux\.mjs\?v=20260831-386/);
assert.match(app, /expectedAtomDriftIdentityResidualPerObservedTimescale/);
assert.match(model, /probabilityTrafficPerObservedTimescale/);
assert.match(model, /macroscopicInterfaceVelocityClaimed: false/);
assert.match(model, /steadyStateClaimed: false/);
assert.match(model, /mechanismCatalogComplete: false/);
assert.match(model, /targetUsed: false/);
assert.match(readme, /Build 374/);
assert.match(readme, /geometry-resolved transient probability current/i);
assert.match(benchmark,
  /Geometry-resolved transient probability current \(Build 374\)/);

console.log("finite-network geometric-flux portal contract passed");
