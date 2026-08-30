import assert from "node:assert/strict";
import crypto from "node:crypto";
import { IQC_DISJOINT_CONFIRMATION_ARTIFACT } from
  "../apps/iqc-growth-live/iqc-disjoint-confirmation-artifact.js";
import { executeIqcDisjointConfirmation, validateIqcDisjointConfirmationArtifact } from
  "../apps/iqc-growth-live/iqc-disjoint-confirmation-growth.js";

validateIqcDisjointConfirmationArtifact(IQC_DISJOINT_CONFIRMATION_ARTIFACT);
const trace = executeIqcDisjointConfirmation(IQC_DISJOINT_CONFIRMATION_ARTIFACT);
assert.equal(trace.seedSites.length, 473);
assert.equal(trace.waves[0].candidateTerminals, 128);
assert.equal(trace.waves[0].exactTerminalsPosthoc, 90);
assert.equal(trace.waves[0].selectedRank, 1);
assert.equal(trace.waves[0].acceptedSites, 3);
assert.equal(trace.waves[0].acceptedActions, 3);
assert.equal(trace.waves[0].emittedSites.length, 3);
assert.equal(trace.targetUsed, false);
assert.equal(trace.targetDomainDisjoint, true);
assert.equal(trace.waves[1].candidateTerminals, 128);
assert.equal(trace.waves[1].exactTerminalsPosthoc, 62);
assert.equal(trace.waves[1].fusionFirstExactRank, 16);
assert.equal(trace.waves[1].acceptedActions, 0);
assert.equal(trace.autonomousContinuationCertified, false);
assert.equal(trace.stationaryOrExponentialClaimed, false);
const coordinatePayload = [
  ...IQC_DISJOINT_CONFIRMATION_ARTIFACT.seedSites,
  ...IQC_DISJOINT_CONFIRMATION_ARTIFACT.selectedActionSites,
].map(([species, x, y, z]) =>
  `${species},${x.toFixed(10)},${y.toFixed(10)},${z.toFixed(10)}`).join("\n");
assert.equal(crypto.createHash("sha256").update(coordinatePayload).digest("hex"),
  IQC_DISJOINT_CONFIRMATION_ARTIFACT.coordinateSpeciesSha256);
assert.throws(() => validateIqcDisjointConfirmationArtifact({
  ...IQC_DISJOINT_CONFIRMATION_ARTIFACT, targetUsedForFitCandidateOrRanking: true,
}));
console.log("IQC disjoint confirmation browser artifact: passed");
