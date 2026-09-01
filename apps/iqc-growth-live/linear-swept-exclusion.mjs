const finiteVector = (value) => Array.isArray(value) && value.length === 3
  && value.every(Number.isFinite);
const subtract = (first, second) => first.map((value, axis) => value - second[axis]);
const addScaled = (point, vector, scale) => point.map((value, axis) => value + scale * vector[axis]);
const dot = (first, second) => first.reduce((sum, value, axis) => sum + value * second[axis], 0);

/** Certify hard exclusion over complete affine Cartesian pair paths. */
export function auditLinearSweptExclusion(rawPairs) {
  if (!Array.isArray(rawPairs) || !rawPairs.length) {
    throw new Error("swept exclusion requires at least one pair path");
  }
  let minimumMargin = Infinity;
  let closestPair = null;
  const pairs = rawPairs.map((pair, pairIndex) => {
    for (const field of ["firstStart", "firstEnd", "secondStart", "secondEnd"]) {
      if (!finiteVector(pair?.[field])) throw new Error(`pair ${pairIndex} has invalid ${field}`);
    }
    const exclusion = Number(pair.exclusion);
    if (!(Number.isFinite(exclusion) && exclusion >= 0)) {
      throw new Error(`pair ${pairIndex} has invalid exclusion`);
    }
    const relativeStart = subtract(pair.secondStart, pair.firstStart);
    const firstVelocity = subtract(pair.firstEnd, pair.firstStart);
    const secondVelocity = subtract(pair.secondEnd, pair.secondStart);
    const relativeVelocity = subtract(secondVelocity, firstVelocity);
    const speedSquared = dot(relativeVelocity, relativeVelocity);
    const fraction = speedSquared > 1e-20
      ? Math.max(0, Math.min(1, -dot(relativeStart, relativeVelocity) / speedSquared)) : 0;
    const closestVector = addScaled(relativeStart, relativeVelocity, fraction);
    const closestDistance = Math.hypot(...closestVector);
    const margin = closestDistance - exclusion;
    const record = Object.freeze({
      firstId: pair.firstId ?? pairIndex * 2,
      secondId: pair.secondId ?? pairIndex * 2 + 1,
      fraction,
      closestDistance,
      conservativeExclusion: exclusion,
      margin,
    });
    if (margin < minimumMargin) {
      minimumMargin = margin;
      closestPair = record;
    }
    return record;
  });
  return Object.freeze({
    passed: minimumMargin >= -1e-10,
    pairChecks: pairs.length,
    minimumMargin,
    closestPair,
    pairs: Object.freeze(pairs),
    analyticLinearClosestApproach: true,
    conservativeDirectionalExclusionUpperBound: true,
    sampledOnly: false,
    targetUsed: false,
    claimBoundary: "This certifies a declared scalar exclusion over affine Cartesian pair paths. It is not a physical trajectory, minimum-energy path, dynamics, or time.",
  });
}
