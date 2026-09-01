import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const atlas = fs.readFileSync("apps/iqc-growth-live/evidence-atlas.js", "utf8");
const model = fs.readFileSync("apps/iqc-growth-live/hierarchy-physics-transport.mjs", "utf8");
const style = fs.readFileSync("apps/iqc-growth-live/style.css", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /hierarchyPhysicsTransport/);
  assert.match(document, /What survives when clusters become clusters²/);
  assert.match(document, /evidence-atlas\.js\?v=20260901-433/);
}
assert.match(atlas, /hierarchy-physics-transport\.mjs\?v=20260901-433/);
assert.match(atlas, /renderHierarchyPhysicsTransport/);
assert.match(atlas, /transport certificate/);
assert.match(model, /gcts-hierarchy-physics-transport-v1/);
assert.match(model, /representation-only means observed atoms remain accountably encoded but are not generated/);
assert.match(model, /no cross-scale operator is certified/);
assert.match(style, /hierarchy-physics-transport-matrix/);
assert.match(readme, /Build 389/);
assert.match(benchmark, /Physics transport across recursive promotion \(Build 389\)/);

console.log("hierarchy physics transport portal contract passed");

