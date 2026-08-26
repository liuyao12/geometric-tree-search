import assert from "node:assert/strict";
import { analyzeCollinearSpinGeometry, COLLINEAR_SPIN_PROVENANCE }
  from "../apps/iqc-growth-live/collinear-spin-geometry.js";

const ferro = [0, 1, 2, 3].map((x) => ({ species: "Fe", position: [x, 0, 0], spin: 2 }));
const anti = [0, 1, 2, 3].map((x) => ({ species: "Fe", position: [x, 0, 0], spin: x % 2 ? -2 : 2 }));
const ferroAudit = analyzeCollinearSpinGeometry(ferro, { maximumReach: 1.1, binCount: 4 });
const antiAudit = analyzeCollinearSpinGeometry(anti, { maximumReach: 1.1, binCount: 4 });
assert.equal(ferroAudit.available, true);
assert.equal(ferroAudit.weightedPairCorrelation, 1);
assert.equal(ferroAudit.netPolarization, 1);
assert.equal(antiAudit.weightedPairCorrelation, -1);
assert.equal(antiAudit.netPolarization, 0);
assert.equal(antiAudit.checkedPairs, 3);

const transformed = anti.slice().reverse().map((site) => ({ ...site,
  position: [-site.position[1] + 7, site.position[0] - 4, site.position[2] + 2],
  spin: -site.spin,
}));
const transformedAudit = analyzeCollinearSpinGeometry(transformed, { maximumReach: 1.1, binCount: 4 });
assert.equal(transformedAudit.weightedPairCorrelation, antiAudit.weightedPairCorrelation);
assert.deepEqual(transformedAudit.radialCorrelation.map((bin) => bin.correlation),
  antiAudit.radialCorrelation.map((bin) => bin.correlation));
assert.ok(Math.abs(transformedAudit.netPolarization + antiAudit.netPolarization) < 1e-12);
assert.equal(transformedAudit.translationInvariant, true);
assert.equal(transformedAudit.properRotationInvariant, true);
assert.equal(transformedAudit.permutationInvariant, true);
assert.equal(transformedAudit.vectorAxisInferred, false);
assert.equal(transformedAudit.exchangeEnergyInferred, false);
assert.equal(COLLINEAR_SPIN_PROVENANCE.unitGuaranteedBySchema, false);

const missing = analyzeCollinearSpinGeometry([{ species: "Fe", position: [0, 0, 0] }]);
assert.equal(missing.available, false);
assert.equal(missing.coverage, 0);

console.log("collinear spin geometry: invariant scalar-correlation checks passed");
