function stringHash(value) {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index++) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}

function round(value, digits = 10) {
  const scale = 10 ** digits;
  return Math.round(value * scale) / scale;
}

export function archiveResponseFrontierRankAudit({ snapshotIndex = null, frontierCount = 0,
  candidateSetDigest = null, candidates = [] } = {}) {
  const rows = candidates.map((candidate) => {
    const responseTerm = candidate.scoreTerms?.find((term) => term.id === "geometric-strain");
    if (!responseTerm || !Number.isFinite(candidate.observedGeometricStrain)
      || !Number.isFinite(candidate.responseGeometricStrain)
      || !Number.isFinite(candidate.baselineScore)) return null;
    const controlContribution = responseTerm.weight * candidate.observedGeometricStrain;
    return { candidateKey: candidate.candidateKey, candidateDigest: candidate.candidateDigest,
      action: candidate.action, responseScore: candidate.baselineScore,
      controlScore: candidate.baselineScore - responseTerm.contribution + controlContribution,
      responseStrain: candidate.responseGeometricStrain,
      controlStrain: candidate.observedGeometricStrain,
      responseContribution: responseTerm.contribution, controlContribution };
  }).filter(Boolean);
  if (!rows.length) return null;
  const stableRank = (field) => [...rows].sort((first, second) => second[field] - first[field]
    || first.candidateKey.localeCompare(second.candidateKey));
  const responseRanked = stableRank("responseScore");
  const controlRanked = stableRank("controlScore");
  const responseRanks = new Map(responseRanked.map((row, index) => [row.candidateKey, index + 1]));
  const controlRanks = new Map(controlRanked.map((row, index) => [row.candidateKey, index + 1]));
  rows.forEach((row) => {
    row.responseRank = responseRanks.get(row.candidateKey);
    row.controlRank = controlRanks.get(row.candidateKey);
    row.rankDisplacement = row.controlRank - row.responseRank;
    row.scoreDelta = row.responseScore - row.controlScore;
  });
  let pairwiseRankInversions = 0;
  for (let first = 0; first < responseRanked.length; first++) {
    for (let second = first + 1; second < responseRanked.length; second++) {
      if (controlRanks.get(responseRanked[first].candidateKey)
        > controlRanks.get(responseRanked[second].candidateKey)) pairwiseRankInversions++;
    }
  }
  const squaredRankDifference = rows.reduce((sum, row) =>
    sum + (row.responseRank - row.controlRank) ** 2, 0);
  const candidateCount = rows.length;
  const spearmanRho = candidateCount < 2 ? 1
    : 1 - 6 * squaredRankDifference / (candidateCount * (candidateCount ** 2 - 1));
  const rankedRows = [...rows].sort((first, second) => first.responseRank - second.responseRank);
  const digestPayload = rankedRows.map((row) => ({ key: row.candidateKey,
    responseRank: row.responseRank, controlRank: row.controlRank,
    responseScore: round(row.responseScore), controlScore: round(row.controlScore) }));
  return { snapshotIndex, frontierCount, candidateCount, candidateSetDigest,
    admittedCandidateSetDigest: stringHash(rows.map((row) => row.candidateKey).sort().join("|")),
    responseWinner: responseRanked[0].action, controlWinner: controlRanked[0].action,
    responseWinnerKey: responseRanked[0].candidateKey, controlWinnerKey: controlRanked[0].candidateKey,
    winnerChanged: responseRanked[0].candidateKey !== controlRanked[0].candidateKey,
    changedRanks: rows.filter((row) => row.responseRank !== row.controlRank).length,
    maximumRankDisplacement: Math.max(...rows.map((row) => Math.abs(row.rankDisplacement))),
    pairwiseRankInversions, spearmanRho, rows: rankedRows,
    auditDigest: stringHash(JSON.stringify({ candidateSetDigest,
      responseMode: "archive-response", controlMode: "none", rows: digestPayload })) };
}
