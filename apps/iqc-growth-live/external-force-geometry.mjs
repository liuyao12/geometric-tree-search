function finiteVector(vector, label) {
  if (!Array.isArray(vector) || vector.length !== 3 || !vector.every(Number.isFinite)) {
    throw new TypeError(`${label} must be a finite three-vector`);
  }
  return vector.map(Number);
}

export function buildValidatedForceGeometryRuntime(response, audit, responseSha256) {
  if (audit?.quantityId !== "forces" || audit.configurationRole !== "observation"
      || audit.validationPassed !== true || audit.targetCoordinatesEmbedded !== false) {
    throw new Error("force geometry requires a validated target-free observation response");
  }
  const vectors = response?.results?.forceVectorsElectronVoltPerAngstrom;
  if (!Array.isArray(vectors) || !vectors.length) throw new Error("validated force vectors are unavailable");
  const normalized = vectors.map((vector, index) => finiteVector(vector, `force site ${index + 1}`));
  const magnitudes = normalized.map((vector) => Math.hypot(...vector));
  const forceRmsElectronVoltPerAngstrom = Math.sqrt(magnitudes.reduce((sum, value) => sum + value ** 2, 0)
    / normalized.length);
  const forceMaximumElectronVoltPerAngstrom = Math.max(...magnitudes);
  const sortedMagnitudes = magnitudes.slice().sort((first, second) => first - second);
  const forceP90ElectronVoltPerAngstrom = sortedMagnitudes[
    Math.floor(.9 * Math.max(0, sortedMagnitudes.length - 1))];
  const stress = response.results.stressTensorGigaPascal === undefined
    || response.results.stressTensorGigaPascal === null ? null
    : response.results.stressTensorGigaPascal.map((row, index) => finiteVector(row, `stress row ${index + 1}`));
  if (stress && stress.length !== 3) throw new TypeError("stress tensor must contain three rows");
  const stressHydrostaticGigaPascal = stress
    ? (stress[0][0] + stress[1][1] + stress[2][2]) / 3 : null;
  const stressFrobeniusGigaPascal = stress
    ? Math.sqrt(stress.flat().reduce((sum, value) => sum + value ** 2, 0)) : null;
  const stressDeviatoricFrobeniusGigaPascal = stress ? Math.sqrt(stress.reduce((sum, row, i) =>
    sum + row.reduce((inner, value, j) => inner
      + (value - (i === j ? stressHydrostaticGigaPascal : 0)) ** 2, 0), 0)) : null;
  const totalEnergyElectronVolt = Number(response.results.totalEnergyElectronVolt);
  if (!Number.isFinite(totalEnergyElectronVolt)) throw new TypeError("total energy must be finite");
  return {
    quantityId: "forces", configurationRole: "observation",
    configurationSha256: audit.configurationSha256, responseSha256,
    forceVectorsElectronVoltPerAngstrom: normalized,
    forceP90ElectronVoltPerAngstrom,
    calculationProvenance: {
      available: true, source: "validated request-linked external-physics response",
      responseSha256, requestSha256: audit.requestSha256,
      programName: audit.method.program, programVersion: audit.method.version,
      methodFamily: audit.method.family, methodSettingsSha256: audit.method.settingsSha256,
      forceCoverage: 1, forceVectorCount: normalized.length,
      forceRmsElectronVoltPerAngstrom, forceMaximumElectronVoltPerAngstrom,
      forceP90ElectronVoltPerAngstrom,
      totalEnergyElectronVolt,
      energyPerPrimitiveAtomElectronVolt: totalEnergyElectronVolt / normalized.length,
      stressCoverage: stress ? 1 : 0, stressTensorGigaPascal: stress,
      stressHydrostaticGigaPascal, stressFrobeniusGigaPascal,
      stressDeviatoricFrobeniusGigaPascal,
      exactObservationStructureMatched: true, validationGatePassed: true,
      targetUsed: false, usedAsPotential: false, physicalTimeModeled: false,
    },
  };
}

export function validatedForcePairGeometry(runtime, firstIndex, secondIndex, direction) {
  const vectors = runtime?.forceVectorsElectronVoltPerAngstrom;
  const first = vectors?.[firstIndex];
  const second = vectors?.[secondIndex];
  if (!first || !second) return { available: false, reason: "validated pair forces unavailable" };
  const axis = finiteVector(direction, "pair direction");
  const length = Math.hypot(...axis);
  if (!(length > 1e-14)) throw new Error("pair direction must be nonzero");
  const unit = axis.map((value) => value / length);
  const project = (vector) => vector.reduce((sum, value, component) =>
    sum + value * unit[component], 0);
  const firstAlongConnection = project(first);
  const secondAlongConnection = project(second);
  const inwardProjectionElectronVoltPerAngstrom = .5
    * (firstAlongConnection - secondAlongConnection);
  const commonModeProjectionElectronVoltPerAngstrom = .5
    * (firstAlongConnection + secondAlongConnection);
  const relative = second.map((value, component) => value - first[component]);
  const relativeNorm = Math.hypot(...relative);
  const relativeLongitudinal = project(relative);
  const transverseRelativeElectronVoltPerAngstrom = Math.sqrt(Math.max(0,
    relativeNorm ** 2 - relativeLongitudinal ** 2));
  const normalization = Math.max(1e-14,
    runtime.forceP90ElectronVoltPerAngstrom
      || runtime.calculationProvenance?.forceP90ElectronVoltPerAngstrom
      || runtime.calculationProvenance?.forceRmsElectronVoltPerAngstrom || 0);
  return {
    available: true,
    firstReferenceIndex: firstIndex,
    secondReferenceIndex: secondIndex,
    inwardProjectionElectronVoltPerAngstrom,
    commonModeProjectionElectronVoltPerAngstrom,
    transverseRelativeElectronVoltPerAngstrom,
    normalizedInwardProjection: Math.max(-1, Math.min(1,
      inwardProjectionElectronVoltPerAngstrom / normalization)),
    normalization: "observation force-magnitude p90",
    normalizationElectronVoltPerAngstrom: normalization,
    properRotationInvariant: true,
    forceFieldInferred: false,
    energySurfaceInferred: false,
    targetUsed: false,
  };
}

export function bindValidatedForceGeometry(source, runtime) {
  if (!Array.isArray(source) || !source.length) throw new TypeError("observation sites are required");
  if (runtime?.quantityId !== "forces" || runtime.configurationRole !== "observation") {
    throw new Error("validated observation force runtime is required");
  }
  const vectors = runtime.forceVectorsElectronVoltPerAngstrom;
  if (!Array.isArray(vectors) || vectors.length !== source.length) {
    throw new Error("validated external-force vector count no longer matches the observation");
  }
  source.forEach((atom, index) => {
    atom.calculationForceEvPerAngstrom = vectors[index].slice();
    atom.calculationForceResponseSha256 = runtime.responseSha256;
    atom.calculationForceValidatedExternal = true;
    atom.externalForceReferenceIndex = index;
  });
  return { boundSites: source.length, properPoseTransport: "F_world = R_cluster F_local",
    candidateGeometryChanged: false, candidateRankingChanged: false,
    forceIntegrated: false, usedAsPotential: false, physicalTimeModeled: false, targetUsed: false };
}
