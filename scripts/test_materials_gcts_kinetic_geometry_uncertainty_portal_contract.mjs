import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const response = fs.readFileSync("apps/iqc-growth-live/kinetic-geometry-response.mjs", "utf8");
const style = fs.readFileSync("apps/iqc-growth-live/style.css", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) assert.match(document, /app\.js\?v=20260901-446/);
assert.match(app, /rateIntervalAssumption/);
assert.match(app, /not confidence intervals/);
assert.match(response, /rateBoxObservableEnvelope/);
assert.match(response, /extremalSignedSumSign/);
assert.match(response, /adversarialRateIntervalEnvelopeComputed: true/);
assert.match(response, /stochasticUncertaintyPropagatedIntoResponse: false/);
assert.match(style, /atom-envelope/);
assert.match(style, /contact-envelope/);
assert.match(readme, /Build 371/);
assert.match(readme, /adversarial kinetic-response uncertainty envelopes/i);
assert.match(benchmark, /Adversarial kinetic-response uncertainty envelopes \(Build 371\)/);

console.log("kinetic geometry uncertainty-envelope portal contract passed");
