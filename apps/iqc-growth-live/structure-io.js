const NUMBER = /^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?(?:\(\d+\))?$/;

function numeric(value, label) {
  const cleaned = String(value).replace(/\([^)]*\)$/, "");
  if (!NUMBER.test(String(value)) && !NUMBER.test(cleaned)) throw new Error(`Invalid ${label}: ${value}`);
  const result = Number(cleaned);
  if (!Number.isFinite(result)) throw new Error(`Invalid ${label}: ${value}`);
  return result;
}

function tokens(line) {
  return [...String(line).matchAll(/'(?:[^']|'')*'|"(?:[^"]|"")*"|\S+/g)].map((match) => {
    const value = match[0];
    return ((value.startsWith("'") && value.endsWith("'")) || (value.startsWith('"') && value.endsWith('"')))
      ? value.slice(1, -1) : value;
  });
}

function elementSymbols(value) {
  const text = String(value || "X").trim();
  const parts = text.split(/[\/|,]/).map((part) => part.trim()).filter(Boolean);
  const matches = (parts.length > 1 ? parts : [text]).map((part) => part.match(/[A-Z][a-z]?/)?.[0]).filter(Boolean);
  return [...new Set(matches.length ? matches : ["X"])];
}

function elementSymbol(value) {
  return elementSymbols(value)[0];
}

function formalChargeFromLabel(value) {
  const text = String(value || "").trim();
  const terminal = text.match(/^[A-Z][a-z]?\s*(?:(\d+(?:\.\d+)?)\s*([+-])|([+-])\s*(\d+(?:\.\d+)?))$/);
  if (!terminal) return null;
  const sign = terminal[2] || terminal[3];
  const magnitude = Number(terminal[1] || terminal[4] || 1);
  return magnitude * (sign === "+" ? 1 : -1);
}

function speciesChargeAlternativesFromLabel(value) {
  const parts = String(value || "X").split(/[\/|,]/).map((part) => part.trim()).filter(Boolean);
  const records = parts.map((part) => ({
    species: elementSymbol(part),
    formalCharge: formalChargeFromLabel(part),
  }));
  const unique = new Map();
  records.forEach((record) => unique.set(
    `${record.species}|${record.formalCharge === null ? "?" : record.formalCharge}`,
    record,
  ));
  return [...unique.values()];
}

function optionalFormalCharge(value, fallback = null) {
  if (value === undefined || value === null || value === "" || value === "." || value === "?") return fallback;
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new Error(`Invalid formal charge: ${value}`);
    return value;
  }
  const text = String(value).trim();
  if (NUMBER.test(text)) return numeric(text, "formal charge");
  const suffix = text.match(/^([+-]?\d+(?:\.\d+)?)?([+-])$/);
  if (suffix) {
    const magnitude = suffix[1] ? Math.abs(Number(suffix[1])) : 1;
    return magnitude * (suffix[2] === "+" ? 1 : -1);
  }
  throw new Error(`Invalid formal charge: ${value}`);
}

const occupancyFraction = (value, fallback = null) => {
  if (value === undefined || value === null || value === "" || value === "." || value === "?") return fallback;
  const fraction = numeric(value, "occupancy");
  if (!(fraction >= 0 && fraction <= 1 + 1e-8)) throw new Error(`Occupancy must lie between 0 and 1: ${value}`);
  return Math.max(0, Math.min(1, fraction));
};

const optionalCifNumber = (value, label) => value === undefined || value === null || value === "" || value === "." || value === "?"
  ? null : numeric(value, label);

function recordedCifMeasurementConditions(get) {
  const readNumber = (primaryTags, fallbackTags, label) => {
    for (const [tags, deprecatedFallback] of [[primaryTags, false], [fallbackTags, true]]) {
      for (const sourceTag of tags) {
        const raw = get(sourceTag);
        const value = optionalCifNumber(raw, label);
        if (value === null) continue;
        if (value < 0) throw new Error(`${label} must be nonnegative: ${raw}`);
        return { value, sourceTag, deprecatedFallback };
      }
    }
    return null;
  };
  const readText = (tags) => {
    for (const sourceTag of tags) {
      const raw = get(sourceTag);
      if (raw === undefined || raw === null || raw === "" || raw === "." || raw === "?") continue;
      return { value: String(raw).trim(), sourceTag };
    }
    return null;
  };
  const temperature = readNumber(
    ["_diffrn_ambient_temperature", "_diffrn_ambient_temp"],
    ["_cell_measurement_temperature", "_cell_measurement_temp"],
    "recorded measurement temperature",
  );
  const pressure = readNumber(
    ["_diffrn_ambient_pressure"], ["_cell_measurement_pressure"],
    "recorded measurement pressure",
  );
  const environment = readText(["_diffrn_ambient_environment"]);
  if (!temperature && !pressure && !environment) return null;
  return {
    temperature: temperature ? { ...temperature, unit: "K" } : null,
    pressure: pressure ? { ...pressure, unit: "kPa" } : null,
    environment,
    provenance: "recorded diffraction/cell-measurement conditions",
    usedAsSimulationControl: false,
    synthesisConditionsClaimed: false,
    thermodynamicStateReconstructed: false,
  };
}

function normalizeThermalDisplacement({ uIsoA2 = null, bIsoA2 = null, thermalSigmaA = null } = {}) {
  let uIso = optionalCifNumber(uIsoA2, "isotropic displacement U") ?? null;
  const bIso = optionalCifNumber(bIsoA2, "isotropic displacement B") ?? null;
  const sigma = optionalCifNumber(thermalSigmaA, "thermal displacement sigma") ?? null;
  if (uIso === null && bIso !== null) uIso = bIso / (8 * Math.PI * Math.PI);
  if (uIso === null && sigma !== null) uIso = sigma * sigma;
  if (uIso !== null && uIso < 0) throw new Error(`Isotropic displacement U must be nonnegative: ${uIso}`);
  if (uIso === null) return {};
  return { uIsoA2: uIso, bIsoA2: uIso * 8 * Math.PI * Math.PI, thermalSigmaA: Math.sqrt(uIso) };
}

function normalizeAnisotropicDisplacement(tensor, scale = 1) {
  if (!tensor) return {};
  const uAnisoCartesianA2 = tensor.map((row) => row.map((value) => Number(value) * scale));
  const eigen = symmetricTensorEigenSystem(uAnisoCartesianA2);
  const uIsoA2 = eigen.eigenvaluesA2.reduce((sum, value) => sum + value, 0) / 3;
  return {
    uAnisoCartesianA2,
    uIsoA2,
    bIsoA2: uIsoA2 * 8 * Math.PI * Math.PI,
    thermalSigmaA: Math.sqrt(uIsoA2),
    thermalSigmaAxesA: eigen.sigmaAxesA,
    thermalAxesCartesian: eigen.axes,
  };
}

function thermalTensorForSite(site) {
  if (site.uAnisoCartesianA2) return site.uAnisoCartesianA2;
  if (!Number.isFinite(site.uIsoA2)) return null;
  return [[site.uIsoA2, 0, 0], [0, site.uIsoA2, 0], [0, 0, site.uIsoA2]];
}

