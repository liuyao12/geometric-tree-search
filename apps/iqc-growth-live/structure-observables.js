const DEFAULT_Q_MIN = 2;
const DEFAULT_Q_MAX = 20;
const DEFAULT_Q_BINS = 48;
const DEFAULT_ORDER_BINS = 24;

// Numerical Recipes' rational/asymptotic approximation.  The 2D isotropic
// powder average is J0(qr); using cos(qr) would silently apply a 1D model.
export function besselJ0(value) {
  const x = Math.abs(value);
  if (x < 1e-12) return 1;
  if (x < 8) {
    const y = x * x;
    const numerator = 57568490574 + y * (-13362590354 + y * (651619640.7
      + y * (-11214424.18 + y * (77392.33017 + y * -184.9052456))));
    const denominator = 57568490411 + y * (1029532985 + y * (9494680.718
      + y * (59272.64853 + y * (267.8532712 + y))));
    return numerator / denominator;
  }
  const z = 8 / x;
  const y = z * z;
  const phase = x - .785398164;
  const amplitude = 1 + y * (-.1098628627e-2 + y * (.2734510407e-4
    + y * (-.2073370639e-5 + y * .2093887211e-6)));
  const correction = -.1562499995e-1 + y * (.1430488765e-3
    + y * (-.6911147651e-5 + y * (.7621095161e-6 - y * .934945152e-7)));
  return Math.sqrt(.636619772 / x) * (Math.cos(phase) * amplitude - z * Math.sin(phase) * correction);
}

function powderKernel(value, dimension) {
  if (Math.abs(value) < 1e-10) return 1;
  return dimension === 2 ? besselJ0(value) : Math.sin(value) / value;
}

/**
 * Debye-style powder average for a finite colored-point observation with unit
 * scattering weights.  Pair distances and q are normalized by the same
 * nearest-neighbour length a.  This is geometric S(q), not an X-ray or neutron
 * intensity: no species-dependent form factors, occupancies, or instrument
 * response enter the calculation.
 */
export function powderStructureFactor(pairDistances, atomCount, dimension = 3, {
  qMin = DEFAULT_Q_MIN,
  qMax = DEFAULT_Q_MAX,
  bins = DEFAULT_Q_BINS,
} = {}) {
  if (!Array.isArray(pairDistances)) throw new Error("powder S(q) requires pair distances");
  if (!Number.isInteger(atomCount) || atomCount < 0) throw new Error("powder S(q) requires an atom count");
  if (dimension !== 2 && dimension !== 3) throw new Error("powder S(q) supports intrinsic dimension 2 or 3");
  if (!(qMax > qMin) || bins < 2) throw new Error("powder S(q) requires a finite q interval");
  const q = Array.from({ length: bins }, (_, index) => qMin + index / (bins - 1) * (qMax - qMin));
  if (atomCount < 2) return { q, values: q.map(() => atomCount ? 1 : 0), dimension, qMin, qMax };
  const values = q.map((waveNumber) => {
    const pairSum = pairDistances.reduce((sum, distance) =>
      sum + powderKernel(waveNumber * distance, dimension), 0);
    // The orientational average of |sum_j exp(i q.r_j)|^2 / N is nonnegative;
    // clip only floating-point undershoot from the finite kernel approximation.
    return Math.max(0, 1 + 2 * pairSum / atomCount);
  });
  return { q, values, dimension, qMin, qMax };
}

/**
 * Finite-observation Debye powder average for arbitrary real per-site
 * scattering weights. `pairTerms` contains each unordered i<j pair once and
 * `selfWeightSquares` is sum_i w_i^2.  Normalization therefore preserves a
 * unit high-q self baseline and is invariant to a common rescaling of all
 * weights. Signed weights are allowed for a declared chemical-contrast view;
 * the result remains an orientationally averaged squared amplitude, not a
 * calibrated X-ray or neutron intensity.
 */
