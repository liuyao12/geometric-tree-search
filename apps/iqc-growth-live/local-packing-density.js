function squaredDistance(first, second) {
  let total = 0;
  for (let axis = 0; axis < first.length; axis++) {
    const delta = first[axis] - second[axis]; total += delta * delta;
  }
  return total;
}

function quantile(values, fraction) {
  if (!values.length) return null;
  const sorted = [...values].sort((first, second) => first - second);
  const position = Math.max(0, Math.min(sorted.length - 1, fraction * (sorted.length - 1)));
  const lower = Math.floor(position); const upper = Math.ceil(position);
  return sorted[lower] + (sorted[upper] - sorted[lower]) * (position - lower);
}

function radialSamples(positions, maximumCenters) {
  if (!positions.length) return [];
  const dimension = positions[0].length;
  const centroid = new Array(dimension).fill(0);
  positions.forEach((point) => point.forEach((value, axis) => { centroid[axis] += value / positions.length; }));
  const ordered = positions.map((point, index) => ({ index, radius2: squaredDistance(point, centroid) }))
    .sort((first, second) => first.radius2 - second.radius2 || first.index - second.index);
  if (ordered.length <= maximumCenters) return ordered;
  return Array.from({ length: maximumCenters }, (_, sample) => ordered[Math.min(ordered.length - 1,
    Math.floor((sample + .5) * ordered.length / maximumCenters))]);
}

function densityAt(positions, centerIndex, rank, dimension) {
  const distances2 = [];
  for (let index = 0; index < positions.length; index++) {
    if (index !== centerIndex) distances2.push(squaredDistance(positions[centerIndex], positions[index]));
  }
  distances2.sort((first, second) => first - second);
  const radius = Math.sqrt(distances2[Math.min(rank - 1, distances2.length - 1)] || 0);
  const measure = dimension === 2 ? Math.PI * radius ** 2 : 4 * Math.PI * radius ** 3 / 3;
  return { radius, density: measure > 1e-18 ? Math.min(rank, distances2.length) / measure : null };
}

function sampledDensities(positions, rank, dimension, maximumCenters) {
  const samples = radialSamples(positions, maximumCenters);
  return samples.map((sample, radialOrder) => ({ ...sample, radialOrder,
    ...densityAt(positions, sample.index, rank, dimension) }))
    .filter((record) => Number.isFinite(record.density));
}

export function localPackingDensityAudit(currentPositions, referencePositions, {
  dimension = 3, neighborRank = 6, maximumCenters = 128, histogramBins = 20,
  histogramMaximumRatio = 2.5,
} = {}) {
  const rank = Math.max(1, Math.floor(neighborRank));
  const validDimension = dimension === 2 ? 2 : 3;
  if (currentPositions.length <= rank || referencePositions.length <= rank) return {
    available: false, reason: `at least ${rank + 1} current and reference sites are required`,
    neighborRank: rank, dimension: validDimension, currentSites: currentPositions.length,
    referenceSites: referencePositions.length, targetUsed: false,
  };
  const referenceRecords = sampledDensities(referencePositions, rank, validDimension, maximumCenters);
  const referenceCoreCount = Math.max(1, Math.ceil(referenceRecords.length / 2));
  const referenceCoreDensity = quantile(referenceRecords.slice(0, referenceCoreCount)
    .map((record) => record.density), .5);
  const records = sampledDensities(currentPositions, rank, validDimension, maximumCenters)
    .map((record) => ({ ...record, relativeDensity: record.density / referenceCoreDensity,
      relativeLocalVolume: referenceCoreDensity / record.density }));
  const coreCount = Math.max(1, Math.ceil(records.length / 2));
  const surfaceStart = Math.max(0, Math.floor(records.length * .75));
  const ratios = records.map((record) => record.relativeDensity);
  const histogram = new Array(histogramBins).fill(0);
  ratios.forEach((ratio) => {
    const index = Math.min(histogramBins - 1, Math.max(0,
      Math.floor(ratio / histogramMaximumRatio * histogramBins)));
    histogram[index]++;
  });
  return {
    available: true,
    dimension: validDimension,
    neighborRank: rank,
    currentSites: currentPositions.length,
    referenceSites: referencePositions.length,
    sampledCenters: records.length,
    referenceSampledCenters: referenceRecords.length,
    referenceCoreDensity,
    medianRelativeDensity: quantile(ratios, .5),
    percentile10RelativeDensity: quantile(ratios, .1),
    percentile90RelativeDensity: quantile(ratios, .9),
    medianRelativeLocalVolume: quantile(records.map((record) => record.relativeLocalVolume), .5),
    coreMedianRelativeDensity: quantile(records.slice(0, coreCount).map((record) => record.relativeDensity), .5),
    surfaceMedianRelativeDensity: quantile(records.slice(surfaceStart).map((record) => record.relativeDensity), .5),
    underpackedFraction: ratios.filter((value) => value < .8).length / records.length,
    referenceLikeFraction: ratios.filter((value) => value >= .8 && value <= 1.2).length / records.length,
    overpackedFraction: ratios.filter((value) => value > 1.2).length / records.length,
    histogram,
    histogramMaximumRatio,
    histogramOverflowIncludedInLastBin: true,
    centerSampling: `radial quantiles, maximum ${maximumCenters}`,
    coreDefinition: "inner half of sampled centers by centroid radius",
    surfaceDefinition: "outer quarter of sampled centers by centroid radius",
    referenceDefinition: "median k-nearest-neighbor number density over the inner half of the supplied configuration",
    finiteObservationNoPeriodicImages: true,
    translationInvariant: true,
    properRotationInvariant: true,
    atomPermutationInvariant: true,
    uniformScaleInvariantWhenCurrentAndReferenceShareScale: true,
    targetUsed: false,
    usedAsGrowthInput: false,
    massDensityInferred: false,
    thermodynamicVolumeInferred: false,
    porosityInferred: false,
    pressureInferred: false,
    freeEnergyInferred: false,
    physicalTimeIntegrated: false,
  };
}
