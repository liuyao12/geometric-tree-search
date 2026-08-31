function finiteVector(vector, label) {
  if (!Array.isArray(vector) || vector.length !== 3 || !vector.every(Number.isFinite)) {
    throw new TypeError(`${label} must be a finite three-vector`);
  }
  return vector.map(Number);
}

function norm(vector) {
  return Math.hypot(vector[0], vector[1], vector[2]);
}

function subtract(first, second) {
  return first.map((value, axis) => value - second[axis]);
}

function meanVector(vectors) {
  return vectors.reduce((sum, vector) => sum.map((value, axis) => value + vector[axis]), [0, 0, 0])
    .map((value) => value / vectors.length);
}

function medianNearestDistance(positions) {
  if (positions.length < 2) return 1;
  const nearest = positions.map((position, index) => Math.min(...positions
    .map((other, otherIndex) => otherIndex === index ? Infinity : norm(subtract(position, other)))))
    .sort((first, second) => first - second);
  return nearest[Math.floor(nearest.length / 2)] || 1;
}

function normalizedTrapezoidalWeights(times) {
  if (!Array.isArray(times) || times.length < 2 || times.some((time) => !Number.isFinite(time))) {
    throw new TypeError("trajectory times must contain at least two finite values");
  }
  const intervals = times.slice(1).map((time, index) => time - times[index]);
  if (intervals.some((interval) => !(interval > 0))) {
    throw new Error("trajectory frame times must be strictly increasing");
  }
  const weights = times.map((_, index) => index === 0 ? intervals[0] / 2
    : index === times.length - 1 ? intervals.at(-1) / 2
      : (intervals[index - 1] + intervals[index]) / 2);
  const total = weights.reduce((sum, weight) => sum + weight, 0);
  return weights.map((weight) => weight / total);
}

function weightedMean(vectors, weights) {
  return [0, 1, 2].map((axis) => vectors.reduce((sum, vector, index) =>
    sum + weights[index] * vector[axis], 0));
}

function weightedCovariance(vectors, weights, mean) {
  return [0, 1, 2].map((row) => [0, 1, 2].map((column) => vectors.reduce((sum, vector, index) =>
    sum + weights[index] * (vector[row] - mean[row]) * (vector[column] - mean[column]), 0)));
}

export function buildValidatedTrajectoryGeometryRuntime(response, audit, responseSha256,
  referencePositionsAngstrom, { referenceToleranceAngstrom = 1e-7 } = {}) {
  if (audit?.quantityId !== "trajectory" || audit.configurationRole !== "observation"
      || audit.validationPassed !== true || audit.targetCoordinatesEmbedded !== false) {
    throw new Error("trajectory geometry requires a validated target-free observation response");
  }
  const reference = referencePositionsAngstrom.map((position, index) =>
    finiteVector(position, `reference site ${index + 1}`));
  const frames = response?.results?.frames;
  if (!Array.isArray(frames) || frames.length < 2) throw new Error("validated trajectory frames are unavailable");
  const normalized = frames.map((frame, frameIndex) => ({
    timeSeconds: Number(frame.timeSeconds),
    positionsAngstrom: frame.positionsAngstrom.map((position, siteIndex) =>
      finiteVector(position, `trajectory frame ${frameIndex + 1} site ${siteIndex + 1}`)),
  }));
  if (reference.length !== normalized[0].positionsAngstrom.length
      || normalized.some((frame) => frame.positionsAngstrom.length !== reference.length)) {
    throw new Error("validated trajectory site count no longer matches the observation");
  }
  const referenceMaximumMismatchAngstrom = Math.max(0, ...reference.map((position, index) =>
    norm(subtract(normalized[0].positionsAngstrom[index], position))));
  if (referenceMaximumMismatchAngstrom > referenceToleranceAngstrom) {
    throw new Error("trajectory reference frame does not match the exact ordered observation");
  }
  const displacements = normalized.map((frame) => frame.positionsAngstrom.map((position, index) =>
    subtract(position, reference[index])));
  const frameDrifts = displacements.map(meanVector);
  const centered = displacements.map((frame, frameIndex) => frame.map((vector) =>
    subtract(vector, frameDrifts[frameIndex])));
  const timeWeights = normalizedTrapezoidalWeights(normalized.map((frame) => frame.timeSeconds));
  const records = reference.map((_, siteIndex) => {
    const path = centered.map((frame) => frame[siteIndex]);
    const pathLengthAngstrom = path.slice(1).reduce((sum, vector, frameIndex) =>
      sum + norm(subtract(vector, path[frameIndex])), 0);
    const maximumExcursionAngstrom = Math.max(...path.map(norm));
    const rmsExcursionAngstrom = Math.sqrt(path.reduce((sum, vector) => sum + norm(vector) ** 2, 0)
      / path.length);
    const timeWeightedMeanDisplacementAngstrom = weightedMean(path, timeWeights);
    const covarianceCartesianAngstromSquared = weightedCovariance(path, timeWeights,
      timeWeightedMeanDisplacementAngstrom);
    const covarianceTraceAngstromSquared = covarianceCartesianAngstromSquared[0][0]
      + covarianceCartesianAngstromSquared[1][1] + covarianceCartesianAngstromSquared[2][2];
    const covarianceFrobeniusAngstromSquared = Math.sqrt(covarianceCartesianAngstromSquared
      .reduce((sum, row) => sum + row.reduce((inner, value) => inner + value * value, 0), 0));
    return {
      referenceIndex: siteIndex,
      endpointDisplacementAngstrom: path.at(-1).slice(),
      maximumExcursionAngstrom,
      rmsExcursionAngstrom,
      pathLengthAngstrom,
      timeWeightedMeanDisplacementAngstrom,
      covarianceCartesianAngstromSquared,
      covarianceTraceAngstromSquared,
      covarianceRmsAngstrom: Math.sqrt(Math.max(0, covarianceTraceAngstromSquared)),
      covarianceAnisotropy: covarianceTraceAngstromSquared > 0
        ? covarianceFrobeniusAngstromSquared / covarianceTraceAngstromSquared : 0,
    };
  });
  const timeSpanSeconds = normalized.at(-1).timeSeconds - normalized[0].timeSeconds;
  const endpointRmsAngstrom = Math.sqrt(records.reduce((sum, record) =>
    sum + norm(record.endpointDisplacementAngstrom) ** 2, 0) / records.length);
  const endpointMaximumAngstrom = Math.max(...records.map((record) => norm(record.endpointDisplacementAngstrom)));
  const meanPathLengthAngstrom = records.reduce((sum, record) => sum + record.pathLengthAngstrom, 0)
    / records.length;
  return {
    quantityId: "trajectory", configurationRole: "observation",
    configurationSha256: audit.configurationSha256, responseSha256,
    referenceToleranceAngstrom, referenceMaximumMismatchAngstrom,
    referenceMedianNearestAngstrom: medianNearestDistance(reference),
    frameCount: normalized.length, timeSpanSeconds,
    frameTimesSeconds: normalized.map((frame) => frame.timeSeconds),
    normalizedTrapezoidalTimeWeights: timeWeights,
    frameDriftAngstrom: frameDrifts,
    records,
    trajectoryProvenance: {
      available: true, source: "validated request-linked external-physics trajectory",
      responseSha256, requestSha256: audit.requestSha256,
      programName: audit.method.program, programVersion: audit.method.version,
      methodFamily: audit.method.family, methodSettingsSha256: audit.method.settingsSha256,
      frameCount: normalized.length, timeSpanSeconds,
      endpointRmsAngstrom, endpointMaximumAngstrom, meanPathLengthAngstrom,
      meanPathSpeedAngstromPerSecond: meanPathLengthAngstrom / timeSpanSeconds,
      covarianceSource: "time-weighted drift-removed empirical trajectory covariance",
      covarianceTimeWeighting: "normalized trapezoidal physical-time weights",
      covarianceFrame: "observation Cartesian angstrom squared",
      covarianceProbabilityDistributionInferred: false,
      covarianceThermalEquilibriumAssumed: false,
      covariancePhononModelAssumed: false,
      globalTranslationRemovedPerFrame: true,
      globalRotationRemovedPerFrame: false,
      exactObservationStructureMatched: true, validationGatePassed: true,
      targetUsed: false, usedAsPotential: false, usedAsPhysicalClock: false,
      trajectoryIntegratedByGcts: false,
    },
  };
}

