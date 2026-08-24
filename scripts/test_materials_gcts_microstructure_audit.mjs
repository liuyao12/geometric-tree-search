import assert from "node:assert/strict";
import { auditGeometricMicrostructure } from "../apps/iqc-growth-live/microstructure-audit.js";

const report = auditGeometricMicrostructure({
  atoms: [
    { chemistryToken: "A", coordination: 4 },
    { chemistryToken: "A", coordination: 4 },
    { chemistryToken: "A", coordination: 4 },
    { chemistryToken: "A", coordination: 0 },
    { chemistryToken: "occ[A=0.5;B=0.5]", coordination: 3 },
    { chemistryToken: "occ[A=0.5;Vac=0.5]", coordination: 1 },
  ],
  types: [
    { id: 0, residual: false, gap: false },
    { id: 1, residual: true, gap: false },
    { id: 2, residual: false, gap: true },
  ],
  placements: [
    { type: 0, support: [0, 1], centerPosition: [0, 0, 0], pose: 0 },
    { type: 0, support: [1, 2], centerPosition: [1, 0, 0], pose: 0 },
    { type: 0, support: [2, 3], centerPosition: [1.5, 0, 0], pose: 1 },
    { type: 1, support: [5], centerPosition: [3, 0, 0], pose: null },
    { type: 2, support: [3, 4], centerPosition: [2, 0, 0], pose: null },
  ],
  adjacencyReach: 1.6,
});

assert.equal(report.recurringTypes, 1);
assert.equal(report.gapBoundaryTypes, 1);
assert.equal(report.terminalTypes, 1);
assert.equal(report.recurringCoveredAtoms, 4);
assert.equal(report.gapBoundaryAtoms, 2);
assert.equal(report.terminalCoveredAtoms, 1);
assert.equal(report.literalOnlyAtoms, 1);
assert.equal(report.coordinationAnomalyAtoms, 1);
assert.equal(report.occupationalAlternativeSites, 2);
assert.equal(report.explicitVacancySites, 1);
assert.equal(report.posedOccurrences, 3);
assert.equal(report.poseDomainComponents, 2);
assert.equal(report.samePoseContacts, 1);
assert.equal(report.crossPoseContacts, 2);
assert.equal(report.grainBoundaryClaimed, false);
assert.equal(report.defectFormationEnergyModeled, false);
assert.equal(report.literalTerminalsPromoted, false);
assert.equal(report.gapBoundaryClassesEmitAtoms, false);
assert.equal(report.gapBoundaryClassesReusableAsConstraints, true);
assert.match(report.interpretation, /local pose domains/);

assert.throws(() => auditGeometricMicrostructure({ atoms: [], placements: [], types: [], adjacencyReach: 0 }), /positive and finite/);
assert.throws(() => auditGeometricMicrostructure({
  atoms: [{ chemistryToken: "A", coordination: 1 }],
  placements: [{ type: 2, support: [0], centerPosition: [0, 0, 0] }],
  types: [], adjacencyReach: 1,
}), /invalid type/);

console.log("geometric microstructure audit: passed");
