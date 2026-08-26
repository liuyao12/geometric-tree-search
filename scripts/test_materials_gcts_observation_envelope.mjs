import assert from "node:assert/strict";
import {
  classifyObservationSites,
  fitObservationEnvelope,
  observationEnvelopeSignedMargin,
} from "../apps/iqc-growth-live/observation-envelope.js";

const box = fitObservationEnvelope([
  [-1, -1, -1], [1, 1, 1], [-1, 1, -1], [1, -1, 1],
], { shape: "box", padding: .5, source: "finite periodic cell" });
assert.deepEqual(box.halfExtents, [1.5, 1.5, 1.5]);
assert(Math.abs(observationEnvelopeSignedMargin(box, [1.4, 0, 0]) - .1) < 1e-12);
assert(Math.abs(observationEnvelopeSignedMargin(box, [1.8, 0, 0]) + .3) < 1e-12);

const sphere = fitObservationEnvelope([[0, 0, 0], [2, 0, 0]], {
  shape: "sphere", center: [0, 0, 0], radius: 3,
});
assert.equal(sphere.source, "declared spherical crop");
assert(Math.abs(observationEnvelopeSignedMargin(sphere, [0, 0, 2.5]) - .5) < 1e-12);

const slab = fitObservationEnvelope([[-2, 0, -.1], [2, 0, .1], [0, 2, 0]], {
  shape: "slab", padding: .2,
});
assert(observationEnvelopeSignedMargin(slab, [0, 0, .25]) > 0);
assert(observationEnvelopeSignedMargin(slab, [0, 0, .4]) < 0);

const audit = classifyObservationSites([
  { known: true, position: [0, 0, 0] },
  { known: false, position: [1.4, 0, 0] },
  { known: false, position: [1.8, 0, 0] },
], box, 1e-9);
assert.deepEqual({ known: audit.known, novel: audit.novel, novelInside: audit.novelInside, beyond: audit.beyond },
  { known: 1, novel: 2, novelInside: 1, beyond: 1 });
assert(Math.abs(audit.maximumExcursion - .3) < 1e-12);

console.log("observation-envelope site classification: passed");
