import assert from "node:assert/strict";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";
import { LATTICE_POLYHEDRON_CENSUS_POOL } from "../assets/lattice-polyhedron-survivors.js";

const candidate = LATTICE_POLYHEDRON_CENSUS_POOL.find(item => item.id === "10_45026");
assert.ok(candidate);

const baseConfig = {
  mode_key: "cube",
  custom_system: {
    name: "Search baseline regression 10_45026",
    figure_refs: [],
    polycubes: [],
    polyhedra: [{ name: candidate.name, vertices: candidate.vertices }],
    polycube_lattice: "z3"
  },
  polycube_lattice: "z3",
  criterion: "count",
  target_val: 30,
  tiling_strategy: "free_range",
  move_order: "balanced",
  face_order: "mrv",
  exhaustive: true,
  forced_move_layer_lag_cap: 2,
  template_preflight: false,
  generic_failure_memo: false,
  snapshot_every: 0,
  placement_details: true,
  random_seed: 17,
  seeded_tie_breaks: true,
  time_limit_ms: 200,
  ui_yield_interval_ms: 1000000
};

async function run(overrides = {}) {
  let final = null;
  const successors = [];
  for await (const message of createTilingStream(
    { ...baseConfig, ...overrides },
    tileSpecs,
    { stop: false }
  )) {
    if (message.type === "search_successor") successors.push(message.snapshot);
    if (message.type === "finished") final = message;
  }
  assert.ok(final);
  return { final, successors };
}

const discrepancy = await run({ search_discrepancy_limit: 0 });
assert.equal(discrepancy.final.search_stats.discrepancy_limit, 0);
assert.ok(discrepancy.final.search_stats.discrepancy_prunes > 0);
assert.equal(discrepancy.final.search_incomplete, true);

const uct = await run({ move_order: "uct" });
assert.ok(uct.final.search_stats.uct_simulations > 1);
assert.ok(uct.final.search_stats.uct_states > 0);
assert.ok(uct.final.search_stats.uct_action_visits > 0);

const successors = await run({ enumerate_successors_only: true });
assert.ok(successors.successors.length > 1);
assert.equal(
  successors.final.search_stats.successor_states_emitted,
  successors.successors.length
);

console.log("3D search-baseline regressions passed", {
  discrepancy_prunes: discrepancy.final.search_stats.discrepancy_prunes,
  uct_simulations: uct.final.search_stats.uct_simulations,
  successors: successors.successors.length
});
