import assert from "node:assert/strict";
import { evidenceOrderedClusterDiscoverySchedule, evidenceOrderedPlacementSchedule }
  from "../apps/iqc-growth-live/cluster-discovery-schedule.js";

const placements = [
  { placementIndex: 0, family: "support", type: 0, support: [2, 0, 1], edgeKeys: ["0:1"] },
  { placementIndex: 1, family: "support", type: 0, support: [3, 2], edgeKeys: ["2:3"] },
  { placementIndex: 2, family: "gap", type: 1, support: [4], edgeKeys: [] },
];

const ordered = evidenceOrderedPlacementSchedule(placements);
assert.deepEqual(ordered.map((placement) => placement.placementIndex), [0, 1, 2]);
assert.deepEqual(ordered.map((placement) => placement.uncoveredGain), [3, 1, 1]);
assert.deepEqual(ordered.map((placement) => placement.selectionReason),
  ["maximum-cover-gain", "maximum-cover-gain", "maximum-cover-gain"]);

const edges = [
  { key: "0:1", first: 0, second: 1, length: 1, final: true, placementIndices: new Set([0]) },
  { key: "2:3", first: 2, second: 3, length: 1.1, final: true, placementIndices: new Set([1]) },
  { key: "0:3", first: 0, second: 3, length: 1.05, final: false, placementIndices: new Set() },
];
const schedule = evidenceOrderedClusterDiscoverySchedule({ placements, edges, totalSteps: 36 });
assert.deepEqual(schedule.placements.map((placement) => placement.settleStep), [8, 19, 31]);
const byKey = Object.fromEntries(schedule.edges.map((edge) => [edge.key, edge]));
assert.equal(byKey["0:1"].decisionStep, 8);
assert.equal(byKey["2:3"].decisionStep, 19);
assert.equal(byKey["0:3"].decisionStep, 20);
assert.equal(schedule.orderingAudit.hashSchedulingUsed, false);
assert.equal(schedule.orderingAudit.physicalTimeClaimed, false);

const permuted = evidenceOrderedClusterDiscoverySchedule({
  placements: [placements[2], placements[0], placements[1]],
  edges: [edges[2], edges[1], edges[0]], totalSteps: 36,
});
assert.deepEqual(permuted.placements.map((placement) => [placement.placementIndex, placement.settleStep]),
  schedule.placements.map((placement) => [placement.placementIndex, placement.settleStep]));
assert.deepEqual(Object.fromEntries(permuted.edges.map((edge) => [edge.key, [edge.birthStep, edge.decisionStep]])),
  Object.fromEntries(schedule.edges.map((edge) => [edge.key, [edge.birthStep, edge.decisionStep]])));

console.log(JSON.stringify({ passed: true, placementOrder: ordered.map((row) => row.placementIndex),
  rejectedDecisionStep: byKey["0:3"].decisionStep, orderingAudit: schedule.orderingAudit }));
