import assert from "node:assert/strict";
import { buildExecutedGrowthRegime, growthRegimePlotRows }
  from "../apps/iqc-growth-live/growth-regime-map.mjs";

const state = (atoms, exposure, order, peak, anisotropy, interfaces, nuclei = 1) => ({
  atoms,
  morphology: { coordinationDeficit: exposure, relativeShapeAnisotropy: anisotropy,
    phenotype: anisotropy > .4 ? "needle-like" : "compact",
    lineageEnsemble: { sharedInterfaceFraction: interfaces, effectiveNucleusCount: nuclei } },
  packing: { underpackedFraction: exposure / 2 },
  orientationalOrder: { harmonics: { 6: { mean: order } } },
  scattering: { summary: { peakProminence: peak } },
});

const audit = buildExecutedGrowthRegime([
  { index: 1, status: "accepted", label: "batch A", targetUsed: false,
    before: state(100, .30, .4, 1.2, .2, 0), after: { ...state(112, .2, .5, 1.4, .3, .1), accepted: 3, rejected: 1, depth: 2 } },
  { index: 2, status: "fixed", before: state(112, .2, .5, 1.4, .3, .1),
    after: state(112, .2, .5, 1.4, .3, .1) },
  { index: 3, status: "accepted", targetUsed: true, before: state(112, .2, .5, 1.4, .3, .1),
    after: state(120, .1, .6, 1.5, .4, .2) },
]);

assert.equal(audit.executedLeaps, 1);
assert.equal(audit.excludedLeaps, 2);
assert.equal(audit.records[0].emittedAtoms, 12);
assert.ok(Math.abs(audit.records[0].response.coordinationDeficitDelta + .1) < 1e-12);
assert.ok(Math.abs(audit.records[0].response.localOrder6Delta - .1) < 1e-12);
assert.ok(Math.abs(audit.records[0].response.sharedInterfaceFractionDelta - .1) < 1e-12);
assert.equal(audit.coordinatesEmbedded, false);
assert.equal(audit.targetUsed, false);
assert.equal(audit.usedForRanking, false);
assert.equal(audit.phaseDiagramInferred, false);
assert.deepEqual(growthRegimePlotRows(audit, "coordinationDeficit", "emittedAtoms")
  .map(({ leapIndex, x, y }) => ({ leapIndex, x, y })), [{ leapIndex: 1, x: .3, y: 12 }]);

console.log("growth-regime-map contract: pass");
