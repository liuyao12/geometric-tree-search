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
  let periodicCertificate = null;
  const translationalChecks = [];
  for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
    if (message.periodic_template) periodicCertificate = message.periodic_template;
    if (message.type === "translational_check") {
      translationalChecks.push({ patchSize: message.patch_size, certified: message.certified });
    }
    if (message.type === "finished") final = message;
  }
  assert.ok(final, "strategy run must emit a terminal result");
  return { final, periodicCertificate, translationalChecks };
}

const translational = await solve({ tiling_strategy: "translational" });
assert.equal(translational.final.success, true);
assert.ok(translational.periodicCertificate, "translational mode requires an exact patch certificate");
assert.equal(translational.final.search_stats.branch_choices_visited, 0);
assert.equal(translational.final.search_stats.growth_axis_rank, 3);

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
assert.equal(isohedral.periodicCertificate, null, "isohedral mode must skip translational certificates");
assert.equal(isohedral.final.search_stats.growth_axis_rank, 3);

const generic = await solve({
  tiling_strategy: "generic",
  target_val: 12
});
assert.equal(generic.final.success, true);
assert.equal(generic.periodicCertificate, null, "generic mode must skip structural fast paths");
assert.ok(generic.final.search_stats.branch_choices_visited > 0);

console.log("3D strategy regressions passed", {
  translational_tiles: translational.final.tile_count,
  isohedral_tiles: isohedral.final.tile_count,
  generic_choices: generic.final.search_stats.branch_choices_visited,
  rejected_uncertified_tiles: noOneTilePatch.final.tile_count
});
