import { besselJ0 } from "./structure-observables.js";

const FOUR_PI = 4 * Math.PI;

// Neutral-atom Cromer-Mann coefficients from International Tables for
// Crystallography Vol. C (1992), transcribed from Gemmi's IT92 table.  The
// table is intentionally limited to chemistry exercised by the portal and its
// pinned public powder-profile library. Unsupported chemistry fails closed.
export const XRAY_FORM_FACTOR_PROVENANCE = Object.freeze({
  model: "International Tables 1992 neutral-atom Cromer-Mann f0",
  equation: "f0(s) = sum_i a_i exp(-b_i s^2) + c; s = q/(4 pi)",
  validity: "sin(theta)/lambda < 2 inverse angstrom",
  iucrDefinition: "https://dictionary.iucr.org/Cromer%E2%80%93Mann_coefficients",
  implementationSource: "https://github.com/project-gemmi/gemmi/blob/d6ccb33d4be318adfd8a73ae30ce3a01ed0c5a8d/include/gemmi/it92.hpp",
  implementationSourceSha256: "e9c5a0854c098136de2e463bfb175c33d195c518299c602956ed9d782dff21ee",
});

// [a1, a2, a3, a4, b1, b2, b3, b4, c]
const IT92 = Object.freeze({
  H: [0.493002, 0.322912, 0.140191, 0.04081, 10.5109, 26.1257, 3.14236, 57.7997, 0.003038],
  B: [2.0545, 1.3326, 1.0979, 0.7068, 23.2185, 1.021, 60.3498, 0.1403, -0.1932],
  C: [2.31, 1.02, 1.5886, 0.865, 20.8439, 10.2075, 0.5687, 51.6512, 0.2156],
  N: [12.2126, 3.1322, 2.0125, 1.1663, 0.0057, 9.8933, 28.9975, 0.5826, -11.529],
  O: [3.0485, 2.2868, 1.5463, 0.867, 13.2771, 5.7011, 0.3239, 32.9089, 0.2508],
  F: [3.5392, 2.6412, 1.517, 1.0243, 10.2825, 4.2944, 0.2615, 26.1476, 0.2776],
  Na: [4.7626, 3.1736, 1.2674, 1.1128, 3.285, 8.8422, 0.3136, 129.424, 0.676],
  Mg: [5.4204, 2.1735, 1.2269, 2.3073, 2.8275, 79.2611, 0.3808, 7.1937, 0.8584],
  Al: [6.4202, 1.9002, 1.5936, 1.9646, 3.0387, 0.7426, 31.5472, 85.0886, 1.1151],
  Si: [6.2915, 3.0353, 1.9891, 1.541, 2.4386, 32.3337, 0.6785, 81.6937, 1.1407],
  P: [6.4345, 4.1791, 1.78, 1.4908, 1.9067, 27.157, 0.526, 68.1645, 1.1149],
  S: [6.9053, 5.2034, 1.4379, 1.5863, 1.4679, 22.2151, 0.2536, 56.172, 0.8669],
  Cl: [11.4604, 7.1964, 6.2556, 1.6455, 0.0104, 1.1662, 18.5194, 47.7784, -9.5574],
  K: [8.2186, 7.4398, 1.0519, 0.8659, 12.7949, 0.7748, 213.187, 41.6841, 1.4228],
  Ca: [8.6266, 7.3873, 1.5899, 1.0211, 10.4421, 0.6599, 85.7484, 178.437, 1.3751],
  Sc: [9.189, 7.3679, 1.6409, 1.468, 9.0213, 0.5729, 136.108, 51.3531, 1.3329],
  Ti: [9.7595, 7.3558, 1.6991, 1.9021, 7.8508, 0.5, 35.6338, 116.105, 1.2807],
  V: [10.2971, 7.3511, 2.0703, 2.0571, 6.8657, 0.4385, 26.8938, 102.478, 1.2199],
  Fe: [11.7695, 7.3573, 3.5222, 2.3045, 4.7611, 0.3072, 15.3535, 76.8805, 1.0369],
  Co: [12.2841, 7.3409, 4.0034, 2.3488, 4.2791, 0.2784, 13.5359, 71.1692, 1.0118],
  Ni: [12.8376, 7.292, 4.4438, 2.38, 3.8785, 0.2565, 12.1763, 66.3421, 1.0341],
  Cu: [13.338, 7.1676, 5.6158, 1.6735, 3.5828, 0.247, 11.3966, 64.8126, 1.191],
  Zn: [14.0743, 7.0318, 5.1652, 2.41, 3.2655, 0.2333, 10.3163, 58.7097, 1.3041],
  Zr: [17.8765, 10.948, 5.41732, 3.65721, 1.27618, 11.916, 0.117622, 87.6627, 2.06929],
  Mo: [3.7025, 17.2356, 12.8876, 3.7429, 0.2772, 1.0958, 11.004, 61.6584, 4.3875],
  Cd: [19.2214, 17.6444, 4.461, 1.6029, 0.5946, 6.9089, 24.7008, 87.4825, 5.0694],
  Te: [19.9644, 19.0138, 6.14487, 2.5239, 4.81742, 0.420885, 28.5284, 70.8403, 4.352],
  Yb: [28.6641, 15.4345, 15.3087, 2.98963, 1.9889, 0.257119, 10.6647, 100.417, 7.56672],
  Ta: [29.2024, 15.2293, 14.5135, 4.76492, 1.77333, 9.37046, 0.295977, 63.3644, 9.24354],
  W: [29.0818, 15.43, 14.4327, 5.11982, 1.72029, 9.2259, 0.321703, 57.056, 9.8875],
});

