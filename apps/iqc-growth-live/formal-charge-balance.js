function resolveCharges(tokens, chargeForToken) {
  const charges = tokens.map((token) => chargeForToken(token));
  return {
    charges,
    known: charges.filter((charge) => Number.isFinite(charge)).length,
    complete: charges.every((charge) => Number.isFinite(charge)),
  };
}

function sum(values) {
  return values.reduce((total, value) => total + value, 0);
}

/**
 * Learn the formal-charge density supplied by one observed configuration.
 * Charges are metadata channels (including occupancy-weighted mixed valence),
 * not inferred oxidation states and not an electrostatic potential.
 */
export function learnFormalChargeTarget(tokens, chargeForToken) {
  if (!Array.isArray(tokens) || !tokens.length) throw new Error("formal-charge target requires site tokens");
  if (typeof chargeForToken !== "function") throw new Error("formal-charge target requires a token resolver");
  const resolved = resolveCharges(tokens, chargeForToken);
  const knownCharges = resolved.charges.filter((charge) => Number.isFinite(charge));
  const netFormalCharge = sum(knownCharges);
  return {
    available: resolved.complete,
    observations: tokens.length,
    resolvedObservations: resolved.known,
    coverage: resolved.known / tokens.length,
    netFormalCharge,
    meanFormalCharge: resolved.complete ? netFormalCharge / tokens.length : null,
    maximumAbsoluteSiteCharge: knownCharges.length ? Math.max(...knownCharges.map(Math.abs), 1) : 1,
    source: "supplied formal oxidation states",
  };
}

function unavailable(target, added, reason) {
  return {
    available: false,
    reason,
    before: 0,
    after: 0,
    delta: 0,
    scaledDelta: 0,
    currentNetFormalCharge: null,
    freshNetFormalCharge: null,
    projectedNetFormalCharge: null,
    projectedMeanFormalCharge: null,
    referenceMeanFormalCharge: target?.meanFormalCharge ?? null,
    added,
  };
}

/**
 * Rank an unchanged exact action by whether its formal-charge density moves a
 * finite frontier toward the observed reference density. This remains soft:
 * charged surfaces and intermediate fronts are allowed, and no Coulomb,
 * dielectric, redox, electron-transfer, or chemical-potential term is used.
 */
export function formalChargeBalanceDelta(currentTokens, freshTokens, target, chargeForToken) {
  if (!target?.available) return unavailable(target, freshTokens.length, "reference formal charge is incomplete");
  if (!freshTokens.length) return unavailable(target, 0, "candidate adds no sites");
  const current = resolveCharges(currentTokens, chargeForToken);
  const fresh = resolveCharges(freshTokens, chargeForToken);
  if (!current.complete || !fresh.complete) return unavailable(target, freshTokens.length, "frontier formal charge is incomplete");
  const currentNet = sum(current.charges);
  const freshNet = sum(fresh.charges);
  const projectedCount = currentTokens.length + freshTokens.length;
  const projectedNet = currentNet + freshNet;
  const reference = target.meanFormalCharge;
  const normalization = Math.max(1, target.maximumAbsoluteSiteCharge);
  const beforeMean = currentTokens.length ? currentNet / currentTokens.length : reference;
  const projectedMean = projectedNet / projectedCount;
  const before = Math.abs(beforeMean - reference) / normalization;
  const after = Math.abs(projectedMean - reference) / normalization;
  return {
    available: true,
    reason: "complete supplied formal-charge channel",
    before,
    after,
    delta: after - before,
    scaledDelta: (after - before) * Math.sqrt(Math.max(1, projectedCount)),
    currentNetFormalCharge: currentNet,
    freshNetFormalCharge: freshNet,
    projectedNetFormalCharge: projectedNet,
    projectedMeanFormalCharge: projectedMean,
    referenceMeanFormalCharge: reference,
    added: freshTokens.length,
  };
}
