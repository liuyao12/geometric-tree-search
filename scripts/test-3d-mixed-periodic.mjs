import assert from "node:assert/strict";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

const config = {
  mode_key: "cube",
  custom_system: {
    name: "Mixed-volume periodic regression",
    figure_refs: [],
    polycubes: [
      { name: "Domino species", voxels: [[0, 0, 0], [1, 0, 0]] },
      { name: "Monomino species", voxels: [[0, 0, 0]] }
    ],
    polyhedra: [],
    polycube_lattice: "z3"
  },
  polycube_lattice: "z3",
  criterion: "count",
  target_val: 60,
  exhaustive: false,
  include_mirrors: false,
  snapshot_every: 1000,
  placement_details: true,
  face_order: "mrv",
  move_order: "rl",
  agent_exhaustive: true,
  branch_cap: null,
  node_limit: 10000,
  candidate_cap: null,
  time_limit_ms: 30000,
  ui_yield_interval_ms: 1000,
  template_preflight: true,
  periodic_tile_count: 2,
  periodic_require_all_types: true
};

let certificate = null;
let finalSnapshot = null;
let finished = null;
for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
  if (message.periodic_template?.mixed_prototile) certificate = message.periodic_template;
  if (message.type === "full_update") finalSnapshot = message;
  if (message.type === "finished") finished = message;
}

assert.ok(certificate, "mixed species must produce a periodic quotient certificate");
assert.equal(certificate.motif.length, 2);
assert.equal(certificate.cell_volume, 3);
assert.deepEqual(certificate.tile_volumes, [2, 1]);
assert.deepEqual(
  [...new Set(certificate.motif.map(item => item.prototile_idx))].sort(),
  [0, 1],
  "the certified motif must use both selected species"
);
assert.deepEqual(certificate.prototile_counts, [
  { prototile_idx: 0, count: 1 },
  { prototile_idx: 1, count: 1 }
]);

const quotientCells = certificate.motif.flatMap(item => item.quotient_cells);
assert.equal(
  new Set(quotientCells).size,
  certificate.cell_volume,
  "motif placements may not overlap in the quotient"
);
assert.equal(
  quotientCells.length,
  certificate.cell_volume,
  "the motif must cover every quotient cell exactly once"
);

assert.ok(finished?.success, "mixed periodic growth must reach its target");
assert.equal(finalSnapshot?.placements?.length, config.target_val);
const colorsByCell = new Map();
const baseColorsByMotif = new Map();
const translationalColorOffset = tileSpecs.TRANSLATIONAL_CELL_COLOR_OFFSET;
const translationalCellColorId = (baseColorId, cell) =>
  translationalColorOffset + baseColorId * 8 + cell.reduce((index, coordinate, axis) =>
    index + (((coordinate % 2) + 2) % 2) * (2 ** axis), 0);
for (const placement of finalSnapshot.placements) {
  assert.ok(
    Number.isInteger(placement.periodic_motif_index),
    "every certified translational placement must retain its motif identity"
  );
  assert.ok(
    Array.isArray(placement.periodic_cell),
    "every certified translational placement must retain its translation cell"
  );
  assert.ok(
    Number.isInteger(placement.periodic_base_color_id),
    "every motif tile must retain its randomly assigned base color"
  );
  const knownBaseColor = baseColorsByMotif.get(placement.periodic_motif_index);
  if (knownBaseColor == null) {
    baseColorsByMotif.set(placement.periodic_motif_index, placement.periodic_base_color_id);
  } else {
    assert.equal(
      placement.periodic_base_color_id,
      knownBaseColor,
      "translated copies of one motif tile must retain its base color"
    );
  }
  const cellKey = placement.periodic_cell.join(",");
  const cellColors = colorsByCell.get(cellKey) ?? new Set();
  cellColors.add(placement.color_id);
  colorsByCell.set(cellKey, cellColors);
  assert.equal(
    placement.color_id,
    translationalCellColorId(placement.periodic_base_color_id, placement.periodic_cell),
    "each translation direction must toggle the motif tile's own base RGB color"
  );
}
assert.ok(
  new Set(baseColorsByMotif.values()).size > 1,
  "a multi-tile unit patch must preserve distinct randomly assigned motif colors"
);
assert.ok(
  [...colorsByCell.values()].some(colors => colors.size > 1),
  "tiles inside one translated multi-tile patch copy must keep their individual colors"
);
assert.deepEqual(
  finalSnapshot.tile_counts.map(item => item.type_idx),
  [0, 1],
  "periodic growth must preserve both motif species identities"
);
const finiteCounts = finalSnapshot.tile_counts.map(item => item.count);
assert.ok(
  Math.max(...finiteCounts) - Math.min(...finiteCounts) <= certificate.motif.length * 3,
  `a finite boundary may cut period cells, but species imbalance must remain boundary-sized: ${finiteCounts.join("/")}`
);
assert.equal(finished.search_stats.branch_choices_visited, 0);
assert.equal(finished.search_stats.backtracks, 0);
assert.equal(finished.search_stats.growth_axis_rank, 3);
assert.ok(finished.search_stats.growth_isotropy >= 0.75);

console.log("3D mixed-prototile periodic regression passed", {
  tiles: finished.tile_count,
  tileCounts: finalSnapshot.tile_counts.map(item => [item.name, item.count]),
  spans: finished.search_stats.growth_spans,
  isotropy: finished.search_stats.growth_isotropy,
  cellVolume: certificate.cell_volume
});
