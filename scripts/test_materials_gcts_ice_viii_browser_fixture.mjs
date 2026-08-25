import assert from "node:assert/strict";
import crypto from "node:crypto";

import {
  generateIceViiiObservation,
  ICE_VIII_BROWSER_FIXTURE,
  iceViiiUnitCellSites,
} from "../apps/iqc-growth-live/ice-viii-browser-fixture.js";
import {
  discoverFiniteMolecularComponents,
  discoverMolecularConnectionTopology,
} from "../apps/iqc-growth-live/molecular-components.js";

assert.equal(ICE_VIII_BROWSER_FIXTURE.codId, "1566658");
assert.equal(ICE_VIII_BROWSER_FIXTURE.codRevision, 273854);
assert.equal(ICE_VIII_BROWSER_FIXTURE.license, "CC0");
assert.equal(ICE_VIII_BROWSER_FIXTURE.doi, "10.1063/1.448027");
assert.equal(ICE_VIII_BROWSER_FIXTURE.cifSha256,
  "00ea6c9535c1995feb98a18372cf3f9514816a715d79ab01dc30cacef8cfe875");

const unit = iceViiiUnitCellSites();
assert.equal(unit.length, 24);
assert.equal(unit.filter((site) => site.species === "O").length, 8);
assert.equal(unit.filter((site) => site.species === "D").length, 16);
assert.ok(unit.every((site) => site.fractional.every((value) => value >= 0 && value < 1)));

const observation = generateIceViiiObservation();
assert.equal(observation.atoms.length, 192);
assert.equal(observation.atoms.filter((atom) => atom.species === "O").length, 64);
assert.equal(observation.atoms.filter((atom) => atom.species === "D").length, 128);
const normalized = observation.atoms.map((atom) => [atom.species,
  ...atom.position.map((value) => value.toFixed(10))].join(",")).sort().join("\n");
assert.equal(crypto.createHash("sha256").update(normalized).digest("hex"),
  ICE_VIII_BROWSER_FIXTURE.normalizedAtomsSha256);

const lengths = observation.cell.map((vector, axis) => vector[axis]);
const distance = (first, second) => Math.sqrt(observation.atoms[first].position.reduce((sum, value, axis) => {
  let delta = observation.atoms[second].position[axis] - value;
  delta -= Math.round(delta / lengths[axis]) * lengths[axis];
  return sum + delta ** 2;
}, 0));
const molecular = discoverFiniteMolecularComponents({
  species: observation.atoms.map((atom) => atom.species),
  distance,
  descriptorToleranceA: .025,
});
assert.equal(molecular.accepted, true);
assert.equal(molecular.materialLabelUsed, false);
assert.equal(molecular.expectedFormulaUsed, false);
assert.equal(molecular.componentCount, 64);
assert.equal(molecular.typeCount, 1);
assert.deepEqual(molecular.types[0].formula, [["D", 2], ["O", 1]]);
assert.equal(molecular.types[0].occurrences.length, 64);
assert.ok(molecular.components.every((component) => component.length === 3));

const connection = discoverMolecularConnectionTopology({
  discovery: molecular,
  species: observation.atoms.map((atom) => atom.species),
  distance,
  descriptorToleranceA: .025,
});
assert.equal(connection.componentEdges.length, 128);
assert.equal(connection.connectionTypeCount, 1);
assert.equal(connection.componentGraphConnected, false,
  "ice VIII must retain its two interpenetrating, non-bonded water networks");
assert.equal(connection.materialLabelUsed, false);
assert.equal(connection.expectedRingSizeUsed, false);

console.log("ice VIII published D2O browser fixture: passed");
