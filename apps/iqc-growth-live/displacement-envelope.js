export const DISPLACEMENT_SIGMA_MULTIPLIERS = Object.freeze([1, 2, 3]);

export function displacementClearanceKey(radiusModel = "point", sigmaMultiplier = 0) {
  return `${radiusModel}:${Number(sigmaMultiplier) || 0}`;
}

function validTensor(tensor) {
  return Array.isArray(tensor) && tensor.length === 3
    && tensor.every((row) => Array.isArray(row) && row.length === 3 && row.every(Number.isFinite));
}

/** Directional support k sqrt(n^T U n) of a crystallographic Cartesian ADP.
 * U is mean-square displacement in the same squared units as the direction's
 * coordinates. This is an ellipsoidal support hypothesis, not a sampled
 * trajectory, temperature, confidence probability, or dynamical amplitude. */
export function directionalDisplacementSupport(tensor, direction, sigmaMultiplier = 0) {
  if (!validTensor(tensor) || !(Number.isFinite(sigmaMultiplier) && sigmaMultiplier > 0)
    || !Array.isArray(direction) || direction.length !== 3 || direction.some((value) => !Number.isFinite(value))) return 0;
  const length = Math.hypot(...direction);
  if (length <= 1e-14) {
    const bound = Math.max(0, ...tensor.map((row) => row.reduce((sum, value) => sum + Math.abs(value), 0)));
    return sigmaMultiplier * Math.sqrt(bound);
  }
  const unit = direction.map((value) => value / length);
  const variance = unit.reduce((sum, firstValue, first) => sum + firstValue
    * unit.reduce((inner, secondValue, second) => inner + tensor[first][second] * secondValue, 0), 0);
  return sigmaMultiplier * Math.sqrt(Math.max(0, variance));
}

/** One-dimensional standard deviation of the relative displacement of two
 * reported sites along their connecting direction. Independent reported ADPs
 * add as covariance, so sigma_pair² = nᵀ(U_i + U_j)n. A missing tensor is an
 * explicit zero contribution. This is a geometric resolution envelope, not a
 * probability of contact, a correlated phonon model, or sampled motion. */
export function directionalPairDisplacementSigma(firstTensor, secondTensor, direction) {
  if (!Array.isArray(direction) || direction.length !== 3
    || direction.some((value) => !Number.isFinite(value))) return 0;
  const length = Math.hypot(...direction);
  if (length <= 1e-14) return 0;
  const unit = direction.map((value) => value / length);
  const directionalVariance = (tensor) => {
    if (!validTensor(tensor)) return 0;
    return unit.reduce((sum, firstValue, first) => sum + firstValue
      * unit.reduce((inner, secondValue, second) => inner + tensor[first][second] * secondValue, 0), 0);
  };
  return Math.sqrt(Math.max(0, directionalVariance(firstTensor) + directionalVariance(secondTensor)));
}

export function normalizeDisplacementTensors(tensorsAngstrom2, siteCount, lengthScaleAngstrom) {
  if (!Array.isArray(tensorsAngstrom2) || tensorsAngstrom2.length !== siteCount
    || !(Number.isFinite(lengthScaleAngstrom) && lengthScaleAngstrom > 0)) return null;
  const scale2 = lengthScaleAngstrom * lengthScaleAngstrom;
  return tensorsAngstrom2.map((tensor) => validTensor(tensor)
    ? tensor.map((row) => row.map((value) => value / scale2)) : null);
}
