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
  const parts = text.split(/[\/|,+]/).map((part) => part.trim()).filter(Boolean);
  const matches = (parts.length > 1 ? parts : [text]).map((part) => part.match(/[A-Z][a-z]?/)?.[0]).filter(Boolean);
  return [...new Set(matches.length ? matches : ["X"])];
}

function elementSymbol(value) {
  return elementSymbols(value)[0];
}

const occupancyFraction = (value, fallback = null) => {
  if (value === undefined || value === null || value === "" || value === "." || value === "?") return fallback;
  const fraction = numeric(value, "occupancy");
  if (!(fraction >= 0 && fraction <= 1 + 1e-8)) throw new Error(`Occupancy must lie between 0 and 1: ${value}`);
  return Math.max(0, Math.min(1, fraction));
};

const optionalCifNumber = (value, label) => value === undefined || value === null || value === "" || value === "." || value === "?"
  ? null : numeric(value, label);

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

function occupancyEntries(value) {
  if (Array.isArray(value)) return value.map((entry) => typeof entry === "string"
    ? { species: elementSymbol(entry), fraction: null }
    : { species: elementSymbol(entry.species || entry.element || entry.symbol),
      fraction: occupancyFraction(entry.fraction ?? entry.occupancy, null) });
  if (value && typeof value === "object") return Object.entries(value)
    .map(([species, fraction]) => ({ species: elementSymbol(species), fraction: occupancyFraction(fraction, null) }));
  return [];
}

export function normalizeSiteOccupancy(speciesValue, occupancyValue = 1, alternativesValue = null) {
  const labelSpecies = elementSymbols(speciesValue);
  const explicit = occupancyEntries(alternativesValue);
  let entries = explicit.length ? explicit : labelSpecies.map((species) => ({ species, fraction: null }));
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
  }));
  const combined = new Map();
  entries.forEach(({ species, fraction }) => combined.set(species, (combined.get(species) || 0) + fraction));
  const alternatives = [...combined.entries()].filter(([, fraction]) => fraction > 1e-10)
    .map(([species, fraction]) => ({ species, fraction }))
    .sort((first, second) => second.fraction - first.fraction || first.species.localeCompare(second.species));
  const total = alternatives.reduce((sum, entry) => sum + entry.fraction, 0);
  if (!alternatives.length || total <= 0) throw new Error("A crystallographic site must have positive occupancy");
  if (total > 1 + 1e-8) throw new Error(`Occupational alternatives sum to ${total.toFixed(6)}, above 1`);
  return {
    species: alternatives[0].species,
    occupancy: total,
    occupancyTotal: total,
    occupancyAlternatives: alternatives,
    occupancyFractionsInferred: !explicit.length && labelSpecies.length > 1,
  };
}

const compactFraction = (value) => Number(value.toFixed(8)).toString();

export function occupancyChemistryToken(atom) {
  const normalized = normalizeSiteOccupancy(atom?.species, atom?.occupancy ?? atom?.occupancyTotal ?? 1,
    atom?.occupancyAlternatives ?? (Array.isArray(atom?.occupancy) || (atom?.occupancy && typeof atom.occupancy === "object") ? atom.occupancy : null));
  if (normalized.occupancyAlternatives.length === 1 && Math.abs(normalized.occupancyTotal - 1) < 1e-8) {
    return normalized.occupancyAlternatives[0].species;
  }
  const entries = normalized.occupancyAlternatives
    .slice().sort((first, second) => first.species.localeCompare(second.species))
    .map((entry) => `${entry.species}=${compactFraction(entry.fraction)}`);
  const vacancy = Math.max(0, 1 - normalized.occupancyTotal);
  if (vacancy > 1e-8) entries.push(`Vac=${compactFraction(vacancy)}`);
  return `occ[${entries.join(";")}]`;
}

