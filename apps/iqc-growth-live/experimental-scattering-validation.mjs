const TWO_PI = 2 * Math.PI;

function finite(value, label) {
  const number = Number(value);
  if (!Number.isFinite(number)) throw new TypeError(`${label} must be finite`);
  return number;
}

function positive(value, label) {
  const number = finite(value, label);
  if (!(number > 0)) throw new RangeError(`${label} must be positive`);
  return number;
}

function canonicalChannel(channel = {}) {
  const kind = String(channel.kind || "unit");
  if (!["unit", "constant-Z", "xray-neutral-f0", "chemical-Z", "species-sublattice"].includes(kind)) {
    throw new RangeError("unsupported scattering model channel");
  }
  const species = kind === "species-sublattice" ? String(channel.species || "").trim() : null;
  if (kind === "species-sublattice" && !species) throw new Error("species-sublattice requires species");
  return Object.freeze({ kind, species });
}

function channelKey(channel) {
  return `${channel.kind}:${channel.species || "all"}`;
}

function canonicalCoherence(coherence = {}) {
  const kind = String(coherence.kind || "finite-section");
  if (!["finite-section", "periodic-cell"].includes(kind)) {
    throw new RangeError("unsupported calculated-intensity coherence model");
  }
  const coherenceLengthAngstrom = kind === "periodic-cell"
    ? positive(coherence.coherenceLengthAngstrom, "coherence length") : null;
  return Object.freeze({ kind, coherenceLengthAngstrom });
}

function xToQ(value, axis, wavelengthAngstrom) {
  if (axis === "q-inverse-angstrom") return positive(value, "q");
  if (axis === "d-angstrom") return TWO_PI / positive(value, "d spacing");
  if (axis === "two-theta-degree") {
    const twoTheta = finite(value, "two theta");
    if (!(twoTheta > 0 && twoTheta < 180)) throw new RangeError("two theta must lie between 0 and 180 degrees");
    return 4 * Math.PI * Math.sin(twoTheta * Math.PI / 360)
      / positive(wavelengthAngstrom, "wavelength");
  }
  throw new RangeError("unsupported powder-profile axis");
}

export function buildExperimentalScatteringRequest(input = {}) {
  const structureSha256 = String(input.structureSha256 || "").toLowerCase();
  if (!/^[0-9a-f]{64}$/.test(structureSha256)) throw new Error("structureSha256 must be a SHA-256 digest");
  const probe = String(input.probe || "x-ray");
  if (!["x-ray", "neutron", "electron"].includes(probe)) throw new RangeError("unsupported probe");
  const modelChannel = canonicalChannel(input.modelChannel);
  const modelCoherence = canonicalCoherence(input.modelCoherence);
  const qMinimum = positive(input.qMinimumInverseAngstrom ?? .25, "minimum q");
  const qMaximum = positive(input.qMaximumInverseAngstrom ?? 18, "maximum q");
  if (!(qMaximum > qMinimum)) throw new RangeError("maximum q must exceed minimum q");
  return Object.freeze({
    schema: "gcts-experimental-scattering-request-v1",
    requestId: String(input.requestId || `powder-${structureSha256.slice(0, 12)}`),
    structureSha256,
    materialLabel: String(input.materialLabel || "unlabelled specimen"),
    species: Object.freeze([...(input.species || [])].map(String).sort()),
    probe,
    modelChannel,
    modelCoherence,
    requestedAxes: Object.freeze(["q-inverse-angstrom", "two-theta-degree", "d-angstrom"]),
    qRangeInverseAngstrom: Object.freeze([qMinimum, qMaximum]),
    requiredPointFields: Object.freeze(["abscissa", "intensity"]),
    requestedPointFields: Object.freeze(["standardUncertainty"]),
    requestedMetadata: Object.freeze([
      "source URL or DOI", "measurement temperature", "wavelength for 2theta",
      "intensity units", "background/normalization corrections", "instrument resolution",
    ]),
    acceptedCifDataNames: Object.freeze([
      "_pd_meas.2theta_scan", "_pd_proc.2theta_corrected", "_pd_proc.d_spacing",
      "_pd_meas.intensity_total", "_pd_meas.counts_total", "_pd_proc.intensity_total",
    ]),
    analysisRole: "post-growth validation only",
    mayAffectClustering: false,
    mayAffectMarking: false,
    mayAffectCandidateAdmission: false,
    mayAffectGrowth: false,
    targetUsed: false,
  });
}