export function weightedPowderStructureFactor(pairTerms, selfWeightSquares, dimension = 3, {
  qMin = DEFAULT_Q_MIN,
  qMax = DEFAULT_Q_MAX,
  bins = DEFAULT_Q_BINS,
} = {}) {
  if (!Array.isArray(pairTerms) || pairTerms.some((term) => !Number.isFinite(term?.distance)
      || !Number.isFinite(term?.weightProduct))) {
    throw new Error("weighted powder S(q) requires finite distance/weight pair terms");
  }
  if (!(Number.isFinite(selfWeightSquares) && selfWeightSquares > 0)) {
    throw new Error("weighted powder S(q) requires positive total squared self weight");
  }
  if (dimension !== 2 && dimension !== 3) throw new Error("weighted powder S(q) supports intrinsic dimension 2 or 3");
  if (!(qMax > qMin) || bins < 2) throw new Error("weighted powder S(q) requires a finite q interval");
  const q = Array.from({ length: bins }, (_, index) => qMin + index / (bins - 1) * (qMax - qMin));
  const values = q.map((waveNumber) => {
    const pairSum = pairTerms.reduce((sum, term) => sum
      + term.weightProduct * powderKernel(waveNumber * term.distance, dimension), 0);
    return Math.max(0, 1 + 2 * pairSum / selfWeightSquares);
  });
  return { q, values, dimension, qMin, qMax, selfWeightSquares };
}

/**
 * Coherent finite-observation powder term with an isotropic-equivalent
 * crystallographic displacement attenuation on each i<j cross term.
 * `meanSquareSum` is (Ueq_i + Ueq_j) / a^2 in the observation dimension.
 * Self scattering remains one; diffuse intensity displaced from the coherent
 * curve is not modeled. Missing tensors must be supplied explicitly as zero.
 */
export function displacementDampedWeightedPowderStructureFactor(pairTerms, selfWeightSquares,
  dimension = 3, options = {}) {
  if (!Array.isArray(pairTerms) || pairTerms.some((term) => !Number.isFinite(term?.distance)
      || !Number.isFinite(term?.weightProduct) || !Number.isFinite(term?.meanSquareSum)
      || term.meanSquareSum < 0)) {
    throw new Error("displacement-damped powder S(q) requires finite pair geometry, weights, and Ueq sums");
  }
  if (!(Number.isFinite(selfWeightSquares) && selfWeightSquares > 0)) {
    throw new Error("displacement-damped powder S(q) requires positive total squared self weight");
  }
  if (dimension !== 2 && dimension !== 3) throw new Error("displacement-damped powder S(q) supports intrinsic dimension 2 or 3");
  const qMin = options.qMin ?? DEFAULT_Q_MIN;
  const qMax = options.qMax ?? DEFAULT_Q_MAX;
  const bins = options.bins ?? DEFAULT_Q_BINS;
  if (!(qMax > qMin) || bins < 2) throw new Error("displacement-damped powder S(q) requires a finite q interval");
  const q = Array.from({ length: bins }, (_, index) => qMin + index / (bins - 1) * (qMax - qMin));
  const values = q.map((waveNumber) => {
    const pairSum = pairTerms.reduce((sum, term) => sum + term.weightProduct
      * Math.exp(-.5 * waveNumber * waveNumber * term.meanSquareSum)
      * powderKernel(waveNumber * term.distance, dimension), 0);
    return Math.max(0, 1 + 2 * pairSum / selfWeightSquares);
  });
  return { q, values, dimension, qMin, qMax, selfWeightSquares,
    coherentDisplacementAttenuation: true, diffuseRedistributionIncluded: false };
}

