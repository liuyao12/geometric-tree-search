const finite = (value) => Number.isFinite(Number(value));
const HEX64 = /^[a-f0-9]{64}$/;

function requiredText(value, label) {
  if (typeof value !== "string" || !value.trim()) throw new TypeError(`${label} is required`);
  return value.trim();
}

function canonicalValue(value) {
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (value && typeof value === "object") return Object.fromEntries(Object.keys(value).sort()
    .filter((key) => value[key] !== undefined).map((key) => [key, canonicalValue(value[key])]));
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new TypeError("canonical payload contains a non-finite number");
    return Object.is(value, -0) ? 0 : value;
  }
  return value;
}

export async function stateRelaxationSha256(value) {
  const bytes = new TextEncoder().encode(JSON.stringify(canonicalValue(value)));
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function normalizedSite(site, label) {
  const atomId = Number(site?.atomId);
  const species = requiredText(site?.species, `${label} species`);
  const positionAngstrom = Array.isArray(site?.positionAngstrom)
    ? site.positionAngstrom.map(Number) : [];
  if (!Number.isInteger(atomId) || atomId < 0 || positionAngstrom.length !== 3
      || !positionAngstrom.every(Number.isFinite)) {
    throw new TypeError(`${label} needs a nonnegative integer atomId and finite Cartesian position`);
  }
  return { atomId, species, positionAngstrom };
}

function normalizedSites(sites, label) {
  if (!Array.isArray(sites) || !sites.length) throw new TypeError(`${label} must be a nonempty array`);
  const normalized = sites.map((site, index) => normalizedSite(site, `${label} ${index + 1}`))
    .sort((first, second) => first.atomId - second.atomId);
  if (new Set(normalized.map((site) => site.atomId)).size !== normalized.length) {
    throw new Error(`${label} contains duplicate atom IDs`);
  }
  return normalized;
}

function siteGeometryPayload(sites) {
  return sites.map(({ atomId, species, positionAngstrom }) => ({ atomId, species, positionAngstrom }));
}

function normalizedCell(cell) {
  if (cell == null) return null;
  if (!Array.isArray(cell) || cell.length !== 3 || cell.some((row) =>
    !Array.isArray(row) || row.length !== 3 || !row.every(finite))) {
    throw new TypeError("cell must be null or a finite 3 by 3 matrix in angstroms");
  }
  return cell.map((row) => row.map(Number));
}

function determinant3(matrix) {
  return matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
    - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
    + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0]);
}

function transpose(matrix) {
  return matrix[0].map((_, column) => matrix.map((row) => row[column]));
}

function multiplyMatrices(first, second) {
  return first.map((row) => second[0].map((_, column) =>
    row.reduce((sum, value, index) => sum + value * second[index][column], 0)));
}

function multiplyVector(matrix, vector) {
  return matrix.map((row) => row.reduce((sum, value, index) => sum + value * vector[index], 0));
}

function inverse3(matrix) {
  const determinant = determinant3(matrix);
  if (!Number.isFinite(determinant) || Math.abs(determinant) <= 1e-12) {
    throw new Error("cell matrix must be nonsingular");
  }
  const [a, b, c] = matrix;
  return [
    [b[1] * c[2] - b[2] * c[1], a[2] * c[1] - a[1] * c[2], a[1] * b[2] - a[2] * b[1]],
    [b[2] * c[0] - b[0] * c[2], a[0] * c[2] - a[2] * c[0], a[2] * b[0] - a[0] * b[2]],
    [b[0] * c[1] - b[1] * c[0], a[1] * c[0] - a[0] * c[1], a[0] * b[1] - a[1] * b[0]],
  ].map((row) => row.map((value) => value / determinant));
}

function normalizedPeriodicBoundary(periodicBoundary) {
  if (!Array.isArray(periodicBoundary) || periodicBoundary.length !== 3
      || periodicBoundary.some((value) => typeof value !== "boolean")) {
    throw new TypeError("periodicBoundary must contain three booleans");
  }
  return [...periodicBoundary];
}

function statePayload(sites, cellAngstrom, periodicBoundary) {
  return { sites: siteGeometryPayload(sites), cellAngstrom, periodicBoundary };
}

