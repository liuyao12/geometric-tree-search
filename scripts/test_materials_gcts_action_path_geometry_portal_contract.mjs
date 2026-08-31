import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const barrier = fs.readFileSync("apps/iqc-growth-live/external-action-barrier.mjs", "utf8");
const pathContract = fs.readFileSync("apps/iqc-growth-live/action-path-geometry.mjs", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /kineticEventPathPlot/);
  assert.match(document, /coordinate-bearing external path/);
  assert.match(document, /app\.js\?v=20260831-366/);
}
assert.match(app, /external-action-barrier\.mjs\?v=20260831-366/);
assert.match(app, /pathGeometrySha256/);
assert.match(app, /fixedMaterialSiteCount/);
assert.match(barrier, /action-barrier-request-v4/);
assert.match(barrier, /action-path-geometry\.mjs\?v=20260831-366/);
assert.match(barrier, /everyPathGeometryValidated/);
assert.match(barrier, /initialConfiguration/);
assert.match(pathContract, /closed-system-fixed-composition/);
assert.match(pathContract, /explicit-reservoir-extended-system/);
assert.match(pathContract, /fixedMaterialSites/);
assert.match(pathContract, /does not reproduce the frozen candidate endpoint/);
assert.match(readme, /Build 366/);
assert.match(readme, /coordinate-bearing external action paths/i);
assert.match(benchmark, /Coordinate-bearing external action paths \(Build 366\)/);
assert.match(benchmark, /not a browser-generated\s+reaction path/);

console.log("coordinate-bearing action-path portal contract passed");
