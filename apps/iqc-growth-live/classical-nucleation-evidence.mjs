export const BULK_DRIVING_FORCE_REQUEST_SCHEMA = "gcts-bulk-driving-force-request-v1";
export const BULK_DRIVING_FORCE_RESPONSE_SCHEMA = "gcts-bulk-driving-force-response-v1";

const EPS = 1e-12;
const ELECTRON_VOLT_JOULE = 1.602176634e-19;

function requiredText(value, label) {
  if (typeof value !== "string" || !value.trim()) throw new TypeError(`${label} is required`);
  return value.trim();
}

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

function digest(value, label) {
  const text = requiredText(value, label).toLowerCase();
  if (!/^[0-9a-f]{64}$/.test(text)) throw new TypeError(`${label} must be a SHA-256 digest`);
  return text;
}

function distance(first, second) {
  return Math.hypot(...first.map((value, axis) => value - second[axis]));
}

function triangleArea(first, second, third) {
  const a = second.map((value, axis) => value - first[axis]);
  const b = third.map((value, axis) => value - first[axis]);
  const cross = [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
    a[0] * b[1] - a[1] * b[0]];
  return Math.hypot(...cross) / 2;
}

export function measureNormalizedWulffGeometry(interfacialAudit) {
  const dimension = Number(interfacialAudit?.intrinsicDimension);
  if (![2, 3].includes(dimension)) throw new Error("validated 2D or 3D interfacial evidence is required");
  if (!interfacialAudit?.responseAccepted || interfacialAudit?.targetUsed) {
    throw new Error("accepted target-blind interfacial evidence is required");
  }
  const geometry = interfacialAudit.geometry;
  if (!geometry?.bounded || geometry.intrinsicDimension !== dimension || !geometry.facets?.length) {
    throw new Error("a bounded normalized Wulff geometry is required");
  }
  const orientationById = new Map(interfacialAudit.orientations.map((entry) =>
    [entry.orientationId, entry]));
  let normalizedContent = 0; let interfacialCoefficient = 0; let coefficientVariance = 0;
  const facetMeasures = geometry.facets.map((facet) => {
    const orientation = orientationById.get(facet.orientationId);
    if (!orientation) throw new Error(`active facet ${facet.orientationId} has no validated energy`);
    const points = facet.vertexIndices.map((index) => geometry.vertices[index]);
    let measure = 0;
    if (dimension === 2) {
      if (points.length !== 2) throw new Error("a 2D Wulff facet must be one line segment");
      measure = distance(points[0], points[1]);
      normalizedContent += measure * facet.supportDistance / 2;
    } else {
      for (let index = 1; index + 1 < points.length; index++) {
        measure += triangleArea(points[0], points[index], points[index + 1]);
      }
      normalizedContent += measure * facet.supportDistance / 3;
    }
    interfacialCoefficient += orientation.interfacialFreeEnergy * measure;
    coefficientVariance += (orientation.uncertainty * measure) ** 2;
    return { orientationId: facet.orientationId, measure, supportDistance: facet.supportDistance,
      interfacialFreeEnergy: orientation.interfacialFreeEnergy, uncertainty: orientation.uncertainty };
  });
  if (!(normalizedContent > EPS) || !(interfacialCoefficient > EPS)) {
    throw new Error("normalized Wulff content and interfacial coefficient must be positive");
  }
  const gammaMinimum = Math.min(...interfacialAudit.orientations.map((entry) => entry.interfacialFreeEnergy));
  const wulffIdentityResidual = Math.abs(interfacialCoefficient
    - dimension * gammaMinimum * normalizedContent);
  return { intrinsicDimension: dimension, normalizedContent, interfacialCoefficient,
    interfacialCoefficientUncertainty: Math.sqrt(coefficientVariance), gammaMinimum,
    facetMeasures, wulffIdentityResidual,
    wulffIdentityRelativeResidual: wulffIdentityResidual / interfacialCoefficient,
    targetUsed: false };
}