function normalizedTensor(tensor, label) {
  if (!Array.isArray(tensor) || tensor.length !== 3 || tensor.some((row) =>
    !Array.isArray(row) || row.length !== 3 || !row.every(finite))) {
    throw new TypeError(`${label} must be a finite 3 by 3 tensor`);
  }
  const result = tensor.map((row) => row.map(Number));
  for (let row = 0; row < 3; row++) for (let column = row + 1; column < 3; column++) {
    if (Math.abs(result[row][column] - result[column][row]) > 1e-8) {
      throw new Error(`${label} must be symmetric`);
    }
  }
  return result;
}

export async function buildExternalStateRelaxationRequest({ generatedAt, buildId, materialName,
  sites, cellAngstrom = null, periodicBoundary = [false, false, false],
  boundary = null, sourceLeapReceiptSha256 = null, cellPolicy = "fixed",
  targetPressureGPa = null, targetUsed = false } = {}) {
  if (targetUsed) throw new Error("post-leap relaxation request may not use a target structure");
  const normalized = normalizedSites(sites, "initial site");
  const periodic = normalizedPeriodicBoundary(periodicBoundary);
  const cell = normalizedCell(cellAngstrom);
  if (periodic.some(Boolean) && !cell) throw new Error("periodic relaxation requires a cell");
  if (cell && Math.abs(determinant3(cell)) <= 1e-12) throw new Error("cell matrix must be nonsingular");
  if (!["fixed", "variable-isotropic-pressure"].includes(cellPolicy)) {
    throw new Error("cellPolicy must be fixed or variable-isotropic-pressure");
  }
  const variableCell = cellPolicy === "variable-isotropic-pressure";
  const pressure = targetPressureGPa == null ? null : Number(targetPressureGPa);
  if (variableCell && (!cell || !periodic.every(Boolean))) {
    throw new Error("variable-cell relaxation requires a fully periodic 3D cell");
  }
  if (variableCell && !Number.isFinite(pressure)) {
    throw new Error("variable-cell relaxation requires a finite target pressure in GPa");
  }
  if (!variableCell && pressure != null) throw new Error("fixed-cell relaxation cannot set target pressure");
  if (sourceLeapReceiptSha256 != null && !HEX64.test(String(sourceLeapReceiptSha256))) {
    throw new TypeError("source leap receipt SHA-256 must be 64 lowercase hex characters");
  }
  const initialGeometrySha256 = await stateRelaxationSha256(siteGeometryPayload(normalized));
  const initialStateSha256 = await stateRelaxationSha256(statePayload(normalized, cell, periodic));
  const request = {
    schema: "gcts-external-state-relaxation-request-v2",
    generatedAt: requiredText(generatedAt, "generation timestamp"),
    buildId: requiredText(buildId, "build ID"),
    materialName: requiredText(materialName, "material name"),
    initialState: {
      atomCount: normalized.length,
      sites: normalized,
      geometrySha256: initialGeometrySha256,
      stateSha256: initialStateSha256,
      cellAngstrom: cell,
      periodicBoundary: periodic,
      boundary: boundary == null ? null : canonicalValue(boundary),
      sourceLeapReceiptSha256,
    },
    calculation: {
      quantity: "fixed-composition structural relaxation of one exact post-leap colored configuration",
      allowedMethods: ["DFT geometry optimization", "validated interatomic-potential minimization",
        "machine-learned-potential relaxation with documented training domain"],
      requiredOutputs: ["one final Cartesian position for every supplied atom ID",
        "unchanged species and atom IDs", "authorized final cell and periodic axes",
        "total energy and energy unit", "maximum residual force",
        "force RMS", "convergence criterion and iteration count", "method and settings provenance"],
      cellPolicy,
      targetPressureGPa: variableCell ? pressure : null,
      requiredVariableCellOutputs: variableCell
        ? ["final 3 by 3 cell in angstroms", "symmetric final Cauchy stress tensor",
          "stress unit and sign convention", "maximum stress residual in GPa"] : [],
    },
    responseContract: {
      schema: "gcts-external-state-relaxation-response-v2",
      requiredFields: ["requestSha256", "initialGeometrySha256", "initialStateSha256",
        "finalGeometrySha256", "finalStateSha256", "finalCellAngstrom",
        "finalSites", "totalEnergy", "energyUnit", "maximumResidualForce", "forceRms",
        "forceUnit", "converged", "convergenceCriterion", "iterationCount", "method",
        "methodVersion", "settingsSha256"],
      finalSitesOrdering: "ascending integer atomId",
      geometryHashCanonicalization: "UTF-8 JSON; object keys sorted lexicographically; sites sorted by atomId; finite numbers; SHA-256 lowercase hex",
      acceptedEnergyUnits: ["eV", "hartree"],
      acceptedForceUnits: ["eV/angstrom", "hartree/bohr"],
      acceptedStressUnits: ["GPa", "eV/angstrom^3"],
    },
    safeguards: {
      topologyAndSpeciesMustBePreserved: true,
      atomCountMayChange: false,
      cellRelaxationAuthorized: variableCell,
      periodicAxesMayChange: false,
      targetPressureGPa: variableCell ? pressure : null,
      targetStructureUsed: false,
      browserGeometryOptimizerUsed: false,
      responseMustBindInitialGeometrySha256: true,
      adoptionCreatesNewObservationRound: true,
    },
  };
  return { ...request, requestSha256: await stateRelaxationSha256(request) };
}

