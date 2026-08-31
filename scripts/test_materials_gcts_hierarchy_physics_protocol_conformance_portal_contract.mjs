import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const atlas = fs.readFileSync("apps/iqc-growth-live/evidence-atlas.js", "utf8");
const model = fs.readFileSync("apps/iqc-growth-live/hierarchy-physics-protocol-conformance.mjs", "utf8");
const style = fs.readFileSync("apps/iqc-growth-live/style.css", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /receiptScaleBridgeConformance/);
  assert.match(document, /Protocol conformance audit/);
  assert.match(document, /hierarchyPhysicsProtocolConformanceRoute/);
  assert.match(document, /app\.js\?v=20260831-397/);
  assert.match(document, /evidence-atlas\.js\?v=20260831-397/);
}
assert.match(app, /hierarchy-physics-protocol-conformance\.mjs\?v=20260831-397/);
assert.match(app, /scaleBridgeConformance,/);
assert.match(app, /currentScaleBridgeConformanceEvidence/);
assert.match(app, /gateEvaluation: null/);
assert.match(atlas, /hierarchyPhysicsProtocolConformanceRoute/);
assert.match(atlas, /receiptScaleBridgeConformance/);
assert.match(model, /gcts-hierarchy-physics-protocol-conformance-v1/);
assert.match(model, /ready-for-sealed-gate/);
assert.match(model, /sealed-gate-passed/);
assert.match(model, /preregistered/);
assert.match(model, /metricDenominatorsFrozen/);
assert.match(model, /targetUsedForFitOrSelection: false/);
assert.match(style, /receipt-scale-bridge-conformance-progress/);
assert.match(readme, /Build 396/);
assert.match(benchmark, /Design-versus-run conformance audit \(Build 396\)/);

console.log("hierarchy physics protocol conformance portal contract passed");
