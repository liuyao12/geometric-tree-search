#!/usr/bin/env node
import assert from "node:assert/strict";
import fs from "node:fs";

const app = fs.readFileSync(new URL("../apps/iqc-growth-live/app.js", import.meta.url), "utf8");
const match = app.match(/function studyArmNotebookEvidence[\s\S]*?\n}\n\nfunction renderStudyComparisonProgress/);
assert.ok(match, "study-arm notebook matcher remains extractable");
const source = match[0].replace(/\n\nfunction renderStudyComparisonProgress$/, "");
const entries = [
  { id: "a", scenarioId: "competition", registeredStudy: { recipeId: "bulk-order", armId: "reference", settingsStillMatch: true },
    executionEvidence: { executed: false, structuralLeapEvents: 0 } },
  { id: "b", scenarioId: "competition", registeredStudy: { recipeId: "bulk-order", armId: "reference", settingsStillMatch: true },
    executionEvidence: { executed: true, structuralLeapEvents: 3 } },
  { id: "wrong-sample", scenarioId: "cdyb", registeredStudy: { recipeId: "bulk-order", armId: "reference", settingsStillMatch: true },
    executionEvidence: { executed: true, structuralLeapEvents: 9 } },
  { id: "edited", scenarioId: "competition", registeredStudy: { recipeId: "bulk-order", armId: "reference", settingsStillMatch: false },
    executionEvidence: { executed: true, structuralLeapEvents: 8 } },
  { id: "contrast", scenarioId: "competition", registeredStudy: { recipeId: "bulk-order", armId: "contrast", settingsStillMatch: true },
    executionEvidence: { executed: false, structuralLeapEvents: 0 } },
];
const studyArmNotebookEvidence = Function("experimentNotebookEntries", "scenarioSelect",
  `"use strict"; ${source}; return studyArmNotebookEvidence;`)(entries, { value: "competition" });

assert.deepEqual(studyArmNotebookEvidence("bulk-order", "reference"), {
  savedRuns: 2, executedRuns: 1, latest: entries[1],
});
assert.deepEqual(studyArmNotebookEvidence("bulk-order", "contrast"), {
  savedRuns: 1, executedRuns: 0, latest: entries[4],
});
assert.deepEqual(studyArmNotebookEvidence("moire", "reference"), {
  savedRuns: 0, executedRuns: 0, latest: null,
});

console.log("study arm progress matching passed");
