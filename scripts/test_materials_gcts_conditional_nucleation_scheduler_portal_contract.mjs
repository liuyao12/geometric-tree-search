import assert from "node:assert/strict";
import fs from "node:fs";

const root = new URL("../", import.meta.url);
const read = (path) => fs.readFileSync(new URL(path, root), "utf8");
const app = read("apps/iqc-growth-live/app.js");
const html = read("apps/iqc-growth-live/index.html");
const css = read("apps/iqc-growth-live/style.css");
const moduleSource = read("apps/iqc-growth-live/conditional-nucleation-scheduler.mjs");
const atlas = read("apps/iqc-growth-live/evidence-atlas.js");
const readme = read("apps/iqc-growth-live/README.md");
const methods = read("docs/projects/materials-recursive-gcts-benchmark.md");

for (const token of ["buildConditionalNucleationSchedule", "mulberry32",
  "logTotalIntensityPerSecond", "waitingUniform", "normalizedPosition", "positionMetre",
  "firstOmittedEventFallsInsideExposure", "scheduleTruncated",
  "truncationProbe",
  "atomisticNucleusConstructed: false", "crystallographicPoseAssigned: false",
  "gctsSeedChanged: false", "gctsClockChanged: false", "targetUsed: false"])
  assert.ok(moduleSource.includes(token), token);

for (const token of ["Seeded nucleation-event hypotheses",
  "id=\"nucleationScheduleSeedSelect\"", "id=\"nucleationScheduleCapSelect\"",
  "id=\"freezeNucleationSchedule\"", "id=\"releaseNucleationSchedule\"",
  "id=\"nucleationSchedulePlot\"", "id=\"nucleationScheduleMetrics\"",
  "Points are not atomistic nuclei"])
  assert.ok(html.includes(token), token);

for (const token of ["conditional-nucleation-scheduler.mjs?v=20260901-415",
  "function renderConditionalNucleationSchedule()", "function freezeConditionalNucleationSchedule()",
  "conditionalNucleationScheduleAudit = buildConditionalNucleationSchedule(",
  "events: conditionalNucleationScheduleAudit.events.map", "no atoms or GCTS seeds changed"])
  assert.ok(app.includes(token), token);

assert.ok(css.includes(".conditional-nucleation-scheduler"));
assert.ok(atlas.includes("Seeded conditional nucleation schedule"));
assert.ok(readme.includes("Build 413 · conditional nucleation becomes a geometric event schedule"));
assert.ok(methods.includes("Seeded conditional nucleation point process (Build 413)"));

console.log("conditional nucleation scheduler portal contract: passed");
