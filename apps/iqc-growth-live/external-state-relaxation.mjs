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

export async function buildExternalStateRelaxationRequest({ generatedAt, buildId, materialName,
  sites, cellAngstrom = null, periodicBoundary = [false, false, false],
  boundary = null, sourceLeapReceiptSha256 = null, targetUsed = false } = {}) {
  if (targetUsed) throw new Error("post-leap relaxation request may not use a target structure");
  const normalized = normalizedSites(sites, "initial site");
  if (!Array.isArray(periodicBoundary) || periodicBoundary.length !== 3
      || periodicBoundary.some((value) => typeof value !== "boolean")) {
    throw new TypeError("periodicBoundary must contain three booleans");
  }
  if (sourceLeapReceiptSha256 != null && !HEX64.test(String(sourceLeapReceiptSha256))) {
    throw new TypeError("source leap receipt SHA-256 must be 64 lowercase hex characters");
  }
  const initialGeometrySha256 = await stateRelaxationSha256(siteGeometryPayload(normalized));
  const request = {
    schema: "gcts-external-state-relaxation-request-v1",
    generatedAt: requiredText(generatedAt, "generation timestamp"),
    buildId: requiredText(buildId, "build ID"),
    materialName: requiredText(materialName, "material name"),
    initialState: {
      atomCount: normalized.length,
      sites: normalized,
      geometrySha256: initialGeometrySha256,
      cellAngstrom: normalizedCell(cellAngstrom),
      periodicBoundary: [...periodicBoundary],
      boundary: boundary == null ? null : canonicalValue(boundary),
      sourceLeapReceiptSha256,
    },
    calculation: {
      quantity: "fixed-composition structural relaxation of one exact post-leap colored configuration",
      allowedMethods: ["DFT geometry optimization", "validated interatomic-potential minimization",
        "machine-learned-potential relaxation with documented training domain"],
      requiredOutputs: ["one final Cartesian position for every supplied atom ID",
        "unchanged species and atom IDs", "total energy and energy unit", "maximum residual force",
        "force RMS", "convergence criterion and iteration count", "method and settings provenance"],
      cellPolicy: "fixed unless a future request explicitly authorizes cell relaxation",
    },
    responseContract: {
      schema: "gcts-external-state-relaxation-response-v1",
      requiredFields: ["requestSha256", "initialGeometrySha256", "finalGeometrySha256",
        "finalSites", "totalEnergy", "energyUnit", "maximumResidualForce", "forceRms",
        "forceUnit", "converged", "convergenceCriterion", "iterationCount", "method",
        "methodVersion", "settingsSha256"],
      finalSitesOrdering: "ascending integer atomId",
      geometryHashCanonicalization: "UTF-8 JSON; object keys sorted lexicographically; sites sorted by atomId; finite numbers; SHA-256 lowercase hex",
      acceptedEnergyUnits: ["eV", "hartree"],
      acceptedForceUnits: ["eV/angstrom", "hartree/bohr"],
    },
    safeguards: {
      topologyAndSpeciesMustBePreserved: true,
      atomCountMayChange: false,
      cellRelaxationAuthorized: false,
      targetStructureUsed: false,
      browserGeometryOptimizerUsed: false,
      responseMustBindInitialGeometrySha256: true,
      adoptionCreatesNewObservationRound: true,
    },
  };
  return { ...request, requestSha256: await stateRelaxationSha256(request) };
}

function displacementAudit(initialSites, finalSites) {
  const initialById = new Map(initialSites.map((site) => [site.atomId, site]));
  const records = finalSites.map((site) => {
    const initial = initialById.get(site.atomId);
    const vector = site.positionAngstrom.map((value, axis) => value - initial.positionAngstrom[axis]);
    return { atomId: site.atomId, species: site.species, displacementAngstrom: vector,
      magnitudeAngstrom: Math.hypot(...vector) };
  });
  const squared = records.reduce((sum, record) => sum + record.magnitudeAngstrom ** 2, 0);
  return { records,
    rmsAngstrom: Math.sqrt(squared / records.length),
    maximumAngstrom: Math.max(...records.map((record) => record.magnitudeAngstrom)),
    movedAtomCount: records.filter((record) => record.magnitudeAngstrom > 1e-10).length };
}

export async function validateExternalStateRelaxationResponse(response, request) {
  if (response?.schema !== "gcts-external-state-relaxation-response-v1") {
    throw new Error("relaxation response schema must be gcts-external-state-relaxation-response-v1");
  }
  if (request?.schema !== "gcts-external-state-relaxation-request-v1"
      || !HEX64.test(String(request.requestSha256 || ""))) {
    throw new Error("a valid frozen relaxation request is required");
  }
  const { requestSha256, ...requestPayload } = request;
  if (await stateRelaxationSha256(requestPayload) !== requestSha256) {
    throw new Error("frozen relaxation request SHA-256 no longer matches its payload");
  }
  if (response.requestSha256 !== request.requestSha256
      || response.initialGeometrySha256 !== request.initialState.geometrySha256) {
    throw new Error("relaxation response does not bind the frozen request and initial geometry");
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
  const method = requiredText(response.method, "relaxation method");
  const settingsSha256 = requiredText(response.settingsSha256, "settings SHA-256");
  if (!HEX64.test(settingsSha256)) throw new Error("settings SHA-256 must be 64 lowercase hex characters");
  const convergenceCriterion = requiredText(response.convergenceCriterion, "convergence criterion");
  const displacement = displacementAudit(initialSites, finalSites);
  const normalizedResponse = { schema: response.schema, requestSha256: response.requestSha256,
    initialGeometrySha256: response.initialGeometrySha256, finalGeometrySha256,
    finalSites, totalEnergy, energyUnit, maximumResidualForce, forceRms, forceUnit,
    converged, convergenceCriterion, iterationCount, method, settingsSha256,
    methodVersion: response.methodVersion == null ? null : String(response.methodVersion),
    uncertainty: response.uncertainty == null ? null : canonicalValue(response.uncertainty) };
  return {
    schema: "gcts-validated-external-state-relaxation-v1",
    response: normalizedResponse,
    responseSha256: await stateRelaxationSha256(normalizedResponse),
    audit: {
      atomCount: finalSites.length,
      atomCountPreserved: true,
      atomIdsPreserved: true,
      speciesPreserved: true,
      cellPreserved: true,
      exactFinalGeometryBound: true,
      convergenceEvidencePresent: true,
      displacement,
      targetUsed: false,
      browserRelaxationUsed: false,
      physicalTimeInferred: false,
      adoptionRequiresNewObservationRound: true,
      claimBoundary: "This validates one externally computed fixed-composition relaxed endpoint. It does not infer the relaxation trajectory, elapsed time, transition barrier, thermodynamic ensemble, or transferability of the supplied method.",
    },
  };
}
