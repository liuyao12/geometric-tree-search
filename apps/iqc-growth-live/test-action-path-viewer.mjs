import assert from "node:assert/strict";
import { buildActionPathViewerFrame, projectActionPathViewerFrame }
  from "./action-path-viewer.mjs";

const path = { saddleImageIndex: 1,
  fixedMaterialSites: Array.from({ length: 5 }, (_, index) => ({
    pathSiteId: `fixed-${index}`, species: index % 2 ? "Cl" : "Na",
    positionAngstrom: [index - 2, 0, 0] })),
  images: [0, .5, 1].map((reactionCoordinate, index) => ({ reactionCoordinate,
    energyElectronVolt: [0, .7, -.1][index],
    maximumForceElectronVoltPerAngstrom: [.02, .05, .01][index],
    sites: [{ pathSiteId: "moving-Na", species: "Na", domain:
      index === 0 ? "reservoir" : index === 1 ? "interface" : "material",
    positionAngstrom: [0, index - 1, .5 * index] }] })) };

const frame = buildActionPathViewerFrame(path, 1, { maximumFixedSites: 3 });
const firstFrame = buildActionPathViewerFrame(path, 0, { maximumFixedSites: 3 });
const lastFrame = buildActionPathViewerFrame(path, 2, { maximumFixedSites: 3 });
assert.equal(frame.saddle, true);
assert.equal(frame.displayedFixedMaterialSiteCount, 3);
assert.equal(frame.fixedMaterialSiteCount, 5);
assert.equal(frame.movingOrReservoirSiteCount, 1);
assert.equal(frame.interfaceSiteCount, 1);
assert.equal(frame.relativeEnergyElectronVolt, .7);
assert.equal(frame.sites.length, 4);
assert.equal(frame.trails[0].positions.length, 3);
assert.equal(frame.interpolationUsed, false);
assert.deepEqual(firstFrame.sites.filter((site) => site.fixed).map((site) => site.pathSiteId),
  lastFrame.sites.filter((site) => site.fixed).map((site) => site.pathSiteId));

const projected = projectActionPathViewerFrame(frame, { width: 360, height: 190,
  yaw: .4, pitch: -.2 });
assert.equal(projected.projectedSites.length, 4);
assert.equal(projected.projectedTrails[0].points.length, 3);
assert.ok(projected.projectedSites.every((site) => Number.isFinite(site.x)
  && Number.isFinite(site.y) && Number.isFinite(site.depth)));
assert.equal(projected.projectionKind, "proper-rotation-perspective");
assert.equal(projected.interpolationUsed, false);
assert.deepEqual(frame.sites.map((site) => site.positionAngstrom),
  projected.sites.map((site) => site.positionAngstrom));

assert.throws(() => buildActionPathViewerFrame(path, 3), /outside/);
assert.throws(() => projectActionPathViewerFrame(frame, { width: 0, height: 10 }), /positive/);

console.log("coordinate-bearing action-path viewer tests passed");
