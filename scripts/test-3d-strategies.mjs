import assert from "node:assert/strict";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

async function solve(overrides) {
  const config = {
    mode_key: "cube",
    criterion: "count",
    target_val: 24,
    tiling_strategy: "auto",
    move_order: "balanced",
    face_order: "mrv",
    template_preflight: true,
    periodic_tile_count: 2,
    time_limit_ms: 10000,
    ui_yield_interval_ms: 1000,
    ...overrides
  };
  let final = null;
  let latestSnapshot = null;
  let periodicCertificate = null;
  const translationalChecks = [];
  for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
    if (message.periodic_template) periodicCertificate = message.periodic_template;
    if (message.type === "translational_check") {
      translationalChecks.push({ patchSize: message.patch_size, certified: message.certified });
    }
    if (message.type === "full_update") latestSnapshot = message;
    if (message.type === "finished") final = message;
  }
  assert.ok(final, "strategy run must emit a terminal result");
  return { final, latestSnapshot, periodicCertificate, translationalChecks };
}

const translational = await solve({ tiling_strategy: "translational", placement_details: true });
assert.equal(translational.final.success, true);
assert.ok(translational.periodicCertificate, "translational mode requires an exact patch certificate");
assert.equal(translational.final.search_stats.branch_choices_visited, 0);
assert.equal(translational.final.search_stats.growth_axis_rank, 3);
for (const placement of translational.latestSnapshot?.placements ?? []) {
  assert.ok(Number.isInteger(placement.periodic_motif_index));
  assert.equal(
    placement.color_id,
    placement.periodic_motif_index % tileSpecs.COLOR_PALETTE.length,
    "translated copies of each motif tile must reuse its color"
  );
}

for (const polycubeLattice of ["fcc", "half"]) {
  const latticeRun = await solve({
    polycube_lattice: polycubeLattice,
    periodic_patch_max_tiles: 4
  });
  assert.equal(latticeRun.final.success, true, `${polycubeLattice} translational growth must be certified`);
  assert.equal(latticeRun.final.search_stats.growth_axis_rank, 3);
}

const noOneTilePatch = await solve({
  mode_key: "tet_oct",
  target_val: 8,
  tiling_strategy: "translational",
  periodic_tile_count: 1
});
assert.equal(noOneTilePatch.final.success, false, "translational mode must not fall back");
assert.equal(noOneTilePatch.final.tile_count, 1);
assert.equal(noOneTilePatch.final.search_stats.branch_choices_visited, 0);

const progressivePatchCheck = await solve({
  mode_key: "tet_oct",
  target_val: 8,
  tiling_strategy: "translational",
  periodic_tile_count: undefined,
  periodic_patch_max_tiles: 4
});
assert.deepEqual(
  progressivePatchCheck.translationalChecks.map(check => check.patchSize),
  [1, 2, 3, 4],
  "translational mode must test candidate patch sizes progressively"
);

const isohedral = await solve({
  tiling_strategy: "isohedral",
  target_val: 12
});
assert.equal(isohedral.final.success, true);
assert.equal(isohedral.final.result_kind, "patch_found");
assert.equal(isohedral.final.can_tile, null, "a finite isohedral patch is not a global tiling proof");
assert.equal(isohedral.periodicCertificate, null, "isohedral mode must skip translational certificates");
assert.equal(isohedral.final.search_stats.growth_axis_rank, 3);

const generic = await solve({
  tiling_strategy: "generic",
  target_val: 12
});
assert.equal(generic.final.success, true);
assert.equal(generic.periodicCertificate, null, "generic mode must skip structural fast paths");
assert.ok(generic.final.search_stats.branch_choices_visited > 0);

const freestyle = await solve({
  tiling_strategy: "freestyle",
  target_val: 12
});
assert.equal(freestyle.final.success, true);
assert.equal(freestyle.final.result_kind, "patch_found");
assert.equal(freestyle.final.search_stats.tiling_strategy, "generic");

const freeRange = await solve({
  tiling_strategy: "free_range",
  move_order: "no_brainer",
  greedy_no_backtrack: true,
  template_preflight: false,
  target_val: 12
});
assert.equal(freeRange.final.success, true);
assert.equal(freeRange.final.search_stats.tiling_strategy, "generic");
assert.equal(freeRange.final.search_stats.backtracks, 0);

for (const [mode_key, polycube_lattice] of [
  ["letter_o", "fcc"],
  ["letter_o", "half"],
  ["2_cross", "fcc"],
  ["2_cross", "half"]
]) {
  const refined = await solve({
    mode_key,
    polycube_lattice,
    periodic_patch_max_tiles: 4,
    periodic_template_max_volume: undefined
  });
  assert.equal(
    refined.final.result_kind,
    "certified_tiling",
    `${mode_key} must be checked on the ${polycube_lattice} refined lattice`
  );
}

const certificateBeforeDisplayTarget = await solve({
  mode_key: "fcc_pure",
  target_val: 20,
  tiling_strategy: "translational",
  periodic_patch_max_tiles: 4
});
assert.equal(certificateBeforeDisplayTarget.final.result_kind, "certified_tiling");
assert.equal(
  certificateBeforeDisplayTarget.final.success,
  true,
  "an exact infinite-tiling certificate must count as success even if its preview is shorter than the display target"
);

const retainedCertifiedPreview = await solve({
  mode_key: "cube",
  criterion: "layer",
  target_val: 50,
  tiling_strategy: "translational",
  periodic_patch_max_tiles: 4,
  safety_max_tiles: 2,
  snapshot_every: 0
});
assert.equal(retainedCertifiedPreview.final.result_kind, "certified_tiling");
assert.equal(retainedCertifiedPreview.final.tile_count, 2);
assert.equal(
  retainedCertifiedPreview.latestSnapshot?.tile_count,
  2,
  "the terminal snapshot must retain the best displayed patch after certified growth rolls back"
);

const reflectionHoneycomb = await solve({
  mode_key: "tetragonal_disphenoid",
  criterion: "layer",
  target_val: 1,
  tiling_strategy: "isohedral",
  include_mirrors: true
});
assert.equal(reflectionHoneycomb.final.result_kind, "patch_found");
assert.equal(reflectionHoneycomb.final.success, true);
assert.equal(reflectionHoneycomb.final.search_stats.growth_axis_rank, 3);
assert.ok(
  reflectionHoneycomb.final.search_stats.reflection_continuations_seen > 0,
  "isohedral mode must retain face-reflection continuations for Coxeter-style honeycombs"
);

for (const mode_key of ["corner_tetra", "big_corner_tetra"]) {
  const obstruction = await solve({
    mode_key,
    criterion: "layer",
    target_val: 1,
    tiling_strategy: "freestyle",
    include_mirrors: true
  });
  assert.equal(obstruction.final.result_kind, "no_tiling");
  assert.equal(obstruction.final.can_tile, false);
  assert.equal(obstruction.final.tiling_evidence?.kind, "local_edge_obstruction");
}

console.log("3D strategy regressions passed", {
  translational_tiles: translational.final.tile_count,
  isohedral_tiles: isohedral.final.tile_count,
  generic_choices: generic.final.search_stats.branch_choices_visited,
  rejected_uncertified_tiles: noOneTilePatch.final.tile_count
});
