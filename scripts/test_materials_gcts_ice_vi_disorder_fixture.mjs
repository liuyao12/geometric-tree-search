import assert from "node:assert/strict";
import crypto from "node:crypto";

import {
  generateIceViAverageObservation,
  ICE_VI_BROWSER_FIXTURE,
  iceViAverageUnitCellSites,
  resolveIceViIceRuleMicrostate,
} from "../apps/iqc-growth-live/ice-vi-browser-fixture.js";
import {
  occupancyChemistryToken,
  occupancyDisplayLabel,
} from "../apps/iqc-growth-live/structure-io.js";

assert.equal(ICE_VI_BROWSER_FIXTURE.codId, "1567346");
assert.equal(ICE_VI_BROWSER_FIXTURE.codRevision, 276901);
assert.equal(ICE_VI_BROWSER_FIXTURE.license, "CC-BY-4.0");
assert.equal(ICE_VI_BROWSER_FIXTURE.doi, "10.1107/S2052252522006662");
assert.equal(ICE_VI_BROWSER_FIXTURE.cifSha256,
  "a8eba8ab43c98a30d62ee08fe83f003f945aa22018331254df852c8bbdc2efc6");

const unit = iceViAverageUnitCellSites();
assert.equal(unit.length, 50);
assert.equal(unit.filter((site) => site.species === "O").length, 10);
assert.equal(unit.filter((site) => site.species === "D").length, 40);
assert.ok(unit.filter((site) => site.species === "O").every((site) => site.occupancy === 1));
assert.ok(unit.filter((site) => site.species === "D").every((site) => site.occupancy === .5));

const observation = generateIceViAverageObservation();
assert.equal(observation.atoms.length, 400);
assert.equal(observation.atoms.filter((atom) => atom.species === "O").length, 80);
assert.equal(observation.atoms.filter((atom) => atom.species === "D").length, 320);
assert.equal(observation.atoms.reduce((sum, atom) => sum + atom.occupancy, 0), 240);
const normalized = observation.atoms.map((atom) => [atom.label, atom.species,
  atom.occupancy.toFixed(6), atom.uIsoA2.toFixed(6),
  ...atom.position.map((value) => value.toFixed(10))].join(",")).sort().join("\n");
assert.equal(crypto.createHash("sha256").update(normalized).digest("hex"),
  ICE_VI_BROWSER_FIXTURE.normalizedAtomsSha256);

const candidateD = observation.atoms.find((atom) => atom.species === "D");
assert.equal(occupancyChemistryToken(candidateD), "occ[D=0.5;Vac=0.5]");
assert.equal(occupancyDisplayLabel(candidateD), "D 50% / vacancy 50%");
assert.equal(occupancyChemistryToken(observation.atoms.find((atom) => atom.species === "O")), "O");

const realization = resolveIceViIceRuleMicrostate(1);
assert.equal(realization.atoms.length, 240);
assert.equal(realization.atoms.filter((atom) => atom.species === "O").length, 80);
assert.equal(realization.atoms.filter((atom) => atom.species === "D").length, 160);
assert.ok(realization.atoms.every((atom) => atom.occupancy === 1));
assert.deepEqual(realization.audit.oxygenDegreeHistogram, { 4: 80 });
assert.deepEqual(realization.audit.donorCountHistogram, { 2: 80 });
assert.equal(realization.audit.oxygenBonds, 160);
assert.equal(realization.audit.connectedOxygenNetworks, 2);
assert.equal(realization.audit.oneDeuteriumPerBond, true);
assert.equal(realization.audit.twoCovalentDeuteriaPerOxygen, true);
assert.equal(realization.audit.hiddenSiteLabelsUsed, false);
assert.equal(realization.audit.reportedPeriodicCellUsedForMinimumImage, true);
assert.equal(realization.audit.latticeSiteIndicesUsed, false);
assert.equal(realization.audit.preassignedOxygenBondGraphUsed, false);
assert.equal(realization.audit.energyOrPotentialUsed, false);

const realizedO = realization.atoms.filter((atom) => atom.species === "O");
const realizedD = realization.atoms.filter((atom) => atom.species === "D");
const lengths = realization.cell.map((vector, axis) => vector[axis]);
const periodicDistance = (first, second) => Math.hypot(...first.map((value, axis) => {
  let delta = value - second[axis];
  delta -= Math.round(delta / lengths[axis]) * lengths[axis];
  return delta;
}));
const covalentOwners = Array(realizedO.length).fill(0);
const occupiedBonds = new Set();
realizedD.forEach((deuterium) => {
  const nearest = realizedO.map((oxygen, oxygenIndex) => ({
    oxygenIndex, distance: periodicDistance(deuterium.position, oxygen.position),
  })).sort((first, second) => first.distance - second.distance || first.oxygenIndex - second.oxygenIndex).slice(0, 2);
  covalentOwners[nearest[0].oxygenIndex]++;
  occupiedBonds.add(nearest.map(({ oxygenIndex }) => oxygenIndex).sort((a, b) => a - b).join(":"));
});
assert.ok(covalentOwners.every((count) => count === 2));
assert.equal(occupiedBonds.size, 160);

const secondRealization = resolveIceViIceRuleMicrostate(2);
const selectedDigest = (sample) => crypto.createHash("sha256").update(sample.atoms
  .filter((atom) => atom.species === "D").map((atom) => atom.position.join(",")).sort().join("\n")).digest("hex");
assert.notEqual(selectedDigest(realization), selectedDigest(secondRealization));
assert.equal(selectedDigest(realization), selectedDigest(resolveIceViIceRuleMicrostate(1)),
  "the same seed must reproduce the same occupational microstate");

const larger = resolveIceViIceRuleMicrostate(9, [3, 3, 3]);
assert.equal(larger.atoms.length, 810);
assert.equal(larger.audit.oxygenAtoms, 270);
assert.equal(larger.audit.oxygenBonds, 540);
assert.equal(larger.audit.selectedDeuteriumAtoms, 540);
assert.equal(larger.audit.twoCovalentDeuteriaPerOxygen, true);
assert.throws(() => generateIceViAverageObservation([2, 0, 2]), /three positive integers/);

console.log("ice VI occupational-disorder browser fixture: passed");
