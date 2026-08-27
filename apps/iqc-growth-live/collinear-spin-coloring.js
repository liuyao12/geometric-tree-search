// A supplied collinear atomic spin is a signed scalar site label.  With no
// archive-supplied axis or moment unit it may be compared at an exact overlap,
// but it must never be rotated as a 3D vector or interpreted as an exchange
// energy.  Missing labels remain unconstrained.

export const SCALAR_SPIN_ZERO_TOLERANCE = 1e-8;

export function scalarSpinPolarity(value, tolerance = SCALAR_SPIN_ZERO_TOLERANCE) {
  if (!Number.isFinite(value)) return null;
  if (Math.abs(value) <= tolerance) return 0;
  return value > 0 ? 1 : -1;
}

export function scalarSpinCompatible(first, second, {
  enabled = true,
  tolerance = SCALAR_SPIN_ZERO_TOLERANCE,
} = {}) {
  if (!enabled) return true;
  const firstPolarity = scalarSpinPolarity(first, tolerance);
  const secondPolarity = scalarSpinPolarity(second, tolerance);
  if (firstPolarity === null || secondPolarity === null) return true;
  return firstPolarity === secondPolarity;
}

export function auditScalarSpinOverlaps(pairs, options = {}) {
  let suppliedPairs = 0;
  let compatiblePairs = 0;
  let conflictingPairs = 0;
  for (const [first, second] of pairs) {
    if (!(Number.isFinite(first) && Number.isFinite(second))) continue;
    suppliedPairs++;
    if (scalarSpinCompatible(first, second, options)) compatiblePairs++;
    else conflictingPairs++;
  }
  return {
    suppliedPairs,
    compatiblePairs,
    conflictingPairs,
    missingPairs: pairs.length - suppliedPairs,
    hardColoringApplied: options.enabled !== false,
    vectorAxisInferred: false,
    magneticEnergyInferred: false,
  };
}
