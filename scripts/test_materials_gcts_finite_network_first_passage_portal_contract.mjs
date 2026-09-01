import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const model = fs.readFileSync("apps/iqc-growth-live/finite-network-first-passage.mjs", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /finiteNetworkFirstPassagePlot/);
  assert.match(document, /Observed first-passage leap/);
  assert.match(document, /app\.js\?v=20260901-432/);
}
assert.match(app, /finite-network-first-passage\.mjs\?v=20260901-432/);
assert.match(app, /buildFiniteNetworkFirstPassage/);
assert.match(app, /finiteNetworkFirstPassage,/);
assert.match(model, /targetUnreachableObservedStatesTreatedAsFailure: true/);
assert.match(model, /missingExitRatesAssumedZeroForConditionalProjection: true/);
assert.match(model, /completeCommittorClaimed: false/);
assert.match(model, /backwardEquationConditionalTimeResidual/);
assert.match(model, /sourceConditionalExpectedObservedJumps/);
assert.match(readme, /Build 377/);
assert.match(readme, /observed first-passage leap/i);
assert.match(benchmark, /Observed first-passage leap \(Build 377\)/);

console.log("finite-network first-passage portal contract passed");
