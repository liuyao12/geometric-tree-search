/** Robust local pair-distance variation across fixed-topology snapshots.
 *
 * Pair distances are evaluated independently inside each frame. Translation,
 * global proper rotation, atom permutation outside the declared identity map,
 * and snapshot order cannot affect the statistic. It is structural uncertainty,
 * not temperature, time, a force, or an independent-sample estimate.
 */

function quantile(sorted, fraction) {
  if (!sorted.length) return 0;
  const position = Math.max(0, Math.min(1, fraction)) * (sorted.length - 1);
  const lower = Math.floor(position);
  const upper = Math.ceil(position);
  if (lower === upper) return sorted[lower];
  return sorted[lower] * (upper - position) + sorted[upper] * (position - lower);
}

function sampleStandardDeviation(values) {
  if (values.length < 2) return 0;
  const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
  return Math.sqrt(values.reduce((sum, value) => sum + (value - mean) ** 2, 0) / (values.length - 1));
}

export function learnLocalPairDistanceUncertaintyEnsemble(frames, {
  referenceFrameIndex = 0,
  localCutoff,
  upperQuantile = .9,
} = {}) {
  if (!Array.isArray(frames) || frames.length < 2) return {
    available: false,
    reason: "at least two fixed-topology frames are required",
    frameCount: frames?.length || 0,
    atomPresentations: frames?.reduce?.((sum, frame) => sum + (frame.species?.length || 0), 0) || 0,
    localPairCount: 0,
    medianPairDistanceSigma: 0,
    upperPairDistanceSigma: 0,
    maximumPairDistanceSigma: 0,
    upperQuantile,
  };
  if (!(Number.isFinite(localCutoff) && localCutoff > 0)) throw new Error("ensemble uncertainty requires a positive local cutoff");
  if (!(Number.isFinite(upperQuantile) && upperQuantile >= .5 && upperQuantile <= 1)) {
    throw new Error("ensemble uncertainty upper quantile must lie in [0.5, 1]");
  }
  if (!Number.isInteger(referenceFrameIndex) || referenceFrameIndex < 0 || referenceFrameIndex >= frames.length) {
    throw new Error("ensemble uncertainty reference frame is out of range");
  }
  const referenceSpecies = frames[referenceFrameIndex].species;
  frames.forEach((frame, frameIndex) => {
    if (!Array.isArray(frame.species) || typeof frame.distance !== "function") {
      throw new Error(`ensemble uncertainty frame ${frameIndex + 1} lacks species or a distance callback`);
    }
    if (frame.species.length !== referenceSpecies.length
      || frame.species.some((species, index) => species !== referenceSpecies[index])) {
      throw new Error(`ensemble uncertainty frame ${frameIndex + 1} changes fixed atom identity`);
    }
  });
  const sigmas = [];
  for (let first = 0; first < referenceSpecies.length - 1; first++) {
    for (let second = first + 1; second < referenceSpecies.length; second++) {
      const referenceDistance = frames[referenceFrameIndex].distance(first, second);
      if (!(referenceDistance > 1e-9) || referenceDistance > localCutoff) continue;
      const values = frames.map((frame) => frame.distance(first, second));
      if (values.some((value) => !(value > 1e-9) || !Number.isFinite(value))) continue;
      sigmas.push(sampleStandardDeviation(values));
    }
  }
  sigmas.sort((first, second) => first - second);
  return {
    available: sigmas.length > 0,
    reason: sigmas.length ? "fixed-identity local pair distances pooled within frames" : "no local pairs fall inside the cutoff",
    frameCount: frames.length,
    atomPresentations: frames.reduce((sum, frame) => sum + frame.species.length, 0),
    localPairCount: sigmas.length,
    medianPairDistanceSigma: quantile(sigmas, .5),
    upperPairDistanceSigma: quantile(sigmas, upperQuantile),
    maximumPairDistanceSigma: sigmas.at(-1) || 0,
    localCutoff,
    upperQuantile,
    crossFramePairsConstructed: false,
    temporalOrderingUsed: false,
    independentSampleCountClaimed: false,
  };
}
