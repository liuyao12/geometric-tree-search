function finite(value) {
  return Number.isFinite(Number(value));
}

function factorial(value) {
  let result = 1;
  for (let index = 2; index <= value; index += 1) result *= index;
  return result;
}

function associatedLegendre(degree, order, x) {
  let pmm = 1;
  if (order > 0) {
    const root = Math.sqrt(Math.max(0, 1 - x * x));
    let factor = 1;
    for (let index = 1; index <= order; index += 1) {
      pmm *= -factor * root; factor += 2;
    }
  }
  if (degree === order) return pmm;
  let pmmp1 = x * (2 * order + 1) * pmm;
  if (degree === order + 1) return pmmp1;
  let previous = pmm;
  let current = pmmp1;
  for (let ell = order + 2; ell <= degree; ell += 1) {
    const next = ((2 * ell - 1) * x * current - (ell + order - 1) * previous)
      / (ell - order);
    previous = current; current = next;
  }
  return current;
}

function sphericalHarmonicPositiveOrder(degree, order, vector) {
  const radius = Math.hypot(...vector);
  const cosTheta = Math.max(-1, Math.min(1, vector[2] / radius));
  const phi = Math.atan2(vector[1], vector[0]);
  const normalization = Math.sqrt((2 * degree + 1) / (4 * Math.PI)
    * factorial(degree - order) / factorial(degree + order));
  const amplitude = normalization * associatedLegendre(degree, order, cosTheta);
  return { real: amplitude * Math.cos(order * phi),
    imaginary: amplitude * Math.sin(order * phi) };
}

function median(values) {
  const ordered = [...values].sort((first, second) => first - second);
  const middle = Math.floor(ordered.length / 2);
  return ordered.length % 2 ? ordered[middle] : (ordered[middle - 1] + ordered[middle]) / 2;
}

function populationStandardDeviation(values, mean) {
  return Math.sqrt(values.reduce((sum, value) => sum + (value - mean) ** 2, 0)
    / values.length);
}

function steinhardtGlobalOrder(directedBonds, degree) {
  if (!directedBonds.length) return null;
  let normSquared = 0;
  for (let order = 0; order <= degree; order += 1) {
    const sum = directedBonds.reduce((accumulator, vector) => {
      const harmonic = sphericalHarmonicPositiveOrder(degree, order, vector);
      accumulator.real += harmonic.real;
      accumulator.imaginary += harmonic.imaginary;
      return accumulator;
    }, { real: 0, imaginary: 0 });
    const real = sum.real / directedBonds.length;
    const imaginary = sum.imaginary / directedBonds.length;
    normSquared += (order === 0 ? 1 : 2) * (real * real + imaginary * imaginary);
  }
  return Math.sqrt(4 * Math.PI / (2 * degree + 1) * normSquared);
}

function normalizedSites(rawSites) {
  if (!Array.isArray(rawSites) || rawSites.length < 2) {
    throw new TypeError("a global geometric state descriptor needs at least two sites");
  }
  return rawSites.map((site, index) => {
    if (typeof site?.species !== "string" || !site.species.trim()
        || !Array.isArray(site.positionAngstrom) || site.positionAngstrom.length !== 3
        || !site.positionAngstrom.every(finite)) {
      throw new TypeError(`state site ${index + 1} needs species and a finite Cartesian position`);
    }
    return { species: site.species.trim(), positionAngstrom: site.positionAngstrom.map(Number) };
  });
}

export function materialEndpointSites(pathGeometry, endpoint = "final") {
  if (!pathGeometry?.coordinateBearingImagesValidated
      || !Array.isArray(pathGeometry.fixedMaterialSites)
      || !Array.isArray(pathGeometry.images) || pathGeometry.images.length < 2) {
    throw new TypeError("endpoint reconstruction needs a validated coordinate-bearing path");
  }
  if (!['initial', 'final'].includes(endpoint)) {
    throw new Error("endpoint must be initial or final");
  }
  const image = endpoint === "initial" ? pathGeometry.images[0] : pathGeometry.images.at(-1);
  return [...pathGeometry.fixedMaterialSites, ...image.sites.filter((site) =>
    site.domain === "material")].map((site) => ({ species: site.species,
    positionAngstrom: [...site.positionAngstrom] }));
}

