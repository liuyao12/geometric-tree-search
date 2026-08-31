import assert from "node:assert/strict";
import { actionPathMechanismSensitivity, analyzeActionPathMechanism }
  from "./action-path-mechanism.mjs";

const path = { candidateId: "attach:1", eventDirection: "attach",
  fixedMaterialSites: [
    { pathSiteId: "f0", species: "Na", positionAngstrom: [0, 0, 0] },
    { pathSiteId: "f1", species: "Cl", positionAngstrom: [1, 0, 0] },
  ],
  images: [
    { reactionCoordinate: 0, sites: [{ pathSiteId: "m0", species: "Na",
      domain: "reservoir", positionAngstrom: [0, 4, 0] }] },
    { reactionCoordinate: .5, sites: [{ pathSiteId: "m0", species: "Na",
      domain: "interface", positionAngstrom: [0, 1.8, 0] }] },
    { reactionCoordinate: 1, sites: [{ pathSiteId: "m0", species: "Na",
      domain: "material", positionAngstrom: [0, 1, 0] }] },
  ] };

const audit = analyzeActionPathMechanism(path, { contactReach: 1.35 });
assert.ok(Math.abs(audit.referenceLengthAngstrom - 1.4) < 1e-12);
assert.ok(Math.abs(audit.cutoffAngstrom - 1.89) < 1e-12);
assert.equal(audit.netFormedContactCount, 2);
assert.equal(audit.netBrokenContactCount, 0);
assert.equal(audit.geometricCharacter, "contact-forming");
assert.equal(audit.perImage[0].contactCount, 0);
assert.equal(audit.perImage[2].contactCount, 2);
assert.equal(audit.perImage[1].formedContactCount, 1);
assert.equal(audit.perImage[2].formedContactCount, 1);
assert.ok(audit.perImage[1].maximumDynamicDisplacementAngstrom > 2);
assert.equal(audit.chemicalBondClaimed, false);

const sensitivity = actionPathMechanismSensitivity(path, [1.15, 1.35, 1.6]);
assert.equal(sensitivity.audits.length, 3);
assert.equal(sensitivity.thresholdSensitivityReported, true);
assert.deepEqual(sensitivity.netFormedRange, [2, 2]);
assert.equal(sensitivity.characterStable, true);

const noReference = analyzeActionPathMechanism({ ...path, fixedMaterialSites: [],
  images: path.images.map((image) => ({ ...image, sites: image.sites.map((site) => ({ ...site,
    domain: "reservoir" })) })) });
assert.equal(noReference.referenceAvailable, false);
assert.equal(noReference.cutoffAngstrom, null);
assert.equal(noReference.netFormedContactCount, 0);
assert.throws(() => analyzeActionPathMechanism(path, { contactReach: 1 }), /greater than one/);

console.log("action-path geometric mechanism tests passed");
