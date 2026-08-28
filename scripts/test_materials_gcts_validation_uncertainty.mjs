import assert from "node:assert/strict";
import { channelValidationMetricsFromCounts, validationOccurrenceJackknife }
  from "../apps/iqc-growth-live/validation-uncertainty.mjs";

const record = (sampleIndex, observedCompatible, predictedCompatible) => ({
  sampleIndex, observedCompatible, predictedCompatible,
});

const records = [
  record(0, true, true), record(0, false, false),
  record(1, true, true), record(1, false, true),
  record(2, true, false), record(2, false, false),
  record(3, true, false), record(3, false, true),
];

const metrics = channelValidationMetricsFromCounts({ tp: 2, fp: 2, fn: 2, tn: 2 });
assert.equal(metrics.labels, 8);
assert.equal(metrics.balancedAccuracy, .5);

const audit = validationOccurrenceJackknife(records);
assert.equal(audit.method, "delete-one-heldout-occurrence jackknife");
assert.equal(audit.occurrenceBlocks, 4);
assert.equal(audit.sectorLabels, 8);
assert.equal(audit.finiteReplicates, 4);
assert.equal(audit.estimate, .5);
assert.ok(Math.abs(audit.standardError - Math.sqrt(1 / 24)) < 1e-12);
assert.ok(Math.abs(audit.lower - (.5 - 1.96 * Math.sqrt(1 / 24))) < 1e-12);
assert.ok(Math.abs(audit.upper - (.5 + 1.96 * Math.sqrt(1 / 24))) < 1e-12);
assert.match(audit.groupingUnit, /within an occurrence remain correlated/);
assert.match(audit.interpretation, /not an independent-material/);

const empty = validationOccurrenceJackknife([]);
assert.equal(empty.occurrenceBlocks, 0);
assert.equal(empty.sectorLabels, 0);
assert.equal(empty.estimate, null);
assert.equal(empty.lower, null);
assert.equal(empty.upper, null);

console.log("occurrence-blocked validation uncertainty contract passed");
