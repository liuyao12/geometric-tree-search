import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const model = fs.readFileSync("apps/iqc-growth-live/hierarchy-evidence-microscope.mjs", "utf8");
const style = fs.readFileSync("apps/iqc-growth-live/style.css", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /hierarchyEvidenceMicroscope/);
  assert.match(document, /Hierarchy evidence microscope/);
  assert.match(document, /app\.js\?v=20260901-452/);
}
assert.match(app, /hierarchy-evidence-microscope\.mjs\?v=20260901-452/);
assert.match(app, /buildHierarchyEvidenceMicroscope/);
assert.match(app, /renderHierarchyEvidenceMicroscope/);
assert.match(model, /gcts-hierarchy-evidence-microscope-v1/);
assert.match(model, /held-out coordinates are observed only for exact matching/);
assert.match(model, /no exact production key survives three consecutive levels/);
assert.match(model, /symbolic representation is not an MD trajectory/);
assert.match(style, /hierarchy-evidence-microscope/);
assert.match(readme, /Build 388/);
assert.match(benchmark, /Hierarchy evidence microscope \(Build 388\)/);

console.log("hierarchy evidence microscope portal contract passed");

