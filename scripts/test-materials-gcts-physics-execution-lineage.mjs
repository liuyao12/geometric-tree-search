import assert from "node:assert/strict";

import {
  buildPhysicsEffectMatrix,
  buildPhysicsInvestigationProtocol,
  PHYSICS_ABLATION_CONTROL_BINDINGS,
  physicsExecutionLineage,
} from "../apps/iqc-growth-live/physics-compression-map.js";

const activeRecords = [
  {
    id: "collinear-spin",
    process: "scalar spin overlap color",
    status: "hard",
    role: "transported exact overlap color",
    encoding: "signed scalar labels",
    evidence: "one overlap rejected",
    boundary: "not a spin Hamiltonian",
    controlRouteAvailable: true,
  },
  {
    id: "long-range",
    process: "collective graph response",
    status: "soft",
    role: "screened accepted-history graph field",
    encoding: "screened graph mark",
    evidence: "candidate score audited",
    boundary: "not long-range elasticity",
    controlRouteAvailable: true,
  },
  {
    id: "configurational-entropy",
    process: "continuation multiplicity",
    status: "soft",
    role: "fit-only frozen-grammar look-ahead",
    encoding: "effective outgoing-rule count",
    evidence: "candidate score audited",
    boundary: "not thermodynamic entropy",
    controlRouteAvailable: true,
  },
  {
    id: "constraint-rigidity",
    process: "constraint dimensionality",
    status: "soft",
    role: "unit-contact direction-tensor ordering",
    encoding: "normalized contact tensor",
    evidence: "candidate score audited",
    boundary: "not a Hessian",
    controlRouteAvailable: true,
  },
];

const spin = physicsExecutionLineage(activeRecords[0]);
assert.equal(spin.hardAdmissionCanChange, true);
assert.equal(spin.diagnosticOnly, false);
assert.deepEqual(spin.effects, ["hard admission"]);
assert.deepEqual(spin.executionObjects, ["candidate acceptance / rejection"]);

for (const record of activeRecords.slice(1)) {
  const lineage = physicsExecutionLineage(record);
  assert.equal(lineage.rankingCanChange, true, `${record.id} must expose its live rank hook`);
  assert.equal(lineage.diagnosticOnly, false);
  assert.deepEqual(lineage.effects, ["soft branch ranking"]);
  assert.deepEqual(lineage.executionObjects, ["signed candidate score and branch rank"]);
  assert.equal(PHYSICS_ABLATION_CONTROL_BINDINGS[record.id].ablationValue, "none");
}

const matrix = buildPhysicsEffectMatrix(activeRecords);
assert.equal(matrix.counts.hardAdmission, 1);
assert.equal(matrix.counts.ranking, 3);
assert.equal(matrix.counts.diagnostic, 0);
assert.equal(matrix.readinessCounts.executing, 4);

const protocol = buildPhysicsInvestigationProtocol(
  activeRecords,
  activeRecords.map((record) => record.id),
);
assert.equal(protocol.selectedRecordCount, 4);
assert.equal(protocol.effectCoverage.hardAdmission.count, 1);
assert.equal(protocol.effectCoverage.ranking.count, 3);
assert.deepEqual(protocol.blockingRecordIds, []);

const inactiveRank = physicsExecutionLineage({ ...activeRecords[1], status: "open", role: "diagnostic" });
assert.equal(inactiveRank.rankingCanChange, false);
assert.equal(inactiveRank.diagnosticOnly, true);

console.log("physics execution lineage contract passed");