export const XRAY_FORM_FACTOR_ELEMENTS = Object.freeze(Object.keys(IT92));

function symbolsForToken(token) {
  const text = String(token || "");
  const occupational = text.match(/^occ\[(.*)]$/);
  const symbols = occupational
    ? occupational[1].split(";").filter(record => !/^Vac=/.test(record))
      .flatMap(record => (record.split("=")[0].match(/[A-Z][a-z]?/) || []))
    : text.match(/[A-Z][a-z]?/g) || [];
  return symbols.map(symbol => symbol === "D" ? "H" : symbol);
}

function componentsForToken(token) {
  const text = String(token || "");
  const occupational = text.match(/^occ\[(.*)]$/);
  if (occupational) return occupational[1].split(";").filter(record => !/^Vac=/.test(record))
    .map((record) => {
      const [label, rawFraction] = record.split("=");
      const species = (label.match(/[A-Z][a-z]?/) || [])[0];
      return { species: species === "D" ? "H" : species, fraction: Number(rawFraction) };
    }).filter(component => component.species && Number.isFinite(component.fraction) && component.fraction > 0);
  const symbols = symbolsForToken(text);
  return symbols.map(species => ({ species, fraction: 1 / Math.max(1, symbols.length) }));
}

export function neutralXrayFormFactorSupport(token) {
  const symbols = symbolsForToken(token);
  const unsupported = [...new Set(symbols.filter(symbol => !IT92[symbol]))].sort();
  return Object.freeze({ supported: symbols.length > 0 && unsupported.length === 0,
    symbols: Object.freeze(symbols), unsupported: Object.freeze(unsupported) });
}

export function neutralXrayFormFactor(token, qInverseAngstrom) {
  const q = Number(qInverseAngstrom);
  if (!(Number.isFinite(q) && q >= 0)) throw new RangeError("X-ray form factor requires nonnegative finite q");
  const support = neutralXrayFormFactorSupport(token);
  if (!support.supported) throw new Error(`neutral-atom X-ray form factor unavailable for ${support.unsupported.join(", ") || token}`);
  const s = q / FOUR_PI;
  if (!(s < 2)) throw new RangeError("Cromer-Mann f0 is restricted to sin(theta)/lambda < 2 inverse angstrom");
  return componentsForToken(token).reduce((sum, component) => {
    const coefficients = IT92[component.species];
    const value = coefficients[8] + [0, 1, 2, 3].reduce((inner, index) => inner
      + coefficients[index] * Math.exp(-coefficients[index + 4] * s * s), 0);
    return sum + component.fraction * value;
  }, 0);
}

