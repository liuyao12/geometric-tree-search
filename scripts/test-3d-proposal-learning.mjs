import assert from "node:assert/strict";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";
import {
  createInitialProposalPopulation,
  growthCurveArea,
  mutateProposalProgram,
  normalizeProposalProgram
} from "../apps/3d-lattice-tiler/proposal-learner.js";

const populationA = createInitialProposalPopulation({
  tileKey: "cube",
  populationSize: 8,
  seed: 41
});
const populationB = createInitialProposalPopulation({
  tileKey: "cube",
  populationSize: 8,
  seed: 41
});
assert.deepEqual(populationA, populationB, "proposal populations must be reproducible");
assert.equal(populationA.length, 8);
assert.ok(
  new Set(populationA.map(program => JSON.stringify(program.weights))).size > 3,
  "one learner must explore structurally different proposal programs"
);

const mutationA = mutateProposalProgram(populationA[0], { seed: 99 });
const mutationB = mutateProposalProgram(populationA[0], { seed: 99 });
assert.deepEqual(mutationA, mutationB, "proposal mutation must be reproducible");
assert.notDeepEqual(mutationA.weights, populationA[0].weights);

assert.equal(
  growthCurveArea([
    { milliseconds: 0, tiles: 1 },
    { milliseconds: 50, tiles: 5 },
    { milliseconds: 100, tiles: 10 }
  ], { horizonMs: 100, targetTiles: 10 }),
  0.3
);

async function run(moveOrder, randomSeed, proposalProgram = null) {
  const config = {
    mode_key: "cube",
    criterion: "count",
    target_val: 24,
    tiling_strategy: "generic",
    move_order: moveOrder,
    proposal_program: proposalProgram,
    greedy_no_backtrack: true,
    random_seed: randomSeed,
    template_preflight: false,
    periodic_preflight: false,
    snapshot_every: 0,
    placement_details: true,
    face_order: "coverage",
    exhaustive: false,
    time_limit_ms: 5000,
    ui_yield_interval_ms: 1000
  };
  let final = null;
  let snapshot = null;
  for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
    if (message.type === "full_update") snapshot = message;
    if (message.type === "finished") final = message;
  }
  assert.ok(final);
  assert.ok(snapshot);
  return { final, snapshot };
}

const baselineA = await run("no_brainer", 7);
const baselineB = await run("no_brainer", 7);
const baselineC = await run("no_brainer", 8);
assert.equal(baselineA.final.success, true);
assert.equal(baselineA.final.search_stats.backtracks, 0);
assert.deepEqual(
  baselineA.snapshot.placements.map(placement => placement.translation),
  baselineB.snapshot.placements.map(placement => placement.translation),
  "the no-brainer tie sequence must repeat for the same seed"
);
assert.notDeepEqual(
  baselineA.snapshot.placements.map(placement => placement.translation),
  baselineC.snapshot.placements.map(placement => placement.translation),
  "equally sensible no-brainer placements must vary with the random seed"
);

const proposal = normalizeProposalProgram({
  id: "balanced-cube-test",
  tile_key: "cube",
  weights: {
    coverage: 1,
    growth_axis_rank: 2,
    growth_isotropy: 1,
    growth_compactness: 0.25
  }
});
const learned = await run("proposal", 7, proposal);
assert.equal(learned.final.success, true);
assert.equal(learned.final.search_stats.backtracks, 0);
assert.equal(learned.final.search_stats.proposal_program_id, proposal.id);

console.log("3D proposal-learning regressions passed", {
  population: populationA.length,
  baseline_tiles: baselineA.final.tile_count,
  learned_tiles: learned.final.tile_count,
  proposal: proposal.id
});
