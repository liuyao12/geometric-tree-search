import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const normalization = fs.readFileSync("apps/iqc-growth-live/score-normalization.mjs", "utf8");
const moduleText = fs.readFileSync("apps/iqc-growth-live/external-interface-flux.mjs", "utf8");
const atlas = fs.readFileSync("apps/iqc-growth-live/evidence-atlas.js", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");

for (const document of [html, alias]) {
  for (const id of ["interfaceFluxPlot", "downloadInterfaceFluxRequest", "importInterfaceFluxResponse",
    "interfaceFluxModeSelect", "interfaceFluxReachSelect", "interfaceFluxWeightSelect",
    "interfaceFluxRankingAudit"]) assert.match(document, new RegExp(`id="${id}"`));
  assert.match(document, /Interface supply map/);
  assert.match(document, /Resolve diffusion, substrate supply, or shadowing outside GCTS/);
}
assert.match(app, /external-interface-flux\.mjs\?v=20260901-417/);
assert.match(app, /buildInterfaceFluxRequest/);
assert.match(app, /validateInterfaceFluxResponse/);
assert.match(app, /evaluateInterfaceFluxScore/);
assert.match(app, /captureInterfaceFluxMatchedRankingAudit\(evaluated\)/);
assert.match(app, /activeInterfaceFluxWeight\(\) \* evaluation\.interfaceFlux\.score/);
assert.match(app, /spatialInterfaceFluxEvidence: interfaceFluxReceipt\(\)/);
assert.match(app, /geometricVisibilityUsedAsPhysicalFlux: false/);
assert.match(normalization, /"interface-flux"/);
assert.match(normalization, /"interface-flux": "spatial-interface-flux"/);
assert.match(moduleText, /massBalanceRelativeResidual > 1e-3/);
assert.match(moduleText, /meshConvergenceRelativeChange > \.05/);
assert.match(moduleText, /candidateSetChanged: false/);
assert.match(moduleText, /physicalTimeIntegrated: false/);
assert.match(readme, /Build 356/);
assert.match(readme, /geometric visibility into diffusion/i);
assert.match(atlas, /spatial supply, rate control, and exact events stay distinct/);
assert.match(atlas, /geometric visibility is not diffusion/i);
console.log("spatial interface-flux portal contract passed");
