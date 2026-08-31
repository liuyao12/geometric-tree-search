import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const moduleText = fs.readFileSync("apps/iqc-growth-live/species-exchange-events.mjs", "utf8");
const barrier = fs.readFileSync("apps/iqc-growth-live/external-action-barrier.mjs", "utf8");
const lineage = fs.readFileSync("apps/iqc-growth-live/reversible-transition-lineage.mjs", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /value="local-events"/);
  assert.match(document, /species exchange/);
  assert.match(document, /class="exchange"><\/i>species exchange/);
  assert.match(document, /app\.js\?v=20260831-384/);
}
assert.match(app, /species-exchange-events\.mjs\?v=20260831-384/);
assert.match(app, /function speciesExchangeEventCatalog/);
assert.match(app, /async function performOwnershipCertifiedSpeciesExchange/);
assert.match(app, /committed species exchange failed exact endpoint or atom-count reproduction/);
assert.match(app, /selectedEventDirection: "exchange"/);
assert.match(moduleText, /atom-count-not-conserved/);
assert.match(moduleText, /no-species-exchange/);
assert.match(moduleText, /destination-uses-removed-source-atom/);
assert.match(moduleText, /ChemicalPotentialInferred: false/);
assert.match(barrier, /action-barrier-request-v4/);
assert.match(barrier, /speciesExchangeGeometryPresent/);
assert.match(lineage, /"hop", "exchange"/);
assert.match(readme, /Build 365/);
assert.match(readme, /Build 366/);
assert.match(readme, /exact local species-exchange events/i);
assert.match(benchmark, /Exact local species exchange \(Build 365\)/);
assert.match(benchmark, /not a transition path, transmutation/);

console.log("local species-exchange portal contract passed");
