import assert from "node:assert/strict";
import { buildPhysicsCompressionMap, buildPhysicsEffectMatrix, buildPhysicsLineagePath,
  PHYSICS_EFFECT_COLUMNS, physicsExecutionLineage }
  from "../apps/iqc-growth-live/physics-compression-map.js";

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
assert.equal(map.executionEffectsComplete, true);
assert.equal(map.effectCounts.hardAdmission, 2);
assert.equal(map.effectCounts.ranking, 2);
assert.equal(map.targetUsed, false);
const incomplete = buildPhysicsCompressionMap([...records, { id: "new-process", status: "soft" }]);
assert.equal(incomplete.complete, false);
assert.deepEqual(incomplete.unclassifiedRecordIds, ["new-process"]);
assert.equal(incomplete.lanes.at(-1).id, "unclassified");
assert.throws(() => buildPhysicsCompressionMap([{ id: "same", status: "hard" }, { id: "same", status: "open" }]));

const connection = physicsExecutionLineage({ id: "connection", status: "learned",
  process: "cluster attachment", role: "learned local connection gate / rank" });
assert.equal(connection.hardAdmissionCanChange, true);
assert.equal(connection.rankingCanChange, true);
assert.equal(connection.candidateGeometryCanChange, false);
assert.equal(connection.targetUsed, false);

const responseInactive = physicsExecutionLineage({ id: "stress-strain-response", status: "learned",
  process: "apparent response", role: "eligible but not selected" });
assert.equal(responseInactive.diagnosticOnly, true);
const responseActive = physicsExecutionLineage({ id: "stress-strain-response", status: "soft",
  process: "apparent response", role: "bounded target-blind deformed-metric ordering" });
assert.equal(responseActive.rankingCanChange, true);

const refinement = physicsExecutionLineage({ id: "constraint-projection", status: "sampled",
  process: "local projection", role: "fail-closed projection attempt" });
assert.equal(refinement.candidateGeometryCanChange, true);
assert.equal(refinement.hardAdmissionCanChange, false);

const lineage = buildPhysicsLineagePath({ id: "steric", status: "hard",
  process: "short-range contact", role: "hard admission gate", encoding: "colored exclusion",
  evidence: "three contacts checked", boundary: "not a pair potential" });
assert.deepEqual(lineage.nodes.map((node) => node.id),
  ["evidence", "encoding", "execution", "response", "boundary"]);
assert.equal(lineage.execution.summary, "hard admission");
assert.equal(lineage.coordinatesEmbedded, false);

const matrix = buildPhysicsEffectMatrix(records);
assert.equal(matrix.recordCount, records.length);
assert.deepEqual(matrix.columns.map((column) => column.id),
  ["hardAdmission", "candidateGeometry", "initialState", "ranking", "searchOrder", "diagnostic"]);
assert.deepEqual(PHYSICS_EFFECT_COLUMNS.map((column) => column.label),
  ["admission", "geometry", "seed", "ranking", "order", "no hook"]);
assert.equal(matrix.rows.find((row) => row.recordId === "steric").effects.hardAdmission, true);
assert.equal(matrix.rows.find((row) => row.recordId === "front-morphology").effects.ranking, true);
assert.equal(matrix.rows.find((row) => row.recordId === "kinetics").effects.diagnostic, true);
assert.equal(matrix.rows.find((row) => row.recordId === "long-range").laneId, "open");
assert.equal(matrix.counts.hardAdmission, 2);
assert.equal(matrix.counts.ranking, 2);
assert.equal(matrix.counts.diagnostic, 2);
assert.equal(matrix.everyRecordClassified, true);
assert.equal(matrix.candidateSetInspected, false);
assert.equal(matrix.targetUsed, false);
console.log("materials physics compression map: passed");
