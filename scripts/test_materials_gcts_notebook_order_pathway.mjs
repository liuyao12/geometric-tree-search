import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const source = readFileSync(new URL("../apps/iqc-growth-live/app.js", import.meta.url), "utf8");
const match = source.match(/function notebookMultiscaleOrderPathway\([\s\S]*?\n}\n\nfunction showNotebookPathwayState/);
assert.ok(match, "notebook multiscale pathway implementation must remain extractable");
const functionSource = match[0].replace(/\n\nfunction showNotebookPathwayState$/, "");
const notebookMultiscaleOrderPathway = Function(`"use strict"; return (${functionSource});`)();

const point = (step, localOrder, prominence, status = "accepted") => ({
  step,
  status,
  atoms: 100 + step * 10,
  clusters: step,
  depth: step,
  orientationalOrder: { harmonics: { 4: { mean: localOrder / 2 }, 6: { mean: localOrder }, 12: { mean: localOrder * 1.5 } } },
  scattering: { summary: { peakProminence: prominence } },
});

const comparison = {
  firstPoints: [point(0, 0.2, 0.5, "seed"), point(1, 0.3, 0.7), point(2, 0.4, 1.0, "fixed")],
  secondPoints: [point(0, 0.2, 0.5, "seed"), point(1, 0.35, 0.6), point(2, 0.5, 0.8, "rejected")],
};
const pathway = notebookMultiscaleOrderPathway(comparison, 6);
assert.equal(pathway.harmonic, 6);
assert.equal(pathway.first.length, 3);
assert.equal(pathway.second.length, 3);
assert.equal(pathway.localMinimum, 0.2);
assert.equal(pathway.localMaximum, 0.5);
assert.equal(pathway.reciprocalMinimum, 0.5);
assert.equal(pathway.reciprocalMaximum, 1.0);
assert.ok(pathway.firstSummary.normalizedPathLength > 0);
assert.ok(pathway.secondSummary.normalizedPathLength > 0);
assert.ok(pathway.finalNormalizedSeparation > 0);
assert.equal(pathway.properRotationInvariant, true);
assert.equal(pathway.physicalTimeModeled, false);
assert.equal(pathway.phaseDiagram, false);

const degenerate = notebookMultiscaleOrderPathway({
  firstPoints: [point(0, 0.3, 0.8), point(1, 0.3, 0.8)],
  secondPoints: [point(0, 0.3, 0.8), point(1, 0.3, 0.8)],
}, 6);
assert.ok(Number.isFinite(degenerate.firstSummary.normalizedPathLength));
assert.equal(degenerate.firstSummary.normalizedPathLength, 0);
assert.equal(degenerate.finalNormalizedSeparation, 0);

const legacy = structuredClone(comparison);
legacy.secondPoints[1].scattering = null;
assert.equal(notebookMultiscaleOrderPathway(legacy, 6), null);

const harmonicFour = notebookMultiscaleOrderPathway(comparison, 4);
assert.equal(harmonicFour.localMaximum, 0.25);

console.log("notebook multiscale order pathway: passed");