export function occupancyDisplayLabel(atom) {
  const normalized = normalizeSiteOccupancy(atom?.species, atom?.occupancy ?? atom?.occupancyTotal ?? 1,
    atom?.occupancyAlternatives ?? (Array.isArray(atom?.occupancy) || (atom?.occupancy && typeof atom.occupancy === "object") ? atom.occupancy : null));
  const entries = normalized.occupancyAlternatives.map((entry) => `${entry.species} ${Math.round(entry.fraction * 1000) / 10}%`);
  const vacancy = Math.max(0, 1 - normalized.occupancyTotal);
  if (vacancy > 1e-8) entries.push(`vacancy ${Math.round(vacancy * 1000) / 10}%`);
  return entries.join(" / ");
}

export function isotropicPairDistanceUncertaintyA(oneAxisSigmaA) {
  const sigma = Number(oneAxisSigmaA);
  if (!Number.isFinite(sigma) || sigma < 0) throw new Error("Isotropic site sigma must be a finite nonnegative length");
  return Math.SQRT2 * sigma;
}

function mergeSiteOccupancies(first, second, additive) {
  const fractions = new Map(first.occupancyAlternatives.map((entry) => [entry.species, entry.fraction]));
  second.occupancyAlternatives.forEach((entry) => fractions.set(entry.species, additive
    ? (fractions.get(entry.species) || 0) + entry.fraction
    : Math.max(fractions.get(entry.species) || 0, entry.fraction)));
  const normalized = normalizeSiteOccupancy(first.species, 1,
    [...fractions].map(([species, fraction]) => ({ species, fraction })));
  const thermal = [[first, first.occupancyTotal ?? first.occupancy ?? 1], [second, second.occupancyTotal ?? second.occupancy ?? 1]]
    .filter(([site]) => Number.isFinite(site.uIsoA2));
  const thermalWeight = thermal.reduce((sum, [, weight]) => sum + weight, 0);
  const uIsoA2 = thermalWeight ? thermal.reduce((sum, [site, weight]) => sum + site.uIsoA2 * weight, 0) / thermalWeight : null;
  return { ...normalized, ...normalizeThermalDisplacement({ uIsoA2 }) };
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
  return (fractional) => rows.map((row) => row.coefficients.reduce((sum, value, index) => sum + value * fractional[index], row.offset));
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
  const column = (names) => names.map((name) => atomLoop.headers.indexOf(name)).find((index) => index >= 0) ?? -1;
  const speciesColumn = column(["_atom_site_type_symbol", "_atom_site_label"]);
  const occupancyColumn = column(["_atom_site_occupancy"]);
  const uIsoColumn = column(["_atom_site_u_iso_or_equiv", "_atom_site_u_iso"]);
  const bIsoColumn = column(["_atom_site_b_iso_or_equiv", "_atom_site_b_iso"]);
  const fractionalColumns = ["_atom_site_fract_x", "_atom_site_fract_y", "_atom_site_fract_z"].map((name) => atomLoop.headers.indexOf(name));
  const cartesianColumns = ["_atom_site_cartn_x", "_atom_site_cartn_y", "_atom_site_cartn_z"].map((name) => atomLoop.headers.indexOf(name));
  const fractional = fractionalColumns.every((index) => index >= 0);
  if (!fractional && !cartesianColumns.every((index) => index >= 0)) throw new Error("CIF atom sites lack a complete coordinate triplet");
  const asymmetricRows = atomLoop.rows.map((row) => {
    const coordinates = (fractional ? fractionalColumns : cartesianColumns).map((index, axis) => numeric(row[index], `atom coordinate ${axis + 1}`));
    return {
      ...normalizeSiteOccupancy(row[speciesColumn], occupancyColumn >= 0 ? row[occupancyColumn] : 1),
      ...normalizeThermalDisplacement({
        uIsoA2: uIsoColumn >= 0 ? row[uIsoColumn] : null,
        bIsoA2: bIsoColumn >= 0 ? row[bIsoColumn] : null,
      }),
      coordinates,
    };
  });
  const asymmetric = [];
  asymmetricRows.forEach((site) => {
    const existing = asymmetric.find((candidate) => distance(site.coordinates.map((value, axis) => value - candidate.coordinates[axis])) < 1e-8);
    if (!existing) { asymmetric.push(site); return; }
    Object.assign(existing, mergeSiteOccupancies(existing, site, true));
  });
  const symmetryLoop = loops.find((loop) => loop.headers.includes("_space_group_symop_operation_xyz") || loop.headers.includes("_symmetry_equiv_pos_as_xyz"));
  const symmetryHeader = symmetryLoop && (symmetryLoop.headers.indexOf("_space_group_symop_operation_xyz") >= 0
    ? symmetryLoop.headers.indexOf("_space_group_symop_operation_xyz") : symmetryLoop.headers.indexOf("_symmetry_equiv_pos_as_xyz"));
  const operations = fractional && symmetryLoop ? symmetryLoop.rows.map((row) => parseSymmetryOperation(row[symmetryHeader])) : [(value) => value];
  const atoms = [];
  asymmetric.forEach((site) => operations.forEach((operation) => {
    const frac = fractional ? operation(site.coordinates).map((value) => ((value % 1) + 1) % 1) : null;
    const position = fractional ? fractionalToCartesian(frac, cell) : site.coordinates;
    const duplicate = atoms.find((atom) => distance(displacement(atom.position, position, cell, [true, true, true])) < 1e-4);
    if (!duplicate) {
      const { coordinates: _coordinates, ...chemistry } = site;
      atoms.push({ ...chemistry, position });
    }
    else if (occupancyChemistryToken(duplicate) !== occupancyChemistryToken(site)) {
      Object.assign(duplicate, mergeSiteOccupancies(duplicate, site, false));
    }
  }));
  return {
    name: get("_chemical_name_common", get("_chemical_formula_sum", filename.replace(/\.[^.]+$/, ""))),
    format: "CIF", atoms, cell, pbc: [true, true, true],
    metadata: { spaceGroup: get("_space_group_name_h-m_alt", get("_symmetry_space_group_name_h-m", "unassigned")), symmetryOperations: operations.length },
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

function parseXyz(text, filename) {
  const lines = text.replace(/\r/g, "").split("\n");
  const count = Math.trunc(numeric(lines[0]?.trim(), "XYZ atom count"));
  const comment = lines[1] || "";
  const commentName = comment
    .replace(/\b(?:Lattice|pbc|Properties)\s*=\s*(?:"[^"]*"|'[^']*'|\S+)/gi, "")
    .replace(/\s*\|\s*$/, "").trim();
  const latticeMatch = comment.match(/Lattice\s*=\s*"([^"]+)"/i);
  const latticeValues = latticeMatch ? tokens(latticeMatch[1]).map((value) => numeric(value, "XYZ lattice")) : null;
  const cell = latticeValues?.length === 9 ? [latticeValues.slice(0, 3), latticeValues.slice(3, 6), latticeValues.slice(6, 9)] : null;
  const pbcMatch = comment.match(/pbc\s*=\s*"([^"]+)"/i);
  const pbc = pbcMatch ? tokens(pbcMatch[1]).map((value) => /^(t|true|1)$/i.test(value)).slice(0, 3) : [false, false, false];
  const atoms = [];
  for (let index = 0; index < count; index++) {
    const row = tokens(lines[index + 2] || "");
    if (row.length < 4) throw new Error(`XYZ atom row ${index + 1} is incomplete`);
    atoms.push({ ...normalizeSiteOccupancy(row[0], 1), position: row.slice(1, 4).map((value, axis) => numeric(value, `atom coordinate ${axis + 1}`)) });
  }
  return { name: commentName || filename.replace(/\.[^.]+$/, ""), format: cell ? "extended XYZ" : "XYZ", atoms, cell, pbc: cell ? pbc : [false, false, false], metadata: {} };
}

function parseJson(text, filename) {
  const data = JSON.parse(text);
  const cell = data.cell || data.lattice || null;
  const pbc = Array.isArray(data.pbc) ? data.pbc.map(Boolean).slice(0, 3) : cell ? [true, true, true] : [false, false, false];
  let atoms;
  if (Array.isArray(data.atoms)) atoms = data.atoms.map((atom) => ({
    ...normalizeSiteOccupancy(atom.species || atom.element || atom.symbol,
      typeof atom.occupancy === "number" ? atom.occupancy : atom.occupancyTotal ?? 1,
      atom.occupancyAlternatives ?? (typeof atom.occupancy === "object" ? atom.occupancy : null)),
    ...normalizeThermalDisplacement({
      uIsoA2: atom.uIsoA2 ?? atom.u_iso_or_equiv,
      bIsoA2: atom.bIsoA2 ?? atom.b_iso_or_equiv,
      thermalSigmaA: atom.thermalSigmaA,
    }),
    position: (atom.position || atom.xyz || atom.cartesian).map(Number),
  }));
  else if (Array.isArray(data.positions) && Array.isArray(data.species)) atoms = data.positions.map((position, index) => ({
    ...normalizeSiteOccupancy(data.species[index], Array.isArray(data.occupancies) ? data.occupancies[index] : 1),
    position: position.map(Number),
  }));
  else throw new Error("JSON must contain atoms[] or parallel positions[] and species[] arrays");
  return { name: data.name || filename.replace(/\.[^.]+$/, ""), format: "JSON", atoms, cell, pbc, metadata: data.metadata || {} };
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
  if (!structure?.atoms?.length) errors.push("No atoms were parsed");
  if (structure?.atoms?.length > maximumAtoms) errors.push(`${structure.atoms.length} atoms exceed the browser analysis limit of ${maximumAtoms}`);
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
  structure?.atoms?.forEach((atom, index) => {
    let normalized = null;
    try {
      normalized = normalizeSiteOccupancy(atom.species, atom.occupancy ?? atom.occupancyTotal ?? 1,
        atom.occupancyAlternatives ?? (typeof atom.occupancy === "object" ? atom.occupancy : null));
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
    });
    if (normalized?.occupancyAlternatives.length > 1) mixedOccupancySites++;
    if (normalized && normalized.occupancyTotal < .999999) {
      partialOccupancySites++;
      vacancyFraction += 1 - normalized.occupancyTotal;
    }
    if (atom.occupancyFractionsInferred) inferredOccupancySites++;
    try {
      const thermal = normalizeThermalDisplacement(atom);
      if (Number.isFinite(thermal.thermalSigmaA)) thermalSigmas.push(thermal.thermalSigmaA);
    } catch (error) {
      errors.push(`Atom ${index + 1}: ${error.message}`);
    }
  });
  if (mixedOccupancySites) warnings.push(`${mixedOccupancySites} mixed-occupancy crystallographic site${mixedOccupancySites === 1 ? "" : "s"} preserved as occupational alternatives`);
  if (partialOccupancySites) warnings.push(`${partialOccupancySites} partially occupied site${partialOccupancySites === 1 ? "" : "s"} preserve explicit vacancy fractions`);
  if (inferredOccupancySites) warnings.push(`${inferredOccupancySites} composite species label${inferredOccupancySites === 1 ? "" : "s"} lacked explicit fractions; equal alternatives were retained and marked inferred`);
  if (thermalSigmas.length) warnings.push(`${thermalSigmas.length} site${thermalSigmas.length === 1 ? "" : "s"} preserve isotropic positional uncertainty from Uiso/Biso`);
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
    minimumDistance: Number.isFinite(minimumDistance) ? minimumDistance : null,
    medianNearestDistance, cellVolume: structure?.cell ? Math.abs(determinant(structure.cell)) : null,
  };
}

export { displacement, fractionalToCartesian };
