const finite = (value) => Number.isFinite(Number(value));

function requiredNumber(value, label) {
  if (!finite(value)) throw new TypeError(`${label} must be finite`);
  return Number(value);
}

function normalizedRecord(record, index) {
  const candidateId = typeof record?.candidateId === "string" ? record.candidateId.trim() : "";
  if (!candidateId) throw new TypeError(`kinetic record ${index + 1} needs a candidate ID`);
  const eventDirection = record.eventDirection === "detach" ? "detach" : "attach";
  const log10RatePerSecond = requiredNumber(record.log10RatePerSecond,
    `log10 rate for ${candidateId}`);
  const lower = requiredNumber(record.log10RateLowerPerSecond,
    `lower log10 rate for ${candidateId}`);
  const upper = requiredNumber(record.log10RateUpperPerSecond,
    `upper log10 rate for ${candidateId}`);
  if (lower > log10RatePerSecond || upper < log10RatePerSecond) {
    throw new RangeError(`kinetic uncertainty interval for ${candidateId} must contain its rate`);
  }
  const probability = requiredNumber(record.probabilityWithinFrozenCatalog,
    `catalog probability for ${candidateId}`);
  if (probability < 0 || probability > 1) {
    throw new RangeError(`catalog probability for ${candidateId} must be between zero and one`);
  }
  return {
    candidateId,
    eventDirection,
    barrierElectronVolt: requiredNumber(record.barrierElectronVolt,
      `barrier for ${candidateId}`),
    uncertaintyElectronVolt: requiredNumber(record.uncertaintyElectronVolt,
      `barrier uncertainty for ${candidateId}`),
    attemptFrequencyPerSecond: requiredNumber(record.attemptFrequencyPerSecond,
      `attempt frequency for ${candidateId}`),
    attemptFrequencyUncertaintyLog10: requiredNumber(record.attemptFrequencyUncertaintyLog10,
      `prefactor uncertainty for ${candidateId}`),
    log10RatePerSecond,
    log10RateLowerPerSecond: lower,
    log10RateUpperPerSecond: upper,
    probabilityWithinFrozenCatalog: probability,
  };
}

export function buildKineticEventSpectrum(competition) {
  if (!Array.isArray(competition?.records) || !competition.records.length) {
    throw new TypeError("a kinetic spectrum needs at least one frozen event record");
  }
  const temperatureKelvin = requiredNumber(competition.temperatureKelvin,
    "kinetic-spectrum temperature");
  if (temperatureKelvin < 1 || temperatureKelvin > 5000) {
    throw new RangeError("kinetic-spectrum temperature must be between 1 and 5000 K");
  }
  const records = competition.records.map(normalizedRecord)
    .sort((first, second) => second.log10RatePerSecond - first.log10RatePerSecond
      || first.candidateId.localeCompare(second.candidateId));
  if (new Set(records.map((record) => record.candidateId)).size !== records.length) {
    throw new Error("kinetic-spectrum candidate IDs must be unique");
  }
  const probabilitySum = records.reduce((sum, record) =>
    sum + record.probabilityWithinFrozenCatalog, 0);
  if (Math.abs(probabilitySum - 1) > 1e-6) {
    throw new Error("frozen-catalog kinetic probabilities must sum to one");
  }
  const ranked = records.map((record, index) => ({ ...record, rank: index + 1,
    selected: record.candidateId === competition.selectedCandidateId }));
  const selected = ranked.find((record) => record.selected);
  if (!selected) throw new Error("selected kinetic candidate is absent from the frozen catalog");
  const fastest = ranked[0];
  const uncertaintyCompetitive = ranked.filter((record) =>
    record.log10RateUpperPerSecond >= fastest.log10RateLowerPerSecond);
  const entropyNats = -ranked.reduce((sum, record) => {
    const probability = record.probabilityWithinFrozenCatalog;
    return sum + (probability > 0 ? probability * Math.log(probability) : 0);
  }, 0);
  const probabilityMass = (direction) => ranked.filter((record) =>
    record.eventDirection === direction).reduce((sum, record) =>
    sum + record.probabilityWithinFrozenCatalog, 0);
  const topProbability = fastest.probabilityWithinFrozenCatalog;
  return {
    schema: 1,
    mode: competition.mode,
    temperatureKelvin,
    candidateCount: ranked.length,
    selectedCandidateId: selected.candidateId,
    selectedRank: selected.rank,
    selectedEventDirection: selected.eventDirection,
    selectedProbabilityWithinFrozenCatalog: selected.probabilityWithinFrozenCatalog,
    probabilityMassByDirection: {
      attach: probabilityMass("attach"),
      detach: probabilityMass("detach"),
    },
    entropyNats,
    effectiveCompetingEventCount: Math.exp(entropyNats),
    rateSpanDecades: fastest.log10RatePerSecond
      - ranked[ranked.length - 1].log10RatePerSecond,
    uncertaintyCompetitiveCandidateCount: uncertaintyCompetitive.length,
    fastestCandidateSeparatedByUncertainty: uncertaintyCompetitive.length === 1,
    selectedInsideFastestUncertaintySet: uncertaintyCompetitive.some((record) => record.selected),
    topProbabilityWithinFrozenCatalog: topProbability,
    catalogCharacter: topProbability >= .9 ? "single-event dominated"
      : topProbability >= .5 ? "few-event dominated" : "distributed competition",
    rankedRecords: ranked,
    candidateSetChanged: false,
    selectedEventChanged: false,
    hardAdmissionChanged: false,
    targetUsed: false,
    catalogCompleteBeyondFrozenFrontier: false,
    claimBoundary: "The spectrum resolves rates and uncertainty only inside this exact frozen, hard-admitted event catalog. It does not add missing diffusion, reconstruction, concerted, nucleation, or desorption mechanisms and cannot promote a candidate into the catalog.",
  };
}
