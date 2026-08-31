const SHA256 = /^[a-f0-9]{64}$/i;
const finite = (value) => Number.isFinite(Number(value));

function requiredText(value, label) {
  if (typeof value !== "string" || !value.trim()) throw new TypeError(`${label} is required`);
  return value.trim();
}

function finiteVector(value, label) {
  if (!Array.isArray(value) || value.length !== 3 || !value.every(finite)) {
    throw new TypeError(`${label} must be a finite Cartesian three-vector`);
  }
  return value.map(Number);
}

function normalizedColoredSite(site, label) {
  return { species: requiredText(site?.species, `${label} species`),
    positionAngstrom: finiteVector(site?.positionAngstrom, `${label} position`) };
}

function coloredSiteKey(site) {
  return `${site.species}\u0000${site.positionAngstrom.map((value) =>
    Number(value).toPrecision(15)).join(",")}`;
}

function multiset(sites) {
  const counts = new Map();
  sites.forEach((site) => counts.set(coloredSiteKey(site),
    (counts.get(coloredSiteKey(site)) || 0) + 1));
  return counts;
}

function sameColoredMultiset(first, second) {
  const a = multiset(first); const b = multiset(second);
  return a.size === b.size && [...a].every(([key, count]) => b.get(key) === count);
}

function reconstructFinalSites(initialSites, candidate) {
  const finalSites = initialSites.map((site) => ({ ...site,
    positionAngstrom: [...site.positionAngstrom] }));
  if (["detach", "hop", "exchange"].includes(candidate.eventDirection)) {
    candidate.removedSites.forEach((site) => {
      const key = coloredSiteKey(site);
      const index = finalSites.findIndex((entry) => coloredSiteKey(entry) === key);
      if (index < 0) throw new Error(`path candidate ${candidate.candidateId} removes an absent site`);
      finalSites.splice(index, 1);
    });
  }
  if (["attach", "hop", "exchange"].includes(candidate.eventDirection)) {
    candidate.emittedSites.forEach((site) => {
      if (!finalSites.some((entry) => coloredSiteKey(entry) === coloredSiteKey(site))) {
        finalSites.push({ ...site, positionAngstrom: [...site.positionAngstrom] });
      }
    });
  }
  return finalSites;
}

function normalizeReservoir(raw, eventDirection) {
  if (eventDirection === "hop") {
    if (raw != null) throw new Error("a closed-system surface hop may not declare a reservoir");
    return null;
  }
  if (!raw || raw.mode !== "explicit-extended-system") {
    throw new Error(`${eventDirection} path geometry requires an explicit extended-system reservoir`);
  }
  const settingsSha256 = requiredText(raw.settingsSha256, "reservoir settings SHA-256");
  if (!SHA256.test(settingsSha256)) {
    throw new Error("reservoir settings SHA-256 must contain 64 hexadecimal characters");
  }
  const boundaryCondition = requiredText(raw.boundaryCondition, "reservoir boundary condition");
  if (!["gas-phase", "solution", "surface-feedstock", "bulk-reservoir"].includes(boundaryCondition)) {
    throw new Error("reservoir boundary condition is not supported by the path contract");
  }
  return { mode: raw.mode, boundaryCondition,
    description: requiredText(raw.description, "reservoir description"),
    settingsSha256: settingsSha256.toLowerCase(),
    chemicalPotentialReference: raw.chemicalPotentialReference == null ? null
      : requiredText(raw.chemicalPotentialReference, "reservoir chemical-potential reference") };
}

function normalizeImage(raw, index) {
  if (!finite(raw?.reactionCoordinate) || Number(raw.reactionCoordinate) < 0
      || Number(raw.reactionCoordinate) > 1) {
    throw new Error(`path image ${index + 1} reaction coordinate must lie in [0,1]`);
  }
  if (!finite(raw.energyElectronVolt)) {
    throw new TypeError(`path image ${index + 1} energy must be finite`);
  }
  if (!finite(raw.maximumForceElectronVoltPerAngstrom)
      || Number(raw.maximumForceElectronVoltPerAngstrom) < 0) {
    throw new TypeError(`path image ${index + 1} maximum force must be finite and nonnegative`);
  }
  if (!Array.isArray(raw.sites) || !raw.sites.length) {
    throw new Error(`path image ${index + 1} needs a nonempty extended-system site list`);
  }
  const seen = new Set();
  const sites = raw.sites.map((site, siteIndex) => {
    const pathSiteId = requiredText(site?.pathSiteId,
      `path image ${index + 1} site ${siteIndex + 1} ID`);
    if (seen.has(pathSiteId)) throw new Error(`duplicate path site ID ${pathSiteId}`);
    seen.add(pathSiteId);
    const domain = requiredText(site.domain,
      `path image ${index + 1} site ${pathSiteId} domain`);
    if (!["material", "interface", "reservoir"].includes(domain)) {
      throw new Error(`path site ${pathSiteId} domain must be material, interface, or reservoir`);
    }
    return { pathSiteId, ...normalizedColoredSite(site,
      `path image ${index + 1} site ${pathSiteId}`), domain };
  }).sort((first, second) => first.pathSiteId.localeCompare(second.pathSiteId));
  return { imageIndex: index, reactionCoordinate: Number(raw.reactionCoordinate),
    energyElectronVolt: Number(raw.energyElectronVolt),
    maximumForceElectronVoltPerAngstrom: Number(raw.maximumForceElectronVoltPerAngstrom),
    sites };
}

