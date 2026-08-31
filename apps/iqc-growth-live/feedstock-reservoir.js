const FACTORS = Object.freeze({ "finite-1": 1, "finite-4": 4, "finite-16": 16 });

function counts(tokens) {
  const result = {};
  for (const token of tokens) result[token] = (result[token] || 0) + 1;
  return Object.fromEntries(Object.entries(result).sort(([a], [b]) => a.localeCompare(b)));
}

export function initializeFeedstockReservoir(referenceSpecies, mode = "open") {
  const referenceCounts = counts(referenceSpecies);
  const factor = FACTORS[mode] || null;
  const initial = factor === null ? null
    : Object.fromEntries(Object.entries(referenceCounts).map(([species, count]) => [species, count * factor]));
  return { mode: factor === null ? "open" : mode, factor, referenceCounts, initial,
    remaining: initial ? { ...initial } : null, consumed: Object.fromEntries(Object.keys(referenceCounts).map((key) => [key, 0])),
    admittedAtoms: 0, rejectedAtoms: 0, targetUsed: false };
}

export function evaluateFeedstockDemand(reservoir, requestedSpecies) {
  const requested = counts(requestedSpecies);
  if (!reservoir || reservoir.mode === "open") return {
    admitted: true, open: true, requested, deficits: {}, remainingAfter: null,
    requestedAtoms: requestedSpecies.length, limitingSpecies: [], targetUsed: false };
  const deficits = {}; const remainingAfter = { ...reservoir.remaining };
  for (const [species, demand] of Object.entries(requested)) {
    const available = remainingAfter[species] || 0;
    if (demand > available) deficits[species] = demand - available;
    remainingAfter[species] = Math.max(0, available - demand);
  }
  return { admitted: Object.keys(deficits).length === 0, open: false, requested, deficits,
    remainingAfter, requestedAtoms: requestedSpecies.length, limitingSpecies: Object.keys(deficits), targetUsed: false };
}

export function consumeFeedstock(reservoir, requestedSpecies) {
  const audit = evaluateFeedstockDemand(reservoir, requestedSpecies);
  if (!audit.admitted) return { reservoir: { ...reservoir,
    rejectedAtoms: reservoir.rejectedAtoms + audit.requestedAtoms }, audit };
  const consumed = { ...reservoir.consumed };
  for (const [species, amount] of Object.entries(audit.requested)) consumed[species] = (consumed[species] || 0) + amount;
  if (audit.open) return { reservoir: { ...reservoir, consumed,
    admittedAtoms: reservoir.admittedAtoms + audit.requestedAtoms }, audit };
  return { reservoir: { ...reservoir, remaining: audit.remainingAfter, consumed,
    admittedAtoms: reservoir.admittedAtoms + audit.requestedAtoms }, audit };
}

export function releaseFeedstock(reservoir, releasedSpecies) {
  const released = counts(releasedSpecies);
  const consumed = { ...reservoir.consumed };
  for (const [species, amount] of Object.entries(released)) {
    if ((consumed[species] || 0) < amount) {
      throw new Error(`cannot return ${amount} ${species} atoms when only ${consumed[species] || 0} were supplied`);
    }
    consumed[species] -= amount;
  }
  if (reservoir.mode === "open") return { reservoir: { ...reservoir, consumed,
    admittedAtoms: Math.max(0, reservoir.admittedAtoms - releasedSpecies.length) },
  audit: { released, releasedAtoms: releasedSpecies.length, open: true, targetUsed: false } };
  const remaining = { ...reservoir.remaining };
  for (const [species, amount] of Object.entries(released)) {
    remaining[species] = (remaining[species] || 0) + amount;
    if (remaining[species] > reservoir.initial[species]) {
      throw new Error(`returned ${species} inventory exceeds the declared finite reservoir`);
    }
  }
  return { reservoir: { ...reservoir, remaining, consumed,
    admittedAtoms: Math.max(0, reservoir.admittedAtoms - releasedSpecies.length) },
  audit: { released, releasedAtoms: releasedSpecies.length, open: false, targetUsed: false } };
}

export function feedstockReservoirSnapshot(reservoir) {
  const finite = reservoir?.mode !== "open";
  const species = Object.keys(reservoir?.referenceCounts || {}).map((symbol) => ({
    symbol, initial: finite ? reservoir.initial[symbol] : null,
    consumed: reservoir.consumed[symbol] || 0,
    remaining: finite ? reservoir.remaining[symbol] : null,
    remainingFraction: finite && reservoir.initial[symbol]
      ? reservoir.remaining[symbol] / reservoir.initial[symbol] : null,
  }));
  return { mode: reservoir?.mode || "open", finite, factor: reservoir?.factor || null,
    admittedAtoms: reservoir?.admittedAtoms || 0, rejectedAtoms: reservoir?.rejectedAtoms || 0,
    initialAtoms: finite ? species.reduce((sum, entry) => sum + entry.initial, 0) : null,
    remainingAtoms: finite ? species.reduce((sum, entry) => sum + entry.remaining, 0) : null,
    species, targetUsed: false, coordinatesEmbedded: false, physicalTimeModeled: false,
    chemicalPotentialInferred: false, fluxInferred: false, diffusionIntegrated: false };
}