function symmetricEigenSystem(tensor) {
  const dimension = tensor.length;
  const matrix = tensor.map((row) => row.slice());
  const vectors = Array.from({ length: dimension }, (_, row) =>
    Array.from({ length: dimension }, (_, column) => row === column ? 1 : 0));
  for (let iteration = 0; iteration < 32; iteration++) {
    let first = 0; let second = 1; let largest = 0;
    for (let row = 0; row < dimension; row++) {
      for (let column = row + 1; column < dimension; column++) {
        if (Math.abs(matrix[row][column]) > largest) {
          largest = Math.abs(matrix[row][column]); first = row; second = column;
        }
      }
    }
    if (largest < 1e-12) break;
    const angle = .5 * Math.atan2(2 * matrix[first][second],
      matrix[second][second] - matrix[first][first]);
    const cosine = Math.cos(angle); const sine = Math.sin(angle);
    const app = matrix[first][first]; const aqq = matrix[second][second];
    const apq = matrix[first][second];
    matrix[first][first] = cosine * cosine * app - 2 * sine * cosine * apq + sine * sine * aqq;
    matrix[second][second] = sine * sine * app + 2 * sine * cosine * apq + cosine * cosine * aqq;
    matrix[first][second] = 0; matrix[second][first] = 0;
    for (let index = 0; index < dimension; index++) {
      if (index === first || index === second) continue;
      const aip = matrix[index][first]; const aiq = matrix[index][second];
      matrix[index][first] = cosine * aip - sine * aiq;
      matrix[first][index] = matrix[index][first];
      matrix[index][second] = sine * aip + cosine * aiq;
      matrix[second][index] = matrix[index][second];
    }
    for (let row = 0; row < dimension; row++) {
      const vip = vectors[row][first]; const viq = vectors[row][second];
      vectors[row][first] = cosine * vip - sine * viq;
      vectors[row][second] = sine * vip + cosine * viq;
    }
  }
  return Array.from({ length: dimension }, (_, index) => ({
    value: matrix[index][index],
    vector: vectors.map((row) => row[index]),
  })).sort((first, second) => first.value - second.value);
}

function directionalQuadrature(dimension) {
  const count = 96;
  if (dimension === 2) return Array.from({ length: count }, (_, index) => {
    const angle = 2 * Math.PI * (index + .5) / count;
    return { direction: [Math.cos(angle), Math.sin(angle)], weight: 1 / count };
  });
  const goldenAngle = Math.PI * (3 - Math.sqrt(5));
  return Array.from({ length: count }, (_, index) => {
    const z = 1 - 2 * (index + .5) / count;
    const radius = Math.sqrt(Math.max(0, 1 - z * z));
    const angle = goldenAngle * index;
    return { direction: [radius * Math.cos(angle), radius * Math.sin(angle), z], weight: 1 / count };
  });
}

/**
 * Coherent finite-observation powder term retaining the full reported
 * intrinsic-space displacement covariance for every site. A deterministic
 * 96-direction circle/sphere quadrature averages the coherent amplitude, then
 * restores the exact unit self term omitted by amplitude attenuation. This is
 * O(QDN), rather than a directional O(QDN²) pair expansion. Fully isotropic
 * tensors retain the exact analytic pair kernel. Displaced diffuse intensity
 * is not redistributed.
 */