function canonicalSiteScatteringComponents(species, siteScatteringComponents) {
  if (siteScatteringComponents == null) {
    return species.map(token => Object.freeze([{ species: token, fraction: 1 }]));
  }
  if (!Array.isArray(siteScatteringComponents) || siteScatteringComponents.length !== species.length) {
    throw new Error("X-ray site components must align with species sites");
  }
  return siteScatteringComponents.map((components, siteIndex) => {
    if (!Array.isArray(components) || components.length === 0) {
      throw new Error(`X-ray site ${siteIndex} requires at least one occupied component`);
    }
    const canonical = components.map((component, componentIndex) => {
      const token = String(component?.species || "");
      const fraction = Number(component?.fraction);
      if (!(Number.isFinite(fraction) && fraction > 0 && fraction <= 1)) {
        throw new RangeError(`X-ray site ${siteIndex} component ${componentIndex} has invalid occupancy`);
      }
      const support = neutralXrayFormFactorSupport(token);
      if (!support.supported) {
        throw new Error(`neutral-atom X-ray form factor unavailable for ${support.unsupported.join(", ") || token}`);
      }
      return Object.freeze({ species: token, fraction });
    });
    const total = canonical.reduce((sum, component) => sum + component.fraction, 0);
    if (total > 1 + 1e-8) throw new RangeError(`X-ray site ${siteIndex} occupancy exceeds one`);
    return Object.freeze(canonical);
  });
}

function coherentSiteAmplitude(components, qInverseAngstrom) {
  return components.reduce((sum, component) => sum
    + component.fraction * neutralXrayFormFactor(component.species, qInverseAngstrom), 0);
}

function occupancyAudit(siteComponents) {
  const totals = siteComponents.map(components => components.reduce((sum, component) => sum + component.fraction, 0));
  return {
    occupancyWeightedAmplitudesUsed: siteComponents.some((components, index) =>
      components.length > 1 || Math.abs(totals[index] - 1) > 1e-8),
    mixedOccupancySites: siteComponents.filter(components => components.length > 1).length,
    partialOccupancySites: totals.filter(total => total < 1 - 1e-8).length,
    totalSiteOccupancy: totals.reduce((sum, total) => sum + total, 0),
    occupationalDiffuseIncluded: false,
    occupancyModel: "coherent average-site amplitude sum_alpha occupancy_alpha f0_alpha(q)",
  };
}

function powderKernel(value, dimension) {
  if (Math.abs(value) < 1e-10) return 1;
  return dimension === 2 ? besselJ0(value) : Math.sin(value) / value;
}

function vector3(value, label) {
  if (!Array.isArray(value) || value.length !== 3 || value.some(component => !Number.isFinite(component))) {
    throw new Error(`${label} must be a finite Cartesian vector`);
  }
  return value.map(Number);
}

function dot(first, second) {
  return first[0] * second[0] + first[1] * second[1] + first[2] * second[2];
}

function cross(first, second) {
  return [first[1] * second[2] - first[2] * second[1],
    first[2] * second[0] - first[0] * second[2],
    first[0] * second[1] - first[1] * second[0]];
}

function norm(value) {
  return Math.sqrt(dot(value, value));
}

