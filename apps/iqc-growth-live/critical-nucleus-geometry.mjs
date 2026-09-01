export const CRITICAL_NUCLEUS_GEOMETRY_REQUEST_SCHEMA =
  "gcts-critical-nucleus-geometry-request-v1";
export const CRITICAL_NUCLEUS_GEOMETRY_RESPONSE_SCHEMA =
  "gcts-critical-nucleus-geometry-response-v1";

const ANGSTROM_METRE = 1e-10;
const UINT32_RANGE = 0x1_0000_0000;

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

function probability(value, label) {
  const number = finite(value, label);
  if (number < 0 || number > 1) throw new RangeError(`${label} must be in [0,1]`);
  return number;
}

function digest(value, label) {
  const text = requiredText(value, label).toLowerCase();
  if (!/^[0-9a-f]{64}$/.test(text)) throw new TypeError(`${label} must be a SHA-256 digest`);
  return text;
}

function mulberry32(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return (((value ^ (value >>> 14)) >>> 0) + .5) / UINT32_RANGE;
  };
}

function requireSchedule(schedule) {
  if (schedule?.schema !== "gcts-conditional-nucleation-schedule-v1"
      || schedule?.targetUsed || schedule?.gctsSeedChanged) {
    throw new Error("an accepted target-blind conditional nucleation schedule is required");
  }
  const dimension = Number(schedule.intrinsicDimension);
  if (![2, 3].includes(dimension)) throw new RangeError("schedule dimension must be 2 or 3");
  return dimension;
}

export function buildCriticalNucleusGeometryRequest(input) {
  if (input?.targetUsed || input?.targetCoordinatesEmbedded) {
    throw new Error("a critical-nucleus geometry request cannot use a growth target");
  }
  const schedule = input?.schedule;
  const dimension = requireSchedule(schedule);
  const scheduleSha256 = digest(input.scheduleSha256, "schedule SHA-256");
  const structureSha256 = digest(schedule.structureSha256, "structure SHA-256");
  const workSha256 = digest(schedule.workSha256, "nucleation-work SHA-256");
  const kineticsRequestSha256 = digest(schedule.kineticsRequestSha256,
    "kinetics-request SHA-256");
  const criticalScaleMetre = positive(input.criticalScaleMetre, "critical scale");
  return {
    schema: CRITICAL_NUCLEUS_GEOMETRY_REQUEST_SCHEMA,
    generatedAt: String(input.generatedAt),
    application: { name: "Materials Growth Lab", buildId: String(input.buildId) },
    specimen: {
      scenarioId: String(input.scenarioId),
      materialName: requiredText(input.materialName, "material name"),
      structureSha256,
      intrinsicDimension: dimension,
      sourceProvenance: input.sourceProvenance || null,
    },
    coupledEvidence: {
      scheduleSha256,
      workSha256,
      kineticsRequestSha256,
      parentPhase: requiredText(schedule.parentPhase, "parent phase"),
      nucleusPhase: requiredText(schedule.nucleusPhase, "nucleus phase"),
      temperatureKelvin: positive(schedule.temperatureKelvin, "temperature"),
      criticalScaleMetre,
    },
    calculation: {
      quantity: "representative atomistic critical-nucleus geometry",
      suitableMethods: [
        "committor-validated rare-event ensemble with a declared structural classifier",
        "umbrella, transition-interface, forward-flux, or seeding calculation with atomistic snapshots",
        "experimentally constrained atomistic nucleus model at the declared thermodynamic state",
      ],
      requiredOutputs: [
        "species-labelled Cartesian sites for one declared representative critical configuration",
        "per-site nucleus-membership probabilities and core/interface labels",
        "committor evidence whose uncertainty interval contains one half",
        "method, classifier, ensemble, settings digest, convergence, and validation declarations",
      ],
      responseSchema: CRITICAL_NUCLEUS_GEOMETRY_RESPONSE_SCHEMA,
    },
    expectedResponse: {
      schema: CRITICAL_NUCLEUS_GEOMETRY_RESPONSE_SCHEMA,
      requestSha256: "SHA-256 of this complete request file",
      scheduleSha256,
      workSha256,
      structureSha256,
      intrinsicDimension: dimension,
      temperatureKelvin: schedule.temperatureKelvin,
      phases: { parent: schedule.parentPhase, nucleus: schedule.nucleusPhase },
      geometry: {
        coordinateUnits: "angstrom",
        periodic: false,
        sites: "2 to 4096 unique species-labelled Cartesian sites",
        siteRecord: { siteId: "unique string", species: "element/chemistry token",
          positionAngstrom: ["x", "y", "z"], membershipProbability: "value in [0.5,1]",
          region: "core or interface" },
        orientationDistribution: dimension === 3 ? "isotropic-proper-rotation"
          : "uniform-in-plane",
      },
      criticality: {
        reactionCoordinateName: "required",
        meanCommittor: "finite value in [0,1]",
        committorStandardError: "finite positive value; interval must contain 0.5",
        independentShootingTrajectories: "integer >= 20",
        representativeSelection: "required",
      },
      method: { family: "required", program: "required", version: "declared or null",
        settingsSha256: "64 hexadecimal characters", classifier: "required" },
      validation: { passed: true, converged: true, uncertaintiesReported: true,
        criticalityValidated: true, speciesAndUnitsValidated: true,
        representativeGeometryDeclared: true },
    },
    safeguards: {
      requestOnly: true,
      targetCoordinatesEmbedded: false,
      targetUsedForSelection: false,
      cntScaleDoesNotDetermineAtomCount: true,
      geometryMustComeFromIndependentEvidence: true,
      responseMayOnlySupplyAPreviewPrototype: true,
      responseMayNotAlterGctsCandidatesAdmissionRankingOrClock: true,
      heterogeneousAndNonclassicalNucleiRemainOpen: true,
    },
  };
}

