const NOMAD_API = "https://nomad-lab.eu/prod/v1/api/v1";
const JOULE_PER_ELECTRON_VOLT = 1.602176634e-19;
const NEWTON_PER_ELECTRON_VOLT_PER_ANGSTROM = 1.602176634e-9;
const MAX_NOMAD_RELAXATION_FRAMES = 24;
const MAX_NOMAD_RESPONSE_BYTES = 32 * 1024 * 1024;
export const NOMAD_EVIDENCE_TARGETS = Object.freeze({
  geometry: Object.freeze({ id: "geometry", label: "geometry · any usable periodic archive" }),
  relaxation: Object.freeze({ id: "relaxation", label: "relaxation series · at least 3 fixed-topology snapshots" }),
  forces: Object.freeze({ id: "forces", label: "force-labelled geometry · complete forces on at least 1 snapshot" }),
  calibration: Object.freeze({ id: "calibration", label: "surrogate-ready series · at least 5 paired calculation snapshots" }),
});
export const NOMAD_STRUCTURE_FAMILIES = Object.freeze({
  bulk: Object.freeze({ id: "bulk", label: "3D bulk solid", structuralType: "bulk", fixedElements: null, formula: null }),
  twoD: Object.freeze({ id: "twoD", label: "intrinsic 2D / layered material", structuralType: "2D", fixedElements: null, formula: null }),
  water: Object.freeze({ id: "water", label: "crystalline H₂O family", structuralType: "bulk", fixedElements: ["H", "O"], formula: "H2O" }),
});
const ELEMENT_PATTERN = /^(?:H|He|Li|Be|B|C|N|O|F|Ne|Na|Mg|Al|Si|P|S|Cl|Ar|K|Ca|Sc|Ti|V|Cr|Mn|Fe|Co|Ni|Cu|Zn|Ga|Ge|As|Se|Br|Kr|Rb|Sr|Y|Zr|Nb|Mo|Tc|Ru|Rh|Pd|Ag|Cd|In|Sn|Sb|Te|I|Xe|Cs|Ba|La|Ce|Pr|Nd|Pm|Sm|Eu|Gd|Tb|Dy|Ho|Er|Tm|Yb|Lu|Hf|Ta|W|Re|Os|Ir|Pt|Au|Hg|Tl|Pb|Bi|Po|At|Rn|Fr|Ra|Ac|Th|Pa|U|Np|Pu|Am|Cm|Bk|Cf|Es|Fm|Md|No|Lr|Rf|Db|Sg|Bh|Hs|Mt|Ds|Rg|Cn|Nh|Fl|Mc|Lv|Ts|Og)$/;
const ATOMIC_SYMBOLS = " H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og".split(" ");

function canonicalElement(value) {
  const text = String(value || "").trim();
  const symbol = text ? text[0].toUpperCase() + text.slice(1).toLowerCase() : "";
  if (!ELEMENT_PATTERN.test(symbol)) throw new Error(`Unknown element symbol: ${value || "(blank)"}`);
  return symbol;
}

function normalizeElements(values) {
  const elements = [...new Set((values || []).map(canonicalElement))];
  if (!elements.length) throw new Error("Choose at least one element");
  if (elements.length > 8) throw new Error("Choose at most eight elements for one database query");
  return elements;
}

