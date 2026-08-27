function finiteVector(raw, label) {
  if (!Array.isArray(raw) || raw.length !== 3 || raw.some((value) => !Number.isFinite(Number(value)))) {
    throw new Error(`${label} must be a finite Cartesian 3-vector`);
  }
  return raw.map(Number);
}

function magnitude(vector) {
  return Math.hypot(vector[0], vector[1], vector[2]);
}

export function forceMagnitudeP90(rawVectors) {
  if (!Array.isArray(rawVectors)) throw new Error("force sample must be an array");
  const magnitudes = rawVectors.map((vector) => magnitude(finiteVector(vector, "force")))
    .filter((value) => value > 1e-14).sort((first, second) => first - second);
  if (!magnitudes.length) return null;
  return magnitudes[Math.min(magnitudes.length - 1, Math.ceil(.9 * magnitudes.length) - 1)];
}

export function boundedForceSeedOffset(rawForce, referenceScale, displacementCap) {
  const force = finiteVector(rawForce, "force");
  if (!(Number.isFinite(referenceScale) && referenceScale > 0)) {
    throw new Error("force seed requires a positive reference scale");
  }
  if (!(Number.isFinite(displacementCap) && displacementCap > 0)) {
    throw new Error("force seed requires a positive displacement cap");
  }
  const norm = magnitude(force);
  if (!(norm > 1e-14)) return [0, 0, 0];
  const factor = displacementCap * Math.min(1, norm / referenceScale) / norm;
  return force.map((value) => value * factor);
}

export function meanForceVectors(rawVectors) {
  if (!Array.isArray(rawVectors) || !rawVectors.length) return null;
  const vectors = rawVectors.map((vector) => finiteVector(vector, "force"));
  return [0, 1, 2].map((axis) => vectors.reduce((sum, vector) => sum + vector[axis], 0)
    / vectors.length);
}
