// Proton-disordered ice VI from the open-access IUCrJ HAR refinement and
// COD 1567346.  Every candidate D site is retained at occupancy 1/2.  The
// average diffraction structure therefore supplies finite D/vacancy
// alternatives, not a unique assignment of two deuteria to each oxygen.

export const ICE_VI_BROWSER_FIXTURE = Object.freeze({
  codId: "1567346",
  codRevision: 276901,
  title: "Accurate crystal structure of ice VI from X-ray diffraction with Hirshfeld atom refinement",
  doi: "10.1107/S2052252522006662",
  license: "CC-BY-4.0",
  cifSha256: "a8eba8ab43c98a30d62ee08fe83f003f945aa22018331254df852c8bbdc2efc6",
  normalizedAtomsSha256: "71c5c6b0e5c4b746a2e02e7b87ee7351fa06d2ff8012b648ae40a6f68e6fd905",
  cellAngstrom: Object.freeze([6.1732, 6.1732, 5.6881]),
  spaceGroup: "P 42/n m c :2 · #137",
  repeats: Object.freeze([2, 2, 2]),
  measurement: Object.freeze({ temperatureK: 293, radiation: "synchrotron X-ray", wavelengthA: .27552 }),
  asymmetricSites: Object.freeze([
    Object.freeze({ label: "O1", species: "O", fractional: Object.freeze([.52944, .75, .12894]), occupancy: 1, uIsoA2: .03827 }),
    Object.freeze({ label: "O2", species: "O", fractional: Object.freeze([.25, .75, -.25]), occupancy: 1, uIsoA2: .04005 }),
    Object.freeze({ label: "D1A", species: "D", fractional: Object.freeze([.4686, .630, .210]), occupancy: .5, uIsoA2: .049 }),
    Object.freeze({ label: "D1B", species: "D", fractional: Object.freeze([.690, .75, .128]), occupancy: .5, uIsoA2: .037 }),
    Object.freeze({ label: "D2", species: "D", fractional: Object.freeze([.137, .75, -.137]), occupancy: .5, uIsoA2: .044 }),
    Object.freeze({ label: "D1C", species: "D", fractional: Object.freeze([.462, .75, -.023]), occupancy: .5, uIsoA2: .039 }),
  ]),
  symmetryOperations: Object.freeze([
    "x,y,z", "-y+1/2,x,z+1/2", "y,-x+1/2,z+1/2", "x+1/2,-y,-z",
    "-x,y+1/2,-z", "-x+1/2,-y+1/2,z", "y+1/2,x+1/2,-z+1/2", "-y,-x,-z+1/2",
    "-x,-y,-z", "y-1/2,-x,-z-1/2", "-y,x-1/2,-z-1/2", "-x-1/2,y,z",
    "x,-y-1/2,z", "x-1/2,y-1/2,-z", "-y-1/2,-x-1/2,z-1/2", "y,x,z-1/2",
  ]),
});

function wrap(value) {
  const result = value - Math.floor(value);
  return Math.abs(result - 1) < 1e-10 ? 0 : result;
}

function numericFraction(text) {
  const [numerator, denominator] = text.split("/").map(Number);
  return denominator ? numerator / denominator : numerator;
}

function termValue(term, [x, y, z]) {
  const match = term.replace(/\s+/g, "").match(/^(-?)([xyz])(?:(\+|-)(\d+(?:\/\d+)?))?$/);
  if (!match) throw new Error(`Unsupported ice-VI symmetry term: ${term}`);
  let value = { x, y, z }[match[2]];
  if (match[1] === "-") value = -value;
  if (match[3]) value += (match[3] === "-" ? -1 : 1) * numericFraction(match[4]);
  return wrap(value);
}

function apply(operation, fractional) {
  return operation.split(",").map((term) => termValue(term, fractional));
}

function positionKey(species, fractional) {
  return `${species}:${fractional.map((value) => Math.round(wrap(value) * 1e8)).join(":")}`;
}

