import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";
import {
  classifyLatticeCandidateScreen,
  LATTICE_POLYHEDRON_CENSUS_POOL,
  LATTICE_POLYHEDRON_SCREENING,
  LATTICE_POLYHEDRON_SURVIVORS
} from "../assets/lattice-polyhedron-survivors.js";

const fingerprintDigest = values => createHash("sha256")
  .update(values.slice().sort().join("\n"))
  .digest("hex");

const growthWorkerSource = await readFile(
  new URL("../apps/3d-lattice-tiler/growth-benchmark-worker.js", import.meta.url),
  "utf8"
);
const growthAppSource = await readFile(
  new URL("../apps/3d-lattice-tiler/app.js", import.meta.url),
  "utf8"
);
const canonicalTilerHtml = await readFile(
  new URL("../3d-lattice-tiler/index.html", import.meta.url),
  "utf8"
);
const sourceTilerHtml = await readFile(
  new URL("../apps/3d-lattice-tiler/index.html", import.meta.url),
  "utf8"
);
const appModuleVersion = html => html.match(/<script type="module" src="\.\/app\.js\?v=([^"]+)"/)?.[1];
assert.equal(
  appModuleVersion(canonicalTilerHtml),
  appModuleVersion(sourceTilerHtml),
  "the root GitHub Pages wrapper must load the same cache-busted app module as the source page"
);
assert.match(growthWorkerSource, /id: "proof"[\s\S]*?proof: true/, "the comparison worker must expose a proof lane");
assert.match(
  growthWorkerSource,
  /id: "proof_nogood"[\s\S]*?proof: true,[\s\S]*?nogood: true/,
  "the comparison worker must expose the complementary exact-nogood proof lane"
);
assert.match(
  growthWorkerSource,
  /forced_move_layer_lag_cap: mode\.proof \? 0 : baseConfig\.forced_move_layer_lag_cap/,
  "the proof lane must disable the generational band"
);
assert.match(growthWorkerSource, /generic_failure_memo: mode\.proof/, "the proof lane must memoize exact failures");
assert.match(
  growthWorkerSource,
  /generic_failure_memo_symmetry: "fixed"/,
  "the proof lane must retain the benchmarked fixed-root failure memo"
);
assert.match(
  growthWorkerSource,
  /generic_geometric_nogood: !!mode\.nogood/,
  "only the complementary proof lane may enable translated nogoods"
);
assert.match(growthWorkerSource, /generic_geometric_nogood_max_clauses: 20000/);
assert.match(growthWorkerSource, /generic_geometric_nogood_index: true/);
assert.match(
  growthWorkerSource,
  /generic_geometric_nogood_activation_failure_states: mode\.nogood \? 25 : 0/,
  "the complementary web lane must delay nogood application until 25 failed states"
);
assert.match(
  growthWorkerSource,
  /seeded_tie_breaks: !!mode\.proof/,
  "the proof comparison lane must use replayable seeded tie diversification"
);
assert.match(
  growthWorkerSource,
  /generic_periodic_certificate_check_distinct_patches: !!mode\.proof/,
  "the proof comparison lane must check distinct branch patches at the same size"
);
assert.match(
  growthWorkerSource,
  /generic_periodic_certificate_checkpoint_sampling_policy: mode\.proof \? "hybrid" : "prefix"/,
  "the proof comparison lane must retain early patches and sample later branches"
);
assert.match(
  growthWorkerSource,
  /generic_periodic_certificate: !!mode\.proof/,
  "the proof lane must test a reached target patch for an exact translational quotient"
);
assert.match(growthWorkerSource, /exhaustive: !!mode\.proof/, "only the proof comparison lane may claim exhaustive search");
assert.match(growthWorkerSource, /certificateKind: final\?\.tiling_evidence\?\.kind/, "proof certificates must reach the UI");
assert.match(growthAppSource, /id: "proof"[\s\S]*?label: "Proof search · unbanded"/, "the proof trace must be visible in the chart");
assert.match(growthAppSource, /id: "proof_nogood"[\s\S]*?label: "Proof search · delayed nogoods"/, "the complementary proof trace must be visible in the chart");
assert.match(growthAppSource, /id: "proof_crystal"[\s\S]*?label: "Proof search · crystal order"/, "the crystal-ordered proof trace must be visible in the chart");
assert.match(growthWorkerSource, /id: "proof_crystal"[\s\S]*?moveOrder: "crystal"[\s\S]*?proof: true/, "the crystal lane must retain exact proof-search semantics");
assert.match(growthAppSource, /All eight modes finished\./, "the comparison status must include all eight lanes");
assert.match(growthAppSource, /finite-patch witnesses, not space-tiling certificates/, "the catalog must not overstate a large GCTS patch");
assert.match(
  growthAppSource,
  /this excludes those particular patches as translational fundamental domains, not other possible motifs/,
  "the catalog must state the narrow scope of a negative target-patch quotient check"
);
assert.match(growthAppSource, /4 unresolved lattice candidates/, "the periodic checkpoint rejection must leave four catalog candidates");
assert.match(
  growthAppSource,
  /hybrid branch screen saw/,
  "the catalog must expose the stronger distinct-branch checkpoint evidence"
);
assert.match(
  growthAppSource,
  /proper-rigid-motion patch fingerprints/,
  "the catalog must distinguish state-path check counts from globally distinct geometry"
);
assert.match(
  growthAppSource,
  /fixed-versus-rigid failure-memo replay produced identical search outcomes/,
  "the catalog must expose the measured reason for retaining fixed-root memo keys"
);
assert.match(
  growthAppSource,
  /complementary translation-equivariant nogood policy/,
  "the catalog must expose the complementary nogood screen"
);
assert.match(
  growthAppSource,
  /delayed until 25 failed states have been learned/,
  "the catalog must disclose the benchmarked nogood activation delay"
);
assert.match(
  growthAppSource,
  /On five unseen seeds/,
  "the catalog must expose the holdout generalization screen"
);
assert.match(
  growthAppSource,
  /remain complementary rather than universally superior/,
  "the catalog must not overstate delayed nogood generalization"
);
assert.match(
  growthAppSource,
  /that target patch is not a translational quotient/,
  "the completed proof-lane summary must retain the target-patch quotient result"
);

