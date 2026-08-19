import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";
import {
  classifyLatticeCandidateScreen,
  LATTICE_POLYHEDRON_CENSUS_POOL,
  LATTICE_POLYHEDRON_SCREENING,
  LATTICE_POLYHEDRON_SURVIVORS
} from "../assets/lattice-polyhedron-survivors.js";

const growthWorkerSource = await readFile(
  new URL("../apps/3d-lattice-tiler/growth-benchmark-worker.js", import.meta.url),
  "utf8"
);
const growthAppSource = await readFile(
  new URL("../apps/3d-lattice-tiler/app.js", import.meta.url),
  "utf8"
);
assert.match(growthWorkerSource, /id: "proof"[\s\S]*?proof: true/, "the comparison worker must expose a proof lane");
assert.match(
  growthWorkerSource,
  /forced_move_layer_lag_cap: mode\.proof \? 0 : baseConfig\.forced_move_layer_lag_cap/,
  "the proof lane must disable the generational band"
);
assert.match(growthWorkerSource, /generic_failure_memo: mode\.proof/, "the proof lane must memoize exact failures");
assert.match(
  growthWorkerSource,
  /seeded_tie_breaks: !!mode\.proof/,
  "the proof comparison lane must use replayable seeded tie diversification"
);
assert.match(
  growthWorkerSource,
  /generic_periodic_certificate: !!mode\.proof/,
  "the proof lane must test a reached target patch for an exact translational quotient"
);
assert.match(growthWorkerSource, /exhaustive: !!mode\.proof/, "only the proof comparison lane may claim exhaustive search");
assert.match(growthWorkerSource, /certificateKind: final\?\.tiling_evidence\?\.kind/, "proof certificates must reach the UI");
assert.match(growthAppSource, /id: "proof"[\s\S]*?label: "Proof search · unbanded"/, "the proof trace must be visible in the chart");
assert.match(growthAppSource, /All six modes finished\./, "the comparison status must include all six lanes");
assert.match(growthAppSource, /finite-patch witnesses, not space-tiling certificates/, "the catalog must not overstate a large GCTS patch");
assert.match(
  growthAppSource,
  /this excludes those patches as translational fundamental domains, not other possible motifs/,
  "the catalog must state the narrow scope of a negative target-patch quotient check"
);
assert.match(
  growthAppSource,
  /that target patch is not a translational quotient/,
  "the completed proof-lane summary must retain the target-patch quotient result"
);

