import assert from "node:assert/strict";
import { validateCandidateActionPathGeometry } from "./action-path-geometry.mjs";

const sha = (letter) => letter.repeat(64);
const initialConfiguration = { atoms: [
  { siteId: "a", species: "Na", positionAngstrom: [0, 0, 0] },
  { siteId: "b", species: "Cl", positionAngstrom: [1, 0, 0] },
] };
const candidate = { candidateId: "exchange:1->x", candidateDigestSha256: sha("a"),
  eventDirection: "exchange", initialGeometrySha256: sha("b"), finalGeometrySha256: sha("c"),
  removedSites: [{ species: "Na", positionAngstrom: [0, 0, 0] }],
  emittedSites: [{ species: "Cl", positionAngstrom: [0, 1, 0] }] };
const images = [
  { reactionCoordinate: 0, energyElectronVolt: 0,
    maximumForceElectronVoltPerAngstrom: .01, sites: [
      { pathSiteId: "cl-in", species: "Cl", positionAngstrom: [0, 3, 0], domain: "reservoir" },
      { pathSiteId: "na-out", species: "Na", positionAngstrom: [0, 0, 0], domain: "material" },
    ] },
  { reactionCoordinate: .5, energyElectronVolt: .6,
    maximumForceElectronVoltPerAngstrom: .03, sites: [
      { pathSiteId: "cl-in", species: "Cl", positionAngstrom: [0, 2, 0], domain: "interface" },
      { pathSiteId: "na-out", species: "Na", positionAngstrom: [0, 1, 0], domain: "interface" },
    ] },
  { reactionCoordinate: 1, energyElectronVolt: .1,
    maximumForceElectronVoltPerAngstrom: .01, sites: [
      { pathSiteId: "cl-in", species: "Cl", positionAngstrom: [0, 1, 0], domain: "material" },
      { pathSiteId: "na-out", species: "Na", positionAngstrom: [0, 3, 0], domain: "reservoir" },
    ] },
];
const raw = { candidateId: candidate.candidateId,
  candidateDigestSha256: candidate.candidateDigestSha256,
  initialGeometrySha256: candidate.initialGeometrySha256,
  finalGeometrySha256: candidate.finalGeometrySha256,
  pathModel: "explicit-reservoir-extended-system",
  fixedMaterialSites: [
    { pathSiteId: "cl-existing", species: "Cl", positionAngstrom: [1, 0, 0] },
  ],
  reservoir: { mode: "explicit-extended-system", boundaryCondition: "surface-feedstock",
    description: "explicit incoming Cl and outgoing Na feedstock sites",
    settingsSha256: sha("d"), chemicalPotentialReference: "independent feedstock state" },
  pathConverged: true, endpointMappingVerified: true,
  extendedSystemAtomCountConstant: true, speciesIdentityConstant: true,
  saddleImageIndex: 1, images };
const options = { candidate, initialConfiguration, barrierElectronVolt: .6,
  barrierUncertaintyElectronVolt: .01, energyDeltaElectronVolt: .1,
  energyDeltaUncertaintyElectronVolt: .01, maximumForceElectronVoltPerAngstrom: .03 };

const audit = validateCandidateActionPathGeometry(raw, options);
assert.equal(audit.imageCount, 3);
assert.equal(audit.saddleImageIndex, 1);
assert.equal(audit.extendedSystemAtomCount, 3);
assert.deepEqual(audit.materialCounts, [2, 1, 2]);
assert.deepEqual(audit.interfaceCounts, [0, 2, 0]);
assert.deepEqual(audit.reservoirCounts, [1, 0, 1]);
assert.equal(audit.coordinateBearingImagesValidated, true);
assert.equal(audit.targetUsed, false);

assert.throws(() => validateCandidateActionPathGeometry({ ...raw,
  images: images.map((image, index) => index === 2 ? { ...image,
    sites: image.sites.map((site) => site.pathSiteId === "cl-in"
      ? { ...site, positionAngstrom: [0, 1.2, 0] } : site) } : image) }, options),
/does not reproduce the frozen candidate endpoint/);
assert.throws(() => validateCandidateActionPathGeometry({ ...raw,
  images: images.map((image, index) => index === 1 ? { ...image,
    sites: image.sites.map((site) => site.pathSiteId === "cl-in"
      ? { ...site, species: "Na" } : site) } : image) }, options),
/preserve the exact extended-system site IDs and species/);
assert.throws(() => validateCandidateActionPathGeometry({ ...raw,
  saddleImageIndex: 0, images: images.map((image, index) => ({ ...image,
    energyElectronVolt: index === 0 ? .6 : index === 1 ? .4 : .1 })) }, options),
/declared saddle must be an internal/);
assert.throws(() => validateCandidateActionPathGeometry({ ...raw, reservoir: null }, options),
/requires an explicit extended-system reservoir/);

const hopCandidate = { ...candidate, candidateId: "hop", eventDirection: "hop",
  removedSites: [{ species: "Na", positionAngstrom: [0, 0, 0] }],
  emittedSites: [{ species: "Na", positionAngstrom: [0, 1, 0] }] };
assert.throws(() => validateCandidateActionPathGeometry({ ...raw,
  candidateId: "hop", pathModel: "closed-system-fixed-composition" }, {
  ...options, candidate: hopCandidate }), /closed-system surface hop may not declare a reservoir/);

console.log("candidate action path-geometry contract tests passed");