export function buildGeometricStateDescriptor(rawSites, { contactReach = 1.35 } = {}) {
  const sites = normalizedSites(rawSites);
  if (!finite(contactReach) || Number(contactReach) <= 1) {
    throw new RangeError("state contact reach must be a finite multiplier greater than one");
  }
  const nearestDistances = Array(sites.length).fill(Infinity);
  const pairDistances = [];
  for (let first = 0; first < sites.length; first += 1) {
    for (let second = first + 1; second < sites.length; second += 1) {
      const distance = Math.hypot(...sites[first].positionAngstrom.map((value, axis) =>
        value - sites[second].positionAngstrom[axis]));
      if (!(distance > 1e-10)) throw new Error("geometric state sites must be distinct");
      pairDistances.push({ first, second, distance });
      nearestDistances[first] = Math.min(nearestDistances[first], distance);
      nearestDistances[second] = Math.min(nearestDistances[second], distance);
    }
  }
  const medianNearestNeighborAngstrom = median(nearestDistances);
  const cutoffAngstrom = medianNearestNeighborAngstrom * Number(contactReach);
  const coordination = Array(sites.length).fill(0);
  const directedBonds = [];
  const speciesPairCounts = new Map();
  let contactCount = 0;
  let sameSpeciesContactCount = 0;
  pairDistances.forEach(({ first, second, distance }) => {
    if (distance > cutoffAngstrom) return;
    contactCount += 1; coordination[first] += 1; coordination[second] += 1;
    if (sites[first].species === sites[second].species) sameSpeciesContactCount += 1;
    const pair = [sites[first].species, sites[second].species].sort().join("–");
    speciesPairCounts.set(pair, (speciesPairCounts.get(pair) || 0) + 1);
    const vector = sites[second].positionAngstrom.map((value, axis) =>
      value - sites[first].positionAngstrom[axis]);
    directedBonds.push(vector, vector.map((value) => -value));
  });
  const meanCoordination = coordination.reduce((sum, value) => sum + value, 0)
    / coordination.length;
  const speciesCounts = new Map();
  sites.forEach((site) => speciesCounts.set(site.species,
    (speciesCounts.get(site.species) || 0) + 1));
  return {
    schema: "gcts-global-geometric-state-descriptor-v1",
    atomCount: sites.length,
    speciesCounts: Object.fromEntries([...speciesCounts.entries()].sort(([first], [second]) =>
      first.localeCompare(second))),
    contactReach: Number(contactReach),
    medianNearestNeighborAngstrom,
    cutoffAngstrom,
    contactCount,
    meanCoordination,
    coordinationStandardDeviation: populationStandardDeviation(coordination, meanCoordination),
    minimumCoordination: Math.min(...coordination),
    maximumCoordination: Math.max(...coordination),
    sameSpeciesContactFraction: contactCount ? sameSpeciesContactCount / contactCount : null,
    speciesPairContactFractions: Object.fromEntries([...speciesPairCounts.entries()]
      .sort(([first], [second]) => first.localeCompare(second))
      .map(([pair, count]) => [pair, count / contactCount])),
    steinhardtQ4: steinhardtGlobalOrder(directedBonds, 4),
    steinhardtQ6: steinhardtGlobalOrder(directedBonds, 6),
    finiteObservationBoundaryIncluded: true,
    periodicImagesAdded: false,
    targetUsed: false,
    rotationallyInvariant: true,
    chemicalBondClaimed: false,
    thermodynamicOrderParameterClaimed: false,
    claimBoundary: "Coordination and global Steinhardt Q4/Q6 are computed from the finite exact colored point set using a cutoff equal to the declared reach times that state's median nearest-neighbor distance. Observation-boundary undercoordination is retained and no periodic images are invented. These geometric descriptors are not bond orders, phase labels, thermodynamic order parameters, or infinite-system averages.",
  };
}
