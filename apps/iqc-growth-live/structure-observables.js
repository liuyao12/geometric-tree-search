const DEFAULT_Q_MIN = 2;
const DEFAULT_Q_MAX = 20;
const DEFAULT_Q_BINS = 48;

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
