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