function queryPayload(elementValues, pageOffset = 0, evidenceTargetValue = "geometry", structureFamilyValue = "bulk") {
  const structureFamily = normalizeNomadStructureFamily(structureFamilyValue);
  const suppliedElements = normalizeElements(elementValues);
  const elements = structureFamily.fixedElements || suppliedElements;
  if (structureFamily.fixedElements && (suppliedElements.length !== elements.length
      || elements.some((element) => !suppliedElements.includes(element)))) {
    throw new Error(`${structureFamily.label} requires exactly ${elements.join(" + ")}`);
  }
  const evidenceTarget = normalizeNomadEvidenceTarget(evidenceTargetValue);
  const evidenceFilter = evidenceTarget.id === "forces"
    ? { "results.properties.geometry_optimization.final_force_maximum:lte": 1e6 }
    : ["relaxation", "calibration"].includes(evidenceTarget.id)
      ? { "results.properties.geometry_optimization.final_energy_difference:lte": 1e6 } : null;
  return {
    owner: "public",
    query: {
      and: [
        { "results.material.elements": { all: elements } },
        { "results.material.n_elements": elements.length },
        { "results.material.structural_type": structureFamily.structuralType },
        ...(structureFamily.formula ? [{ "results.material.chemical_formula_reduced": structureFamily.formula }] : []),
        ...(evidenceFilter ? [evidenceFilter] : []),
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
        "results.properties.geometry_optimization.final_energy_difference",
        "results.properties.geometry_optimization.final_force_maximum",
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
  const declaredBytes = Number(response.headers?.get?.("content-length"));
  if (Number.isFinite(declaredBytes) && declaredBytes > MAX_NOMAD_RESPONSE_BYTES) {
    throw new Error(`NOMAD archive payload exceeds the ${MAX_NOMAD_RESPONSE_BYTES / 1024 / 1024} MB browser limit`);
  }
  const text = await response.text();
  if (new TextEncoder().encode(text).length > MAX_NOMAD_RESPONSE_BYTES) {
    throw new Error(`NOMAD archive payload exceeds the ${MAX_NOMAD_RESPONSE_BYTES / 1024 / 1024} MB browser limit`);
  }
  return JSON.parse(text);
}

function randomIndex(limit, random = Math.random) {
  return Math.max(0, Math.min(limit - 1, Math.floor(random() * limit)));
}

function vectorLength(vector) {
  return Math.hypot(...vector);
}

function expandPeriodicFrame(frame, repetitions) {
  if (!frame.cell || !frame.pbc?.every(Boolean)) return {
    ...frame,
    atoms: frame.atoms.map((atom, primitiveSourceIndex) => ({ ...atom, position: [...atom.position],
      primitiveSourceIndex: atom.primitiveSourceIndex ?? primitiveSourceIndex,
      supercellImage: atom.supercellImage?.slice() || [0, 0, 0] })),
    metadata: { ...frame.metadata, repetitions: [1, 1, 1], primitiveAtomCount: frame.atoms.length },
  };
  const atoms = [];
  for (let i = 0; i < repetitions[0]; i++) for (let j = 0; j < repetitions[1]; j++) for (let k = 0; k < repetitions[2]; k++) {
    const shift = [0, 1, 2].map((axis) => i * frame.cell[0][axis] + j * frame.cell[1][axis] + k * frame.cell[2][axis]);
    frame.atoms.forEach((atom, primitiveSourceIndex) => atoms.push({
      ...atom,
      position: atom.position.map((value, axis) => value + shift[axis]),
      primitiveSourceIndex: atom.primitiveSourceIndex ?? primitiveSourceIndex,
      supercellImage: [i, j, k],
    }));
  }
  return {
    ...frame,
    atoms,
    cell: frame.cell.map((vector, axis) => vector.map((value) => value * repetitions[axis])),
    metadata: { ...frame.metadata, repetitions: repetitions.slice(), primitiveAtomCount: frame.atoms.length },
  };
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
  const expanded = expandPeriodicFrame(structure, repetitions);
  const frames = structure.frames?.map((frame) => expandPeriodicFrame(frame, repetitions));
  return {
    ...structure,
    atoms: expanded.atoms,
    cell: expanded.cell,
    ...(frames?.length ? { frames } : {}),
    metadata: { ...structure.metadata, repetitions, primitiveAtomCount: structure.atoms.length },
  };
}

function nomadSymbols(atomsData) {
  const labels = atomsData.labels || [];
  if (labels.length !== atomsData.positions.length) throw new Error("NOMAD returned inconsistent atom labels and positions");
  return labels.map((label, index) => {
    try { return canonicalElement(label); }
    catch {
      const atomicNumber = Number(atomsData.species?.[index]);
      if (Number.isInteger(atomicNumber) && ATOMIC_SYMBOLS[atomicNumber]) return ATOMIC_SYMBOLS[atomicNumber];
      throw new Error(`NOMAD atom ${index + 1} has an unsupported species label: ${label}`);
    }
  });
}

function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (value && typeof value === "object") return `{${Object.keys(value).sort()
    .filter((key) => value[key] !== undefined).map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(",")}}`;
  return JSON.stringify(value);
}

function nomadCalculationRecord(calculation, atomCount, program, methodRecord,
  runIndex, calculationIndex, systemIndex) {
  const totalEnergyJoule = Number(calculation?.energy?.total?.value);
  const totalEnergyElectronVolt = Number.isFinite(totalEnergyJoule)
    ? totalEnergyJoule / JOULE_PER_ELECTRON_VOLT : null;
  const rawForces = calculation?.forces?.total?.value;
  const forceVectors = Array.isArray(rawForces) && rawForces.length === atomCount
    && rawForces.every((vector) => Array.isArray(vector) && vector.length === 3
      && vector.every((component) => Number.isFinite(Number(component))))
    ? rawForces.map((vector) => vector.map((component) =>
      Number(component) / NEWTON_PER_ELECTRON_VOLT_PER_ANGSTROM)) : null;
  const forceMagnitudes = forceVectors?.map((vector) => Math.hypot(...vector)) || [];
  const chargeRecords = Array.isArray(calculation?.charges) ? calculation.charges : [];
  let spinRecord = null;
  let spinRecordIndex = null;
  for (let index = chargeRecords.length - 1; index >= 0; index--) {
    const rawSpins = chargeRecords[index]?.spins;
    if (Array.isArray(rawSpins) && rawSpins.length === atomCount
      && rawSpins.every((value) => Number.isFinite(Number(value)))) {
      spinRecord = chargeRecords[index]; spinRecordIndex = index; break;
    }
  }
  const atomicSpins = spinRecord?.spins?.map(Number) || null;
  return {
    forceVectors, atomicSpins,
    provenance: {
      available: Boolean(calculation),
      sourcePath: calculationIndex === null ? null : `run/${runIndex}/calculation/${calculationIndex}`,
      pairedSystemPath: `run/${runIndex}/system/${systemIndex}`,
      systemReference: calculation?.system_ref || null,
      methodReference: calculation?.method_ref || null,
      methodRecordAvailable: Boolean(methodRecord),
      methodCanonicalJson: methodRecord ? canonicalJson(methodRecord) : null,
      methodCompatibilityPolicy: "exact canonical normalized NOMAD method record",
      programName: program.name || null,
      programVersion: program.version || null,
      totalEnergyElectronVolt,
      energyPerPrimitiveAtomElectronVolt: totalEnergyElectronVolt === null ? null : totalEnergyElectronVolt / atomCount,
      forceCoverage: forceVectors ? 1 : 0,
      forceRmsElectronVoltPerAngstrom: forceMagnitudes.length
        ? Math.sqrt(forceMagnitudes.reduce((sum, value) => sum + value * value, 0) / forceMagnitudes.length) : null,
      forceMaximumElectronVoltPerAngstrom: forceMagnitudes.length ? Math.max(...forceMagnitudes) : null,
      spinCoverage: atomicSpins ? 1 : 0,
      atomicSpinCount: atomicSpins?.length || 0,
      atomicSpinMinimum: atomicSpins ? Math.min(...atomicSpins) : null,
      atomicSpinMaximum: atomicSpins ? Math.max(...atomicSpins) : null,
      atomicSpinAbsoluteSum: atomicSpins
        ? atomicSpins.reduce((sum, value) => sum + Math.abs(value), 0) : null,
      atomicSpinSourcePath: spinRecordIndex === null || calculationIndex === null ? null
        : `run/${runIndex}/calculation/${calculationIndex}/charges/${spinRecordIndex}/spins`,
      atomicSpinAnalysisMethod: spinRecord?.analysis_method || null,
      atomicSpinQuantityKind: "signed collinear atomic spin population",
      atomicSpinUnit: null,
      atomicSpinAxisAvailable: false,
      atomicSpinsUsedForGrowth: false,
      energyUnit: "eV",
      forceUnit: "eV/Å",
      forcesUsedForGrowth: false,
      absoluteEnergyComparedAcrossEntries: false,
    },
  };
}

function referencedSystemIndex(reference) {
  const match = String(reference || "").match(/\/system\/(\d+)(?:$|[#/?])/);
  return match ? Number(match[1]) : null;
}

function referencedMethodIndex(reference) {
  const match = String(reference || "").match(/\/method\/(\d+)(?:$|[#/?])/);
  return match ? Number(match[1]) : null;
}

function methodForCalculation(run, calculation) {
  const index = referencedMethodIndex(calculation?.method_ref);
  return Number.isInteger(index) ? run.method?.[index] || null : null;
}

function calculationForSystem(run, systemIndex) {
  const calculations = run.calculation || [];
  for (let index = calculations.length - 1; index >= 0; index--) {
    if (referencedSystemIndex(calculations[index]?.system_ref) === systemIndex) return { calculation: calculations[index], index };
  }
  if (calculations.length === (run.system || []).length && calculations[systemIndex]) {
    return { calculation: calculations[systemIndex], index: systemIndex };
  }
  return { calculation: null, index: null };
}

function sampledFrameIndices(count, maximum = MAX_NOMAD_RELAXATION_FRAMES) {
  if (count <= maximum) return Array.from({ length: count }, (_, index) => index);
  return [...new Set(Array.from({ length: maximum }, (_, index) =>
    Math.round(index * (count - 1) / (maximum - 1))))];
}

function nomadFrame(atomsData, symbols, calculationRecord, name, metadata = {}) {
  return {
    name,
    atoms: atomsData.positions.map((position, index) => ({
      species: symbols[index], position: position.map((value) => value * 1e10),
      occupancy: 1, occupancyTotal: 1,
      occupancyAlternatives: [{ species: symbols[index], fraction: 1 }],
      calculationForceEvPerAngstrom: calculationRecord.forceVectors?.[index] || null,
      calculationSpin: calculationRecord.atomicSpins?.[index] ?? null,
    })),
    cell: atomsData.lattice_vectors.map((vector) => vector.map((value) => value * 1e10)),
    pbc: atomsData.periodic?.map(Boolean) || [true, true, true],
    metadata: { ...metadata, calculation: calculationRecord.provenance },
  };
}

export function nomadArchiveToStructure(entry, archiveResponse) {
  const archive = archiveResponse?.data?.archive;
  const runs = archive?.run || [];
  let selectedRun = null;
  let selectedRunIndex = null;
  let systemRecords = [];
  for (let runIndex = runs.length - 1; runIndex >= 0; runIndex--) {
    const run = runs[runIndex];
    const records = (run.system || []).map((system, systemIndex) => ({ atomsData: system.atoms, systemIndex }))
      .filter(({ atomsData }) => atomsData?.positions?.length && atomsData?.lattice_vectors?.length === 3);
    if (records.length) { selectedRun = run; selectedRunIndex = runIndex; systemRecords = records; break; }
  }
  if (!systemRecords.length) throw new Error("The selected NOMAD archive has no normalized periodic atomic system");
  const finalRecord = systemRecords.at(-1);
  const finalSymbols = nomadSymbols(finalRecord.atomsData);
  const topologyRecords = systemRecords.flatMap((record) => {
    try {
      const symbols = nomadSymbols(record.atomsData);
      return symbols.length === finalSymbols.length && symbols.every((symbol, index) => symbol === finalSymbols[index])
        ? [{ ...record, symbols }] : [];
    } catch { return []; }
  });
  const retainedRecords = sampledFrameIndices(topologyRecords.length).map((index) => topologyRecords[index]);
  const material = entry.results?.material || {};
  const symmetry = material.symmetry || {};
  const program = selectedRun?.program || {};
  const makeRecordFrame = (record, retainedIndex) => {
    const paired = calculationForSystem(selectedRun, record.systemIndex);
    const calculationRecord = nomadCalculationRecord(paired.calculation, record.atomsData.positions.length,
      program, methodForCalculation(selectedRun, paired.calculation),
      selectedRunIndex, paired.index, record.systemIndex);
    return nomadFrame(record.atomsData, record.symbols, calculationRecord,
      `NOMAD relaxation snapshot ${retainedIndex + 1} / ${retainedRecords.length}`,
      { frameIndex: retainedIndex, nomadSystemIndex: record.systemIndex, nomadCalculationIndex: paired.index,
        orderedRelaxationSnapshot: true, physicalTimeAvailable: false });
  };
  const frames = retainedRecords.map(makeRecordFrame);
  const finalFrame = frames.at(-1) || makeRecordFrame({ ...finalRecord, symbols: finalSymbols }, 0);
  const entryId = entry.entry_id;
  const sourceUrl = `https://nomad-lab.eu/prod/v1/gui/search/entries/entry/id/${encodeURIComponent(entryId)}`;
  return {
    name: material.chemical_formula_reduced || `NOMAD ${entryId.slice(0, 8)}`,
    format: "NOMAD archive",
    atoms: finalFrame.atoms,
    cell: finalFrame.cell,
    pbc: finalFrame.pbc,
    ...(frames.length > 1 ? { frames } : {}),
    metadata: {
      source: "NOMAD",
      entryId,
      materialId: material.material_id,
      sourceUrl,
      formula: material.chemical_formula_reduced,
      crystalSystem: symmetry.crystal_system,
      spaceGroupNumber: symmetry.space_group_number,
      spaceGroup: symmetry.space_group_symbol || "unassigned",
      calculation: finalFrame.metadata.calculation,
      preferredFrameIndex: Math.max(0, frames.length - 1),
      relaxationSequence: frames.length > 1 ? {
        available: true,
        sourcePath: `run/${selectedRunIndex}/system + calculation system_ref`,
        originalSystemCount: systemRecords.length,
        topologyCompatibleSystemCount: topologyRecords.length,
        retainedFrameCount: frames.length,
        retainedSystemIndices: retainedRecords.map((record) => record.systemIndex),
        fixedTopology: true,
        orderedSnapshots: true,
        physicalTimeAvailable: false,
        integratedAsTrajectory: false,
        usedAsGeometricEnsembleOnly: true,
      } : { available: false, retainedFrameCount: 1, integratedAsTrajectory: false },
    },
  };
}

function finiteCalculationValue(frame, key) {
  return Number.isFinite(Number(frame?.metadata?.calculation?.[key]));
}

export function nomadStructureEvidenceProfile(structure) {
  const frames = structure?.frames?.length ? structure.frames : structure?.atoms?.length ? [structure] : [];
  const energyFrames = frames.filter((frame) => finiteCalculationValue(frame, "energyPerPrimitiveAtomElectronVolt")).length;
  const forceFrames = frames.filter((frame) => Number(frame?.metadata?.calculation?.forceCoverage) === 1).length;
  const spinFrames = frames.filter((frame) => Number(frame?.metadata?.calculation?.spinCoverage) === 1).length;
  const methodRecords = frames.map((frame) => frame?.metadata?.calculation?.methodCanonicalJson).filter(Boolean);
  const methodKeys = new Set(methodRecords);
  const pairedCalculationFrames = Math.max(energyFrames, forceFrames);
  const relaxationFrames = structure?.metadata?.relaxationSequence?.available ? frames.length : 0;
  const methodConsistent = methodKeys.size === 1 && methodRecords.length >= pairedCalculationFrames;
  return Object.freeze({
    frameCount: frames.length,
    relaxationFrames,
    energyFrames,
    forceFrames,
    spinFrames,
    methodFrames: methodRecords.length,
    pairedCalculationFrames,
    methodConsistent,
    geometryAvailable: frames.length > 0,
    relaxationAvailable: relaxationFrames >= 3,
    forceLabelsAvailable: forceFrames >= 1,
    calibrationReady: relaxationFrames >= 5 && pairedCalculationFrames >= 5 && methodConsistent,
  });
}

export function normalizeNomadEvidenceTarget(value) {
  const id = String(value || "geometry");
  const target = NOMAD_EVIDENCE_TARGETS[id];
  if (!target) throw new Error(`Unknown NOMAD evidence target: ${id}`);
  return target;
}

export function normalizeNomadStructureFamily(value) {
  const id = String(value || "bulk");
  const family = NOMAD_STRUCTURE_FAMILIES[id];
  if (!family) throw new Error(`Unknown NOMAD structure family: ${id}`);
  return family;
}

export function nomadEvidenceTargetAccepts(profile, targetValue = "geometry") {
  const target = normalizeNomadEvidenceTarget(targetValue);
  if (target.id === "geometry") return Boolean(profile.geometryAvailable);
  if (target.id === "relaxation") return Boolean(profile.relaxationAvailable);
  if (target.id === "forces") return Boolean(profile.forceLabelsAvailable);
  return Boolean(profile.calibrationReady);
}

export function nomadEvidenceProfileLabel(profile) {
  if (profile.calibrationReady) return `${profile.relaxationFrames} snapshots · calculation-series ready`;
  if (profile.relaxationAvailable) return `${profile.relaxationFrames} relaxation snapshots · ${profile.forceFrames} force-labelled`;
  if (profile.forceLabelsAvailable) return `force-labelled geometry · ${profile.forceFrames}/${profile.frameCount} snapshots`;
  return "geometry-only archive";
}

export async function randomNomadStructure(elementValues, options = {}) {
  const structureFamily = normalizeNomadStructureFamily(options.structureFamily);
  const elements = normalizeElements(elementValues);
  const evidenceTarget = normalizeNomadEvidenceTarget(options.evidenceTarget);
  const fetchImpl = options.fetchImpl || fetch;
  const initial = await postJson(`${NOMAD_API}/entries/query`,
    queryPayload(elements, 0, evidenceTarget.id, structureFamily.id), fetchImpl);
  const total = Number(initial.pagination?.total || 0);
  if (!total) throw new Error(`NOMAD has no public ${structureFamily.label} entries containing exactly ${elements.join(" + ")}`);
  const accessibleTotal = Math.min(total, 10_000);
  const attempts = Math.min(8, accessibleTotal);
  const triedOffsets = new Set();
  let lastError = null;
  for (let attempt = 0; attempt < attempts; attempt++) {
    let offset = randomIndex(accessibleTotal, options.random);
    while (triedOffsets.has(offset) && triedOffsets.size < accessibleTotal) offset = (offset + 1) % accessibleTotal;
    triedOffsets.add(offset);
    const page = offset === 0 ? initial : await postJson(`${NOMAD_API}/entries/query`,
      queryPayload(elements, offset, evidenceTarget.id, structureFamily.id), fetchImpl);
    const entry = page.data?.[0];
    if (!entry) continue;
    try {
      const hasRelaxation = Boolean(entry.results?.properties?.geometry_optimization);
      const archive = await postJson(`${NOMAD_API}/entries/${encodeURIComponent(entry.entry_id)}/archive/query`, {
        required: { run: hasRelaxation ? {
          program: "*",
          system: { atoms: "*" },
          calculation: { energy: "*", forces: "*", charges: "*", system_ref: "*", method_ref: "*" },
        } : {
          program: "*",
          "system[-1]": { atoms: "*" },
          "calculation[-1]": { energy: "*", forces: "*", charges: "*", system_ref: "*", method_ref: "*" },
        } },
      }, fetchImpl);
      const primitive = nomadArchiveToStructure(entry, archive);
      if (primitive.atoms.length > 512) throw new Error(`archive contains ${primitive.atoms.length} atoms before expansion`);
      const evidenceProfile = nomadStructureEvidenceProfile(primitive);
      if (!nomadEvidenceTargetAccepts(evidenceProfile, evidenceTarget.id)) {
        throw new Error(`entry does not satisfy ${evidenceTarget.label}`);
      }
      const structure = makeLearningSupercell(primitive);
      structure.metadata = { ...structure.metadata, nomadStructureFamily: structureFamily.id,
        nomadStructureFamilyLabel: structureFamily.label, nomadEvidenceTarget: evidenceTarget.id,
        nomadEvidenceProfile: evidenceProfile, nomadEvidenceLabel: nomadEvidenceProfileLabel(evidenceProfile) };
      return { structure, total, selectedOffset: offset, attemptedEntries: triedOffsets.size,
        structureFamily, evidenceTarget, evidenceProfile };
    } catch (error) {
      lastError = error;
    }
  }
  throw new Error(`No public ${structureFamily.label} archive matched ${evidenceTarget.label} after ${attempts} random samples${lastError ? `: ${lastError.message}` : ""}`);
}

export { canonicalElement, normalizeElements, queryPayload };
