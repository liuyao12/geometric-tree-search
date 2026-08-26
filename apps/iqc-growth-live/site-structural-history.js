function rounded(value, digits = 5) {
  if (!Number.isFinite(value)) return null;
  const scale = 10 ** digits;
  return Math.round(value * scale) / scale;
}

function stateSignature(record) {
  return JSON.stringify([
    record.persistentNeighborCount, record.lostNeighborCount, record.gainedNeighborCount,
    rounded(record.centerDisplacementAngstrom), rounded(record.radialRmsAngstrom),
    rounded(record.rootD2MinAngstrom), rounded(record.equivalentShearStrain),
    rounded(record.localVolumeChangeFraction),
  ]);
}

/** Retain only changed, ordered local structural states in a bounded per-site history. */
export function appendSiteStructuralHistory(history, record, maximumRecords = 24) {
  if (!Array.isArray(history) || !Number.isInteger(record?.leapIndex) || record.leapIndex < 1
      || typeof record.label !== "string" || typeof record.persistentNeighborCount !== "number"
      || typeof record.lostNeighborCount !== "number" || typeof record.gainedNeighborCount !== "number"
      || maximumRecords < 2) throw new Error("site structural history needs an ordered finite leap record");
  const normalized = { ...record,
    centerDisplacementAngstrom: rounded(record.centerDisplacementAngstrom),
    radialRmsAngstrom: rounded(record.radialRmsAngstrom),
    rootD2MinAngstrom: rounded(record.rootD2MinAngstrom),
    normalizedRootD2Min: rounded(record.normalizedRootD2Min),
    equivalentShearStrain: rounded(record.equivalentShearStrain),
    localVolumeChangeFraction: rounded(record.localVolumeChangeFraction),
    targetUsed: false, physicalTimeModeled: false, dynamicsIntegrated: false,
  };
  const ordered = history.filter((entry) => entry.leapIndex < normalized.leapIndex);
  const previous = ordered.at(-1);
  if (previous && stateSignature(previous) === stateSignature(normalized)) return ordered.slice(-maximumRecords);
  return [...ordered, normalized].slice(-maximumRecords);
}

export function summarizeSiteStructuralHistory(history) {
  if (!Array.isArray(history) || !history.length) return {
    available: false, records: 0, changedLeaps: 0, targetUsed: false,
  };
  const finite = (key) => history.map((record) => record[key]).filter(Number.isFinite);
  const shellChanged = history.filter((record) => record.lostNeighborCount || record.gainedNeighborCount).length;
  return {
    available: true, records: history.length,
    firstLeap: history[0].leapIndex, lastLeap: history.at(-1).leapIndex,
    shellChangedLeaps: shellChanged,
    maximumCenterDisplacementAngstrom: Math.max(0, ...finite("centerDisplacementAngstrom")),
    maximumRadialRmsAngstrom: Math.max(0, ...finite("radialRmsAngstrom")),
    maximumRootD2MinAngstrom: Math.max(0, ...finite("rootD2MinAngstrom")),
    maximumGainedNeighbors: Math.max(0, ...history.map((record) => record.gainedNeighborCount)),
    maximumLostNeighbors: Math.max(0, ...history.map((record) => record.lostNeighborCount)),
    historyTruncated: history[0].leapIndex > 1,
    targetUsed: false, physicalTimeModeled: false, dynamicsIntegrated: false,
  };
}
