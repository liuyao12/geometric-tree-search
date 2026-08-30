export const EXTERNAL_PHYSICS_REQUEST_TEMPLATES = Object.freeze({
  trajectory: Object.freeze({
    quantity: "time-resolved atomic trajectory",
    suitableMethods: Object.freeze(["molecular dynamics", "time-resolved scattering or microscopy"]),
    requiredOutputs: Object.freeze(["ordered Cartesian coordinates", "physical time per frame", "cell and boundary conditions", "species identity and atom correspondence"]),
    units: Object.freeze({ coordinates: "angstrom", time: "seconds or a declared physical submultiple" }),
    validation: "hold out at least one contiguous time interval; report coordinate and local-environment error without reordering frames",
  }),
  clock: Object.freeze({
    quantity: "calibrated growth clock or event rate",
    suitableMethods: Object.freeze(["kinetic Monte Carlo", "calibrated molecular dynamics", "time-resolved growth experiment"]),
    requiredOutputs: Object.freeze(["event exposure time", "accepted and censored event counts", "attempt frequency or transport coefficient", "temperature and driving conditions"]),
    units: Object.freeze({ time: "seconds", rate: "events per second", temperature: "kelvin" }),
    validation: "calibrate on independent time windows or specimens and report censoring; GCTS search steps are never used as clock labels",
  }),
  barrier: Object.freeze({
    quantity: "transition or migration barrier",
    suitableMethods: Object.freeze(["nudged elastic band", "dimer or saddle search", "enhanced-sampling free-energy path"]),
    requiredOutputs: Object.freeze(["explicit initial and final states", "intermediate images", "energy per image", "force convergence and electronic-structure provenance"]),
    units: Object.freeze({ coordinates: "angstrom", energy: "electronvolt", force: "electronvolt per angstrom" }),
    validation: "validate the path independently; a collision-free geometric route is candidate initialization, never a barrier estimate",
  }),
  "free-energy": Object.freeze({
    quantity: "free-energy difference or direction",
    suitableMethods: Object.freeze(["thermodynamic integration", "umbrella sampling", "phonon or configurational free-energy calculation"]),
    requiredOutputs: Object.freeze(["state definition and collective variables", "temperature, pressure, and ensemble", "energy and entropy contributions", "uncertainty and convergence diagnostics"]),
    units: Object.freeze({ energy: "electronvolt or joule per declared amount", temperature: "kelvin", pressure: "pascal" }),
    validation: "compare independently sampled states at matched composition and thermodynamic conditions; geometric rank scores remain excluded",
  }),
  probability: Object.freeze({
    quantity: "path probability or branching rate",
    suitableMethods: Object.freeze(["transition-path sampling", "Markov-state modeling", "kinetic Monte Carlo", "repeated time-resolved experiment"]),
    requiredOutputs: Object.freeze(["transition counts with exposure", "state and event definitions", "lag time or rate model", "independent validation trajectories"]),
    units: Object.freeze({ probability: "dimensionless", rate: "events per second", time: "seconds" }),
    validation: "group by independent trajectory or specimen; frozen GCTS branch multiplicity is a feature, not a probability label",
  }),
  forces: Object.freeze({
    quantity: "forces, stress, and heat-flow response",
    suitableMethods: Object.freeze(["density-functional theory", "validated machine-learned potential", "force-labelled molecular dynamics"]),
    requiredOutputs: Object.freeze(["per-site Cartesian forces", "total energy with method provenance", "stress tensor when periodic", "units and convergence settings"]),
    units: Object.freeze({ coordinates: "angstrom", force: "electronvolt per angstrom", energy: "electronvolt", stress: "gigapascal" }),
    validation: "freeze the model before a composition- and method-compatible held-out archive; abstain outside training feature support",
  }),
});

function finiteVector(vector, label) {
  if (!Array.isArray(vector) || vector.length !== 3 || !vector.every(Number.isFinite)) {
    throw new TypeError(`${label} must be a finite Cartesian three-vector`);
  }
  return vector.map(Number);
}

