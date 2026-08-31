import assert from "node:assert/strict";
import { buildHierarchyPhysicsTransport, HIERARCHY_TRANSPORT_STAGES,
  HIERARCHY_TRANSPORT_STATES }
  from "../apps/iqc-growth-live/hierarchy-physics-transport.mjs";

assert.deepEqual(HIERARCHY_TRANSPORT_STAGES.map((stage) => stage.id),
  ["atomic", "cluster", "macro", "stationary"]);
assert.deepEqual(Object.keys(HIERARCHY_TRANSPORT_STATES),
  ["exact", "reevaluated", "representation", "open"]);

const iqc = buildHierarchyPhysicsTransport("iqc-reencoding");
assert.equal(iqc.schema, "gcts-hierarchy-physics-transport-v1");
assert.equal(iqc.rows.length, 10);
assert.deepEqual(iqc.stageSummaries.map((stage) => stage.total), [10, 10, 10, 10]);
assert.deepEqual(iqc.stageSummaries[0].counts,
  { exact: 5, reevaluated: 0, representation: 3, open: 2 });
assert.deepEqual(iqc.stageSummaries[1].counts,
  { exact: 5, reevaluated: 2, representation: 1, open: 2 });
assert.deepEqual(iqc.stageSummaries[2].counts,
  { exact: 4, reevaluated: 3, representation: 1, open: 2 });
assert.deepEqual(iqc.stageSummaries[3].counts,
  { exact: 0, reevaluated: 0, representation: 0, open: 10 });
assert.deepEqual(iqc.exactMacroChannels,
  ["colored-geometry", "proper-pose", "connection-topology", "composition"]);
assert.deepEqual(iqc.representationOnlyMacroChannels, ["residuals"]);
assert.deepEqual(iqc.openMacroChannels, ["kinetics", "nonlocal"]);
assert.deepEqual(iqc.stationaryPhysicsChannels, []);
assert.equal(iqc.targetUsed, false);
assert.equal(iqc.coarsePhysicsInferredFromHierarchyDepth, false);

const residuals = iqc.rows.find((row) => row.id === "residuals");
assert.deepEqual(residuals.stages.map((stage) => stage.status),
  ["exact", "representation", "representation", "open"]);
assert.match(residuals.boundary, /not a predicted atom/);

const nacl = buildHierarchyPhysicsTransport("nacl-stationary");
assert.deepEqual(nacl.stationaryPhysicsChannels,
  ["colored-geometry", "proper-pose", "connection-topology", "composition"]);
assert.deepEqual(nacl.stageSummaries[3].counts,
  { exact: 4, reevaluated: 1, representation: 0, open: 5 });
assert.equal(nacl.stageSummaries[3].causalCount, 5);
assert.equal(nacl.rows.find((row) => row.id === "steric-exclusion")
  .stages.at(-1).status, "reevaluated");
assert.equal(nacl.rows.find((row) => row.id === "kinetics")
  .stages.at(-1).status, "open");

const cdyb = buildHierarchyPhysicsTransport("cdyb-transfer");
assert.ok(cdyb.rows.every((row) => row.stages.at(-1).status === "open"));
assert.equal(cdyb.hierarchy.highestProvenClaim.id, "reencoding");

assert.throws(() => buildHierarchyPhysicsTransport("missing"), /Unknown hierarchy evidence receipt/);

console.log("hierarchy physics transport model passed");

