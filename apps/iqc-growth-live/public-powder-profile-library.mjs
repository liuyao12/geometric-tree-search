export const RRUFF_LIBRARY_ASSET_SHA256 = "87feefb42fcd82b180233f320c5b78bb1f9ce911c8faf3eca56a756d6332f68e";
export const RRUFF_LIBRARY_ASSET = new URL("./data/rruff-powder-profiles-v1.json", import.meta.url);

const PHASE_ALIASES = Object.freeze({
  Halite: Object.freeze(["halite", "nacl", "rocksalt", "rock salt"]),
  Graphite: Object.freeze(["graphite"]),
  Silicon: Object.freeze(["diamond cubic silicon", "silicon diamond", "fd3m silicon"]),
  Calcite: Object.freeze(["calcite"]),
  Aragonite: Object.freeze(["aragonite"]),
  Rutile: Object.freeze(["rutile"]),
  Brookite: Object.freeze(["brookite"]),
});

function elementKey(elements = []) {
  return [...new Set(elements.map(String))].sort().join("|");
}

async function sha256Hex(bytes) {
  const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map(value => value.toString(16).padStart(2, "0")).join("");
}

function validateRecord(record) {
  if (!/^R\d{6}$/.test(record?.rruffId || "")) throw new Error("invalid RRUFF profile identifier");
  if (!Array.isArray(record.elements) || !record.elements.length) throw new Error("RRUFF profile elements missing");
  if (record.axis !== "two-theta-degree") throw new Error("RRUFF profile axis must be two theta");
  if (!(Number(record.wavelengthAngstrom) > 0)) throw new Error("RRUFF wavelength missing");
  if (!Array.isArray(record.x) || record.x.length < 12 || record.x.length !== record.y?.length) {
    throw new Error("RRUFF profile arrays do not align");
  }
  for (let index = 0; index < record.x.length; index++) {
    if (!Number.isFinite(record.x[index]) || !Number.isFinite(record.y[index]) || record.y[index] < 0) {
      throw new Error("RRUFF profile contains invalid values");
    }
    if (index && !(record.x[index] > record.x[index - 1])) throw new Error("RRUFF profile axis is not increasing");
  }
  return record;
}

export async function loadRruffPowderLibrary(options = {}) {
  const fetchImpl = options.fetchImpl || globalThis.fetch;
  if (typeof fetchImpl !== "function") throw new Error("fetch is required for the public profile library");
  const response = await fetchImpl(options.assetUrl || RRUFF_LIBRARY_ASSET);
  if (!response?.ok) throw new Error(`RRUFF profile library request failed (${response?.status || "network"})`);
  const bytes = await response.arrayBuffer();
  const assetSha256 = await sha256Hex(bytes);
  if (assetSha256 !== RRUFF_LIBRARY_ASSET_SHA256) throw new Error("RRUFF profile library digest mismatch");
  const library = JSON.parse(new TextDecoder().decode(bytes));
  if (library.schema !== "gcts-rruff-powder-profile-library-v1"
      || library.license !== "CC BY 4.0"
      || library.datasetDoi !== "https://doi.org/10.6084/m9.figshare.31817977.v1"
      || library.profileCount !== library.profiles?.length) {
    throw new Error("RRUFF profile library provenance contract failed");
  }
  library.profiles.forEach(validateRecord);
  return Object.freeze({ ...library, assetSha256,
    profiles: Object.freeze(library.profiles.map(record => Object.freeze(record))) });
}

export function findRruffPowderProfiles(library, request = {}) {
  if (library?.schema !== "gcts-rruff-powder-profile-library-v1") throw new Error("validated RRUFF library required");
  const requestedElements = elementKey(request.species || []);
  const materialLabel = String(request.materialLabel || "").toLowerCase();
  return Object.freeze(library.profiles
    .filter(record => elementKey(record.elements) === requestedElements)
    .map(record => {
      const aliases = PHASE_ALIASES[record.phase] || [];
      const exactPhase = aliases.some(alias => materialLabel.includes(alias));
      return Object.freeze({ record,
        correspondence: Object.freeze({
          level: exactPhase ? "exact-phase" : "composition-only",
          elements: Object.freeze([...record.elements]), formula: record.formula, phase: record.phase,
          basis: exactPhase
            ? "exact element set plus curated phase-name correspondence"
            : "exact element set only; polymorph/phase identity is not established",
          sameMaterialClaimAllowed: exactPhase,
        }) });
    })
    .sort((first, second) => Number(second.correspondence.sameMaterialClaimAllowed)
      - Number(first.correspondence.sameMaterialClaimAllowed)
      || first.record.phase.localeCompare(second.record.phase)
      || first.record.rruffId.localeCompare(second.record.rruffId)));
}

export function rruffRequestCompatibility(request = {}) {
  if (request.probe !== "x-ray") return Object.freeze({ compatible: false, reason: "RRUFF library contains X-ray powder profiles" });
  if (request.modelChannel?.kind !== "constant-Z") {
    return Object.freeze({ compatible: false,
      reason: "select the constant-Z electron-count X-ray approximation; unit, centered-contrast, and sublattice curves are not comparable to measured X-ray intensity" });
  }
  return Object.freeze({ compatible: true, reason: "X-ray probe and constant-Z electron-count model channel agree" });
}

export function buildRruffExperimentalResponse(request, match, library) {
  if (!request || !match?.record || library?.schema !== "gcts-rruff-powder-profile-library-v1") {
    throw new Error("request, profile match, and validated RRUFF library are required");
  }
  const compatibility = rruffRequestCompatibility(request);
  if (!compatibility.compatible) throw new Error(compatibility.reason);
  if (elementKey(match.record.elements) !== elementKey(request.species || [])) {
    throw new Error("RRUFF profile chemistry does not match the requested element set");
  }
  const record = validateRecord(match.record);
  return {
    requestId: request.requestId,
    structureSha256: request.structureSha256,
    probe: "x-ray",
    modelChannel: { kind: "constant-Z", species: null },
    axis: record.axis,
    wavelengthAngstrom: record.wavelengthAngstrom,
    abscissa: record.x,
    intensity: record.y,
    intensityUnits: record.intensityUnits,
    resolutionFwhmQ: 0,
    corrections: [
      "RRUFF processed XY profile retained without portal smoothing or peak picking",
      "instrument resolution absent from normalized record; no extra convolution applied",
      "uncertainties absent from normalized record; uniform unit weights",
    ],
    provenance: {
      title: `${record.phase} ${record.rruffId} · experimental powder XRD`,
      url: record.sourceUrl,
      datasetId: record.rruffId,
      datasetDoi: library.datasetDoi,
      license: library.license,
      source: record.source,
      locality: record.locality,
      cellParameters: record.cellParameters,
      spaceGroup: record.spaceGroup,
      profileSha256: record.profileSha256,
      libraryAssetSha256: library.assetSha256,
      difTextSha256: record.difTextSha256,
      selectionRule: library.selectionRule,
    },
    materialCorrespondence: match.correspondence,
    independentOfGrowth: true,
    usedForGrowth: false,
    usedForMarking: false,
    usedForCandidateSelection: false,
  };
}
