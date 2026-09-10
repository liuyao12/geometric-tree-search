import assert from "node:assert/strict";
import { compareStructure } from "./metrics.mjs";
import { samplePatch } from "./samples.mjs";
import { centralSeed } from "./seed.mjs";
import { axisAngle, transform } from "./geometry.mjs";
const centered = (id) => {
  const a = samplePatch(id).atoms,
    o = centralSeed(a).origin;
  return a.map((a) => ({ ...a, position: a.position.map((v, k) => v - o[k]) }));
};
const ref = centered("nacl"),
  same = compareStructure(ref, ref);
assert.equal(same.status, "measured");
assert.equal(same.rdfError, 0);
assert.equal(same.angleTV, 0);
const rotate = (a) =>
  a.map((a) => ({
    ...a,
    position: transform(
      { r: axisAngle([1, 2, 3], 0.738), t: [0, 0, 0] },
      a.position,
    ),
  }));
const r = compareStructure(rotate(ref), rotate(ref));
assert.ok(Math.abs(r.reference.density - same.reference.density) < 1e-9);
assert.ok(
  r.reference.rdf.every((v, i) => Math.abs(v - same.reference.rdf[i]) < 1e-8),
);
const missing = compareStructure(
  ref,
  ref.filter((a) => a.species === "Na"),
);
assert.ok(missing.compositionTV > 0.4);
assert.ok(Object.values(missing.partialErrors).some((v) => v === null));
assert.ok(
  compareStructure(
    ref,
    ref.map((a) => ({ ...a, position: a.position.map((v) => v * 1.15) })),
  ).rdfError > 0.1,
);
const planar = centered("bn");
assert.ok(compareStructure(planar, rotate(planar)).rdfError < 1e-8);
assert.equal(compareStructure(planar, planar).dimension, 2);
assert.match(
  compareStructure(
    planar,
    planar.map((a, i) => ({
      ...a,
      position: [a.position[0], a.position[1], i % 2],
    })),
  ).status,
  /dimension mismatch/,
);
assert.equal(compareStructure(ref, [ref[0]]).rdfError, null);
assert.equal(
  compareStructure(ref, [
    ...ref,
    ...Array.from({ length: 1600 }, (_, i) => ({
      species: "Na",
      position: [1000 + i, 1000, 1000],
    })),
  ]).rdfError,
  0,
);
// Uniform ball control: finite-window translation correction has mean g≈1.
let seed = 12345;
const random = () => {
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
    return seed / 2 ** 32;
  },
  ball = [];
while (ball.length < 600) {
  const position = [0, 0, 0].map(() => 2 * random() - 1);
  if (Math.hypot(...position) < 1) ball.push({ species: "opaque", position });
}
const rdf = compareStructure(ball, ball).reference.rdf.slice(10),
  mean = rdf.reduce((a, b) => a + b, 0) / rdf.length;
assert.ok(mean > 0.85 && mean < 1.15, mean);
console.log(
  "RDF controls PASS: identity, rotation, missing species, wrong scale, 2D/3D, insufficient data, uniform ball normalization",
  mean,
);
