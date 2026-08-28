export const GROWTH_REGIME_STATE_AXES = Object.freeze([
  Object.freeze({ id: "coordinationDeficit", label: "coordination exposure", unit: "fraction" }),
  Object.freeze({ id: "underpackedFraction", label: "underpacked sites", unit: "fraction" }),
  Object.freeze({ id: "localOrder6", label: "q6 / |psi6|", unit: "dimensionless" }),
  Object.freeze({ id: "scatteringProminence", label: "S(q) peak prominence", unit: "unit-weight" }),
  Object.freeze({ id: "shapeAnisotropy", label: "shape anisotropy", unit: "kappa squared" }),
  Object.freeze({ id: "sharedInterfaceFraction", label: "shared interface", unit: "fraction" }),
]);

export const GROWTH_REGIME_RESPONSE_AXES = Object.freeze([
  Object.freeze({ id: "coordinationDeficitDelta", label: "change in exposure", unit: "fraction" }),
  Object.freeze({ id: "localOrder6Delta", label: "change in q6 / |psi6|", unit: "dimensionless" }),
  Object.freeze({ id: "scatteringProminenceDelta", label: "change in S(q) prominence", unit: "unit-weight" }),
  Object.freeze({ id: "shapeAnisotropyDelta", label: "change in anisotropy", unit: "kappa squared" }),
  Object.freeze({ id: "effectiveNucleusCountDelta", label: "change in effective nuclei", unit: "count" }),
  Object.freeze({ id: "sharedInterfaceFractionDelta", label: "change in shared interface", unit: "fraction" }),
  Object.freeze({ id: "emittedAtoms", label: "explicit atoms emitted", unit: "atoms" }),
]);

const finite = (value) => Number.isFinite(value) ? value : null;
const order6 = (state) => finite(state?.orientationalOrder?.harmonics?.[6]?.mean);
const prominence = (state) => finite(state?.scattering?.summary?.peakProminence);

function stateValues(state) {
  return {
    coordinationDeficit: finite(state?.morphology?.coordinationDeficit),
    underpackedFraction: finite(state?.packing?.underpackedFraction),
    localOrder6: order6(state),
    scatteringProminence: prominence(state),
    shapeAnisotropy: finite(state?.morphology?.relativeShapeAnisotropy),
    sharedInterfaceFraction: finite(state?.morphology?.lineageEnsemble?.sharedInterfaceFraction),
  };
}

function difference(after, before) {
  return Number.isFinite(after) && Number.isFinite(before) ? after - before : null;
}

export function buildExecutedGrowthRegime(leaps = []) {
  const records = [];
  let excluded = 0;
  for (const leap of leaps) {
    const before = leap?.before;
    const after = leap?.after;
    const emittedAtoms = finite(after?.atoms) !== null && finite(before?.atoms) !== null
      ? after.atoms - before.atoms : null;
    if (leap?.status !== "accepted" || !before || !after || !(emittedAtoms > 0)
      || leap.targetUsed === true || before.targetUsed === true || after.targetUsed === true) {
      excluded++;
      continue;
    }
    const state = stateValues(before);
    const afterState = stateValues(after);
    const response = {
      coordinationDeficitDelta: difference(afterState.coordinationDeficit, state.coordinationDeficit),
      localOrder6Delta: difference(afterState.localOrder6, state.localOrder6),
      scatteringProminenceDelta: difference(afterState.scatteringProminence, state.scatteringProminence),
      shapeAnisotropyDelta: difference(afterState.shapeAnisotropy, state.shapeAnisotropy),
      effectiveNucleusCountDelta: difference(
        finite(after?.morphology?.lineageEnsemble?.effectiveNucleusCount),
        finite(before?.morphology?.lineageEnsemble?.effectiveNucleusCount)),
      sharedInterfaceFractionDelta: difference(afterState.sharedInterfaceFraction,
        state.sharedInterfaceFraction),
      emittedAtoms,
    };
    records.push({
      leapIndex: leap.index,
      label: leap.label || `leap ${leap.index}`,
      acceptedActions: finite(after.accepted),
      rejectedActions: finite(after.rejected),
      emittedAtoms,
      causalDepth: finite(after.depth),
      beforePhenotype: before.morphology?.phenotype || "unresolved",
      afterPhenotype: after.morphology?.phenotype || "unresolved",
      state,
      response,
    });
  }
  return {
    schema: 1,
    records,
    executedLeaps: records.length,
    excludedLeaps: excluded,
    stateAxes: GROWTH_REGIME_STATE_AXES.map((axis) => ({ ...axis })),
    responseAxes: GROWTH_REGIME_RESPONSE_AXES.map((axis) => ({ ...axis })),
    coordinatesEmbedded: false,
    targetUsed: false,
    usedForCandidateEnumeration: false,
    usedForAdmission: false,
    usedForRanking: false,
    physicalTimeModeled: false,
    energyInferred: false,
    kineticsInferred: false,
    phaseDiagramInferred: false,
    claimBoundary: "finite accepted GCTS leaps in execution order; descriptive state-response association, not a phase diagram, free-energy surface, kinetic trajectory, or causal law",
  };
}

export function growthRegimePlotRows(audit, stateAxisId, responseAxisId) {
  return (audit?.records || []).map((record) => ({
    ...record,
    x: record.state?.[stateAxisId],
    y: record.response?.[responseAxisId],
  })).filter((record) => Number.isFinite(record.x) && Number.isFinite(record.y));
}
