import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const model = fs.readFileSync("apps/iqc-growth-live/finite-network-passage-control.mjs", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /finiteNetworkPassageControlPlot/);
  assert.match(document, /Geometric kinetic-control map/);
  assert.match(document, /app\.js\?v=20260901-435/);
}
assert.match(app, /finite-network-passage-control\.mjs\?v=20260901-435/);
assert.match(app, /buildFiniteNetworkPassageControl/);
assert.match(app, /finiteNetworkPassageControl,/);
assert.match(model, /commonModeTargetProbabilityDerivative/);
assert.match(model, /commonModeLogPassageTimeDerivative/);
assert.match(model, /commonModeLogExpectedJumpsDerivative/);
assert.match(model, /geometricCharacter/);
assert.match(model, /causalMechanismClaimed: false/);
assert.match(model, /independentEdgePerturbationPhysicallyRealizableClaimed: false/);
assert.match(readme, /Build 379/);
assert.match(readme, /geometry-linked kinetic-control map/i);
assert.match(benchmark, /Geometry-linked kinetic-control map \(Build 379\)/);

console.log("finite-network passage-control portal contract passed");
