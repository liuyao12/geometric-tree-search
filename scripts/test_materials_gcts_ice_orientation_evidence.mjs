import assert from "node:assert/strict";
import {
  buildIceOrientationEvidenceRequest,
  ICE_ORIENTATION_RESPONSE_SCHEMA,
  validateIceOrientationEvidenceResponse,
} from "../apps/iqc-growth-live/ice-orientation-evidence.mjs";

const molecule = (x, upper = false) => [["O", [x, 0, 0]], ["H", [x + .7, upper ? .5 : -.5, 0]], ["H", [x - .7, upper ? .5 : -.5, 0]]];
const audit = {
  consistent: true, targetUsed: false, physicalPotentialUsed: false,
  canonicalBranchMaterialized: false,
  orientationDomains: [
    { anchorKey: "a", anchorSite: ["O", [0, 0, 0]], alternatives: [
      { poseKey: "a0", sites: molecule(0, false) }, { poseKey: "a1", sites: molecule(0, true) }] },
    { anchorKey: "b", anchorSite: ["O", [2.7, 0, 0]], alternatives: [
      { poseKey: "b0", sites: molecule(2.7, false) }, { poseKey: "b1", sites: molecule(2.7, true) }] },
  ],
  orientationConstraints: [{ firstAnchorKey: "a", secondAnchorKey: "b", separation: 2.7,
    allowedPosePairs: [["a0", "b1"], ["a1", "b0"]] }],
};

const request = await buildIceOrientationEvidenceRequest({
  generatedAt: "2026-08-31T00:00:00.000Z", buildId: "test", caseId: "ice-test",
  artifactDigest: "a".repeat(64), temperatureKelvin: 100, pressureGPa: 0,
  boundaryCondition: "finite embedded O scaffold; exterior H bonds omitted", orientationAudit: audit,
});
assert.equal(request.finiteGeometry.domainCount, 2);
assert.equal(request.finiteGeometry.unresolvedDomainCount, 2);
assert.equal(request.finiteGeometry.retainedPoseCount, 4);
assert.equal(request.calculation.independentLocalPoseEnergiesInsufficient, true);
assert.equal(request.requestSha256.length, 64);

const response = {
  schema: ICE_ORIENTATION_RESPONSE_SCHEMA,
  requestSha256: request.requestSha256,
  thermodynamicState: request.thermodynamicState,
  method: { name: "test free-energy solver", version: "1", provenance: "synthetic contract" },
  modelScope: "global-configurational",
  stateSpaceCoverage: { kind: "exhaustive-enumeration", feasibleAssignmentCount: 2,
    certificateSha256: "c".repeat(64) },
  states: [
    { stateId: "low", assignment: [{ anchorKey: "a", poseKey: "a0" }, { anchorKey: "b", poseKey: "b1" }], freeEnergyEv: 0, uncertaintyEv: .01 },
    { stateId: "high", assignment: [{ anchorKey: "a", poseKey: "a1" }, { anchorKey: "b", poseKey: "b0" }], freeEnergyEv: .08, uncertaintyEv: .01 },
  ],
};
const validation = await validateIceOrientationEvidenceResponse(response, request);
assert.equal(validation.selectionEligible, true);
assert.equal(validation.selectedStateId, "low");
assert.ok(validation.minimumGapKbt > 9);
assert.equal(validation.candidateGeometryChanged, false);

await assert.rejects(() => validateIceOrientationEvidenceResponse({ ...response,
  modelScope: "independent-local" }, request), /independent local pose energies/);
await assert.rejects(() => validateIceOrientationEvidenceResponse({ ...response,
  states: [{ ...response.states[0], assignment: [{ anchorKey: "a", poseKey: "a0" }, { anchorKey: "b", poseKey: "b0" }] }, response.states[1]] }, request), /violates frozen ice-rule constraint/);
const overlapping = await validateIceOrientationEvidenceResponse({ ...response,
  states: [{ ...response.states[0], uncertaintyEv: .05 }, { ...response.states[1], uncertaintyEv: .05 }] }, request);
assert.equal(overlapping.selectionEligible, false);
assert.equal(overlapping.selectedStateId, null);
await assert.rejects(() => validateIceOrientationEvidenceResponse({ ...response,
  stateSpaceCoverage: { ...response.stateSpaceCoverage, feasibleAssignmentCount: 3 } }, request),
/state-space completeness/);

console.log("ice orientation external-evidence contract: passed");
