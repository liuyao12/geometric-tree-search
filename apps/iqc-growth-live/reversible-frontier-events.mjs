function integerSet(values) {
  return new Set((Array.isArray(values) ? values : []).filter(Number.isInteger));
}

function sortedIntegers(values) {
  return [...values].sort((first, second) => first - second);
}

/**
 * Certify the exact subset of a placed cluster that can be removed without
 * deleting shared support or invalidating a later placement.  This is a
 * topology/ownership certificate only; an external path calculation still
 * has to supply the physical barrier and prefactor.
 */
export function detachableLeafPlacementAudit(placement, placements, atoms, context = null) {
  const placementId = Number(placement?.id);
  const byAtomId = context?.byAtomId || new Map((Array.isArray(atoms) ? atoms : [])
    .filter((atom) => Number.isInteger(atom?.id)).map((atom) => [atom.id, atom]));
  const children = context?.childrenByParent?.get(placementId)
    || (Array.isArray(placements) ? placements : [])
      .filter((candidate) => candidate?.parentId === placementId).map((candidate) => candidate.id);
  const freshAtomIds = integerSet(placement?.freshAtomIds);
  const supportAtomIds = integerSet(placement?.atomIds);
  const missingFreshAtomIds = sortedIntegers([...freshAtomIds].filter((id) => !byAtomId.has(id)));
  const nonexclusiveFreshAtomIds = sortedIntegers([...freshAtomIds].filter((id) => {
    const atom = byAtomId.get(id);
    const owners = integerSet(atom?.clusterIds);
    return !atom || atom.createdByClusterId !== placementId
      || owners.size !== 1 || !owners.has(placementId);
  }));
  const crossNucleusFreshAtomIds = sortedIntegers([...freshAtomIds].filter((id) => {
    const atom = byAtomId.get(id);
    const nuclei = integerSet(atom?.nucleusIds);
    return atom && (nuclei.size !== 1 || !nuclei.has(placement?.nucleusId));
  }));
  const sharedSupportAtomIds = sortedIntegers([...supportAtomIds].filter((id) => !freshAtomIds.has(id)));
  const invalidSharedSupportAtomIds = sharedSupportAtomIds.filter((id) => {
    const atom = byAtomId.get(id);
    return !atom || !integerSet(atom.clusterIds).has(placementId);
  });
  const reasons = [];
  if (!Number.isInteger(placementId)) reasons.push("invalid-placement-id");
  if (placement?.seedNucleus || placement?.observedWindowSupport || placement?.parentId == null) {
    reasons.push("seed-or-observed-support");
  }
  if (!freshAtomIds.size) reasons.push("no-originally-emitted-atoms");
  if (children.length) reasons.push("has-dependent-child-placement");
  if (missingFreshAtomIds.length) reasons.push("missing-created-atom");
  if (nonexclusiveFreshAtomIds.length) reasons.push("created-atom-shared-or-reowned");
  if (crossNucleusFreshAtomIds.length) reasons.push("created-atom-cross-nucleus");
  if (invalidSharedSupportAtomIds.length) reasons.push("shared-support-membership-missing");
  if (placement?.targetAwareReplay === true || placement?.reconstructionOnly === true) {
    reasons.push("target-aware-replay-placement");
  }
  return {
    schema: "gcts-detachable-leaf-placement-audit-v1",
    placementId,
    parentPlacementId: placement?.parentId ?? null,
    ruleId: placement?.ruleId ?? null,
    removableAtomIds: sortedIntegers(freshAtomIds),
    retainedSharedAtomIds: sharedSupportAtomIds,
    childPlacementIds: sortedIntegers(children),
    missingFreshAtomIds,
    nonexclusiveFreshAtomIds,
    crossNucleusFreshAtomIds,
    invalidSharedSupportAtomIds,
    admitted: reasons.length === 0,
    reasons,
    targetUsed: false,
    sharedAtomsDeleted: false,
    cascadingDeletionAuthorized: false,
  };
}

export function enumerateDetachableLeafPlacements({ placements, atoms }) {
  const byAtomId = new Map((Array.isArray(atoms) ? atoms : [])
    .filter((atom) => Number.isInteger(atom?.id)).map((atom) => [atom.id, atom]));
  const childrenByParent = new Map();
  (Array.isArray(placements) ? placements : []).forEach((placement) => {
    if (!Number.isInteger(placement?.parentId)) return;
    const children = childrenByParent.get(placement.parentId) || [];
    children.push(placement.id); childrenByParent.set(placement.parentId, children);
  });
  const audits = (Array.isArray(placements) ? placements : [])
    .map((placement) => detachableLeafPlacementAudit(placement, placements, atoms,
      { byAtomId, childrenByParent }));
  return {
    schema: "gcts-reversible-leaf-catalog-v1",
    placementCount: audits.length,
    admitted: audits.filter((audit) => audit.admitted),
    rejected: audits.filter((audit) => !audit.admitted),
    targetUsed: false,
    exactOwnershipRequired: true,
    sharedAtomsRetained: true,
    descendantsProtected: true,
    claimBoundary: "Only exact non-seed leaf placements whose originally emitted atoms remain exclusively owned are reversible. This is a finite geometric event catalog, not a barrier, reservoir chemical potential, equilibrium ensemble, or detailed-balance certificate.",
  };
}
