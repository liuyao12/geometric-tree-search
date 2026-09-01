import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const model = fs.readFileSync(
  "apps/iqc-growth-live/finite-network-conditioned-passage.mjs", "utf8");
const style = fs.readFileSync("apps/iqc-growth-live/style.css", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /finiteNetworkConditionedPassagePlot/);
  assert.match(document, /Successful-passage anatomy/);
  assert.match(document, /app\.js\?v=20260901-411/);
}
assert.match(app, /finite-network-conditioned-passage\.mjs\?v=20260901-411/);
assert.match(app, /buildFiniteNetworkConditionedPassage/);
assert.match(app, /finiteNetworkConditionedPassage,/);
assert.match(app, /finite-network-conditioned-passage/);
assert.match(model, /expectedScaledResidence/);
assert.match(model, /expectedTraversalCount/);
assert.match(model, /targetAbsorptionIdentityResidual/);
assert.match(model, /atomCountTelescopingResidual/);
assert.match(model, /trajectoryEnsembleSampled: false/);
assert.match(style, /finite-network-conditioned-passage/);
assert.match(readme, /Build 382/);
assert.match(benchmark, /Successful-passage geometric anatomy \(Build 382\)/);

console.log("finite-network conditioned-passage portal contract passed");
