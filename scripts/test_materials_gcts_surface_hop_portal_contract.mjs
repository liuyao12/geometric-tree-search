import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const moduleText = fs.readFileSync("apps/iqc-growth-live/surface-hop-events.mjs", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /value="surface-hops"/);
  assert.match(document, /id="actionBarrierHopReach"/);
  assert.match(document, /ΔN = 0/);
  assert.match(document, /app\.js\?v=20260901-424/);
}
assert.match(app, /surface-hop-events\.mjs\?v=20260901-424/);
assert.match(app, /function surfaceHopEventCatalog/);
assert.match(app, /async function performOwnershipCertifiedSurfaceHop/);
assert.match(app, /committed surface hop failed exact endpoint or atom-count reproduction/);
assert.match(app, /speciesPopulationConserved: true/);
assert.match(moduleText, /species-population-not-conserved/);
assert.match(moduleText, /destination-uses-removed-source-atom/);
assert.match(moduleText, /barrierAndPrefactorInferred: false/);
assert.match(moduleText, /intermediateTrajectoryInferred: false/);
assert.match(readme, /Build 362/);
assert.match(readme, /exact mass-conserving surface hops/i);
assert.match(benchmark, /Exact mass-conserving surface hops \(Build 362\)/);
assert.match(benchmark, /does not enumerate all diffusion/);

console.log("mass-conserving surface-hop portal contract passed");