export function buildBulkDrivingForceRequest(input) {
  if (input?.targetUsed || input?.targetCoordinatesEmbedded) {
    throw new Error("a bulk-driving-force request cannot use a growth target");
  }
  const dimension = Number(input?.intrinsicDimension);
  if (![2, 3].includes(dimension)) throw new RangeError("intrinsicDimension must be 2 or 3");
  const structureSha256 = digest(input.structureSha256, "structure SHA-256");
  const interfacialEnergyResponseSha256 = digest(input.interfacialEnergyResponseSha256,
    "interfacial-energy response SHA-256");
  const temperatureKelvin = positive(input.temperatureKelvin, "temperature");
  return {
    schema: BULK_DRIVING_FORCE_REQUEST_SCHEMA,
    generatedAt: String(input.generatedAt),
    application: { name: "Materials Growth Lab", buildId: String(input.buildId) },
    specimen: { scenarioId: String(input.scenarioId),
      materialName: requiredText(input.materialName, "material name"), structureSha256,
      intrinsicDimension: dimension, sourceProvenance: input.sourceProvenance || null },
    coupledInterfacialEvidence: { interfacialEnergyResponseSha256,
      adjacentParentPhase: requiredText(input.adjacentParentPhase, "adjacent parent phase"),
      temperatureKelvin },
    calculation: {
      quantity: "positive parent-to-nucleus bulk free-energy driving-force density",
      definition: "delta_g = g_parent - g_nucleus; positive delta_g favors the declared nucleus phase",
      units: dimension === 3 ? "joule per cubic metre" : "joule per square metre",
      suitableMethods: ["same-condition phase free-energy calculation",
        "thermodynamic integration or assessed free-energy model", "calibrated experimental thermodynamics"],
      requiredOutputs: ["positive delta_g and one-sigma uncertainty", "parent and nucleus phase identities",
        "temperature, ensemble, method, settings digest, convergence and validation declarations"],
      responseSchema: BULK_DRIVING_FORCE_RESPONSE_SCHEMA,
    },
    expectedResponse: {
      schema: BULK_DRIVING_FORCE_RESPONSE_SCHEMA,
      requestSha256: "SHA-256 of this complete request file", structureSha256,
      interfacialEnergyResponseSha256, intrinsicDimension: dimension,
      units: dimension === 3 ? "joule per cubic metre" : "joule per square metre",
      temperatureKelvin, phases: { parent: "must equal adjacentParentPhase", nucleus: "required" },
      bulkDrivingFreeEnergyDensity: "finite positive delta_g",
      uncertainty: "finite nonnegative one-sigma uncertainty",
      method: { family: "required", program: "required", version: "declared or null",
        settingsSha256: "64 hexadecimal characters" },
      validation: { passed: true, converged: true, uncertaintyReported: true,
        phaseIdentityMatched: true },
    },
    safeguards: { requestOnly: true, targetCoordinatesEmbedded: false, targetUsedForSelection: false,
      supersaturationNotInferredFromGeometry: true, bulkDrivingForceNotInferredFromGrowth: true,
      responseMayOnlyBuildAConditionalClassicalNucleationWorkProfile: true,
      responseMayNotChangeGrowthRanking: true },
  };
}

export function validateBulkDrivingForceResponse(response, expected) {
  if (response?.schema !== BULK_DRIVING_FORCE_RESPONSE_SCHEMA) {
    throw new Error("unsupported bulk-driving-force response schema");
  }
  const requestSha256 = digest(response.requestSha256, "request SHA-256");
  const structureSha256 = digest(response.structureSha256, "structure SHA-256");
  const interfacialEnergyResponseSha256 = digest(response.interfacialEnergyResponseSha256,
    "interfacial-energy response SHA-256");
  if (requestSha256 !== digest(expected.requestSha256, "expected request SHA-256")
    || structureSha256 !== digest(expected.structureSha256, "expected structure SHA-256")
    || interfacialEnergyResponseSha256 !== digest(expected.interfacialEnergyResponseSha256,
      "expected interfacial-energy response SHA-256")) {
    throw new Error("bulk-driving-force response is not bound to the frozen request and interfacial evidence");
  }
  const dimension = Number(response.intrinsicDimension);
  if (dimension !== Number(expected.intrinsicDimension) || ![2, 3].includes(dimension)) {
    throw new Error("bulk-driving-force intrinsic dimension mismatch");
  }
  const expectedUnits = dimension === 3 ? "joule per cubic metre" : "joule per square metre";
  if (response.units !== expectedUnits) throw new Error(`response units must be '${expectedUnits}'`);
  const temperatureKelvin = positive(response.temperatureKelvin, "temperature");
  if (Math.abs(temperatureKelvin - positive(expected.temperatureKelvin, "expected temperature")) > 1e-6) {
    throw new Error("bulk and interfacial evidence temperatures differ");
  }
  const parentPhase = requiredText(response.phases?.parent, "parent phase");
  const nucleusPhase = requiredText(response.phases?.nucleus, "nucleus phase");
  if (parentPhase === nucleusPhase) throw new Error("parent and nucleus phases must differ");
  if (parentPhase !== requiredText(expected.adjacentParentPhase, "expected parent phase")) {
    throw new Error("bulk parent phase does not match the interfacial adjacent phase");
  }
  const bulkDrivingFreeEnergyDensity = positive(response.bulkDrivingFreeEnergyDensity,
    "bulk driving free-energy density");
  const uncertainty = finite(response.uncertainty, "bulk driving-force uncertainty");
  if (uncertainty < 0 || !(bulkDrivingFreeEnergyDensity - 3 * uncertainty > 0)) {
    throw new Error("bulk driving force must remain positive at the three-sigma lower bound");
  }
  for (const field of ["passed", "converged", "uncertaintyReported", "phaseIdentityMatched"]) {
    if (response.validation?.[field] !== true) throw new Error(`validation.${field} must be true`);
  }
  return { schema: BULK_DRIVING_FORCE_RESPONSE_SCHEMA, requestSha256, structureSha256,
    interfacialEnergyResponseSha256, intrinsicDimension: dimension, units: expectedUnits,
    temperatureKelvin, phases: { parent: parentPhase, nucleus: nucleusPhase },
    bulkDrivingFreeEnergyDensity, uncertainty,
    method: { family: requiredText(response.method?.family, "method family"),
      program: requiredText(response.method?.program, "method program"),
      version: response.method?.version == null ? null : String(response.method.version),
      settingsSha256: digest(response.method?.settingsSha256, "method settings SHA-256") },
    validation: { ...response.validation }, responseAccepted: true, targetUsed: false };
}

