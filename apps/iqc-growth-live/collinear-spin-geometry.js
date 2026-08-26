export const COLLINEAR_SPIN_PROVENANCE = Object.freeze({
  source: "https://github.com/nomad-coe/nomad-schema-plugin-run/blob/0f1000184032b742da8b7f0421b5605a5b086918/runschema/calculation.py",
  sourceSchema: "NOMAD runschema.calculation.Charges.spins",
  quantityKind: "signed scalar atomic spin population",
  schemaShape: "n_atoms",
  vectorAxisAvailable: false,
  unitGuaranteedBySchema: false,
  interpretation: "archive-native collinear scalar; sign and magnitude are preserved without inventing a direction or unit",
});

function finiteSite(site) {
  return typeof site?.species === "string"
    && Array.isArray(site.position) && site.position.length === 3
    && site.position.every((value) => Number.isFinite(Number(value)))
    && Number.isFinite(Number(site.spin));
}

function distance(first, second) {
  return Math.hypot(...first.position.map((value, axis) => Number(value) - Number(second.position[axis])));
}

function percentile(values, fraction) {
  if (!values.length) return null;
  const sorted = values.slice().sort((a, b) => a - b);
  return sorted[Math.max(0, Math.min(sorted.length - 1, Math.round(fraction * (sorted.length - 1))))];
}

export function analyzeCollinearSpinGeometry(sites = [], options = {}) {
  const valid = sites.filter(finiteSite).map((site, sourceIndex) => ({
    species: site.species,
    position: site.position.map(Number),
    spin: Number(site.spin),
    sourceIndex: Number.isInteger(site.sourceIndex) ? site.sourceIndex : sourceIndex,
  }));
  if (!valid.length) return {
    available: false,
    reason: "no explicit finite scalar atomic spins",
    suppliedSites: 0,
    inputSites: sites.length,
    coverage: 0,
    provenance: COLLINEAR_SPIN_PROVENANCE,
    targetUsed: false,
    usedForGrowth: false,
  };
  const nearest = new Array(valid.length).fill(Infinity);
  const pairs = [];
  for (let first = 0; first < valid.length; first++) for (let second = first + 1; second < valid.length; second++) {
    const separation = distance(valid[first], valid[second]);
    if (!(separation > 0)) continue;
    nearest[first] = Math.min(nearest[first], separation);
    nearest[second] = Math.min(nearest[second], separation);
    pairs.push({ first, second, separation });
  }
  const nearestFinite = nearest.filter(Number.isFinite);
  const medianNearestDistance = percentile(nearestFinite, .5);
  const requestedReach = Number(options.maximumReach);
  const maximumReach = requestedReach > 0 ? requestedReach
    : Math.max(1e-9, (medianNearestDistance || 1) * 5);
  const binCount = Math.max(3, Math.min(32, Math.round(Number(options.binCount) || 12)));
  const bins = Array.from({ length: binCount }, (_, index) => ({
    index,
    minimumDistance: maximumReach * index / binCount,
    maximumDistance: maximumReach * (index + 1) / binCount,
    pairCount: 0,
    signedProductSum: 0,
    absoluteProductSum: 0,
  }));
  const local = valid.map(() => ({ pairCount: 0, signedProductSum: 0, absoluteProductSum: 0 }));
  let checkedPairs = 0;
  pairs.forEach(({ first, second, separation }) => {
    if (separation > maximumReach + 1e-12) return;
    checkedPairs++;
    const product = valid[first].spin * valid[second].spin;
    const absolute = Math.abs(product);
    const binIndex = Math.min(binCount - 1, Math.floor(separation / maximumReach * binCount));
    const bin = bins[binIndex];
    bin.pairCount++; bin.signedProductSum += product; bin.absoluteProductSum += absolute;
    [first, second].forEach((index) => {
      local[index].pairCount++;
      local[index].signedProductSum += product;
      local[index].absoluteProductSum += absolute;
    });
  });
  const correlation = (record) => record.absoluteProductSum > 1e-15
    ? record.signedProductSum / record.absoluteProductSum : null;
  bins.forEach((bin) => { bin.correlation = correlation(bin); });
  const localRecords = valid.map((site, index) => ({
    ...site,
    neighborPairs: local[index].pairCount,
    localCorrelation: correlation(local[index]),
  }));
  const spins = valid.map((site) => site.spin);
  const signedSum = spins.reduce((sum, value) => sum + value, 0);
  const absoluteSum = spins.reduce((sum, value) => sum + Math.abs(value), 0);
  const zeroTolerance = Math.max(0, Number(options.zeroTolerance) || 1e-10);
  const weightedPairNumerator = bins.reduce((sum, bin) => sum + bin.signedProductSum, 0);
  const weightedPairDenominator = bins.reduce((sum, bin) => sum + bin.absoluteProductSum, 0);
  return {
    available: true,
    suppliedSites: valid.length,
    inputSites: sites.length,
    coverage: valid.length / Math.max(1, sites.length),
    positiveSites: spins.filter((value) => value > zeroTolerance).length,
    negativeSites: spins.filter((value) => value < -zeroTolerance).length,
    nearZeroSites: spins.filter((value) => Math.abs(value) <= zeroTolerance).length,
    signedSum,
    absoluteSum,
    netPolarization: absoluteSum > 1e-15 ? signedSum / absoluteSum : 0,
    maximumAbsoluteSpin: Math.max(...spins.map(Math.abs)),
    medianNearestDistance,
    maximumReach,
    binCount,
    checkedPairs,
    weightedPairCorrelation: weightedPairDenominator > 1e-15
      ? weightedPairNumerator / weightedPairDenominator : null,
    radialCorrelation: bins,
    localRecords,
    provenance: COLLINEAR_SPIN_PROVENANCE,
    finiteObservedCrop: true,
    periodicImagesSummed: false,
    translationInvariant: true,
    properRotationInvariant: true,
    permutationInvariant: true,
    globalSpinSignPairInvariant: true,
    targetUsed: false,
    usedForGrowth: false,
    vectorAxisInferred: false,
    magneticMomentUnitInferred: false,
    exchangeEnergyInferred: false,
    magneticHamiltonianInferred: false,
    temperatureOrOrderingTransitionInferred: false,
  };
}
