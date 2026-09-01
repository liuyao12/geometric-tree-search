import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const moduleText = fs.readFileSync("apps/iqc-growth-live/catalog-conditional-chronology.mjs", "utf8");
const css = fs.readFileSync("apps/iqc-growth-live/style.css", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  for (const id of ["kineticChronologyBadge", "kineticChronologyPlot", "kineticChronologyMetrics",
    "kineticChronologyState", "kineticChronologyBoundary"]) {
    assert.match(document, new RegExp(`id="${id}"`));
  }
  assert.match(document, /Kinetic leap chronicle/);
}
assert.match(app, /catalog-conditional-chronology\.mjs\?v=20260901-448/);
assert.match(app, /function currentKineticChronology\(/);
assert.match(app, /function renderKineticChronology\(/);
assert.match(app, /catalogConditionalChronology: currentKineticChronology\(\)/);
assert.match(app, /"kinetic-chronology": \{ stage: 4, controlId: "kineticChronologyPlot"/);
assert.match(moduleText, /unconditionalMaterialTimeClaimed: false/);
assert.match(moduleText, /bulkGrowthRateClaimed: false/);
assert.match(moduleText, /dynamicalTrajectoryIntegrated: false/);
assert.match(moduleText, /clocked event count must increment by one/);
assert.match(css, /\.kinetic-chronology-plot/);
assert.match(readme, /Build 359/);
assert.match(readme, /Missing\s+mechanisms and ordinary geometric leaps receive no time/);
assert.match(benchmark, /Catalog-conditional kinetic leap chronicle \(Build 359\)/);
assert.match(benchmark, /not an unconditional material clock/);
console.log("catalog-conditional kinetic chronology portal contract passed");