function same(expected, actual, label) {
  if (requiredText(actual, label) !== requiredText(expected, `expected ${label}`)) {
    throw new Error(`${label} mismatch`);
  }
}

export function validateCriticalNucleusGeometryResponse(response, expected) {
  if (response?.schema !== CRITICAL_NUCLEUS_GEOMETRY_RESPONSE_SCHEMA) {
    throw new Error("unsupported critical-nucleus geometry response schema");
  }
  for (const field of ["requestSha256", "scheduleSha256", "workSha256", "structureSha256"]) {
    if (digest(response[field], field) !== digest(expected[field], `expected ${field}`)) {
      throw new Error(`critical-nucleus geometry ${field} mismatch`);
    }
  }
  const dimension = Number(response.intrinsicDimension);
  if (dimension !== Number(expected.intrinsicDimension) || ![2, 3].includes(dimension)) {
    throw new Error("critical-nucleus geometry dimension mismatch");
  }
  const temperatureKelvin = positive(response.temperatureKelvin, "temperature");
  if (Math.abs(temperatureKelvin - positive(expected.temperatureKelvin,
    "expected temperature")) > 1e-6) throw new Error("critical-nucleus temperature mismatch");
  same(expected.parentPhase, response.phases?.parent, "parent phase");
  same(expected.nucleusPhase, response.phases?.nucleus, "nucleus phase");
  if (response.geometry?.coordinateUnits !== "angstrom" || response.geometry?.periodic !== false) {
    throw new Error("nucleus geometry must be a finite nonperiodic Cartesian angstrom cluster");
  }
  const orientationDistribution = requiredText(response.geometry?.orientationDistribution,
    "orientation distribution");
  const requiredDistribution = dimension === 3 ? "isotropic-proper-rotation" : "uniform-in-plane";
  if (orientationDistribution !== requiredDistribution) {
    throw new Error(`orientation distribution must be '${requiredDistribution}'`);
  }
  const rawSites = response.geometry?.sites;
  if (!Array.isArray(rawSites) || rawSites.length < 2 || rawSites.length > 4096) {
    throw new RangeError("critical-nucleus geometry must contain 2 to 4096 sites");
  }
  const ids = new Set();
  const sites = rawSites.map((site, index) => {
    const siteId = requiredText(site.siteId, `site ${index} ID`);
    if (ids.has(siteId)) throw new Error(`duplicate critical-nucleus site ID '${siteId}'`);
    ids.add(siteId);
    const species = requiredText(site.species, `site ${siteId} species`);
    const position = site.positionAngstrom;
    if (!Array.isArray(position) || position.length !== 3) {
      throw new TypeError(`site ${siteId} position must have three Cartesian components`);
    }
    const positionAngstrom = position.map((value, axis) => finite(value,
      `site ${siteId} coordinate ${axis}`));
    if (dimension === 2 && Math.abs(positionAngstrom[2]) > 1e-6) {
      throw new Error("2D critical-nucleus sites must be planar in their supplied local frame");
    }
    const membershipProbability = probability(site.membershipProbability,
      `site ${siteId} membership probability`);
    if (membershipProbability < .5) {
      throw new Error(`site ${siteId} is not majority-assigned to the supplied nucleus`);
    }
    const region = requiredText(site.region, `site ${siteId} region`);
    if (!["core", "interface"].includes(region)) {
      throw new Error(`site ${siteId} region must be 'core' or 'interface'`);
    }
    return { siteId, species, positionAngstrom, membershipProbability, region };
  });
  const centroidAngstrom = [0, 1, 2].map(axis =>
    sites.reduce((sum, site) => sum + site.positionAngstrom[axis], 0) / sites.length);
  const centeredSites = sites.map(site => ({ ...site,
    positionAngstrom: site.positionAngstrom.map((value, axis) => value - centroidAngstrom[axis]) }));
  let minimumPairDistanceAngstrom = Infinity;
  for (let i = 0; i < centeredSites.length; i += 1) {
    for (let j = i + 1; j < centeredSites.length; j += 1) {
      const distance = Math.hypot(...centeredSites[i].positionAngstrom.map((value, axis) =>
        value - centeredSites[j].positionAngstrom[axis]));
      if (distance < minimumPairDistanceAngstrom) minimumPairDistanceAngstrom = distance;
    }
  }
  if (!(minimumPairDistanceAngstrom >= .2)) {
    throw new Error("critical-nucleus geometry contains coincident or implausibly close sites");
  }
  const boundingRadiusAngstrom = Math.max(...centeredSites.map(site =>
    Math.hypot(...site.positionAngstrom)));
  const criticality = response.criticality || {};
  const meanCommittor = probability(criticality.meanCommittor, "mean committor");
  const committorStandardError = positive(criticality.committorStandardError,
    "committor standard error");
  if (committorStandardError > .2
      || meanCommittor - committorStandardError > .5
      || meanCommittor + committorStandardError < .5) {
    throw new Error("committor uncertainty interval must contain 0.5 and its standard error must not exceed 0.2");
  }
  const independentShootingTrajectories = Number(criticality.independentShootingTrajectories);
  if (!Number.isInteger(independentShootingTrajectories)
      || independentShootingTrajectories < 20) {
    throw new Error("at least 20 independent shooting trajectories are required");
  }
  const validation = response.validation || {};
  for (const field of ["passed", "converged", "uncertaintiesReported", "criticalityValidated",
    "speciesAndUnitsValidated", "representativeGeometryDeclared"]) {
    if (validation[field] !== true) throw new Error(`validation.${field} must be true`);
  }
  const settingsSha256 = digest(response.method?.settingsSha256, "method settings SHA-256");
  const speciesCounts = {};
  for (const site of centeredSites) speciesCounts[site.species] = (speciesCounts[site.species] || 0) + 1;
  return {
    schema: "gcts-critical-nucleus-geometry-evidence-v1",
    requestSha256: digest(response.requestSha256, "request SHA-256"),
    scheduleSha256: digest(response.scheduleSha256, "schedule SHA-256"),
    workSha256: digest(response.workSha256, "work SHA-256"),
    structureSha256: digest(response.structureSha256, "structure SHA-256"),
    intrinsicDimension: dimension,
    temperatureKelvin,
    parentPhase: response.phases.parent,
    nucleusPhase: response.phases.nucleus,
    orientationDistribution,
    sites: centeredSites,
    atomCount: centeredSites.length,
    speciesCounts,
    suppliedCentroidAngstrom: centroidAngstrom,
    minimumPairDistanceAngstrom,
    boundingRadiusAngstrom,
    criticality: {
      reactionCoordinateName: requiredText(criticality.reactionCoordinateName,
        "reaction-coordinate name"),
      meanCommittor,
      committorStandardError,
      independentShootingTrajectories,
      representativeSelection: requiredText(criticality.representativeSelection,
        "representative selection"),
    },
    method: {
      family: requiredText(response.method?.family, "method family"),
      program: requiredText(response.method?.program, "method program"),
      version: response.method?.version == null ? null : String(response.method.version),
      settingsSha256,
      classifier: requiredText(response.method?.classifier, "structural classifier"),
    },
    atomisticPrototypeSupplied: true,
    representativeNotEnsemble: true,
    targetUsed: false,
    gctsCandidatesChanged: false,
    gctsSeedChanged: false,
    gctsClockChanged: false,
  };
}