function occupancyEntries(value) {
  if (Array.isArray(value)) return value.map((entry) => typeof entry === "string"
    ? { species: elementSymbol(entry), fraction: null, formalCharge: formalChargeFromLabel(entry) }
    : { species: elementSymbol(entry.species || entry.element || entry.symbol),
      fraction: occupancyFraction(entry.fraction ?? entry.occupancy, null),
      formalCharge: optionalFormalCharge(entry.formalCharge ?? entry.charge ?? entry.oxidationState, null) });
  if (value && typeof value === "object") return Object.entries(value)
    .map(([species, record]) => typeof record === "object"
      ? { species: elementSymbol(species), fraction: occupancyFraction(record.fraction ?? record.occupancy, null),
        formalCharge: optionalFormalCharge(record.formalCharge ?? record.charge ?? record.oxidationState, formalChargeFromLabel(species)) }
      : { species: elementSymbol(species), fraction: occupancyFraction(record, null), formalCharge: formalChargeFromLabel(species) });
  return [];
}

export function normalizeSiteOccupancy(speciesValue, occupancyValue = 1, alternativesValue = null, formalChargeValue = null) {
  const labelAlternatives = speciesChargeAlternativesFromLabel(speciesValue);
  const siteCharge = optionalFormalCharge(formalChargeValue, null);
  const explicit = occupancyEntries(alternativesValue);
  let entries = explicit.length ? explicit : labelAlternatives.map(({ species, formalCharge }) => ({
    species, fraction: null, formalCharge: siteCharge ?? formalCharge,
  }));
  if (siteCharge !== null) entries = entries.map((entry) => ({ ...entry, formalCharge: entry.formalCharge ?? siteCharge }));
  const scalar = occupancyFraction(Array.isArray(occupancyValue) || (occupancyValue && typeof occupancyValue === "object")
    ? 1 : occupancyValue, 1);
  const known = entries.reduce((sum, entry) => sum + (entry.fraction ?? 0), 0);
  const unknown = entries.filter((entry) => entry.fraction === null);
  if (known > 1 + 1e-8) throw new Error(`Occupational alternatives sum to ${known.toFixed(6)}, above 1`);
  const target = explicit.some((entry) => entry.fraction !== null) ? Math.max(scalar, known) : scalar;
  const remaining = Math.max(0, target - known);
  entries = entries.map((entry) => ({
    species: entry.species,
    fraction: entry.fraction ?? (unknown.length ? remaining / unknown.length : 0),
    formalCharge: entry.formalCharge ?? null,
  }));
  const combined = new Map();
  entries.forEach(({ species, fraction, formalCharge }) => {
    const key = `${species}|${formalCharge === null ? "?" : formalCharge}`;
    const current = combined.get(key) || { species, fraction: 0, formalCharge };
    current.fraction += fraction;
    combined.set(key, current);
  });
  const alternatives = [...combined.values()].filter((entry) => entry.fraction > 1e-10)
    .sort((first, second) => second.fraction - first.fraction || first.species.localeCompare(second.species)
      || (first.formalCharge ?? 0) - (second.formalCharge ?? 0));
  const total = alternatives.reduce((sum, entry) => sum + entry.fraction, 0);
  if (!alternatives.length || total <= 0) throw new Error("A crystallographic site must have positive occupancy");
  if (total > 1 + 1e-8) throw new Error(`Occupational alternatives sum to ${total.toFixed(6)}, above 1`);
  return {
    species: alternatives[0].species,
    occupancy: total,
    occupancyTotal: total,
    occupancyAlternatives: alternatives,
    occupancyFractionsInferred: !explicit.length && labelAlternatives.length > 1,
    formalCharge: alternatives.every((entry) => entry.formalCharge !== null)
      ? alternatives.reduce((sum, entry) => sum + entry.fraction * entry.formalCharge, 0) : null,
    formalChargeKnownFraction: alternatives.reduce((sum, entry) => sum + (entry.formalCharge === null ? 0 : entry.fraction), 0),
  };
}

const compactFraction = (value) => Number(value.toFixed(8)).toString();

export function occupancyChemistryToken(atom) {
  const normalized = normalizeSiteOccupancy(atom?.species, atom?.occupancy ?? atom?.occupancyTotal ?? 1,
    atom?.occupancyAlternatives ?? (Array.isArray(atom?.occupancy) || (atom?.occupancy && typeof atom.occupancy === "object") ? atom.occupancy : null),
    atom?.formalCharge ?? atom?.charge ?? null);
  const chargedSpecies = (entry) => entry.formalCharge === null ? entry.species
    : `${entry.species}^${entry.formalCharge >= 0 ? "+" : ""}${compactFraction(entry.formalCharge)}`;
  if (normalized.occupancyAlternatives.length === 1 && Math.abs(normalized.occupancyTotal - 1) < 1e-8) {
    return chargedSpecies(normalized.occupancyAlternatives[0]);
  }
  const entries = normalized.occupancyAlternatives
    .slice().sort((first, second) => chargedSpecies(first).localeCompare(chargedSpecies(second)))
    .map((entry) => `${chargedSpecies(entry)}=${compactFraction(entry.fraction)}`);
  const vacancy = Math.max(0, 1 - normalized.occupancyTotal);
  if (vacancy > 1e-8) entries.push(`Vac=${compactFraction(vacancy)}`);
  return `occ[${entries.join(";")}]`;
}

export function occupancyDisplayLabel(atom) {
  const normalized = normalizeSiteOccupancy(atom?.species, atom?.occupancy ?? atom?.occupancyTotal ?? 1,
    atom?.occupancyAlternatives ?? (Array.isArray(atom?.occupancy) || (atom?.occupancy && typeof atom.occupancy === "object") ? atom.occupancy : null),
    atom?.formalCharge ?? atom?.charge ?? null);
  const entries = normalized.occupancyAlternatives.map((entry) => `${entry.species}${entry.formalCharge === null ? "" : `(${entry.formalCharge >= 0 ? "+" : ""}${compactFraction(entry.formalCharge)})`} ${Math.round(entry.fraction * 1000) / 10}%`);
  const vacancy = Math.max(0, 1 - normalized.occupancyTotal);
  if (vacancy > 1e-8) entries.push(`vacancy ${Math.round(vacancy * 1000) / 10}%`);
  return entries.join(" / ");
}

function chargeFromTokenSpecies(tokenSpecies) {
  const match = String(tokenSpecies).match(/\^([+-]\d+(?:\.\d+)?)$/);
  return match ? Number(match[1]) : null;
}

export function formalChargeFromChemistryToken(token) {
  const occupational = String(token).match(/^occ\[(.*)]$/);
  if (!occupational) return chargeFromTokenSpecies(token);
  let total = 0;
  for (const record of occupational[1].split(";")) {
    const [species, fractionText] = record.split("=");
    if (species === "Vac") continue;
    const charge = chargeFromTokenSpecies(species);
    if (charge === null) return null;
    const fraction = Number(fractionText);
    if (!Number.isFinite(fraction)) return null;
    total += fraction * charge;
  }
  return total;
}