export function anisotropicDisplacementDampedWeightedPowderStructureFactor(siteTerms,
  selfWeightSquares, dimension = 3, options = {}) {
  if (!Array.isArray(siteTerms) || siteTerms.some((term) => !Array.isArray(term?.position)
      || term.position.length !== dimension || term.position.some((value) => !Number.isFinite(value))
      || !Number.isFinite(term?.weight) || !Array.isArray(term?.meanSquareTensor)
      || term.meanSquareTensor.length !== dimension
      || term.meanSquareTensor.some((row, rowIndex) => !Array.isArray(row) || row.length !== dimension
        || row.some((value, columnIndex) => !Number.isFinite(value)
          || Math.abs(value - term.meanSquareTensor[columnIndex]?.[rowIndex]) > 1e-9)))) {
    throw new Error("anisotropic displacement powder S(q) requires finite site positions, weights, and symmetric covariances");
  }
  if (!(Number.isFinite(selfWeightSquares) && selfWeightSquares > 0)) {
    throw new Error("anisotropic displacement powder S(q) requires positive total squared self weight");
  }
  if (dimension !== 2 && dimension !== 3) throw new Error("anisotropic displacement powder S(q) supports intrinsic dimension 2 or 3");
  const qMin = options.qMin ?? DEFAULT_Q_MIN;
  const qMax = options.qMax ?? DEFAULT_Q_MAX;
  const bins = options.bins ?? DEFAULT_Q_BINS;
  if (!(qMax > qMin) || bins < 2) throw new Error("anisotropic displacement powder S(q) requires a finite q interval");
  const quadrature = directionalQuadrature(dimension);
  const centroid = Array.from({ length: dimension }, (_, axis) => siteTerms.reduce((sum, term) =>
    sum + term.position[axis], 0) / Math.max(1, siteTerms.length));
  const prepared = siteTerms.map((term) => {
    const eigen = symmetricEigenSystem(term.meanSquareTensor);
    if (eigen.some((entry) => entry.value < -1e-10)) {
      throw new Error("anisotropic displacement powder S(q) requires positive-semidefinite covariances");
    }
    const diagonal = term.meanSquareTensor.map((row, index) => row[index]);
    const scalar = diagonal.reduce((sum, value) => sum + value, 0) / dimension;
    const isotropic = term.meanSquareTensor.every((row, rowIndex) => row.every((value, columnIndex) =>
      Math.abs(value - (rowIndex === columnIndex ? scalar : 0)) <= 1e-10 * Math.max(1, scalar)));
    return { position: term.position.map((value, index) => value - centroid[index]),
      weight: term.weight, tensor: term.meanSquareTensor, scalar: Math.max(0, scalar), isotropic };
  });
  const q = Array.from({ length: bins }, (_, index) => qMin + index / (bins - 1) * (qMax - qMin));
  if (prepared.every((term) => term.isotropic)) {
    const pairTerms = [];
    for (let first = 0; first < prepared.length; first++) {
      for (let second = first + 1; second < prepared.length; second++) {
        pairTerms.push({
          distance: Math.sqrt(prepared[first].position.reduce((sum, value, index) =>
            sum + (value - prepared[second].position[index]) ** 2, 0)),
          weightProduct: prepared[first].weight * prepared[second].weight,
          meanSquareSum: prepared[first].scalar + prepared[second].scalar,
        });
      }
    }
    const exact = displacementDampedWeightedPowderStructureFactor(pairTerms, selfWeightSquares,
      dimension, { qMin, qMax, bins });
    return { ...exact, fullAnisotropicCovarianceUsed: true,
      orientationQuadrature: "analytic isotropic reduction", quadratureDirections: 0,
      anisotropicSiteTerms: 0 };
  }
  const values = q.map((waveNumber) => {
    let orientationalSum = 0;
    for (const sample of quadrature) {
      let real = 0; let imaginary = 0; let selfCorrection = 0;
      for (const term of prepared) {
        let phase = 0; let variance = 0;
        for (let row = 0; row < dimension; row++) {
          phase += sample.direction[row] * term.position[row];
          for (let column = 0; column < dimension; column++) variance += sample.direction[row]
            * term.tensor[row][column] * sample.direction[column];
        }
        const attenuation = Math.exp(-.5 * waveNumber * waveNumber * Math.max(0, variance));
        const angle = waveNumber * phase;
        real += term.weight * attenuation * Math.cos(angle);
        imaginary += term.weight * attenuation * Math.sin(angle);
        selfCorrection += term.weight * term.weight * (1 - attenuation * attenuation);
      }
      orientationalSum += sample.weight * (real * real + imaginary * imaginary + selfCorrection);
    }
    return Math.max(0, orientationalSum / selfWeightSquares);
  });
  return { q, values, dimension, qMin, qMax, selfWeightSquares,
    coherentDisplacementAttenuation: true, fullAnisotropicCovarianceUsed: true,
    orientationQuadrature: dimension === 2 ? "96-direction circle" : "96-direction Fibonacci sphere",
    quadratureDirections: quadrature.length,
    anisotropicSiteTerms: prepared.filter((term) => !term.isotropic).length,
    diffuseRedistributionIncluded: false };
}