export function finiteDebyeXrayPowderIntensity({ species, pairs, nearestNeighborAngstrom,
  dimension = 3, qMinTimesNearestNeighbor = 2, qMaxTimesNearestNeighbor = 20,
  bins = 96, meanSquareDisplacements = null, includeIsotropicDisplacement = false,
  siteScatteringComponents = null } = {}) {
  if (!Array.isArray(species) || species.length === 0) throw new Error("X-ray powder intensity requires species");
  if (!Array.isArray(pairs) || pairs.some(pair => !Number.isInteger(pair?.first)
      || !Number.isInteger(pair?.second) || pair.first < 0 || pair.second <= pair.first
      || pair.second >= species.length || !(Number.isFinite(pair.distance) && pair.distance >= 0))) {
    throw new Error("X-ray powder intensity requires finite indexed pair geometry");
  }
  if (!(Number.isFinite(nearestNeighborAngstrom) && nearestNeighborAngstrom > 0)) {
    throw new RangeError("X-ray powder intensity requires a positive nearest-neighbor scale");
  }
  if (dimension !== 2 && dimension !== 3) throw new RangeError("X-ray powder intensity supports intrinsic dimension 2 or 3");
  const maximumByValidity = FOUR_PI * 2 * nearestNeighborAngstrom * (1 - 1e-9);
  const qMaximum = Math.min(Number(qMaxTimesNearestNeighbor), maximumByValidity);
  const qMinimum = Number(qMinTimesNearestNeighbor);
  if (!(qMaximum > qMinimum) || !Number.isInteger(bins) || bins < 4) throw new RangeError("invalid X-ray q grid");
  const siteComponents = canonicalSiteScatteringComponents(species, siteScatteringComponents);
  if (includeIsotropicDisplacement && (!Array.isArray(meanSquareDisplacements)
      || meanSquareDisplacements.length !== species.length
      || meanSquareDisplacements.some(value => value != null && !(Number.isFinite(value) && value >= 0)))) {
    throw new Error("reported-displacement X-ray intensity requires nonnegative supplied Ueq values");
  }
  const displacement = includeIsotropicDisplacement
    ? meanSquareDisplacements.map(value => Number.isFinite(value) ? value : 0) : null;
  const q = Array.from({ length: bins }, (_, index) => qMinimum
    + index / (bins - 1) * (qMaximum - qMinimum));
  const qPhysicalInverseAngstrom = q.map(value => value / nearestNeighborAngstrom);
  const forward = siteComponents.map(components => coherentSiteAmplitude(components, 0));
  const forwardSelfNormalization = forward.reduce((sum, value) => sum + value * value, 0);
  const values = q.map((qa, qIndex) => {
    const factors = siteComponents.map(components => coherentSiteAmplitude(components,
      qPhysicalInverseAngstrom[qIndex]));
    const self = factors.reduce((sum, value) => sum + value * value, 0);
    const pairSum = pairs.reduce((sum, pair) => {
      const attenuation = includeIsotropicDisplacement
        ? Math.exp(-.5 * qa * qa * (displacement[pair.first] + displacement[pair.second])) : 1;
      return sum + factors[pair.first] * factors[pair.second] * attenuation
        * powderKernel(qa * pair.distance, dimension);
    }, 0);
    return Math.max(0, (self + 2 * pairSum) / forwardSelfNormalization);
  });
  return {
    q: Object.freeze(q), values: Object.freeze(values),
    qPhysicalInverseAngstrom: Object.freeze(qPhysicalInverseAngstrom),
    dimension, qMin: qMinimum, qMax: qMaximum,
    forwardSelfNormalization, bins,
    formFactorModel: XRAY_FORM_FACTOR_PROVENANCE.model,
    formFactorSource: XRAY_FORM_FACTOR_PROVENANCE.implementationSource,
    qDependentFormFactorsUsed: true,
    anomalousDispersionIncluded: false,
    ionicFormFactorsIncluded: false,
    coherentDisplacementAttenuation: includeIsotropicDisplacement,
    diffuseRedistributionIncluded: false,
    ...occupancyAudit(siteComponents),
    normalization: "finite coherent-average Debye intensity divided by sum of squared average-site forward amplitudes",
  };
}

