function coordinates(atom) {
  const point = atom?.p || atom?.position || atom;
  const values = Array.isArray(point) ? point : [point?.x, point?.y, point?.z];
  if (values.length !== 3 || values.some((value) => !Number.isFinite(Number(value)))) {
    throw new Error("phase evidence requires finite three-dimensional positions");
  }
  return values.map(Number);
}

function symmetricEigenvalues3(matrix) {
  const values = matrix.map((row) => row.slice());
  for (let iteration = 0; iteration < 32; iteration++) {
    let first = 0; let second = 1;
    [[0, 1], [0, 2], [1, 2]].forEach(([row, column]) => {
      if (Math.abs(values[row][column]) > Math.abs(values[first][second])) {
        first = row; second = column;
      }
    });
    if (Math.abs(values[first][second]) < 1e-14) break;
    const angle = .5 * Math.atan2(2 * values[first][second], values[second][second] - values[first][first]);
    const cosine = Math.cos(angle); const sine = Math.sin(angle);
    const rotation = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
    rotation[first][first] = cosine; rotation[second][second] = cosine;
    rotation[first][second] = sine; rotation[second][first] = -sine;
    const intermediate = Array.from({ length: 3 }, () => [0, 0, 0]);
    const updated = Array.from({ length: 3 }, () => [0, 0, 0]);
    for (let row = 0; row < 3; row++) for (let column = 0; column < 3; column++) {
      for (let axis = 0; axis < 3; axis++) intermediate[row][column] += values[row][axis] * rotation[axis][column];
    }
    for (let row = 0; row < 3; row++) for (let column = 0; column < 3; column++) {
      for (let axis = 0; axis < 3; axis++) updated[row][column] += rotation[axis][row] * intermediate[axis][column];
    }
    for (let row = 0; row < 3; row++) for (let column = 0; column < 3; column++) values[row][column] = updated[row][column];
  }
  return [values[0][0], values[1][1], values[2][2]].map((value) => Math.max(0, value)).sort((a, b) => b - a);
}

export function centeredStructuralWindow(source, maximumAtoms) {
  if (!Array.isArray(source)) throw new Error("phase evidence source must be an array");
  if (!Number.isInteger(maximumAtoms) || maximumAtoms < 1) throw new Error("phase evidence window size must be a positive integer");
  if (source.length <= maximumAtoms) return source.slice();
  const center = source.reduce((sum, atom) => {
    const point = coordinates(atom);
    return sum.map((value, axis) => value + point[axis]);
  }, [0, 0, 0]).map((value) => value / source.length);
  return source.map((atom, index) => {
    const point = coordinates(atom);
    const radiusSquared = point.reduce((sum, value, axis) => sum + (value - center[axis]) ** 2, 0);
    return { atom, index, radiusSquared };
  }).sort((first, second) => first.radiusSquared - second.radiusSquared || first.index - second.index)
    .slice(0, maximumAtoms).map((entry) => entry.atom);
}

export function inferPointSetDimension(source, planarVarianceRatio = .02) {
  if (!Array.isArray(source) || source.length < 4) return {
    dimension: 3, eigenvalues: [0, 0, 0], planarityRatio: 1,
    localPlanarityRatio: 1, basis: "insufficient geometry", sufficient: false,
  };
  const points = source.map(coordinates);
  const center = points.reduce((sum, point) => sum.map((value, axis) => value + point[axis]), [0, 0, 0])
    .map((value) => value / points.length);
  const covariance = Array.from({ length: 3 }, () => [0, 0, 0]);
  points.forEach((point) => {
    const delta = point.map((value, axis) => value - center[axis]);
    for (let row = 0; row < 3; row++) for (let column = 0; column < 3; column++) {
      covariance[row][column] += delta[row] * delta[column] / points.length;
    }
  });
  const eigenvalues = symmetricEigenvalues3(covariance);
  const planarityRatio = eigenvalues[0] > 1e-12 ? eigenvalues[2] / eigenvalues[0] : 1;
  // A multilayer 2D material has finite variance normal to the sheets, so its
  // global covariance is full rank even though every local atomic environment
  // is intrinsically planar.  Audit six nearest neighbours around a bounded,
  // deterministic sample of sites and use the median local spectrum as the
  // second geometry-only test.  This also resists finite-window surfaces: a
  // majority of a volumetric nucleus still has non-coplanar local support.
  const sampledIndices = points.length <= 96
    ? points.map((_, index) => index)
    : Array.from({ length: 96 }, (_, index) => Math.floor(index * points.length / 96));
  const localRatios = sampledIndices.map((centerIndex) => {
    const neighbors = points.map((point, index) => ({
      index,
      distanceSquared: point.reduce((sum, value, axis) =>
        sum + (value - points[centerIndex][axis]) ** 2, 0),
    })).filter((entry) => entry.index !== centerIndex)
      .sort((first, second) => first.distanceSquared - second.distanceSquared || first.index - second.index)
      .slice(0, Math.min(6, points.length - 1));
    const local = [points[centerIndex], ...neighbors.map((entry) => points[entry.index])];
    const localCenter = local.reduce((sum, point) => sum.map((value, axis) => value + point[axis]), [0, 0, 0])
      .map((value) => value / local.length);
    const localCovariance = Array.from({ length: 3 }, () => [0, 0, 0]);
    local.forEach((point) => {
      const delta = point.map((value, axis) => value - localCenter[axis]);
      for (let row = 0; row < 3; row++) for (let column = 0; column < 3; column++) {
        localCovariance[row][column] += delta[row] * delta[column] / local.length;
      }
    });
    const localEigenvalues = symmetricEigenvalues3(localCovariance);
    return localEigenvalues[0] > 1e-12 ? localEigenvalues[2] / localEigenvalues[0] : 1;
  }).sort((first, second) => first - second);
  const middle = Math.floor(localRatios.length / 2);
  const localPlanarityRatio = localRatios.length % 2
    ? localRatios[middle] : (localRatios[middle - 1] + localRatios[middle]) / 2;
  const globallyPlanar = planarityRatio <= planarVarianceRatio;
  const locallyPlanar = localPlanarityRatio <= planarVarianceRatio;
  return {
    dimension: globallyPlanar || locallyPlanar ? 2 : 3,
    eigenvalues,
    planarityRatio,
    localPlanarityRatio,
    basis: globallyPlanar ? "global covariance" : locallyPlanar ? "median local covariance" : "volumetric covariance",
    sufficient: true,
  };
}