export function isotropicPairDistanceUncertaintyA(oneAxisSigmaA) {
  const sigma = Number(oneAxisSigmaA);
  if (!Number.isFinite(sigma) || sigma < 0) throw new Error("Isotropic site sigma must be a finite nonnegative length");
  return Math.SQRT2 * sigma;
}

function mergeSiteOccupancies(first, second, additive) {
  const keyFor = (entry) => `${entry.species}|${entry.formalCharge === null || entry.formalCharge === undefined ? "?" : entry.formalCharge}`;
  const fractions = new Map(first.occupancyAlternatives.map((entry) => [keyFor(entry), { ...entry }]));
  second.occupancyAlternatives.forEach((entry) => {
    const key = keyFor(entry); const previous = fractions.get(key);
    fractions.set(key, { ...entry, fraction: additive
      ? (previous?.fraction || 0) + entry.fraction : Math.max(previous?.fraction || 0, entry.fraction) });
  });
  const normalized = normalizeSiteOccupancy(first.species, 1,
    [...fractions.values()]);
  const thermal = [[first, first.occupancyTotal ?? first.occupancy ?? 1], [second, second.occupancyTotal ?? second.occupancy ?? 1]]
    .filter(([site]) => thermalTensorForSite(site));
  const thermalWeight = thermal.reduce((sum, [, weight]) => sum + weight, 0);
  const tensor = thermalWeight ? Array.from({ length: 3 }, (_, row) => Array.from({ length: 3 }, (_, column) =>
    thermal.reduce((sum, [site, weight]) => sum + thermalTensorForSite(site)[row][column] * weight, 0) / thermalWeight)) : null;
  const anisotropic = Boolean(first.uAnisoCartesianA2 || second.uAnisoCartesianA2);
  return { ...normalized, ...(tensor ? anisotropic ? normalizeAnisotropicDisplacement(tensor)
    : normalizeThermalDisplacement({ uIsoA2: tensor[0][0] }) : {}) };
}

function determinant(cell) {
  const [a, b, c] = cell;
  return a[0] * (b[1] * c[2] - b[2] * c[1])
    - b[0] * (a[1] * c[2] - a[2] * c[1])
    + c[0] * (a[1] * b[2] - a[2] * b[1]);
}

function fractionalToCartesian(frac, cell) {
  return [0, 1, 2].map((axis) => frac[0] * cell[0][axis] + frac[1] * cell[1][axis] + frac[2] * cell[2][axis]);
}

function inverseCell(cell) {
  const [a, b, c] = cell;
  const matrix = [
    [a[0], b[0], c[0]],
    [a[1], b[1], c[1]],
    [a[2], b[2], c[2]],
  ];
  const det = determinant(cell);
  if (Math.abs(det) < 1e-10) throw new Error("Cell vectors are singular");
  return [
    [(matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1]) / det, (matrix[0][2] * matrix[2][1] - matrix[0][1] * matrix[2][2]) / det, (matrix[0][1] * matrix[1][2] - matrix[0][2] * matrix[1][1]) / det],
    [(matrix[1][2] * matrix[2][0] - matrix[1][0] * matrix[2][2]) / det, (matrix[0][0] * matrix[2][2] - matrix[0][2] * matrix[2][0]) / det, (matrix[0][2] * matrix[1][0] - matrix[0][0] * matrix[1][2]) / det],
    [(matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0]) / det, (matrix[0][1] * matrix[2][0] - matrix[0][0] * matrix[2][1]) / det, (matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]) / det],
  ];
}

function matrixVector(matrix, vector) {
  return matrix.map((row) => row[0] * vector[0] + row[1] * vector[1] + row[2] * vector[2]);
}

function transpose(matrix) {
  return matrix[0].map((_, column) => matrix.map((row) => row[column]));
}

function matrixMultiply(first, second) {
  const transposed = transpose(second);
  return first.map((row) => transposed.map((column) => row.reduce((sum, value, index) => sum + value * column[index], 0)));
}

function cellMatrix(cell) {
  return [[cell[0][0], cell[1][0], cell[2][0]], [cell[0][1], cell[1][1], cell[2][1]], [cell[0][2], cell[1][2], cell[2][2]]];
}

function cross(first, second) {
  return [first[1] * second[2] - first[2] * second[1], first[2] * second[0] - first[0] * second[2], first[0] * second[1] - first[1] * second[0]];
}

function reciprocalAxisLengths(cell) {
  const volume = determinant(cell);
  return [cross(cell[1], cell[2]), cross(cell[2], cell[0]), cross(cell[0], cell[1])]
    .map((vector) => distance(vector) / Math.abs(volume));
}

function cifAnisotropicToCartesian(tensor, cell) {
  const lengths = reciprocalAxisLengths(cell);
  const orthogonalization = matrixMultiply(cellMatrix(cell), [
    [lengths[0], 0, 0], [0, lengths[1], 0], [0, 0, lengths[2]],
  ]);
  return matrixMultiply(matrixMultiply(orthogonalization, tensor), transpose(orthogonalization));
}

function transformCartesianTensor(tensor, fractionalRotation, cell) {
  const cartesianRotation = matrixMultiply(matrixMultiply(cellMatrix(cell), fractionalRotation), inverseCell(cell));
  return matrixMultiply(matrixMultiply(cartesianRotation, tensor), transpose(cartesianRotation));
}

export function symmetricTensorEigenSystem(tensor) {
  if (!Array.isArray(tensor) || tensor.length !== 3 || tensor.some((row) => !Array.isArray(row) || row.length !== 3
    || row.some((value) => !Number.isFinite(Number(value))))) throw new Error("Anisotropic displacement tensor must be a finite 3×3 matrix");
  const matrix = tensor.map((row) => row.map(Number));
  for (let row = 0; row < 3; row++) for (let column = row + 1; column < 3; column++) {
    if (Math.abs(matrix[row][column] - matrix[column][row]) > 1e-8) throw new Error("Anisotropic displacement tensor must be symmetric");
    const average = (matrix[row][column] + matrix[column][row]) / 2;
    matrix[row][column] = average; matrix[column][row] = average;
  }
  const vectors = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
  for (let iteration = 0; iteration < 32; iteration++) {
    let p = 0; let q = 1;
    [[0, 1], [0, 2], [1, 2]].forEach(([first, second]) => {
      if (Math.abs(matrix[first][second]) > Math.abs(matrix[p][q])) { p = first; q = second; }
    });
    if (Math.abs(matrix[p][q]) < 1e-14) break;
    const angle = .5 * Math.atan2(2 * matrix[p][q], matrix[q][q] - matrix[p][p]);
    const cosine = Math.cos(angle); const sine = Math.sin(angle);
    const rotation = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
    rotation[p][p] = cosine; rotation[q][q] = cosine;
    rotation[p][q] = sine; rotation[q][p] = -sine;
    const updated = matrixMultiply(matrixMultiply(transpose(rotation), matrix), rotation);
    for (let row = 0; row < 3; row++) for (let column = 0; column < 3; column++) matrix[row][column] = updated[row][column];
    const updatedVectors = matrixMultiply(vectors, rotation);
    for (let row = 0; row < 3; row++) for (let column = 0; column < 3; column++) vectors[row][column] = updatedVectors[row][column];
  }
  const records = [0, 1, 2].map((axis) => ({
    value: matrix[axis][axis],
    vector: vectors.map((row) => row[axis]),
  })).sort((first, second) => second.value - first.value);
  if (records.some((record) => record.value < -1e-8)) throw new Error("Anisotropic displacement tensor is not positive semidefinite");
  const handedness = records[0].vector[0] * (records[1].vector[1] * records[2].vector[2] - records[1].vector[2] * records[2].vector[1])
    - records[0].vector[1] * (records[1].vector[0] * records[2].vector[2] - records[1].vector[2] * records[2].vector[0])
    + records[0].vector[2] * (records[1].vector[0] * records[2].vector[1] - records[1].vector[1] * records[2].vector[0]);
  if (handedness < 0) records[2].vector = records[2].vector.map((value) => -value);
  return {
    eigenvaluesA2: records.map((record) => Math.max(0, record.value)),
    axes: records.map((record) => record.vector),
    sigmaAxesA: records.map((record) => Math.sqrt(Math.max(0, record.value))),
  };
}

