import assert from "node:assert/strict";
import { buildKineticGeometryResponse, inspectKineticGeometryResponse,
  rateBoxObservableEnvelope }
  from "./kinetic-geometry-response.mjs";

const path = (candidateId, eventDirection, initialDomain, finalDomain,
  initialPosition, finalPosition) => ({
  candidateId, eventDirection, coordinateBearingImagesValidated: true,
  maximumSiteDisplacementAngstrom: Math.hypot(...initialPosition.map((value, axis) =>
    value - finalPosition[axis])),
  materialCounts: [1 + (initialDomain === "material" ? 1 : 0),
    1 + (finalDomain === "material" ? 1 : 0)],
  fixedMaterialSites: [{ pathSiteId: "fixed", species: "Na", positionAngstrom: [0, 0, 0] }],
  images: [
    { reactionCoordinate: 0, sites: [{ pathSiteId: "moving", species: "Cl",
      domain: initialDomain, positionAngstrom: initialPosition }] },
    { reactionCoordinate: 1, sites: [{ pathSiteId: "moving", species: "Cl",
      domain: finalDomain, positionAngstrom: finalPosition }] },
  ],
});

const records = [
  { candidateId: "grow", eventDirection: "attach", barrierElectronVolt: .3,
    uncertaintyElectronVolt: .01, attemptFrequencyPerSecond: 1e8,
    attemptFrequencyUncertaintyLog10: .05,
    pathGeometry: path("grow", "attach", "reservoir", "material", [5, 0, 0], [1, 0, 0]) },
  { candidateId: "shrink", eventDirection: "detach", barrierElectronVolt: .7,
    uncertaintyElectronVolt: .01, attemptFrequencyPerSecond: 1e14,
    attemptFrequencyUncertaintyLog10: .05,
    pathGeometry: path("shrink", "detach", "material", "reservoir", [1, 0, 0], [5, 0, 0]) },
];
const applicability = { scope: "bounded-constant-htst", minimumKelvin: 150,
  maximumKelvin: 1500, externallyAuthorized: true,
  barrierAndPrefactorAssumedConstant: true };
const response = buildKineticGeometryResponse(records, applicability,
  { contactReach: 1.35, sampleCount: 61 });
assert.equal(response.available, true);
assert.equal(response.candidateCount, 2);
assert.equal(response.eventGeometry.find((event) => event.candidateId === "grow")
  .materialAtomDelta, 1);
assert.equal(response.eventGeometry.find((event) => event.candidateId === "shrink")
  .materialAtomDelta, -1);
assert.ok(response.samples[0].expectedMaterialAtomDeltaPerEvent > 0);
assert.ok(response.samples.at(-1).expectedMaterialAtomDeltaPerEvent < 0);
assert.ok(response.samples[0].signedGrowthBias > 0);
assert.ok(response.samples.at(-1).signedGrowthBias < 0);
assert.ok(response.samples.every((sample) => Math.abs(sample.growingProbability
  + sample.shrinkingProbability + sample.countPreservingProbability - 1) < 1e-12));
assert.ok(response.samples.every((sample) => sample.contactResolvedProbabilityMass > 0));
assert.equal(response.physicalTrajectoryIntegrated, false);
assert.equal(response.futureFrontierAssumedUnchanged, false);
assert.equal(response.adversarialRateIntervalEnvelopeComputed, true);
assert.equal(response.stochasticUncertaintyPropagatedIntoResponse, false);
response.samples.forEach((sample) => {
  const [atomLow, atomHigh] = sample.rateBoxEnvelope.expectedMaterialAtomDeltaPerEvent;
  assert.ok(atomLow <= sample.expectedMaterialAtomDeltaPerEvent);
  assert.ok(atomHigh >= sample.expectedMaterialAtomDeltaPerEvent);
  const [growthLow, growthHigh] = sample.rateBoxEnvelope.growingProbability;
  assert.ok(growthLow <= sample.growingProbability && growthHigh >= sample.growingProbability);
  const [contactLow, contactHigh] = sample.rateBoxEnvelope
    .conditionalExpectedNetContactDeltaPerResolvedEvent;
  assert.ok(contactLow <= sample.conditionalExpectedNetContactDeltaPerResolvedEvent);
  assert.ok(contactHigh >= sample.conditionalExpectedNetContactDeltaPerResolvedEvent);
});
const extremeSpanRecords = [
  { log10RateLowerPerSecond: -1000, log10RateUpperPerSecond: -900, value: -2 },
  { log10RateLowerPerSecond: 900, log10RateUpperPerSecond: 1000, value: 3 },
];
const extremeEnvelope = rateBoxObservableEnvelope(extremeSpanRecords, (record) => record.value);
assert.ok(extremeEnvelope[0] >= -2 && extremeEnvelope[1] <= 3);
assert.ok(extremeEnvelope[0] <= extremeEnvelope[1]);
const bruteRecords = [
  { log10RateLowerPerSecond: -1, log10RateUpperPerSecond: 1, value: -3 },
  { log10RateLowerPerSecond: -.4, log10RateUpperPerSecond: .7, value: 2 },
  { log10RateLowerPerSecond: .2, log10RateUpperPerSecond: 1.2, value: 5 },
];
const bruteRatios = Array.from({ length: 8 }, (_, mask) => {
  const rates = bruteRecords.map((record, index) => 10 ** ((mask >> index) & 1
    ? record.log10RateUpperPerSecond : record.log10RateLowerPerSecond));
  return rates.reduce((sum, rate, index) => sum + rate * bruteRecords[index].value, 0)
    / rates.reduce((sum, rate) => sum + rate, 0);
});
const exactEnvelope = rateBoxObservableEnvelope(bruteRecords, (record) => record.value);
assert.ok(Math.abs(exactEnvelope[0] - Math.min(...bruteRatios)) < 1e-12);
assert.ok(Math.abs(exactEnvelope[1] - Math.max(...bruteRatios)) < 1e-12);
assert.deepEqual(rateBoxObservableEnvelope(records.map((record) => ({ ...record,
  log10RateLowerPerSecond: -2, log10RateUpperPerSecond: 2 })), () => 7), [7, 7]);
assert.ok(inspectKineticGeometryResponse(response, 700));
assert.equal(buildKineticGeometryResponse(records, null).available, false);
assert.equal(inspectKineticGeometryResponse({ available: false }, 700), null);

console.log("finite-catalog kinetic geometry response: ok");
