import assert from "node:assert/strict";
import fs from "node:fs";

const html = fs.readFileSync("apps/iqc-growth-live/index.html", "utf8");
const alias = fs.readFileSync("iqc-growth-live/index.html", "utf8");
const app = fs.readFileSync("apps/iqc-growth-live/app.js", "utf8");
const moduleText = fs.readFileSync("apps/iqc-growth-live/leapfrog-physics-cycle.mjs", "utf8");
const css = fs.readFileSync("apps/iqc-growth-live/style.css", "utf8");
const readme = fs.readFileSync("apps/iqc-growth-live/README.md", "utf8");
const benchmark = fs.readFileSync("docs/projects/materials-recursive-gcts-benchmark.md", "utf8");

for (const document of [html, alias]) {
  for (const id of ["multiphysicsCycleBadge", "multiphysicsCouplingModeSelect",
    "multiphysicsCycleNextButton", "multiphysicsCycleFlow", "multiphysicsCycleState",
    "multiphysicsCycleBoundary"]) assert.match(document, new RegExp(`id="${id}"`));
  assert.match(document, /Leap-frog co-simulation cycle/);
  assert.match(document, /Event-resolved · require J \+ action physics/);
}
assert.match(app, /leapfrog-physics-cycle\.mjs\?v=20260831-376/);
assert.match(app, /function currentLeapfrogPhysicsCycle\(\)/);
assert.match(app, /function renderLeapfrogPhysicsCycle\(\)/);
assert.match(app, /function routeLeapfrogNextAction\(\)/);
assert.match(app, /couplingModeGate\(currentLeapfrogPhysicsCycle\(\)\)/);
assert.match(app, /leapfrogPhysicsCycle: currentLeapfrogPhysicsCycle\(\)/);
assert.match(app, /"leapfrog-physics-cycle": \{ stage: 4, controlId: "multiphysicsCouplingModeSelect"/);
assert.match(moduleText, /targetUsed: false/);
assert.match(moduleText, /physicalTimeIntegrated: false/);
assert.match(moduleText, /current-interface transport map/);
assert.match(moduleText, /candidate-resolved barriers and prefactors/);
assert.match(css, /\.multiphysics-cycle-flow/);
assert.match(css, /grid-template-columns:repeat\(6,minmax\(0,1fr\)\)/);
assert.match(readme, /Build 358/);
assert.match(readme, /interface-flux map,\s+frozen candidate/);
assert.match(benchmark, /Leap-frog multiphysics refresh cycle \(Build 358\)/);
assert.match(benchmark, /co-simulation protocol/);
console.log("leap-frog multiphysics cycle portal contract passed");
