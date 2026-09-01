import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const atlas = fs.readFileSync("apps/iqc-growth-live/evidence-atlas.js", "utf8");
const model = fs.readFileSync("apps/iqc-growth-live/hierarchy-physics-investigation.mjs", "utf8");
const style = fs.readFileSync("apps/iqc-growth-live/style.css", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /hierarchyPhysicsInvestigation/);
  assert.match(document, /Build a sealed scale-bridge experiment/);
  assert.match(document, /evidence-atlas\.js\?v=20260901-424/);
}
assert.match(atlas, /hierarchy-physics-investigation\.mjs\?v=20260901-424/);
assert.match(atlas, /renderHierarchyPhysicsInvestigation/);
assert.match(atlas, /routeToHierarchyPhysicsInvestigation/);
assert.match(model, /gcts-hierarchy-physics-investigation-v1/);
assert.match(model, /candidateGeometryFrozenDuringAblation: true/);
assert.match(model, /targetUsedForFitOrSelection: false/);
assert.match(style, /hierarchy-physics-investigation-flow/);
assert.match(readme, /Build 390/);
assert.match(benchmark, /Sealed scale-bridge investigation planner \(Build 390\)/);

console.log("hierarchy physics investigation portal contract passed");