function sampledPose2(random) {
  const angle = 2 * Math.PI * random();
  const cosine = Math.cos(angle);
  const sine = Math.sin(angle);
  return { kind: "uniform-in-plane", angleRadian: angle,
    matrix: [[cosine, -sine, 0], [sine, cosine, 0], [0, 0, 1]] };
}

function quaternionMatrix(random) {
  const u1 = random();
  const u2 = random();
  const u3 = random();
  const q = [Math.sqrt(1 - u1) * Math.sin(2 * Math.PI * u2),
    Math.sqrt(1 - u1) * Math.cos(2 * Math.PI * u2),
    Math.sqrt(u1) * Math.sin(2 * Math.PI * u3),
    Math.sqrt(u1) * Math.cos(2 * Math.PI * u3)];
  const [x, y, z, w] = q;
  return { quaternionXyzw: q, matrix: [
    [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
    [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
    [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
  ] };
}

function sampledPose3(random) {
  const { quaternionXyzw, matrix } = quaternionMatrix(random);
  return { kind: "isotropic-proper-rotation", quaternionXyzw, matrix };
}

function applyPose(position, pose) {
  return pose.matrix.map(row => row.reduce((sum, value, axis) =>
    sum + value * position[axis], 0));
}

export function embedCriticalNucleusAtScheduledEvents(schedule, geometry, options = {}) {
  const dimension = requireSchedule(schedule);
  if (geometry?.schema !== "gcts-critical-nucleus-geometry-evidence-v1"
      || geometry?.targetUsed || geometry?.gctsSeedChanged) {
    throw new Error("validated target-blind critical-nucleus geometry evidence is required");
  }
  if (Number(geometry.intrinsicDimension) !== dimension
      || geometry.structureSha256 !== schedule.structureSha256
      || geometry.workSha256 !== schedule.workSha256
      || geometry.scheduleSha256 !== digest(options.scheduleSha256, "schedule SHA-256")) {
    throw new Error("critical-nucleus geometry is not bound to this schedule and structure");
  }
  const orientationSeed = Number(options.orientationSeed ?? 414);
  if (!Number.isInteger(orientationSeed) || orientationSeed < 0 || orientationSeed > 0xffff_ffff) {
    throw new RangeError("orientation seed must be a 32-bit unsigned integer");
  }
  const maximumEmbeddedEvents = Number(options.maximumEmbeddedEvents ?? 8);
  if (!Number.isInteger(maximumEmbeddedEvents) || maximumEmbeddedEvents < 1
      || maximumEmbeddedEvents > 128) throw new RangeError("embedded-event cap must be 1 to 128");
  const events = schedule.events.slice(0, maximumEmbeddedEvents).map((event, eventIndex) => {
    const random = mulberry32((orientationSeed ^ Math.imul(eventIndex + 1, 0x9e3779b1)) >>> 0);
    const pose = dimension === 3 ? sampledPose3(random) : sampledPose2(random);
    const sites = geometry.sites.map(site => {
      const rotated = applyPose(site.positionAngstrom, pose);
      const positionMetre = [0, 1, 2].map(axis =>
        (event.positionMetre[axis] ?? 0) + rotated[axis] * ANGSTROM_METRE);
      const normalizedPosition = positionMetre.map(value =>
        value / schedule.characteristicLengthMetre);
      const insideObservation = normalizedPosition.slice(0, dimension)
        .every(value => value >= 0 && value <= 1);
      return { ...site, localRotatedPositionAngstrom: rotated,
        positionMetre, normalizedPosition, insideObservation };
    });
    const outsideSiteCount = sites.filter(site => !site.insideObservation).length;
    return {
      eventId: event.eventId,
      eventTimeSeconds: event.eventTimeSeconds,
      eventPositionMetre: [...event.positionMetre],
      eventNormalizedPosition: [...event.normalizedPosition],
      pose,
      sites,
      atomCount: sites.length,
      outsideSiteCount,
      fullyInsideObservation: outsideSiteCount === 0,
      atomisticPrototypeSupplied: true,
      crystallographicPoseSampled: true,
      committedToGrowth: false,
      gctsSeedChanged: false,
      targetUsed: false,
    };
  });
  return {
    schema: "gcts-scheduled-critical-nucleus-preview-v1",
    scheduleSha256: geometry.scheduleSha256,
    geometryRequestSha256: geometry.requestSha256,
    structureSha256: geometry.structureSha256,
    intrinsicDimension: dimension,
    orientationDistribution: geometry.orientationDistribution,
    randomGenerator: "mulberry32",
    orientationSeed,
    maximumEmbeddedEvents,
    scheduledEventCount: schedule.events.length,
    embeddedEventCount: events.length,
    omittedEventCount: Math.max(0, schedule.events.length - events.length),
    events,
    totalEmbeddedSites: events.reduce((sum, event) => sum + event.sites.length, 0),
    fullyInsideEventCount: events.filter(event => event.fullyInsideObservation).length,
    atomisticNucleusPrototypeSupplied: true,
    atomisticNucleusEnsembleSampled: false,
    crystallographicPosesSampled: true,
    heterogeneousSitePreferenceInferred: false,
    parentMatrixAtomsConstructed: false,
    nucleiCommittedToGrowth: false,
    gctsSeedChanged: false,
    gctsClockChanged: false,
    candidateSetChanged: false,
    targetUsed: false,
    claimBoundary: "Externally supplied representative critical geometry is rigidly posed for preview only; it is not an admitted GCTS seed, a sampled critical ensemble, or a growth trajectory.",
  };
}
