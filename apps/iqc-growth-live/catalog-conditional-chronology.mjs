function finite(value, label, { nonnegative = false } = {}) {
  const number = Number(value);
  if (!Number.isFinite(number) || (nonnegative && number < 0)) {
    throw new TypeError(`${label} must be ${nonnegative ? "finite and nonnegative" : "finite"}`);
  }
  return number;
}

function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === "object") return Object.fromEntries(Object.keys(value).sort()
    .map((key) => [key, canonical(value[key])]));
  return value;
}

export function chronologyFingerprint(value) {
  const source = JSON.stringify(canonical(value));
  let hash = 0x811c9dc5;
  for (let index = 0; index < source.length; index += 1) {
    hash ^= source.charCodeAt(index); hash = Math.imul(hash, 0x01000193) >>> 0;
  }
  return hash.toString(16).padStart(8, "0");
}

function clockedRecord(leap, retainedIndex) {
  const kinetic = leap?.actionBarrierCheckpoint?.kineticCompetition;
  if (!kinetic?.committed || kinetic.mode !== "seeded-kmc") return null;
  if (leap?.status !== "accepted") throw new Error("a clocked event must be an accepted structural leap");
  const clockBeforeSeconds = finite(kinetic.clockBeforeSeconds, "clock before", { nonnegative: true });
  const clockAfterSeconds = finite(kinetic.clockAfterSeconds, "clock after", { nonnegative: true });
  const waitingTimeSeconds = finite(kinetic.waitingTimeSeconds, "waiting time", { nonnegative: true });
  if (clockAfterSeconds + 1e-15 < clockBeforeSeconds
      || Math.abs((clockBeforeSeconds + waitingTimeSeconds) - clockAfterSeconds)
        > Math.max(1e-12, Math.abs(clockAfterSeconds) * 1e-9)) {
    throw new Error("catalog-conditional clock increment is inconsistent");
  }
  const eventCountBefore = Number(kinetic.eventCountBefore);
  const eventCountAfter = Number(kinetic.eventCountAfter);
  if (!Number.isInteger(eventCountBefore) || !Number.isInteger(eventCountAfter)
      || eventCountAfter !== eventCountBefore + 1) throw new Error("clocked event count must increment by one");
  const atomsBefore = Math.max(0, Number(leap?.before?.atoms) || 0);
  const atomsAfter = Math.max(0, Number(leap?.after?.atoms) || atomsBefore);
  const probability = finite(kinetic.selectedProbabilityWithinFrozenCatalog,
    "selected catalog probability", { nonnegative: true });
  if (probability > 1) throw new Error("selected catalog probability cannot exceed one");
  const temperatureKelvin = finite(kinetic.temperatureKelvin, "temperature");
  if (temperatureKelvin <= 0) throw new Error("temperature must be positive");
  const candidateCount = Number(kinetic.candidateCount);
  if (!Number.isInteger(candidateCount) || candidateCount < 1) {
    throw new Error("a clocked event requires a nonempty frozen candidate catalog");
  }
  return { retainedIndex, leapIndex: Number(leap.index) || retainedIndex + 1,
    label: leap.label || "seeded KMC structural leap", candidateId: kinetic.selectedCandidateId || null,
    eventDirection: kinetic.selectedEventDirection || "unknown", temperatureKelvin,
    clockBeforeSeconds, clockAfterSeconds, waitingTimeSeconds,
    eventCountBefore, eventCountAfter, atomsBefore, atomsAfter, atomDelta: atomsAfter - atomsBefore,
    selectedProbabilityWithinFrozenCatalog: probability,
    selectedLog10RatePerSecond: finite(kinetic.selectedLog10RatePerSecond, "selected log rate"),
    log10TotalRatePerSecond: finite(kinetic.log10TotalRatePerSecond, "total log rate"),
    candidateCount,
    catalogScope: kinetic.catalogScope || "requested-hard-admitted-actions-only" };
}

export function buildCatalogConditionalChronology(structuralLeaps = [], options = {}) {
  if (!Array.isArray(structuralLeaps)) throw new TypeError("structural leaps must be an array");
  const records = structuralLeaps.map(clockedRecord).filter(Boolean);
  for (let index = 1; index < records.length; index += 1) {
    if (Math.abs(records[index].clockBeforeSeconds - records[index - 1].clockAfterSeconds)
        > Math.max(1e-12, Math.abs(records[index].clockBeforeSeconds) * 1e-9)) {
      throw new Error("retained clocked events do not form a continuous conditional clock");
    }
  }
  const accepted = structuralLeaps.filter((leap) => leap?.status === "accepted");
  const unclockedAcceptedLeaps = accepted.length - records.length;
  const elapsedSeconds = records.length ? records.at(-1).clockAfterSeconds : 0;
  const retainedClockStartSeconds = records.length ? records[0].clockBeforeSeconds : 0;
  const retainedWaitingSpanSeconds = records.length ? elapsedSeconds - retainedClockStartSeconds : 0;
  const structuralAtomAdvance = records.reduce((sum, record) => sum + record.atomDelta, 0);
  const totalLeapEvents = Math.max(structuralLeaps.length, Number(options.totalLeapEvents) || 0);
  const historyTruncated = totalLeapEvents > structuralLeaps.length;
  const core = { schema: 1, available: records.length > 0, records, clockedEvents: records.length,
    unclockedAcceptedLeaps, totalRetainedLeaps: structuralLeaps.length, totalLeapEvents, historyTruncated,
    elapsedSeconds, retainedClockStartSeconds, retainedWaitingSpanSeconds, structuralAtomAdvance,
    physicalScope: "finite enumerated catalog conditional", targetUsed: false,
    completeMechanismCatalogClaimed: false, unconditionalMaterialTimeClaimed: false,
    bulkGrowthRateClaimed: false, dynamicalTrajectoryIntegrated: false, computationalSpeedupClaimed: false };
  return { ...core, chronologyFingerprint: chronologyFingerprint(core),
    claimBoundary: records.length
      ? "Elapsed time is the sum of seeded exponential waiting-time draws from successive finite, frozen, hard-admitted action catalogs. Missing mechanisms and unclocked structural leaps are not assigned time, so this is not an unconditional material clock or bulk growth rate."
      : "No committed structural leap has both a complete frozen-frontier barrier/prefactor response and a seeded KMC waiting-time draw. Browser duration and geometric leap count are not physical time." };
}