export function validateExperimentalScatteringResponse(request, response = {}) {
  if (request?.schema !== "gcts-experimental-scattering-request-v1") throw new Error("a valid frozen request is required");
  if (response.requestId !== request.requestId || response.structureSha256 !== request.structureSha256) {
    throw new Error("response identity does not match the frozen request");
  }
  const axis = String(response.axis || "");
  if (!request.requestedAxes.includes(axis)) throw new RangeError("response axis was not requested");
  const probe = String(response.probe || "");
  if (probe !== request.probe && probe !== "synthetic-instrument-demonstrator") {
    throw new Error("response probe does not match the request");
  }
  const modelChannel = canonicalChannel(response.modelChannel);
  if (channelKey(modelChannel) !== channelKey(request.modelChannel)) {
    throw new Error("response preprocessing does not match the requested model channel");
  }
  const abscissa = [...(response.abscissa || [])];
  const intensity = [...(response.intensity || [])];
  if (abscissa.length < 12 || intensity.length !== abscissa.length) {
    throw new Error("a powder profile requires at least 12 aligned points");
  }
  const wavelengthAngstrom = axis === "two-theta-degree"
    ? positive(response.wavelengthAngstrom, "wavelength")
    : response.wavelengthAngstrom == null ? null : positive(response.wavelengthAngstrom, "wavelength");
  const q = abscissa.map(value => xToQ(value, axis, wavelengthAngstrom));
  const y = intensity.map((value, index) => {
    const number = finite(value, `intensity ${index}`);
    if (number < 0) throw new RangeError("measured intensities cannot be negative");
    return number;
  });
  for (let index = 1; index < q.length; index++) {
    if (!(q[index] > q[index - 1])) throw new Error("profile abscissa must map to strictly increasing q");
  }
  const suppliedUncertainty = Array.isArray(response.standardUncertainty);
  let sigma;
  if (suppliedUncertainty) {
    if (response.standardUncertainty.length !== q.length) throw new Error("uncertainty length mismatch");
    sigma = response.standardUncertainty.map((value, index) => positive(value, `uncertainty ${index}`));
  } else if (String(response.intensityUnits || "").toLowerCase().includes("count")) {
    sigma = y.map(value => Math.sqrt(Math.max(1, value)));
  } else {
    sigma = y.map(() => 1);
  }
  const provenance = response.provenance || {};
  const source = String(provenance.doi || provenance.url || provenance.datasetId || "").trim();
  if (!source) throw new Error("a DOI, URL, or dataset ID is required");
  const synthetic = probe === "synthetic-instrument-demonstrator";
  if (!synthetic && response.independentOfGrowth !== true) {
    throw new Error("an experimental profile must be independent of the growth result");
  }
  if (response.usedForGrowth === true || response.usedForMarking === true
      || response.usedForCandidateSelection === true) {
    throw new Error("post-growth evidence cannot feed growth, marking, or candidate selection");
  }
  const resolutionFwhmQ = response.resolutionFwhmQ == null ? 0
    : Math.max(0, finite(response.resolutionFwhmQ, "resolution FWHM"));
  const correspondence = response.materialCorrespondence || {};
  const correspondenceLevel = String(correspondence.level || "unspecified");
  if (!["exact-phase", "composition-only", "unspecified"].includes(correspondenceLevel)) {
    throw new Error("unsupported material-correspondence level");
  }
  const sameMaterialClaimAllowed = !synthetic && correspondenceLevel === "exact-phase"
    && correspondence.sameMaterialClaimAllowed === true;
  return Object.freeze({
    schema: "gcts-validated-experimental-scattering-profile-v1",
    requestId: request.requestId,
    structureSha256: request.structureSha256,
    probe,
    modelChannel,
    axis,
    wavelengthAngstrom,
    q: Object.freeze(q),
    intensity: Object.freeze(y),
    standardUncertainty: Object.freeze(sigma),
    uncertaintySource: suppliedUncertainty ? "supplied" : String(response.intensityUnits || "").toLowerCase().includes("count")
      ? "Poisson sqrt(counts)" : "uniform unit weight",
    intensityUnits: String(response.intensityUnits || "arbitrary"),
    resolutionFwhmQ,
    corrections: Object.freeze([...(response.corrections || [])].map(String)),
    provenance: Object.freeze({
      title: String(provenance.title || "Powder profile"), source,
      doi: provenance.doi ? String(provenance.doi) : null,
      url: provenance.url ? String(provenance.url) : null,
      datasetId: provenance.datasetId ? String(provenance.datasetId) : null,
      temperatureKelvin: provenance.temperatureKelvin == null ? null
        : positive(provenance.temperatureKelvin, "measurement temperature"),
      datasetDoi: provenance.datasetDoi ? String(provenance.datasetDoi) : null,
      license: provenance.license ? String(provenance.license) : null,
      locality: provenance.locality ? String(provenance.locality) : null,
      cellParameters: provenance.cellParameters ? String(provenance.cellParameters) : null,
      spaceGroup: provenance.spaceGroup ? String(provenance.spaceGroup) : null,
      profileSha256: provenance.profileSha256 ? String(provenance.profileSha256) : null,
      libraryAssetSha256: provenance.libraryAssetSha256 ? String(provenance.libraryAssetSha256) : null,
      difTextSha256: provenance.difTextSha256 ? String(provenance.difTextSha256) : null,
      selectionRule: provenance.selectionRule ? String(provenance.selectionRule) : null,
    }),
    materialCorrespondence: Object.freeze({
      level: correspondenceLevel,
      elements: Object.freeze([...(correspondence.elements || [])].map(String).sort()),
      formula: correspondence.formula ? String(correspondence.formula) : null,
      phase: correspondence.phase ? String(correspondence.phase) : null,
      basis: String(correspondence.basis || "material identity not supplied"),
      sameMaterialClaimAllowed,
    }),
    experimentalEvidence: !synthetic,
    sameMaterialEvidence: sameMaterialClaimAllowed,
    demonstratorOnly: synthetic,
    independentOfGrowth: !synthetic,
    targetUsedBeforeGrowth: false,
    candidateSetChanged: false,
  });
}

