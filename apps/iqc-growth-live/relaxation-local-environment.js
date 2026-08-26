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

function transpose(matrix) {
  return matrix[0].map((_, column) => matrix.map((row) => row[column]));
}

function determinant3(matrix) {
  const [[a, b, c], [d, e, f], [g, h, i]] = matrix;
  return a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g);
}

function frobeniusSquared(matrix) {
  return matrix.flat().reduce((sum, value) => sum + value * value, 0);
}

/**
 * Rotation-invariant finite-strain scalars derived from a local deformation
 * gradient.  Full 3D strain is intentionally withheld when the source
 * neighborhood does not span 3D: regularization can stabilize D²min for a
 * planar shell, but it cannot supply the missing out-of-plane deformation.
 */
export function affineDeformationInvariants(bestAffine, sourceVectors) {
  if (!Array.isArray(bestAffine) || bestAffine.length !== 3
      || !bestAffine.every((row) => Array.isArray(row) && row.length === 3 && row.every(Number.isFinite))
      || !Array.isArray(sourceVectors) || !sourceVectors.length || !sourceVectors.every(finiteVector)) {
    throw new Error("affine deformation invariants need a finite 3x3 map and finite source vectors");
  }
  const sourceMoment = Array.from({ length: 3 }, () => [0, 0, 0]);
  sourceVectors.forEach((source) => {
    for (let row = 0; row < 3; row++) for (let column = 0; column < 3; column++) {
      sourceMoment[row][column] += source[row] * source[column];
    }
  });
  const sourceTrace = sourceMoment[0][0] + sourceMoment[1][1] + sourceMoment[2][2];
  const normalizedSourceMomentDeterminant = sourceTrace > 0
    ? determinant3(sourceMoment) / ((sourceTrace / 3) ** 3) : 0;
  const fullRankSource = Number.isFinite(normalizedSourceMomentDeterminant)
    && normalizedSourceMomentDeterminant > 1e-8;
  const deformationGradientDeterminant = determinant3(bestAffine);
  if (!fullRankSource) return {
    sourceMeanSquaredRadius: sourceTrace / sourceVectors.length,
    normalizedSourceMomentDeterminant,
    fullRankSource: false,
    deformationGradientDeterminant: null,
    localVolumeChangeFraction: null,
    meanNormalGreenLagrangeStrain: null,
    deviatoricGreenLagrangeMagnitude: null,
    equivalentShearStrain: null,
    orientationPreserving: null,
  };
  const rightCauchyGreen = multiply(transpose(bestAffine), bestAffine);
  const greenLagrange = rightCauchyGreen.map((row, rowIndex) => row.map((value, columnIndex) =>
    .5 * (value - Number(rowIndex === columnIndex))));
  const trace = greenLagrange[0][0] + greenLagrange[1][1] + greenLagrange[2][2];
  const meanNormal = trace / 3;
  const deviatoric = greenLagrange.map((row, rowIndex) => row.map((value, columnIndex) =>
    value - (rowIndex === columnIndex ? meanNormal : 0)));
  const deviatoricSquared = frobeniusSquared(deviatoric);
  return {
    sourceMeanSquaredRadius: sourceTrace / sourceVectors.length,
    normalizedSourceMomentDeterminant,
    fullRankSource: true,
    deformationGradientDeterminant,
    localVolumeChangeFraction: deformationGradientDeterminant - 1,
    meanNormalGreenLagrangeStrain: meanNormal,
    deviatoricGreenLagrangeMagnitude: Math.sqrt(Math.max(0, deviatoricSquared)),
    equivalentShearStrain: Math.sqrt(Math.max(0, 2 * deviatoricSquared / 3)),
    orientationPreserving: deformationGradientDeterminant > 0,
  };
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
  const deformation = affineDeformationInvariants(bestAffine, sourceVectors);
  const rootD2Min = Math.sqrt(Math.max(0, d2Min));
  return { bestAffine, d2Min, rootD2Min: Math.sqrt(Math.max(0, d2Min)),
    normalizedRootD2Min: rootD2Min / Math.sqrt(Math.max(1e-30, deformation.sourceMeanSquaredRadius)),
    neighborCount: sourceVectors.length, regularizer, ...deformation };
}
