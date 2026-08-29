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

const RESPONSE_DOMAIN_DEFINITIONS = [
  { id: "extent", label: "material extent", metricLabels: [
    "explicit structural sites", "placed clusters", "causal depth"],
    question: "How much explicit geometric material and lineage depth exist at the matched horizon?" },
  { id: "search", label: "search work", metricLabels: [
    "frontier actions", "accepted actions", "rejected actions"],
    question: "How did the omission alter the finite candidate frontier and retained/pruned decisions?" },
  { id: "order", label: "structural order", metricLabels: [
    "S(q) peak prominence", "mean q₆ / |ψ₆|"],
    question: "How did reciprocal and local orientational order change at the same update count?" },
];

function symmetricResponse(metricRecord) {
  if (metricRecord?.delta === null || metricRecord?.baseline === null
      || metricRecord?.ablation === null) return null;
  const scale = Math.abs(metricRecord.baseline) + Math.abs(metricRecord.ablation);
  if (scale <= 1e-12) return 0;
  return Math.max(-1, Math.min(1, metricRecord.delta / scale));
}

/** Condense unit-bearing matched deltas without assigning energy, favorability, or causality. */
export function buildPhysicsProtocolResponseFingerprint(audit) {
  if (audit?.comparable !== true || !Array.isArray(audit.metrics)) {
    return { schema: 1, available: false, responseObserved: false, domains: [],
      dominantDomainId: null, responseDigest: null,
      interpretation: "A receipt-verified baseline and Arm B pair is required.",
      physicalTimeInferred: false, causalPhysicalMechanismInferred: false };
  }
  const domains = RESPONSE_DOMAIN_DEFINITIONS.map((definition) => {
    const records = definition.metricLabels.map((label) =>
      audit.metrics.find((record) => record.label === label)).filter(Boolean);
    const resolved = records.map((record) => ({ ...record,
      normalizedResponse: symmetricResponse(record) }))
      .filter((record) => record.normalizedResponse !== null);
    const signedMean = resolved.length
      ? resolved.reduce((sum, record) => sum + record.normalizedResponse, 0) / resolved.length : null;
    const rmsMagnitude = resolved.length ? Math.sqrt(resolved.reduce((sum, record) =>
      sum + record.normalizedResponse ** 2, 0) / resolved.length) : null;
    const dominant = resolved.slice().sort((a, b) =>
      Math.abs(b.normalizedResponse) - Math.abs(a.normalizedResponse))[0] || null;
    return { id: definition.id, label: definition.label, question: definition.question,
      resolvedMetrics: resolved.length, metricCount: records.length,
      coverage: records.length ? resolved.length / records.length : 0,
      signedMean, rmsMagnitude, dominantMetric: dominant ? {
        label: dominant.label, unit: dominant.unit, baseline: dominant.baseline,
        ablation: dominant.ablation, delta: dominant.delta,
        normalizedResponse: dominant.normalizedResponse, provenance: dominant.provenance } : null };
  });
  const ranked = domains.filter((domain) => domain.rmsMagnitude !== null)
    .sort((a, b) => b.rmsMagnitude - a.rmsMagnitude);
  const responseObserved = audit.metrics.some((record) => record.delta !== null
    && Math.abs(record.delta) > 1e-12);
  const dominantDomainId = ranked[0]?.id || null;
  const payload = { commonUpdates: audit.commonUpdates, responseObserved,
    candidateGate: audit.candidateIdentity?.gate || null,
    domains: domains.map(({ id, coverage, signedMean, rmsMagnitude, dominantMetric }) =>
      ({ id, coverage, signedMean, rmsMagnitude, dominantMetric })) };
  return { schema: 1, available: true, responseObserved, domains, dominantDomainId,
    responseDigest: digest(payload),
    interpretation: responseObserved
      ? `Arm B changes at least one retained geometric observable after ${audit.commonUpdates} matched structural update${audit.commonUpdates === 1 ? "" : "s"}. The registered layer is algorithmically consequential for this supplied seed and horizon.`
      : `No retained geometric observable differs after ${audit.commonUpdates} matched structural update${audit.commonUpdates === 1 ? "" : "s"}. This finite null response does not establish physical irrelevance.`,
    normalization: "signed (Arm B − baseline) / (|Arm B| + |baseline|), evaluated per observable; domain magnitude is RMS and sign is reported separately",
    favorableDirectionAssigned: false, coordinatesEmbedded: false, targetUsed: false,
    physicalTimeInferred: false, causalPhysicalMechanismInferred: false };
}