function linearInterpolate(xs, ys, x) {
  if (x < xs[0] || x > xs.at(-1)) return null;
  let low = 0; let high = xs.length - 1;
  while (high - low > 1) {
    const middle = (low + high) >> 1;
    if (xs[middle] <= x) low = middle; else high = middle;
  }
  const span = xs[high] - xs[low];
  const fraction = span > 0 ? (x - xs[low]) / span : 0;
  return ys[low] * (1 - fraction) + ys[high] * fraction;
}

function broaden(values, q, fwhm) {
  if (!(fwhm > 0)) return [...values];
  const sigma = fwhm / (2 * Math.sqrt(2 * Math.log(2)));
  return q.map((center) => {
    let numerator = 0; let denominator = 0;
    q.forEach((position, index) => {
      const delta = (position - center) / sigma;
      if (Math.abs(delta) > 4) return;
      const weight = Math.exp(-.5 * delta * delta);
      numerator += weight * values[index]; denominator += weight;
    });
    return denominator ? numerator / denominator : 0;
  });
}

function solveWeightedNuisance(model, observed, sigma, q, nuisance) {
  const columns = nuisance === "scale+constant+linear-q" ? 3
    : nuisance === "scale+constant" ? 2 : 1;
  const matrix = Array.from({ length: columns }, () => new Array(columns).fill(0));
  const vector = new Array(columns).fill(0);
  const qCenter = q.reduce((sum, value) => sum + value, 0) / q.length;
  model.forEach((value, index) => {
    const row = [value, 1, q[index] - qCenter].slice(0, columns);
    const weight = 1 / (sigma[index] ** 2);
    row.forEach((first, i) => {
      vector[i] += weight * first * observed[index];
      row.forEach((second, j) => { matrix[i][j] += weight * first * second; });
    });
  });
  for (let pivot = 0; pivot < columns; pivot++) {
    let selected = pivot;
    for (let row = pivot + 1; row < columns; row++) {
      if (Math.abs(matrix[row][pivot]) > Math.abs(matrix[selected][pivot])) selected = row;
    }
    [matrix[pivot], matrix[selected]] = [matrix[selected], matrix[pivot]];
    [vector[pivot], vector[selected]] = [vector[selected], vector[pivot]];
    const diagonal = matrix[pivot][pivot];
    if (Math.abs(diagonal) < 1e-12) throw new Error("nuisance fit is singular");
    for (let column = pivot; column < columns; column++) matrix[pivot][column] /= diagonal;
    vector[pivot] /= diagonal;
    for (let row = 0; row < columns; row++) {
      if (row === pivot) continue;
      const factor = matrix[row][pivot];
      for (let column = pivot; column < columns; column++) matrix[row][column] -= factor * matrix[pivot][column];
      vector[row] -= factor * vector[pivot];
    }
  }
  const [scale, constant = 0, slope = 0] = vector;
  if (!(scale >= 0)) throw new Error("best-fit intensity scale is negative");
  return { scale, constant, slope, qCenter, parameterCount: columns };
}

