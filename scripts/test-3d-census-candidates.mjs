import assert from "node:assert/strict";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

const candidates = tileSpecs.figureCatalog.filter(figure => figure.census_candidate);
assert.equal(candidates.length, 16, "the research catalog must expose all screened candidates");
const survivors = candidates.filter(figure => figure.census_candidate.screen_status === "unresolved");
const isohedralGrowers = candidates.filter(figure => figure.census_candidate.screen_status === "isohedral_grower");
assert.equal(survivors.length, 6, "only candidates that pass the bounded isohedral screen remain unresolved");
assert.equal(isohedralGrowers.length, 10, "long isohedral growers must be retained only as screened-out controls");
assert.deepEqual(
  survivors.map(figure => figure.census_candidate.survivor_priority),
  Array.from({ length: 6 }, (_, index) => index + 1),
  "survivor priority metadata must be complete"
);

async function solve(config) {
  let final = null;
  let largestPatch = 0;
  for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
    largestPatch = Math.max(largestPatch, message.tile_count ?? message.placements?.length ?? 0);
    if (message.type === "finished") final = message;
  }
  assert.ok(final, "search must emit a terminal result");
  return { final, largestPatch };
}

const first = survivors[0];
const candidateRun = await solve({
  mode_key: first.mode_key,
  custom_system: {
    name: "Candidate catalog smoke test",
    figure_refs: [first.id],
    polycubes: [],
    polycube_lattice: "z3"
  },
  polycube_lattice: "z3",
  criterion: "count",
  target_val: 8,
  tiling_strategy: "free_range",
  exhaustive: true,
  include_mirrors: false,
  snapshot_every: 0,
  placement_details: true,
  face_order: "mrv",
  move_order: "balanced",
  time_limit_ms: 2000,
  ui_yield_interval_ms: 100,
  template_preflight: true
});
assert.equal(candidateRun.final.success, true, "the first survivor must grow beyond its seed tile");
assert.equal(candidateRun.largestPatch, 8);
assert.ok(candidateRun.final.search_stats.visited_nodes < 1000, "visited nodes must report actual work, not the mixed-radix estimate");

const exhaustiveWitness = await solve({
  mode_key: "cube",
  criterion: "count",
  target_val: 2,
  tiling_strategy: "free_range",
  exhaustive: true,
  template_preflight: false,
  time_limit_ms: 1000
});
assert.equal(exhaustiveWitness.final.success, true, "exhaustive mode must stop when it finds a witness");
assert.equal(exhaustiveWitness.final.result_kind, "patch_found");

console.log("3D census candidate regressions passed", {
  candidates: candidates.length,
  survivors: survivors.length,
  firstCandidate: first.census_candidate.id,
  firstPatch: candidateRun.largestPatch,
  visitedNodes: candidateRun.final.search_stats.visited_nodes
});