export function buildClassicalNucleationWork(interfacialAudit, bulkAudit) {
  if (!bulkAudit?.responseAccepted || bulkAudit?.targetUsed) {
    throw new Error("accepted target-blind bulk-driving-force evidence is required");
  }
  if (bulkAudit.structureSha256 !== interfacialAudit.structureSha256
    || bulkAudit.intrinsicDimension !== interfacialAudit.intrinsicDimension
    || bulkAudit.interfacialEnergyResponseSha256 !== interfacialAudit.responseSha256) {
    throw new Error("bulk and interfacial evidence are not bound to the same specimen and response");
  }
  const measure = measureNormalizedWulffGeometry(interfacialAudit);
  const dimension = measure.intrinsicDimension;
  const driving = bulkAudit.bulkDrivingFreeEnergyDensity;
  const criticalScaleMetre = (dimension - 1) * measure.interfacialCoefficient
    / (dimension * driving * measure.normalizedContent);
  const criticalContentSi = measure.normalizedContent * criticalScaleMetre ** dimension;
  const criticalInterfacialWorkJoule = measure.interfacialCoefficient
    * criticalScaleMetre ** (dimension - 1);
  const criticalBulkGainJoule = driving * criticalContentSi;
  const barrierJoule = criticalInterfacialWorkJoule - criticalBulkGainJoule;
  const coefficientRelativeSigma = measure.interfacialCoefficientUncertainty
    / measure.interfacialCoefficient;
  const drivingRelativeSigma = bulkAudit.uncertainty / driving;
  const criticalScaleRelativeSigma = Math.hypot(coefficientRelativeSigma, drivingRelativeSigma);
  const barrierRelativeSigma = Math.hypot(dimension * coefficientRelativeSigma,
    (dimension - 1) * drivingRelativeSigma);
  const points = Array.from({ length: 81 }, (_, index) => {
    const scaled = index / 20;
    const scaleMetre = scaled * criticalScaleMetre;
    const interfacialJoule = measure.interfacialCoefficient * scaleMetre ** (dimension - 1);
    const bulkJoule = driving * measure.normalizedContent * scaleMetre ** dimension;
    return { scaledCriticalCoordinate: scaled, scaleMetre,
      workJoule: interfacialJoule - bulkJoule,
      workElectronVolt: (interfacialJoule - bulkJoule) / ELECTRON_VOLT_JOULE };
  });
  return { schema: "gcts-conditional-classical-nucleation-work-v1", intrinsicDimension: dimension,
    structureSha256: bulkAudit.structureSha256,
    interfacialEnergyResponseSha256: bulkAudit.interfacialEnergyResponseSha256,
    bulkDrivingForceRequestSha256: bulkAudit.requestSha256,
    parentPhase: bulkAudit.phases.parent, nucleusPhase: bulkAudit.phases.nucleus,
    temperatureKelvin: bulkAudit.temperatureKelvin,
    normalizedWulffContent: measure.normalizedContent,
    interfacialCoefficient: measure.interfacialCoefficient,
    interfacialCoefficientUncertainty: measure.interfacialCoefficientUncertainty,
    wulffIdentityRelativeResidual: measure.wulffIdentityRelativeResidual,
    bulkDrivingFreeEnergyDensity: driving, bulkDrivingFreeEnergyDensityUncertainty: bulkAudit.uncertainty,
    criticalScaleMetre, criticalScaleNanometre: criticalScaleMetre * 1e9,
    criticalScaleUncertaintyNanometre: criticalScaleMetre * criticalScaleRelativeSigma * 1e9,
    criticalContentSi,
    criticalInterfacialWorkJoule, criticalBulkGainJoule,
    barrierJoule, barrierElectronVolt: barrierJoule / ELECTRON_VOLT_JOULE,
    barrierUncertaintyElectronVolt: barrierJoule * barrierRelativeSigma / ELECTRON_VOLT_JOULE,
    workProfile: points,
    uncertaintyModel: "independent one-sigma linear propagation from supplied gamma and delta_g",
    conditionalClassicalModel: true, heterogeneousShapeFactorApplied: false,
    atomicVolumeInferred: false, criticalAtomCountInferred: false,
    zeldovichFactorInferred: false, attachmentRateInferred: false, nucleationRateInferred: false,
    targetUsed: false,
    claimBoundary: "Conditional capillarity work for a homothetically scaled finite Wulff shape using validated oriented interfacial energies and an independently validated positive bulk driving-force density. No atom count, heterogeneous wetting factor, diffuse interface, elastic/strain energy, curvature correction, attachment kinetics, Zeldovich factor, prefactor, nucleation rate, pathway, or macroscopic phase stability is inferred." };
}