export function iceViAverageUnitCellSites() {
  const unique = new Map();
  ICE_VI_BROWSER_FIXTURE.asymmetricSites.forEach((site) => {
    ICE_VI_BROWSER_FIXTURE.symmetryOperations.forEach((operation) => {
      const fractional = apply(operation, site.fractional);
      const key = positionKey(site.species, fractional);
      if (!unique.has(key)) unique.set(key, { ...site, fractional });
    });
  });
  return [...unique.values()].sort((first, second) => first.species.localeCompare(second.species)
    || first.fractional[0] - second.fractional[0]
    || first.fractional[1] - second.fractional[1]
    || first.fractional[2] - second.fractional[2]
    || first.label.localeCompare(second.label));
}

export function generateIceViAverageObservation() {
  const unit = iceViAverageUnitCellSites();
  const [rx, ry, rz] = ICE_VI_BROWSER_FIXTURE.repeats;
  const [a, b, c] = ICE_VI_BROWSER_FIXTURE.cellAngstrom;
  const atoms = [];
  for (let ix = 0; ix < rx; ix++) for (let iy = 0; iy < ry; iy++) for (let iz = 0; iz < rz; iz++) {
    unit.forEach((site, basisIndex) => atoms.push(Object.freeze({
      label: site.label,
      species: site.species,
      position: Object.freeze([(ix + site.fractional[0]) * a,
        (iy + site.fractional[1]) * b, (iz + site.fractional[2]) * c]),
      occupancy: site.occupancy,
      occupancyAlternatives: Object.freeze([Object.freeze({ species: site.species, fraction: site.occupancy })]),
      uIsoA2: site.uIsoA2,
      q: Object.freeze([ix, iy, iz, basisIndex]),
    })));
  }
  return Object.freeze({
    atoms: Object.freeze(atoms),
    cell: Object.freeze([[rx * a, 0, 0], [0, ry * b, 0], [0, 0, rz * c]]
      .map((vector) => Object.freeze(vector))),
    pbc: Object.freeze([true, true, true]),
  });
}

function minimumImageDisplacement(first, second, lengths) {
  return first.map((value, axis) => {
    let delta = value - second[axis];
    delta -= Math.round(delta / lengths[axis]) * lengths[axis];
    return delta;
  });
}

function periodicDistance(first, second, lengths) {
  return Math.hypot(...minimumImageDisplacement(first, second, lengths));
}

function seededRank(edge, seed) {
  let value = (seed ^ Math.imul(edge + 1, 0x9e3779b1)) >>> 0;
  value ^= value >>> 16;
  value = Math.imul(value, 0x7feb352d) >>> 0;
  value ^= value >>> 15;
  return value >>> 0;
}

