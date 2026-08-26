#!/usr/bin/env node
import assert from "node:assert/strict";
import fs from "node:fs";

const app = fs.readFileSync(new URL("../apps/iqc-growth-live/app.js", import.meta.url), "utf8");
const match = app.match(/function notebookRegisteredPairAudit[\s\S]*?\n}\n\nfunction signedNotebookDelta/);
assert.ok(match, "registered pair audit remains extractable");
const source = match[0].replace(/\n\nfunction signedNotebookDelta$/, "");
const notebookRegisteredPairAudit = Function(`"use strict"; ${source}; return notebookRegisteredPairAudit;`)();

const study = (armId, overrides = {}) => ({
  recipeId: "bulk-order", recipeLabel: "Bulk crystal order", factor: "clusters² promotion",
  question: "Does hierarchy reduce branch work?", armId,
  armLabel: armId === "reference" ? "hierarchical" : "primitive only",
  settingsStillMatch: true, settings: { hierarchyEnabled: armId === "reference" },
  outcomes: ["accepted branches", "causal depth"],
  boundary: "Finite structural comparison only.", autoExecuted: false, ...overrides,
});
const entry = (armId, overrides = {}) => ({ registeredStudy: study(armId, overrides) });
const controlled = { sameInput: true, changedFactors: [{ key: "hierarchy", label: "hierarchy" }] };

const passing = notebookRegisteredPairAudit(entry("reference"), entry("contrast"), controlled);
assert.equal(passing.valid, true);
assert.equal(passing.status, "registered");
assert.equal(passing.referenceLabel, "hierarchical");
assert.equal(passing.contrastLabel, "primitive only");
assert.deepEqual(passing.outcomes, ["accepted branches", "causal depth"]);
assert.equal(passing.autoExecuted, false);

assert.equal(notebookRegisteredPairAudit(entry("reference"), entry("reference"), controlled).valid, false,
  "two copies of one arm are not a registered pair");
assert.equal(notebookRegisteredPairAudit(entry("reference"), entry("contrast", { settingsStillMatch: false }), controlled).valid, false,
  "an edited arm fails closed");
assert.equal(notebookRegisteredPairAudit(entry("reference"), entry("contrast"),
  { sameInput: true, changedFactors: [{}, {}] }).valid, false, "multiple interventions fail closed");
assert.equal(notebookRegisteredPairAudit(entry("reference"), entry("contrast"),
  { sameInput: false, changedFactors: [{}] }).valid, false, "different input geometry fails closed");
assert.equal(notebookRegisteredPairAudit({}, entry("contrast"), controlled).status, "unavailable",
  "legacy summaries remain visibly uncertified");

console.log("registered study pair audit passed");
