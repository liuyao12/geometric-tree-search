import assert from "node:assert/strict";
import fs from "node:fs";

const root = new URL("../", import.meta.url);
const read = (path) => fs.readFileSync(new URL(path, root), "utf8");
const app = read("apps/iqc-growth-live/app.js");
const html = read("apps/iqc-growth-live/index.html");
const css = read("apps/iqc-growth-live/style.css");
const moduleSource = read("apps/iqc-growth-live/classical-nucleation-evidence.mjs");
const atlas = read("apps/iqc-growth-live/evidence-atlas.js");
const readme = read("apps/iqc-growth-live/README.md");
const methods = read("docs/projects/materials-recursive-gcts-benchmark.md");

for (const token of ["BULK_DRIVING_FORCE_REQUEST_SCHEMA", "BULK_DRIVING_FORCE_RESPONSE_SCHEMA",
  "measureNormalizedWulffGeometry", "buildBulkDrivingForceRequest",
  "validateBulkDrivingForceResponse", "buildClassicalNucleationWork",
  "criticalScaleMetre", "barrierElectronVolt", "wulffIdentityRelativeResidual",
  "heterogeneousShapeFactorApplied: false", "criticalAtomCountInferred: false",
  "nucleationRateInferred: false", "targetUsed: false"]) assert.ok(moduleSource.includes(token), token);

for (const token of ["id=\"classicalNucleationEvidence\"", "Conditional nucleation-work profile",
  "id=\"classicalNucleationPlot\"", "id=\"classicalNucleationMetrics\"",
  "id=\"downloadBulkDrivingRequest\"", "id=\"importBulkDrivingResponse\"",
  "id=\"bulkDrivingResponseInput\"", "id=\"classicalNucleationState\"",
  "id=\"classicalNucleationBoundary\""]) assert.ok(html.includes(token), token);

for (const token of ["classical-nucleation-evidence.mjs?v=20260901-449",
  "function renderClassicalNucleationEvidence()", "function classicalNucleationReceipt()",
  "function downloadBulkDrivingForceEvidenceRequest()", "function validateBulkDrivingForceFile(file)",
  "classicalNucleation: classicalNucleationReceipt()", "candidateSetChanged: false",
  "growthRankingChanged: activeClassicalCapillarityWeight() > 0", "buildId: \"20260901-449\""]) assert.ok(app.includes(token), token);

assert.ok(css.includes(".classical-nucleation-evidence"));
assert.ok(css.includes(".classical-net"));
assert.ok(atlas.includes("Conditional classical nucleation work"));
assert.ok(atlas.includes("bulk parent-to-nucleus driving-force density Δg"));
assert.ok(readme.includes("Build 410 · geometry-bound classical nucleation work"));
assert.ok(methods.includes("Conditional Wulff nucleation-work bridge (Build 410)"));
assert.ok(html.includes("app.js?v=20260901-449"));
assert.ok(html.includes("style.css?v=20260901-449"));
assert.ok(html.includes("evidence-atlas.js?v=20260901-449"));

console.log("classical nucleation portal contract: passed");
