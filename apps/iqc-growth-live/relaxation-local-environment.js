function finiteVector(vector) {
  return Array.isArray(vector) && vector.length === 3 && vector.every(Number.isFinite);
}

function invert3(matrix) {
  const [a, b, c, d, e, f, g, h, i] = matrix.flat();
  const A = e * i - f * h;
  const B = c * h - b * i;
  const C = b * f - c * e;
  const D = f * g - d * i;
  const E = a * i - c * g;
  const F = c * d - a * f;
  const G = d * h - e * g;
  const H = b * g - a * h;
  const I = a * e - b * d;
  const determinant = a * A + b * D + c * G;
  if (!Number.isFinite(determinant) || Math.abs(determinant) < 1e-30) throw new Error("local source moment is singular");
  return [[A, B, C], [D, E, F], [G, H, I]].map((row) => row.map((value) => value / determinant));
}

function multiply(first, second) {
  return first.map((row) => second[0].map((_, column) => row.reduce(
    (sum, value, inner) => sum + value * second[inner][column], 0)));
}

function apply(matrix, vector) {
  return matrix.map((row) => row.reduce((sum, value, index) => sum + value * vector[index], 0));
}

export function bestAffineNeighborhoodResidual(sourceVectors, targetVectors, regularizationFraction = 1e-10) {
  if (!Array.isArray(sourceVectors) || sourceVectors.length < 3
      || sourceVectors.length !== targetVectors?.length
      || !sourceVectors.every(finiteVector) || !targetVectors.every(finiteVector)) {
    throw new Error("best-affine residual needs at least three paired finite 3D neighbor vectors");
  }
  const sourceMoment = Array.from({ length: 3 }, () => [0, 0, 0]);
  const crossMoment = Array.from({ length: 3 }, () => [0, 0, 0]);
  sourceVectors.forEach((source, sample) => {
    const target = targetVectors[sample];
    for (let row = 0; row < 3; row++) for (let column = 0; column < 3; column++) {
      sourceMoment[row][column] += source[row] * source[column];
      crossMoment[row][column] += target[row] * source[column];
    }
  });
  const trace = sourceMoment[0][0] + sourceMoment[1][1] + sourceMoment[2][2];
  const regularizer = Math.max(1e-12, trace * regularizationFraction);
  for (let axis = 0; axis < 3; axis++) sourceMoment[axis][axis] += regularizer;
  const bestAffine = multiply(crossMoment, invert3(sourceMoment));
  const d2Min = sourceVectors.reduce((sum, source, sample) => {
    const predicted = apply(bestAffine, source);
    return sum + predicted.reduce((residual, value, axis) => residual
      + (value - targetVectors[sample][axis]) ** 2, 0);
  }, 0) / sourceVectors.length;
  return { bestAffine, d2Min, rootD2Min: Math.sqrt(Math.max(0, d2Min)),
    neighborCount: sourceVectors.length, regularizer };
}