function displacementAudit(initialSites, finalSites, initialCell, finalCell, periodicBoundary) {
  const initialById = new Map(initialSites.map((site) => [site.atomId, site]));
  const periodicCell = initialCell && finalCell && periodicBoundary.some(Boolean);
  const initialMatrix = periodicCell ? transpose(initialCell) : null;
  const finalMatrix = periodicCell ? transpose(finalCell) : null;
  const initialInverse = periodicCell ? inverse3(initialMatrix) : null;
  const finalInverse = periodicCell ? inverse3(finalMatrix) : null;
  const records = finalSites.map((site) => {
    const initial = initialById.get(site.atomId);
    let affine = [0, 0, 0];
    let nonAffine;
    if (periodicCell) {
      const initialFractional = multiplyVector(initialInverse, initial.positionAngstrom);
      const finalFractional = multiplyVector(finalInverse, site.positionAngstrom);
      const fractionalChange = finalFractional.map((value, axis) => {
        const delta = value - initialFractional[axis];
        return periodicBoundary[axis] ? delta - Math.round(delta) : delta;
      });
      affine = multiplyVector(finalMatrix, initialFractional)
        .map((value, axis) => value - initial.positionAngstrom[axis]);
      nonAffine = multiplyVector(finalMatrix, fractionalChange);
    } else nonAffine = site.positionAngstrom.map((value, axis) => value - initial.positionAngstrom[axis]);
    const vector = affine.map((value, axis) => value + nonAffine[axis]);
    return { atomId: site.atomId, species: site.species, displacementAngstrom: vector,
      affineDisplacementAngstrom: affine, nonAffineDisplacementAngstrom: nonAffine,
      magnitudeAngstrom: Math.hypot(...vector), affineMagnitudeAngstrom: Math.hypot(...affine),
      nonAffineMagnitudeAngstrom: Math.hypot(...nonAffine) };
  });
  const rms = (field) => Math.sqrt(records.reduce((sum, record) => sum + record[field] ** 2, 0)
    / records.length);
  return { records,
    rmsAngstrom: rms("magnitudeAngstrom"),
    affineRmsAngstrom: rms("affineMagnitudeAngstrom"),
    nonAffineRmsAngstrom: rms("nonAffineMagnitudeAngstrom"),
    maximumAngstrom: Math.max(...records.map((record) => record.magnitudeAngstrom)),
    movedAtomCount: records.filter((record) => record.magnitudeAngstrom > 1e-10).length };
}

