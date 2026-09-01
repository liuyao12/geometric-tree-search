import { validateCandidateActionPathGeometry }
  from "./action-path-geometry.mjs?v=20260831-408";

export const ACTION_BARRIER_REQUEST_SCHEMA = "gcts-frozen-frontier-action-barrier-request-v4";
export const ACTION_BARRIER_RESPONSE_SCHEMA = "gcts-frozen-frontier-action-barrier-response-v4";

const finite = (value) => Number.isFinite(Number(value));

function requiredText(value, label) {
  if (typeof value !== "string" || !value.trim()) throw new TypeError(`${label} is required`);
  return value.trim();
}

function requiredSha(value, label) {
  const normalized = requiredText(value, label).toLowerCase();
  if (!/^[a-f0-9]{64}$/.test(normalized)) throw new TypeError(`${label} must contain 64 hexadecimal characters`);
  return normalized;
}

function finiteVector(value, label) {
  if (!Array.isArray(value) || value.length !== 3 || !value.every(finite)) {
    throw new TypeError(`${label} must be a finite Cartesian three-vector`);
  }
  return value.map(Number);
}

function normalizedSite(site, label) {
  return {
    species: requiredText(site?.species, `${label} species`),
    positionAngstrom: finiteVector(site?.positionAngstrom, `${label} position`),
  };
}

function speciesCounts(sites) {
  const result = {};
  (Array.isArray(sites) ? sites : []).forEach((site) => {
    result[site.species] = (result[site.species] || 0) + 1;
  });
  return result;
}

function sameSpeciesCounts(firstSites, secondSites) {
  const first = speciesCounts(firstSites);
  const second = speciesCounts(secondSites);
  const species = [...new Set([...Object.keys(first), ...Object.keys(second)])];
  return species.every((name) => (first[name] || 0) === (second[name] || 0));
}

function candidateSpeciesDelta(candidate) {
  const emitted = speciesCounts(candidate.emittedSites);
  const removed = speciesCounts(candidate.removedSites);
  return Object.fromEntries([...new Set([...Object.keys(emitted), ...Object.keys(removed)])]
    .sort().map((species) => [species, (emitted[species] || 0) - (removed[species] || 0)])
    .filter(([, delta]) => delta !== 0));
}

function canonicalValue(value) {
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (value && typeof value === "object") return Object.fromEntries(Object.keys(value).sort()
    .map((key) => [key, canonicalValue(value[key])]));
  return value;
}

export function canonicalActionBarrierJson(value) {
  return JSON.stringify(canonicalValue(value));
}

