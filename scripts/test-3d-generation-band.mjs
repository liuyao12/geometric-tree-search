import assert from "node:assert/strict";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

const config = {
  mode_key: "census_10_24775",
  criterion: "count",
  target_val: 40,
  tiling_strategy: "free_range",
  move_order: "no_brainer",
  face_order: "mrv",
  template_preflight: false,
  exhaustive: false,
  forced_move_layer_lag_cap: 2,
  time_limit_ms: 5000,
  ui_yield_interval_ms: 1000
};

let final = null;
const appliedLags = [];
for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
  if (message.type === "placement_delta" && message.action === "add") {
    assert.ok(Number.isFinite(message.generation_lag), "every ordinary applied move must expose its generation lag");
    appliedLags.push(message.generation_lag);
  }
  if (message.type === "finished") final = message;
}

assert.equal(final?.success, true, "the hard shell band must still permit bounded growth");
assert.equal(final?.tile_count, 40);
assert.equal(final?.search_stats?.generation_lag_cap, 2);
assert.ok(final?.search_stats?.generation_band_deferrals > 0, "the fixture must exercise deferred outer-shell moves");
assert.ok(appliedLags.length > 0);
assert.ok(Math.max(...appliedLags) <= 2, "no applied move may escape more than two generations beyond the oldest frontier");

console.log("3D generation-band regression passed", {
  tiles: final.tile_count,
  appliedMoves: appliedLags.length,
  maximumAppliedLag: Math.max(...appliedLags),
  deferredMoves: final.search_stats.generation_band_deferrals,
  forcedThrottles: final.search_stats.forced_throttles
});
