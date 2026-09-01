const finitePositive = (value) => Number.isFinite(Number(value)) && Number(value) > 0;

export const BORN_MAYER_PAIR_POLICIES = Object.freeze({
  uniform: Object.freeze({
    id: "uniform",
    label: "Uniform reference · one A and ρ",
    description: "Every observed species pair uses the same declared reference coefficients.",
  }),
  "contact-scaled": Object.freeze({
    id: "contact-scaled",
    label: "Observed-contact scaled ρᵢⱼ",
    description: "The decay length is scaled by the frozen additive contact envelope of each species pair.",
  }),
});

export function canonicalSpeciesPairKey(firstSpecies, secondSpecies) {
  const pair = [String(firstSpecies ?? ""), String(secondSpecies ?? "")].sort();
  if (!pair[0] || !pair[1]) throw new TypeError("species-pair keys require two nonempty species tokens");
  return `${pair[0]}\u241f${pair[1]}`;
}

function median(values) {
  const ordered = values.filter(finitePositive).map(Number).sort((first, second) => first - second);
  if (!ordered.length) return null;
  const middle = Math.floor(ordered.length / 2);
  return ordered.length % 2 ? ordered[middle] : (ordered[middle - 1] + ordered[middle]) / 2;
}

/**
 * Build a finite species-pair Born–Mayer hypothesis from the supplied structure.
 *
 * The contact-scaled policy changes only rho_ij. It uses the already-frozen
 * additive geometric contact envelope and keeps the declared amplitude fixed.
 * No energy, force, target configuration, oxidation state, or material label is
 * fitted here.
 */
export function buildBornMayerPairMatrix(speciesTokens = [], contactEnvelope = null, {
  policy = "uniform",
  amplitudeElectronVolt = 1000,
  decayAngstrom = .3,
} = {}) {
  if (!Object.hasOwn(BORN_MAYER_PAIR_POLICIES, policy)) {
    throw new RangeError(`unknown Born–Mayer pair policy: ${policy}`);
  }
  if (!finitePositive(amplitudeElectronVolt) || Number(amplitudeElectronVolt) > 1e6) {
    throw new RangeError("amplitudeElectronVolt must be in (0, 1e6] eV");
  }
  if (!finitePositive(decayAngstrom) || Number(decayAngstrom) > 10) {
    throw new RangeError("decayAngstrom must be in (0, 10] angstrom");
  }
  const species = [...new Set(speciesTokens.map((token) => String(token ?? "")).filter(Boolean))].sort();
  if (!species.length) return {
    available: false,
    reason: "no observed species tokens",
    policy,
    records: [],
    targetUsed: false,
  };
  const radii = contactEnvelope?.available ? contactEnvelope.radiiAngstrom || {} : {};
  const rawPairs = [];
  species.forEach((first, firstIndex) => species.slice(firstIndex).forEach((second) => {
    const contactAngstrom = finitePositive(radii[first]) && finitePositive(radii[second])
      ? Number(radii[first]) + Number(radii[second]) : null;
    rawPairs.push({ first, second, contactAngstrom });
  }));
  const referenceContactAngstrom = median(rawPairs.map((record) => record.contactAngstrom));
  const records = rawPairs.map(({ first, second, contactAngstrom }) => {
    const geometryConditioned = policy === "contact-scaled"
      && finitePositive(contactAngstrom) && finitePositive(referenceContactAngstrom);
    const contactScale = geometryConditioned
      ? contactAngstrom / referenceContactAngstrom : 1;
    return Object.freeze({
      key: canonicalSpeciesPairKey(first, second),
      species: Object.freeze([first, second]),
      amplitudeElectronVolt: Number(amplitudeElectronVolt),
      decayAngstrom: Number(decayAngstrom) * contactScale,
      observedContactAngstrom: finitePositive(contactAngstrom) ? contactAngstrom : null,
      contactScale,
      geometryConditioned,
      parameterSource: geometryConditioned
        ? "frozen additive leading-contact envelope"
        : "declared uniform reference fallback",
    });
  });
  const geometryConditionedPairs = records.filter((record) => record.geometryConditioned).length;
  return Object.freeze({
    available: records.length > 0,
    policy,
    policyLabel: BORN_MAYER_PAIR_POLICIES[policy].label,
    species: Object.freeze(species),
    pairCount: records.length,
    records: Object.freeze(records),
    referenceAmplitudeElectronVolt: Number(amplitudeElectronVolt),
    referenceDecayAngstrom: Number(decayAngstrom),
    referenceContactAngstrom,
    geometryConditionedPairs,
    uniformFallbackPairs: records.length - geometryConditionedPairs,
    contactEnvelopeAvailable: Boolean(contactEnvelope?.available),
    contactEnvelopeSelectedPairCount: contactEnvelope?.available
      ? Number(contactEnvelope.selectedPairCount || 0) : 0,
    contactEnvelopeRmsResidualAngstrom: contactEnvelope?.available
      && Number.isFinite(contactEnvelope.rmsResidualAngstrom)
      ? Number(contactEnvelope.rmsResidualAngstrom) : null,
    energyOrForceFitted: false,
    materialIdentityUsed: false,
    oxidationStatesInferred: false,
    targetUsed: false,
    claimBoundary: policy === "contact-scaled"
      ? "rho_ij is scaled only by a frozen sample-fitted geometric contact envelope. A is declared and no pair energy or force coefficient is fitted."
      : "All species pairs use one declared A and rho; this is not a species-specific force field.",
  });
}

export function bornMayerPairParameter(matrix, firstSpecies, secondSpecies) {
  if (!matrix?.available || !Array.isArray(matrix.records)) return null;
  const key = canonicalSpeciesPairKey(firstSpecies, secondSpecies);
  return matrix.records.find((record) => record.key === key) || null;
}
