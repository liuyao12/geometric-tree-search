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