export function summarizeStructureFactor(structureFactor) {
  const { q, values } = structureFactor;
  if (!values.length) return { peakQ: 0, peakHeight: 0, peakProminence: 0, highQMean: 0 };
  const localPeaks = values.map((value, index) => ({ value, index }))
    .filter(({ value, index }) => index > 0 && index < values.length - 1
      && value >= values[index - 1] && value > values[index + 1]);
  const strongest = (localPeaks.length ? localPeaks : values.map((value, index) => ({ value, index })))
    .sort((first, second) => second.value - first.value || first.index - second.index)[0];
  const highQ = values.slice(Math.floor(values.length * .72));
  const highQMean = highQ.reduce((sum, value) => sum + value, 0) / Math.max(1, highQ.length);
  const background = values.reduce((sum, value) => sum + value, 0) / values.length;
  return {
    peakQ: q[strongest.index],
    peakHeight: strongest.value,
    peakProminence: strongest.value / Math.max(1e-9, background),
    highQMean,
  };
}

export function compareStructureFactors(first, second) {
  const comparable = first?.values?.length && first.values.length === second?.values?.length
    && first.dimension === second.dimension && first.q?.every((value, index) =>
      Math.abs(value - second.q[index]) <= 1e-10);
  if (!comparable) throw new Error("structure-factor comparison requires matching dimension and q grid");
  const firstSummary = first.summary || summarizeStructureFactor(first);
  const secondSummary = second.summary || summarizeStructureFactor(second);
  return {
    spectralShapeDistance: jensenShannonDistance(first.values, second.values),
    peakQBefore: firstSummary.peakQ,
    peakQAfter: secondSummary.peakQ,
    peakQDelta: secondSummary.peakQ - firstSummary.peakQ,
    peakProminenceBefore: firstSummary.peakProminence,
    peakProminenceAfter: secondSummary.peakProminence,
    peakProminenceDelta: secondSummary.peakProminence - firstSummary.peakProminence,
    highQMeanBefore: firstSummary.highQMean,
    highQMeanAfter: secondSummary.highQMean,
    highQMeanDelta: secondSummary.highQMean - firstSummary.highQMean,
  };
}

export function legendrePolynomial(order, value) {
  if (!Number.isInteger(order) || order < 0) throw new Error("Legendre order must be a non-negative integer");
  if (!Number.isFinite(value)) throw new Error("Legendre input must be finite");
  const x = Math.max(-1, Math.min(1, value));
  if (order === 0) return 1;
  if (order === 1) return x;
  let previous = 1;
  let current = x;
  for (let degree = 2; degree <= order; degree++) {
    const next = ((2 * degree - 1) * x * current - (degree - 1) * previous) / degree;
    previous = current;
    current = next;
  }
  return current;
}

function normalizedVector(vector) {
  if (!Array.isArray(vector) || vector.length !== 3 || vector.some((value) => !Number.isFinite(value))) {
    throw new Error("orientational-order neighbor vectors must be finite Cartesian triples");
  }
  const length = Math.hypot(...vector);
  return length > 1e-12 ? vector.map((value) => value / length) : null;
}

function planeBasis(normal) {
  const unitNormal = normalizedVector(normal || [0, 0, 1]);
  if (!unitNormal) throw new Error("2D orientational order requires a non-zero plane normal");
  const reference = Math.abs(unitNormal[2]) < .9 ? [0, 0, 1] : [0, 1, 0];
  const first = normalizedVector([
    reference[1] * unitNormal[2] - reference[2] * unitNormal[1],
    reference[2] * unitNormal[0] - reference[0] * unitNormal[2],
    reference[0] * unitNormal[1] - reference[1] * unitNormal[0],
  ]);
  const second = [
    unitNormal[1] * first[2] - unitNormal[2] * first[1],
    unitNormal[2] * first[0] - unitNormal[0] * first[2],
    unitNormal[0] * first[1] - unitNormal[1] * first[0],
  ];
  return [first, second, unitNormal];
}

/**
 * Dimension-aware local orientational order.  In 3D this evaluates the
 * rotational invariant Steinhardt q_l magnitude through the Legendre
 * addition theorem, avoiding any global reference frame.  In 2D it evaluates
 * the l-fold bond-orientational magnitude |psi_l| in the inferred material
 * plane.  Values lie in [0, 1]; this is a structural descriptor, not an energy.
 */