function normalizeConfiguration(configuration, label) {
  if (!configuration || !Array.isArray(configuration.atoms) || !configuration.atoms.length) {
    throw new TypeError(`${label} needs at least one atom`);
  }
  const atoms = configuration.atoms.map((atom, index) => {
    if (!atom || typeof atom.species !== "string" || !atom.species.trim()) {
      throw new TypeError(`${label} atom ${index} needs a species token`);
    }
    return {
      siteId: String(atom.siteId ?? index),
      sourceIndex: Number.isInteger(atom.sourceIndex) ? atom.sourceIndex : null,
      species: atom.species,
      occupancy: Number.isFinite(atom.occupancy) ? atom.occupancy : 1,
      positionAngstrom: finiteVector(atom.positionAngstrom, `${label} atom ${index}`),
      formalCharge: Number.isFinite(atom.formalCharge) ? atom.formalCharge : null,
      scalarSpin: Number.isFinite(atom.scalarSpin) ? atom.scalarSpin : null,
    };
  });
  const cell = configuration.cellVectorsAngstrom === null ? null
    : configuration.cellVectorsAngstrom.map((vector, index) =>
      finiteVector(vector, `${label} cell vector ${index}`));
  if (cell !== null && cell.length !== 3) throw new TypeError(`${label} cell must have three vectors`);
  const periodicBoundary = Array.isArray(configuration.periodicBoundary)
    && configuration.periodicBoundary.length === 3
    ? configuration.periodicBoundary.map(Boolean) : [false, false, false];
  return {
    role: String(configuration.role || label),
    coordinateUnits: "angstrom",
    atomCount: atoms.length,
    structureSha256: configuration.structureSha256 || null,
    cellVectorsAngstrom: cell,
    periodicBoundary,
    atoms,
  };
}

export function buildExternalPhysicsRequest(input) {
  const template = EXTERNAL_PHYSICS_REQUEST_TEMPLATES[input?.quantityId];
  if (!template) throw new RangeError(`unsupported external-physics quantity: ${input?.quantityId}`);
  if (!input.handoff || input.handoff.quantityId !== input.quantityId) {
    throw new Error("external-physics request needs the matching frozen evidence handoff");
  }
  if (input.handoff.targetUsed === true || input.targetCoordinatesEmbedded === true) {
    throw new Error("external-physics request cannot contain a hidden growth target");
  }
  const observation = normalizeConfiguration(input.observation, "observation");
  const growthSeed = normalizeConfiguration(input.growthSeed, "growth seed");
  const records = Array.isArray(input.manifestRecords) ? input.manifestRecords.map((record) => ({
    id: String(record.id), process: String(record.process), status: String(record.status),
    role: String(record.role), evidence: String(record.evidence), boundary: String(record.boundary),
  })) : [];
  return {
    schema: "gcts-external-physics-request-v1",
    generatedAt: String(input.generatedAt),
    application: { name: "Materials Growth Lab", buildId: String(input.buildId) },
    specimen: {
      scenarioId: String(input.scenarioId),
      materialName: String(input.materialName),
      elements: [...new Set(input.elements.map(String))].sort(),
      sourceProvenance: input.sourceProvenance || null,
      recordedConditions: input.recordedConditions || null,
    },
    request: {
      quantityId: input.quantityId,
      quantityLabel: input.quantityLabel || template.quantity,
      requestMode: input.handoff.mode,
      inferenceResolved: false,
      suitableMethods: [...template.suitableMethods],
      requiredOutputs: [...template.requiredOutputs],
      units: { ...template.units },
      validationProtocol: template.validation,
      earliestPermittedUse: String(input.earliestPermittedUse),
      selectedManifestRecordIds: [...input.handoff.selectedRecordIds],
      requestedManifestRecordIds: [...input.handoff.requestedRecordIds],
      relatedGeometryRecords: records,
    },
    configurations: { observation, growthSeed },
    safeguards: {
      requestOnly: true,
      submittedToExternalService: false,
      targetCoordinatesEmbedded: false,
      targetUsedForSelection: false,
      geometricScoresUsedAsEnergyLabels: false,
      searchStepsUsedAsPhysicalTime: false,
      physicalInferenceRemainsOpen: true,
    },
  };
}
