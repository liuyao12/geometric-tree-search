const PASCAL_PER_GIGAPASCAL = 1e9;

function finiteMatrix3(value) {
  return Array.isArray(value) && value.length === 3
    && value.every((row) => Array.isArray(row) && row.length === 3
      && row.every((component) => Number.isFinite(Number(component))));
}

export function nomadStressTensorGigaPascal(valuePascal) {
  if (!finiteMatrix3(valuePascal)) return null;
  const tensor = valuePascal.map((row) => row.map((component) => Number(component) / PASCAL_PER_GIGAPASCAL));
  return tensor.map((row, first) => row.map((component, second) =>
    .5 * (component + tensor[second][first])));
}

export function stressTensorSummary(tensorGigaPascal) {
  if (!finiteMatrix3(tensorGigaPascal)) return null;
  const tensor = tensorGigaPascal.map((row) => row.map(Number));
  const trace = tensor[0][0] + tensor[1][1] + tensor[2][2];
  const hydrostatic = trace / 3;
  const frobenius = Math.sqrt(tensor.reduce((sum, row) =>
    sum + row.reduce((rowSum, value) => rowSum + value * value, 0), 0));
  const deviatoric = tensor.map((row, first) => row.map((value, second) =>
    value - (first === second ? hydrostatic : 0)));
  const deviatoricFrobenius = Math.sqrt(deviatoric.reduce((sum, row) =>
    sum + row.reduce((rowSum, value) => rowSum + value * value, 0), 0));
  return Object.freeze({
    tensorGigaPascal: Object.freeze(tensor.map((row) => Object.freeze(row))),
    traceGigaPascal: trace,
    hydrostaticGigaPascal: hydrostatic,
    frobeniusGigaPascal: frobenius,
    deviatoricFrobeniusGigaPascal: deviatoricFrobenius,
  });
}

export function normalizedStressShapeDeformation(tensorGigaPascal, magnitude, polarity = 1) {
  const summary = stressTensorSummary(tensorGigaPascal);
  const resolvedMagnitude = Number(magnitude);
  const resolvedPolarity = Number(polarity) < 0 ? -1 : 1;
  if (!summary || !(summary.frobeniusGigaPascal > 0)
    || !Number.isFinite(resolvedMagnitude) || resolvedMagnitude < 0 || resolvedMagnitude > .1) return null;
  const scale = resolvedPolarity * resolvedMagnitude / summary.frobeniusGigaPascal;
  return summary.tensorGigaPascal.map((row, first) => row.map((value, second) =>
    (first === second ? 1 : 0) + scale * value));
}
