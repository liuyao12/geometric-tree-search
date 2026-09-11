import { samplePatch as legacySample } from "../iqc-growth-live/continuous-samples.mjs";
import { asiSample } from "./asi-sample.mjs";
import {
  ICE_VIII_BROWSER_FIXTURE,
  iceViiiUnitCellSites,
} from "../iqc-growth-live/ice-viii-browser-fixture.js";
export const sampleCatalog = [
  ["nacl", "NaCl · rocksalt"],
  ["ice", "Ice VIII · diffraction-derived D₂O"],
  ["copper", "Cu · ideal FCC"],
  ["iron", "Fe · ideal BCC"],
  ["silicon", "Si · ideal diamond"],
  ["cscl", "CsCl · ideal cubic binary"],
  ["zincblende", "ZnS · ideal zincblende"],
  ["sc", "Simple cubic · geometric control"],
  ["square", "Square sheet · geometric control"],
  ["triangular", "Triangular sheet · geometric control"],
  ["bn", "h-BN · ideal 2D honeycomb"],
  ["graphene", "Graphene · ideal 2D"],
  ["cdyb", "Cd–Yb · quasicrystal model crop"],
  ["glass", "Cu–Zr · disordered negative control"],
];
export function samplePatch(id) {
  if (["square", "triangular"].includes(id)) {
    const atoms = [];
    for (let i = -7; i <= 7; i++)
      for (let j = -7; j <= 7; j++)
        atoms.push({
          species: "X",
          position:
            id === "square"
              ? [2 * i, 2 * j, 0]
              : [2 * i + j, Math.sqrt(3) * j, 0],
        });
    return {
      name: sampleCatalog.find((s) => s[0] === id)[1],
      source:
        "Synthetic geometry-only 2D control; X is an opaque label, not a chemical element",
      atoms,
    };
  }
  if (id === "asi") return structuredClone(asiSample);
  if (id === "ice")
    return {
      ...legacySample(id),
      evaluation: {
        cell: ICE_VIII_BROWSER_FIXTURE.cellAngstrom,
        sites: iceViiiUnitCellSites(),
      },
    };
  if (["nacl", "ice", "graphene", "cdyb", "glass"].includes(id))
    return legacySample(id);
  if (id === "bn") {
    const s = legacySample("graphene");
    return {
      name: "h-BN · ideal honeycomb",
      source:
        "Geometric binary honeycomb control; illustrative 2.46 Å cell scale, not relaxed or measured",
      atoms: s.atoms.map((a, i) => ({ ...a, species: i % 2 ? "N" : "B" })),
    };
  }
  const fcc = [
    [0, 0, 0],
    [0, 0.5, 0.5],
    [0.5, 0, 0.5],
    [0.5, 0.5, 0],
  ];
  const spec = {
    copper: { label: "Cu", a: 3.615, basis: fcc, n: 4 },
    sc: { label: "X", a: 2, basis: [[0, 0, 0]], n: 6 },
    zincblende: {
      label: "Zn",
      a: 5.4,
      basis: [...fcc, ...fcc.map((p) => p.map((v) => v + 0.25))],
      n: 3,
    },
    iron: {
      label: "Fe",
      a: 2.866,
      basis: [
        [0, 0, 0],
        [0.5, 0.5, 0.5],
      ],
      n: 5,
    },
    silicon: {
      label: "Si",
      a: 5.431,
      basis: [...fcc, ...fcc.map((p) => p.map((v) => v + 0.25))],
      n: 3,
    },
    cscl: {
      label: "Cs",
      a: 4.12,
      basis: [
        [0, 0, 0],
        [0.5, 0.5, 0.5],
      ],
      n: 5,
    },
  }[id];
  if (!spec) throw Error("Unknown sample");
  const atoms = [];
  for (let i = 0; i < spec.n; i++)
    for (let j = 0; j < spec.n; j++)
      for (let k = 0; k < spec.n; k++)
        spec.basis.forEach((p, b) =>
          atoms.push({
            species:
              id === "cscl" && b
                ? "Cl"
                : id === "zincblende" && b >= 4
                  ? "S"
                  : spec.label,
            position: p.map(
              (v, d) => (v + [i, j, k][d] - (spec.n - 1) / 2) * spec.a,
            ),
          }),
        );
  return {
    name: sampleCatalog.find((s) => s[0] === id)[1],
    source: `Ideal geometric control · illustrative cell scale ${spec.a} Å · no thermal relaxation or experimental claim`,
    atoms,
    evaluation: {
      cell: [spec.a, spec.a, spec.a],
      sites: spec.basis.map((p, b) => ({
        fractional: p.map((v) => v - (spec.n - 1) / 2),
        species:
          id === "cscl" && b
            ? "Cl"
            : id === "zincblende" && b >= 4
              ? "S"
              : spec.label,
      })),
    },
  };
}
sampleCatalog.splice(sampleCatalog.length - 1, 0, [
  "asi",
  "Melt-quenched Si · a-Si research dataset",
]);
