const finite = (value) => Number.isFinite(Number(value));

function position(site, label) {
  if (!Array.isArray(site?.positionAngstrom) || site.positionAngstrom.length !== 3
      || !site.positionAngstrom.every(finite)) {
    throw new TypeError(`${label} needs a finite Cartesian position`);
  }
  return site.positionAngstrom.map(Number);
}

function distance(first, second) {
  return Math.hypot(...first.map((value, axis) => value - second[axis]));
}

function median(values) {
  if (!values.length) return null;
  const sorted = [...values].sort((first, second) => first - second);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

function normalizedFixedSites(path) {
  return (path.fixedMaterialSites || []).map((site, index) => ({
    identity: `fixed:${String(site.pathSiteId)}`, pathSiteId: String(site.pathSiteId),
    species: String(site.species), domain: "material", fixed: true,
    positionAngstrom: position(site, `fixed path site ${index + 1}`),
  }));
}

function normalizedDynamicSites(image, imageIndex) {
  return image.sites.map((site, index) => ({
    identity: `dynamic:${String(site.pathSiteId)}`, pathSiteId: String(site.pathSiteId),
    species: String(site.species), domain: String(site.domain), fixed: false,
    positionAngstrom: position(site, `path image ${imageIndex + 1} site ${index + 1}`),
  }));
}

function contactKey(first, second) {
  return [first.identity, second.identity].sort().join("\u0000");
}

function speciesPair(first, second) {
  return [first.species, second.species].sort().join("–");
}

function deriveLocalReferenceLength(fixedSites, dynamicByImage) {
  const nearest = [];
  dynamicByImage.forEach((dynamicSites) => {
    const materialFacing = dynamicSites.filter((site) => site.domain !== "reservoir");
    const neighbors = [...fixedSites, ...materialFacing];
    materialFacing.forEach((site) => {
      const distances = neighbors.filter((neighbor) => neighbor.identity !== site.identity)
        .map((neighbor) => distance(site.positionAngstrom, neighbor.positionAngstrom))
        .filter((value) => value > 1e-8);
      if (distances.length) nearest.push(Math.min(...distances));
    });
  });
  return median(nearest);
}

function imageContactMap(fixedSites, dynamicSites, cutoffAngstrom) {
  if (cutoffAngstrom == null) return new Map();
  const materialFacing = dynamicSites.filter((site) => site.domain !== "reservoir");
  const neighbors = [...fixedSites, ...materialFacing];
  const contacts = new Map();
  materialFacing.forEach((site) => {
    neighbors.forEach((neighbor) => {
      if (site.identity === neighbor.identity) return;
      const separationAngstrom = distance(site.positionAngstrom, neighbor.positionAngstrom);
      if (!(separationAngstrom <= cutoffAngstrom)) return;
      const key = contactKey(site, neighbor);
      if (!contacts.has(key)) contacts.set(key, { contactId: key,
        firstSiteId: [site.identity, neighbor.identity].sort()[0],
        secondSiteId: [site.identity, neighbor.identity].sort()[1],
        speciesPair: speciesPair(site, neighbor), separationAngstrom });
    });
  });
  return contacts;
}

function rms(values) {
  return values.length ? Math.sqrt(values.reduce((sum, value) => sum + value ** 2, 0)
    / values.length) : 0;
}

function contactCharacter(formed, broken) {
  if (formed && broken) return "contact exchange / reconstructive";
  if (formed) return "contact-forming";
  if (broken) return "contact-breaking";
  return "displacive at this contact reach";
}

export function analyzeActionPathMechanism(path, { contactReach = 1.35,
  referenceLengthAngstrom = null } = {}) {
  if (!path || !Array.isArray(path.images) || path.images.length < 2) {
    throw new TypeError("a mechanism audit needs at least two coordinate-bearing path images");
  }
  if (!finite(contactReach) || Number(contactReach) <= 1) {
    throw new RangeError("contactReach must be a finite multiplier greater than one");
  }
  const fixedSites = normalizedFixedSites(path);
  const dynamicByImage = path.images.map(normalizedDynamicSites);
  const derivedReference = deriveLocalReferenceLength(fixedSites, dynamicByImage);
  const reference = referenceLengthAngstrom == null ? derivedReference
    : Number(referenceLengthAngstrom);
  if (reference != null && (!finite(reference) || reference <= 0)) {
    throw new RangeError("referenceLengthAngstrom must be finite and positive");
  }
  const cutoffAngstrom = reference == null ? null : reference * Number(contactReach);
  const contactsByImage = dynamicByImage.map((sites) =>
    imageContactMap(fixedSites, sites, cutoffAngstrom));
  const perImage = path.images.map((image, index) => {
    const contacts = contactsByImage[index];
    const previous = index ? contactsByImage[index - 1] : new Map();
    const formed = index ? [...contacts.values()].filter((contact) =>
      !previous.has(contact.contactId)) : [];
    const broken = index ? [...previous.values()].filter((contact) =>
      !contacts.has(contact.contactId)) : [];
    const previousSites = index ? new Map(dynamicByImage[index - 1].map((site) =>
      [site.identity, site])) : new Map();
    const displacements = dynamicByImage[index].map((site) => previousSites.has(site.identity)
      ? distance(site.positionAngstrom, previousSites.get(site.identity).positionAngstrom) : 0);
    const activeDynamic = dynamicByImage[index].filter((site) => site.domain !== "reservoir");
    const coordination = activeDynamic.map((site) => [...contacts.values()].filter((contact) =>
      contact.firstSiteId === site.identity || contact.secondSiteId === site.identity).length);
    return { imageIndex: index, reactionCoordinate: Number(image.reactionCoordinate),
      contactCount: contacts.size, formedContactCount: formed.length,
      brokenContactCount: broken.length, formedContacts: formed, brokenContacts: broken,
      meanDynamicCoordination: coordination.length
        ? coordination.reduce((sum, value) => sum + value, 0) / coordination.length : 0,
      maximumDynamicCoordination: coordination.length ? Math.max(...coordination) : 0,
      rmsDynamicDisplacementAngstrom: rms(displacements),
      maximumDynamicDisplacementAngstrom: displacements.length ? Math.max(...displacements) : 0,
      materialFacingDynamicSiteCount: activeDynamic.length };
  });
  const initial = contactsByImage[0]; const final = contactsByImage.at(-1);
  const netFormed = [...final.values()].filter((contact) => !initial.has(contact.contactId));
  const netBroken = [...initial.values()].filter((contact) => !final.has(contact.contactId));
  const intermediateKeys = new Set(contactsByImage.slice(1, -1).flatMap((contacts) =>
    [...contacts.keys()]));
  const transientContactCount = [...intermediateKeys].filter((key) =>
    !initial.has(key) && !final.has(key)).length;
  const totalFormations = perImage.reduce((sum, image) => sum + image.formedContactCount, 0);
  const totalBreaks = perImage.reduce((sum, image) => sum + image.brokenContactCount, 0);
  return { schema: "gcts-action-path-geometric-mechanism-v1",
    candidateId: path.candidateId || null, eventDirection: path.eventDirection || null,
    contactReach: Number(contactReach), referenceLengthAngstrom: reference,
    referenceLengthSource: referenceLengthAngstrom == null
      ? "median-nearest-material-facing-dynamic-site" : "explicit-viewer-input",
    cutoffAngstrom, referenceAvailable: reference != null,
    imageCount: path.images.length, fixedMaterialSiteCount: fixedSites.length,
    dynamicSiteCount: dynamicByImage[0].length, perImage,
    netFormedContactCount: netFormed.length, netBrokenContactCount: netBroken.length,
    netFormedContacts: netFormed, netBrokenContacts: netBroken,
    transientContactCount, totalFormationCount: totalFormations,
    totalBreakCount: totalBreaks,
    geometricCharacter: contactCharacter(netFormed.length, netBroken.length),
    targetUsed: false, contactThresholdChangesCandidate: false,
    chemicalBondClaimed: false, physicalTimeInferred: false,
    claimBoundary: "Contacts are thresholded geometric neighbor relations involving at least one moving path site. They are not bond orders, bond energies, electronic reactions, a unique mechanism, or elapsed physical time." };
}

export function actionPathMechanismSensitivity(path, reaches = [1.15, 1.35, 1.6]) {
  if (!Array.isArray(reaches) || !reaches.length) throw new TypeError("sensitivity needs contact reaches");
  const audits = reaches.map((contactReach) => analyzeActionPathMechanism(path, { contactReach }));
  return { schema: "gcts-action-path-mechanism-sensitivity-v1", reaches: [...reaches],
    audits, characterStable: new Set(audits.map((audit) => audit.geometricCharacter)).size === 1,
    netFormedRange: [Math.min(...audits.map((audit) => audit.netFormedContactCount)),
      Math.max(...audits.map((audit) => audit.netFormedContactCount))],
    netBrokenRange: [Math.min(...audits.map((audit) => audit.netBrokenContactCount)),
      Math.max(...audits.map((audit) => audit.netBrokenContactCount))],
    targetUsed: false, thresholdSensitivityReported: true };
}
