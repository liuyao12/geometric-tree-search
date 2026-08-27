import assert from "node:assert/strict";
import {
  buildClusterMarkingPortAtlas,
  clusterMarkingPortSummary,
} from "../apps/iqc-growth-live/cluster-marking-port-atlas.js";

const scalar = buildClusterMarkingPortAtlas({
  prototypeCount: 2,
  activeChannelsByPrototype: [1, 1],
  channelAxes: [[0, 0, 0]],
  observations: [
    { prototype: 0, direction: [1, 0, 0], shared: 2, observations: 3 },
    { prototype: 0, direction: [.999, .02, 0], shared: 4, observations: 1 },
  ],
});
assert.equal(scalar.physicalPotential, false);
assert.equal(scalar.candidateGeometryChanged, false);
assert.equal(scalar.prototypes[0].compatiblePorts.length, 1);
assert.equal(scalar.prototypes[0].compatiblePorts[0].observations, 4);
assert.equal(scalar.prototypes[0].compatiblePorts[0].sharedMean, 2.5);
assert.equal(scalar.prototypes[0].scalarDirectional, true);
assert.equal(scalar.prototypes[0].sphericalFallbackUsed, false);
assert.equal(scalar.prototypes[1].hasDirectionalEvidence, false);
assert.equal(scalar.prototypes[1].sphericalFallbackUsed, false);

const directional = buildClusterMarkingPortAtlas({
  prototypeCount: 1,
  activeChannelsByPrototype: [3],
  channelAxes: [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
  observations: [
    { prototype: 0, direction: [.98, .1, 0], shared: 2 },
    { prototype: 0, direction: [0, 1, 0], shared: 3 },
  ],
});
assert.deepEqual(directional.prototypes[0].compatiblePorts.map((port) => port.channel), [0, 1]);
assert.deepEqual(directional.prototypes[0].unsupportedSectors.map((sector) => sector.channel), [2]);
assert.deepEqual(clusterMarkingPortSummary(directional, 0), {
  compatiblePorts: 2,
  compatibleObservations: 2,
  unsupportedSectors: 1,
  rawDirectionalModes: 2,
  maximumModesPerChannel: 2,
  scalarDirectional: false,
  sphericalFallbackUsed: false,
  invalidObservations: 0,
});

const rotated = buildClusterMarkingPortAtlas({
  prototypeCount: 1,
  activeChannelsByPrototype: [3],
  channelAxes: [[0, 1, 0], [-1, 0, 0], [0, 0, 1]],
  observations: [
    { prototype: 0, direction: [-.1, .98, 0], shared: 2 },
    { prototype: 0, direction: [-1, 0, 0], shared: 3 },
  ],
});
assert.deepEqual(rotated.prototypes[0].compatiblePorts.map((port) => port.channel), [0, 1]);
assert.equal(rotated.prototypes[0].unsupportedSectors.length, 1);

console.log("cluster marking port atlas tests passed");