function displacement(first, second, cell, pbc = [false, false, false]) {
  let delta = second.map((value, axis) => value - first[axis]);
  if (cell && pbc.some(Boolean)) {
    const fractional = matrixVector(inverseCell(cell), delta);
    pbc.forEach((periodic, axis) => { if (periodic) fractional[axis] -= Math.round(fractional[axis]); });
    delta = fractionalToCartesian(fractional, cell);
  }
  return delta;
}

function distance(vector) {
  return Math.hypot(...vector);
}

function cellFromParameters(a, b, c, alpha, beta, gamma) {
  const radians = (degrees) => degrees * Math.PI / 180;
  const ca = Math.cos(radians(alpha));
  const cb = Math.cos(radians(beta));
  const cg = Math.cos(radians(gamma));
  const sg = Math.sin(radians(gamma));
  if (Math.abs(sg) < 1e-8) throw new Error("CIF cell gamma angle is singular");
  const cx = c * cb;
  const cy = c * (ca - cb * cg) / sg;
  const cz = Math.sqrt(Math.max(0, c * c - cx * cx - cy * cy));
  return [[a, 0, 0], [b * cg, b * sg, 0], [cx, cy, cz]];
}

function parseFraction(value) {
  const text = String(value).trim();
  if (text.includes("/")) {
    const [top, bottom] = text.split("/");
    return numeric(top, "symmetry fraction") / numeric(bottom, "symmetry denominator");
  }
  return numeric(text, "symmetry value");
}

function parseSymmetryComponent(component) {
  const normalized = String(component).replace(/\s+/g, "").replace(/-/g, "+-");
  const coefficients = [0, 0, 0];
  let offset = 0;
  normalized.split("+").filter(Boolean).forEach((term) => {
    const variable = ["x", "y", "z"].find((candidate) => term.includes(candidate));
    if (!variable) { offset += parseFraction(term); return; }
    const coefficientText = term.replace(variable, "").replace("*", "");
    const coefficient = coefficientText === "" || coefficientText === "+" ? 1 : coefficientText === "-" ? -1 : parseFraction(coefficientText);
    coefficients[["x", "y", "z"].indexOf(variable)] += coefficient;
  });
  return { coefficients, offset };
}

function parseSymmetryOperation(operation) {
  const components = String(operation).split(",");
  if (components.length !== 3) throw new Error(`Unsupported CIF symmetry operation: ${operation}`);
  const rows = components.map(parseSymmetryComponent);
  const apply = (fractional) => rows.map((row) => row.coefficients.reduce((sum, value, index) => sum + value * fractional[index], row.offset));
  apply.rotation = rows.map((row) => row.coefficients.slice());
  return apply;
}