function cellDeformationAudit(initialCell, finalCell, cellPolicy) {
  if (!initialCell && !finalCell) return { cellPolicy, cellPresent: false, cellPreserved: true,
    initialVolumeCubicAngstrom: null, finalVolumeCubicAngstrom: null, volumeRatio: null,
    volumetricStrain: null, deformationGradient: null, greenLagrangeStrain: null,
    greenLagrangeStrainNorm: null, maximumAbsGreenLagrangeStrain: null };
  if (!initialCell || !finalCell) throw new Error("relaxation cannot create or remove a periodic cell");
  const initialMatrix = transpose(initialCell); const finalMatrix = transpose(finalCell);
  const initialDeterminant = determinant3(initialMatrix); const finalDeterminant = determinant3(finalMatrix);
  if (initialDeterminant * finalDeterminant <= 0) throw new Error("relaxation inverted the cell handedness");
  const deformationGradient = multiplyMatrices(finalMatrix, inverse3(initialMatrix));
  const rightCauchyGreen = multiplyMatrices(transpose(deformationGradient), deformationGradient);
  const strain = rightCauchyGreen.map((row, i) => row.map((value, j) =>
    .5 * (value - (i === j ? 1 : 0))));
  const flat = strain.flat();
  const exactCellPreserved = JSON.stringify(initialCell) === JSON.stringify(finalCell);
  if (cellPolicy === "fixed" && !exactCellPreserved) throw new Error("fixed-cell relaxation changed the cell");
  const initialVolume = Math.abs(initialDeterminant); const finalVolume = Math.abs(finalDeterminant);
  return { cellPolicy, cellPresent: true, cellPreserved: exactCellPreserved,
    initialVolumeCubicAngstrom: initialVolume, finalVolumeCubicAngstrom: finalVolume,
    volumeRatio: finalVolume / initialVolume, volumetricStrain: finalVolume / initialVolume - 1,
    deformationGradient, greenLagrangeStrain: strain,
    greenLagrangeStrainNorm: Math.hypot(...flat),
    maximumAbsGreenLagrangeStrain: Math.max(...flat.map(Math.abs)) };
}

