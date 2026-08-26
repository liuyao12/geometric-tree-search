function pairKey(first, second) { return first < second ? `${first}|${second}` : `${second}|${first}`; }
function angularKey(center, first, second) { const pair = [first, second].sort(); return `${pair[0]}<${center}>${pair[1]}`; }
function angleDegrees(first, second) {
  const a = Math.hypot(...first), b = Math.hypot(...second);
  if (!(a > 1e-9 && b > 1e-9)) return null;
  const cosine = first.reduce((sum, value, axis) => sum + value * second[axis], 0) / (a * b);
  return Math.acos(Math.max(-1, Math.min(1, cosine))) * 180 / Math.PI;
}
function round(value, digits = 4) { const scale = 10 ** digits; return Math.round(value * scale) / scale; }
function mean(values) { return values.reduce((sum, value) => sum + value, 0) / Math.max(1, values.length); }

/** Expand one exact current center into interpretable learned-geometry channels. */
export function buildSiteConstraintAudit({ centerSpecies, neighbors, distanceModel,
  coordinationModel, angularModel, aggregate, populationContext = null }) {
  if (!centerSpecies || !Array.isArray(neighbors) || !distanceModel?.byKey
      || !coordinationModel?.records || !angularModel?.byKey || !aggregate) {
    throw new Error("Site constraint audit requires one center, neighbors, frozen models, and aggregate residual");
  }
  const contacts = neighbors.map((neighbor) => {
    const coordination = coordinationModel.byKey?.[`${centerSpecies}>${neighbor.species}`];
    return coordination && neighbor.distance <= coordination.contactCutoff ? { ...neighbor, coordination } : null;
  }).filter(Boolean);
  const distanceChannels = contacts.map((contact) => {
    const envelope = distanceModel.byKey[pairKey(centerSpecies, contact.species)];
    if (!envelope) return null;
    const normalizedResidual = Math.abs(contact.distance - envelope.typicalContact) / envelope.contactScale;
    return { kind: "contact", species: `${centerSpecies}–${contact.species}`,
      observed: round(contact.distance), expected: round(envelope.typicalContact),
      lower: round(envelope.lowerContact), upper: round(envelope.upperContact),
      normalizedResidual: round(normalizedResidual),
      status: normalizedResidual <= 1 ? "within mode" : normalizedResidual <= 2 ? "strained" : "off mode" };
  }).filter(Boolean);
  const coordinationChannels = coordinationModel.records.filter((record) => record.centerSpecies === centerSpecies)
    .map((record) => {
      const observed = contacts.filter((contact) => contact.species === record.neighborSpecies).length;
      return { kind: "coordination", species: `${centerSpecies}→${record.neighborSpecies}`,
        observed, expected: record.medianObserved, maximum: record.maximumObserved,
        deficit: record.medianObserved > 0 ? round(Math.max(0, record.medianObserved - observed) / record.medianObserved) : 0,
        status: observed > record.maximumObserved ? "over capacity"
          : observed < record.medianObserved ? "frontier deficit" : "within learned range" };
    });
  const angleChannels = [];
  for (let first = 0; first < contacts.length - 1; first += 1) for (let second = first + 1; second < contacts.length; second += 1) {
    const envelope = angularModel.byKey[angularKey(centerSpecies, contacts[first].species, contacts[second].species)];
    if (!envelope) continue;
    const degrees = angleDegrees(contacts[first].vector, contacts[second].vector);
    if (!Number.isFinite(degrees)) continue;
    const inside = envelope.bands.some((band) => degrees >= band.minimum && degrees <= band.maximum);
    const nearestDeviation = Math.min(...envelope.bands.map((band) => degrees < band.minimum
      ? band.minimum - degrees : degrees > band.maximum ? degrees - band.maximum : 0));
    angleChannels.push({ kind: "angle", species: `${contacts[first].species}<${centerSpecies}>${contacts[second].species}`,
      observed: round(degrees, 2), bands: envelope.bands.map((band) => [round(band.minimum, 2), round(band.maximum, 2)]),
      deviationDegrees: round(nearestDeviation, 2), status: inside ? "within band" : "outside band" });
  }
  const hardConflicts = coordinationChannels.filter((channel) => channel.status === "over capacity").length
    + angleChannels.filter((channel) => channel.status === "outside band").length;
  const summary = {
    contactAngleMismatch: round(aggregate.contactAngleMismatch),
    distanceMismatch: round(aggregate.distance), angleMismatch: round(aggregate.angle),
    coordinationDeficit: round(aggregate.coordinationDeficit),
    contactTerms: aggregate.contactTerms, angleTerms: aggregate.angleTerms,
    coordinationTerms: aggregate.coordinationTerms, neighborCount: aggregate.neighborCount,
    hardConflicts, status: hardConflicts ? "outside learned support"
      : aggregate.contactAngleMismatch > 1 ? "high geometric strain"
        : aggregate.coordinationDeficit > 0 ? "admissible frontier deficit" : "inside learned local geometry",
    populationContext,
  };
  return { schema: 1, summary, distanceChannels, coordinationChannels, angleChannels,
    channelCounts: { contacts: distanceChannels.length, coordination: coordinationChannels.length,
      angles: angleChannels.length },
    channelResidualMean: round(mean(distanceChannels.map((channel) => channel.normalizedResidual))),
    targetUsed: false, physicalPotentialUsed: false, forceInferred: false,
    surfaceEnergyInferred: false, defectIdentityInferred: false };
}