assert.equal(LATTICE_POLYHEDRON_CENSUS_POOL.length, 16, "the rescreener and catalog must share the full source pool");
assert.equal(
  LATTICE_POLYHEDRON_CENSUS_POOL.filter(candidate => candidate.screening.status === "exact_rejection").length,
  12,
  "all removed candidates must retain their exact rejection certificates"
);
assert.equal(LATTICE_POLYHEDRON_SCREENING.source_pool_size, LATTICE_POLYHEDRON_CENSUS_POOL.length);
const archivedScreening = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-rescreen-2026-08-17.json", import.meta.url),
  "utf8"
));
const archivedDiversifiedScreening = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-diversified-gcts-screen-2026-08-18.json", import.meta.url),
  "utf8"
));
const archivedProofScreening = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-gcts-checkpoint-screen-2026-08-18.json", import.meta.url),
  "utf8"
));
const archivedPrefixScreening = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-distinct-checkpoint-screen-2026-08-18.json", import.meta.url),
  "utf8"
));
const archivedDistinctScreening = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-hybrid-checkpoint-screen-2026-08-19.json", import.meta.url),
  "utf8"
));
const archivedFixedFrameOverlap = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-global-checkpoint-overlap-2026-08-19.json", import.meta.url),
  "utf8"
));
const archivedGlobalOverlap = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-rigid-checkpoint-overlap-2026-08-19.json", import.meta.url),
  "utf8"
));
const archivedFailureMemoAb = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-failure-memo-ab-2026-08-19.json", import.meta.url),
  "utf8"
));
const archivedNogoodPortfolio = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-nogood-proof-portfolio-2026-08-19.json", import.meta.url),
  "utf8"
));
const archivedDelayedNogood = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-delayed-nogood-screen-2026-08-19.json", import.meta.url),
  "utf8"
));
const archivedHoldout = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-holdout-screen-2026-08-19.json", import.meta.url),
  "utf8"
));
const archivedStagnationNogoodAb = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-stagnation-nogood-ab-2026-08-19.json", import.meta.url),
  "utf8"
));
const archivedBudgetOrder = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-budget-order-screen-2026-08-19.json", import.meta.url),
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
    screen_date: archivedDiversifiedScreening.screen_date,
    lane: archivedDiversifiedScreening.baseline_protocol.lane,
    target_tiles: archivedDiversifiedScreening.baseline_protocol.target_tiles,
    configured_node_limit: archivedDiversifiedScreening.baseline_protocol.configured_node_limit,
    time_limit_ms: archivedDiversifiedScreening.baseline_protocol.time_limit_ms,
    seeds: archivedDiversifiedScreening.baseline_protocol.seeds,
    seeded_tie_breaks: archivedDiversifiedScreening.baseline_protocol.seeded_tie_breaks,
    generation_band: archivedDiversifiedScreening.baseline_protocol.generation_band,
    exact_failure_memo: archivedDiversifiedScreening.baseline_protocol.exact_failure_memo,
    translation_equivariant_nogoods: archivedDiversifiedScreening.baseline_protocol.translation_equivariant_nogoods,
    mirrors: archivedDiversifiedScreening.baseline_protocol.mirrors
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
  archivedDiversifiedScreening.baseline_candidates
    .filter(candidate => LATTICE_POLYHEDRON_SURVIVORS.some(survivor => survivor.id === candidate.id))
    .map(candidate => ({
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
  LATTICE_POLYHEDRON_SCREENING.gcts_proof.checkpoint_quotient_check,
  {
    minimum_patch_tiles: archivedProofScreening.protocol.minimum_checkpoint_tiles,
    maximum_patch_tiles: archivedProofScreening.protocol.maximum_checkpoint_tiles,
    candidates_screened: archivedProofScreening.summary.candidates_screened,
    completed_checks: archivedProofScreening.summary.checkpoint_checks_completed,
    certificates_found: archivedProofScreening.summary.exact_periodic_rejections,
    rejected_candidate: archivedProofScreening.exact_periodic_rejection.id,
    certificate_method: archivedProofScreening.protocol.certificate_method,
    report: "data/lattice-polyhedron-gcts-checkpoint-screen-2026-08-18.json"
  },
  "runtime target-patch quotient evidence must match the archived exact checks"
);
assert.deepEqual(archivedProofScreening.summary.rejected_candidates, ["10_26470"]);
assert.deepEqual(
  LATTICE_POLYHEDRON_SCREENING.gcts_proof.distinct_patch_checkpoint_screen,
  {
    paths_screened: archivedDistinctScreening.summary.paths_screened,
    sampling_policy: archivedDistinctScreening.protocol.sampling_policy,
    sampling_prefix: archivedDistinctScreening.protocol.sampling_prefix,
    sampling_stride: archivedDistinctScreening.protocol.sampling_stride,
    maximum_checks_per_size_per_path:
      archivedDistinctScreening.protocol.maximum_checks_per_size_per_path,
    eligible_distinct_path_states: archivedDistinctScreening.summary.eligible_distinct_path_states,
    completed_checks: archivedDistinctScreening.summary.checkpoint_checks_completed,
    checks_timed_out: archivedDistinctScreening.summary.checkpoint_checks_timed_out,
    certificates_found: archivedDistinctScreening.summary.exact_periodic_certificates_found,
    sampling_skips: archivedDistinctScreening.summary.sampling_skips,
    duplicate_states_skipped: archivedDistinctScreening.summary.duplicate_states_skipped,
    per_size_cap_skips: archivedDistinctScreening.summary.per_size_cap_skips,
    fingerprint_equivalence: "orientation_preserving_cubic_rigid_motion",
    globally_distinct_candidate_states:
      archivedGlobalOverlap.summary.globally_distinct_candidate_states,
    repeated_state_path_pairs: archivedGlobalOverlap.summary.repeated_state_path_pairs,
    global_uniqueness_rate: archivedGlobalOverlap.summary.global_uniqueness_rate,
    report: "data/lattice-polyhedron-hybrid-checkpoint-screen-2026-08-19.json",
    overlap_report: "data/lattice-polyhedron-rigid-checkpoint-overlap-2026-08-19.json",
    prior_fixed_frame_overlap_report: "data/lattice-polyhedron-global-checkpoint-overlap-2026-08-19.json",
    prior_prefix_report: "data/lattice-polyhedron-distinct-checkpoint-screen-2026-08-18.json"
  },
  "runtime distinct-patch evidence must match the archived executed screen"
);
assert.deepEqual(
  LATTICE_POLYHEDRON_SCREENING.gcts_proof.failure_memo_ab,
  {
    paths_screened: archivedFailureMemoAb.summary.paths,
    fixed_and_rigid_outcomes_identical:
      archivedFailureMemoAb.summary.identical_bounded_search_outcomes,
    additional_rigid_memo_hits: archivedFailureMemoAb.summary.additional_rigid_memo_hits,
    observed_fixed_elapsed_ms: archivedFailureMemoAb.summary.fixed_elapsed_ms,
    observed_rigid_elapsed_ms: archivedFailureMemoAb.summary.rigid_elapsed_ms,
    observed_elapsed_ratio: archivedFailureMemoAb.summary.observed_elapsed_ratio,
    production_default: archivedFailureMemoAb.summary.production_default,
    report: "data/lattice-polyhedron-failure-memo-ab-2026-08-19.json"
  },
  "runtime failure-memo policy must match the controlled archived A/B"
);
assert.equal(archivedFailureMemoAb.benchmark_schema_version, 14);
assert.equal(archivedFailureMemoAb.paths.length, 12);
assert.ok(archivedFailureMemoAb.paths.every(path =>
  path.additional_rigid_hits === 0
  && path.fixed_memo_hits === path.rigid_memo_hits
  && path.observed_elapsed_ratio > 1
));
assert.deepEqual(
  LATTICE_POLYHEDRON_SCREENING.gcts_proof.complementary_nogood_screen,
  {
    paths_screened: archivedNogoodPortfolio.summary.paths_per_policy,
    improved_paths: archivedNogoodPortfolio.summary.improved_nogood_paths,
    equal_paths: archivedNogoodPortfolio.summary.equal_nogood_paths,
    worsened_paths: archivedNogoodPortfolio.summary.worsened_nogood_paths,
    target_hits: archivedNogoodPortfolio.summary.nogood_target_hits,
    learned_clauses: archivedNogoodPortfolio.summary.total_nogood_clauses,
    exact_prunes: archivedNogoodPortfolio.summary.total_nogood_prunes,
    checkpoint_checks_completed: archivedNogoodPortfolio.summary.nogood_checkpoint_checks_completed,
    checkpoint_checks_timed_out: archivedNogoodPortfolio.summary.nogood_checkpoint_checks_timed_out,
    periodic_certificates_found: archivedNogoodPortfolio.summary.nogood_periodic_certificates_found,
    new_rigid_motion_fingerprints: archivedNogoodPortfolio.summary.new_nogood_fingerprints,
    combined_rigid_motion_fingerprints: archivedNogoodPortfolio.summary.combined_distinct_fingerprints,
    policy_decision: archivedNogoodPortfolio.summary.policy_decision,
    report: "data/lattice-polyhedron-nogood-proof-portfolio-2026-08-19.json"
  },
  "the runtime complementary proof policy must match its archived A/B and exact screen"
);
assert.equal(archivedNogoodPortfolio.benchmark_schema_version, 14);
assert.equal(archivedNogoodPortfolio.proof_paths.length, 12);
assert.equal(archivedNogoodPortfolio.summary.nogood_checkpoint_state_path_checks, 1109);
assert.equal(archivedNogoodPortfolio.summary.nogood_checkpoint_checks_completed, 1109);
assert.equal(archivedNogoodPortfolio.summary.nogood_checkpoint_checks_timed_out, 0);
assert.equal(archivedNogoodPortfolio.summary.nogood_periodic_certificates_found, 0);
assert.equal(archivedNogoodPortfolio.summary.new_nogood_fingerprints, 823);
assert.equal(archivedNogoodPortfolio.summary.combined_distinct_fingerprints, 1874);
assert.equal(archivedNogoodPortfolio.summary.policy_decision, "complementary_proof_lane");
assert.ok(archivedNogoodPortfolio.proof_paths.every(path =>
  path.checks_attempted === path.fingerprints.length
  && path.checks_completed === path.checks_attempted
  && path.checks_timed_out === 0
  && !path.certificate_found
  && new Set(path.fingerprints).size === path.fingerprints.length
  && path.fingerprint_digest_sha256 === fingerprintDigest(path.fingerprints)
));
assert.deepEqual(
  archivedNogoodPortfolio.proof_paths
    .filter(path => path.target_check_completed)
    .map(path => ({ id: path.id, seed: path.seed, largest_patch: path.largest_patch })),
  [{ id: "10_45033", seed: 1, largest_patch: 40 }],
  "the complementary policy must retain its checked 40-tile 10_45033 witness"
);
for (const coverage of archivedNogoodPortfolio.candidate_coverage) {
  const priorCandidate = archivedGlobalOverlap.candidates.find(candidate => candidate.id === coverage.id);
  const prior = new Set(priorCandidate.paths.flatMap(path => path.fingerprints));
  const currentPaths = archivedNogoodPortfolio.proof_paths.filter(path => path.id === coverage.id);
  const current = new Set(currentPaths.flatMap(path => path.fingerprints));
  const combined = new Set([...prior, ...current]);
  assert.equal(coverage.prior_distinct_fingerprints, prior.size);
  assert.equal(coverage.nogood_distinct_fingerprints, current.size);
  assert.equal(coverage.shared_fingerprints, [...current].filter(value => prior.has(value)).length);
  assert.equal(coverage.new_fingerprints, [...current].filter(value => !prior.has(value)).length);
  assert.equal(coverage.combined_distinct_fingerprints, combined.size);
  assert.equal(coverage.combined_digest_sha256, fingerprintDigest([...combined]));
}
assert.deepEqual(
  LATTICE_POLYHEDRON_SCREENING.gcts_proof.delayed_nogood_screen,
  {
    paths_screened: archivedDelayedNogood.summary.paths_per_policy,
    activation_failure_states: 25,
    improved_over_immediate_paths: archivedDelayedNogood.summary.delayed_25_better_than_immediate,
    equal_to_immediate_paths: archivedDelayedNogood.summary.delayed_25_equal_to_immediate,
    worsened_from_immediate_paths: archivedDelayedNogood.summary.delayed_25_worse_than_immediate,
    target_hits: archivedDelayedNogood.summary.delayed_25_target_hits,
    learned_clauses: archivedDelayedNogood.summary.delayed_25_nogood_clauses,
    exact_prunes: archivedDelayedNogood.summary.delayed_25_nogood_prunes,
    checkpoint_checks_completed: archivedDelayedNogood.summary.delayed_checkpoint_checks_completed,
    checkpoint_checks_timed_out: archivedDelayedNogood.summary.delayed_checkpoint_checks_timed_out,
    periodic_certificates_found: archivedDelayedNogood.summary.delayed_periodic_certificates_found,
    new_rigid_motion_fingerprints: archivedDelayedNogood.summary.new_delayed_fingerprints,
    combined_rigid_motion_fingerprints: archivedDelayedNogood.summary.three_policy_fingerprints,
    policy_decision: archivedDelayedNogood.summary.policy_decision,
    report: "data/lattice-polyhedron-delayed-nogood-screen-2026-08-19.json"
  },
  "the runtime delayed proof policy must match its archived activation sweep and exact screen"
);
assert.equal(archivedDelayedNogood.benchmark_schema_version, 15);
assert.equal(archivedDelayedNogood.proof_paths.length, 12);
assert.deepEqual(
  archivedDelayedNogood.threshold_summary.find(summary => summary.activation_failure_states === 25),
  {
    activation_failure_states: 25,
    better_than_immediate: 2,
    equal_to_immediate: 10,
    worse_than_immediate: 0,
    better_than_baseline: 6,
    equal_to_baseline: 1,
    worse_than_baseline: 5,
    target_hits: 2
  }
);
assert.equal(archivedDelayedNogood.summary.delayed_checkpoint_checks_completed, 1116);
assert.equal(archivedDelayedNogood.summary.delayed_checkpoint_checks_timed_out, 0);
assert.equal(archivedDelayedNogood.summary.delayed_periodic_certificates_found, 0);
assert.equal(archivedDelayedNogood.summary.new_delayed_fingerprints, 199);
assert.equal(archivedDelayedNogood.summary.three_policy_fingerprints, 2073);
assert.equal(archivedDelayedNogood.summary.policy_decision, "replace_immediate_nogood_lane_with_delayed_25");
assert.ok(archivedDelayedNogood.proof_paths.every(path =>
  path.checks_attempted === path.fingerprints.length
  && path.checks_completed === path.checks_attempted
  && path.checks_timed_out === 0
  && !path.certificate_found
  && new Set(path.fingerprints).size === path.fingerprints.length
  && path.fingerprint_digest_sha256 === fingerprintDigest(path.fingerprints)
));
assert.deepEqual(
  archivedDelayedNogood.proof_paths
    .filter(path => path.target_check_completed)
    .map(path => ({ id: path.id, seed: path.seed, largest_patch: path.largest_patch })),
  [
    { id: "10_45033", seed: 1, largest_patch: 40 },
    { id: "10_45033", seed: 2, largest_patch: 40 }
  ],
  "the delayed policy must retain both checked 40-tile 10_45033 witnesses"
);
for (const coverage of archivedDelayedNogood.candidate_coverage) {
  const baselineCandidate = archivedGlobalOverlap.candidates.find(candidate => candidate.id === coverage.id);
  const baselineSet = new Set(baselineCandidate.paths.flatMap(path => path.fingerprints));
  const immediateSet = new Set(
    archivedNogoodPortfolio.proof_paths
      .filter(path => path.id === coverage.id)
      .flatMap(path => path.fingerprints)
  );
  const delayedSet = new Set(
    archivedDelayedNogood.proof_paths
      .filter(path => path.id === coverage.id)
      .flatMap(path => path.fingerprints)
  );
  const priorTwoPolicy = new Set([...baselineSet, ...immediateSet]);
  const threePolicy = new Set([...priorTwoPolicy, ...delayedSet]);
  assert.equal(coverage.baseline_distinct_fingerprints, baselineSet.size);
  assert.equal(coverage.immediate_distinct_fingerprints, immediateSet.size);
  assert.equal(coverage.delayed_distinct_fingerprints, delayedSet.size);
  assert.equal(coverage.prior_two_policy_fingerprints, priorTwoPolicy.size);
  assert.equal(coverage.new_delayed_fingerprints, [...delayedSet].filter(value => !priorTwoPolicy.has(value)).length);
  assert.equal(coverage.three_policy_fingerprints, threePolicy.size);
  assert.equal(coverage.three_policy_digest_sha256, fingerprintDigest([...threePolicy]));
}
assert.deepEqual(
  LATTICE_POLYHEDRON_SCREENING.gcts_proof.holdout_screen,
  {
    seeds: archivedHoldout.summary.holdout_seeds,
    paths_per_policy: archivedHoldout.summary.paths_per_policy,
    total_policy_paths: archivedHoldout.summary.total_policy_paths,
    delayed_better_than_immediate:
      archivedHoldout.generalization.holdout_seeds_4_through_8.delayed_better_than_immediate,
    delayed_equal_to_immediate:
      archivedHoldout.generalization.holdout_seeds_4_through_8.delayed_equal_to_immediate,
    delayed_worse_than_immediate:
      archivedHoldout.generalization.holdout_seeds_4_through_8.delayed_worse_than_immediate,
    baseline_target_hits: archivedHoldout.generalization.holdout_seeds_4_through_8.baseline_target_hits,
    immediate_target_hits: archivedHoldout.generalization.holdout_seeds_4_through_8.immediate_target_hits,
    delayed_target_hits: archivedHoldout.generalization.holdout_seeds_4_through_8.delayed_target_hits,
    checkpoint_checks_completed: archivedHoldout.summary.exact_checks_completed,
    checkpoint_checks_timed_out: archivedHoldout.summary.exact_checks_timed_out,
    periodic_certificates_found: archivedHoldout.summary.periodic_certificates_found,
    new_rigid_motion_fingerprints: archivedHoldout.summary.new_holdout_fingerprints,
    expanded_rigid_motion_fingerprints: archivedHoldout.summary.expanded_eight_seed_fingerprints,
    policy_decision: archivedHoldout.summary.policy_decision,
    report: "data/lattice-polyhedron-holdout-screen-2026-08-19.json"
  },
  "the runtime holdout evidence must match the archived five-seed exact screen"
);
assert.equal(archivedHoldout.benchmark_schema_version, 15);
assert.equal(archivedHoldout.search_paths.length, 20);
assert.equal(archivedHoldout.proof_paths.length, 60);
assert.equal(archivedHoldout.summary.exact_checks_completed, 5540);
assert.equal(archivedHoldout.summary.exact_checks_timed_out, 0);
assert.equal(archivedHoldout.summary.periodic_certificates_found, 0);
assert.equal(archivedHoldout.summary.completed_target_patch_checks, 4);
assert.equal(archivedHoldout.summary.distinct_target_witnesses, 2);
assert.equal(archivedHoldout.summary.new_holdout_fingerprints, 2758);
assert.equal(archivedHoldout.summary.expanded_eight_seed_fingerprints, 4831);
assert.equal(
  archivedHoldout.summary.policy_decision,
  "retain_delayed_25_as_complementary_holdout_supported_lane"
);
assert.deepEqual(
  archivedHoldout.generalization.holdout_seeds_4_through_8,
  {
    delayed_better_than_immediate: 5,
    delayed_equal_to_immediate: 14,
    delayed_worse_than_immediate: 1,
    delayed_better_than_baseline: 6,
    delayed_equal_to_baseline: 3,
    delayed_worse_than_baseline: 11,
    baseline_target_hits: 1,
    immediate_target_hits: 1,
    delayed_target_hits: 2
  }
);
assert.deepEqual(
  LATTICE_POLYHEDRON_SCREENING.gcts_proof.stagnation_nogood_ab,
  {
    training_thresholds: archivedStagnationNogoodAb.protocol.training_stagnation_failure_thresholds,
    selected_holdout_threshold: archivedStagnationNogoodAb.protocol.selected_holdout_threshold,
    training_paths_per_policy: archivedStagnationNogoodAb.summary.training_paths_per_policy,
    holdout_paths: archivedStagnationNogoodAb.summary.holdout_paths,
    training_10_better_than_fixed_delayed_25:
      archivedStagnationNogoodAb.training_summary[0].better_than_fixed_delayed_25,
    training_10_equal_to_fixed_delayed_25:
      archivedStagnationNogoodAb.training_summary[0].equal_to_fixed_delayed_25,
    training_10_worse_than_fixed_delayed_25:
      archivedStagnationNogoodAb.training_summary[0].worse_than_fixed_delayed_25,
    training_10_target_hits: archivedStagnationNogoodAb.training_summary[0].target_hits,
    holdout_10_better_than_fixed_delayed_25:
      archivedStagnationNogoodAb.holdout_summary.better_than_fixed_delayed_25,
    holdout_10_equal_to_fixed_delayed_25:
      archivedStagnationNogoodAb.holdout_summary.equal_to_fixed_delayed_25,
    holdout_10_worse_than_fixed_delayed_25:
      archivedStagnationNogoodAb.holdout_summary.worse_than_fixed_delayed_25,
    holdout_10_target_hits: archivedStagnationNogoodAb.holdout_summary.target_hits,
    fixed_delayed_25_holdout_target_hits:
      archivedStagnationNogoodAb.holdout_summary.fixed_delayed_25_target_hits,
    policy_decision: archivedStagnationNogoodAb.summary.policy_decision,
    report: "data/lattice-polyhedron-stagnation-nogood-ab-2026-08-19.json"
  },
  "the runtime policy decision must include the archived stagnation-gate rejection"
);
assert.equal(archivedStagnationNogoodAb.benchmark_schema_version, 16);
assert.equal(archivedStagnationNogoodAb.summary.policy_decision, "reject_stagnation_gate_retain_fixed_delayed_25");
assert.deepEqual(archivedStagnationNogoodAb.summary.combined_stagnation_10, {
  better_than_fixed_delayed_25: 0,
  equal_to_fixed_delayed_25: 27,
  worse_than_fixed_delayed_25: 5,
  target_hits: 3,
  fixed_delayed_25_target_hits: 4
});
assert.deepEqual(
  LATTICE_POLYHEDRON_SCREENING.gcts_proof.budget_order_screen,
  {
    target_tiles: archivedBudgetOrder.protocol.target_tiles,
    training_seeds: archivedBudgetOrder.protocol.training_seeds,
    holdout_seeds: archivedBudgetOrder.protocol.holdout_seeds,
    baseline_node_limits: archivedBudgetOrder.protocol.baseline_node_limits,
    balanced_1000_target_hits: archivedBudgetOrder.budget_scaling.summary.balanced_1000.target_hits,
    balanced_2000_target_hits: archivedBudgetOrder.budget_scaling.summary.balanced_2000.target_hits,
    balanced_2000_exact_target_checks: archivedBudgetOrder.budget_scaling.summary.exact_target_checks_completed,
    frontier_order_decision: archivedBudgetOrder.frontier_order_screen.policy_decision,
    crystal_better_than_balanced: archivedBudgetOrder.move_order_screen.combined_comparison.better,
    crystal_equal_to_balanced: archivedBudgetOrder.move_order_screen.combined_comparison.equal,
    crystal_worse_than_balanced: archivedBudgetOrder.move_order_screen.combined_comparison.worse,
    balanced_target_hits: archivedBudgetOrder.move_order_screen.combined_comparison.baseline_target_hits,
    crystal_target_hits: archivedBudgetOrder.move_order_screen.combined_comparison.challenger_target_hits,
    exact_target_checks_completed: archivedBudgetOrder.move_order_screen.exact_target_checks_completed,
    exact_target_checks_timed_out: archivedBudgetOrder.move_order_screen.exact_target_checks_timed_out,
    periodic_certificates_found: archivedBudgetOrder.move_order_screen.periodic_certificates_found,
    distinct_candidate_target_witnesses: archivedBudgetOrder.move_order_screen.distinct_candidate_target_witnesses,
    policy_decision: archivedBudgetOrder.move_order_screen.policy_decision,
    report: "data/lattice-polyhedron-budget-order-screen-2026-08-19.json"
  },
  "the runtime crystal-lane decision must match the archived budget and order screen"
);
assert.deepEqual(archivedBudgetOrder.benchmark_schema_versions, [16, 17]);
assert.deepEqual(archivedBudgetOrder.move_order_screen.training_comparison, {
  better: 8,
  equal: 0,
  worse: 4,
  baseline_target_hits: 1,
  challenger_target_hits: 3
});
assert.deepEqual(archivedBudgetOrder.move_order_screen.holdout_comparison, {
  better: 13,
  equal: 0,
  worse: 7,
  baseline_target_hits: 0,
  challenger_target_hits: 4
});
assert.ok(archivedBudgetOrder.budget_scaling.summary.all_paths_non_decreasing);
assert.equal(archivedBudgetOrder.frontier_order_screen.policy_decision, "retain_mrv");
assert.equal(archivedBudgetOrder.move_order_screen.exact_target_checks_completed, 8);
assert.equal(archivedBudgetOrder.move_order_screen.exact_target_checks_timed_out, 0);
assert.equal(archivedBudgetOrder.move_order_screen.periodic_certificates_found, 0);
assert.equal(archivedBudgetOrder.move_order_screen.distinct_candidate_target_witnesses, 6);
assert.ok(archivedBudgetOrder.move_order_screen.exact_target_proofs.every(path =>
  path.target_check_completed && !path.target_check_timed_out && !path.target_certificate_found
));
for (const path of archivedDelayedNogood.paths) {
  for (const outcome of [path.baseline, path.immediate, ...Object.values(path.delayed)]) {
    assert.ok(outcome.max_live_tiles >= outcome.largest_patch);
    assert.equal(outcome.uncaptured_max_live_tiles, outcome.max_live_tiles - outcome.largest_patch);
  }
}
for (const path of archivedHoldout.search_paths) {
  for (const outcome of [path.baseline, path.immediate, path.delayed_25]) {
    assert.ok(outcome.max_live_tiles >= outcome.largest_patch);
    assert.equal(outcome.uncaptured_max_live_tiles, outcome.max_live_tiles - outcome.largest_patch);
    assert.equal(outcome.growth_milestones.at(-1).patch_size, outcome.largest_patch);
    assert.equal(outcome.growth_milestones.at(-1).witness_hash, outcome.witness_hash);
  }
}
assert.ok(archivedHoldout.proof_paths.every(path =>
  path.checks_attempted === path.fingerprints.length
  && path.checks_completed === path.checks_attempted
  && path.checks_timed_out === 0
  && !path.certificate_found
  && new Set(path.fingerprints).size === path.fingerprints.length
  && path.fingerprint_digest_sha256 === fingerprintDigest(path.fingerprints)
));
for (const coverage of archivedHoldout.candidate_coverage) {
  const priorBaselineCandidate = archivedGlobalOverlap.candidates.find(candidate => candidate.id === coverage.id);
  const priorSet = new Set([
    ...priorBaselineCandidate.paths.flatMap(path => path.fingerprints),
    ...archivedNogoodPortfolio.proof_paths
      .filter(path => path.id === coverage.id)
      .flatMap(path => path.fingerprints),
    ...archivedDelayedNogood.proof_paths
      .filter(path => path.id === coverage.id)
      .flatMap(path => path.fingerprints)
  ]);
  const holdoutByPolicy = Object.fromEntries(["baseline", "immediate", "delayed"].map(policy => [
    policy,
    new Set(archivedHoldout.proof_paths
      .filter(path => path.id === coverage.id && path.policy === policy)
      .flatMap(path => path.fingerprints))
  ]));
  const holdoutUnion = new Set(Object.values(holdoutByPolicy).flatMap(set => [...set]));
  const expanded = new Set([...priorSet, ...holdoutUnion]);
  assert.equal(coverage.prior_three_policy_fingerprints, priorSet.size);
  assert.equal(coverage.holdout_baseline_fingerprints, holdoutByPolicy.baseline.size);
  assert.equal(coverage.holdout_immediate_fingerprints, holdoutByPolicy.immediate.size);
  assert.equal(coverage.holdout_delayed_fingerprints, holdoutByPolicy.delayed.size);
  assert.equal(coverage.holdout_union_fingerprints, holdoutUnion.size);
  assert.equal(coverage.new_holdout_fingerprints, [...holdoutUnion].filter(value => !priorSet.has(value)).length);
  assert.equal(coverage.expanded_eight_seed_fingerprints, expanded.size);
  assert.equal(coverage.expanded_digest_sha256, fingerprintDigest([...expanded]));
}
assert.equal(archivedDistinctScreening.paths.length, 12);
assert.ok(
  archivedDistinctScreening.paths.every(path =>
    path.checks_attempted === path.checks_completed
    && path.checks_timed_out === 0
    && !path.certificate_found
    && path.eligible_states === path.checks_attempted
      + path.sampling_skips
      + path.per_size_cap_skips
      + path.total_cap_skips
      + path.time_budget_skips
  ),
  "every archived distinct-patch check must be complete and internally accounted"
);
assert.deepEqual(
  archivedDistinctScreening.paths.map(path => ({ id: path.id, seed: path.seed, witness_hash: path.witness_hash })),
  archivedPrefixScreening.paths.map(path => ({ id: path.id, seed: path.seed, witness_hash: path.witness_hash })),
  "the prefix and hybrid policies must replay exactly the same GCTS paths"
);
assert.equal(
  archivedDistinctScreening.policy_comparison.prefix_checks_completed
    + archivedDistinctScreening.policy_comparison.spread_diagnostic_checks_completed
    - archivedDistinctScreening.policy_comparison.shared_first_patch_checks,
  archivedDistinctScreening.summary.checkpoint_checks_completed,
  "the hybrid evidence must be the exact union of prefix and later-branch samples"
);
assert.equal(archivedGlobalOverlap.source_benchmark_schema_version, 13);
assert.equal(archivedGlobalOverlap.prior_outcome_report, LATTICE_POLYHEDRON_SCREENING.gcts_proof.distinct_patch_checkpoint_screen.report);
assert.equal(
  archivedGlobalOverlap.prior_fingerprint_report,
  LATTICE_POLYHEDRON_SCREENING.gcts_proof.distinct_patch_checkpoint_screen.prior_fixed_frame_overlap_report
);
assert.equal(archivedGlobalOverlap.fingerprint.equivalence, "orientation-preserving cubic rigid motion");
assert.equal(archivedGlobalOverlap.summary.paths, archivedDistinctScreening.summary.paths_screened);
assert.equal(archivedGlobalOverlap.summary.state_path_pairs, archivedDistinctScreening.summary.checkpoint_checks_completed);
assert.equal(archivedGlobalOverlap.summary.exact_checks_completed, archivedGlobalOverlap.summary.state_path_pairs);
assert.equal(archivedGlobalOverlap.summary.exact_checks_timed_out, 0);
assert.equal(archivedGlobalOverlap.summary.exact_periodic_certificates_found, 0);
assert.deepEqual(
  archivedGlobalOverlap.candidates.flatMap(candidate => candidate.paths.map(path => ({
    id: candidate.id,
    seed: path.seed,
    witness_hash: path.witness_hash
  }))),
  archivedDistinctScreening.paths.map(path => ({ id: path.id, seed: path.seed, witness_hash: path.witness_hash })),
  "global fingerprint accounting must replay the same archived GCTS paths"
);
const globalCandidateFingerprints = [];
for (const overlapCandidate of archivedGlobalOverlap.candidates) {
  const union = new Set();
  const pathSets = new Map();
  const membership = new Map();
  let statePathPairs = 0;
  for (const path of overlapCandidate.paths) {
    assert.equal(path.fingerprints.length, path.checks_attempted);
    assert.equal(path.checks_completed + path.checks_timed_out, path.checks_attempted);
    assert.ok(path.fingerprints.every(value => /^[0-9a-f]{32}$/.test(value)));
    assert.equal(new Set(path.fingerprints).size, path.fingerprints.length);
    assert.equal(path.fingerprint_digest_sha256, fingerprintDigest(path.fingerprints));
    pathSets.set(path.seed, new Set(path.fingerprints));
    statePathPairs += path.fingerprints.length;
    path.fingerprints.forEach(fingerprint => {
      union.add(fingerprint);
      if (!membership.has(fingerprint)) membership.set(fingerprint, new Set());
      membership.get(fingerprint).add(path.seed);
    });
  }
  assert.equal(overlapCandidate.state_path_pairs, statePathPairs);
  assert.equal(overlapCandidate.globally_distinct_fingerprints, union.size);
  assert.equal(overlapCandidate.repeated_state_path_pairs, statePathPairs - union.size);
  assert.equal(overlapCandidate.union_digest_sha256, fingerprintDigest([...union]));
  const membershipHistogram = {};
  for (const seeds of membership.values()) {
    membershipHistogram[seeds.size] = (membershipHistogram[seeds.size] ?? 0) + 1;
  }
  assert.deepEqual(overlapCandidate.path_membership_histogram, membershipHistogram);
  for (const pair of overlapCandidate.pairwise_intersections) {
    const [leftSeed, rightSeed] = pair.seeds;
    const left = pathSets.get(leftSeed);
    const right = pathSets.get(rightSeed);
    const shared = [...left].filter(fingerprint => right.has(fingerprint)).length;
    const pairUnion = left.size + right.size - shared;
    assert.equal(pair.shared_fingerprints, shared);
    assert.equal(pair.union_fingerprints, pairUnion);
    assert.equal(pair.jaccard, pairUnion ? shared / pairUnion : 0);
  }
  for (const fingerprint of union) globalCandidateFingerprints.push(`${overlapCandidate.id}:${fingerprint}`);
}
assert.equal(
  archivedGlobalOverlap.summary.globally_distinct_candidate_states,
  archivedGlobalOverlap.candidates.reduce((sum, candidate) => sum + candidate.globally_distinct_fingerprints, 0)
);
assert.equal(
  archivedGlobalOverlap.summary.repeated_state_path_pairs,
  archivedGlobalOverlap.summary.state_path_pairs
    - archivedGlobalOverlap.summary.globally_distinct_candidate_states
);
assert.equal(
  archivedGlobalOverlap.summary.globally_distinct_digest_sha256,
  fingerprintDigest(globalCandidateFingerprints)
);
assert.equal(
  archivedFixedFrameOverlap.summary.globally_distinct_candidate_states
    - archivedGlobalOverlap.summary.globally_distinct_candidate_states,
  2,
  "proper rigid-motion canonicalization must identify the two rotated fixed-frame duplicates"
);
assert.ok(
  archivedGlobalOverlap.candidates.every(candidate => {
    const fixedFrame = archivedFixedFrameOverlap.candidates.find(item => item.id === candidate.id);
    return candidate.globally_distinct_fingerprints <= fixedFrame.globally_distinct_fingerprints;
  }),
  "a stronger equivalence relation must never increase a candidate's distinct-state count"
);
assert.ok(
  archivedProofScreening.paths
    .filter(path => path.id !== "10_26470")
    .every(path => path.checks_completed === 39 && !path.certificate_found)
  ,
  "all surviving focused paths must complete every size checkpoint without a certificate"
);
assert.ok(
  archivedProofScreening.paths.every(
    path => path.checks_timed_out === 0
  ),
  "the checkpoint screen must not hide an incomplete certificate check"
);
for (const candidate of LATTICE_POLYHEDRON_SURVIVORS) {
  const witness = archivedProofScreening.paths.find(item => item.id === candidate.id);
  assert.ok(witness, `${candidate.id} must retain its focused 40-tile witness`);
  assert.equal(candidate.gcts_proof_screening.focused_witness_hash, witness.witness_hash);
  assert.equal(candidate.gcts_proof_screening.checkpoint_quotient_checks, 39);
  assert.equal(candidate.gcts_proof_screening.checkpoint_quotient_certificates, 0);
  const distinctSummary = archivedDistinctScreening.candidate_summary.find(item => item.id === candidate.id);
  assert.ok(distinctSummary, `${candidate.id} must retain its distinct-branch screen summary`);
  assert.equal(candidate.gcts_proof_screening.distinct_checkpoint_paths, distinctSummary.paths);
  assert.equal(candidate.gcts_proof_screening.distinct_checkpoint_eligible_states, distinctSummary.eligible_states);
  assert.equal(candidate.gcts_proof_screening.distinct_checkpoint_checks, distinctSummary.checks_completed);
  assert.equal(candidate.gcts_proof_screening.distinct_checkpoint_max_size, distinctSummary.maximum_patch);
  assert.equal(candidate.gcts_proof_screening.distinct_checkpoint_certificates, distinctSummary.certificates_found);
  assert.equal(candidate.gcts_proof_screening.distinct_checkpoint_timeouts, distinctSummary.checks_timed_out);
  assert.equal(candidate.gcts_proof_screening.distinct_checkpoint_sampling_skips, distinctSummary.sampling_skips);
  assert.equal(candidate.gcts_proof_screening.distinct_checkpoint_duplicate_skips, distinctSummary.duplicate_states_skipped);
  assert.equal(candidate.gcts_proof_screening.distinct_checkpoint_cap_skips, distinctSummary.per_size_cap_skips);
  const overlapSummary = archivedGlobalOverlap.candidates.find(item => item.id === candidate.id);
  assert.ok(overlapSummary, `${candidate.id} must retain its global checkpoint coverage summary`);
  assert.equal(candidate.gcts_proof_screening.global_checkpoint_states, overlapSummary.globally_distinct_fingerprints);
  assert.equal(candidate.gcts_proof_screening.repeated_checkpoint_path_pairs, overlapSummary.repeated_state_path_pairs);
  const nogoodSummary = archivedDelayedNogood.candidate_summary.find(item => item.id === candidate.id);
  const nogoodCoverage = archivedDelayedNogood.candidate_coverage.find(item => item.id === candidate.id);
  assert.ok(nogoodSummary && nogoodCoverage, `${candidate.id} must retain its delayed nogood evidence`);
  assert.equal(candidate.gcts_proof_screening.nogood_robust_largest_patch, nogoodSummary.delayed_25_robust_largest_patch);
  assert.equal(candidate.gcts_proof_screening.nogood_median_largest_patch, nogoodSummary.delayed_25_median_largest_patch);
  assert.equal(candidate.gcts_proof_screening.nogood_best_largest_patch, nogoodSummary.delayed_25_best_largest_patch);
  assert.equal(candidate.gcts_proof_screening.nogood_target_hits, nogoodSummary.delayed_25_target_hits);
  assert.equal(candidate.gcts_proof_screening.portfolio_robust_largest_patch, nogoodSummary.baseline_delayed_portfolio_robust_largest_patch);
  assert.equal(candidate.gcts_proof_screening.portfolio_median_largest_patch, nogoodSummary.baseline_delayed_portfolio_median_largest_patch);
  assert.equal(candidate.gcts_proof_screening.portfolio_best_largest_patch, nogoodSummary.baseline_delayed_portfolio_best_largest_patch);
  assert.equal(candidate.gcts_proof_screening.portfolio_target_hits, nogoodSummary.baseline_delayed_portfolio_target_hits);
  assert.equal(candidate.gcts_proof_screening.nogood_checkpoint_checks, nogoodCoverage.delayed_state_path_checks);
  assert.equal(candidate.gcts_proof_screening.nogood_checkpoint_distinct, nogoodCoverage.delayed_distinct_fingerprints);
  assert.equal(candidate.gcts_proof_screening.nogood_new_checkpoint_states, nogoodCoverage.new_delayed_fingerprints);
  assert.equal(candidate.gcts_proof_screening.combined_checkpoint_states, nogoodCoverage.three_policy_fingerprints);
  const holdoutSummary = archivedHoldout.candidate_summary.find(item => item.id === candidate.id);
  const holdoutCoverage = archivedHoldout.candidate_coverage.find(item => item.id === candidate.id);
  assert.ok(holdoutSummary && holdoutCoverage, `${candidate.id} must retain its holdout evidence`);
  assert.equal(candidate.gcts_proof_screening.holdout_trials, archivedHoldout.summary.holdout_seeds.length);
  assert.equal(
    candidate.gcts_proof_screening.holdout_nogood_robust_largest_patch,
    holdoutSummary.holdout_delayed_robust_largest_patch
  );
  assert.equal(
    candidate.gcts_proof_screening.holdout_nogood_median_largest_patch,
    holdoutSummary.holdout_delayed_median_largest_patch
  );
  assert.equal(
    candidate.gcts_proof_screening.holdout_nogood_best_largest_patch,
    holdoutSummary.holdout_delayed_best_largest_patch
  );
  assert.equal(
    candidate.gcts_proof_screening.holdout_nogood_target_hits,
    holdoutSummary.holdout_delayed_target_hits
  );
  assert.equal(candidate.gcts_proof_screening.holdout_checkpoint_checks, holdoutCoverage.holdout_checks_completed);
  assert.equal(candidate.gcts_proof_screening.holdout_new_checkpoint_states, holdoutCoverage.new_holdout_fingerprints);
  assert.equal(candidate.gcts_proof_screening.expanded_checkpoint_states, holdoutCoverage.expanded_eight_seed_fingerprints);
  const crystalSummary = archivedBudgetOrder.move_order_screen.candidate_summary.find(item => item.id === candidate.id);
  assert.ok(crystalSummary, `${candidate.id} must retain its balanced-versus-crystal evidence`);
  assert.equal(candidate.gcts_proof_screening.crystal_trials, crystalSummary.paths);
  assert.equal(candidate.gcts_proof_screening.crystal_better_than_balanced, crystalSummary.crystal_better);
  assert.equal(candidate.gcts_proof_screening.crystal_equal_to_balanced, crystalSummary.crystal_equal);
  assert.equal(candidate.gcts_proof_screening.crystal_worse_than_balanced, crystalSummary.crystal_worse);
  assert.equal(candidate.gcts_proof_screening.crystal_robust_largest_patch, crystalSummary.crystal_robust_largest_patch);
  assert.equal(candidate.gcts_proof_screening.crystal_median_largest_patch, crystalSummary.crystal_median_largest_patch);
  assert.equal(candidate.gcts_proof_screening.crystal_best_largest_patch, crystalSummary.crystal_best_largest_patch);
  assert.equal(candidate.gcts_proof_screening.crystal_target_hits, crystalSummary.crystal_target_hits);
  assert.equal(
    candidate.gcts_proof_screening.crystal_distinct_target_witnesses,
    crystalSummary.crystal_distinct_target_witnesses
  );
}
assert.deepEqual(
  LATTICE_POLYHEDRON_CENSUS_POOL
    .filter(candidate => candidate.screening.status === "exact_rejection")
    .filter(candidate => candidate.id !== archivedProofScreening.exact_periodic_rejection.id)
    .map(candidate => ({
      id: candidate.id,
      certificate: candidate.screening.certificate,
      motif_tiles: candidate.screening.motif_tiles,
      period_vectors: candidate.screening.period_vectors
    })),
  archivedScreening.exact_rejections,
  "the original runtime rejection certificates must match the archived exact rescreen"
);
const checkpointRejection = LATTICE_POLYHEDRON_CENSUS_POOL.find(
  candidate => candidate.id === archivedProofScreening.exact_periodic_rejection.id
);
assert.deepEqual(
  {
    certificate: checkpointRejection?.screening.certificate,
    motif_tiles: checkpointRejection?.screening.motif_tiles,
    period_vectors: checkpointRejection?.screening.period_vectors
  },
  {
    certificate: "translational",
    motif_tiles: archivedProofScreening.exact_periodic_rejection.patch_tiles,
    period_vectors: archivedProofScreening.exact_periodic_rejection.period_vectors
  },
  "the newly rejected candidate must retain its exact checkpoint certificate"
);
assert.equal(archivedProofScreening.exact_periodic_rejection.motif.length, 8);
assert.equal(archivedProofScreening.exact_periodic_rejection.proof.boundary_face_count, 30);
assert.equal(archivedProofScreening.exact_periodic_rejection.proof.boundary_pairing.length, 15);
assert.equal(archivedProofScreening.exact_periodic_rejection.proof.motif_volume, 16);
assert.equal(archivedProofScreening.exact_periodic_rejection.proof.lattice_determinant, 16);
assert.deepEqual(
  LATTICE_POLYHEDRON_CENSUS_POOL
    .filter(candidate => candidate.screening.status === "inconclusive")
    .map(candidate => candidate.id),
  archivedProofScreening.summary.inconclusive_survivors,
  "the public survivors must match the checkpoint-screen result"
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
assert.equal(candidates.length, 4, "certified periodic and isohedral tiles must not remain in the catalog");
assert.ok(!candidates.some(figure => figure.census_candidate.id === "10_26470"));
const survivors = candidates;
assert.deepEqual(
  survivors.map(figure => figure.census_candidate.survivor_priority),
  Array.from({ length: 4 }, (_, index) => index + 1),
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
