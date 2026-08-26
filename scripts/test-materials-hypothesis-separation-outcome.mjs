import assert from "node:assert/strict";
import { compareHypothesisSeparationOutcomes }
  from "../apps/iqc-growth-live/hypothesis-separation-outcome.js";

const manifest = { schema: 1, mode: "conditional", pair: { firstId: "composition", secondId: "charge" },
  ablatedTermId: "composition", retainedComparisonTermId: "charge",
  sourceCandidateSetDigest: "frontier-01", sourceAuditDigest: "audit-01",
  settingsStillMatch: true, inputScenarioStillMatches: true };
const point = (atoms, clusters, depth, accepted, rejected, prominence, q6) => ({ atoms, clusters, depth,
  cumulativeAccepted: accepted, cumulativeRejected: rejected,
  scattering: { summary: { peakProminence: prominence } },
  orientationalOrder: { harmonics: { 6: { mean: q6 } } } });
const entry = (id, arm, points, factor = arm) => ({ id, inputIdentity: "nacl:sha256",
  hypothesisSeparationExperiment: { ...manifest, arm },
  executionEvidence: { executed: true, structuralLeapEvents: points.length - 1, targetUsed: false },
  trajectory: { points, historyTruncated: false, targetUsed: false },
  interventionFactors: { geometry: { value: "same" }, search: { value: "same" },
    hypothesisSeparation: { value: factor } } });
const baseline = entry("base", "baseline", [point(10, 1, 0, 0, 0, 1, .2), point(20, 3, 1, 2, 1, 3, .5), point(40, 5, 2, 4, 2, 4, .7)]);
const ablation = entry("abl", "ablation", [point(10, 1, 0, 0, 0, 1, .2), point(17, 2, 1, 1, 3, 2, .35)]);
const audit = compareHypothesisSeparationOutcomes([ablation, baseline]);
assert.equal(audit.comparable, true);
assert.equal(audit.commonUpdates, 1);
assert.equal(audit.baselineEntryId, "base");
assert.equal(audit.ablationEntryId, "abl");
assert.deepEqual(audit.metrics.slice(0, 5).map((metric) => metric.delta), [-3, -1, 0, -1, 2]);
assert.equal(audit.metrics[5].delta, -1);
assert.ok(Math.abs(audit.metrics[6].delta + .15) < 1e-12);
assert.equal(audit.physicalTimeInferred, false);
assert.equal(audit.causalPhysicalMechanismInferred, false);
assert.equal(audit.candidatesPooled, false);
assert.match(audit.boundary, /not physical time/);
assert.equal(compareHypothesisSeparationOutcomes([baseline]).reason, "select-two");
assert.equal(compareHypothesisSeparationOutcomes([{ ...baseline, inputIdentity: "other" }, ablation]).reason, "input-mismatch");
assert.equal(compareHypothesisSeparationOutcomes([{ ...baseline,
  interventionFactors: { ...baseline.interventionFactors, geometry: { value: "changed" } } }, ablation]).reason, "controls-mismatch");
assert.equal(compareHypothesisSeparationOutcomes([{ ...baseline,
  trajectory: { ...baseline.trajectory, historyTruncated: true } }, ablation]).reason, "history-truncated");
assert.equal(compareHypothesisSeparationOutcomes([{ ...baseline,
  executionEvidence: { ...baseline.executionEvidence, targetUsed: true } }, ablation]).reason, "target-tainted");
console.log("materials hypothesis separation outcome: passed");
