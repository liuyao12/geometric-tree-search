#!/usr/bin/env node
import assert from "node:assert/strict";
import fs from "node:fs";

const app = fs.readFileSync(new URL("../apps/iqc-growth-live/app.js", import.meta.url), "utf8");
const match = app.match(/function notebookOutcomeRecord[\s\S]*?\n}\n\nfunction experimentNotebookSummary/);
assert.ok(match, "registered outcome serializer remains extractable");
const source = match[0].replace(/\n\nfunction experimentNotebookSummary$/, "");
const { notebookRegisteredOutcomeObservations } = Function(
  `"use strict"; ${source}; return { notebookRegisteredOutcomeObservations };`,
)();

const final = {
  domain: { continuationAtoms: 24 },
  scattering: { summary: { peakProminence: 1.25 } },
  orientationalOrder: { harmonics: { 6: { mean: 0.72 } } },
  morphology: { lineageEnsemble: { effectiveNucleusCount: 2.5, sharedInterfaceFraction: 0.125 } },
};
const receipt = {
  studyDesign: { id: "epitaxy", predictionAudit: { evidence: { microscope: { metrics: null } } } },
  marking: { learned: { validationMismatch: 0.14 } },
  search: {
    explicitSites: 160,
    rejectedDecisions: 7,
    publicBoundaryPrunes: 3,
    epitaxialRegistryRanking: { acceptedMeanScore: 0.81 },
    actionDefectPrecursorRanking: { acceptedMeanBurden: 0.22 },
    mesoscopicLoopClosureRanking: { acceptedMeanIndependentCompatiblePaths: 1.5 },
    localConstraintWork: { evaluations: 420 },
  },
};
const epitaxy = notebookRegisteredOutcomeObservations(receipt, [final], 24, 3);
assert.deepEqual(Object.keys(epitaxy), ["registry score", "seam burden", "|ψ6| response"]);
assert.equal(epitaxy["registry score"].value, 0.81);
assert.equal(epitaxy["seam burden"].value, 0.22);
assert.equal(epitaxy["|ψ6| response"].value, 0.72);
assert.equal(epitaxy["registry score"].available, true);

receipt.studyDesign.id = "quasicrystal";
const quasicrystal = notebookRegisteredOutcomeObservations(receipt, [final], 24, 3);
assert.equal(quasicrystal["continuation precision"].available, false);
assert.match(quasicrystal["continuation precision"].limitation, /separate sealed scorer/);
assert.equal(quasicrystal["causal depth"].value, 3);
assert.equal(quasicrystal["S(q) response"].value, 1.25);

receipt.studyDesign.id = "molecular-ice";
receipt.search.finiteIceAnchorTrace = {
  emittedAnchorCount: 8,
  unresolvedOrientationDomains: 5,
  waves: [{ rejectedCandidateAnchors: 3 }, { rejectedCandidateAnchors: 2 }],
};
const ice = notebookRegisteredOutcomeObservations(receipt, [final], 8, 2);
assert.equal(ice["exact oxygen anchors"].value, 8);
assert.equal(ice["rejected poses"].value, 5);
assert.equal(ice["orientation domains"].value, 5);

console.log("registered response serialization passed");
