import assert from "node:assert/strict";
import {
  exclusionForPair,
  learnColoredDistanceEnvelopes,
} from "../apps/iqc-growth-live/colored-distance-envelopes.js";

const species = ["O", "H", "H", "Na", "Cl", "Na", "Cl"];
const positions = [
  [0, 0, 0], [.96, 0, 0], [-.24, .93, 0],
  [5, 0, 0], [7.82, 0, 0], [10.64, 0, 0], [13.46, 0, 0],
];
const distance = (first, second) => Math.hypot(...positions[second].map((value, axis) => value - positions[first][axis]));
const model = learnColoredDistanceEnvelopes(species, distance);
assert.deepEqual(model.records.map((record) => record.key), ["Cl|Cl", "Cl|H", "Cl|Na", "Cl|O", "H|H", "H|Na", "H|O", "Na|Na", "Na|O"]);
model.records.forEach((record) => {
  assert.ok(record.exclusion < record.minimumObserved,
    `${record.key} exclusion must preserve every supplied contact`);
  assert.ok(record.nearestObservations > 0);
});
assert.ok(exclusionForPair(model, "H", "O") < exclusionForPair(model, "Na", "Cl"),
  "short molecular H-O contacts need a different envelope from Na-Cl contacts");
assert.equal(exclusionForPair(model, "Xe", "Xe"), .46, "unobserved chemistry must use the explicit fallback");
assert.equal(exclusionForPair(model, "O", "H"), exclusionForPair(model, "H", "O"));

const reversedSpecies = species.slice().reverse();
const reversedPositions = positions.slice().reverse();
const reversed = learnColoredDistanceEnvelopes(reversedSpecies, (first, second) =>
  Math.hypot(...reversedPositions[second].map((value, axis) => value - reversedPositions[first][axis])));
assert.deepEqual(reversed.records, model.records, "colored envelopes must be invariant to atom ordering");

console.log("train-derived colored distance envelopes: passed", Object.fromEntries(
  model.records.map((record) => [record.key, record.exclusion.toFixed(3)])));