function fail(reason, detail, evidence = {}) {
  return { schema: 1, status: "unavailable", comparable: false, reason, detail,
    experiment: null, metrics: [], candidateIdentity: null, changedControlIds: [],
    coordinatesEmbedded: false, targetUsed: false, candidatesPooled: false,
    searchReplayed: false, physicalTimeInferred: false,
    causalPhysicalMechanismInferred: false, ...evidence };
}

function commonPlan(plan) {
  return {
    schema: plan?.schema,
    ablatedRecordId: plan?.ablatedRecordId,
    ablatedProcess: plan?.ablatedProcess,
    comparisonMode: plan?.comparisonMode,
    changedExecutionObjects: plan?.changedExecutionObjects,
    baselineSelectedRecordIds: plan?.baselineSelectedRecordIds,
    ablationSelectedRecordIds: plan?.ablationSelectedRecordIds,
    candidateSetMustRemainIdentical: plan?.candidateSetMustRemainIdentical,
    candidateSetMayChange: plan?.candidateSetMayChange,
    initialStateMayChange: plan?.initialStateMayChange,
    candidateIdentityGate: plan?.candidateIdentityGate,
    controlBinding: plan?.controlBinding ? {
      schema: plan.controlBinding.schema,
      recordId: plan.controlBinding.recordId,
      controlId: plan.controlBinding.controlId,
      interventionKind: plan.controlBinding.interventionKind,
      baselineValue: plan.controlBinding.baselineValue,
      ablationValue: plan.controlBinding.ablationValue,
      affectedRecordIds: plan.controlBinding.affectedRecordIds,
      selectedAffectedRecordIds: plan.controlBinding.selectedAffectedRecordIds,
      exactlyOneControlChanges: plan.controlBinding.exactlyOneControlChanges,
      changedControlIds: plan.controlBinding.changedControlIds,
    } : null,
  };
}

function controlVectorChanges(baseline, ablation) {
  const a = baseline?.physicsProtocolExperiment?.controlVector;
  const b = ablation?.physicsProtocolExperiment?.controlVector;
  if (a?.schema !== 1 || b?.schema !== 1 || !a.values || !b.values) return null;
  const aKeys = Object.keys(a.values).sort();
  const bKeys = Object.keys(b.values).sort();
  if (stableString(aKeys) !== stableString(bKeys)) return null;
  return aKeys.filter((key) => a.values[key] !== b.values[key]);
}

