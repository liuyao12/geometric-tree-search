export const ICE_ORIENTATION_REQUEST_SCHEMA = "gcts-ice-global-orientation-free-energy-request-v1";
export const ICE_ORIENTATION_RESPONSE_SCHEMA = "gcts-ice-global-orientation-free-energy-response-v1";
const BOLTZMANN_EV_PER_KELVIN = 8.617333262145e-5;

function requiredText(value, label) {
  if (typeof value !== "string" || !value.trim()) throw new TypeError(`${label} is required`);
  return value.trim();
}

function finite(value, label) {
  const number = Number(value);
  if (!Number.isFinite(number)) throw new TypeError(`${label} must be finite`);
  return number;
}

function canonicalValue(value) {
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (value && typeof value === "object") return Object.fromEntries(Object.keys(value).sort()
    .map((key) => [key, canonicalValue(value[key])]));
  return value;
}

export function canonicalIceOrientationJson(value) {
  return JSON.stringify(canonicalValue(value));
}

export async function iceOrientationSha256(value) {
  const payload = typeof value === "string" ? value : canonicalIceOrientationJson(value);
  const digest = await globalThis.crypto.subtle.digest("SHA-256", new TextEncoder().encode(payload));
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function normalizeSite(site, label) {
  if (!Array.isArray(site) || site.length !== 2 || typeof site[0] !== "string"
      || !Array.isArray(site[1]) || site[1].length !== 3) {
    throw new TypeError(`${label} must be [species, Cartesian position]`);
  }
  return [site[0], site[1].map((value, axis) => finite(value, `${label} axis ${axis}`))];
}

function normalizedDomains(audit) {
  if (!Array.isArray(audit?.orientationDomains) || !audit.orientationDomains.length) {
    throw new Error("the finite ice-rule audit has no orientation domains");
  }
  const domains = audit.orientationDomains.map((domain, index) => {
    const anchorKey = requiredText(domain.anchorKey, `domain ${index + 1} anchor key`);
    const alternatives = (domain.alternatives || []).map((alternative, poseIndex) => ({
      poseKey: requiredText(alternative.poseKey, `domain ${anchorKey} pose ${poseIndex + 1}`),
      sites: (alternative.sites || []).map((site, siteIndex) =>
        normalizeSite(site, `domain ${anchorKey} pose ${poseIndex + 1} site ${siteIndex + 1}`)),
    })).sort((first, second) => first.poseKey.localeCompare(second.poseKey));
    if (!alternatives.length || new Set(alternatives.map(({ poseKey }) => poseKey)).size !== alternatives.length) {
      throw new Error(`domain ${anchorKey} needs unique retained pose alternatives`);
    }
    alternatives.forEach((alternative) => {
      if (alternative.sites.filter(([species]) => species === "O").length !== 1
          || alternative.sites.filter(([species]) => species === "H").length !== 2) {
        throw new Error(`domain ${anchorKey} pose ${alternative.poseKey} must contain one O and two H sites`);
      }
    });
    return { anchorKey, anchorSite: normalizeSite(domain.anchorSite, `domain ${anchorKey} anchor`), alternatives };
  }).sort((first, second) => first.anchorKey.localeCompare(second.anchorKey));
  if (new Set(domains.map(({ anchorKey }) => anchorKey)).size !== domains.length) {
    throw new Error("orientation-domain anchor keys must be unique");
  }
  return domains;
}

function normalizedConstraints(audit, domains) {
  const poses = new Map(domains.map((domain) => [domain.anchorKey,
    new Set(domain.alternatives.map(({ poseKey }) => poseKey))]));
  return (audit.orientationConstraints || []).map((constraint, index) => {
    const firstAnchorKey = requiredText(constraint.firstAnchorKey, `constraint ${index + 1} first anchor`);
    const secondAnchorKey = requiredText(constraint.secondAnchorKey, `constraint ${index + 1} second anchor`);
    if (!poses.has(firstAnchorKey) || !poses.has(secondAnchorKey) || firstAnchorKey === secondAnchorKey) {
      throw new Error(`constraint ${index + 1} references an unknown or repeated anchor`);
    }
    const allowedPosePairs = (constraint.allowedPosePairs || []).map((pair) => {
      if (!Array.isArray(pair) || pair.length !== 2 || !poses.get(firstAnchorKey).has(pair[0])
          || !poses.get(secondAnchorKey).has(pair[1])) {
        throw new Error(`constraint ${index + 1} has an unknown pose pair`);
      }
      return [pair[0], pair[1]];
    }).sort((first, second) => first.join("\0").localeCompare(second.join("\0")));
    if (!allowedPosePairs.length) throw new Error(`constraint ${index + 1} has no allowed pose pair`);
    return { firstAnchorKey, secondAnchorKey,
      separationAngstrom: finite(constraint.separation, `constraint ${index + 1} separation`),
      allowedPosePairs };
  }).sort((first, second) => `${first.firstAnchorKey}\0${first.secondAnchorKey}`
    .localeCompare(`${second.firstAnchorKey}\0${second.secondAnchorKey}`));
}

export async function buildIceOrientationEvidenceRequest(input) {
  const audit = input?.orientationAudit;
  if (!audit?.consistent || audit.targetUsed || audit.physicalPotentialUsed
      || audit.canonicalBranchMaterialized) {
    throw new Error("only a consistent target-free symbolic ice-rule audit can request orientation physics");
  }
  const domains = normalizedDomains(audit);
  const constraints = normalizedConstraints(audit, domains);
  const unresolved = domains.filter((domain) => domain.alternatives.length > 1);
  if (!unresolved.length) throw new Error("the current finite scaffold has no unresolved orientation domain");
  const temperatureKelvin = finite(input.temperatureKelvin, "temperature");
  const pressureGPa = finite(input.pressureGPa ?? 0, "pressure");
  if (!(temperatureKelvin > 0)) throw new Error("temperature must be positive Kelvin");
  const body = {
    schema: ICE_ORIENTATION_REQUEST_SCHEMA,
    generatedAt: requiredText(input.generatedAt, "generation time"),
    application: { name: "Materials Growth Lab", buildId: requiredText(input.buildId, "build ID") },
    specimen: { caseId: requiredText(input.caseId, "ice case"),
      molecularGrammarSha256: requiredText(input.artifactDigest, "molecular grammar digest") },
    thermodynamicState: { temperatureKelvin, pressureGPa,
      boundaryCondition: requiredText(input.boundaryCondition, "boundary condition") },
    finiteGeometry: {
      domains,
      constraints,
      domainCount: domains.length,
      unresolvedDomainCount: unresolved.length,
      retainedPoseCount: domains.reduce((sum, domain) => sum + domain.alternatives.length, 0),
      exteriorHydrogenBondsOmitted: true,
      candidateGeometryFrozenBeforeRequest: true,
      targetUsed: false,
    },
    calculation: {
      quantity: "global proton-orientation free energy over complete ice-rule-compatible assignments",
      suitableMethods: ["periodic or embedded electronic-structure free energy", "validated machine-learned potential with proton-ordering calibration", "path-integral or configurational free-energy method"],
      requiredOutput: "two or more complete assignments with relative free energy and uncertainty at the exact declared thermodynamic and boundary state",
      independentLocalPoseEnergiesInsufficient: true,
    },
    claimBoundary: "Returned energies may rank only the frozen complete assignments. They cannot create a pose, repair missing candidate supply, infer exterior boundary bonds, or establish kinetics, tunnelling, stationarity, or elapsed time.",
  };
  return { ...body, requestSha256: await iceOrientationSha256(body) };
}

function assignmentMap(record, domains) {
  const mapping = new Map((record.assignment || []).map((entry) => [String(entry.anchorKey), String(entry.poseKey)]));
  if (mapping.size !== domains.length || domains.some((domain) => !mapping.has(domain.anchorKey)
      || !domain.alternatives.some(({ poseKey }) => poseKey === mapping.get(domain.anchorKey)))) {
    throw new Error(`state ${record.stateId} must assign one retained pose to every frozen anchor`);
  }
  return mapping;
}

export async function validateIceOrientationEvidenceResponse(response, request) {
  if (response?.schema !== ICE_ORIENTATION_RESPONSE_SCHEMA) throw new Error("unknown ice orientation-energy response schema");
  if (response.requestSha256 !== request.requestSha256) throw new Error("response does not bind the frozen request");
  const state = response.thermodynamicState || {};
  if (Number(state.temperatureKelvin) !== request.thermodynamicState.temperatureKelvin
      || Number(state.pressureGPa) !== request.thermodynamicState.pressureGPa
      || state.boundaryCondition !== request.thermodynamicState.boundaryCondition) {
    throw new Error("response thermodynamic/boundary state does not match the request");
  }
  const method = response.method || {};
  requiredText(method.name, "method name");
  requiredText(method.version, "method version");
  requiredText(method.provenance, "method provenance");
  if (response.modelScope !== "global-configurational") {
    throw new Error("independent local pose energies cannot resolve the constrained global microstate");
  }
  const records = (response.states || []).map((record, index) => {
    const stateId = requiredText(record.stateId, `state ${index + 1} ID`);
    const mapping = assignmentMap({ ...record, stateId }, request.finiteGeometry.domains);
    request.finiteGeometry.constraints.forEach((constraint) => {
      const key = `${mapping.get(constraint.firstAnchorKey)}\0${mapping.get(constraint.secondAnchorKey)}`;
      if (!constraint.allowedPosePairs.some((pair) => pair.join("\0") === key)) {
        throw new Error(`state ${stateId} violates frozen ice-rule constraint ${constraint.firstAnchorKey}–${constraint.secondAnchorKey}`);
      }
    });
    const freeEnergyEv = finite(record.freeEnergyEv, `state ${stateId} free energy`);
    const uncertaintyEv = finite(record.uncertaintyEv, `state ${stateId} uncertainty`);
    if (uncertaintyEv < 0) throw new Error(`state ${stateId} uncertainty cannot be negative`);
    return { stateId, assignment: request.finiteGeometry.domains.map((domain) =>
      ({ anchorKey: domain.anchorKey, poseKey: mapping.get(domain.anchorKey) })), freeEnergyEv, uncertaintyEv,
      lowerEv: freeEnergyEv - uncertaintyEv, upperEv: freeEnergyEv + uncertaintyEv };
  }).sort((first, second) => first.freeEnergyEv - second.freeEnergyEv || first.stateId.localeCompare(second.stateId));
  if (records.length < 2 || new Set(records.map(({ stateId }) => stateId)).size !== records.length) {
    throw new Error("response needs at least two uniquely identified global states");
  }
  const coverage = response.stateSpaceCoverage || {};
  const coverageDigest = requiredText(coverage.certificateSha256, "state-space certificate SHA-256").toLowerCase();
  if (coverage.kind !== "exhaustive-enumeration" || !/^[a-f0-9]{64}$/.test(coverageDigest)
      || Number(coverage.feasibleAssignmentCount) !== records.length) {
    throw new Error("state-space completeness requires a SHA-bound exhaustive enumeration whose feasible count equals the returned states");
  }
  const best = records[0];
  const competitors = records.slice(1);
  const uniqueIntervalWinner = competitors.every((record) => best.upperEv < record.lowerEv);
  const stateSpaceComplete = true;
  const kbtEv = BOLTZMANN_EV_PER_KELVIN * request.thermodynamicState.temperatureKelvin;
  const minimumGapEv = Math.min(...competitors.map((record) => record.freeEnergyEv - best.freeEnergyEv));
  const selectionEligible = uniqueIntervalWinner && stateSpaceComplete;
  const responseSha256 = await iceOrientationSha256(response);
  return {
    requestSha256: request.requestSha256,
    responseSha256,
    stateCount: records.length,
    stateSpaceComplete,
    stateSpaceCertificateSha256: coverageDigest,
    uniqueIntervalWinner,
    selectedStateId: selectionEligible ? best.stateId : null,
    selectionEligible,
    minimumGapEv,
    minimumGapKbt: minimumGapEv / kbtEv,
    records,
    targetUsed: false,
    candidateGeometryChanged: false,
    claimBoundary: selectionEligible
      ? "One complete frozen proton assignment is separated from every returned competitor after uncertainty, within an explicitly complete state space at this finite boundary and thermodynamic state. This is equilibrium ordering evidence, not a reorientation path, tunnelling rate, growth law, or physical clock."
      : "The response does not uniquely resolve the complete frozen state space after uncertainty. All proton alternatives remain symbolic and no branch may be selected.",
  };
}