export async function validateExternalStateRelaxationResponse(response, request) {
  if (response?.schema !== "gcts-external-state-relaxation-response-v2") {
    throw new Error("relaxation response schema must be gcts-external-state-relaxation-response-v2");
  }
  if (request?.schema !== "gcts-external-state-relaxation-request-v2"
      || !HEX64.test(String(request.requestSha256 || ""))) {
    throw new Error("a valid frozen relaxation request is required");
  }
  const { requestSha256, ...requestPayload } = request;
  if (await stateRelaxationSha256(requestPayload) !== requestSha256) {
    throw new Error("frozen relaxation request SHA-256 no longer matches its payload");
  }
  if (response.requestSha256 !== request.requestSha256
      || response.initialGeometrySha256 !== request.initialState.geometrySha256
      || response.initialStateSha256 !== request.initialState.stateSha256) {
    throw new Error("relaxation response does not bind the frozen request, geometry, and cell state");
  }
  const finalSites = normalizedSites(response.finalSites, "final site");
  const initialSites = request.initialState.sites;
  if (finalSites.length !== initialSites.length) throw new Error("relaxation changed the atom count");
  const initialById = new Map(initialSites.map((site) => [site.atomId, site]));
  finalSites.forEach((site) => {
    const initial = initialById.get(site.atomId);
    if (!initial) throw new Error(`relaxation introduced unknown atom ID ${site.atomId}`);
    if (initial.species !== site.species) throw new Error(`relaxation changed species for atom ID ${site.atomId}`);
  });
  if (finalSites.some((site) => !initialById.has(site.atomId))
      || finalSites.length !== initialById.size) throw new Error("relaxation atom-ID topology is incomplete");
  const variableCell = request.calculation.cellPolicy === "variable-isotropic-pressure";
  if (variableCell && response.finalCellAngstrom == null) {
    throw new Error("variable-cell relaxation must return finalCellAngstrom");
  }
  const finalCellAngstrom = normalizedCell(response.finalCellAngstrom
    ?? request.initialState.cellAngstrom);
  const cell = cellDeformationAudit(request.initialState.cellAngstrom, finalCellAngstrom,
    request.calculation.cellPolicy);
  const totalEnergy = Number(response.totalEnergy);
  const maximumResidualForce = Number(response.maximumResidualForce);
  const forceRms = Number(response.forceRms);
  const iterationCount = Number(response.iterationCount);
  const converged = response.converged === true;
  if (![totalEnergy, maximumResidualForce, forceRms].every(Number.isFinite)
      || maximumResidualForce < 0 || forceRms < 0 || !Number.isInteger(iterationCount)
      || iterationCount < 1 || !converged) {
    throw new Error("relaxation needs converged finite energy/force evidence and a positive iteration count");
  }
  const energyUnit = requiredText(response.energyUnit, "energy unit");
  const forceUnit = requiredText(response.forceUnit, "force unit");
  if (!new Set(["eV", "hartree"]).has(energyUnit)
      || !new Set(["eV/angstrom", "hartree/bohr"]).has(forceUnit)) {
    throw new Error("relaxation units must be eV or hartree and eV/angstrom or hartree/bohr");
  }
  const finalGeometrySha256 = await stateRelaxationSha256(siteGeometryPayload(finalSites));
  if (response.finalGeometrySha256 !== finalGeometrySha256) {
    throw new Error("relaxation final geometry SHA-256 does not match finalSites");
  }
  const finalStateSha256 = await stateRelaxationSha256(statePayload(finalSites,
    finalCellAngstrom, request.initialState.periodicBoundary));
  if (response.finalStateSha256 !== finalStateSha256) {
    throw new Error("relaxation final state SHA-256 does not match finalSites, cell, and periodic axes");
  }
  let stress = null;
  if (variableCell || response.stressTensor != null) {
    const tensor = normalizedTensor(response.stressTensor, "stressTensor");
    const unit = requiredText(response.stressUnit, "stress unit");
    if (!["GPa", "eV/angstrom^3"].includes(unit)) {
      throw new Error("stress unit must be GPa or eV/angstrom^3");
    }
    const maximumResidualGPa = Number(response.maximumStressResidualGPa);
    const reportedTargetPressureGPa = Number(response.targetPressureGPa);
    if (!Number.isFinite(maximumResidualGPa) || maximumResidualGPa < 0
        || !Number.isFinite(reportedTargetPressureGPa)
        || Math.abs(reportedTargetPressureGPa - request.calculation.targetPressureGPa) > 1e-12) {
      throw new Error("variable-cell response needs its frozen target pressure and finite stress residual");
    }
    stress = { tensor, unit, convention: requiredText(response.stressConvention, "stress convention"),
      targetPressureGPa: reportedTargetPressureGPa, maximumResidualGPa };
  }
  const method = requiredText(response.method, "relaxation method");
  const settingsSha256 = requiredText(response.settingsSha256, "settings SHA-256");
  if (!HEX64.test(settingsSha256)) throw new Error("settings SHA-256 must be 64 lowercase hex characters");
  const convergenceCriterion = requiredText(response.convergenceCriterion, "convergence criterion");
  const displacement = displacementAudit(initialSites, finalSites,
    request.initialState.cellAngstrom, finalCellAngstrom, request.initialState.periodicBoundary);
  const normalizedResponse = { schema: response.schema, requestSha256: response.requestSha256,
    initialGeometrySha256: response.initialGeometrySha256,
    initialStateSha256: response.initialStateSha256, finalGeometrySha256, finalStateSha256,
    finalSites, finalCellAngstrom, totalEnergy, energyUnit, maximumResidualForce, forceRms, forceUnit,
    converged, convergenceCriterion, iterationCount, method, settingsSha256,
    methodVersion: response.methodVersion == null ? null : String(response.methodVersion), stress,
    uncertainty: response.uncertainty == null ? null : canonicalValue(response.uncertainty) };
  return {
    schema: "gcts-validated-external-state-relaxation-v2",
    response: normalizedResponse,
    responseSha256: await stateRelaxationSha256(normalizedResponse),
    audit: {
      atomCount: finalSites.length,
      atomCountPreserved: true,
      atomIdsPreserved: true,
      speciesPreserved: true,
      cell,
      cellPreserved: cell.cellPreserved,
      cellRelaxationAuthorized: variableCell,
      exactFinalGeometryBound: true,
      convergenceEvidencePresent: true,
      displacement,
      targetUsed: false,
      browserRelaxationUsed: false,
      physicalTimeInferred: false,
      adoptionRequiresNewObservationRound: true,
      claimBoundary: `This validates one externally computed fixed-composition ${variableCell
        ? "variable-cell, fixed-pressure" : "fixed-cell"} relaxed endpoint. It does not infer the relaxation trajectory, elapsed time, transition barrier, thermal ensemble, equation of state, elastic constants, or transferability of the supplied method.`,
    },
  };
}
