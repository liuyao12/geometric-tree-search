import assert from "node:assert/strict";
import { buildPhysicsCompressionMap } from "../apps/iqc-growth-live/physics-compression-map.js";

const records = [
  { id: "steric", status: "hard" }, { id: "connection", status: "learned" },
  { id: "front-morphology", status: "soft" }, { id: "kinetics", status: "open" },
  { id: "long-range", status: "open" },
];
const map = buildPhysicsCompressionMap(records);
assert.equal(map.recordCount, 5);
assert.equal(map.complete, true);
assert.equal(map.unclassifiedRecordIds.length, 0);
assert.equal(map.lanes.find((lane) => lane.id === "local").state, "structural");
assert.equal(map.lanes.find((lane) => lane.id === "interface").state, "declared");
assert.equal(map.lanes.find((lane) => lane.id === "open").state, "open");
assert.equal(map.structuralStatesAreNotPhysicalTime, true);
assert.equal(map.hypothesesAreNotLearnedPhysics, true);
assert.equal(map.targetUsed, false);
const incomplete = buildPhysicsCompressionMap([...records, { id: "new-process", status: "soft" }]);
assert.equal(incomplete.complete, false);
assert.deepEqual(incomplete.unclassifiedRecordIds, ["new-process"]);
assert.equal(incomplete.lanes.at(-1).id, "unclassified");
assert.throws(() => buildPhysicsCompressionMap([{ id: "same", status: "hard" }, { id: "same", status: "open" }]));
console.log("materials physics compression map: passed");
