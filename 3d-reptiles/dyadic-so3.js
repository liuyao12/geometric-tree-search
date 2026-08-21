const SQRT3 = Math.sqrt(3);
const Q_DIAGONAL = [1, 3, 3];

export function physicalToQCoordinates(rotation) {
  const scales = [1, SQRT3, SQRT3];
  return rotation.map((row, rowIndex) => row.map(
    (value, columnIndex) => value * scales[columnIndex] / scales[rowIndex]
  ));
}

function determinant3(matrix) {
  return matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
    - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
    + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0]);
}

export function verifyDyadicSO3(numerators, denominator) {
  for (let row = 0; row < 3; row += 1) {
    for (let column = 0; column < 3; column += 1) {
      let value = 0;
      for (let index = 0; index < 3; index += 1) {
        value += numerators[index][row] * Q_DIAGONAL[index] * numerators[index][column];
      }
      const expected = row === column ? denominator * denominator * Q_DIAGONAL[row] : 0;
      if (value !== expected) return false;
    }
  }
  return determinant3(numerators) === denominator ** 3;
}

export function exactDyadicSO3(rotation, maxExponent = 24, tolerance = 1e-7) {
  const qMatrix = physicalToQCoordinates(rotation);
  for (let exponent = 0; exponent <= maxExponent; exponent += 1) {
    const denominator = 2 ** exponent;
    const numerators = qMatrix.map(row => row.map(value => Math.round(value * denominator)));
    const close = qMatrix.every((row, rowIndex) => row.every(
      (value, columnIndex) => Math.abs(value * denominator - numerators[rowIndex][columnIndex]) <= tolerance
    ));
    if (close && verifyDyadicSO3(numerators, denominator)) {
      return { exponent, denominator, numerators };
    }
  }
  return null;
}

export function multiplyMatrices(left, right) {
  return left.map((_, row) => right[0].map((__, column) =>
    left[row].reduce((sum, value, index) => sum + value * right[index][column], 0)
  ));
}
