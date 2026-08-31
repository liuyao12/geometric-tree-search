import assert from "node:assert/strict";
import { INTERFACE_FLUX_RESPONSE_SCHEMA, buildInterfaceFluxRequest, evaluateInterfaceFluxScore,
  interfaceFluxSha256, matchedInterfaceFluxRankingAudit, validateInterfaceFluxResponse }
  from "./external-interface-flux.mjs";

const structure = "a".repeat(64); const surface = "b".repeat(64);
const request = buildInterfaceFluxRequest({ generatedAt: "2026-08-31T00:00:00Z", buildId: "test",
  scenarioId: "fixture", materialName: "binary nucleus", species: ["B", "A"],
  structureSha256: structure, interfaceGeometrySha256: surface,
  publicBoundary: { kind: "sphere", radiusAngstrom: 12 }, targetUsed: false });
assert.deepEqual(request.specimen.species, ["A", "B"]);
assert.equal(request.safeguards.geometricVisibilityUsedAsPhysicalFlux, false);
assert.throws(() => buildInterfaceFluxRequest({ ...request.specimen, generatedAt: "x", buildId: "x",
  scenarioId: "x", materialName: "x", targetUsed: true }), /cannot use a growth target/);
const requestSha256 = await interfaceFluxSha256(request);
const speciesFluxes = (total) => [{ species: "A", incorporationFlux: total * .6 },
  { species: "B", incorporationFlux: total * .4 }];
const patch = (patchId, positionCartesianAngstrom, outwardNormalCartesian, netIncorporationFlux) => ({
  patchId, positionCartesianAngstrom, outwardNormalCartesian, areaWeightSquareMetre: 1e-18,
  netIncorporationFlux, uncertainty: netIncorporationFlux * .02, speciesFluxes: speciesFluxes(netIncorporationFlux),
});
const response = { schema: INTERFACE_FLUX_RESPONSE_SCHEMA, requestSha256, structureSha256: structure,
  interfaceGeometrySha256: surface, species: ["A", "B"], fluxUnits: "atoms per square metre per second",
  method: { family: "steady diffusion", program: "test-solver", version: "1",
    settingsSha256: "c".repeat(64), boundaryConditionsSha256: "d".repeat(64) },
  validation: { passed: true, converged: true, steadyStateVerified: true, uncertaintyReported: true,
    interfaceMeshPredeclared: true, speciesBalanceChecked: true,
    massBalanceRelativeResidual: 2e-4, meshConvergenceRelativeChange: .02 },
  patches: [patch("+x", [4, 0, 0], [1, 0, 0], 8e20), patch("-x", [-4, 0, 0], [-1, 0, 0], 1e20),
    patch("+y", [0, 4, 0], [0, 1, 0], 2e20), patch("-y", [0, -4, 0], [0, -1, 0], 2e20),
    patch("+z", [0, 0, 4], [0, 0, 1], 2e20), patch("-z", [0, 0, -4], [0, 0, -1], 2e20)] };
const validated = validateInterfaceFluxResponse(response, { requestSha256, structureSha256: structure,
  interfaceGeometrySha256: surface, species: ["A", "B"] });
assert.equal(validated.patches.length, 6); assert.equal(validated.targetUsed, false);
assert.throws(() => validateInterfaceFluxResponse({ ...response, validation: { ...response.validation,
  massBalanceRelativeResidual: .01 } }, { requestSha256, structureSha256: structure,
  interfaceGeometrySha256: surface, species: ["A", "B"] }), /mass-balance/);
assert.throws(() => validateInterfaceFluxResponse({ ...response, patches: response.patches.map((entry, index) =>
  index ? entry : { ...entry, speciesFluxes: speciesFluxes(entry.netIncorporationFlux * .5) }) },
{ requestSha256, structureSha256: structure, interfaceGeometrySha256: surface, species: ["A", "B"] }), /do not sum/);

const occupied = [[0, 0, 0], [3, 0, 0], [-3, 0, 0], [0, 3, 0], [0, -3, 0], [0, 0, 3], [0, 0, -3]];
const fast = evaluateInterfaceFluxScore({ occupiedPositions: occupied, emittedPositions: [[4.1, 0, 0]],
  patches: validated.patches, maximumSpatialReachRelativeRadius: .5, maximumAngleRadians: Math.PI / 4 });
const slow = evaluateInterfaceFluxScore({ occupiedPositions: occupied, emittedPositions: [[-4.1, 0, 0]],
  patches: validated.patches, maximumSpatialReachRelativeRadius: .5, maximumAngleRadians: Math.PI / 4 });
assert.equal(fast.supported, true); assert.equal(slow.supported, true);
assert.ok(fast.score > slow.score); assert.ok(fast.netIncorporationFlux > slow.netIncorporationFlux);
const translated = [10, -7, 3];
const move = (point) => point.map((entry, axis) => entry + translated[axis]);
const translatedScore = evaluateInterfaceFluxScore({ occupiedPositions: occupied.map(move),
  emittedPositions: [[4.1, 0, 0].map((entry, axis) => entry + translated[axis])],
  patches: validated.patches.map((entry) => ({ ...entry, positionCartesianAngstrom: move(entry.positionCartesianAngstrom) })),
  maximumSpatialReachRelativeRadius: .5, maximumAngleRadians: Math.PI / 4 });
assert.ok(Math.abs(translatedScore.score - fast.score) < 1e-12, "joint translation must preserve the local flux score");
const audit = matchedInterfaceFluxRankingAudit([
  { candidateId: "slow", baselineScore: 2, rankedScore: 1, supported: true },
  { candidateId: "fast", baselineScore: 1, rankedScore: 2, supported: true },
]);
assert.equal(audit.rankInversions, 1); assert.equal(audit.candidateSetIdentical, true);
console.log("external spatial interface-flux tests passed");