export function compareExperimentalScattering(model = {}, profile, options = {}) {
  if (profile?.schema !== "gcts-validated-experimental-scattering-profile-v1") {
    throw new Error("a validated experimental profile is required");
  }
  const nearestNeighborAngstrom = positive(options.nearestNeighborAngstrom, "nearest-neighbor scale");
  const qModel = [...(model.q || [])].map(value => positive(value, "model qa"))
    .map(value => value / nearestNeighborAngstrom);
  const values = [...(model.values || [])].map((value, index) => finite(value, `model intensity ${index}`));
  if (qModel.length < 4 || qModel.length !== values.length) throw new Error("model q and intensity arrays must align");
  const broadened = broaden(values, qModel, profile.resolutionFwhmQ);
  const qMinimum = Math.max(qModel[0], profile.q[0]);
  const qMaximum = Math.min(qModel.at(-1), profile.q.at(-1));
  const indices = profile.q.map((q, index) => q >= qMinimum && q <= qMaximum ? index : -1)
    .filter(index => index >= 0);
  if (indices.length < 12) throw new Error("model and experiment overlap at fewer than 12 points");
  const q = indices.map(index => profile.q[index]);
  const observed = indices.map(index => profile.intensity[index]);
  const sigma = indices.map(index => profile.standardUncertainty[index]);
  const sampledModel = q.map(value => linearInterpolate(qModel, broadened, value));
  const nuisance = String(options.nuisance || "scale+constant");
  if (!["scale", "scale+constant", "scale+constant+linear-q"].includes(nuisance)) {
    throw new RangeError("unsupported nuisance model");
  }
  const fit = solveWeightedNuisance(sampledModel, observed, sigma, q, nuisance);
  const calculated = sampledModel.map((value, index) => fit.scale * value + fit.constant
    + fit.slope * (q[index] - fit.qCenter));
  const residual = observed.map((value, index) => value - calculated[index]);
  const weightedResidual = residual.reduce((sum, value, index) => sum + (value / sigma[index]) ** 2, 0);
  const weightedObserved = observed.reduce((sum, value, index) => sum + (value / sigma[index]) ** 2, 0);
  const degreesOfFreedom = Math.max(1, observed.length - fit.parameterCount);
  const rwp = Math.sqrt(weightedResidual / Math.max(1e-30, weightedObserved));
  const reducedChiSquared = weightedResidual / degreesOfFreedom;
  const observedMean = observed.reduce((sum, value) => sum + value, 0) / observed.length;
  const calculatedMean = calculated.reduce((sum, value) => sum + value, 0) / calculated.length;
  const covariance = observed.reduce((sum, value, index) => sum
    + (value - observedMean) * (calculated[index] - calculatedMean), 0);
  const varianceObserved = observed.reduce((sum, value) => sum + (value - observedMean) ** 2, 0);
  const varianceCalculated = calculated.reduce((sum, value) => sum + (value - calculatedMean) ** 2, 0);
  const correlation = covariance / Math.sqrt(Math.max(1e-30, varianceObserved * varianceCalculated));
  return Object.freeze({
    schema: "gcts-experimental-scattering-comparison-v1",
    q: Object.freeze(q), observed: Object.freeze(observed), calculated: Object.freeze(calculated),
    residual: Object.freeze(residual), standardUncertainty: Object.freeze(sigma),
    qRangeInverseAngstrom: Object.freeze([q[0], q.at(-1)]),
    comparedPoints: q.length, nuisance,
    nuisanceParameters: Object.freeze({ scale: fit.scale, constant: fit.constant, slope: fit.slope }),
    rwp, reducedChiSquared, correlation,
    resolutionFwhmQ: profile.resolutionFwhmQ,
    uncertaintySource: profile.uncertaintySource,
    experimentalEvidence: profile.experimentalEvidence,
    sameMaterialEvidence: profile.sameMaterialEvidence,
    materialCorrespondence: profile.materialCorrespondence,
    demonstratorOnly: profile.demonstratorOnly,
    targetUsedBeforeGrowth: false,
    candidateSetChanged: false,
    interpretation: profile.sameMaterialEvidence
      ? "post-growth same-phase profile agreement; not a structure refinement or causal growth score"
      : profile.experimentalEvidence
        ? "post-growth experimental reference with unresolved material identity; not validation of the selected phase"
      : "instrument-pipeline demonstrator only; not independent experimental evidence",
  });
}