export function bindValidatedTrajectoryGeometry(source, runtime, scenePerAngstrom) {
  if (!Array.isArray(source) || !source.length) throw new TypeError("observation sites are required");
  if (runtime?.quantityId !== "trajectory" || runtime.configurationRole !== "observation") {
    throw new Error("validated observation trajectory runtime is required");
  }
  if (!Number.isFinite(scenePerAngstrom) || scenePerAngstrom <= 0) {
    throw new TypeError("a positive scene-per-angstrom scale is required");
  }
  if (!Array.isArray(runtime.records) || runtime.records.length !== source.length) {
    throw new Error("validated trajectory site count no longer matches the observation");
  }
  source.forEach((atom, index) => {
    const record = runtime.records[index];
    atom.observedRelaxationWorldSceneArray = record.endpointDisplacementAngstrom
      .map((value) => value * scenePerAngstrom);
    atom.externalTrajectoryReferenceIndex = index;
    atom.externalTrajectoryPathLengthAngstrom = record.pathLengthAngstrom;
    atom.externalTrajectoryMaximumExcursionAngstrom = record.maximumExcursionAngstrom;
    atom.externalTrajectoryRmsExcursionAngstrom = record.rmsExcursionAngstrom;
    atom.trajectoryCovarianceCartesianA2 = record.covarianceCartesianAngstromSquared
      .map((row) => row.slice());
    atom.trajectoryCovarianceTraceA2 = record.covarianceTraceAngstromSquared;
    atom.trajectoryCovarianceRmsAngstrom = record.covarianceRmsAngstrom;
    atom.trajectoryCovarianceAnisotropy = record.covarianceAnisotropy;
    atom.trajectoryCovarianceSource = "time-weighted drift-removed empirical trajectory covariance";
    atom.externalTrajectoryResponseSha256 = runtime.responseSha256;
  });
  return {
    boundSites: source.length,
    properPoseTransport: "delta_r_world = R_cluster delta_r_local",
    covarianceProperPoseTransport: "C_world = R_cluster C_local R_cluster^T",
    covarianceModeAtBinding: "display-only",
    covarianceTimeWeighting: "normalized trapezoidal physical-time weights",
    globalTranslationRemovedPerFrame: true,
    globalRotationRemovedPerFrame: false,
    candidateGeometryChanged: false, candidateRankingChanged: false,
    trajectoryIntegrated: false, usedAsPhysicalClock: false,
    usedAsPotential: false, probabilityDistributionInferred: false,
    thermalEquilibriumAssumed: false, phononModelAssumed: false, targetUsed: false,
  };
}
