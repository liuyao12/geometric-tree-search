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
    .sort((first, second) => first.radius2 - second.radius2);
  if (ordered.length <= maximumCenters) return ordered;
  const maximumRadius2 = Math.max(1e-18, ordered.at(-1).radius2);
  const radialKey = (record) => Math.round(record.radius2 / maximumRadius2 * 1e10);
  const selectedKeys = new Set(Array.from({ length: maximumCenters }, (_, sample) => radialKey(ordered[
    Math.min(ordered.length - 1, Math.floor((sample + .5) * ordered.length / maximumCenters))])));
  // A radial tie is retained as a whole. Splitting one symmetry shell by input
  // index would make the finite estimator depend on atom order.
  return ordered.filter((record) => selectedKeys.has(radialKey(record)));
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

function radialRecords(positions, species = []) {
  if (!positions.length) return [];
  const centroid = new Array(positions[0].length).fill(0);
  positions.forEach((point) => point.forEach((value, axis) => { centroid[axis] += value / positions.length; }));
  const records = positions.map((point, index) => ({ index, species: species[index] || "site",
    radius2: squaredDistance(point, centroid) }));
  const maximumRadius2 = Math.max(1e-18, ...records.map((record) => record.radius2));
  return records.map((record) => ({ ...record,
    normalizedRadius: Math.sqrt(record.radius2 / maximumRadius2) }));
}

function speciesFractions(records, vocabulary) {
  const counts = Object.fromEntries(vocabulary.map((symbol) => [symbol, 0]));
  records.forEach((record) => { counts[record.species] = (counts[record.species] || 0) + 1; });
  return Object.fromEntries(vocabulary.map((symbol) => [symbol, counts[symbol] / Math.max(1, records.length)]));
}

function radialProfile(positions, species, densityRecords, referenceDensity, shellCount, vocabulary) {
  const sites = radialRecords(positions, species);
  return Array.from({ length: shellCount }, (_, shell) => {
    const radialMinimum = shell / shellCount;
    const radialMaximum = (shell + 1) / shellCount;
    const within = (radius) => radius >= radialMinimum
      && (shell === shellCount - 1 ? radius <= radialMaximum : radius < radialMaximum);
    const shellSites = sites.filter((record) => within(record.normalizedRadius));
    const shellDensities = densityRecords.filter((record) => {
      const site = sites[record.index]; return site && within(site.normalizedRadius);
    });
    return {
      shell,
      radialMinimum,
      radialMaximum,
      siteCount: shellSites.length,
      sampledDensityCenters: shellDensities.length,
      medianRelativeDensity: quantile(shellDensities.map((record) => record.density / referenceDensity), .5),
      medianRelativeLocalVolume: quantile(shellDensities.map((record) => referenceDensity / record.density), .5),
      speciesFractions: speciesFractions(shellSites, vocabulary),
    };
  });
}

export function localPackingDensityAudit(currentPositions, referencePositions, {
  dimension = 3, neighborRank = 6, maximumCenters = 128, histogramBins = 20,
  histogramMaximumRatio = 2.5, currentSpecies = [], referenceSpecies = [], radialShells = 8,
} = {}) {
  const rank = Math.max(1, Math.floor(neighborRank));
  const validDimension = dimension === 2 ? 2 : 3;
  if (currentPositions.length <= rank || referencePositions.length <= rank) return {
    available: false, reason: `at least ${rank + 1} current and reference sites are required`,
    neighborRank: rank, dimension: validDimension, currentSites: currentPositions.length,
    referenceSites: referencePositions.length, targetUsed: false,
  };
  const referenceRecords = sampledDensities(referencePositions, rank, validDimension, maximumCenters);
  const referenceCoreRadius2 = quantile(referenceRecords.map((record) => record.radius2), .5);
  const referenceCoreDensity = quantile(referenceRecords.filter((record) => record.radius2 <= referenceCoreRadius2)
    .map((record) => record.density), .5);
  const records = sampledDensities(currentPositions, rank, validDimension, maximumCenters)
    .map((record) => ({ ...record, relativeDensity: record.density / referenceCoreDensity,
      relativeLocalVolume: referenceCoreDensity / record.density }));
  const coreRadius2 = quantile(records.map((record) => record.radius2), .5);
  const surfaceRadius2 = quantile(records.map((record) => record.radius2), .75);
  const coreRecords = records.filter((record) => record.radius2 <= coreRadius2);
  const surfaceRecords = records.filter((record) => record.radius2 >= surfaceRadius2);
  const ratios = records.map((record) => record.relativeDensity);
  const vocabulary = [...new Set([...currentSpecies, ...referenceSpecies].filter(Boolean))].sort();
  const shellCount = Math.max(2, Math.min(16, Math.floor(radialShells)));
  const currentRadialProfile = radialProfile(currentPositions, currentSpecies, records,
    referenceCoreDensity, shellCount, vocabulary);
  const referenceRadialProfile = radialProfile(referencePositions, referenceSpecies, referenceRecords,
    referenceCoreDensity, shellCount, vocabulary);
  const currentFractions = speciesFractions(radialRecords(currentPositions, currentSpecies), vocabulary);
  const outerShell = currentRadialProfile.at(-1);
  const surfaceExcess = Object.fromEntries(vocabulary.map((symbol) => [symbol,
    (outerShell?.speciesFractions?.[symbol] || 0) - (currentFractions[symbol] || 0)]));
  const dominantSurfaceExcessSpecies = vocabulary.length ? [...vocabulary].sort((first, second) =>
    surfaceExcess[second] - surfaceExcess[first] || first.localeCompare(second))[0] : null;
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
    coreMedianRelativeDensity: quantile(coreRecords.map((record) => record.relativeDensity), .5),
    surfaceMedianRelativeDensity: quantile(surfaceRecords.map((record) => record.relativeDensity), .5),
    underpackedFraction: ratios.filter((value) => value < .8).length / records.length,
    referenceLikeFraction: ratios.filter((value) => value >= .8 && value <= 1.2).length / records.length,
    overpackedFraction: ratios.filter((value) => value > 1.2).length / records.length,
    histogram,
    histogramMaximumRatio,
    histogramOverflowIncludedInLastBin: true,
    centerSampling: `${maximumCenters} radial quantiles; complete equal-radius ties retained`,
    coreDefinition: "inner half of sampled centers by centroid radius",
    surfaceDefinition: "outer quarter of sampled centers by centroid radius",
    referenceDefinition: "median k-nearest-neighbor number density over the inner half of the supplied configuration",
    radialShellCount: shellCount,
    radialCoordinate: "centroid radius divided by the maximum explicit-site centroid radius",
    radialProfile: currentRadialProfile,
    referenceRadialProfile,
    speciesVocabulary: vocabulary,
    globalSpeciesFractions: currentFractions,
    surfaceExcess,
    dominantSurfaceExcessSpecies,
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