/**
 * Coordinate-free whole-point-set shape observables.  The covariance spectrum
 * is invariant under translation and every orthogonal change of frame; the
 * caller supplies only the conversion from coordinate units to a physical
 * length unit.  The phenotype is deliberately descriptive rather than a
 * crystal-habit, surface-energy, or kinetic classification.
 */
export function covarianceMorphology(source, lengthScale = 1, planarVarianceRatio = .02) {
  if (!Array.isArray(source)) throw new Error("morphology source must be an array");
  if (!(Number.isFinite(lengthScale) && lengthScale > 0)) {
    throw new Error("morphology length scale must be finite and positive");
  }
  if (!source.length) return {
    atomCount: 0, sufficient: false, phenotype: "empty", intrinsicDimension: null,
    dimensionInferenceBasis: "insufficient geometry", principalVarianceFractions: [0, 0, 0],
    principalVariance: [0, 0, 0], radiusOfGyration: 0, maximumExtent: 0,
    relativeShapeAnisotropy: 0, planarityRatio: 1, localPlanarityRatio: 1,
  };
  const points = source.map(coordinates);
  const center = points.reduce((sum, point) => sum.map((value, axis) => value + point[axis]), [0, 0, 0])
    .map((value) => value / points.length);
  const dimension = inferPointSetDimension(source, planarVarianceRatio);
  const principalVariance = dimension.eigenvalues.map((value) => value * lengthScale ** 2);
  const varianceSum = principalVariance.reduce((sum, value) => sum + value, 0);
  const principalVarianceFractions = principalVariance
    .map((value) => varianceSum > 1e-15 ? value / varianceSum : 0);
  const squaredVarianceSum = principalVariance.reduce((sum, value) => sum + value * value, 0);
  const relativeShapeAnisotropy = varianceSum > 1e-15
    ? Math.max(0, Math.min(1, 1.5 * squaredVarianceSum / varianceSum ** 2 - .5)) : 0;
  const maximumExtent = points.reduce((maximum, point) => Math.max(maximum,
    Math.hypot(...point.map((value, axis) => value - center[axis]))), 0) * lengthScale;
  const secondToFirst = dimension.eigenvalues[0] > 1e-12
    ? dimension.eigenvalues[1] / dimension.eigenvalues[0] : 1;
  const thirdToFirst = dimension.eigenvalues[0] > 1e-12
    ? dimension.eigenvalues[2] / dimension.eigenvalues[0] : 1;
  const phenotype = !dimension.sufficient ? "insufficient"
    : secondToFirst <= .18 ? "needle-like"
      : thirdToFirst <= .08 && secondToFirst > .25 ? "plate-like"
        : relativeShapeAnisotropy >= .35 ? "elongated" : "compact";
  return {
    atomCount: source.length, sufficient: dimension.sufficient, phenotype,
    intrinsicDimension: dimension.dimension, dimensionInferenceBasis: dimension.basis,
    principalVarianceFractions, principalVariance,
    radiusOfGyration: Math.sqrt(Math.max(0, varianceSum)), maximumExtent,
    relativeShapeAnisotropy, planarityRatio: dimension.planarityRatio,
    localPlanarityRatio: dimension.localPlanarityRatio,
  };
}

/**
 * Fit log(mass) = intercept + D_M log(radius) across a finite sequence of
 * certified structural states. D_M is a descriptive mass-radius exponent for
 * the observed scale window. It is not promoted to an asymptotic fractal
 * dimension, kinetic exponent, or rate law.
 */
