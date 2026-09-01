import assert from "node:assert/strict";
import fs from "node:fs";

const root = new URL("../", import.meta.url);
const read = path => fs.readFileSync(new URL(path, root), "utf8");
const app = read("apps/iqc-growth-live/app.js");
const html = read("apps/iqc-growth-live/index.html");
const css = read("apps/iqc-growth-live/style.css");
const moduleSource = read("apps/iqc-growth-live/critical-nucleus-geometry.mjs");
const atlas = read("apps/iqc-growth-live/evidence-atlas.js");
const readme = read("apps/iqc-growth-live/README.md");
const methods = read("docs/projects/materials-recursive-gcts-benchmark.md");

for (const token of ["CRITICAL_NUCLEUS_GEOMETRY_REQUEST_SCHEMA",
  "CRITICAL_NUCLEUS_GEOMETRY_RESPONSE_SCHEMA", "buildCriticalNucleusGeometryRequest",
  "validateCriticalNucleusGeometryResponse", "embedCriticalNucleusAtScheduledEvents",
  "isotropic-proper-rotation", "uniform-in-plane", "minimumPairDistanceAngstrom",
  "meanCommittor", "independentShootingTrajectories", "nucleiCommittedToGrowth: false",
  "gctsSeedChanged: false", "gctsClockChanged: false", "targetUsed: false"])
  assert.ok(moduleSource.includes(token), token);

for (const token of ["Atomistic critical-nucleus geometry",
  "id=\"downloadCriticalNucleusGeometryRequest\"",
  "id=\"importCriticalNucleusGeometryResponse\"",
  "id=\"criticalNucleusOrientationSeedSelect\"",
  "id=\"criticalNucleusPreviewCapSelect\"", "id=\"freezeCriticalNucleusPreview\"",
  "id=\"criticalNucleusGeometryPlot\"", "id=\"criticalNucleusGeometryMetrics\"",
  "A CNT critical scale does not determine atom count"])
  assert.ok(html.includes(token), token);

for (const token of ["critical-nucleus-geometry.mjs?v=20260901-442",
  "function renderCriticalNucleusGeometry()", "downloadCriticalNucleusGeometryEvidenceRequest",
  "validateCriticalNucleusGeometryFile", "freezeScheduledCriticalNucleusPreview",
  "scheduledCriticalNucleusPreviewAudit = embedCriticalNucleusAtScheduledEvents(",
  "criticalNucleusGeometry:", "committedToGrowth: false", "growth seed unchanged"])
  assert.ok(app.includes(token), token);

assert.ok(css.includes(".critical-nucleus-geometry"));
assert.ok(atlas.includes("Atomistic critical-nucleus geometry"));
assert.ok(readme.includes("Build 414 · critical-nucleus atoms become an evidence-bound preview"));
assert.ok(methods.includes("Evidence-bound atomistic critical-nucleus preview (Build 414)"));

console.log("critical nucleus geometry portal contract: passed");