function parseCif(text, filename) {
  const lines = text.replace(/\r/g, "").split("\n").map((line) => line.replace(/#.*$/, "").trim()).filter(Boolean);
  const scalars = new Map();
  const loops = [];
  for (let index = 0; index < lines.length;) {
    const lower = lines[index].toLowerCase();
    if (lower === "loop_") {
      index++;
      const headers = [];
      while (index < lines.length && lines[index].startsWith("_")) headers.push(tokens(lines[index++])[0].toLowerCase());
      const values = [];
      while (index < lines.length && !lines[index].startsWith("_") && lines[index].toLowerCase() !== "loop_" && !lines[index].toLowerCase().startsWith("data_")) {
        values.push(...tokens(lines[index++]));
      }
      const rows = [];
      for (let offset = 0; offset + headers.length <= values.length; offset += headers.length) rows.push(values.slice(offset, offset + headers.length));
      loops.push({ headers, rows });
      continue;
    }
    if (lines[index].startsWith("_")) {
      const row = tokens(lines[index]);
      if (row.length >= 2) scalars.set(row[0].toLowerCase(), row.slice(1).join(" "));
      else if (index + 1 < lines.length && !lines[index + 1].startsWith("_") && lines[index + 1].toLowerCase() !== "loop_") {
        scalars.set(row[0].toLowerCase(), tokens(lines[++index]).join(" "));
      }
    }
    index++;
  }
  const get = (key, fallback = null) => scalars.get(key) ?? fallback;
  const cell = cellFromParameters(
    numeric(get("_cell_length_a"), "cell a"), numeric(get("_cell_length_b"), "cell b"), numeric(get("_cell_length_c"), "cell c"),
    numeric(get("_cell_angle_alpha", 90), "cell alpha"), numeric(get("_cell_angle_beta", 90), "cell beta"), numeric(get("_cell_angle_gamma", 90), "cell gamma"),
  );
  const atomLoop = loops.find((loop) => loop.headers.includes("_atom_site_fract_x") || loop.headers.includes("_atom_site_cartn_x"));
  if (!atomLoop) throw new Error("CIF has no supported atom-site coordinate loop");
  const atomTypeLoop = loops.find((loop) => loop.headers.includes("_atom_type_symbol")
    && loop.headers.includes("_atom_type_oxidation_number"));
  const oxidationByType = new Map();
  if (atomTypeLoop) {
    const symbolIndex = atomTypeLoop.headers.indexOf("_atom_type_symbol");
    const oxidationIndex = atomTypeLoop.headers.indexOf("_atom_type_oxidation_number");
    atomTypeLoop.rows.forEach((row) => oxidationByType.set(String(row[symbolIndex]), optionalFormalCharge(row[oxidationIndex], null)));
  }
  const column = (names) => names.map((name) => atomLoop.headers.indexOf(name)).find((index) => index >= 0) ?? -1;
  const speciesColumn = column(["_atom_site_type_symbol", "_atom_site_label"]);
  const siteLabelColumn = column(["_atom_site_label"]);
  const occupancyColumn = column(["_atom_site_occupancy"]);
  const chargeColumn = column(["_atom_site_charge"]);
  const uIsoColumn = column(["_atom_site_u_iso_or_equiv", "_atom_site_u_iso"]);
  const bIsoColumn = column(["_atom_site_b_iso_or_equiv", "_atom_site_b_iso"]);
  const fractionalColumns = ["_atom_site_fract_x", "_atom_site_fract_y", "_atom_site_fract_z"].map((name) => atomLoop.headers.indexOf(name));
  const cartesianColumns = ["_atom_site_cartn_x", "_atom_site_cartn_y", "_atom_site_cartn_z"].map((name) => atomLoop.headers.indexOf(name));
  const fractional = fractionalColumns.every((index) => index >= 0);
  if (!fractional && !cartesianColumns.every((index) => index >= 0)) throw new Error("CIF atom sites lack a complete coordinate triplet");
  const anisoLoop = loops.find((loop) => loop.headers.includes("_atom_site_aniso_label")
    && (loop.headers.includes("_atom_site_aniso_u_11") || loop.headers.includes("_atom_site_aniso_b_11")));
  const anisotropicByLabel = new Map();
  if (anisoLoop) {
    const anisoColumn = (name) => anisoLoop.headers.indexOf(name);
    const labelIndex = anisoColumn("_atom_site_aniso_label");
    anisoLoop.rows.forEach((row) => {
      const readTensor = (prefix) => {
        const read = (first, second) => {
          const index = anisoColumn(`_atom_site_aniso_${prefix}_${first}${second}`);
          return index >= 0 ? optionalCifNumber(row[index], `anisotropic ${prefix.toUpperCase()}${first}${second}`) : null;
        };
        const diagonal = [read(1, 1), read(2, 2), read(3, 3)];
        if (diagonal.some((value) => value === null)) return null;
        const u12 = read(1, 2) ?? 0; const u13 = read(1, 3) ?? 0; const u23 = read(2, 3) ?? 0;
        return [[diagonal[0], u12, u13], [u12, diagonal[1], u23], [u13, u23, diagonal[2]]];
      };
      let tensor = readTensor("u");
      let scale = 1;
      if (!tensor) { tensor = readTensor("b"); scale = 1 / (8 * Math.PI * Math.PI); }
      if (!tensor) return;
      const cartesian = cifAnisotropicToCartesian(tensor, cell).map((tensorRow) => tensorRow.map((value) => value * scale));
      anisotropicByLabel.set(String(row[labelIndex]), normalizeAnisotropicDisplacement(cartesian));
    });
  }
  const asymmetricRows = atomLoop.rows.map((row) => {
    const coordinates = (fractional ? fractionalColumns : cartesianColumns).map((index, axis) => numeric(row[index], `atom coordinate ${axis + 1}`));
    const siteLabel = siteLabelColumn >= 0 ? String(row[siteLabelColumn]) : null;
    const typeLabel = String(row[speciesColumn]);
    const formalCharge = chargeColumn >= 0 ? optionalFormalCharge(row[chargeColumn], null)
      : oxidationByType.get(typeLabel) ?? formalChargeFromLabel(typeLabel);
    const anisotropic = siteLabel ? anisotropicByLabel.get(siteLabel) : null;
    return {
      ...normalizeSiteOccupancy(typeLabel, occupancyColumn >= 0 ? row[occupancyColumn] : 1, null, formalCharge),
      ...(anisotropic || normalizeThermalDisplacement({
        uIsoA2: uIsoColumn >= 0 ? row[uIsoColumn] : null,
        bIsoA2: bIsoColumn >= 0 ? row[bIsoColumn] : null,
      })),
      siteLabels: siteLabel ? [siteLabel] : [],
      coordinates,
    };
  });
  const asymmetric = [];
  asymmetricRows.forEach((site) => {
    const existing = asymmetric.find((candidate) => distance(site.coordinates.map((value, axis) => value - candidate.coordinates[axis])) < 1e-8);
    if (!existing) { asymmetric.push(site); return; }
    const merged = mergeSiteOccupancies(existing, site, true);
    Object.assign(existing, merged, { siteLabels: [...new Set([...(existing.siteLabels || []), ...(site.siteLabels || [])])] });
  });
  const symmetryLoop = loops.find((loop) => loop.headers.includes("_space_group_symop_operation_xyz") || loop.headers.includes("_symmetry_equiv_pos_as_xyz"));
  const symmetryHeader = symmetryLoop && (symmetryLoop.headers.indexOf("_space_group_symop_operation_xyz") >= 0
    ? symmetryLoop.headers.indexOf("_space_group_symop_operation_xyz") : symmetryLoop.headers.indexOf("_symmetry_equiv_pos_as_xyz"));
  const identityOperation = (value) => value;
  identityOperation.rotation = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
  const operations = fractional && symmetryLoop ? symmetryLoop.rows.map((row) => parseSymmetryOperation(row[symmetryHeader])) : [identityOperation];
  const atoms = [];
  asymmetric.forEach((site) => operations.forEach((operation) => {
    const frac = fractional ? operation(site.coordinates).map((value) => ((value % 1) + 1) % 1) : null;
    const position = fractional ? fractionalToCartesian(frac, cell) : site.coordinates;
    const duplicate = atoms.find((atom) => distance(displacement(atom.position, position, cell, [true, true, true])) < 1e-4);
    const transformedSite = site.uAnisoCartesianA2
      ? { ...site, ...normalizeAnisotropicDisplacement(transformCartesianTensor(site.uAnisoCartesianA2, operation.rotation, cell)) }
      : site;
    if (!duplicate) {
      const { coordinates: _coordinates, ...chemistry } = transformedSite;
      atoms.push({ ...chemistry, position });
    }
    else if (occupancyChemistryToken(duplicate) !== occupancyChemistryToken(transformedSite)) {
      Object.assign(duplicate, mergeSiteOccupancies(duplicate, transformedSite, false));
    }
  }));
  return {
    name: get("_chemical_name_common", get("_chemical_formula_sum", filename.replace(/\.[^.]+$/, ""))),
    format: "CIF", atoms, cell, pbc: [true, true, true],
    metadata: {
      spaceGroup: get("_space_group_name_h-m_alt", get("_symmetry_space_group_name_h-m", "unassigned")),
      symmetryOperations: operations.length,
      measurementConditions: recordedCifMeasurementConditions(get),
    },
  };
}

function parsePoscar(text, filename) {
  const lines = text.replace(/\r/g, "").split("\n").map((line) => line.trim()).filter(Boolean);
  if (lines.length < 8) throw new Error("POSCAR is incomplete");
  const title = lines[0] || filename;
  const rawScale = numeric(lines[1], "POSCAR scale");
  const rawCell = lines.slice(2, 5).map((line, row) => tokens(line).slice(0, 3).map((value) => numeric(value, `cell vector ${row + 1}`)));
  const scale = rawScale < 0 ? Math.cbrt(Math.abs(rawScale) / Math.abs(determinant(rawCell))) : rawScale;
  const cell = rawCell.map((vector) => vector.map((value) => value * scale));
  let cursor = 5;
  let species = tokens(lines[cursor]);
  let counts;
  if (species.every((value) => /^\d+$/.test(value))) {
    counts = species.map(Number);
    species = counts.map((_, index) => `X${index + 1}`);
  } else {
    cursor++;
    counts = tokens(lines[cursor]).map((value) => Math.trunc(numeric(value, "species count")));
  }
  cursor++;
  if (/^s/i.test(lines[cursor])) cursor++;
  const direct = /^d/i.test(lines[cursor]);
  const cartesian = /^[ck]/i.test(lines[cursor]);
  if (!direct && !cartesian) throw new Error("POSCAR coordinate mode must be Direct or Cartesian");
  cursor++;
  const atoms = [];
  species.forEach((symbol, speciesIndex) => {
    for (let count = 0; count < counts[speciesIndex]; count++) {
      const row = tokens(lines[cursor++]);
      if (!row || row.length < 3) throw new Error("POSCAR contains fewer coordinates than declared");
      const coordinates = row.slice(0, 3).map((value, axis) => numeric(value, `atom coordinate ${axis + 1}`));
      const position = direct ? fractionalToCartesian(coordinates, cell) : coordinates.map((value) => value * scale);
      atoms.push({ ...normalizeSiteOccupancy(symbol, 1), position });
    }
  });
  return { name: title, format: "POSCAR", atoms, cell, pbc: [true, true, true], metadata: {} };
}

function parseXyzFrame(lines, start, filename, frameIndex) {
  let cursor = start;
  while (cursor < lines.length && !lines[cursor].trim()) cursor++;
  if (cursor >= lines.length) return null;
  const count = Math.trunc(numeric(lines[cursor]?.trim(), `XYZ frame ${frameIndex + 1} atom count`));
  if (!(count > 0)) throw new Error(`XYZ frame ${frameIndex + 1} must contain at least one atom`);
  const comment = lines[cursor + 1] || "";
  const commentName = comment
    .replace(/\b(?:Lattice|pbc|Properties)\s*=\s*(?:"[^"]*"|'[^']*'|\S+)/gi, "")
    .replace(/\s*\|\s*$/, "").trim();
  const latticeMatch = comment.match(/Lattice\s*=\s*"([^"]+)"/i);
  const latticeValues = latticeMatch ? tokens(latticeMatch[1]).map((value) => numeric(value, "XYZ lattice")) : null;
  const cell = latticeValues?.length === 9 ? [latticeValues.slice(0, 3), latticeValues.slice(3, 6), latticeValues.slice(6, 9)] : null;
  const pbcMatch = comment.match(/pbc\s*=\s*"([^"]+)"/i);
  const parsedPbc = pbcMatch ? tokens(pbcMatch[1]).map((value) => /^(t|true|1)$/i.test(value)) : [];
  const pbc = cell ? [0, 1, 2].map((axis) => Boolean(parsedPbc[axis])) : [false, false, false];
  const atoms = [];
  for (let index = 0; index < count; index++) {
    const row = tokens(lines[cursor + index + 2] || "");
    if (row.length < 4) throw new Error(`XYZ frame ${frameIndex + 1} atom row ${index + 1} is incomplete`);
    atoms.push({ ...normalizeSiteOccupancy(row[0], 1), position: row.slice(1, 4).map((value, axis) => numeric(value, `atom coordinate ${axis + 1}`)) });
  }
  return {
    frame: {
      name: commentName || `frame ${frameIndex + 1}`,
      comment,
      atoms,
      cell,
      pbc: cell ? pbc : [false, false, false],
      metadata: { frameIndex },
    },
    next: cursor + count + 2,
  };
}

function parseXyz(text, filename) {
  const lines = text.replace(/\r/g, "").split("\n");
  const frames = [];
  let cursor = 0;
  while (true) {
    const parsed = parseXyzFrame(lines, cursor, filename, frames.length);
    if (!parsed) break;
    frames.push(parsed.frame);
    cursor = parsed.next;
  }
  if (!frames.length) throw new Error("XYZ contains no frames");
  const first = frames[0];
  return {
    name: first.name || filename.replace(/\.[^.]+$/, ""),
    format: first.cell ? "extended XYZ" : "XYZ",
    atoms: first.atoms,
    cell: first.cell,
    pbc: first.pbc,
    ...(frames.length > 1 ? { frames } : {}),
    metadata: { frameCount: frames.length, frameComments: frames.map((frame) => frame.comment) },
  };
}

function jsonFrameRecord(frameValue, root, filename, frameIndex) {
  const frame = Array.isArray(frameValue) ? { positions: frameValue } : frameValue;
  if (!frame || typeof frame !== "object") throw new Error(`JSON frame ${frameIndex + 1} must be an object or position array`);
  const cell = frame.cell || frame.lattice || root.cell || root.lattice || null;
  const rawPbc = frame.pbc ?? root.pbc;
  const pbc = Array.isArray(rawPbc) ? [0, 1, 2].map((axis) => Boolean(rawPbc[axis])) : cell ? [true, true, true] : [false, false, false];
  let atoms;
  if (Array.isArray(frame.atoms)) atoms = frame.atoms.map((atom) => ({
    ...normalizeSiteOccupancy(atom.species || atom.element || atom.symbol,
      typeof atom.occupancy === "number" ? atom.occupancy : atom.occupancyTotal ?? 1,
      atom.occupancyAlternatives ?? (typeof atom.occupancy === "object" ? atom.occupancy : null),
      atom.formalCharge ?? atom.charge ?? atom.oxidationState ?? null),
    ...(atom.uAnisoCartesianA2 || atom.u_aniso_cartesian
      ? normalizeAnisotropicDisplacement(atom.uAnisoCartesianA2 || atom.u_aniso_cartesian)
      : normalizeThermalDisplacement({
      uIsoA2: atom.uIsoA2 ?? atom.u_iso_or_equiv,
      bIsoA2: atom.bIsoA2 ?? atom.b_iso_or_equiv,
      thermalSigmaA: atom.thermalSigmaA,
      })),
    position: (atom.position || atom.xyz || atom.cartesian).map(Number),
  }));
  else {
    const positions = frame.positions;
    const species = frame.species || root.species;
    if (!Array.isArray(positions) || !Array.isArray(species)) {
      throw new Error(`JSON frame ${frameIndex + 1} must contain atoms[] or positions[] with species[]`);
    }
    atoms = positions.map((position, index) => ({
    ...normalizeSiteOccupancy(species[index], Array.isArray(frame.occupancies || root.occupancies)
      ? (frame.occupancies || root.occupancies)[index] : 1,
      Array.isArray(frame.occupancyAlternatives || root.occupancyAlternatives)
        ? (frame.occupancyAlternatives || root.occupancyAlternatives)[index] : null,
      Array.isArray(frame.formalCharges || root.formalCharges)
        ? (frame.formalCharges || root.formalCharges)[index] : null),
    position: position.map(Number),
    }));
  }
  return {
    name: frame.name || `frame ${frameIndex + 1}`,
    atoms,
    cell,
    pbc,
    metadata: { ...(frame.metadata || {}), frameIndex },
  };
}

function parseJson(text, filename) {
  const data = JSON.parse(text);
  const frames = Array.isArray(data.frames) && data.frames.length
    ? data.frames.map((frame, index) => jsonFrameRecord(frame, data, filename, index))
    : [jsonFrameRecord(data, {}, filename, 0)];
  const first = frames[0];
  return {
    name: data.name || filename.replace(/\.[^.]+$/, ""),
    format: "JSON",
    atoms: first.atoms,
    cell: first.cell,
    pbc: first.pbc,
    ...(frames.length > 1 ? { frames } : {}),
    metadata: { ...(data.metadata || {}), frameCount: frames.length },
  };
}

export function parseStructureText(text, filename = "structure.xyz") {
  const lower = filename.toLowerCase();
  if (lower.endsWith(".cif")) return parseCif(text, filename);
  if (lower.endsWith(".xyz") || lower.endsWith(".extxyz")) return parseXyz(text, filename);
  if (lower.endsWith(".json")) return parseJson(text, filename);
  if (/(^|\/)(poscar|contcar)(\.[^/]*)?$/i.test(filename) || lower.endsWith(".vasp")) return parsePoscar(text, filename);
  const first = text.trimStart()[0];
  if (first === "{") return parseJson(text, filename);
  if (/^data_/im.test(text) && /_cell_length_a/i.test(text)) return parseCif(text, filename);
  if (/^\s*\d+\s*$/m.test(text.split(/\r?\n/)[0] || "")) return parseXyz(text, filename);
  return parsePoscar(text, filename);
}

export function validateStructure(structure, options = {}) {
  const errors = [];
  const warnings = [];
  const maximumAtoms = options.maximumAtoms || 1200;
  const maximumFrames = options.maximumFrames || 64;
  const maximumAtomPresentations = options.maximumAtomPresentations || 24000;
  const measurementConditions = structure?.metadata?.measurementConditions || null;
  const measurementTemperatureKelvin = measurementConditions?.temperature?.value ?? null;
  const measurementPressureKilopascal = measurementConditions?.pressure?.value ?? null;
  const measurementEnvironment = measurementConditions?.environment?.value ?? null;
  if (measurementTemperatureKelvin !== null
    && (!Number.isFinite(Number(measurementTemperatureKelvin)) || Number(measurementTemperatureKelvin) < 0)) {
    errors.push("Recorded measurement temperature must be a finite nonnegative value in kelvins");
  }
  if (measurementPressureKilopascal !== null
    && (!Number.isFinite(Number(measurementPressureKilopascal)) || Number(measurementPressureKilopascal) < 0)) {
    errors.push("Recorded measurement pressure must be a finite nonnegative value in kilopascals");
  }
  if (measurementEnvironment !== null && (typeof measurementEnvironment !== "string" || measurementEnvironment.length > 240)) {
    errors.push("Recorded measurement environment must be text of at most 240 characters");
  }
  if (!structure?.atoms?.length) errors.push("No atoms were parsed");
  if (structure?.atoms?.length > maximumAtoms) errors.push(`${structure.atoms.length} atoms exceed the browser analysis limit of ${maximumAtoms}`);
  const trajectoryFrames = structure?.frames?.length ? structure.frames : [];
  const trajectoryFrameCount = trajectoryFrames.length || 1;
  const trajectoryAtomPresentations = trajectoryFrameCount * (structure?.atoms?.length || 0);
  let trajectoryTopologyConsistent = true;
  let trajectoryVariableCell = false;
  if (trajectoryFrameCount > maximumFrames) errors.push(`${trajectoryFrameCount} frames exceed the browser ensemble limit of ${maximumFrames}`);
  if (trajectoryAtomPresentations > maximumAtomPresentations) errors.push(`${trajectoryAtomPresentations} atom presentations exceed the browser ensemble limit of ${maximumAtomPresentations}`);
  if (trajectoryFrames.length) {
    const referenceTokens = trajectoryFrames[0].atoms.map(occupancyChemistryToken);
    const referenceCell = JSON.stringify(trajectoryFrames[0].cell || null);
    trajectoryFrames.forEach((frame, frameIndex) => {
      const tokensForFrame = frame.atoms.map(occupancyChemistryToken);
      if (tokensForFrame.length !== referenceTokens.length
        || tokensForFrame.some((token, index) => token !== referenceTokens[index])) {
        trajectoryTopologyConsistent = false;
        errors.push(`Trajectory frame ${frameIndex + 1} changes atom count, order, species, occupancy, or formal charge`);
      }
      if (frame.atoms.some((atom) => !Array.isArray(atom.position) || atom.position.length !== 3
        || atom.position.some((value) => !Number.isFinite(Number(value))))) {
        errors.push(`Trajectory frame ${frameIndex + 1} has invalid Cartesian coordinates`);
      }
      if (frame.cell && (!Array.isArray(frame.cell) || frame.cell.length !== 3
        || frame.cell.some((vector) => !Array.isArray(vector) || vector.length !== 3
          || vector.some((value) => !Number.isFinite(Number(value))))
        || Math.abs(determinant(frame.cell)) < 1e-6)) {
        errors.push(`Trajectory frame ${frameIndex + 1} has an invalid cell`);
      }
      if (frame.pbc?.some(Boolean) && !frame.cell) errors.push(`Trajectory frame ${frameIndex + 1} has periodic axes without a cell`);
      trajectoryVariableCell ||= JSON.stringify(frame.cell || null) !== referenceCell;
    });
    warnings.push(`${trajectoryFrameCount} trajectory frames retained with fixed atom identity${trajectoryVariableCell ? " and variable cells" : ""}`);
  }
  if (structure?.cell) {
    if (!Array.isArray(structure.cell) || structure.cell.length !== 3 || structure.cell.some((vector) => !Array.isArray(vector) || vector.length !== 3 || vector.some((value) => !Number.isFinite(Number(value))))) errors.push("Cell must contain three finite 3D vectors");
    else if (Math.abs(determinant(structure.cell)) < 1e-6) errors.push("Cell vectors are singular or nearly singular");
  } else if (structure?.pbc?.some(Boolean)) errors.push("Periodic axes require cell vectors");
  const elementCounts = {};
  const siteElementCounts = {};
  let mixedOccupancySites = 0;
  let partialOccupancySites = 0;
  let inferredOccupancySites = 0;
  let vacancyFraction = 0;
  const thermalSigmas = [];
  const thermalAxisSigmas = [];
  let anisotropicDisplacementSites = 0;
  let formalChargeKnownOccupancy = 0;
  let totalOccupiedFraction = 0;
  let netFormalCharge = 0;
  let chargeResolvedSites = 0;
  structure?.atoms?.forEach((atom, index) => {
    let normalized = null;
    try {
      normalized = normalizeSiteOccupancy(atom.species, atom.occupancy ?? atom.occupancyTotal ?? 1,
        atom.occupancyAlternatives ?? (typeof atom.occupancy === "object" ? atom.occupancy : null),
        atom.formalCharge ?? atom.charge ?? atom.oxidationState ?? null);
    } catch (error) {
      errors.push(`Atom ${index + 1}: ${error.message}`);
    }
    if (!normalized || normalized.occupancyAlternatives.some((entry) => !/^[A-Z][a-z]?$/.test(entry.species))) {
      errors.push(`Atom ${index + 1} has an invalid occupational element symbol`);
    }
    if (!Array.isArray(atom.position) || atom.position.length !== 3 || atom.position.some((value) => !Number.isFinite(Number(value)))) errors.push(`Atom ${index + 1} has invalid Cartesian coordinates`);
    normalized?.occupancyAlternatives.forEach((entry) => {
      elementCounts[entry.species] = (elementCounts[entry.species] || 0) + entry.fraction;
      siteElementCounts[entry.species] = (siteElementCounts[entry.species] || 0) + 1;
      totalOccupiedFraction += entry.fraction;
      if (entry.formalCharge !== null) {
        formalChargeKnownOccupancy += entry.fraction;
        netFormalCharge += entry.fraction * entry.formalCharge;
      }
    });
    if (normalized && normalized.formalChargeKnownFraction >= normalized.occupancyTotal - 1e-8) chargeResolvedSites++;
    if (normalized?.occupancyAlternatives.length > 1) mixedOccupancySites++;
    if (normalized && normalized.occupancyTotal < .999999) {
      partialOccupancySites++;
      vacancyFraction += 1 - normalized.occupancyTotal;
    }
    if (atom.occupancyFractionsInferred) inferredOccupancySites++;
    try {
      const thermal = normalizeThermalDisplacement(atom);
      if (Number.isFinite(thermal.thermalSigmaA)) thermalSigmas.push(thermal.thermalSigmaA);
      if (atom.uAnisoCartesianA2) {
        const eigen = symmetricTensorEigenSystem(atom.uAnisoCartesianA2);
        anisotropicDisplacementSites++;
        thermalAxisSigmas.push(...eigen.sigmaAxesA);
      }
    } catch (error) {
      errors.push(`Atom ${index + 1}: ${error.message}`);
    }
  });
  if (mixedOccupancySites) warnings.push(`${mixedOccupancySites} mixed-occupancy crystallographic site${mixedOccupancySites === 1 ? "" : "s"} preserved as occupational alternatives`);
  if (partialOccupancySites) warnings.push(`${partialOccupancySites} partially occupied site${partialOccupancySites === 1 ? "" : "s"} preserve explicit vacancy fractions`);
  if (inferredOccupancySites) warnings.push(`${inferredOccupancySites} composite species label${inferredOccupancySites === 1 ? "" : "s"} lacked explicit fractions; equal alternatives were retained and marked inferred`);
  if (thermalSigmas.length) warnings.push(`${thermalSigmas.length} site${thermalSigmas.length === 1 ? "" : "s"} preserve positional uncertainty from isotropic or equivalent U/B`);
  if (anisotropicDisplacementSites) warnings.push(`${anisotropicDisplacementSites} site${anisotropicDisplacementSites === 1 ? "" : "s"} preserve full Cartesian anisotropic displacement tensors`);
  const formalChargeCoverage = formalChargeKnownOccupancy / Math.max(totalOccupiedFraction, 1e-12);
  if (formalChargeKnownOccupancy > 0) warnings.push(`Formal oxidation-state coverage is ${(formalChargeCoverage * 100).toFixed(1)}%; net supplied-cell formal charge ${netFormalCharge >= 0 ? "+" : ""}${Number(netFormalCharge.toFixed(6))}`);
  if (formalChargeCoverage >= .999999 && Math.abs(netFormalCharge) > 1e-5) warnings.push("Fully charge-resolved supplied cell is not formally neutral; this is retained as input evidence, not corrected");
  if (measurementConditions) {
    const recorded = [
      measurementTemperatureKelvin !== null ? `${Number(measurementTemperatureKelvin)} K` : null,
      measurementPressureKilopascal !== null ? `${Number(measurementPressureKilopascal)} kPa` : null,
      measurementEnvironment ? String(measurementEnvironment) : null,
    ].filter(Boolean).join(" · ");
    warnings.push(`Recorded measurement conditions retained as provenance only${recorded ? `: ${recorded}` : ""}`);
  }
  let minimumDistance = Infinity;
  let duplicatePairs = 0;
  const nearest = [];
  if (!errors.length) {
    for (let first = 0; first < structure.atoms.length; first++) {
      let nearestDistance = Infinity;
      for (let second = 0; second < structure.atoms.length; second++) {
        if (first === second) continue;
        const pairDistance = distance(displacement(structure.atoms[first].position, structure.atoms[second].position, structure.cell, structure.pbc));
        nearestDistance = Math.min(nearestDistance, pairDistance);
        if (second > first) {
          minimumDistance = Math.min(minimumDistance, pairDistance);
          if (pairDistance < .1) duplicatePairs++;
        }
      }
      if (Number.isFinite(nearestDistance)) nearest.push(nearestDistance);
    }
  }
  if (duplicatePairs) errors.push(`${duplicatePairs} atom pair${duplicatePairs === 1 ? "" : "s"} are closer than 0.1 Å`);
  if (structure?.atoms?.length < 16) warnings.push("Fewer than 16 atoms: environment clustering and growth rules will be poorly constrained");
  if (!structure?.cell) warnings.push("No cell supplied: the structure will be treated as non-periodic");
  const sortedNearest = nearest.sort((a, b) => a - b);
  const medianNearestDistance = sortedNearest[Math.floor(sortedNearest.length / 2)] || 1;
  thermalSigmas.sort((first, second) => first - second);
  const medianThermalSigmaA = thermalSigmas[Math.floor(thermalSigmas.length / 2)] || 0;
  return {
    valid: errors.length === 0, errors: [...new Set(errors)], warnings: [...new Set(warnings)],
    atomCount: structure?.atoms?.length || 0, elementCounts, siteElementCounts,
    mixedOccupancySites, partialOccupancySites, inferredOccupancySites, vacancyFraction,
    thermalDisplacementSites: thermalSigmas.length, medianThermalSigmaA,
    maximumThermalSigmaA: thermalSigmas.at(-1) || 0,
    anisotropicDisplacementSites,
    maximumThermalAxisSigmaA: Math.max(0, ...thermalAxisSigmas),
    formalChargeCoverage, chargeResolvedSites,
    netFormalCharge,
    trajectoryFrameCount, trajectoryTopologyConsistent, trajectoryVariableCell,
    trajectoryAtomPresentations,
    measurementConditionsPresent: Boolean(measurementConditions),
    measurementTemperatureKelvin: measurementTemperatureKelvin === null ? null : Number(measurementTemperatureKelvin),
    measurementPressureKilopascal: measurementPressureKilopascal === null ? null : Number(measurementPressureKilopascal),
    measurementEnvironment,
    minimumDistance: Number.isFinite(minimumDistance) ? minimumDistance : null,
    medianNearestDistance, cellVolume: structure?.cell ? Math.abs(determinant(structure.cell)) : null,
  };
}

export { displacement, fractionalToCartesian };
