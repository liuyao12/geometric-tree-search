const NOMAD_API = "https://nomad-lab.eu/prod/v1/api/v1";
const ELEMENT_PATTERN = /^(?:H|He|Li|Be|B|C|N|O|F|Ne|Na|Mg|Al|Si|P|S|Cl|Ar|K|Ca|Sc|Ti|V|Cr|Mn|Fe|Co|Ni|Cu|Zn|Ga|Ge|As|Se|Br|Kr|Rb|Sr|Y|Zr|Nb|Mo|Tc|Ru|Rh|Pd|Ag|Cd|In|Sn|Sb|Te|I|Xe|Cs|Ba|La|Ce|Pr|Nd|Pm|Sm|Eu|Gd|Tb|Dy|Ho|Er|Tm|Yb|Lu|Hf|Ta|W|Re|Os|Ir|Pt|Au|Hg|Tl|Pb|Bi|Po|At|Rn|Fr|Ra|Ac|Th|Pa|U|Np|Pu|Am|Cm|Bk|Cf|Es|Fm|Md|No|Lr|Rf|Db|Sg|Bh|Hs|Mt|Ds|Rg|Cn|Nh|Fl|Mc|Lv|Ts|Og)$/;
const ATOMIC_SYMBOLS = " H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og".split(" ");

function canonicalElement(value) {
  const text = String(value || "").trim();
  const symbol = text ? text[0].toUpperCase() + text.slice(1).toLowerCase() : "";
  if (!ELEMENT_PATTERN.test(symbol)) throw new Error(`Unknown element symbol: ${value || "(blank)"}`);
  return symbol;
}

function queryPayload(first, second, pageOffset = 0) {
  return {
    owner: "public",
    query: {
      and: [
        { "results.material.elements": { all: [first, second] } },
        { "results.material.n_elements": 2 },
        { "results.material.structural_type": "bulk" },
      ],
    },
    pagination: { page_size: 1, page_offset: pageOffset },
    required: {
      include: [
        "entry_id",
        "results.material.material_id",
        "results.material.chemical_formula_reduced",
        "results.material.elements",
        "results.material.symmetry.crystal_system",
        "results.material.symmetry.space_group_number",
        "results.material.symmetry.space_group_symbol",
      ],
    },
  };
}

async function postJson(url, body, fetchImpl = fetch) {
  const response = await fetchImpl(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`NOMAD returned ${response.status}${detail ? `: ${detail.slice(0, 180)}` : ""}`);
  }
  return response.json();
}

function randomIndex(limit, random = Math.random) {
  return Math.max(0, Math.min(limit - 1, Math.floor(random() * limit)));
}

function vectorLength(vector) {
  return Math.hypot(...vector);
}

export function makeLearningSupercell(structure, options = {}) {
  const minimumAtoms = options.minimumAtoms || 128;
  const maximumAtoms = options.maximumAtoms || 512;
  if (!structure.cell || !structure.pbc?.every(Boolean) || structure.atoms.length >= minimumAtoms) {
    return { ...structure, metadata: { ...structure.metadata, repetitions: [1, 1, 1], primitiveAtomCount: structure.atoms.length } };
  }
  const repetitions = [1, 1, 1];
  while (structure.atoms.length * repetitions.reduce((product, value) => product * value, 1) < minimumAtoms) {
    let axis = 0;
    for (let candidate = 1; candidate < 3; candidate++) {
      if (vectorLength(structure.cell[candidate]) * repetitions[candidate] < vectorLength(structure.cell[axis]) * repetitions[axis]) axis = candidate;
    }
    repetitions[axis]++;
    if (structure.atoms.length * repetitions.reduce((product, value) => product * value, 1) > maximumAtoms) {
      repetitions[axis]--;
      break;
    }
  }
  const atoms = [];
  for (let i = 0; i < repetitions[0]; i++) for (let j = 0; j < repetitions[1]; j++) for (let k = 0; k < repetitions[2]; k++) {
    const shift = [0, 1, 2].map((axis) => i * structure.cell[0][axis] + j * structure.cell[1][axis] + k * structure.cell[2][axis]);
    structure.atoms.forEach((atom) => atoms.push({
      ...atom,
      position: atom.position.map((value, axis) => value + shift[axis]),
    }));
  }
  return {
    ...structure,
    atoms,
    cell: structure.cell.map((vector, axis) => vector.map((value) => value * repetitions[axis])),
    metadata: { ...structure.metadata, repetitions, primitiveAtomCount: structure.atoms.length },
  };
}