assert.equal(LATTICE_POLYHEDRON_CENSUS_POOL.length, 16, "the rescreener and catalog must share the full source pool");
assert.equal(
  LATTICE_POLYHEDRON_CENSUS_POOL.filter(candidate => candidate.screening.status === "exact_rejection").length,
  11,
  "all removed candidates must retain their exact rejection certificates"
);
assert.equal(LATTICE_POLYHEDRON_SCREENING.source_pool_size, LATTICE_POLYHEDRON_CENSUS_POOL.length);
const archivedScreening = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-rescreen-2026-08-17.json", import.meta.url),
  "utf8"
));
const archivedProofScreening = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-diversified-gcts-screen-2026-08-18.json", import.meta.url),
  "utf8"
));
assert.deepEqual(
  {
    screen_date: LATTICE_POLYHEDRON_SCREENING.gcts_proof.screen_date,
    lane: LATTICE_POLYHEDRON_SCREENING.gcts_proof.lane,
    target_tiles: LATTICE_POLYHEDRON_SCREENING.gcts_proof.target_tiles,
    configured_node_limit: LATTICE_POLYHEDRON_SCREENING.gcts_proof.configured_node_limit,
    time_limit_ms: LATTICE_POLYHEDRON_SCREENING.gcts_proof.time_limit_seconds * 1000,
    seeds: LATTICE_POLYHEDRON_SCREENING.gcts_proof.seeds,
    seeded_tie_breaks: LATTICE_POLYHEDRON_SCREENING.gcts_proof.seeded_tie_breaks,
    generation_band: LATTICE_POLYHEDRON_SCREENING.gcts_proof.generation_band,
    exact_failure_memo: LATTICE_POLYHEDRON_SCREENING.gcts_proof.exact_failure_memo,
    translation_equivariant_nogoods: LATTICE_POLYHEDRON_SCREENING.gcts_proof.translation_equivariant_nogoods,
    mirrors: LATTICE_POLYHEDRON_SCREENING.gcts_proof.mirrors
  },
  {
    screen_date: archivedProofScreening.screen_date,
    lane: archivedProofScreening.baseline_protocol.lane,
    target_tiles: archivedProofScreening.baseline_protocol.target_tiles,
    configured_node_limit: archivedProofScreening.baseline_protocol.configured_node_limit,
    time_limit_ms: archivedProofScreening.baseline_protocol.time_limit_ms,
    seeds: archivedProofScreening.baseline_protocol.seeds,
    seeded_tie_breaks: archivedProofScreening.baseline_protocol.seeded_tie_breaks,
    generation_band: archivedProofScreening.baseline_protocol.generation_band,
    exact_failure_memo: archivedProofScreening.baseline_protocol.exact_failure_memo,
    translation_equivariant_nogoods: archivedProofScreening.baseline_protocol.translation_equivariant_nogoods,
    mirrors: archivedProofScreening.baseline_protocol.mirrors
  },
  "runtime proof-search limits must match the archived executed protocol"
);
assert.deepEqual(
  LATTICE_POLYHEDRON_SURVIVORS.map(candidate => ({
    id: candidate.id,
    robust_largest_patch: candidate.gcts_proof_screening.robust_largest_patch,
    median_largest_patch: candidate.gcts_proof_screening.median_largest_patch,
    best_largest_patch: candidate.gcts_proof_screening.best_largest_patch,
    target_hits: candidate.gcts_proof_screening.target_hits,
    trials: candidate.gcts_proof_screening.trials
  })),
  archivedProofScreening.baseline_candidates.map(candidate => ({
    id: candidate.id,
    robust_largest_patch: candidate.robust_largest_patch,
    median_largest_patch: candidate.median_largest_patch,
    best_largest_patch: candidate.best_largest_patch,
    target_hits: candidate.trials.filter(trial => trial.termination_reason === "target_reached").length,
    trials: candidate.trials.length
  })),
  "catalog GCTS evidence must match the archived fixed-node runs"
);
assert.deepEqual(
  LATTICE_POLYHEDRON_SCREENING.gcts_proof.target_patch_quotient_check,
  {
    patch_tiles: archivedProofScreening.baseline_protocol.target_tiles,
    candidates_with_witness: archivedProofScreening.screening_summary.candidates_with_40_tile_witness,
    distinct_patches_checked: archivedProofScreening.screening_summary.distinct_40_tile_witnesses_checked,
    completed_checks: archivedProofScreening.screening_summary.completed_target_patch_quotient_checks,
    certificates_found: archivedProofScreening.screening_summary.target_patch_quotient_certificates_found,
    certificate_method: archivedProofScreening.baseline_protocol.certificate_method,
    report: "data/lattice-polyhedron-diversified-gcts-screen-2026-08-18.json"
  },
  "runtime target-patch quotient evidence must match the archived exact checks"
);
assert.equal(archivedProofScreening.screening_summary.screening_conclusion, "all_five_remain_inconclusive");
assert.ok(
  archivedProofScreening.focused_target_witnesses.every(
    witness => witness.quotient_check_completed && !witness.quotient_certificate_found
  ),
  "all recorded target-patch quotient checks must have completed without a certificate"
);
for (const candidate of LATTICE_POLYHEDRON_SURVIVORS) {
  const witness = archivedProofScreening.focused_target_witnesses.find(item => item.id === candidate.id);
  assert.ok(witness, `${candidate.id} must retain its focused 40-tile witness`);
  assert.equal(candidate.gcts_proof_screening.focused_witness_hash, witness.witness_hash);
  assert.equal(candidate.gcts_proof_screening.target_patch_quotient_certificates, 0);
}
assert.deepEqual(
  LATTICE_POLYHEDRON_CENSUS_POOL
    .filter(candidate => candidate.screening.status === "exact_rejection")
    .map(candidate => ({
      id: candidate.id,
      certificate: candidate.screening.certificate,
      motif_tiles: candidate.screening.motif_tiles,
      period_vectors: candidate.screening.period_vectors
    })),
  archivedScreening.exact_rejections,
  "runtime rejection certificates must match the archived exact rescreen"
);
assert.deepEqual(
  LATTICE_POLYHEDRON_CENSUS_POOL
    .filter(candidate => candidate.screening.status === "inconclusive")
    .map(candidate => candidate.id),
  archivedScreening.inconclusive_survivors,
  "the public survivors must match the archived bounded-screen result"
);
assert.equal(
  classifyLatticeCandidateScreen({ translational: { provenImpossible: true }, isohedral: null }),
  "reject_certified_non_tiler",
  "a local impossibility certificate must never survive periodic screening"
);
assert.equal(
  classifyLatticeCandidateScreen({ translational: { certified: false, incomplete: true }, isohedral: null }),
  "inconclusive",
  "a bounded search limit must remain inconclusive"
);

const candidates = tileSpecs.figureCatalog.filter(figure => figure.census_candidate);
assert.equal(candidates.length, 5, "certified periodic and isohedral tiles must not remain in the catalog");
const survivors = candidates;
assert.deepEqual(
  survivors.map(figure => figure.census_candidate.survivor_priority),
  Array.from({ length: 5 }, (_, index) => index + 1),
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
assert.equal(candidateRun.final.search_stats.move_order, "balanced", "candidate benchmarks must honor their selected move order");
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

const conwayFigure = tileSpecs.figureCatalog.find(figure => figure.mode_key === "scd_conway");
assert.ok(conwayFigure?.aperiodic_tile, "the Conway biprism must be visible as a known aperiodic monotile");
const conwayTile = tileSpecs.TILING_REGISTRY.scd_conway.build()[0];
assert.ok(conwayTile.verts.flat().every(Number.isInteger), "the catalog realization must have lattice vertices");
const conwayRun = await solve({
  mode_key: "scd_conway",
  custom_system: {
    name: "SCD layered construction",
    figure_refs: ["scd_conway::0"],
    polycubes: [],
    polycube_lattice: "z3"
  },
  criterion: "count",
  target_val: 24,
  tiling_strategy: "free_range",
  include_mirrors: false,
  snapshot_every: 1,
  placement_details: true
});
assert.equal(conwayRun.final.success, true);
assert.equal(conwayRun.final.can_tile, true);
assert.equal(conwayRun.final.result_kind, "known_aperiodic_construction");
assert.equal(conwayRun.largestPatch, 24);

console.log("3D census candidate regressions passed", {
  candidates: candidates.length,
  firstCandidate: first.census_candidate.id,
  firstPatch: candidateRun.largestPatch,
  visitedNodes: candidateRun.final.search_stats.visited_nodes,
  conwayPatch: conwayRun.largestPatch
});