export function periodicBraggXrayPowderIntensity({ species, positionsAngstrom,
  cellVectorsAngstrom, nearestNeighborAngstrom, qMinTimesNearestNeighbor = 2,
  qMaxTimesNearestNeighbor = 20, bins = 512, coherenceLengthAngstrom = 200,
  meanSquareDisplacementsNormalized = null, includeIsotropicDisplacement = false,
  siteScatteringComponents = null } = {}) {
  if (!Array.isArray(species) || species.length === 0) throw new Error("periodic X-ray intensity requires species");
  if (!Array.isArray(positionsAngstrom) || positionsAngstrom.length !== species.length) {
    throw new Error("periodic X-ray intensity requires one Cartesian position per site");
  }
  const positions = positionsAngstrom.map((value, index) => vector3(value, `position ${index}`));
  if (!Array.isArray(cellVectorsAngstrom) || cellVectorsAngstrom.length !== 3) {
    throw new Error("periodic X-ray intensity requires three cell vectors");
  }
  const cell = cellVectorsAngstrom.map((value, index) => vector3(value, `cell vector ${index}`));
  const volume = dot(cell[0], cross(cell[1], cell[2]));
  if (!(Math.abs(volume) > 1e-8)) throw new Error("periodic X-ray cell must have nonzero volume");
  if (!(Number.isFinite(nearestNeighborAngstrom) && nearestNeighborAngstrom > 0)) {
    throw new RangeError("periodic X-ray intensity requires a positive nearest-neighbor scale");
  }
  if (!(Number.isFinite(coherenceLengthAngstrom) && coherenceLengthAngstrom > 0)) {
    throw new RangeError("periodic X-ray coherence length must be positive");
  }
  if (!Number.isInteger(bins) || bins < 32) throw new RangeError("periodic X-ray intensity requires at least 32 q bins");
  const siteComponents = canonicalSiteScatteringComponents(species, siteScatteringComponents);
  if (includeIsotropicDisplacement && (!Array.isArray(meanSquareDisplacementsNormalized)
      || meanSquareDisplacementsNormalized.length !== species.length
      || meanSquareDisplacementsNormalized.some(value => value != null
        && !(Number.isFinite(value) && value >= 0)))) {
    throw new Error("periodic reported-displacement intensity requires nonnegative supplied Ueq values");
  }
  const displacementAngstrom2 = includeIsotropicDisplacement
    ? meanSquareDisplacementsNormalized.map(value => Number.isFinite(value)
      ? value * nearestNeighborAngstrom * nearestNeighborAngstrom : 0) : null;
  const reciprocal = [cross(cell[1], cell[2]), cross(cell[2], cell[0]), cross(cell[0], cell[1])]
    .map(vector => vector.map(component => component * (2 * Math.PI / volume)));
  const qMinimumPhysical = Number(qMinTimesNearestNeighbor) / nearestNeighborAngstrom;
  const qMaximumByValidity = FOUR_PI * 2 * (1 - 1e-9);
  const qMaximumPhysical = Math.min(Number(qMaxTimesNearestNeighbor) / nearestNeighborAngstrom,
    qMaximumByValidity);
  if (!(qMaximumPhysical > qMinimumPhysical)) throw new RangeError("invalid periodic X-ray q grid");
  const domainFwhmQ = 2 * Math.PI / coherenceLengthAngstrom;
  const domainSigmaQ = domainFwhmQ / (2 * Math.sqrt(2 * Math.log(2)));
  const margin = 4 * domainSigmaQ;
  const maxima = cell.map(vector => Math.ceil((qMaximumPhysical + margin) * norm(vector) / (2 * Math.PI)) + 1);
  const qPhysicalInverseAngstrom = Array.from({ length: bins }, (_, index) => qMinimumPhysical
    + index / (bins - 1) * (qMaximumPhysical - qMinimumPhysical));
  const values = new Array(bins).fill(0);
  const forwardSum = siteComponents.reduce((sum, components) => sum + coherentSiteAmplitude(components, 0), 0);
  let reflectionCount = 0;
  let systematicAbsenceCount = 0;
  let maximumRawIntensity = 0;
  for (let h = -maxima[0]; h <= maxima[0]; h++) {
    for (let k = -maxima[1]; k <= maxima[1]; k++) {
      for (let l = -maxima[2]; l <= maxima[2]; l++) {
        if (h === 0 && k === 0 && l === 0) continue;
        const reciprocalVector = [0, 1, 2].map(index => h * reciprocal[0][index]
          + k * reciprocal[1][index] + l * reciprocal[2][index]);
        const qReflection = norm(reciprocalVector);
        if (qReflection < qMinimumPhysical - margin || qReflection > qMaximumPhysical + margin
            || qReflection >= qMaximumByValidity) continue;
        const factors = siteComponents.map(components => coherentSiteAmplitude(components, qReflection));
        let real = 0;
        let imaginary = 0;
        positions.forEach((position, index) => {
          const attenuation = includeIsotropicDisplacement
            ? Math.exp(-.5 * qReflection * qReflection * displacementAngstrom2[index]) : 1;
          const amplitude = factors[index] * attenuation;
          const phase = dot(reciprocalVector, position);
          real += amplitude * Math.cos(phase);
          imaginary += amplitude * Math.sin(phase);
        });
        const intensity = real * real + imaginary * imaginary;
        const relativeIntensity = intensity / (forwardSum * forwardSum);
        if (relativeIntensity < 1e-12) {
          systematicAbsenceCount++;
          continue;
        }
        reflectionCount++;
        maximumRawIntensity = Math.max(maximumRawIntensity, relativeIntensity);
        const firstBin = Math.max(0, Math.floor((qReflection - 4 * domainSigmaQ - qMinimumPhysical)
          / (qMaximumPhysical - qMinimumPhysical) * (bins - 1)));
        const lastBin = Math.min(bins - 1, Math.ceil((qReflection + 4 * domainSigmaQ - qMinimumPhysical)
          / (qMaximumPhysical - qMinimumPhysical) * (bins - 1)));
        for (let index = firstBin; index <= lastBin; index++) {
          const delta = (qPhysicalInverseAngstrom[index] - qReflection) / domainSigmaQ;
          values[index] += relativeIntensity * Math.exp(-.5 * delta * delta);
        }
      }
    }
  }
  const maximumSampledIntensity = Math.max(...values);
  if (!(maximumSampledIntensity > 0) || reflectionCount === 0) {
    throw new Error("periodic X-ray cell produced no reflections in the requested q range");
  }
  const normalizedValues = values.map(value => value / maximumSampledIntensity);
  return {
    q: Object.freeze(qPhysicalInverseAngstrom.map(value => value * nearestNeighborAngstrom)),
    values: Object.freeze(normalizedValues),
    qPhysicalInverseAngstrom: Object.freeze(qPhysicalInverseAngstrom),
    dimension: 3,
    qMin: qMinimumPhysical * nearestNeighborAngstrom,
    qMax: qMaximumPhysical * nearestNeighborAngstrom,
    bins,
    reciprocalCellVectorsInverseAngstrom: Object.freeze(reciprocal.map(Object.freeze)),
    hklBounds: Object.freeze(maxima),
    reflectionCount,
    systematicAbsenceCount,
    maximumRawIntensity,
    maximumSampledIntensity,
    coherenceLengthAngstrom,
    domainBroadeningFwhmQInverseAngstrom: domainFwhmQ,
    domainBroadeningModel: "Gaussian reciprocal-domain envelope with FWHM 2pi/L",
    formFactorModel: XRAY_FORM_FACTOR_PROVENANCE.model,
    formFactorSource: XRAY_FORM_FACTOR_PROVENANCE.implementationSource,
    qDependentFormFactorsUsed: true,
    periodicTranslationalCoherenceUsed: true,
    anomalousDispersionIncluded: false,
    ionicFormFactorsIncluded: false,
    coherentDisplacementAttenuation: includeIsotropicDisplacement,
    diffuseRedistributionIncluded: false,
    ...occupancyAudit(siteComponents),
    normalization: "sampled periodic powder intensity divided by its maximum",
  };
}
