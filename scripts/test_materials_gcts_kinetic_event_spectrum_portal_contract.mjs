import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const moduleText = fs.readFileSync("apps/iqc-growth-live/kinetic-event-spectrum.mjs", "utf8");
const css = fs.readFileSync("apps/iqc-growth-live/style.css", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  for (const id of ["kineticEventSpectrumBadge", "kineticEventSpectrumMode",
    "kineticEventSpectrumSummary", "kineticEventSpectrumPlot",
    "kineticEventSpectrumDetail"]) assert.match(document, new RegExp(`id="${id}"`));
  assert.match(document, /Frozen-event kinetic spectrum/);
  assert.match(document, /same hard-admitted catalog · no new events/);
}
assert.match(app, /kinetic-event-spectrum\.mjs\?v=20260901-437/);
assert.match(app, /function renderKineticEventSpectrum\(\)/);
assert.match(app, /kineticEventSpectrum: kineticSpectrum \?/);
assert.match(app, /candidateSetChanged: false, selectedEventChanged: false, targetUsed: false/);
assert.match(moduleText, /effectiveCompetingEventCount/);
assert.match(moduleText, /probabilityMassByDirection/);
assert.match(moduleText, /uncertaintyCompetitiveCandidateCount/);
assert.match(moduleText, /selectedEventChanged: false/);
assert.match(moduleText, /catalogCompleteBeyondFrozenFrontier: false/);
assert.match(css, /\.kinetic-event-spectrum/);
assert.match(css, /\.event\.selected \.point/);
assert.match(readme, /Build 361/);
assert.match(readme, /Shannon effective competing-event count/);
assert.match(benchmark, /Frozen-event kinetic spectrum \(Build 361\)/);
assert.match(benchmark, /probabilities remain conditional/);

console.log("frozen-event kinetic spectrum portal contract passed");
