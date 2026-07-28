import assert from "node:assert/strict";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

async function solve(modeKey, target = 40) {
  const config = {
    mode_key: modeKey,
    criterion: "count",
    target_val: target,
    tiling_strategy: "isohedral",
    include_mirrors: true,
    template_preflight: true,
    snapshot_every: 0,
    time_limit_ms: 10000
  };
  let final = null;
  for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
    if (message.type === "finished") final = message;
  }
  assert.ok(final, `${modeKey} must emit a terminal result`);
  return final;
}

for (const modeKey of ["cube", "tetragonal_disphenoid"]) {
  const result = await solve(modeKey);
  const stats = result.search_stats;
  assert.equal(result.success, true, `${modeKey} must admit tile-transitive patch growth`);
  assert.equal(stats.growth_axis_rank, 3, `${modeKey} isohedral growth must span 3-space`);
  assert.ok(stats.growth_isotropy >= 0.5, `${modeKey} isohedral growth must remain balanced`);
  assert.equal(
    stats.branch_choices_visited,
    1,
    `${modeKey} should need only one root-to-neighbor relation`
  );
  assert.ok(
    stats.isohedral_patch_copies_applied > 1,
    `${modeKey} must repeatedly lift and apply the known patch`
  );
  assert.ok(
    stats.isohedral_tiles_propagated >= result.tile_count - 2,
    `${modeKey} must propagate almost every tile after the root and seed relation`
  );
  assert.equal(stats.backtracks, 0, `${modeKey} should not need a fallback branch`);
}

console.log("3D isohedral patch-propagation regressions passed");