// Resolve one instantaneous ice-rule microstate from the diffraction-average
// geometry alone.  Every half-occupied D site identifies an O--O bond through
// its two nearest oxygens.  The resulting four-regular oxygen graph admits an
// Euler orientation: orienting each closed Euler circuit gives exactly two
// outgoing bonds per oxygen.  Selecting the D candidate nearer the outgoing
// oxygen therefore enforces both Bernal--Fowler rules without energies, a
// lattice label, an expected network count, or hidden source-site identities.
export function resolveIceViIceRuleMicrostate(seed = 1) {
  const average = generateIceViAverageObservation();
  const lengths = average.cell.map((vector, axis) => vector[axis]);
  const oxygens = average.atoms.filter((atom) => atom.species === "O");
  const deuteria = average.atoms.filter((atom) => atom.species === "D");
  const bonds = new Map();

  deuteria.forEach((atom) => {
    const nearest = oxygens.map((oxygen, oxygenIndex) => ({
      oxygenIndex,
      distance: periodicDistance(atom.position, oxygen.position, lengths),
    })).sort((first, second) => first.distance - second.distance || first.oxygenIndex - second.oxygenIndex).slice(0, 2);
    const endpoints = nearest.map((entry) => entry.oxygenIndex).sort((first, second) => first - second);
    const key = endpoints.join(":");
    if (!bonds.has(key)) bonds.set(key, { endpoints, candidates: [] });
    bonds.get(key).candidates.push({ atom, nearestOwner: nearest[0].oxygenIndex, nearestDistance: nearest[0].distance,
      partnerDistance: nearest[1].distance });
  });

  const edgeRecords = [...bonds.values()].sort((first, second) => first.endpoints[0] - second.endpoints[0]
    || first.endpoints[1] - second.endpoints[1]);
  if (!edgeRecords.length || edgeRecords.some((edge) => edge.candidates.length !== 2
    || new Set(edge.candidates.map((candidate) => candidate.nearestOwner)).size !== 2)) {
    throw new Error("Ice VI average sites do not form paired O--D···O bond alternatives");
  }
  const adjacency = Array.from({ length: oxygens.length }, () => []);
  edgeRecords.forEach((edge, edgeIndex) => edge.endpoints.forEach((oxygenIndex) => adjacency[oxygenIndex].push({
    edgeIndex, other: edge.endpoints[0] === oxygenIndex ? edge.endpoints[1] : edge.endpoints[0],
  })));
  if (adjacency.some((neighbors) => neighbors.length !== 4)) {
    throw new Error("Ice VI oxygen framework is not four-connected");
  }
  adjacency.forEach((neighbors) => neighbors.sort((first, second) => seededRank(first.edgeIndex, seed)
    - seededRank(second.edgeIndex, seed) || first.edgeIndex - second.edgeIndex));

  const used = new Set();
  const orientations = new Map();
  const components = [];
  for (let start = 0; start < oxygens.length; start++) {
    if (adjacency[start].every(({ edgeIndex }) => used.has(edgeIndex))) continue;
    const componentEdges = [];
    const stack = [start];
    while (stack.length) {
      const current = stack[stack.length - 1];
      const next = adjacency[current].find(({ edgeIndex }) => !used.has(edgeIndex));
      if (!next) { stack.pop(); continue; }
      used.add(next.edgeIndex);
      orientations.set(next.edgeIndex, [current, next.other]);
      componentEdges.push(next.edgeIndex);
      stack.push(next.other);
    }
    components.push(componentEdges);
  }
  if (used.size !== edgeRecords.length) throw new Error("Ice VI Euler orientation omitted oxygen bonds");

  const selectedDeuteria = edgeRecords.map((edge, edgeIndex) => {
    const [donor] = orientations.get(edgeIndex);
    const selected = edge.candidates.find((candidate) => candidate.nearestOwner === donor);
    if (!selected) throw new Error("Ice VI bond lacks a donor-side D alternative");
    return selected.atom;
  });
  const donorCounts = Array(oxygens.length).fill(0);
  const bondCounts = Array(oxygens.length).fill(0);
  orientations.forEach(([donor, acceptor]) => { donorCounts[donor]++; bondCounts[donor]++; bondCounts[acceptor]++; });
  const atoms = [...oxygens, ...selectedDeuteria].map((atom) => Object.freeze({
    ...atom,
    occupancy: 1,
    occupancyAlternatives: Object.freeze([Object.freeze({ species: atom.species, fraction: 1 })]),
  })).sort((first, second) => first.species.localeCompare(second.species)
    || first.position[0] - second.position[0] || first.position[1] - second.position[1]
    || first.position[2] - second.position[2]);

  return Object.freeze({
    atoms: Object.freeze(atoms), cell: average.cell, pbc: average.pbc,
    audit: Object.freeze({
      method: "geometry-only Euler orientation of paired O--D···O alternatives",
      seed: Number(seed) || 0,
      oxygenAtoms: oxygens.length,
      oxygenBonds: edgeRecords.length,
      candidateDeuteriumSites: deuteria.length,
      selectedDeuteriumAtoms: selectedDeuteria.length,
      realizedAtoms: atoms.length,
      connectedOxygenNetworks: components.length,
      oxygenDegreeHistogram: Object.freeze({ 4: bondCounts.filter((count) => count === 4).length }),
      donorCountHistogram: Object.freeze({ 2: donorCounts.filter((count) => count === 2).length }),
      oneDeuteriumPerBond: selectedDeuteria.length === edgeRecords.length,
      twoCovalentDeuteriaPerOxygen: donorCounts.every((count) => count === 2),
      hiddenSiteLabelsUsed: false,
      reportedPeriodicCellUsedForMinimumImage: true,
      latticeSiteIndicesUsed: false,
      preassignedOxygenBondGraphUsed: false,
      energyOrPotentialUsed: false,
    }),
  });
}
