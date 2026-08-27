export const DISPLACEMENT_SIGMA_MULTIPLIERS = Object.freeze([1, 2, 3]);

export function displacementClearanceKey(radiusModel = "point", sigmaMultiplier = 0) {
  return `${radiusModel}:${Number(sigmaMultiplier) || 0}`;
}

function validTensor(tensor) {
  return Array.isArray(tensor) && tensor.length === 3
    && tensor.every((row) => Array.isArray(row) && row.length === 3 && row.every(Number.isFinite));
}

/** Rotate a Cartesian covariance by a unit quaternion [x,y,z,w]. The result
 * is R U R^T, so an ellipsoid stored in a cluster-local frame follows the
 * cluster's proper pose without introducing an improper reflection. Invalid
 * or degenerate inputs fail closed to null. */
export function rotateDisplacementTensor(tensor, quaternion) {
  if (!validTensor(tensor) || !Array.isArray(quaternion) || quaternion.length !== 4
    || quaternion.some((value) => !Number.isFinite(value))) return null;
  const norm = Math.hypot(...quaternion);
  if (!(norm > 1e-14)) return null;
  const [x, y, z, w] = quaternion.map((value) => value / norm);
  const rotation = [
    [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
    [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
    [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
  ];
  const rotated = rotation.map((row, first) => rotation.map((otherRow, second) =>
    row.reduce((sum, firstValue, firstIndex) => sum + firstValue
      * otherRow.reduce((inner, secondValue, secondIndex) => inner
        + tensor[firstIndex][secondIndex] * secondValue, 0), 0)));
  // Suppress only round-off antisymmetry; covariance remains a full tensor.
  return rotated.map((row, first) => row.map((value, second) =>
    (value + rotated[second][first]) / 2));
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

/** Re-evaluate a learned colored hard-contact envelope for the actual placed
 * pair direction. Tensors remain in A^2 while record distances are in scene
 * units, hence the explicit angstromToScene factor. When neither live site has
 * a reported/transported tensor, the frozen scalar exclusion is reproduced
 * exactly. This is a one-sigma independent-covariance geometric support rule,
 * not a contact probability or a correlated motion model. */
export function directionalContactExclusion(record, firstTensor, secondTensor, direction, {
  angstromToScene = 1,
  minimumContactFraction = .88,
  lowerContactFraction = .80,
} = {}) {
  const fallback = Number.isFinite(record?.exclusion) ? record.exclusion : 0;
  if (!validTensor(firstTensor) && !validTensor(secondTensor)) return fallback;
  if (!(Number.isFinite(angstromToScene) && angstromToScene > 0)
    || !(Number.isFinite(minimumContactFraction) && minimumContactFraction > 0)
    || !(Number.isFinite(lowerContactFraction) && lowerContactFraction > 0)
    || !Number.isFinite(record?.minimumObserved) || !Number.isFinite(record?.lowerContact)) return fallback;
  const sigma = directionalPairDisplacementSigma(firstTensor, secondTensor, direction) * angstromToScene;
  if (!Number.isFinite(sigma)) return fallback;
  const meanPositionExclusion = Number.isFinite(record.meanPositionExclusion)
    ? record.meanPositionExclusion : fallback;
  return Math.max(0, Math.min(
    meanPositionExclusion,
    Math.max(0, record.minimumObserved - sigma) * minimumContactFraction,
    Math.max(0, record.lowerContact - sigma) * lowerContactFraction,
  ));
}

export function normalizeDisplacementTensors(tensorsAngstrom2, siteCount, lengthScaleAngstrom) {
  if (!Array.isArray(tensorsAngstrom2) || tensorsAngstrom2.length !== siteCount
    || !(Number.isFinite(lengthScaleAngstrom) && lengthScaleAngstrom > 0)) return null;
  const scale2 = lengthScaleAngstrom * lengthScaleAngstrom;
  return tensorsAngstrom2.map((tensor) => validTensor(tensor)
    ? tensor.map((row) => row.map((value) => value / scale2)) : null);
}
