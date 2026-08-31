import assert from "node:assert/strict";
import { buildFrontierMechanismLandscape }
  from "./frontier-mechanism-landscape.mjs";

const path = (candidateId, eventDirection, firstDomain, lastDomain) => ({
  candidateId, eventDirection, coordinateBearingImagesValidated: true,
  maximumSiteDisplacementAngstrom: 1, materialCounts: [firstDomain === "material" ? 2 : 1,
    lastDomain === "material" ? 2 : 1],
  fixedMaterialSites: [{ pathSiteId: "fixed", species: "Na", positionAngstrom: [0, 0, 0] }],
  images: [
    { reactionCoordinate: 0, sites: [{ pathSiteId: "moving", species: "Cl",
      domain: firstDomain, positionAngstrom: firstDomain === "material" ? [1, 0, 0] : [5, 0, 0] }] },
    { reactionCoordinate: 1, sites: [{ pathSiteId: "moving", species: "Cl",
      domain: lastDomain, positionAngstrom: lastDomain === "material" ? [1, 0, 0] : [5, 0, 0] }] },
  ],
});
const records = [
  { candidateId: "downhill-growth", eventDirection: "attach", barrierElectronVolt: .35,
    uncertaintyElectronVolt: .02, attemptFrequencyPerSecond: 1e12,
    attemptFrequencyUncertaintyLog10: .1, grandPotentialDeltaElectronVolt: -.4,
    grandPotentialDeltaUncertaintyElectronVolt: .05,
    pathGeometry: path("downhill-growth", "attach", "reservoir", "material") },
  { candidateId: "uphill-shrink", eventDirection: "detach", barrierElectronVolt: .7,
    uncertaintyElectronVolt: .03, attemptFrequencyPerSecond: 1e13,
    attemptFrequencyUncertaintyLog10: .1, grandPotentialDeltaElectronVolt: .3,
    grandPotentialDeltaUncertaintyElectronVolt: .04,
    pathGeometry: path("uphill-shrink", "detach", "material", "reservoir") },
  { candidateId: "ambiguous-hop", eventDirection: "hop", barrierElectronVolt: .9,
    uncertaintyElectronVolt: .02, attemptFrequencyPerSecond: 1e11,
    attemptFrequencyUncertaintyLog10: .1, grandPotentialDeltaElectronVolt: .01,
    grandPotentialDeltaUncertaintyElectronVolt: .03,
    pathGeometry: path("ambiguous-hop", "hop", "material", "material") },
];
const thermodynamics = { model: "grand-canonical-state-free-energy",
  ensemble: "grand-canonical-T-V-mu", temperatureKelvin: 600 };
const audit = buildFrontierMechanismLandscape(records, thermodynamics,
  { temperatureKelvin: 600 });
assert.equal(audit.available, true);
assert.equal(audit.candidateCount, 3);
assert.equal(audit.events.find((event) => event.candidateId === "downhill-growth")
  .materialPopulationClass, "growth");
assert.equal(audit.events.find((event) => event.candidateId === "downhill-growth")
  .grandPotentialClass, "downhill");
assert.equal(audit.events.find((event) => event.candidateId === "uphill-shrink")
  .grandPotentialClass, "uphill");
assert.equal(audit.events.find((event) => event.candidateId === "ambiguous-hop")
  .grandPotentialClass, "uncertainty-overlapping-zero");
assert.ok(Math.abs(audit.downhillProbabilityMass + audit.uphillProbabilityMass
  + audit.zeroOverlappingProbabilityMass - 1) < 1e-12);
assert.ok(audit.jointProbabilityMass["growth:downhill"] > 0);
assert.equal(audit.thermodynamicAndKineticTemperatureCoherent, true);
assert.equal(audit.detailedBalanceCertified, false);
assert.equal(buildFrontierMechanismLandscape(records, null,
  { temperatureKelvin: 600 }).available, false);
assert.throws(() => buildFrontierMechanismLandscape(records, thermodynamics,
  { temperatureKelvin: 601 }), /temperatures must match/);

console.log("finite-frontier mechanism landscape: ok");
