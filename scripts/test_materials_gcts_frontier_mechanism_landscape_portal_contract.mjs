import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const landscape = fs.readFileSync("apps/iqc-growth-live/frontier-mechanism-landscape.mjs", "utf8");
const barrier = fs.readFileSync("apps/iqc-growth-live/external-action-barrier.mjs", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /frontierMechanismLandscapePlot/);
  assert.match(document, /Barrier–driving mechanism landscape/);
  assert.match(document, /app\.js\?v=20260831-386/);
}
assert.match(app, /frontier-mechanism-landscape\.mjs\?v=20260831-386/);
assert.match(app, /jointProbabilityMass/);
assert.match(landscape, /thermodynamicAndKineticTemperatureCoherent: true/);
assert.match(landscape, /A potential-energy saddle is not relabeled/);
assert.match(landscape, /detailedBalanceCertified: false/);
assert.match(barrier, /must share one declared temperature/);
assert.match(readme, /Build 372/);
assert.match(readme, /coherent frontier mechanism landscape/i);
assert.match(benchmark, /Coherent frontier mechanism landscape \(Build 372\)/);

console.log("coherent frontier mechanism-landscape portal contract passed");