function normalizeFixedSites(raw) {
  if (!Array.isArray(raw)) throw new TypeError("path fixedMaterialSites must be an array");
  const seen = new Set();
  return raw.map((site, index) => {
    const pathSiteId = requiredText(site?.pathSiteId, `fixed material site ${index + 1} ID`);
    if (seen.has(pathSiteId)) throw new Error(`duplicate fixed path site ID ${pathSiteId}`);
    seen.add(pathSiteId);
    return { pathSiteId, ...normalizedColoredSite(site, `fixed material site ${pathSiteId}`) };
  }).sort((first, second) => first.pathSiteId.localeCompare(second.pathSiteId));
}

export function validateCandidateActionPathGeometry(raw, { candidate, initialConfiguration,
  barrierElectronVolt, barrierUncertaintyElectronVolt, energyDeltaElectronVolt = null,
  energyDeltaUncertaintyElectronVolt = null, maximumForceElectronVoltPerAngstrom } = {}) {
  if (!candidate || !initialConfiguration?.atoms) {
    throw new TypeError("path validation needs its frozen candidate and initial configuration");
  }
  if (raw?.candidateId !== candidate.candidateId
      || raw?.candidateDigestSha256 !== candidate.candidateDigestSha256
      || raw?.initialGeometrySha256 !== candidate.initialGeometrySha256
      || raw?.finalGeometrySha256 !== candidate.finalGeometrySha256) {
    throw new Error(`path geometry is not bound to candidate ${candidate.candidateId}`);
  }
  const pathModel = requiredText(raw.pathModel, "path model");
  const expectedPathModel = candidate.eventDirection === "hop"
    ? "closed-system-fixed-composition" : "explicit-reservoir-extended-system";
  if (pathModel !== expectedPathModel) {
    throw new Error(`${candidate.eventDirection} candidate needs ${expectedPathModel}`);
  }
  const reservoir = normalizeReservoir(raw.reservoir, candidate.eventDirection);
  if (!(raw.pathConverged === true && raw.endpointMappingVerified === true
      && raw.extendedSystemAtomCountConstant === true
      && raw.speciesIdentityConstant === true)) {
    throw new Error("path geometry has not passed convergence, endpoint, cardinality, and species-identity gates");
  }
  if (!Array.isArray(raw.images) || raw.images.length < 3) {
    throw new Error("path geometry needs at least three coordinate-bearing images");
  }
  const fixedMaterialSites = normalizeFixedSites(raw.fixedMaterialSites || []);
  const images = raw.images.map(normalizeImage);
  if (images[0].reactionCoordinate !== 0
      || images.at(-1).reactionCoordinate !== 1
      || images.some((image, index) => index > 0
        && image.reactionCoordinate <= images[index - 1].reactionCoordinate)) {
    throw new Error("path reaction coordinates must increase strictly from 0 to 1");
  }
  const firstIds = images[0].sites.map((site) => site.pathSiteId);
  const firstSpecies = images[0].sites.map((site) => site.species);
  const fixedIds = new Set(fixedMaterialSites.map((site) => site.pathSiteId));
  if (firstIds.some((pathSiteId) => fixedIds.has(pathSiteId))) {
    throw new Error("fixed and moving path-site IDs must be disjoint");
  }
  images.slice(1).forEach((image) => {
    if (image.sites.length !== firstIds.length
        || image.sites.some((site, index) => site.pathSiteId !== firstIds[index])
        || image.sites.some((site, index) => site.species !== firstSpecies[index])) {
      throw new Error("every path image must preserve the exact extended-system site IDs and species");
    }
  });
  const initialMaterial = [...fixedMaterialSites,
    ...images[0].sites.filter((site) => site.domain === "material")];
  const finalMaterial = [...fixedMaterialSites,
    ...images.at(-1).sites.filter((site) => site.domain === "material")];
  const expectedInitial = initialConfiguration.atoms.map(normalizedColoredSite);
  const expectedFinal = reconstructFinalSites(expectedInitial, candidate);
  if (!sameColoredMultiset(initialMaterial, expectedInitial)) {
    throw new Error("path image 0 does not reproduce the frozen initial material geometry");
  }
  if (!sameColoredMultiset(finalMaterial, expectedFinal)) {
    throw new Error("final path image does not reproduce the frozen candidate endpoint");
  }
  if (candidate.eventDirection === "hop"
      && images.some((image) => image.sites.some((site) => site.domain !== "material"))) {
    throw new Error("closed-system surface-hop images must keep every site in the material domain");
  }
  const energies = images.map((image) => image.energyElectronVolt);
  const maximumEnergy = Math.max(...energies);
  const saddleImageIndex = energies.indexOf(maximumEnergy);
  if (saddleImageIndex === 0 || saddleImageIndex === images.length - 1
      || Number(raw.saddleImageIndex) !== saddleImageIndex) {
    throw new Error("the declared saddle must be an internal maximum-energy image");
  }
  const profileBarrier = maximumEnergy - energies[0];
  const barrierTolerance = Math.max(1e-8, Number(barrierUncertaintyElectronVolt) || 0);
  if (Math.abs(profileBarrier - Number(barrierElectronVolt)) > barrierTolerance) {
    throw new Error("coordinate-bearing path energies do not reproduce the reported barrier");
  }
  const profileEnergyDelta = energies.at(-1) - energies[0];
  if (energyDeltaElectronVolt != null && Math.abs(profileEnergyDelta
      - Number(energyDeltaElectronVolt)) > Math.max(1e-8,
        Number(energyDeltaUncertaintyElectronVolt) || 0)) {
    throw new Error("coordinate-bearing path endpoints do not reproduce the reported energy delta");
  }
  const imageMaximumForce = Math.max(...images.map((image) =>
    image.maximumForceElectronVoltPerAngstrom));
  if (Math.abs(imageMaximumForce - Number(maximumForceElectronVoltPerAngstrom)) > 1e-10) {
    throw new Error("path-image forces do not reproduce the reported maximum force");
  }
  const maximumSiteDisplacementAngstrom = Math.max(...images.slice(1).flatMap((image, imageIndex) =>
    image.sites.map((site, siteIndex) => Math.hypot(...site.positionAngstrom.map((value, axis) =>
      value - images[imageIndex].sites[siteIndex].positionAngstrom[axis])))));
  const materialCounts = images.map((image) => fixedMaterialSites.length
    + image.sites.filter((site) => site.domain === "material").length);
  const interfaceCounts = images.map((image) => image.sites.filter((site) =>
    site.domain === "interface").length);
  const reservoirCounts = images.map((image) => image.sites.filter((site) =>
    site.domain === "reservoir").length);
  return { schema: "gcts-candidate-action-path-geometry-audit-v1",
    candidateId: candidate.candidateId, candidateDigestSha256: candidate.candidateDigestSha256,
    eventDirection: candidate.eventDirection, pathModel, reservoir, fixedMaterialSites, images,
    imageCount: images.length, saddleImageIndex, barrierElectronVolt: profileBarrier,
    energyDeltaElectronVolt: profileEnergyDelta, maximumForceElectronVoltPerAngstrom:
      imageMaximumForce, maximumSiteDisplacementAngstrom,
    fixedMaterialSiteCount: fixedMaterialSites.length,
    movingOrReservoirSiteCount: firstIds.length,
    extendedSystemAtomCount: fixedMaterialSites.length + firstIds.length,
    materialCounts, interfaceCounts, reservoirCounts,
    exactInitialEndpoint: true, exactFinalEndpoint: true, pathSiteIdsPreserved: true,
    pathSpeciesPreserved: true, extendedSystemAtomCountConstant: true,
    coordinateBearingImagesValidated: true, targetUsed: false,
    pathCompletenessBeyondReturnedImages: false,
    claimBoundary: "This certificate proves that one externally supplied, constant-cardinality extended-system image chain is species/ID continuous, reaches the exact frozen colored endpoints, and reproduces the reported energy barrier. It does not prove global minimum-energy-path uniqueness, mechanism completeness, recrossing, rate theory, reservoir validity, or transferability of the external method." };
}
