function median(values) {
  if (!values.length) return 0;
  const ordered = values.slice().sort((first, second) => first - second);
  const middle = Math.floor(ordered.length / 2);
  return ordered.length % 2 ? ordered[middle] : .5 * (ordered[middle - 1] + ordered[middle]);
}

function positionDistance(first, second) {
  return Math.hypot(...first.map((value, axis) => value - second[axis]));
}

function unionFind(count) {
  const parent = Array.from({ length: count }, (_, index) => index);
  const find = (index) => {
    while (parent[index] !== index) {
      parent[index] = parent[parent[index]];
      index = parent[index];
    }
    return index;
  };
  const join = (first, second) => {
    const a = find(first); const b = find(second);
    if (a !== b) parent[Math.max(a, b)] = Math.min(a, b);
  };
  return { find, join };
}

export function auditGeometricMicrostructure({
  atoms,
  placements,
  types,
  adjacencyReach,
} = {}) {
  if (!Array.isArray(atoms) || !Array.isArray(placements) || !Array.isArray(types)) {
    throw new Error("Microstructure audit requires atom, placement, and type arrays");
  }
  if (!(Number.isFinite(adjacencyReach) && adjacencyReach > 0)) {
    throw new Error("Microstructure adjacency reach must be positive and finite");
  }
  atoms.forEach((atom) => {
    if (typeof atom.chemistryToken !== "string" || !Number.isFinite(atom.coordination)) {
      throw new Error("Microstructure atoms require chemistry tokens and finite coordination counts");
    }
  });
  const typeById = new Map(types.map((type) => [type.id, type]));
  const terminalTypeIds = new Set(types.filter((type) => type.residual).map((type) => type.id));
  const gapBoundaryTypeIds = new Set(types.filter((type) => !type.residual && type.gap).map((type) => type.id));
  const recurringTypeIds = new Set(types.filter((type) => !type.residual && !type.gap).map((type) => type.id));
  const terminalAtoms = new Set();
  const gapBoundaryAtoms = new Set();
  const recurringAtoms = new Set();
  placements.forEach((placement) => {
    if (!typeById.has(placement.type) || !Array.isArray(placement.support)
      || !Array.isArray(placement.centerPosition) || placement.centerPosition.length !== 3) {
      throw new Error("Microstructure placement references invalid type, support, or center geometry");
    }
    const destination = terminalTypeIds.has(placement.type) ? terminalAtoms
      : gapBoundaryTypeIds.has(placement.type) ? gapBoundaryAtoms : recurringAtoms;
    placement.support.forEach((index) => {
      if (!Number.isInteger(index) || index < 0 || index >= atoms.length) throw new Error("Placement support index is out of range");
      destination.add(index);
    });
  });
  const literalOnlyAtoms = [...terminalAtoms].filter((index) => !recurringAtoms.has(index));

  const coordinationGroups = new Map();
  atoms.forEach((atom, index) => {
    const rows = coordinationGroups.get(atom.chemistryToken) || [];
    rows.push({ index, value: atom.coordination });
    coordinationGroups.set(atom.chemistryToken, rows);
  });
  const coordinationBaselines = [];
  const coordinationAnomalyAtoms = new Set();
  coordinationGroups.forEach((rows, chemistryToken) => {
    const center = median(rows.map((row) => row.value));
    const mad = median(rows.map((row) => Math.abs(row.value - center)));
    const threshold = Math.max(2, 3 * 1.4826 * mad);
    rows.filter((row) => Math.abs(row.value - center) >= threshold).forEach((row) => coordinationAnomalyAtoms.add(row.index));
    coordinationBaselines.push({ chemistryToken, observations: rows.length, median: center, mad, anomalyThreshold: threshold });
  });

  let crossPoseContacts = 0;
  let samePoseContacts = 0;
  let poseDomainComponents = 0;
  let posedOccurrences = 0;
  const poseInterfaceAtoms = new Set();
  const perTypePoseDomains = [];
  recurringTypeIds.forEach((type) => {
    const rows = placements.filter((placement) => placement.type === type && Number.isInteger(placement.pose));
    if (!rows.length) return;
    posedOccurrences += rows.length;
    const components = unionFind(rows.length);
    for (let first = 0; first < rows.length; first++) for (let second = first + 1; second < rows.length; second++) {
      if (positionDistance(rows[first].centerPosition, rows[second].centerPosition) > adjacencyReach) continue;
      if (rows[first].pose === rows[second].pose) {
        samePoseContacts++;
        components.join(first, second);
      } else {
        crossPoseContacts++;
        rows[first].support.forEach((index) => poseInterfaceAtoms.add(index));
        rows[second].support.forEach((index) => poseInterfaceAtoms.add(index));
      }
    }
    const componentCount = new Set(rows.map((_, index) => components.find(index))).size;
    poseDomainComponents += componentCount;
    perTypePoseDomains.push({ type, occurrences: rows.length, poseOrbits: new Set(rows.map((row) => row.pose)).size, components: componentCount });
  });

  const occupationalAlternativeSites = atoms.filter((atom) => atom.chemistryToken.startsWith("occ[")).length;
  const explicitVacancySites = atoms.filter((atom) => atom.chemistryToken.includes("Vac=")).length;
  return {
    atomCount: atoms.length,
    recurringTypes: recurringTypeIds.size,
    gapBoundaryTypes: gapBoundaryTypeIds.size,
    terminalTypes: terminalTypeIds.size,
    recurringCoveredAtoms: recurringAtoms.size,
    gapBoundaryAtoms: gapBoundaryAtoms.size,
    terminalCoveredAtoms: terminalAtoms.size,
    literalOnlyAtoms: literalOnlyAtoms.length,
    coordinationAnomalyAtoms: coordinationAnomalyAtoms.size,
    coordinationBaselines,
    occupationalAlternativeSites,
    explicitVacancySites,
    posedOccurrences,
    poseDomainComponents,
    samePoseContacts,
    crossPoseContacts,
    perTypePoseDomains,
    siteRoles: atoms.map((_, index) => ({
      index,
      recurring: recurringAtoms.has(index),
      gapBoundary: gapBoundaryAtoms.has(index),
      literalTerminal: terminalAtoms.has(index) && !recurringAtoms.has(index),
      coordinationAnomaly: coordinationAnomalyAtoms.has(index),
      poseInterface: poseInterfaceAtoms.has(index),
      occupationalAlternative: atoms[index].chemistryToken.startsWith("occ["),
      explicitVacancy: atoms[index].chemistryToken.includes("Vac="),
    })),
    adjacencyReach,
    interpretation: crossPoseContacts
      ? "spatially adjacent local pose domains observed"
      : "no adjacent unlike-pose domains at the audited reach",
    defectLabelsGiven: false,
    grainBoundaryClaimed: false,
    defectFormationEnergyModeled: false,
    literalTerminalsPromoted: false,
    gapBoundaryClassesEmitAtoms: false,
    gapBoundaryClassesReusableAsConstraints: true,
    localPoseDomainsCalledGrains: false,
  };
}