export function finiteMassRadiusScaling(states, {
  minimumStates = 3,
  minimumRadiusRatio = 1.25,
  minimumRSquared = .8,
} = {}) {
  if (!Array.isArray(states)) throw new Error("mass-radius scaling states must be an array");
  if (!(Number.isInteger(minimumStates) && minimumStates >= 3)) {
    throw new Error("mass-radius scaling requires at least three declared states");
  }
  if (!(Number.isFinite(minimumRadiusRatio) && minimumRadiusRatio > 1)) {
    throw new Error("mass-radius scaling radius ratio must exceed one");
  }
  if (!(Number.isFinite(minimumRSquared) && minimumRSquared >= 0 && minimumRSquared <= 1)) {
    throw new Error("mass-radius scaling R-squared threshold must lie in [0,1]");
  }
  const samples = states.map((state, index) => ({
    index,
    mass: Number(state?.mass ?? state?.atomCount ?? state?.atoms),
    radius: Number(state?.radius ?? state?.radiusOfGyration ?? state?.radiusOfGyrationAngstrom),
    dimension: Number(state?.dimension ?? state?.intrinsicDimension),
  })).filter((sample) => sample.mass > 0 && sample.radius > 0
    && Number.isFinite(sample.mass) && Number.isFinite(sample.radius));
  const radiusMinimum = samples.length ? Math.min(...samples.map((sample) => sample.radius)) : null;
  const radiusMaximum = samples.length ? Math.max(...samples.map((sample) => sample.radius)) : null;
  const radiusRatio = radiusMinimum > 0 ? radiusMaximum / radiusMinimum : null;
  const base = {
    sampleCount: samples.length, minimumStates, radiusMinimum, radiusMaximum, radiusRatio,
    minimumRadiusRatio, minimumRSquared,
    finiteWindowOnly: true, asymptoticFractalDimensionInferred: false,
    physicalTimeUsed: false, kineticsInferred: false, coordinatesUsed: false,
  };
  if (samples.length < minimumStates) return {
    ...base, status: "insufficient states", sufficient: false, exponent: null,
    intercept: null, rSquared: null, fitReliable: false, referenceDimension: null,
    regime: "unresolved",
  };
  if (!(radiusRatio >= minimumRadiusRatio)) return {
    ...base, status: "insufficient radius span", sufficient: false, exponent: null,
    intercept: null, rSquared: null, fitReliable: false, referenceDimension: null,
    regime: "unresolved",
  };
  const x = samples.map((sample) => Math.log(sample.radius));
  const y = samples.map((sample) => Math.log(sample.mass));
  const meanX = x.reduce((sum, value) => sum + value, 0) / x.length;
  const meanY = y.reduce((sum, value) => sum + value, 0) / y.length;
  const varianceX = x.reduce((sum, value) => sum + (value - meanX) ** 2, 0);
  if (!(varianceX > 1e-15)) return {
    ...base, status: "degenerate radius window", sufficient: false, exponent: null,
    intercept: null, rSquared: null, fitReliable: false, referenceDimension: null,
    regime: "unresolved",
  };
  const covariance = x.reduce((sum, value, index) =>
    sum + (value - meanX) * (y[index] - meanY), 0);
  const exponent = covariance / varianceX;
  const intercept = meanY - exponent * meanX;
  const residual = y.map((value, index) => value - (intercept + exponent * x[index]));
  const residualSumSquares = residual.reduce((sum, value) => sum + value * value, 0);
  const totalSumSquares = y.reduce((sum, value) => sum + (value - meanY) ** 2, 0);
  const rSquared = totalSumSquares > 1e-15 ? Math.max(0, 1 - residualSumSquares / totalSumSquares) : 1;
  const dimensions = samples.map((sample) => sample.dimension).filter((value) => value === 2 || value === 3)
    .sort((first, second) => first - second);
  const referenceDimension = dimensions.length ? dimensions[Math.floor(dimensions.length / 2)] : null;
  const fitReliable = rSquared >= minimumRSquared;
  const regime = !fitReliable || !referenceDimension ? "mixed finite-window scaling"
    : exponent > referenceDimension + .35 ? "densifying within window"
      : exponent < referenceDimension - .55 ? "open / anisotropic within window"
        : "dimension-consistent filling";
  return {
    ...base, status: fitReliable ? "finite scaling resolved" : "low fit quality",
    sufficient: true, exponent, intercept, rSquared, fitReliable,
    referenceDimension, regime,
    residualRootMeanSquare: Math.sqrt(residualSumSquares / residual.length),
  };
}

export function phaseComparisonRadius(atomCount, dimension) {
  if (!Number.isInteger(atomCount) || atomCount < 1) throw new Error("phase comparison atom count must be positive");
  if (dimension !== 2 && dimension !== 3) throw new Error("phase comparison dimension must be two or three");
  const scale = dimension === 2 ? Math.sqrt(atomCount) * .32 : Math.cbrt(atomCount) * .55;
  return Math.min(3.2, Math.max(1.5, scale));
}
