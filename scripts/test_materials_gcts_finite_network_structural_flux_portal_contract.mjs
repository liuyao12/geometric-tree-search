import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const lineage = fs.readFileSync("apps/iqc-growth-live/reversible-transition-lineage.mjs", "utf8");
const model = fs.readFileSync("apps/iqc-growth-live/finite-network-structural-flux.mjs", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /finiteNetworkStructuralFluxPlot/);
  assert.match(document, /Structural-order current/);
  assert.match(document, /app\.js\?v=20260901-452/);
}
assert.match(app, /finite-network-structural-flux\.mjs\?v=20260901-452/);
assert.match(app, /buildEventGeometryObservables\(barrier/);
assert.match(lineage, /gcts-committed-path-geometric-observable-v1/);
assert.match(lineage, /geometricPathObservableClosurePassed/);
assert.match(model, /contactResolvedActivityFraction/);
assert.match(model, /unresolvedActivityRetainedAsMissing/);
assert.match(model, /chemicalBondClaimed: false/);
assert.match(model, /bulkOrderParameterKineticsClaimed: false/);
assert.match(readme, /Build 375/);
assert.match(readme, /traffic-weighted structural-order current/i);
assert.match(benchmark, /Traffic-weighted structural-order current \(Build 375\)/);

console.log("finite-network structural-flux portal contract passed");
