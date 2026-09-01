import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const atlas = fs.readFileSync("apps/iqc-growth-live/evidence-atlas.js", "utf8");
const model = fs.readFileSync("apps/iqc-growth-live/hierarchy-physics-protocol-packet.mjs", "utf8");
const style = fs.readFileSync("apps/iqc-growth-live/style.css", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  assert.match(document, /hierarchyPhysicsProtocolPacket/);
  assert.match(document, /Scale-bridge protocol packet/);
  assert.match(document, /Copy plan link/);
  assert.match(document, /evidence-atlas\.js\?v=20260901-428/);
}
assert.match(atlas, /hierarchy-physics-protocol-packet\.mjs\?v=20260901-428/);
assert.match(atlas, /sharedHierarchyPhysicsSelection/);
assert.match(atlas, /protocolPacketDownload/);
assert.match(model, /gcts-hierarchy-physics-protocol-packet-v1/);
assert.match(model, /executionAuthorized: false/);
assert.match(model, /bridgeSha256/);
assert.match(style, /hierarchy-physics-protocol-packet/);
assert.match(readme, /Build 391/);
assert.match(benchmark, /Portable scale-bridge protocol packets \(Build 391\)/);

console.log("hierarchy physics protocol packet portal contract passed");
