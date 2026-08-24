import assert from "node:assert/strict";
import {
  angleAllowed,
  angularEnvelopeFor,
  coloredAngularViolations,
  coloredGeometricStrain,
  coordinationEnvelopeFor,
  exclusionForPair,
  learnColoredAngularEnvelopes,
  learnColoredCoordinationEnvelopes,
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
const coordination = learnColoredCoordinationEnvelopes(species, distance, model);
assert.equal(coordinationEnvelopeFor(coordination, "O", "H").maximumObserved, 2,
  "water oxygen must learn capacity for its two covalent H neighbors");
assert.equal(coordinationEnvelopeFor(coordination, "H", "O").maximumObserved, 1,
  "each water hydrogen must learn one covalent O neighbor");
assert.ok(coordinationEnvelopeFor(coordination, "O", "H").contactCutoff
  > model.byKey["H|O"].minimumObserved);
const displacement = (first, second) => positions[second].map((value, axis) => value - positions[first][axis]);
const angular = learnColoredAngularEnvelopes(species, displacement, coordination);
const waterAngle = angularEnvelopeFor(angular, "O", "H", "H");
assert.equal(waterAngle.bands.length, 1);
assert.ok(angleAllowed(waterAngle, 104.47), "observed bent H-O-H geometry must remain admissible");
assert.equal(angleAllowed(waterAngle, 180), false, "a linearized water molecule must be rejected");

const reversedSpecies = species.slice().reverse();
const reversedPositions = positions.slice().reverse();
const reversed = learnColoredDistanceEnvelopes(reversedSpecies, (first, second) =>
  Math.hypot(...reversedPositions[second].map((value, axis) => value - reversedPositions[first][axis])));
assert.deepEqual(reversed.records, model.records, "colored envelopes must be invariant to atom ordering");
const reversedCoordination = learnColoredCoordinationEnvelopes(reversedSpecies, (first, second) =>
  Math.hypot(...reversedPositions[second].map((value, axis) => value - reversedPositions[first][axis])), reversed);
assert.deepEqual(reversedCoordination.records, coordination.records,
  "ordered coordination capacities must be invariant to atom ordering");
const reversedAngular = learnColoredAngularEnvelopes(reversedSpecies, (first, second) =>
  reversedPositions[second].map((value, axis) => value - reversedPositions[first][axis]), reversedCoordination);
assert.deepEqual(reversedAngular.records, angular.records,
  "colored angular envelopes must be invariant to atom ordering");

const octahedralSpecies = ["Na", "Cl", "Cl", "Cl", "Cl", "Cl", "Cl"];
const octahedralPositions = [[0, 0, 0], [1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]];
const octahedralDisplacement = (first, second) => octahedralPositions[second]
  .map((value, axis) => value - octahedralPositions[first][axis]);
const octahedralDistance = (first, second) => Math.hypot(...octahedralDisplacement(first, second));
const octahedralPairs = learnColoredDistanceEnvelopes(octahedralSpecies, octahedralDistance);
const octahedralCoordination = learnColoredCoordinationEnvelopes(octahedralSpecies, octahedralDistance, octahedralPairs);
const octahedralAngles = learnColoredAngularEnvelopes(octahedralSpecies, octahedralDisplacement, octahedralCoordination);
const clNaCl = angularEnvelopeFor(octahedralAngles, "Na", "Cl", "Cl");
assert.equal(clNaCl.bands.length, 2, "octahedral 90 and 180 degree modes must remain separated");
assert.ok(angleAllowed(clNaCl, 90));
assert.ok(angleAllowed(clNaCl, 180));
assert.equal(angleAllowed(clNaCl, 135), false, "the empty interval between octahedral modes must remain inadmissible");
assert.equal(coloredAngularViolations(octahedralSpecies, octahedralDisplacement,
  octahedralCoordination, octahedralAngles, [0]).length, 0,
"the supplied octahedron must pass its learned angular constraints");
const distortedPositions = octahedralPositions.map((point) => point.slice());
distortedPositions[6] = [Math.SQRT1_2, Math.SQRT1_2, 0];
const distortedViolations = coloredAngularViolations(octahedralSpecies, (first, second) =>
  distortedPositions[second].map((value, axis) => value - distortedPositions[first][axis]),
octahedralCoordination, octahedralAngles, [0]);
assert.ok(distortedViolations.length > 0, "a 45/135 degree distorted octahedral contact must be rejected");
const exactStrain = coloredGeometricStrain(octahedralSpecies, octahedralDisplacement,
  octahedralPairs, octahedralCoordination, octahedralAngles, [0]);
const distortedStrain = coloredGeometricStrain(octahedralSpecies, (first, second) =>
  distortedPositions[second].map((value, axis) => value - distortedPositions[first][axis]),
octahedralPairs, octahedralCoordination, octahedralAngles, [0]);
assert.ok(distortedStrain.total > exactStrain.total,
  "the soft geometric ranking must prefer the supplied octahedron to its distorted alternative");
assert.equal(exactStrain.contactTerms, 6);
assert.equal(exactStrain.angleTerms, 15);
const rotatedOctahedron = octahedralPositions.map(([x, y, z]) => [-y, x, z]);
const rotatedStrain = coloredGeometricStrain(octahedralSpecies, (first, second) =>
  rotatedOctahedron[second].map((value, axis) => value - rotatedOctahedron[first][axis]),
octahedralPairs, octahedralCoordination, octahedralAngles, [0]);
assert.ok(Math.abs(rotatedStrain.total - exactStrain.total) < 1e-12,
  "geometric strain must be invariant to a proper global rotation");
const extendedSpecies = [...octahedralSpecies, "Na", "Cl"];
const extendedPositions = [...octahedralPositions, [100, 100, 100], [101, 100, 100]];
const extendedDisplacement = (first, second) => extendedPositions[second]
  .map((value, axis) => value - extendedPositions[first][axis]);
const finiteReachStrain = coloredGeometricStrain(extendedSpecies, extendedDisplacement,
  octahedralPairs, octahedralCoordination, octahedralAngles, [0]);
assert.deepEqual(finiteReachStrain, exactStrain,
  "atoms outside every learned contact reach must not change a local strain evaluation");
assert.equal(coloredAngularViolations(extendedSpecies, extendedDisplacement,
  octahedralCoordination, octahedralAngles, [0]).length, 0,
"far atoms must not enter the selected center's angular neighborhood");

const planarSpecies = ["B", "N", "N", "N"];
const planarPositions = [[0, 0, 0], [1, 0, 0], [-.5, Math.sqrt(3) / 2, 0], [-.5, -Math.sqrt(3) / 2, 0]];
const planarDisplacement = (first, second) => planarPositions[second]
  .map((value, axis) => value - planarPositions[first][axis]);
const planarDistance = (first, second) => Math.hypot(...planarDisplacement(first, second));
const planarPairs = learnColoredDistanceEnvelopes(planarSpecies, planarDistance);
const planarCoordination = learnColoredCoordinationEnvelopes(planarSpecies, planarDistance, planarPairs);
const planarAngles = learnColoredAngularEnvelopes(planarSpecies, planarDisplacement, planarCoordination);
const nBn = angularEnvelopeFor(planarAngles, "B", "N", "N");
assert.ok(angleAllowed(nBn, 120), "a trigonal-planar 2D environment must remain admissible");
assert.equal(angleAllowed(nBn, 90), false, "the 2D sp2 control must reject an octahedral angle");

console.log("train-derived colored distance envelopes: passed", Object.fromEntries(
  model.records.map((record) => [record.key, record.exclusion.toFixed(3)])));
