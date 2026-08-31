import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const moduleText = fs.readFileSync("apps/iqc-growth-live/growth-regime-bridge.mjs", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /Transport–attachment regime bridge/);
  assert.match(document, /J\(x,n̂\) \/ ρ<sub>site<\/sub> ↔ v\(n̂\)/);
  assert.match(document, /data-rate-control-preset="mixed"/);
  assert.match(document, /id="rateControlPlot"/);
  assert.match(document, /app\.js\?v=20260831-399/);
  assert.match(document, /style\.css\?v=20260831-399/);
}
assert.match(app, /growth-regime-bridge\.mjs\?v=20260831-399/);
assert.match(app, /function periodicRateControlDensity\(\)/);
assert.match(app, /function activeRateControlEvidence\(\)/);
assert.match(app, /both physical responses must declare the same couplingStateSha256/);
assert.match(app, /2D sheet needs an explicit physical thickness/);
assert.match(moduleText, /export function periodicSiteNumberDensity/);
assert.match(moduleText, /export function coupleInterfaceSupplyAndAttachment/);
assert.match(moduleText, /transport and attachment responses declare different driving states/);
assert.match(moduleText, /classificationUsesNonoverlappingThreeSigmaIntervals/);
assert.match(moduleText, /effectiveGrowthVelocityInferred: false/);
assert.match(moduleText, /resistancesInSeriesAssumed: false/);
assert.match(readme, /Build 357/);
assert.match(benchmark, /Transport–attachment rate-control bridge \(Build 357\)/);
console.log("growth-regime bridge portal contract passed");
