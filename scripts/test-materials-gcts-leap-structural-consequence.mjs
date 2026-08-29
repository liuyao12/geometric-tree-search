import assert from "node:assert/strict";
import { buildDimensionlessLeapConsequence, STRUCTURAL_LEAP_AXES,
  UNRESOLVED_DYNAMICAL_QUANTITIES } from "../apps/iqc-growth-live/leap-structural-consequence.mjs";

const records = [
  { id: "atoms", label: "sites", group: "mesoscale", before: 100, after: 125, domain: "adaptive" },
  { id: "coordination", label: "deficit", group: "local", before: .4, after: .2, domain: [0, 1] },
  { id: "packing", label: "packing", group: "local", before: 1, after: 1.1, domain: "adaptive" },
  { id: "composition", label: "composition", group: "chemistry", before: .1, after: .1, domain: [0, 1] },
  { id: "radius", label: "radius", group: "mesoscale", before: 10, after: 12, domain: "adaptive" },
  { id: "reciprocal", label: "contrast", group: "reciprocal", before: null, after: 2, domain: "adaptive" },
];

const result = buildDimensionlessLeapConsequence(records, {
  component: "total", acceptedActions: 4, rejectedActions: 2,
  atomsBefore: 100, atomsAfter: 125, settledGeometry: true,
});
assert.equal(result.axes.length, STRUCTURAL_LEAP_AXES.length);
assert.equal(result.operation.emittedSites, 25);
assert.equal(result.resolvedObservableCount, 5);
assert.equal(result.changedObservableCount, 4);
assert.equal(result.axes.find((axis) => axis.id === "inventory").signedMean, .2);
assert.equal(result.axes.find((axis) => axis.id === "local").resolvedFields, 2);
assert.equal(result.axes.find((axis) => axis.id === "reciprocal").signedMean, null);
assert.equal(result.normalization.favorableDirectionAssigned, false);
assert.equal(result.unresolvedDynamics.length, UNRESOLVED_DYNAMICAL_QUANTITIES.length);
assert.ok(result.unresolvedDynamics.every((quantity) => quantity.status === "not inferred"));
assert.equal(result.targetUsed, false);
assert.equal(result.physicalTimeIntegrated, false);
assert.throws(() => buildDimensionlessLeapConsequence({}), /array/);

const reversed = buildDimensionlessLeapConsequence(records.map((record) => ({
  ...record, before: record.after, after: record.before,
})));
for (const axis of result.axes) {
  const counterpart = reversed.axes.find((candidate) => candidate.id === axis.id);
  if (Number.isFinite(axis.signedMean)) assert.ok(Math.abs(axis.signedMean + counterpart.signedMean) < 1e-12);
  if (Number.isFinite(axis.rmsMagnitude)) assert.ok(Math.abs(axis.rmsMagnitude - counterpart.rmsMagnitude) < 1e-12);
}

console.log("leap structural consequence tests passed");
