#!/usr/bin/env node
import assert from "node:assert/strict";
import fs from "node:fs";

const app = fs.readFileSync(new URL("../apps/iqc-growth-live/app.js", import.meta.url), "utf8");
const match = app.match(/function notebookInterventionFactors[\s\S]*?\n}\n\nfunction experimentNotebookSummary/);
assert.ok(match, "notebook factorization remains extractable");
const source = match[0].replace(/\n\nfunction experimentNotebookSummary$/, "");
const notebookInterventionFactors = Function(`"use strict"; ${source}; return notebookInterventionFactors;`)();

const baseReceipt = () => ({
  pipeline: { stageName: "material growth", visibleStage: 4 },
  input: { externalGeometry: { id: "box", label: "box", shape: "box", publicReachScale: 1,
    parametersAngstrom: { x: 20, y: 20, z: 20 } }, periodicBoundary: [true, true, true] },
  geometry: { requestedMode: "auto", resolvedMode: "lattice", metricIsometryToleranceMode: "balanced",
    metricIsometryToleranceAngstrom: .05 },
  marking: { config: { representation: "ports", reach: 2, channels: 0 }, searchMode: "marked",
    active: { id: "m1", vocabularyKey: "v1" } },
  search: {
    explicitSites: 216, policy: "marked", hierarchyEnabled: true,
    experimentProtocol: { id: "bulk", label: "bulk continuation", preset: true,
      settings: { hierarchyEnabled: true, epitaxyTemplateMode: "none", requestedGrowthNuclei: 1 } },
    scheduling: { mode: "commuting" }, configurationalPathEnsemble: { dimensionlessExplorationScale: 0, seed: 1 },
    multiNucleusGrowth: { requestedNuclei: 1, selection: { mode: "interior" } },
    epitaxialRegistryRanking: { mode: "none", effectiveWeight: 0 },
  },
  structuralEvidence: { selectedView: "order", rdf: { pair: "all" },
    localOrientationalOrder: { harmonic: 6, spatialMap: { enabled: false } } },
  computationalWork: { assumptions: { mdSteps: 1000 } },
});

const clone = (value) => JSON.parse(JSON.stringify(value));
const changedKeys = (first, second) => {
  const a = notebookInterventionFactors(first); const b = notebookInterventionFactors(second);
  return Object.keys(a).filter((key) => a[key].value !== b[key].value);
};

{
  const a = baseReceipt(); const b = clone(a);
  b.search.hierarchyEnabled = false; b.search.experimentProtocol.settings.hierarchyEnabled = false;
  assert.deepEqual(changedKeys(a, b), ["hierarchy"], "nested protocol settings do not duplicate hierarchy");
}
{
  const a = baseReceipt(); const b = clone(a);
  b.search.policy = "action"; b.marking.searchMode = "action";
  assert.deepEqual(changedKeys(a, b), ["ranking"], "marking metadata does not duplicate search policy");
}
{
  const a = baseReceipt(); const b = clone(a);
  b.marking.config.representation = "halo";
  assert.deepEqual(changedKeys(a, b), ["marking"]);
}
{
  const a = baseReceipt(); const b = clone(a);
  b.search.epitaxialRegistryRanking.mode = "hex-mismatch";
  b.search.experimentProtocol.settings.epitaxyTemplateMode = "hex-mismatch";
  assert.deepEqual(changedKeys(a, b), ["softPhysics"]);
}
{
  const a = baseReceipt(); const b = clone(a);
  b.search.multiNucleusGrowth.requestedNuclei = 4;
  b.search.experimentProtocol.settings.requestedGrowthNuclei = 4;
  assert.deepEqual(changedKeys(a, b), ["nucleation"]);
}
{
  const a = baseReceipt(); const b = clone(a);
  b.input.externalGeometry.id = "hourglass"; b.input.externalGeometry.label = "hourglass";
  b.input.externalGeometry.shape = "hourglass";
  assert.deepEqual(changedKeys(a, b), ["boundary"]);
}

console.log("orthogonal notebook intervention factors passed");
