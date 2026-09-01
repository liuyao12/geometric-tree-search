import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const model = fs.readFileSync(
  "apps/iqc-growth-live/finite-network-temperature-intervention.mjs", "utf8");
const lineage = fs.readFileSync("apps/iqc-growth-live/reversible-transition-lineage.mjs", "utf8");
const network = fs.readFileSync("apps/iqc-growth-live/finite-transition-network.mjs", "utf8");
const style = fs.readFileSync("apps/iqc-growth-live/style.css", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /finiteNetworkTemperatureInterventionInput/);
  assert.match(document, /Temperature-coherent passage/);
  assert.match(document, /app\.js\?v=20260831-406/);
}
assert.match(app, /finite-network-temperature-intervention\.mjs\?v=20260831-406/);
assert.match(app, /buildFiniteNetworkTemperatureIntervention/);
assert.match(app, /finiteNetworkTemperatureIntervention,/);
assert.match(app, /finite-network-temperature-intervention/);
assert.match(model, /bounded-constant-htst/);
assert.match(model, /localControlProjectedLogPassageChange/);
assert.match(model, /networkMutated: false/);
assert.match(model, /unauthorizedExtrapolationPerformed: false/);
assert.match(lineage, /temperatureApplicability/);
assert.match(network, /attemptFrequencyPerSecond: record\.attemptFrequencyPerSecond/);
assert.match(network, /temperatureApplicability: record\.temperatureApplicability/);
assert.match(style, /finite-network-temperature-intervention/);
assert.match(readme, /Build 381/);
assert.match(benchmark, /Coherent finite-network temperature intervention \(Build 381\)/);

console.log("finite-network temperature-intervention portal contract passed");
