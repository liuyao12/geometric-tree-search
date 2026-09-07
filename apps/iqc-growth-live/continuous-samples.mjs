import {
  generateIceViiiObservation,
  ICE_VIII_BROWSER_FIXTURE,
} from "./ice-viii-browser-fixture.js";
import { CDYB_BROWSER_FIXTURE } from "./cdyb-browser-fixture.js";
export function samplePatch(id) {
  if (id === "ice")
    return {
      name: "Ice VIII · D₂O",
      source: `Neutron diffraction · COD ${ICE_VIII_BROWSER_FIXTURE.codId} · deuterium retained`,
      atoms: generateIceViiiObservation().atoms.map((s) => ({
        species: s.species,
        position: [...s.position],
      })),
    };
  if (id === "cdyb")
    return {
      name: "Cd–Yb quasicrystal",
      source: `Published model crop · ${CDYB_BROWSER_FIXTURE.articleDoi} · CC BY 4.0`,
      atoms: CDYB_BROWSER_FIXTURE.atoms.map(([species, ...position]) => ({
        species,
        position,
      })),
    };
  if (id === "graphene") {
    const atoms = [];
    for (let i = -4; i <= 4; i++)
      for (let j = -4; j <= 4; j++)
        for (const k of [0, 1])
          atoms.push({
            species: "C",
            position: [
              2.46 * (i + j / 2),
              (2.46 * Math.sqrt(3) * j) / 2 + k * 1.42,
              0,
            ],
          });
    return {
      name: "Graphene",
      source: "Ideal 2D honeycomb control · Cartesian positions in Å",
      atoms,
    };
  }
  if (id === "glass") {
    let s = 217;
    const random = () => {
        s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
        return s / 4294967296;
      },
      atoms = [];
    for (let k = 0; k < 100000 && atoms.length < 180; k++) {
      const position = [0, 0, 0].map(() => random() * 18 - 9);
      if (
        atoms.every(
          (a) => Math.hypot(...a.position.map((v, i) => v - position[i])) > 1.8,
        )
      )
        atoms.push({ species: random() < 0.64 ? "Cu" : "Zr", position });
    }
    return {
      name: "Disordered Cu–Zr",
      source:
        "Seeded hard-core geometric negative control; no glass thermodynamics inferred",
      atoms,
    };
  }
  const atoms = [];
  for (let x = 0; x < 6; x++)
    for (let y = 0; y < 6; y++)
      for (let z = 0; z < 6; z++)
        atoms.push({
          species: (x + y + z) % 2 ? "Cl" : "Na",
          position: [x, y, z].map((v) => (v - 2.5) * 2.8201),
        });
  return {
    name: "NaCl",
    source: "Ideal rocksalt control · 216 sites · nearest spacing 2.8201 Å",
    atoms,
  };
}
