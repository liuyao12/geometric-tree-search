import assert from "node:assert/strict";
import {
  generateAmorphousMixture,
  periodicPairRdf,
} from "../apps/iqc-growth-live/amorphous-glass.js";

const first = generateAmorphousMixture();
const second = generateAmorphousMixture();
assert.deepEqual(first, second, "the negative-control fixture must be deterministic");
assert.equal(first.positions.length, 216);
assert.deepEqual(first.audit.composition, { Cu: 138, Zr: 78 });
assert.ok(Math.abs(first.audit.medianNearestAngstrom - 2.72) < 1e-10);
assert.ok(first.audit.minimumNearestAngstrom > 2.45, "hard-core relaxation must reject close contacts");
assert.equal(first.audit.targetRdfUsed, false);
assert.equal(first.audit.latticeSitesUsed, false);

const rdf = periodicPairRdf(first.positions, first.species, first.cellLengthAngstrom,
  48, first.cellLengthAngstrom * .46);
assert.deepEqual(Object.keys(rdf.byPair).sort(), ["Cu|Cu", "Cu|Zr", "Zr|Zr"]);
const tail = rdf.all.slice(30);
const tailMean = tail.reduce((sum, value) => sum + value, 0) / tail.length;
const tailRms = Math.sqrt(tail.reduce((sum, value) => sum + (value - 1) ** 2, 0) / tail.length);
assert.ok(Math.abs(tailMean - 1) < .08, `amorphous long-range RDF should approach one, got ${tailMean}`);
assert.ok(tailRms < .12, `amorphous tail should lose long-range shells, got RMS ${tailRms}`);
assert.ok(Math.max(...rdf.all.slice(0, 22)) > 2, "short-range packing peak must remain visible");

console.log("deterministic amorphous Cu-Zr packing: passed", {
  composition: first.audit.composition,
  minimumNearestAngstrom: first.audit.minimumNearestAngstrom.toFixed(3),
  tailMean: tailMean.toFixed(3),
  tailRms: tailRms.toFixed(3),
});
