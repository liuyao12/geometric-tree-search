import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const atlas = fs.readFileSync("apps/iqc-growth-live/evidence-atlas.js", "utf8");
const model = fs.readFileSync("apps/iqc-growth-live/hierarchy-physics-execution-binding.mjs", "utf8");
const style = fs.readFileSync("apps/iqc-growth-live/style.css", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /receiptScaleBridgeBinding/);
  assert.match(document, /design packet → run receipt/);
  assert.match(document, /app\.js\?v=20260901-451/);
  assert.match(document, /evidence-atlas\.js\?v=20260901-451/);
}
assert.match(app, /hierarchy-physics-execution-binding\.mjs\?v=20260901-451/);
assert.match(app, /scaleBridgeProtocol: scaleBridgeBinding/);
assert.match(app, /scaleBridgeProtocolLaunchSearch = window\.location\.search/);
assert.match(app, /captureHierarchyPhysicsProtocolLaunch\(scaleBridgeProtocolLaunchSearch\)/);
assert.match(app, /gcts:hierarchy-physics-protocol-audit/);
assert.match(app, /Promise\.race/);
assert.match(atlas, /hierarchyPhysicsProtocolLaunchAuditFromPacket/);
assert.match(atlas, /window\.__gctsHierarchyPhysicsProtocolLaunchAudit/);
assert.match(model, /gcts-hierarchy-physics-protocol-launch-v1/);
assert.match(model, /gcts-hierarchy-physics-execution-binding-v1/);
assert.match(model, /executionAuthorizedByPacket: false/);
assert.match(model, /executionConformanceClaimed: false/);
assert.match(model, /greenGateEvaluated: false/);
assert.match(model, /outcomeClaimUpgraded: false/);
assert.match(style, /receipt-scale-bridge-binding\.verified-design-stage-reached/);
assert.match(readme, /Build 392/);
assert.match(benchmark, /Design packet → execution receipt binding \(Build 392\)/);

console.log("hierarchy physics execution binding portal contract passed");
