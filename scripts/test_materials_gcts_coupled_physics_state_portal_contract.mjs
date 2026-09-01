import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const stateModule = fs.readFileSync("apps/iqc-growth-live/coupled-physics-state.mjs", "utf8");
const barrierModule = fs.readFileSync("apps/iqc-growth-live/external-action-barrier.mjs", "utf8");
const css = fs.readFileSync("apps/iqc-growth-live/style.css", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  for (const id of ["coupledStateBadge", "coupledStateChannels", "coupledStateState",
    "coupledStateBoundary"]) assert.match(document, new RegExp(`id="${id}"`));
  assert.match(document, /Shared-state coherence/);
}
assert.match(app, /coupled-physics-state\.mjs\?v=20260901-438/);
assert.match(app, /function currentCouplingStateExpectation\(\)/);
assert.match(app, /function currentCoupledPhysicsState\(\)/);
assert.match(app, /function renderCoupledPhysicsState\(\)/);
assert.match(app, /coupledPhysicsState: currentCoupledPhysicsState\(\)/);
assert.match(app, /couplingStateExpectation: currentCouplingStateExpectation\(\)/);
assert.match(app, /"coupled-state-coherence": \{ stage: 4, controlId: "coupledStateChannels"/);
assert.match(app, /"select-kinetic-event": "Select HTST \/ seeded KMC event"/);
assert.match(stateModule, /geometryUsedAsThermodynamicState: false/);
assert.match(stateModule, /evidenceCombinedWhenIncompatible: false/);
assert.match(stateModule, /coupling-state-digest-mismatch/);
assert.match(barrierModule, /kinetic response does not match the requested shared coupling state/);
assert.match(barrierModule, /thermodynamic temperature does not match the requested shared state/);
assert.match(css, /\.coupled-state-channels/);
assert.match(readme, /Build 360/);
assert.match(readme, /unselected event blocks commit/);
assert.match(benchmark, /Shared-state coherence across coupled physics \(Build 360\)/);
assert.match(benchmark, /prevents accidental mixing/);
console.log("coupled external-physics state portal contract passed");
