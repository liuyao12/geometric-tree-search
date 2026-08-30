import assert from "node:assert/strict";
import { buildExternalPhysicsRequest, EXTERNAL_PHYSICS_REQUEST_TEMPLATES }
  from "../apps/iqc-growth-live/external-physics-request.mjs";

const atom = (siteId, species, positionAngstrom) => ({ siteId, species, positionAngstrom });
const base = {
  generatedAt: "2026-08-30T00:00:00.000Z",
  buildId: "20260830-341",
  scenarioId: "iqc",
  materialName: "Ideal 6D icosahedral model set",
  elements: ["Fe", "Al", "Cu"],
  sourceProvenance: { fixture: "algorithmic model set" },
  recordedConditions: null,
  targetCoordinatesEmbedded: false,
  observation: { role: "supplied observation", structureSha256: "a".repeat(64),
    atoms: [atom("o0", "Al", [0, 0, 0]), atom("o1", "Cu", [2.5, 0, 0])],
    cellVectorsAngstrom: null, periodicBoundary: [false, false, false] },
  growthSeed: { role: "explicit growth seed", structureSha256: "b".repeat(64),
    atoms: [atom("s0", "Al", [0, 0, 0])], cellVectorsAngstrom: null,
    periodicBoundary: [false, false, false] },
  manifestRecords: [{ id: "calculation-forces", process: "residual forces", status: "unavailable",
    role: "no force channel", evidence: "none", boundary: "not a force field" }],
};

for (const quantityId of Object.keys(EXTERNAL_PHYSICS_REQUEST_TEMPLATES)) {
  const request = buildExternalPhysicsRequest({ ...base, quantityId,
    quantityLabel: EXTERNAL_PHYSICS_REQUEST_TEMPLATES[quantityId].quantity,
    earliestPermittedUse: "only after independent validation",
    handoff: { quantityId, mode: "evidence-request", selectedRecordIds: ["calculation-forces"],
      requestedRecordIds: ["calculation-forces"], targetUsed: false } });
  assert.equal(request.schema, "gcts-external-physics-request-v1");
  assert.equal(request.configurations.observation.atomCount, 2);
  assert.equal(request.configurations.growthSeed.atomCount, 1);
  assert.equal(request.configurations.observation.coordinateUnits, "angstrom");
  assert.equal(request.safeguards.targetCoordinatesEmbedded, false);
  assert.equal(request.safeguards.searchStepsUsedAsPhysicalTime, false);
  assert.ok(request.request.requiredOutputs.length >= 3);
  assert.equal(request.expectedResponse.schema, "gcts-external-physics-response-v1");
  assert.equal(request.expectedResponse.configuration.permittedStructureSha256.observation,
    base.observation.structureSha256);
  assert.equal(typeof request.expectedResponse.results, "object");
}

assert.throws(() => buildExternalPhysicsRequest({ ...base, quantityId: "forces",
  earliestPermittedUse: "later", handoff: { quantityId: "forces", selectedRecordIds: [],
    requestedRecordIds: [], targetUsed: true } }), /hidden growth target/);
assert.throws(() => buildExternalPhysicsRequest({ ...base, quantityId: "forces",
  earliestPermittedUse: "later", observation: { ...base.observation,
    atoms: [atom("bad", "Al", [0, Number.NaN, 0])] }, handoff: { quantityId: "forces",
    selectedRecordIds: [], requestedRecordIds: [], targetUsed: false } }), /finite Cartesian/);

console.log("external physics request contract: passed");
