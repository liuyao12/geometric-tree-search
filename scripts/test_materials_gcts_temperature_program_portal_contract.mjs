import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const contract = fs.readFileSync("apps/iqc-growth-live/external-action-barrier.mjs", "utf8");
const program = fs.readFileSync("apps/iqc-growth-live/temperature-programmed-kinetics.mjs", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /temperatureProgramPlot/);
  assert.match(document, /temperatureProgramInspect/);
  assert.match(document, /Arrhenius mechanism map/);
  assert.match(document, /app\.js\?v=20260901-434/);
}
assert.match(app, /temperature-programmed-kinetics\.mjs\?v=20260901-434/);
assert.match(app, /temperatureProgrammedKinetics/);
assert.match(app, /unauthorizedTemperatureExtrapolationPerformed: false/);
assert.match(contract, /bounded-constant-htst/);
assert.match(contract, /barrierAndPrefactorAssumedConstant/);
assert.match(program, /Uniform inverse-temperature sampling/);
assert.match(program, /missingEventsInferred: false/);
assert.match(program, /No temperature sweep is inferred/);
assert.match(readme, /Build 369/);
assert.match(readme, /temperature-programmed finite-catalog kinetics/i);
assert.match(benchmark, /Temperature-programmed finite-catalog kinetics \(Build 369\)/);

console.log("temperature-programmed kinetic portal contract passed");
