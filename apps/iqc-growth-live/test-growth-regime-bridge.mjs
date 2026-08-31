import assert from "node:assert/strict";
import { periodicSiteNumberDensity, coupleInterfaceSupplyAndAttachment,
  syntheticGrowthRegimePreview } from "./growth-regime-bridge.mjs";

const sha = "a".repeat(64);
const density = periodicSiteNumberDensity({ cellVolumeCubicAngstrom: 100,
  siteOccupancies: [1, 1, .5, .5] });
assert.equal(density.occupiedSites, 3);
assert.ok(Math.abs(density.siteNumberDensityAtomsPerCubicMetre / 3e28 - 1) < 1e-12);
assert.equal(density.atomicVolumeCubicAngstromPerOccupiedSite, 100 / 3);
assert.equal(density.massDensityInferred, false);

const orientations = [
  { orientationId: "+x", normal: [1, 0, 0], normalGrowthVelocity: 2e-9, uncertainty: 1e-11 },
  { orientationId: "-x", normal: [-1, 0, 0], normalGrowthVelocity: 2e-10, uncertainty: 1e-12 },
  { orientationId: "+y", normal: [0, 1, 0], normalGrowthVelocity: 1e-9, uncertainty: 1e-11 },
  { orientationId: "-y", normal: [0, -1, 0], normalGrowthVelocity: 1e-9, uncertainty: 1e-11 },
  { orientationId: "+z", normal: [0, 0, 1], normalGrowthVelocity: 1e-9, uncertainty: 1e-11 },
  { orientationId: "-z", normal: [0, 0, -1], normalGrowthVelocity: 1e-9, uncertainty: 1e-11 },
];
const patches = orientations.map((entry, index) => ({ patchId: `p${index + 1}`,
  outwardNormalCartesian: entry.normal, netIncorporationFlux: index === 0 ? 3e18 : 3e20,
  uncertainty: index === 0 ? 1e16 : 1e18 }));
const result = coupleInterfaceSupplyAndAttachment({ patches, orientations,
  orientationBasisCartesian: [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
  siteNumberDensityAtomsPerCubicMetre: density.siteNumberDensityAtomsPerCubicMetre,
  fluxCouplingStateSha256: sha, kineticsCouplingStateSha256: sha, maximumAngleRadians: .2 });
assert.equal(result.supportedPatchCount, 6);
assert.equal(result.records[0].regime, "supply-limited");
assert.equal(result.records[1].regime, "attachment-limited");
assert.equal(result.effectiveGrowthVelocityInferred, false);
assert.equal(result.targetUsed, false);
assert.throws(() => coupleInterfaceSupplyAndAttachment({ patches, orientations,
  orientationBasisCartesian: [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
  siteNumberDensityAtomsPerCubicMetre: density.siteNumberDensityAtomsPerCubicMetre,
  fluxCouplingStateSha256: sha, kineticsCouplingStateSha256: "b".repeat(64) }), /different driving states/);
assert.equal(syntheticGrowthRegimePreview("mixed").records.length, 14);
console.log("growth-regime bridge tests passed");
