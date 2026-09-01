import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const response = fs.readFileSync("apps/iqc-growth-live/kinetic-geometry-response.mjs", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /kineticGeometryResponsePlot/);
  assert.match(document, /Kinetic → geometric response/);
  assert.match(document, /app\.js\?v=20260901-435/);
}
assert.match(app, /kinetic-geometry-response\.mjs\?v=20260901-435/);
assert.match(app, /expectedMaterialAtomDeltaPerEvent/);
assert.match(app, /futureFrontierAssumedUnchanged: false/);
assert.match(response, /contactResolvedProbabilityMass/);
assert.match(response, /physicalTrajectoryIntegrated: false/);
assert.match(response, /adversarialRateIntervalEnvelopeComputed: true/);
assert.match(response, /stochasticUncertaintyPropagatedIntoResponse: false/);
assert.match(app, /rateBoxEnvelope/);
assert.match(response, /nominal expectation for the next event/);
assert.match(readme, /Build 370/);
assert.match(readme, /kinetic-to-geometric response/i);
assert.match(benchmark, /Finite-catalog kinetic-to-geometric response \(Build 370\)/);

console.log("finite-catalog kinetic geometry-response portal contract passed");
