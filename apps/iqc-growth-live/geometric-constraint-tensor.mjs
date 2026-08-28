function finiteVector(value) {
  return Array.isArray(value) && value.length === 3 && value.every(Number.isFinite);
}

function normalized(value) {
  const norm = Math.hypot(...value);
  return norm > 1e-12 ? value.map((component) => component / norm) : null;
}

function symmetricEigenvalues3(matrix) {
  const a = matrix.map((row) => [...row]);
  for (let sweep = 0; sweep < 16; sweep++) {
    let p = 0; let q = 1; let largest = Math.abs(a[0][1]);
    [[0, 2], [1, 2]].forEach(([first, second]) => {
      const value = Math.abs(a[first][second]);
      if (value > largest) { largest = value; p = first; q = second; }
    });
    if (largest < 1e-13) break;
    const angle = .5 * Math.atan2(2 * a[p][q], a[q][q] - a[p][p]);
    const c = Math.cos(angle); const s = Math.sin(angle);
    for (let k = 0; k < 3; k++) {
      if (k === p || k === q) continue;
      const apk = a[p][k]; const aqk = a[q][k];
      a[p][k] = a[k][p] = c * apk - s * aqk;
      a[q][k] = a[k][q] = s * apk + c * aqk;
    }
    const app = a[p][p]; const aqq = a[q][q]; const apq = a[p][q];
    a[p][p] = c * c * app - 2 * s * c * apq + s * s * aqq;
    a[q][q] = s * s * app + 2 * s * c * apq + c * c * aqq;
    a[p][q] = a[q][p] = 0;
  }
  return [a[0][0], a[1][1], a[2][2]].map((value) => Math.max(0, value))
    .sort((first, second) => second - first);
}

export function geometricConstraintTensor(contactVectors, mode = "none") {
  if (!Array.isArray(contactVectors)) throw new Error("contact vectors must be an array");
  const directions = contactVectors.map((record) => {
    const vector = finiteVector(record) ? record : record?.vector;
    const direction = finiteVector(vector) ? normalized(vector) : null;
    const weight = finiteVector(record) ? 1 : Number(record?.weight ?? 1);
    return direction && Number.isFinite(weight) && weight > 0 ? { direction, weight } : null;
  }).filter(Boolean);
  const tensor = Array.from({ length: 3 }, () => [0, 0, 0]);
  directions.forEach(({ direction, weight }) => {
    for (let row = 0; row < 3; row++) for (let column = 0; column < 3; column++) {
      tensor[row][column] += weight * direction[row] * direction[column];
    }
  });
  const trace = tensor[0][0] + tensor[1][1] + tensor[2][2];
  const normalizedTensor = trace > 0 ? tensor.map((row) => row.map((value) => value / trace)) : tensor;
  const eigenvalues = trace > 0 ? symmetricEigenvalues3(normalizedTensor) : [0, 0, 0];
  const [first, second, third] = eigenvalues;
  const isotropic3d = Math.max(0, Math.min(1, 3 * third));
  const lamellar = Math.max(0, Math.min(1, 2 * second)) * (1 - isotropic3d);
  const axial = Math.max(0, Math.min(1, 1 - 3 * second)) * Math.max(0, Math.min(1, 1.5 * first));
  const probabilities = eigenvalues.filter((value) => value > 1e-15);
  const effectiveDimension = probabilities.length ? Math.exp(-probabilities.reduce((sum, value) =>
    sum + value * Math.log(value), 0)) : 0;
  const rank = eigenvalues.filter((value) => value >= .05).length;
  const metric = mode === "rigid-3d" ? isotropic3d : mode === "lamellar" ? lamellar
    : mode === "axial" ? axial : 0;
  return Object.freeze({
    mode,
    score: directions.length ? 2 * metric - 1 : -1,
    contactDirectionCount: directions.length,
    tensor: Object.freeze(normalizedTensor.map((row) => Object.freeze(row.map((value) => Number(value.toFixed(12)))))),
    eigenvalues: Object.freeze(eigenvalues.map((value) => Number(value.toFixed(12)))),
    rank,
    effectiveDimension,
    isotropic3d,
    lamellar,
    axial,
    scaleInvariant: true,
    properRotationInvariant: true,
    targetUsed: false,
    forceConstantsUsed: false,
    massesUsed: false,
    energyInferred: false,
    modulusInferred: false,
    phononSpectrumInferred: false,
    vibrationalEntropyInferred: false,
  });
}