export function nomadArchiveToStructure(entry, archiveResponse) {
  const archive = archiveResponse?.data?.archive;
  const systems = (archive?.run || []).flatMap((run) => run.system || []);
  const atomsData = [...systems].reverse().map((system) => system.atoms).find((atoms) =>
    atoms?.positions?.length && atoms?.lattice_vectors?.length === 3);
  if (!atomsData) throw new Error("The selected NOMAD archive has no normalized periodic atomic system");
  const labels = atomsData.labels || [];
  if (labels.length !== atomsData.positions.length) throw new Error("NOMAD returned inconsistent atom labels and positions");
  const symbols = labels.map((label, index) => {
    try { return canonicalElement(label); }
    catch {
      const atomicNumber = Number(atomsData.species?.[index]);
      if (Number.isInteger(atomicNumber) && ATOMIC_SYMBOLS[atomicNumber]) return ATOMIC_SYMBOLS[atomicNumber];
      throw new Error(`NOMAD atom ${index + 1} has an unsupported species label: ${label}`);
    }
  });
  const material = entry.results?.material || {};
  const symmetry = material.symmetry || {};
  const entryId = entry.entry_id;
  const sourceUrl = `https://nomad-lab.eu/prod/v1/gui/search/entries/entry/id/${encodeURIComponent(entryId)}`;
  return {
    name: material.chemical_formula_reduced || `NOMAD ${entryId.slice(0, 8)}`,
    format: "NOMAD archive",
    atoms: atomsData.positions.map((position, index) => ({
      species: symbols[index], position: position.map((value) => value * 1e10), occupancy: 1,
    })),
    cell: atomsData.lattice_vectors.map((vector) => vector.map((value) => value * 1e10)),
    pbc: atomsData.periodic?.map(Boolean) || [true, true, true],
    metadata: {
      source: "NOMAD",
      entryId,
      materialId: material.material_id,
      sourceUrl,
      formula: material.chemical_formula_reduced,
      crystalSystem: symmetry.crystal_system,
      spaceGroupNumber: symmetry.space_group_number,
      spaceGroup: symmetry.space_group_symbol || "unassigned",
    },
  };
}

export async function randomNomadBinary(firstValue, secondValue, options = {}) {
  const first = canonicalElement(firstValue);
  const second = canonicalElement(secondValue);
  if (first === second) throw new Error("Choose two different elements");
  const fetchImpl = options.fetchImpl || fetch;
  const initial = await postJson(`${NOMAD_API}/entries/query`, queryPayload(first, second), fetchImpl);
  const total = Number(initial.pagination?.total || 0);
  if (!total) throw new Error(`NOMAD has no public bulk entries containing only ${first} and ${second}`);
  const accessibleTotal = Math.min(total, 10_000);
  const attempts = Math.min(8, accessibleTotal);
  const triedOffsets = new Set();
  let lastError = null;
  for (let attempt = 0; attempt < attempts; attempt++) {
    let offset = randomIndex(accessibleTotal, options.random);
    while (triedOffsets.has(offset) && triedOffsets.size < accessibleTotal) offset = (offset + 1) % accessibleTotal;
    triedOffsets.add(offset);
    const page = offset === 0 ? initial : await postJson(`${NOMAD_API}/entries/query`, queryPayload(first, second, offset), fetchImpl);
    const entry = page.data?.[0];
    if (!entry) continue;
    try {
      const archive = await postJson(`${NOMAD_API}/entries/${encodeURIComponent(entry.entry_id)}/archive/query`, {
        required: { run: { "system[-1]": { atoms: "*" } } },
      }, fetchImpl);
      const primitive = nomadArchiveToStructure(entry, archive);
      if (primitive.atoms.length > 512) throw new Error(`archive contains ${primitive.atoms.length} atoms before expansion`);
      const structure = makeLearningSupercell(primitive);
      return { structure, total, selectedOffset: offset };
    } catch (error) {
      lastError = error;
    }
  }
  throw new Error(`No usable periodic archive found after ${attempts} random samples${lastError ? `: ${lastError.message}` : ""}`);
}

export { canonicalElement, queryPayload };
