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

export function phaseComparisonRadius(atomCount, dimension) {
  if (!Number.isInteger(atomCount) || atomCount < 1) throw new Error("phase comparison atom count must be positive");
  if (dimension !== 2 && dimension !== 3) throw new Error("phase comparison dimension must be two or three");
  const scale = dimension === 2 ? Math.sqrt(atomCount) * .32 : Math.cbrt(atomCount) * .55;
  return Math.min(3.2, Math.max(1.5, scale));
}