/** Validate and compare one frozen physics-layer baseline/ablation pair. */
export function comparePhysicsProtocolOutcomes(entries) {
  if (!Array.isArray(entries) || entries.length !== 2) return fail("select-two", "Select exactly two saved runs.");
  const experiments = entries.map((entry) => entry?.physicsProtocolExperiment);
  if (experiments.some((experiment) => experiment?.schema !== 1)) {
    return fail("registration-missing", "Both summaries must contain a frozen physics-protocol arm registration.");
  }
  const arms = experiments.map((experiment) => experiment.armRegistration?.activeArm);
  const baselineIndex = arms.indexOf("baseline");
  const ablationIndex = arms.indexOf("ablation");
  if (baselineIndex < 0 || ablationIndex < 0 || baselineIndex === ablationIndex) {
    return fail("arms-invalid", "The pair must contain one baseline arm and one Arm B omission.");
  }
  const baseline = entries[baselineIndex];
  const ablation = entries[ablationIndex];
  const baselineExperiment = experiments[baselineIndex];
  const ablationExperiment = experiments[ablationIndex];
  const baselinePlan = baselineExperiment.interventionPlan;
  const ablationPlan = ablationExperiment.interventionPlan;
  if ([baselineExperiment, ablationExperiment].some((experiment) =>
    Number(experiment.preflightManifestSchema) < 4
      || experiment.frozenBeforeFirstStructuralAction !== true
      || experiment.targetUsed !== false
      || experiment.controlVector?.capturedBeforeCandidateEnumeration !== true
      || experiment.controlVector?.candidateSetInspected !== false
      || experiment.controlVector?.targetUsed !== false)) {
    return fail("preflight-not-frozen",
      "Both arm manifests and complete control vectors must be frozen before the first structural action.");
  }
  if (stableString(commonPlan(baselinePlan)) !== stableString(commonPlan(ablationPlan))) {
    return fail("registration-mismatch", "The arms do not share the same frozen omission plan and candidate-identity gate.");
  }
  const plan = commonPlan(baselinePlan);
  const baselineRegistration = baselineExperiment.armRegistration;
  const ablationRegistration = ablationExperiment.armRegistration;
  const registrationsValid = [baselineRegistration, ablationRegistration].every((registration) =>
    registration?.schema === 1 && registration.controlValueMatchesActiveArm === true
      && registration.exactlyOneControlChanges === true
      && registration.controlId === plan.controlBinding?.controlId
      && stableString(registration.changedControlIds) === stableString(plan.controlBinding?.changedControlIds)
      && Array.isArray(registration.activeSelectedRecordIds)
      && registration.configuredBeforeCandidateEnumeration === true
      && registration.candidateSetInspected === false && registration.targetUsed === false);
  if (!registrationsValid) {
    return fail("registration-drift", "An arm was not verified at its registered control value before candidate enumeration.");
  }
  const expectedBaseline = [...(plan.baselineSelectedRecordIds || [])].sort();
  const expectedAblation = [...(plan.ablationSelectedRecordIds || [])].sort();
  if (stableString([...baselineRegistration.activeSelectedRecordIds].sort()) !== stableString(expectedBaseline)
      || stableString([...ablationRegistration.activeSelectedRecordIds].sort()) !== stableString(expectedAblation)) {
    return fail("active-layers-mismatch", "The active physics layers do not match the registered baseline and omission sets.");
  }
  if (!baseline.inputIdentity || baseline.inputIdentity !== ablation.inputIdentity) {
    return fail("input-mismatch", "The observed scenario and structure SHA-256 must be identical.");
  }
  const baselineSeedDigest = baseline.executionEvidence?.seedConfigurationDigest || null;
  const ablationSeedDigest = ablation.executionEvidence?.seedConfigurationDigest || null;
  if (!plan.initialStateMayChange && (!baselineSeedDigest || baselineSeedDigest !== ablationSeedDigest
      || baseline.executionEvidence?.seedTargetUsed !== false
      || ablation.executionEvidence?.seedTargetUsed !== false)) {
    return fail("seed-mismatch",
      "Both arms must begin from one identical target-free frozen seed configuration.",
      { seedIdentity: { baselineDigest: baselineSeedDigest, ablationDigest: ablationSeedDigest,
        passed: false } });
  }
  const firstBoundary = baseline.interventionFactors?.boundary?.value;
  const secondBoundary = ablation.interventionFactors?.boundary?.value;
  if (!firstBoundary || firstBoundary !== secondBoundary) {
    return fail("boundary-mismatch", "Both arms must use the same recorded public external boundary.");
  }
  const changedControlIds = controlVectorChanges(baseline, ablation);
  const expectedControlId = plan.controlBinding?.controlId;
  if (!changedControlIds) {
    return fail("control-vector-missing", "Both runs must retain the same complete reversible-control schema.");
  }
  if (changedControlIds.length !== 1 || changedControlIds[0] !== expectedControlId) {
    return fail("controls-mismatch", "Exactly the registered physics control—and no other reversible control—may differ.",
      { changedControlIds });
  }
  const baselineValues = baselineExperiment.controlVector.values;
  const ablationValues = ablationExperiment.controlVector.values;
  if (baselineValues[expectedControlId] !== plan.controlBinding.baselineValue
      || ablationValues[expectedControlId] !== plan.controlBinding.ablationValue) {
    return fail("control-values-mismatch", "The frozen control vector does not contain the registered baseline and omission values.",
      { changedControlIds });
  }
  if (baseline.executionEvidence?.executed !== true || ablation.executionEvidence?.executed !== true) {
    return fail("execution-missing", "Configure is not execute: both arms need at least one structural-leap event.");
  }
  if (baseline.executionEvidence?.targetUsed === true || ablation.executionEvidence?.targetUsed === true
      || baseline.trajectory?.targetUsed === true || ablation.trajectory?.targetUsed === true) {
    return fail("target-tainted", "A target-informed trajectory cannot enter a physics omission comparison.");
  }
  if (baseline.trajectory?.historyTruncated === true || ablation.trajectory?.historyTruncated === true) {
    return fail("history-truncated", "A retained-window history cannot certify a common horizon from the supplied seed.");
  }

  const baselineCandidateDigest = baseline.executionEvidence?.firstFrontierCandidateSetDigest || null;
  const ablationCandidateDigest = ablation.executionEvidence?.firstFrontierCandidateSetDigest || null;
  let candidateIdentity;
  if (plan.candidateSetMustRemainIdentical) {
    if (baseline.executionEvidence?.firstFrontierTargetUsed !== false
        || ablation.executionEvidence?.firstFrontierTargetUsed !== false) {
      return fail("candidate-frontier-target-tainted",
        "The first evaluated frontier used supplied known-window replay; save arms from a target-free continuation protocol.",
        { changedControlIds, candidateIdentity: { gate: "identical", passed: false,
          baselineDigest: baselineCandidateDigest, ablationDigest: ablationCandidateDigest,
          digestIsOutcome: false } });
    }
    if (!baselineCandidateDigest || !ablationCandidateDigest) {
      return fail("candidate-digest-missing",
        "This ranking/order intervention requires both first-frontier candidate digests.",
        { changedControlIds });
    }
    if (baselineCandidateDigest !== ablationCandidateDigest) {
      return fail("candidate-identity-mismatch",
        "This ranking/order intervention requires identical target-free first-frontier candidate digests.",
        { changedControlIds, candidateIdentity: { gate: "identical", passed: false,
          baselineDigest: baselineCandidateDigest, ablationDigest: ablationCandidateDigest,
          digestIsOutcome: false } });
    }
    candidateIdentity = { gate: "identical", passed: true, baselineDigest: baselineCandidateDigest,
      ablationDigest: ablationCandidateDigest, digestIsOutcome: false };
  } else if (plan.initialStateMayChange) {
    return fail("seed-identity-unavailable",
      "This initial-state intervention needs a frozen seed digest before a matched response can be certified.",
      { changedControlIds });
  } else {
    candidateIdentity = { gate: "response", passed: true, baselineDigest: baselineCandidateDigest,
      ablationDigest: ablationCandidateDigest, digestIsOutcome: true };
  }

  const baselineUpdates = Math.max(0, Number(baseline.executionEvidence.structuralLeapEvents) || 0);
  const ablationUpdates = Math.max(0, Number(ablation.executionEvidence.structuralLeapEvents) || 0);
  const commonUpdates = Math.min(baselineUpdates, ablationUpdates);
  const baselinePoints = baseline.trajectory?.points || [];
  const ablationPoints = ablation.trajectory?.points || [];
  if (commonUpdates < 1 || baselinePoints.length <= commonUpdates || ablationPoints.length <= commonUpdates) {
    return fail("horizon-unavailable", "Both complete histories must retain at least one common structural update.",
      { changedControlIds, candidateIdentity });
  }
  const baselinePoint = baselinePoints[commonUpdates];
  const ablationPoint = ablationPoints[commonUpdates];
  const metrics = [
    metric("explicit structural sites", "sites", baselinePoint.atoms, ablationPoint.atoms, "trajectory point atom count"),
    metric("placed clusters", "clusters", baselinePoint.clusters, ablationPoint.clusters, "trajectory point cluster count"),
    metric("frontier actions", "actions", baselinePoint.frontier, ablationPoint.frontier, "pre-update frozen frontier action count"),
    metric("causal depth", "levels", baselinePoint.depth, ablationPoint.depth, "accepted-parent lineage depth"),
    metric("accepted actions", "actions", baselinePoint.cumulativeAccepted, ablationPoint.cumulativeAccepted, "cumulative accepted search actions"),
    metric("rejected actions", "actions", baselinePoint.cumulativeRejected, ablationPoint.cumulativeRejected, "cumulative rejected search actions"),
    metric("S(q) peak prominence", "ratio", baselinePoint.scattering?.summary?.peakProminence,
      ablationPoint.scattering?.summary?.peakProminence, "unit-weight geometric powder structure factor"),
    metric("mean q₆ / |ψ₆|", "order", harmonicMean(baselinePoint), harmonicMean(ablationPoint),
      "proper-rotation-invariant local orientational order"),
  ];
  const experiment = { ...plan, inputIdentity: baseline.inputIdentity,
    seedConfigurationDigest: baselineSeedDigest, commonUpdates,
    controlVectorSchema: baselineExperiment.controlVector.schema };
  const result = { schema: 1, status: "matched", comparable: true, reason: null,
    detail: `Matched ${plan.ablatedProcess} omission after ${commonUpdates} discrete structural update${commonUpdates === 1 ? "" : "s"}.`,
    baselineEntryId: baseline.id, ablationEntryId: ablation.id, baselineUpdates, ablationUpdates,
    commonUpdates, experiment, candidateIdentity,
    seedIdentity: { baselineDigest: baselineSeedDigest, ablationDigest: ablationSeedDigest,
      passed: !plan.initialStateMayChange && baselineSeedDigest === ablationSeedDigest },
    changedControlIds,
    comparisonDigest: digest({ experiment, candidateIdentity, metrics }), metrics,
    coordinatesEmbedded: false, targetUsed: false, candidatesPooled: false, searchReplayed: false,
    physicalTimeInferred: false, causalPhysicalMechanismInferred: false,
    boundary: "This is a deterministic geometric omission response on one supplied configuration at a matched structural-update horizon. It is not physical time, energy, kinetics, removal of a real interaction, an independent-specimen estimate, or proof of a causal physical mechanism." };
  result.responseFingerprint = buildPhysicsProtocolResponseFingerprint(result);
  return result;
}