export function buildInstrumentProfileDemonstrator(request, model = {}, options = {}) {
  const nearestNeighborAngstrom = positive(options.nearestNeighborAngstrom, "nearest-neighbor scale");
  const q = [...(model.q || [])].map(value => positive(value, "model qa") / nearestNeighborAngstrom);
  const values = [...(model.values || [])].map((value, index) => finite(value, `model intensity ${index}`));
  if (q.length < 12 || q.length !== values.length) throw new Error("demonstrator model arrays must align");
  const fwhm = positive(options.resolutionFwhmQ ?? .12, "demonstrator resolution");
  const smoothed = broaden(values, q, fwhm);
  const intensity = smoothed.map((value, index) => Math.max(0,
    36 + 620 * value + 5 * Math.sin(index * 1.731) + 3 * Math.cos(index * .619)));
  return {
    requestId: request.requestId,
    structureSha256: request.structureSha256,
    probe: "synthetic-instrument-demonstrator",
    modelChannel: request.modelChannel,
    axis: "q-inverse-angstrom",
    abscissa: q,
    intensity,
    standardUncertainty: intensity.map(value => Math.sqrt(Math.max(1, value))),
    intensityUnits: "synthetic counts",
    resolutionFwhmQ: fwhm,
    corrections: ["deterministic constant background", "Gaussian resolution convolution", "deterministic display perturbation"],
    provenance: { title: "Built-in instrument-response demonstrator", datasetId: "gcts-synthetic-powder-demo-v1" },
    independentOfGrowth: false,
    usedForGrowth: false,
    usedForMarking: false,
    usedForCandidateSelection: false,
  };
}
