import { samplePatch as legacySample } from "../iqc-growth-live/continuous-samples.mjs";
import { asiSample } from "./asi-sample.mjs";
export const sampleCatalog = [
  ["nacl", "NaCl · rocksalt"],
  ["ice", "Ice VIII · diffraction-derived D₂O"],
  ["copper", "Cu · ideal FCC"],
  ["iron", "Fe · ideal BCC"],
  ["silicon", "Si · ideal diamond"],
  ["cscl", "CsCl · ideal cubic binary"],
  ["bn", "h-BN · ideal 2D honeycomb"],
  ["graphene", "Graphene · ideal 2D"],
  ["cdyb", "Cd–Yb · quasicrystal model crop"],
  ["glass", "Cu–Zr · disordered negative control"],
];
export function samplePatch(id) {
  if (id === "asi") return structuredClone(asiSample);
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
            species: id === "cscl" && b ? "Cl" : spec.label,
            position: p.map(
              (v, d) => (v + [i, j, k][d] - (spec.n - 1) / 2) * spec.a,
            ),
          }),
        );
  return {
    name: sampleCatalog.find((s) => s[0] === id)[1],
    source: `Ideal geometric control · illustrative cell scale ${spec.a} Å · no thermal relaxation or experimental claim`,
    atoms,
  };
}
sampleCatalog.splice(sampleCatalog.length - 1, 0, [
  "asi",
  "Melt-quenched Si · a-Si research dataset",
]);