function compactArmRun(entry) {
  const experiment = entry?.physicsProtocolExperiment;
  return {
    entryId: entry?.id || null,
    arm: experiment?.armRegistration?.activeArm || null,
    executed: entry?.executionEvidence?.executed === true,
    structuralLeapEvents: Math.max(0,
      Number(entry?.executionEvidence?.structuralLeapEvents) || 0),
    inputIdentity: entry?.inputIdentity || null,
    receiptSha256: entry?.receiptSha256 || null,
    targetUsed: entry?.executionEvidence?.targetUsed === true
      || entry?.trajectory?.targetUsed === true,
  };
}

/** Summarize the live register -> baseline -> Arm B -> compare workflow without executing it. */
export function buildPhysicsProtocolPairProgress(protocol, entries, options = {}) {
  const savedEntries = Array.isArray(entries) ? entries : [];
  const plan = protocol?.interventionPlan || null;
  const registrationReady = Boolean(plan?.armConfigurationReady);
  const activeArm = protocol?.armRegistration?.activeArm || null;
  const currentStructuralLeapEvents = Math.max(0,
    Number(options.currentStructuralLeapEvents) || 0);
  const currentScenarioId = options.currentScenarioId || null;
  const currentSeedConfigurationDigest = options.currentSeedConfigurationDigest || null;
  if (!plan) {
    return { schema: 1, state: "registration-required", registrationReady: false,
      activeArm, baselineRuns: [], ablationRuns: [], matchedPairs: [],
      selectedEntryIds: [], nextAction: "Register one reversible physical layer first.",
      steps: [
        { id: "register", label: "register", complete: false, active: true },
        { id: "baseline", label: "baseline", complete: false, active: false },
        { id: "ablation", label: "Arm B", complete: false, active: false },
        { id: "compare", label: "compare", complete: false, active: false },
      ],
      targetUsed: false, candidatesInspected: false };
  }
  const planKey = stableString(commonPlan(plan));
  const matching = savedEntries.filter((entry) => {
    const experiment = entry?.physicsProtocolExperiment;
    return experiment?.schema === 1
      && stableString(commonPlan(experiment.interventionPlan)) === planKey
      && (!currentScenarioId || entry?.scenarioId === currentScenarioId)
      && (!currentSeedConfigurationDigest
        || entry?.executionEvidence?.seedConfigurationDigest === currentSeedConfigurationDigest);
  });
  const baselineEntries = matching.filter((entry) =>
    entry.physicsProtocolExperiment.armRegistration?.activeArm === "baseline");
  const ablationEntries = matching.filter((entry) =>
    entry.physicsProtocolExperiment.armRegistration?.activeArm === "ablation");
  const baselineRuns = baselineEntries.map(compactArmRun);
  const ablationRuns = ablationEntries.map(compactArmRun);
  const evaluatedPairs = baselineEntries.flatMap((baseline) => ablationEntries.map((ablation) => ({
    baseline,
    ablation,
    audit: comparePhysicsProtocolOutcomes([baseline, ablation]),
  })));
  const matchedPairs = evaluatedPairs.filter((pair) => pair.audit.comparable).map((pair) => ({
    baselineEntryId: pair.baseline.id,
    ablationEntryId: pair.ablation.id,
    commonUpdates: pair.audit.commonUpdates,
    comparisonDigest: pair.audit.comparisonDigest,
  }));
  const latestAttempt = evaluatedPairs.at(-1)?.audit || null;
  const executedBaseline = baselineRuns.some((run) => run.executed && !run.targetUsed);
  const executedAblation = ablationRuns.some((run) => run.executed && !run.targetUsed);
  let state;
  let nextAction;
  if (!registrationReady) {
    state = "configuration-required";
    nextAction = "Choose an active reversible setting before registering its neutral arm.";
  } else if (!activeArm) {
    state = "choose-baseline";
    nextAction = "Configure Baseline before the first structural action.";
  } else if (!executedBaseline) {
    state = activeArm === "baseline" ? "run-baseline" : "baseline-missing";
    nextAction = activeArm === "baseline"
      ? currentStructuralLeapEvents ? "Save the executed Baseline arm." : "Run at least one structural leap, then save Baseline."
      : "Return to Baseline, execute at least one structural leap, and save it before Arm B.";
  } else if (!executedAblation) {
    state = activeArm === "ablation" ? "run-ablation" : "configure-ablation";
    nextAction = activeArm === "ablation"
      ? currentStructuralLeapEvents ? "Save the executed Arm B omission." : "Run at least one structural leap, then save Arm B."
      : "Reset to the supplied state and configure Arm B.";
  } else if (matchedPairs.length) {
    state = "matched";
    nextAction = "Open the receipt-verified matched outcome in the experiment notebook.";
  } else {
    state = "comparison-blocked";
    nextAction = latestAttempt?.detail || "Saved arms exist, but the comparability gate is closed.";
  }
  const selectedPair = matchedPairs.at(-1) || null;
  return {
    schema: 1,
    state,
    registrationReady,
    activeArm,
    currentStructuralLeapEvents,
    baselineRuns,
    ablationRuns,
    matchedPairs,
    selectedEntryIds: selectedPair
      ? [selectedPair.baselineEntryId, selectedPair.ablationEntryId] : [],
    latestComparisonReason: latestAttempt?.reason || null,
    latestComparisonDetail: latestAttempt?.detail || null,
    nextAction,
    steps: [
      { id: "register", label: "register", complete: registrationReady,
        active: !registrationReady },
      { id: "baseline", label: "baseline", complete: executedBaseline,
        active: registrationReady && !executedBaseline },
      { id: "ablation", label: "Arm B", complete: executedAblation,
        active: executedBaseline && !executedAblation },
      { id: "compare", label: "compare", complete: matchedPairs.length > 0,
        active: executedBaseline && executedAblation },
    ],
    coordinatesEmbedded: false,
    targetUsed: false,
    candidatesInspected: false,
    searchExecutedByTracker: false,
  };
}