export function localOrientationalOrder(neighborVectorsByCenter, dimension = 3, {
  harmonic = 6,
  planeNormal = [0, 0, 1],
} = {}) {
  if (!Array.isArray(neighborVectorsByCenter)) throw new Error("local orientational order requires one neighbor-vector list per center");
  if (dimension !== 2 && dimension !== 3) throw new Error("local orientational order supports intrinsic dimension 2 or 3");
  if (!Number.isInteger(harmonic) || harmonic < 1) throw new Error("orientational harmonic must be a positive integer");
  const basis = dimension === 2 ? planeBasis(planeNormal) : null;
  return neighborVectorsByCenter.map((vectors) => {
    if (!Array.isArray(vectors)) throw new Error("each orientational-order center requires an array of neighbor vectors");
    const unit = vectors.map(normalizedVector).filter(Boolean);
    if (!unit.length) return 0;
    if (dimension === 2) {
      let real = 0;
      let imaginary = 0;
      unit.forEach((vector) => {
        const normalComponent = vector[0] * basis[2][0] + vector[1] * basis[2][1] + vector[2] * basis[2][2];
        const projected = vector.map((value, axis) => value - normalComponent * basis[2][axis]);
        const x = projected[0] * basis[0][0] + projected[1] * basis[0][1] + projected[2] * basis[0][2];
        const y = projected[0] * basis[1][0] + projected[1] * basis[1][1] + projected[2] * basis[1][2];
        const angle = Math.atan2(y, x) * harmonic;
        real += Math.cos(angle);
        imaginary += Math.sin(angle);
      });
      return Math.min(1, Math.hypot(real, imaginary) / unit.length);
    }
    let invariant = 0;
    unit.forEach((first) => unit.forEach((second) => {
      invariant += legendrePolynomial(harmonic,
        first[0] * second[0] + first[1] * second[1] + first[2] * second[2]);
    }));
    return Math.min(1, Math.sqrt(Math.max(0, invariant / (unit.length * unit.length))));
  });
}

export function orientationalOrderDistribution(values, bins = DEFAULT_ORDER_BINS) {
  if (!Array.isArray(values) || values.some((value) => !Number.isFinite(value))) {
    throw new Error("orientational-order distribution requires finite values");
  }
  if (!Number.isInteger(bins) || bins < 2) throw new Error("orientational-order distribution requires at least two bins");
  const histogram = new Array(bins).fill(0);
  values.forEach((value) => {
    const index = Math.min(bins - 1, Math.max(0, Math.floor(Math.max(0, Math.min(1, value)) * bins)));
    histogram[index]++;
  });
  if (values.length) histogram.forEach((value, index) => { histogram[index] = value / values.length; });
  const sorted = [...values].sort((first, second) => first - second);
  const mean = values.reduce((sum, value) => sum + value, 0) / Math.max(1, values.length);
  const median = sorted.length ? sorted[Math.floor((sorted.length - 1) / 2)] : 0;
  const highFraction = values.filter((value) => value >= .7).length / Math.max(1, values.length);
  return { histogram, mean, median, highFraction, bins, count: values.length };
}

export function jensenShannonDistance(first, second) {
  if (!Array.isArray(first) || !Array.isArray(second) || first.length !== second.length || !first.length) {
    throw new Error("Jensen-Shannon distance requires equal non-empty distributions");
  }
  if ([...first, ...second].some((value) => !Number.isFinite(value) || value < 0)) {
    throw new Error("Jensen-Shannon distance requires finite non-negative weights");
  }
  const firstTotal = first.reduce((sum, value) => sum + value, 0);
  const secondTotal = second.reduce((sum, value) => sum + value, 0);
  if (!firstTotal && !secondTotal) return 0;
  if (!firstTotal || !secondTotal) return 1;
  const p = first.map((value) => value / firstTotal);
  const q = second.map((value) => value / secondTotal);
  const midpoint = p.map((value, index) => (value + q[index]) / 2);
  const divergence = (distribution) => distribution.reduce((sum, value, index) =>
    sum + (value > 0 ? value * Math.log2(value / midpoint[index]) : 0), 0);
  return Math.min(1, Math.sqrt(Math.max(0, (divergence(p) + divergence(q)) / 2)));
}
