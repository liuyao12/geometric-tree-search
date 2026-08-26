function validPair(pair) {
  return Boolean(pair?.firstId && pair?.secondId && pair.firstId !== pair.secondId);
}

export function validateHypothesisSeparationExperiment(experiment) {
  if (!experiment || experiment.schema !== 1 || !validPair(experiment.pair)) return false;
  if (!["baseline", "ablation"].includes(experiment.arm)) return false;
  if (!["raw", "conditional"].includes(experiment.mode)) return false;
  if (experiment.ablatedTermId !== experiment.pair.firstId
      || experiment.retainedComparisonTermId !== experiment.pair.secondId) return false;
  return Boolean(experiment.sourceCandidateSetDigest && experiment.sourceAuditDigest
    && experiment.targetUsed === false && experiment.coordinatesEmbedded === false
    && experiment.candidateRowsEmbedded === false);
}

export function hypothesisSeparationMultiplier(experiment, termId) {
  if (!validateHypothesisSeparationExperiment(experiment)) return 1;
  return experiment.arm === "ablation" && experiment.ablatedTermId === termId ? 0 : 1;
}

/** Apply the registered arm to score terms only; exact candidates and admission are absent. */
export function applyHypothesisSeparationMultipliers(terms, experiment) {
  if (!Array.isArray(terms)) throw new Error("Score terms must be an array");
  return terms.map((term) => {
    const experimentMultiplier = hypothesisSeparationMultiplier(experiment, term.id);
    return experimentMultiplier === 1 ? { ...term } : { ...term,
      weight: 0,
      contribution: 0,
      experimentMultiplier,
    };
  });
}
