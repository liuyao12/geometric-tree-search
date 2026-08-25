// Proton-ordered ice VIII from neutron powder diffraction.
//
// COD 1566658 is D2O, so deuterium is retained explicitly rather than being
// silently relabelled as hydrogen.  The browser expands the asymmetric unit
// with the published space-group operators and then forms a deterministic
// 2x2x2 observation window.  Only species and Cartesian positions are passed
// to the cluster learner.

export const ICE_VIII_BROWSER_FIXTURE = Object.freeze({
  codId: "1566658",
  codRevision: 273854,
  title: "Structure of D2O ice VIII from in situ powder neutron diffraction",
  authors: "Jorgensen, J. D.; Beyerlein, R. A.; Watanabe, N.; Worlton, T. G.",
  journal: "The Journal of Chemical Physics 81, 3211 (1984)",
  doi: "10.1063/1.448027",
  license: "CC0",
  cifSha256: "00ea6c9535c1995feb98a18372cf3f9514816a715d79ab01dc30cacef8cfe875",
  normalizedAtomsSha256: "08b9aa530e366451b4c927a0fc30fa799225d3f9916655168d62e71fcf218dfb",
  cellAngstrom: Object.freeze([4.6779, 4.6779, 6.8029]),
  spaceGroup: "I 41/a m d :2 · #141",
  repeats: Object.freeze([2, 2, 2]),
  asymmetricSites: Object.freeze([
    Object.freeze({ species: "O", fractional: Object.freeze([0, .25, .1049]) }),
    Object.freeze({ species: "D", fractional: Object.freeze([0, .4137, .1932]) }),
  ]),
  symmetryOperations: Object.freeze([
    "y+1/4,x+3/4,-z+1/4", "y+1/4,-x+3/4,-z+1/4",
    "x,y+1/2,-z", "x,-y,-z",
    "-y+3/4,x+3/4,-z+1/4", "-y+3/4,-x+3/4,-z+1/4",
    "-x,y+1/2,-z", "-x,-y,-z",
    "-y+3/4,-x+1/4,z+3/4", "-y+3/4,x+1/4,z+3/4",
    "-x,-y+1/2,z", "-x,y,z",
    "y+1/4,-x+1/4,z+3/4", "y+1/4,x+1/4,z+3/4",
    "x,-y+1/2,z", "x,y,z",
    "y+3/4,x+1/4,-z+3/4", "y+3/4,-x+1/4,-z+3/4",
    "x+1/2,y,-z+1/2", "x+1/2,-y+1/2,-z+1/2",
    "-y+1/4,x+1/4,-z+3/4", "-y+1/4,-x+1/4,-z+3/4",
    "-x+1/2,y,-z+1/2", "-x+1/2,-y+1/2,-z+1/2",
    "-y+1/4,-x+3/4,z+1/4", "-y+1/4,x+3/4,z+1/4",
    "-x+1/2,-y,z+1/2", "-x+1/2,y+1/2,z+1/2",
    "y+3/4,-x+3/4,z+1/4", "y+3/4,x+3/4,z+1/4",
    "x+1/2,-y,z+1/2", "x+1/2,y+1/2,z+1/2",
  ]),
});

function wrapFractional(value) {
  const wrapped = value - Math.floor(value);
  return Math.abs(wrapped - 1) < 1e-10 ? 0 : wrapped;
}

function fraction(text) {
  const [numerator, denominator] = text.split("/").map(Number);
  return denominator ? numerator / denominator : numerator;
}

function evaluateFractionalTerm(term, [x, y, z]) {
  const compact = term.replace(/\s+/g, "");
  const match = compact.match(/^(-?)([xyz])(?:(\+|-)(\d+(?:\/\d+)?))?$/);
  if (!match) throw new Error(`Unsupported ice-VIII symmetry term: ${term}`);
  const coordinate = { x, y, z }[match[2]];
  const signed = match[1] === "-" ? -coordinate : coordinate;
  const offset = match[3] ? (match[3] === "-" ? -1 : 1) * fraction(match[4]) : 0;
  return wrapFractional(signed + offset);
}

function applySymmetry(operation, fractional) {
  return operation.split(",").map((term) => evaluateFractionalTerm(term, fractional));
}

function fractionalKey(species, fractional) {
  return `${species}:${fractional.map((value) => Math.round(wrapFractional(value) * 1e8)).join(":")}`;
}

export function iceViiiUnitCellSites() {
  const unique = new Map();
  ICE_VIII_BROWSER_FIXTURE.asymmetricSites.forEach((site) => {
    ICE_VIII_BROWSER_FIXTURE.symmetryOperations.forEach((operation) => {
      const fractional = applySymmetry(operation, site.fractional);
      unique.set(fractionalKey(site.species, fractional), { species: site.species, fractional });
    });
  });
  return [...unique.values()].sort((first, second) => first.species.localeCompare(second.species)
    || first.fractional[0] - second.fractional[0]
    || first.fractional[1] - second.fractional[1]
    || first.fractional[2] - second.fractional[2]);
}

export function generateIceViiiObservation() {
  const unit = iceViiiUnitCellSites();
  const [rx, ry, rz] = ICE_VIII_BROWSER_FIXTURE.repeats;
  const [a, b, c] = ICE_VIII_BROWSER_FIXTURE.cellAngstrom;
  const atoms = [];
  for (let ix = 0; ix < rx; ix++) for (let iy = 0; iy < ry; iy++) for (let iz = 0; iz < rz; iz++) {
    unit.forEach((site, basisIndex) => atoms.push({
      species: site.species,
      position: [
        (ix + site.fractional[0]) * a,
        (iy + site.fractional[1]) * b,
        (iz + site.fractional[2]) * c,
      ],
      q: [ix, iy, iz, basisIndex],
    }));
  }
  return Object.freeze({
    atoms: Object.freeze(atoms.map((atom) => Object.freeze({
      ...atom,
      position: Object.freeze(atom.position),
      q: Object.freeze(atom.q),
    }))),
    cell: Object.freeze([[rx * a, 0, 0], [0, ry * b, 0], [0, 0, rz * c]]
      .map((vector) => Object.freeze(vector))),
    pbc: Object.freeze([true, true, true]),
  });
}
