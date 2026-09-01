import assert from "node:assert/strict";
import fs from "node:fs";
import { hierarchyPhysicsProtocolConformanceChannels,
  hierarchyPhysicsProtocolConformanceRequirements }
  from "../apps/iqc-growth-live/hierarchy-physics-protocol-conformance.mjs";

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
  assert.match(document, /receiptScaleBridgeConformanceLedger/);
  assert.match(document, /receiptScaleBridgeConformanceInspector/);
  assert.match(document, /receiptScaleBridgeConformanceRoute/);
  assert.match(document, /data-conformance-filter="evidenced"/);
  assert.match(document, /hierarchyPhysicsProtocolConformanceRoute/);
  assert.match(document, /app\.js\?v=20260901-448/);
  assert.match(document, /evidence-atlas\.js\?v=20260901-448/);
}
assert.match(app, /hierarchy-physics-protocol-conformance\.mjs\?v=20260901-448/);
assert.match(app, /scaleBridgeConformance,/);
assert.match(app, /currentScaleBridgeConformanceEvidence/);
assert.match(app, /renderScaleBridgeConformanceLedger/);
assert.match(app, /selectedScaleBridgeConformanceRequirement/);
assert.match(app, /enterPipelineStage\(requirement\.route\.stage\)/);
assert.match(app, /gateEvaluation: null/);
assert.match(atlas, /hierarchyPhysicsProtocolConformanceRoute/);
assert.match(atlas, /receiptScaleBridgeConformance/);
assert.match(model, /gcts-hierarchy-physics-protocol-conformance-v1/);
assert.match(model, /ready-for-sealed-gate/);
assert.match(model, /sealed-gate-passed/);
assert.match(model, /preregistered/);
assert.match(model, /metricDenominatorsFrozen/);
assert.match(model, /targetUsedForFitOrSelection: false/);
assert.match(model, /evidenceState:/);
assert.match(model, /INSPECTION_ROUTES/);
assert.match(style, /receipt-scale-bridge-conformance-progress/);
assert.match(style, /receipt-conformance-ledger-rows/);
assert.match(style, /receipt-conformance-inspector/);
assert.match(readme, /Build 398/);
assert.match(benchmark, /Interactive conformance evidence ledger \(Build 398\)/);

for (const channel of hierarchyPhysicsProtocolConformanceChannels()) {
  for (const scale of ["atomic", "cluster", "macro", "stationary"]) {
    for (const requirement of hierarchyPhysicsProtocolConformanceRequirements(channel, scale)) {
      assert.ok(html.includes(`id="${requirement.route.focusId}"`),
        `missing evidence route target ${requirement.route.focusId}`);
    }
  }
}

console.log("hierarchy physics protocol conformance portal contract passed");
