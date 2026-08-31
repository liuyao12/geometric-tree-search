import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const normalization = fs.readFileSync("apps/iqc-growth-live/score-normalization.mjs", "utf8");
const moduleText = fs.readFileSync("apps/iqc-growth-live/external-attachment-kinetics.mjs", "utf8");
const atlas = fs.readFileSync("apps/iqc-growth-live/evidence-atlas.js", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");

for (const document of [html, alias]) {
  for (const id of ["kineticHabitPlot", "downloadKineticHabitRequest", "importKineticHabitResponse",
    "kineticHabitModeSelect", "kineticHabitReachSelect", "kineticHabitWeightSelect",
    "kineticHabitRankingAudit"]) assert.match(document, new RegExp(`id="${id}"`));
  assert.match(document, /Kinetic-Wulff growth habit/);
  assert.match(document, /Compare externally validated steady interface velocities with equilibrium γ/);
}
assert.match(app, /external-attachment-kinetics\.mjs\?v=20260831-377/);
assert.match(app, /buildAttachmentKineticsRequest/);
assert.match(app, /validateAttachmentKineticsResponse/);
assert.match(app, /evaluateKineticHabitScore/);
assert.match(app, /captureKineticHabitMatchedRankingAudit\(evaluated\)/);
assert.match(app, /activeKineticHabitWeight\(\) \* evaluation\.kineticHabit\.score/);
assert.match(app, /orientationAttachmentKineticsEvidence: attachmentKineticsReceipt\(\)/);
assert.match(app, /candidateSetChanged: false/);
assert.match(normalization, /"kinetic-habit"/);
assert.match(normalization, /"kinetic-habit": "orientation-attachment-kinetics"/);
assert.match(moduleText, /morphologyUsedToInferVelocity: false/);
assert.match(moduleText, /interfacialFreeEnergyUsedAsVelocity: false/);
assert.match(moduleText, /orientedNormalsNotSilentlyInversionSymmetrized: true/);
assert.match(moduleText, /physicalTimeIntegrated: false/);
assert.match(readme, /Build 355/);
assert.match(readme, /neither the displayed[\s\S]*γ\(n̂\)[\s\S]*supplies `v\(n̂\)`/);
assert.match(atlas, /Equilibrium habit, kinetic habit, spatial supply, rate control, and exact events stay distinct/);
assert.match(atlas, /γ does not supply v/);
console.log("orientation-resolved attachment-kinetics portal contract passed");
