function stableString(value) {
  if (Array.isArray(value)) return `[${value.map(stableString).join(",")}]`;
  if (value && typeof value === "object") return `{${Object.keys(value).sort()
    .map((key) => `${JSON.stringify(key)}:${stableString(value[key])}`).join(",")}}`;
  return JSON.stringify(value);
}

function digest(value) {
  let hash = 2166136261;
  const text = stableString(value);
  for (let index = 0; index < text.length; index += 1) {
    hash ^= text.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}

function finite(value) {
  return Number.isFinite(Number(value)) ? Number(value) : null;
}

function harmonicMean(point, order = 6) {
  const harmonics = point?.orientationalOrder?.harmonics;
  if (Array.isArray(harmonics)) return finite(harmonics.find((entry) => Number(entry?.order) === order)?.mean);
  return finite(harmonics?.[order]?.mean ?? harmonics?.[String(order)]?.mean);
}

function metric(label, unit, baseline, ablation, provenance) {
  const a = finite(baseline);
  const b = finite(ablation);
  return { label, unit, baseline: a, ablation: b,
    delta: a === null || b === null ? null : b - a, provenance };
}

function fail(reason, detail) {
  return { schema: 1, status: "unavailable", comparable: false, reason, detail,
    metrics: [], coordinatesEmbedded: false, targetUsed: false, candidatesPooled: false,
    searchReplayed: false, physicalTimeInferred: false, causalPhysicalMechanismInferred: false };
}

/** Compare a registered score-channel baseline/ablation only at a shared discrete update count. */
export function compareHypothesisSeparationOutcomes(entries) {
  if (!Array.isArray(entries) || entries.length !== 2) return fail("select-two", "Select exactly two saved runs.");
  const manifests = entries.map((entry) => entry?.hypothesisSeparationExperiment);
  if (manifests.some((manifest) => !manifest || manifest.schema !== 1)) {
    return fail("registration-missing", "Both summaries must contain a registered hypothesis-separation manifest.");
  }
  const baselineIndex = manifests.findIndex((manifest) => manifest.arm === "baseline");
  const ablationIndex = manifests.findIndex((manifest) => manifest.arm === "ablation");
  if (baselineIndex < 0 || ablationIndex < 0 || baselineIndex === ablationIndex) {
    return fail("arms-invalid", "The pair must contain one baseline and one ablation arm.");
  }
  const baseline = entries[baselineIndex];
  const ablation = entries[ablationIndex];
  const baselineManifest = manifests[baselineIndex];
  const ablationManifest = manifests[ablationIndex];
  const commonManifest = (manifest) => ({ schema: manifest.schema, pair: manifest.pair,
    ablatedTermId: manifest.ablatedTermId, retainedComparisonTermId: manifest.retainedComparisonTermId,
    mode: manifest.mode, sourceCandidateSetDigest: manifest.sourceCandidateSetDigest,
    sourceAuditDigest: manifest.sourceAuditDigest });
  if (stableString(commonManifest(baselineManifest)) !== stableString(commonManifest(ablationManifest))) {
    return fail("registration-mismatch", "The arms were not registered from the same frozen pair and frontier audit.");
  }
  if (baselineManifest.settingsStillMatch !== true || ablationManifest.settingsStillMatch !== true
      || baselineManifest.inputScenarioStillMatches !== true || ablationManifest.inputScenarioStillMatches !== true) {
    return fail("registration-drift", "At least one saved arm no longer matches its registered settings or scenario.");
  }
  if (!baseline.inputIdentity || baseline.inputIdentity !== ablation.inputIdentity) {
    return fail("input-mismatch", "The observed input scenario and structure SHA-256 must be identical.");
  }
  if (baseline.executionEvidence?.executed !== true || ablation.executionEvidence?.executed !== true) {
    return fail("execution-missing", "Configure is not execute: both registered arms must contain structural-leap evidence.");
  }
  if (baseline.executionEvidence?.targetUsed === true || ablation.executionEvidence?.targetUsed === true
      || baseline.trajectory?.targetUsed === true || ablation.trajectory?.targetUsed === true) {
    return fail("target-tainted", "A target-informed trajectory cannot enter this comparison.");
  }
  const baselineFactors = baseline.interventionFactors || {};
  const ablationFactors = ablation.interventionFactors || {};
  const keys = [...new Set([...Object.keys(baselineFactors), ...Object.keys(ablationFactors)])].sort();
  const changed = keys.filter((key) => baselineFactors[key]?.value !== ablationFactors[key]?.value);
  if (changed.length !== 1 || changed[0] !== "hypothesisSeparation") {
    return fail("controls-mismatch", "Every recorded intervention except the registered hypothesis-separation arm must be byte-identical.");
  }
  if (baseline.trajectory?.historyTruncated === true || ablation.trajectory?.historyTruncated === true) {
    return fail("history-truncated", "A retained-window trajectory cannot certify a common horizon from the supplied seed.");
  }
  const baselineUpdates = Math.max(0, Number(baseline.executionEvidence.structuralLeapEvents) || 0);
  const ablationUpdates = Math.max(0, Number(ablation.executionEvidence.structuralLeapEvents) || 0);
  const commonUpdates = Math.min(baselineUpdates, ablationUpdates);
  const baselinePoints = baseline.trajectory?.points || [];
  const ablationPoints = ablation.trajectory?.points || [];
  if (commonUpdates < 1 || baselinePoints.length <= commonUpdates || ablationPoints.length <= commonUpdates) {
    return fail("horizon-unavailable", "Both complete histories must include at least one common structural update.");
  }
  const baselinePoint = baselinePoints[commonUpdates];
  const ablationPoint = ablationPoints[commonUpdates];
  const metrics = [
    metric("explicit structural sites", "sites", baselinePoint.atoms, ablationPoint.atoms, "trajectory point atom count"),
    metric("placed clusters", "clusters", baselinePoint.clusters, ablationPoint.clusters, "trajectory point cluster count"),
    metric("causal depth", "levels", baselinePoint.depth, ablationPoint.depth, "accepted-parent lineage depth"),
    metric("accepted actions", "actions", baselinePoint.cumulativeAccepted, ablationPoint.cumulativeAccepted, "cumulative accepted search actions"),
    metric("rejected actions", "actions", baselinePoint.cumulativeRejected, ablationPoint.cumulativeRejected, "cumulative rejected search actions"),
    metric("S(q) peak prominence", "ratio", baselinePoint.scattering?.summary?.peakProminence,
      ablationPoint.scattering?.summary?.peakProminence, "unit-weight geometric powder structure factor"),
    metric("mean q₆ / |ψ₆|", "order", harmonicMean(baselinePoint), harmonicMean(ablationPoint),
      "proper-rotation-invariant local orientational order"),
  ];
  const identity = { ...commonManifest(baselineManifest), inputIdentity: baseline.inputIdentity, commonUpdates };
  return { schema: 1, status: "matched", comparable: true, reason: null,
    detail: `Matched after ${commonUpdates} discrete structural update${commonUpdates === 1 ? "" : "s"}.`,
    baselineEntryId: baseline.id, ablationEntryId: ablation.id, commonUpdates,
    baselineUpdates, ablationUpdates, experiment: identity, comparisonDigest: digest({ identity, metrics }), metrics,
    coordinatesEmbedded: false, targetUsed: false, candidatesPooled: false, searchReplayed: false,
    physicalTimeInferred: false, causalPhysicalMechanismInferred: false,
    boundary: "Deltas are responses to an encoded score-term multiplier at a matched discrete search horizon—not physical time, energy, kinetics, removal of a physical interaction, or proof of a causal physical mechanism." };
}
