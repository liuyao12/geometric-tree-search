import assert from "node:assert/strict";
import {
  aggregateMarkingReadout,
  coloredConnectionChirality,
} from "../apps/iqc-growth-live/marking-representation-readout.js";

const translation = [1.1, .3, .2];
const sites = [
  { token: "Cl|1000|A", vector: [1.3, .2, .8] },
  { token: "Na|1200|B", vector: [.6, 1.1, -.4] },
  { token: "O|900|C", vector: [1.4, -.7, .5] },
];
const chirality = coloredConnectionChirality(translation, sites);
assert.ok(Math.abs(chirality) > 1e-3, "fixture must carry a nonzero colored pseudoscalar");

const angle = .73;
const rotate = ([x, y, z]) => [
  Math.cos(angle) * x - Math.sin(angle) * y,
  Math.sin(angle) * x + Math.cos(angle) * y,
  z,
];
const rotated = coloredConnectionChirality(rotate(translation),
  sites.map((site) => ({ ...site, vector: rotate(site.vector) })));
assert.ok(Math.abs(rotated - chirality) < 1e-12,
  "the colored connection pseudoscalar must be proper-rotation invariant");

const mirror = ([x, y, z]) => [-x, y, z];
const mirrored = coloredConnectionChirality(mirror(translation),
  sites.map((site) => ({ ...site, vector: mirror(site.vector) })));
assert.ok(Math.abs(mirrored + chirality) < 1e-12,
  "the colored connection pseudoscalar must change sign under reflection");
assert.ok(Math.abs(coloredConnectionChirality(translation, sites.slice().reverse()) - chirality) < 1e-12,
  "the pseudoscalar must not depend on site insertion order");

const input = { forward: .24, reverse: .17, siteValues: [.31, .08, -.04], chiralityAffinity: .65 };
const scores = Object.fromEntries(["sites", "halo", "chiral-halo", "ports", "whole"].map((representation) =>
  [representation, aggregateMarkingReadout({ representation, ...input })]));
assert.equal(new Set(Object.values(scores).map((value) => value.toFixed(12))).size, 5,
  "each marking representation must have a distinct mathematical readout");
assert.equal(aggregateMarkingReadout({ representation: "ports", ...input }),
  aggregateMarkingReadout({ representation: "ports", ...input, siteValues: [-9], chiralityAffinity: -1 }),
  "the port-vector readout must depend only on bidirectional endpoint ports");
assert.ok(aggregateMarkingReadout({ representation: "chiral-halo", ...input, chiralityAffinity: 1 })
  > aggregateMarkingReadout({ representation: "chiral-halo", ...input, chiralityAffinity: -1 }),
"the chiral halo must respond to the learned mirror-odd channel");

console.log("distinct marking representation readouts: passed", { chirality, scores });
