import assert from "node:assert/strict";
import crypto from "node:crypto";

import {
  generateIceViAverageObservation,
  ICE_VI_BROWSER_FIXTURE,
  iceViAverageUnitCellSites,
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

console.log("ice VI occupational-disorder browser fixture: passed");