export async function actionBarrierSha256(value) {
  const bytes = new TextEncoder().encode(typeof value === "string" ? value : canonicalActionBarrierJson(value));
  const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function normalizeConfiguration(configuration) {
  if (!configuration || !Array.isArray(configuration.atoms) || !configuration.atoms.length) {
    throw new TypeError("the frozen frontier needs a nonempty initial configuration");
  }
  const cell = configuration.cellVectorsAngstrom == null ? null
    : configuration.cellVectorsAngstrom.map((vector, index) => finiteVector(vector, `cell vector ${index + 1}`));
  if (cell && cell.length !== 3) throw new TypeError("cellVectorsAngstrom must contain three vectors");
  return {
    structureSha256: requiredText(configuration.structureSha256, "initial configuration SHA-256"),
    coordinateUnits: "angstrom",
    atomCount: configuration.atoms.length,
    periodicBoundary: Array.isArray(configuration.periodicBoundary) && configuration.periodicBoundary.length === 3
      ? configuration.periodicBoundary.map(Boolean) : [false, false, false],
    cellVectorsAngstrom: cell,
    atoms: configuration.atoms.map((site, index) => ({
      siteId: String(site.siteId ?? index),
      ...normalizedSite(site, `initial site ${index + 1}`),
    })),
  };
}

function normalizeCandidate(candidate, index) {
  const candidateId = requiredText(candidate?.candidateId, `candidate ${index + 1} id`);
  const eventDirection = candidate.eventDirection == null ? "attach"
    : requiredText(candidate.eventDirection, `candidate ${candidateId} event direction`);
  if (!["attach", "detach", "hop", "exchange"].includes(eventDirection)) {
    throw new Error(`candidate ${candidateId} eventDirection must be attach, detach, hop, or exchange`);
  }
  const emittedSites = Array.isArray(candidate.emittedSites)
    ? candidate.emittedSites.map((site, siteIndex) => normalizedSite(site,
      `candidate ${index + 1} emitted site ${siteIndex + 1}`)) : [];
  const removedSites = Array.isArray(candidate.removedSites)
    ? candidate.removedSites.map((site, siteIndex) => normalizedSite(site,
      `candidate ${index + 1} removed site ${siteIndex + 1}`)) : [];
  const actionSites = Array.isArray(candidate.actionSites)
    ? candidate.actionSites.map((site, siteIndex) => normalizedSite(site,
      `candidate ${index + 1} action site ${siteIndex + 1}`)) : [];
  const hopConservesSpecies = eventDirection !== "hop"
    || sameSpeciesCounts(emittedSites, removedSites);
  const exchangeChangesSpecies = eventDirection !== "exchange"
    || !sameSpeciesCounts(emittedSites, removedSites);
  if (!actionSites.length || (eventDirection === "attach" && (!emittedSites.length || removedSites.length))
      || (eventDirection === "detach" && (!removedSites.length || emittedSites.length))
      || (eventDirection === "hop" && (!removedSites.length || !emittedSites.length
        || !hopConservesSpecies))
      || (eventDirection === "exchange" && (!removedSites.length || !emittedSites.length
        || removedSites.length !== emittedSites.length || !exchangeChangesSpecies))) {
    throw new Error(`candidate ${candidateId} needs exact nonempty action geometry and ${eventDirection === "hop" ? "equal colored emitted/removed populations" : eventDirection === "exchange" ? "equal-count but differently colored emitted/removed populations" : `one nonempty ${eventDirection === "attach" ? "emittedSites" : "removedSites"} set with the opposite set empty`}`);
  }
  return {
    candidateId,
    candidateDigestSha256: requiredText(candidate.candidateDigestSha256,
      `candidate ${candidateId} digest`),
    actionLabel: requiredText(candidate.actionLabel, `candidate ${candidateId} label`),
    eventDirection,
    parentType: String(candidate.parentType),
    childType: String(candidate.childType),
    ruleId: String(candidate.ruleId),
    emittedAtomCount: emittedSites.length,
    removedAtomCount: removedSites.length,
    actionAtomCount: actionSites.length,
    emittedSites,
    removedSites,
    actionSites,
    finalStateConstruction: eventDirection === "attach"
      ? "initial configuration union emittedSites; exact same-species coincidences are shared sites"
      : eventDirection === "detach"
        ? "initial configuration minus removedSites; retained shared support remains unchanged"
        : eventDirection === "hop"
          ? "initial configuration minus removedSites then union emittedSites; atom count and colored population remain unchanged"
          : "initial configuration minus removedSites then union emittedSites; atom count remains unchanged and the exact colored population delta is exchanged with the declared reservoir",
  };
}

function stateSiteKey(site) {
  return `${site.species}\u0000${site.positionAngstrom.map((value) => Number(value).toPrecision(15)).join(",")}`;
}

function sortedStateSites(sites) {
  return sites.map((site) => ({ species: site.species, positionAngstrom: [...site.positionAngstrom] }))
    .sort((first, second) => stateSiteKey(first).localeCompare(stateSiteKey(second)));
}

export async function frozenActionStateGeometrySha256(sites) {
  const normalized = (Array.isArray(sites) ? sites : []).map((site, index) =>
    normalizedSite(site, `state site ${index + 1}`));
  return actionBarrierSha256({ coordinateUnits: "angstrom", atoms: sortedStateSites(normalized) });
}

async function bindCandidateStateGeometry(candidate, initialConfiguration) {
  const initialSites = initialConfiguration.atoms.map(({ species, positionAngstrom }) =>
    ({ species, positionAngstrom }));
  const counts = new Map();
  initialSites.forEach((site) => counts.set(stateSiteKey(site), (counts.get(stateSiteKey(site)) || 0) + 1));
  let finalSites = [...initialSites];
  if (["detach", "hop", "exchange"].includes(candidate.eventDirection)) {
    candidate.removedSites.forEach((site) => {
      const key = stateSiteKey(site);
      const count = counts.get(key) || 0;
      if (!count) throw new Error(`${candidate.eventDirection} candidate ${candidate.candidateId} removes a site absent from the initial configuration`);
      counts.set(key, count - 1);
      const index = finalSites.findIndex((entry) => stateSiteKey(entry) === key);
      finalSites.splice(index, 1);
    });
  }
  if (["attach", "hop", "exchange"].includes(candidate.eventDirection)) {
    candidate.emittedSites.forEach((site) => {
      const key = stateSiteKey(site);
      if ((counts.get(key) || 0) === 0) {
        finalSites.push(site);
        counts.set(key, 1);
      }
    });
  }
  const initialGeometrySha256 = await frozenActionStateGeometrySha256(initialSites);
  const finalGeometrySha256 = await frozenActionStateGeometrySha256(finalSites);
  const canonicalCandidateDigest = await actionBarrierSha256({
    candidateId: candidate.candidateId, eventDirection: candidate.eventDirection,
    emittedSites: candidate.emittedSites, removedSites: candidate.removedSites,
    actionSites: candidate.actionSites,
  });
  if (candidate.candidateDigestSha256 !== canonicalCandidateDigest) {
    throw new Error(`candidate ${candidate.candidateId} digest does not match its exact direction and geometry`);
  }
  return { ...candidate, initialGeometrySha256, finalGeometrySha256,
    initialAtomCount: initialSites.length, finalAtomCount: finalSites.length };
}

export async function buildFrozenActionBarrierRequest(input) {
  if (input?.targetUsed === true || input?.candidateSetTargetUsed === true) {
    throw new Error("a frozen action-barrier request cannot use a growth target");
  }
  if (!Array.isArray(input?.candidates) || !input.candidates.length) {
    throw new Error("a frozen action-barrier request needs at least one hard-admitted candidate");
  }
  const initialConfiguration = normalizeConfiguration(input.initialConfiguration);
  const couplingStateExpectation = input.couplingStateExpectation == null ? null : {
    couplingStateSha256: requiredSha(input.couplingStateExpectation.couplingStateSha256,
      "expected coupling-state SHA-256"),
    temperatureKelvin: input.couplingStateExpectation.temperatureKelvin == null ? null
      : Number(input.couplingStateExpectation.temperatureKelvin),
    sourceEvidence: Array.isArray(input.couplingStateExpectation.sourceEvidence)
      ? [...new Set(input.couplingStateExpectation.sourceEvidence.map(String))].sort() : [],
  };
  if (couplingStateExpectation?.temperatureKelvin != null
      && (!Number.isFinite(couplingStateExpectation.temperatureKelvin)
        || couplingStateExpectation.temperatureKelvin <= 0)) {
    throw new TypeError("expected coupling-state temperature must be positive Kelvin");
  }
  const normalizedCandidates = input.candidates.map(normalizeCandidate);
  const candidates = (await Promise.all(normalizedCandidates.map((candidate) =>
    bindCandidateStateGeometry(candidate, initialConfiguration))))
    .sort((first, second) => first.candidateId.localeCompare(second.candidateId));
  if (new Set(candidates.map((candidate) => candidate.candidateId)).size !== candidates.length) {
    throw new Error("frozen frontier candidate IDs must be unique");
  }
  const candidateBatchSha256 = await actionBarrierSha256(candidates.map((candidate) => ({
    candidateId: candidate.candidateId,
    candidateDigestSha256: candidate.candidateDigestSha256,
    eventDirection: candidate.eventDirection,
    emittedSites: candidate.emittedSites,
    removedSites: candidate.removedSites,
    actionSites: candidate.actionSites,
  })));
  return {
    schema: ACTION_BARRIER_REQUEST_SCHEMA,
    generatedAt: String(input.generatedAt),
    application: { name: "Materials Growth Lab", buildId: String(input.buildId) },
    specimen: {
      scenarioId: String(input.scenarioId),
      materialName: String(input.materialName),
      elements: [...new Set((input.elements || []).map(String))].sort(),
      sourceProvenance: input.sourceProvenance || null,
    },
    couplingStateExpectation,
    frontier: {
      candidateBatchSha256,
      candidateCount: candidates.length,
      initialConfiguration,
      candidates,
      candidateSetFrozenBeforeRequest: true,
      candidateGeometryFrozenBeforeRequest: true,
      hardAdmissionFrozenBeforeRequest: true,
    },
    calculation: {
      quantity: "candidate-resolved attachment, exact leaf-detachment, mass-conserving surface-hop, and/or equal-count reservoir-mediated species-exchange transition barriers on one frozen frontier",
      suitableMethods: ["nudged elastic band", "dimer or saddle search", "validated enhanced-sampling path"],
      requiredOutputs: ["one converged record for every candidate ID", "the supplied exact initial and final geometry digests",
        "invariant material sites certified once plus at least three coordinate-bearing moving/reservoir images with stable path-site IDs and species",
        "strictly increasing reaction coordinates, image energies, image maximum forces, and an internal saddle image",
        "maximum residual force", "barrier uncertainty and method provenance"],
      mechanismPathContract: {
        surfaceHop: "closed-system-fixed-composition images; every path site remains in the material domain",
        attachmentAndDetachment: "explicit-reservoir-extended-system images; material plus reservoir cardinality and species identities remain constant",
        speciesExchange: "explicit-reservoir-extended-system images containing both incoming and outgoing colored sites",
        endpointRule: "material-domain sites in image 0 and the final image must exactly reproduce the frozen colored endpoint multisets",
      },
      optionalMicroscopicInverseOutputs: ["energyDeltaElectronVolt between the exact final and initial states",
        "energyDeltaUncertaintyElectronVolt from the same method-specific calculation"],
      optionalReservoirThermodynamics: {
        model: "grand-canonical-state-free-energy",
        ensemble: "grand-canonical-T-V-mu",
        systemFreeEnergyKind: "Helmholtz",
        requiredRootFields: ["temperatureKelvin", "freeEnergyMethod", "freeEnergySettingsSha256",
          "chemicalPotentialReference", "chemicalPotentialSettingsSha256", "evidenceSha256",
          "chemicalPotentials with one value + uncertainty per transferred species",
          "uncertaintyAssumption=independent-one-sigma", "volumeHeldFixedAcrossPath=true"],
        requiredCandidateFields: ["systemFreeEnergyDeltaElectronVolt",
          "systemFreeEnergyDeltaUncertaintyElectronVolt", "stateFreeEnergyConverged=true"],
        scope: "optional evidence for a later exact inverse-pair local-balance audit only",
      },
      optionalKineticOutputs: ["one positive converged attemptFrequencyPerSecond for every candidate ID",
        "attemptFrequencyUncertaintyLog10", "prefactor method and settings SHA-256",
        "explicit requested-frontier-only catalog scope and recrossing declaration",
        "optional temperatureApplicability declaration; no range sweep is authorized when absent"],
      optionalKineticResponseContract: {
        rootKinetics: { model: "harmonic-transition-state-theory", prefactorMethod: "method name",
          prefactorSettingsSha256: "64 hexadecimal characters",
          couplingStateSha256: couplingStateExpectation?.couplingStateSha256
            || "optional shared external-physics state digest",
          temperatureKelvin: couplingStateExpectation?.temperatureKelvin
            || "positive Kelvin when a shared state declares temperature",
          temperatureApplicability: {
            scope: "single-temperature | bounded-constant-htst",
            minimumKelvin: "1..5000 K; required for bounded-constant-htst",
            maximumKelvin: "1..5000 K; required for bounded-constant-htst",
            externallyAuthorized: "true only when the external method authorizes the interval",
            barrierAndPrefactorAssumedConstant: "true only for an explicit bounded constant-HTST sweep",
          },
          recrossingCorrection: "included | not-included",
          catalogScope: "requested-hard-admitted-actions-only" },
        validationFlags: ["prefactorsReported", "everyPrefactorConverged",
          "prefactorUncertaintyReported"],
        everyCandidateRecord: { attemptFrequencyPerSecond: "finite positive s^-1",
          attemptFrequencyUncertaintyLog10: "finite nonnegative decades",
          prefactorConverged: true },
      },
      units: { coordinates: "angstrom", energy: "electronvolt", force: "electronvolt per angstrom" },
      responseSchema: ACTION_BARRIER_RESPONSE_SCHEMA,
    },
    safeguards: {
      requestOnly: true,
      targetCoordinatesEmbedded: false,
      geometricScoresUsedAsEnergyLabels: false,
      searchStepsUsedAsPhysicalTime: false,
      candidateSetMayChangeAfterResponse: false,
      hardAdmissionMayChangeAfterResponse: false,
      responseScope: "ranking this exact candidate batch only",
      reversibleGeometryDoesNotImplyDetailedBalance: true,
      massConservingHopDoesNotSupplyMigrationPathOrBarrier: true,
      speciesExchangeRequiresExternalReservoirChemicalWork: true,
      speciesExchangeDoesNotSupplyReactionPathOrBarrier: true,
      returnedPathCoordinatesMustBeExternallyCalculated: true,
      pathGeometryMayNotCreateOrAlterCandidateEndpoints: true,
      optionalThermodynamicEvidenceMustBeExternal: true,
      geometricScoresMayNotSupplyChemicalPotentialOrFreeEnergy: true,
      oneInversePairMayNotClaimGlobalDetailedBalance: true,
    },
  };
}

export async function frozenActionBarrierRequestReceipt(request) {
  if (request?.schema !== ACTION_BARRIER_REQUEST_SCHEMA) throw new Error("invalid action-barrier request schema");
  return {
    requestSha256: await actionBarrierSha256(request),
    candidateBatchSha256: request.frontier.candidateBatchSha256,
    initialStructureSha256: request.frontier.initialConfiguration.structureSha256,
    candidateCount: request.frontier.candidates.length,
    couplingStateExpectation: request.couplingStateExpectation || null,
  };
}

function median(values) {
  const sorted = [...values].sort((first, second) => first - second);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

function robustBarrierScores(records) {
  const barriers = records.map((record) => record.barrierElectronVolt);
  const center = median(barriers);
  const mad = median(barriers.map((value) => Math.abs(value - center)));
  const range = Math.max(...barriers) - Math.min(...barriers);
  const scale = Math.max(1.4826 * mad, range / 4, 1e-9);
  return {
    centerElectronVolt: center,
    scaleElectronVolt: scale,
    records: records.map((record) => ({ ...record,
      lowerBarrierScore: Math.tanh((center - record.barrierElectronVolt) / (2 * scale)) })),
  };
}

export function validateFrozenActionBarrierResponse(response, expected) {
  if (response?.schema !== ACTION_BARRIER_RESPONSE_SCHEMA) {
    throw new Error(`response schema must be ${ACTION_BARRIER_RESPONSE_SCHEMA}`);
  }
  if (!expected || typeof expected !== "object") throw new TypeError("expected request receipt is required");
  if (!expected.initialConfiguration?.atoms?.length) {
    throw new TypeError("expected frozen initial configuration is required for path geometry validation");
  }
  if (response.requestSha256 !== expected.requestSha256
      || response.candidateBatchSha256 !== expected.candidateBatchSha256
      || response.initialStructureSha256 !== expected.initialStructureSha256) {
    throw new Error("response is not bound to this exact request, configuration, and candidate batch");
  }
  const method = response.method || {};
  const methodSummary = {
    family: requiredText(method.family, "method family"),
    program: requiredText(method.program, "method program"),
    version: method.version == null ? null : String(method.version),
    settingsSha256: requiredText(method.settingsSha256, "method settings SHA-256"),
  };
  if (!/^[a-f0-9]{64}$/i.test(methodSummary.settingsSha256)) {
    throw new Error("method settings SHA-256 must contain 64 hexadecimal characters");
  }
  const validation = response.validation || {};
  if (!(validation.passed === true && validation.protocolMatchesRequest === true
      && validation.independentHoldout === true && validation.uncertaintyReported === true
      && validation.convergenceReported === true && validation.everyCandidateConverged === true
      && validation.everyPathGeometryValidated === true)) {
    throw new Error("action-barrier response has not passed every frozen validation gate");
  }
  const kinetics = response.kinetics == null ? null : {
    model: requiredText(response.kinetics.model, "kinetic prefactor model"),
    prefactorMethod: requiredText(response.kinetics.prefactorMethod, "prefactor method"),
    prefactorSettingsSha256: requiredText(response.kinetics.prefactorSettingsSha256,
      "prefactor settings SHA-256"),
    recrossingCorrection: requiredText(response.kinetics.recrossingCorrection,
      "recrossing correction declaration"),
    catalogScope: requiredText(response.kinetics.catalogScope, "kinetic catalog scope"),
    couplingStateSha256: response.kinetics.couplingStateSha256 == null ? null
      : requiredSha(response.kinetics.couplingStateSha256, "kinetic coupling-state SHA-256"),
    temperatureKelvin: response.kinetics.temperatureKelvin == null ? null
      : Number(response.kinetics.temperatureKelvin),
    temperatureApplicability: response.kinetics.temperatureApplicability == null ? null : {
      scope: requiredText(response.kinetics.temperatureApplicability.scope,
        "kinetic temperature applicability scope"),
      minimumKelvin: response.kinetics.temperatureApplicability.minimumKelvin == null ? null
        : Number(response.kinetics.temperatureApplicability.minimumKelvin),
      maximumKelvin: response.kinetics.temperatureApplicability.maximumKelvin == null ? null
        : Number(response.kinetics.temperatureApplicability.maximumKelvin),
      externallyAuthorized: response.kinetics.temperatureApplicability.externallyAuthorized === true,
      barrierAndPrefactorAssumedConstant:
        response.kinetics.temperatureApplicability.barrierAndPrefactorAssumedConstant === true,
    },
  };
  if (kinetics) {
    if (kinetics.model !== "harmonic-transition-state-theory") {
      throw new Error("kinetic model must be harmonic-transition-state-theory");
    }
    if (!/^[a-f0-9]{64}$/i.test(kinetics.prefactorSettingsSha256)) {
      throw new Error("prefactor settings SHA-256 must contain 64 hexadecimal characters");
    }
    if (!["included", "not-included"].includes(kinetics.recrossingCorrection)) {
      throw new Error("recrossingCorrection must be included or not-included");
    }
    if (kinetics.catalogScope !== "requested-hard-admitted-actions-only") {
      throw new Error("kinetic catalog scope must remain the requested hard-admitted actions only");
    }
    if (!(validation.prefactorsReported === true && validation.everyPrefactorConverged === true
        && validation.prefactorUncertaintyReported === true)) {
      throw new Error("kinetic prefactors have not passed every frozen validation gate");
    }
    const expectedState = expected.couplingStateExpectation;
    if (expectedState && kinetics.couplingStateSha256 !== expectedState.couplingStateSha256) {
      throw new Error("kinetic response does not match the requested shared coupling state");
    }
    if (kinetics.temperatureKelvin != null
        && (!Number.isFinite(kinetics.temperatureKelvin) || kinetics.temperatureKelvin < 1
          || kinetics.temperatureKelvin > 5000)) {
      throw new Error("kinetic response temperature must be between 1 and 5000 Kelvin");
    }
    const applicability = kinetics.temperatureApplicability;
    if (applicability) {
      if (!["single-temperature", "bounded-constant-htst"].includes(applicability.scope)) {
        throw new Error("kinetic temperature applicability must be single-temperature or bounded-constant-htst");
      }
      if (applicability.scope === "single-temperature") {
        if (kinetics.temperatureKelvin == null) {
          throw new Error("single-temperature kinetic applicability needs temperatureKelvin");
        }
        if (applicability.externallyAuthorized
            || applicability.barrierAndPrefactorAssumedConstant
            || applicability.minimumKelvin != null || applicability.maximumKelvin != null) {
          throw new Error("single-temperature applicability cannot authorize a bounded sweep");
        }
      } else {
        if (!Number.isFinite(applicability.minimumKelvin)
            || !Number.isFinite(applicability.maximumKelvin)
            || applicability.minimumKelvin < 1 || applicability.maximumKelvin > 5000
            || applicability.minimumKelvin >= applicability.maximumKelvin
            || !applicability.externallyAuthorized
            || !applicability.barrierAndPrefactorAssumedConstant) {
          throw new Error("bounded constant-HTST applicability needs an authorized 1..5000 K interval and explicit constant barrier/prefactor assumption");
        }
        if (kinetics.temperatureKelvin != null
            && (kinetics.temperatureKelvin < applicability.minimumKelvin
              || kinetics.temperatureKelvin > applicability.maximumKelvin)) {
          throw new Error("kinetic response temperature lies outside its authorized interval");
        }
      }
    }
    if (expectedState?.temperatureKelvin != null
        && (kinetics.temperatureKelvin == null || Math.abs(kinetics.temperatureKelvin
          - expectedState.temperatureKelvin) > Math.max(1e-9, expectedState.temperatureKelvin * 1e-9))) {
      throw new Error("kinetic response temperature does not match the requested shared state");
    }
  }
  const thermodynamics = response.thermodynamics == null ? null : (() => {
    const source = response.thermodynamics;
    const normalized = {
      model: requiredText(source.model, "thermodynamic model"),
      ensemble: requiredText(source.ensemble, "thermodynamic ensemble"),
      systemFreeEnergyKind: requiredText(source.systemFreeEnergyKind, "system free-energy kind"),
      temperatureKelvin: finite(source.temperatureKelvin) ? Number(source.temperatureKelvin) : null,
      freeEnergyMethod: requiredText(source.freeEnergyMethod, "free-energy method"),
      freeEnergySettingsSha256: requiredText(source.freeEnergySettingsSha256,
        "free-energy settings SHA-256"),
      chemicalPotentialReference: requiredText(source.chemicalPotentialReference,
        "chemical-potential reference"),
      chemicalPotentialSettingsSha256: requiredText(source.chemicalPotentialSettingsSha256,
        "chemical-potential settings SHA-256"),
      evidenceSha256: requiredText(source.evidenceSha256, "thermodynamic evidence SHA-256"),
      uncertaintyAssumption: requiredText(source.uncertaintyAssumption,
        "thermodynamic uncertainty assumption"),
      volumeHeldFixedAcrossPath: source.volumeHeldFixedAcrossPath === true,
    };
    if (normalized.model !== "grand-canonical-state-free-energy"
        || normalized.ensemble !== "grand-canonical-T-V-mu"
        || normalized.systemFreeEnergyKind !== "Helmholtz"
        || normalized.uncertaintyAssumption !== "independent-one-sigma"
        || !normalized.volumeHeldFixedAcrossPath) {
      throw new Error("thermodynamic evidence must use the declared grand-canonical T-V-mu Helmholtz contract");
    }
    if (!Number.isFinite(normalized.temperatureKelvin)
        || normalized.temperatureKelvin < 1 || normalized.temperatureKelvin > 5000) {
      throw new RangeError("thermodynamic temperature must be between 1 and 5000 K");
    }
    ["freeEnergySettingsSha256", "chemicalPotentialSettingsSha256", "evidenceSha256"]
      .forEach((field) => {
        if (!/^[a-f0-9]{64}$/i.test(normalized[field])) {
          throw new Error(`${field} must contain 64 hexadecimal characters`);
        }
      });
    if (!Array.isArray(source.chemicalPotentials) || !source.chemicalPotentials.length) {
      throw new Error("thermodynamic evidence needs at least one chemical potential");
    }
    const seenSpecies = new Set();
    normalized.chemicalPotentials = source.chemicalPotentials.map((entry, index) => {
      const species = requiredText(entry?.species, `chemical potential ${index + 1} species`);
      if (seenSpecies.has(species)) throw new Error(`duplicate chemical potential for ${species}`);
      seenSpecies.add(species);
      if (entry.electronVolt == null || entry.uncertaintyElectronVolt == null
          || !finite(entry.electronVolt) || !finite(entry.uncertaintyElectronVolt)
          || Number(entry.uncertaintyElectronVolt) < 0) {
        throw new Error(`chemical potential for ${species} needs a finite value and nonnegative uncertainty`);
      }
      return { species, electronVolt: Number(entry.electronVolt),
        uncertaintyElectronVolt: Number(entry.uncertaintyElectronVolt) };
    }).sort((first, second) => first.species.localeCompare(second.species));
    if (!(validation.thermodynamicsReported === true
        && validation.everyStateFreeEnergyConverged === true
        && validation.chemicalPotentialUncertaintyReported === true)) {
      throw new Error("thermodynamic evidence has not passed every frozen validation gate");
    }
    if (expected.couplingStateExpectation?.temperatureKelvin != null
        && Math.abs(normalized.temperatureKelvin - expected.couplingStateExpectation.temperatureKelvin)
          > Math.max(1e-9, normalized.temperatureKelvin * 1e-9)) {
      throw new Error("thermodynamic temperature does not match the requested shared state");
    }
    return normalized;
  })();
  if (kinetics && thermodynamics
      && (kinetics.temperatureKelvin == null || Math.abs(kinetics.temperatureKelvin
        - thermodynamics.temperatureKelvin) > Math.max(1e-9,
        thermodynamics.temperatureKelvin * 1e-9))) {
    throw new Error("kinetic and grand-canonical evidence must share one declared temperature");
  }
  if (response.safeguards?.containsGrowthTargetCoordinates !== false
      || response.safeguards?.geometricScoresUsedAsPhysicalLabels !== false
      || response.safeguards?.searchStepsUsedAsPhysicalTime !== false
      || response.safeguards?.candidateSetChanged !== false
      || response.safeguards?.hardAdmissionChanged !== false
      || response.safeguards?.pathCoordinatesExternallyCalculated !== true
      || response.safeguards?.pathGeometryChangedCandidateEndpoints !== false) {
    throw new Error("action-barrier response safeguards are incomplete or target-tainted");
  }
  if (thermodynamics && !(response.safeguards.chemicalPotentialsExternallySupplied === true
      && response.safeguards.stateFreeEnergiesExternallySupplied === true
      && response.safeguards.geometricScoresUsedAsThermodynamicLabels === false
      && response.safeguards.globalDetailedBalanceClaimed === false)) {
    throw new Error("grand-canonical evidence safeguards are incomplete or geometry-derived");
  }
  if (!Array.isArray(response.records) || response.records.length !== expected.candidates.length) {
    throw new Error(`action-barrier response needs exactly ${expected.candidates.length} candidate records`);
  }
  if (!kinetics && response.records.some((record) => record?.attemptFrequencyPerSecond != null
      || record?.attemptFrequencyUncertaintyLog10 != null || record?.prefactorConverged != null)) {
    throw new Error("per-candidate kinetic fields require the complete response kinetics declaration");
  }
  const expectedById = new Map(expected.candidates.map((candidate) => [candidate.candidateId, candidate]));
  const seen = new Set();
  const records = response.records.map((record, index) => {
    const candidateId = requiredText(record?.candidateId, `barrier record ${index + 1} candidate ID`);
    if (seen.has(candidateId)) throw new Error(`duplicate barrier record for ${candidateId}`);
    seen.add(candidateId);
    const candidate = expectedById.get(candidateId);
    if (!candidate) throw new Error(`unexpected barrier candidate ${candidateId}`);
    if (record.candidateDigestSha256 !== candidate.candidateDigestSha256) {
      throw new Error(`barrier candidate digest mismatch for ${candidateId}`);
    }
    if (record.initialGeometrySha256 !== candidate.initialGeometrySha256
        || record.finalGeometrySha256 !== candidate.finalGeometrySha256) {
      throw new Error(`barrier path geometry digest mismatch for ${candidateId}`);
    }
    if (!finite(record.barrierElectronVolt) || Number(record.barrierElectronVolt) < 0) {
      throw new TypeError(`barrier for ${candidateId} must be finite and nonnegative`);
    }
    if (!finite(record.maximumForceElectronVoltPerAngstrom)
        || Number(record.maximumForceElectronVoltPerAngstrom) < 0) {
      throw new TypeError(`maximum force for ${candidateId} must be finite and nonnegative`);
    }
    if (!finite(record.uncertaintyElectronVolt) || Number(record.uncertaintyElectronVolt) < 0) {
      throw new TypeError(`uncertainty for ${candidateId} must be finite and nonnegative`);
    }
    if (!Number.isInteger(record.imageCount) || record.imageCount < 3 || record.converged !== true) {
      throw new Error(`barrier path for ${candidateId} is incomplete or unconverged`);
    }
    if ((record.energyDeltaElectronVolt != null && !finite(record.energyDeltaElectronVolt))
        || (record.energyDeltaUncertaintyElectronVolt != null
          && !finite(record.energyDeltaUncertaintyElectronVolt))) {
      throw new TypeError(`energy delta fields for ${candidateId} must be finite when supplied`);
    }
    const energyDeltaElectronVolt = record.energyDeltaElectronVolt == null
      ? null : Number(record.energyDeltaElectronVolt);
    const energyDeltaUncertaintyElectronVolt = record.energyDeltaUncertaintyElectronVolt == null
      ? null : Number(record.energyDeltaUncertaintyElectronVolt);
    if ((energyDeltaElectronVolt == null) !== (energyDeltaUncertaintyElectronVolt == null)
        || (energyDeltaUncertaintyElectronVolt != null && energyDeltaUncertaintyElectronVolt < 0)) {
      throw new Error(`energy delta and its nonnegative uncertainty must be supplied together for ${candidateId}`);
    }
    const speciesDelta = candidateSpeciesDelta(candidate);
    let systemFreeEnergyDeltaElectronVolt = null;
    let systemFreeEnergyDeltaUncertaintyElectronVolt = null;
    let reservoirChemicalWorkElectronVolt = null;
    let reservoirChemicalWorkUncertaintyElectronVolt = null;
    let grandPotentialDeltaElectronVolt = null;
    let grandPotentialDeltaUncertaintyElectronVolt = null;
    if (thermodynamics) {
      if (record.systemFreeEnergyDeltaElectronVolt == null
          || record.systemFreeEnergyDeltaUncertaintyElectronVolt == null
          || !finite(record.systemFreeEnergyDeltaElectronVolt)
          || !finite(record.systemFreeEnergyDeltaUncertaintyElectronVolt)
          || Number(record.systemFreeEnergyDeltaUncertaintyElectronVolt) < 0
          || record.stateFreeEnergyConverged !== true) {
        throw new Error(`state free energy for ${candidateId} is incomplete, invalid, or unconverged`);
      }
      systemFreeEnergyDeltaElectronVolt = Number(record.systemFreeEnergyDeltaElectronVolt);
      systemFreeEnergyDeltaUncertaintyElectronVolt = Number(
        record.systemFreeEnergyDeltaUncertaintyElectronVolt);
      const potentials = new Map(thermodynamics.chemicalPotentials.map((entry) =>
        [entry.species, entry]));
      const missing = Object.keys(speciesDelta).filter((species) => !potentials.has(species));
      if (missing.length) {
        throw new Error(`thermodynamic evidence is missing chemical potentials for ${missing.join(", ")}`);
      }
      reservoirChemicalWorkElectronVolt = Object.entries(speciesDelta).reduce((sum,
        [species, delta]) => sum + delta * potentials.get(species).electronVolt, 0);
      reservoirChemicalWorkUncertaintyElectronVolt = Math.sqrt(Object.entries(speciesDelta)
        .reduce((sum, [species, delta]) => sum
          + (delta * potentials.get(species).uncertaintyElectronVolt) ** 2, 0));
      grandPotentialDeltaElectronVolt = systemFreeEnergyDeltaElectronVolt
        - reservoirChemicalWorkElectronVolt;
      grandPotentialDeltaUncertaintyElectronVolt = Math.sqrt(
        systemFreeEnergyDeltaUncertaintyElectronVolt ** 2
        + reservoirChemicalWorkUncertaintyElectronVolt ** 2);
    } else if (record.systemFreeEnergyDeltaElectronVolt != null
        || record.systemFreeEnergyDeltaUncertaintyElectronVolt != null
        || record.stateFreeEnergyConverged != null) {
      throw new Error("per-candidate state free-energy fields require the complete thermodynamics declaration");
    }
    if (kinetics && (!finite(record.attemptFrequencyPerSecond)
        || Number(record.attemptFrequencyPerSecond) <= 0
        || !finite(record.attemptFrequencyUncertaintyLog10)
        || Number(record.attemptFrequencyUncertaintyLog10) < 0
        || record.prefactorConverged !== true)) {
      throw new Error(`kinetic prefactor for ${candidateId} is incomplete, invalid, or unconverged`);
    }
    const pathGeometry = validateCandidateActionPathGeometry(record.pathGeometry, {
      candidate, initialConfiguration: expected.initialConfiguration,
      barrierElectronVolt: Number(record.barrierElectronVolt),
      barrierUncertaintyElectronVolt: Number(record.uncertaintyElectronVolt),
      energyDeltaElectronVolt, energyDeltaUncertaintyElectronVolt,
      maximumForceElectronVoltPerAngstrom: Number(record.maximumForceElectronVoltPerAngstrom),
    });
    if (pathGeometry.imageCount !== record.imageCount) {
      throw new Error(`path image count for ${candidateId} does not match its barrier record`);
    }
    return {
      candidateId,
      candidateDigestSha256: candidate.candidateDigestSha256,
      eventDirection: candidate.eventDirection,
      initialGeometrySha256: candidate.initialGeometrySha256,
      finalGeometrySha256: candidate.finalGeometrySha256,
      barrierElectronVolt: Number(record.barrierElectronVolt),
      uncertaintyElectronVolt: Number(record.uncertaintyElectronVolt),
      maximumForceElectronVoltPerAngstrom: Number(record.maximumForceElectronVoltPerAngstrom),
      imageCount: record.imageCount,
      energyDeltaElectronVolt,
      energyDeltaUncertaintyElectronVolt,
      speciesDelta,
      systemFreeEnergyDeltaElectronVolt,
      systemFreeEnergyDeltaUncertaintyElectronVolt,
      reservoirChemicalWorkElectronVolt,
      reservoirChemicalWorkUncertaintyElectronVolt,
      grandPotentialDeltaElectronVolt,
      grandPotentialDeltaUncertaintyElectronVolt,
      attemptFrequencyPerSecond: kinetics ? Number(record.attemptFrequencyPerSecond) : null,
      attemptFrequencyUncertaintyLog10: kinetics
        ? Number(record.attemptFrequencyUncertaintyLog10) : null,
      prefactorConverged: Boolean(kinetics),
      pathGeometry,
      converged: true,
    };
  });
  if ([...expectedById.keys()].some((candidateId) => !seen.has(candidateId))) {
    throw new Error("action-barrier response omitted one or more frozen candidates");
  }
  const normalized = robustBarrierScores(records);
  return {
    schema: 1,
    responseSchema: response.schema,
    requestSha256: response.requestSha256,
    candidateBatchSha256: response.candidateBatchSha256,
    initialStructureSha256: response.initialStructureSha256,
    method: methodSummary,
    kinetics,
    thermodynamics,
    couplingStateExpectation: expected.couplingStateExpectation || null,
    kineticsEligible: Boolean(kinetics),
    grandCanonicalEvidenceEligible: Boolean(thermodynamics),
    validationPassed: true,
    candidateCount: records.length,
    robustNormalization: { centerElectronVolt: normalized.centerElectronVolt,
      scaleElectronVolt: normalized.scaleElectronVolt, transform: "tanh((median(E)-E)/(2*robustScale))" },
    records: normalized.records,
    usedForCandidateGeneration: false,
    usedForHardAdmission: false,
    usedAsPotential: false,
    usedAsPhysicalClock: false,
    targetCoordinatesEmbedded: false,
    eligibleForExactBatchRanking: true,
    eligibleAsTransferableLaw: false,
    physicalInferenceScope: "this initial configuration, candidate batch, method, and validation only",
    eventDirections: [...new Set(normalized.records.map((record) => record.eventDirection))].sort(),
    reversibleEventGeometryPresent: normalized.records.some((record) => record.eventDirection === "attach")
      && normalized.records.some((record) => record.eventDirection === "detach"),
    surfaceHopGeometryPresent: normalized.records.some((record) => record.eventDirection === "hop"),
    speciesExchangeGeometryPresent: normalized.records.some((record) => record.eventDirection === "exchange"),
    everyPathGeometryValidated: normalized.records.every((record) =>
      record.pathGeometry?.coordinateBearingImagesValidated === true),
    pathGeometryImageCount: normalized.records.reduce((sum, record) =>
      sum + (record.pathGeometry?.imageCount || 0), 0),
    pathGeometryTargetUsed: false,
    thermodynamicReversibilityCertified: false,
    detailedBalanceCertified: false,
    finitePairLocalBalanceCertified: false,
    equilibriumEnsembleClaimed: false,
  };
}
