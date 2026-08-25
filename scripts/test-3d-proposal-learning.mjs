import assert from "node:assert/strict";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";
import {
  createInitialProposalPopulation,
  growthCurveArea,
  mutateProposalProgram,
  normalizeProposalProgram,
  proposalProgramFromPatchSnapshot,
  proposalTileKey
} from "../apps/3d-lattice-tiler/proposal-learner.js";
import {
  runProposalEpisode,
  trainProposalProgram
} from "../apps/3d-lattice-tiler/proposal-training.js";

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
assert.ok(
  populationA.some(program => program.patch_size > 1),
  "the population must include ordered multi-step patch proposals"
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
    greedy_no_backtrack: false,
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
  patch: baselineA.snapshot.placements.slice(0, 8).map((placement, index) => ({
    prototile_idx: placement.prototile_idx,
    orientation_id: placement.orientation_id,
    translation: index === 0
      ? [0, 0, 0]
      : placement.translation.map(
          (coordinate, axis) => coordinate - baselineA.snapshot.placements[0].translation[axis]
        )
  })),
  sequence: [
    {
      weights: {
        coverage: 1,
        growth_axis_rank: 2
      }
    },
    {
      weights: {
        coverage: 1,
        growth_isotropy: 1,
        growth_compactness: 0.25
      }
    }
  ]
});
const learned = await run("proposal", 7, proposal);
assert.equal(learned.final.success, true);
assert.equal(learned.final.search_stats.proposal_program_id, proposal.id);
assert.equal(learned.final.search_stats.proposal_patch_size, 2);
assert.equal(learned.final.search_stats.proposal_sequence_steps_used, 2);
assert.equal(learned.final.search_stats.proposal_patch_tiles_replayed, 7);
assert.equal(learned.final.search_stats.proposal_patch_conflicts, 0);

const trained = await trainProposalProgram({ mode_key: "cube" }, {
  target: 16,
  horizon_ms: 500,
  generations: 1,
  population: 2,
  elite: 1,
  seed: 13,
  min_improvement: 0,
  baseline_replicates: 1,
  proposal_replicates: 1
});
assert.ok(trained.learned.program.patch.length >= 16, "training must retain its discovered patch");
assert.ok(trained.refinement.length >= 1, "training must verify and refine its winning patch");
assert.equal(trained.refinement[0].horizon_ms, 1000);
const replayed = await runProposalEpisode({ mode_key: "cube" }, {
  target: 16,
  horizon_ms: 500
}, {
  program: trained.learned.program,
  randomSeed: 101
});
assert.equal(replayed.success, true);
assert.equal(replayed.proposal_patch_tiles_replayed, 15);
assert.equal(replayed.proposal_patch_conflicts, 0);

const liveProgram = proposalProgramFromPatchSnapshot(
  { mode_key: "cube", polycube_lattice: "z3" },
  baselineA.snapshot
);
assert.equal(liveProgram.tile_key, proposalTileKey({ mode_key: "cube", polycube_lattice: "z3" }));
assert.equal(liveProgram.patch.length, baselineA.snapshot.placements.length);
assert.deepEqual(liveProgram.patch[0].translation, [0, 0, 0]);
const reservedTailProgram = proposalProgramFromPatchSnapshot(
  { mode_key: "cube", polycube_lattice: "z3" },
  baselineA.snapshot,
  null,
  { tailReserve: 4 }
);
assert.equal(
  reservedTailProgram.patch.length,
  baselineA.snapshot.placements.length - 4,
  "live learning should be able to reserve a backtrackable suffix"
);
const liveReplay = await runProposalEpisode({ mode_key: "cube" }, {
  target: 24,
  horizon_ms: 500
}, {
  program: liveProgram,
  randomSeed: 37
});
assert.equal(liveReplay.success, true);
assert.equal(liveReplay.proposal_patch_tiles_replayed, 23);
const extendedLiveProgram = proposalProgramFromPatchSnapshot(
  { mode_key: "cube", polycube_lattice: "z3" },
  baselineA.snapshot,
  liveProgram
);
assert.equal(extendedLiveProgram.parent_id, liveProgram.id);
assert.equal(extendedLiveProgram.generation, liveProgram.generation + 1);

console.log("3D proposal-learning regressions passed", {
  population: populationA.length,
  baseline_tiles: baselineA.final.tile_count,
  learned_tiles: learned.final.tile_count,
  proposal: proposal.id
});
