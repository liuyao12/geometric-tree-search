function xyz(value) {
  if (Array.isArray(value)) return value.slice(0, 3).map(Number);
  if (value?.toArray) return value.toArray().slice(0, 3).map(Number);
  return [Number(value?.x) || 0, Number(value?.y) || 0, Number(value?.z) || 0];
}

function distance(first, second) {
  return Math.hypot(first[0] - second[0], first[1] - second[1], first[2] - second[2]);
}

function rounded(value, digits = 4) {
  const scale = 10 ** digits;
  return Math.round(Number(value) * scale) / scale;
}

/** Build an ephemeral, target-free site audit. The returned coordinates never enter a receipt. */
export function buildSiteProvenance({ atom, atoms, placements = [], sceneToAngstrom = 1,
  neighborReachScene, geometryLabel = "metric point set" }) {
  if (!atom || !Array.isArray(atoms) || !(neighborReachScene > 0) || !(sceneToAngstrom > 0)) {
    throw new Error("A selected atom, atom set, and positive geometric scales are required");
  }
  const position = xyz(atom.p);
  const neighbors = atoms.filter((other) => other.id !== atom.id).map((other) => ({ atom: other,
    distanceScene: distance(position, xyz(other.p)) })).filter((entry) => entry.distanceScene <= neighborReachScene)
    .sort((first, second) => first.distanceScene - second.distanceScene || first.atom.id - second.atom.id);
  const speciesCounts = new Map();
  neighbors.forEach(({ atom: neighbor }) => speciesCounts.set(neighbor.species,
    (speciesCounts.get(neighbor.species) || 0) + 1));
  const distanceShells = new Map();
  neighbors.forEach(({ atom: neighbor, distanceScene }) => {
    if (!distanceShells.has(neighbor.species)) distanceShells.set(neighbor.species, []);
    distanceShells.get(neighbor.species).push(rounded(distanceScene * sceneToAngstrom));
  });
  const angleShells = new Map();
  for (let first = 0; first < neighbors.length; first++) {
    for (let second = first + 1; second < neighbors.length; second++) {
      const left = xyz(neighbors[first].atom.p).map((value, axis) => value - position[axis]);
      const right = xyz(neighbors[second].atom.p).map((value, axis) => value - position[axis]);
      const denominator = neighbors[first].distanceScene * neighbors[second].distanceScene;
      if (!(denominator > 1e-12)) continue;
      const cosine = Math.max(-1, Math.min(1,
        left.reduce((sum, value, axis) => sum + value * right[axis], 0) / denominator));
      const key = [neighbors[first].atom.species, neighbors[second].atom.species].sort().join("|");
      if (!angleShells.has(key)) angleShells.set(key, []);
      angleShells.get(key).push(rounded(Math.acos(cosine) * 180 / Math.PI, 3));
    }
  }
  const clusterIds = [...new Set(atom.clusterIds || [])].sort((first, second) => first - second);
  const nucleusIds = [...new Set(atom.nucleusIds || [])].sort((first, second) => first - second);
  const creator = placements.find((placement) => placement.id === atom.createdByClusterId)
    || placements.find((placement) => placement.freshAtomIds?.includes(atom.id)) || null;
  const memberships = clusterIds.map((id) => placements.find((placement) => placement.id === id))
    .filter(Boolean).map((placement) => ({ id: placement.id, type: placement.type,
      parentId: placement.parentId, ruleId: placement.ruleId, depth: placement.depth,
      nucleusId: placement.nucleusId, seedNucleus: placement.seedNucleus === true }));
  const supplied = atom.seed === true && !creator;
  const origin = creator ? "GCTS-emitted structural site" : supplied ? "supplied observation / fitted seed" : "structural site";
  return {
    schema: 1, siteId: atom.id, species: atom.species, family: atom.family || null, origin,
    observedReferenceIndex: Number.isInteger(atom.referenceIndex) ? atom.referenceIndex : null,
    positionAngstrom: position.map((value) => rounded(value * sceneToAngstrom)),
    geometryLabel,
    localEnvironment: {
      reachAngstrom: rounded(neighborReachScene * sceneToAngstrom),
      coordination: neighbors.length,
      speciesCounts: [...speciesCounts.entries()].sort(([first], [second]) => first.localeCompare(second)),
      distanceShells: [...distanceShells.entries()].sort(([first], [second]) => first.localeCompare(second)),
      angleShells: [...angleShells.entries()].sort(([first], [second]) => first.localeCompare(second))
        .map(([key, values]) => [key, values.sort((first, second) => first - second)]),
      nearest: neighbors.slice(0, 8).map(({ atom: neighbor, distanceScene }) => ({
        siteId: neighbor.id, species: neighbor.species,
        distanceAngstrom: rounded(distanceScene * sceneToAngstrom),
      })),
    },
    lineage: {
      creatorClusterId: creator?.id ?? null, creatorClusterType: creator ? creator.type : null,
      ruleId: creator?.ruleId ?? null, parentClusterId: creator?.parentId ?? null,
      causalDepth: creator?.depth ?? (Number(atom.depth) || 0),
      clusterMemberships: memberships, nucleusIds,
      sharedClusterSite: clusterIds.length > 1,
      interfaceSite: atom.interfaceContact === true || nucleusIds.length > 1,
    },
    decisionEvidence: creator?.decisionEvidence || null,
    audit: { targetUsed: false, ephemeralInspectorOnly: true, includedInReceipt: false,
      physicalEnergyInferred: false, forceInferred: false, mechanismIdentityInferred: false },
  };
}
