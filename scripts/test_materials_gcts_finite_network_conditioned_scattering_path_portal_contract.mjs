import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const model = fs.readFileSync(
  "apps/iqc-growth-live/finite-network-conditioned-scattering-path.mjs", "utf8");
const descriptor = fs.readFileSync(
  "apps/iqc-growth-live/geometric-state-descriptor.mjs", "utf8");
const lineage = fs.readFileSync(
  "apps/iqc-growth-live/reversible-transition-lineage.mjs", "utf8");
const style = fs.readFileSync("apps/iqc-growth-live/style.css", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /finiteNetworkConditionedScatteringPathPlot/);
  assert.match(document, /Successful-path powder signature/);
  assert.match(document, /app\.js\?v=20260831-387/);
}
assert.match(app, /finite-network-conditioned-scattering-path\.mjs\?v=20260831-387/);
assert.match(app, /buildFiniteNetworkConditionedScatteringPath/);
assert.match(app, /finiteNetworkConditionedScatteringPath,/);
assert.match(app, /finite-network-conditioned-scattering-path/);
assert.match(descriptor, /DIMENSIONLESS_POWDER_Q_GRID/);
assert.match(descriptor, /finite Debye orientational average divided by atom count/);
assert.match(lineage, /normalizedDimensionlessPowderScattering/);
assert.match(model, /targetInclusive/);
assert.match(model, /surviving/);
assert.match(model, /sourceTargetRmsDifference/);
assert.match(model, /trajectorySampled: false/);
assert.match(model, /experimentalIntensityClaimed: false/);
assert.match(model, /qDependentFormFactorsUsed: false/);
assert.match(style, /finite-network-conditioned-scattering-path/);
assert.match(readme, /Build 387/);
assert.match(benchmark, /Reciprocal-space signatures along successful paths \(Build 387\)/);

console.log("finite-network conditioned-scattering-path portal contract passed");
