import assert from "node:assert/strict";
import { archiveResponseFrontierRankAudit }
  from "../apps/iqc-growth-live/archive-response-frontier-audit.js";

const candidate = (candidateKey, baselineScore, responseContribution, observedGeometricStrain) => ({
  candidateKey,
  candidateDigest: `digest-${candidateKey}`,
  action: `action-${candidateKey}`,
  baselineScore,
  observedGeometricStrain,
  responseGeometricStrain: -responseContribution,
  scoreTerms: [{ id: "geometric-strain", weight: -1, contribution: responseContribution }],
});

const audit = archiveResponseFrontierRankAudit({
  snapshotIndex: 7,
  frontierCount: 5,
  candidateSetDigest: "frozen-all",
  candidates: [
    candidate("A", 10, -1, 5),
    candidate("B", 9, -5, 1),
    candidate("C", 8, -2, 2),
  ],
});

assert.equal(audit.candidateCount, 3);
assert.equal(audit.frontierCount, 5);
assert.equal(audit.responseWinnerKey, "A");
assert.equal(audit.controlWinnerKey, "B");
assert.equal(audit.winnerChanged, true);
assert.equal(audit.changedRanks, 3);
assert.equal(audit.maximumRankDisplacement, 2);
assert.equal(audit.pairwiseRankInversions, 2);
assert.equal(audit.spearmanRho, -0.5);
assert.deepEqual(audit.rows.map((row) => [row.candidateKey, row.responseRank, row.controlRank]),
  [["A", 1, 3], ["B", 2, 1], ["C", 3, 2]]);
assert.equal(audit.rows.find((row) => row.candidateKey === "A").controlScore, 6);
assert.match(audit.auditDigest, /^[0-9a-f]{8}$/);

const repeated = archiveResponseFrontierRankAudit({ snapshotIndex: 7, frontierCount: 5,
  candidateSetDigest: "frozen-all",
  candidates: [candidate("C", 8, -2, 2), candidate("A", 10, -1, 5), candidate("B", 9, -5, 1)] });
assert.equal(repeated.auditDigest, audit.auditDigest);
assert.equal(repeated.admittedCandidateSetDigest, audit.admittedCandidateSetDigest);

console.log(JSON.stringify({ passed: true, candidateCount: audit.candidateCount,
  winnerChanged: audit.winnerChanged, pairwiseRankInversions: audit.pairwiseRankInversions,
  spearmanRho: audit.spearmanRho, auditDigest: audit.auditDigest }));
