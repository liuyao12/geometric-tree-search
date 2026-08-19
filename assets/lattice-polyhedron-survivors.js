// One runtime source of truth for the 16 Blanco–Santos lattice-polyhedron
// candidates screened by GCTS. A rejection here always carries a replayable
// exact certificate; a survivor only records the limits of a bounded search.
export const LATTICE_POLYHEDRON_SCREENING = Object.freeze({
  screen_date: "2026-08-17",
  source_pool_size: 16,
  model: "face-to-face congruent lattice-polyhedron tilings using proper cubic lattice orientations",
  translational: Object.freeze({ seconds_per_tile: 20, maximum_requested_motif_tiles: 8 }),
  isohedral: Object.freeze({ seconds_per_tile: 60, growth_horizon_tiles: 60 }),
  gcts_proof: Object.freeze({
    screen_date: "2026-08-18",
    lane: "free_range_unbanded",
    target_tiles: 40,
    configured_node_limit: 500,
    time_limit_seconds: 30,
    seeds: Object.freeze([1, 2, 3]),
    seeded_tie_breaks: true,
    generation_band: false,
    exact_failure_memo: true,
    translation_equivariant_nogoods: false,
    mirrors: false,
    report: "data/lattice-polyhedron-gcts-checkpoint-screen-2026-08-18.json",
    prior_report: "data/lattice-polyhedron-diversified-gcts-screen-2026-08-18.json",
    checkpoint_quotient_check: Object.freeze({
      minimum_patch_tiles: 2,
      maximum_patch_tiles: 40,
      candidates_screened: 5,
      completed_checks: 163,
      certificates_found: 1,
      rejected_candidate: "10_26470",
      certificate_method: "face_paired_boundary_equal_covolume",
      report: "data/lattice-polyhedron-gcts-checkpoint-screen-2026-08-18.json"
    }),
    distinct_patch_checkpoint_screen: Object.freeze({
      paths_screened: 12,
      sampling_policy: "hybrid",
      sampling_prefix: 4,
      sampling_stride: 16,
      maximum_checks_per_size_per_path: 7,
      eligible_distinct_path_states: 5744,
      completed_checks: 1093,
      checks_timed_out: 0,
      certificates_found: 0,
      sampling_skips: 3950,
      duplicate_states_skipped: 277,
      per_size_cap_skips: 701,
      fingerprint_equivalence: "orientation_preserving_cubic_rigid_motion",
      globally_distinct_candidate_states: 1051,
      repeated_state_path_pairs: 42,
      global_uniqueness_rate: 0.9615736505032022,
      report: "data/lattice-polyhedron-hybrid-checkpoint-screen-2026-08-19.json",
      overlap_report: "data/lattice-polyhedron-rigid-checkpoint-overlap-2026-08-19.json",
      prior_fixed_frame_overlap_report: "data/lattice-polyhedron-global-checkpoint-overlap-2026-08-19.json",
      prior_prefix_report: "data/lattice-polyhedron-distinct-checkpoint-screen-2026-08-18.json"
    }),
    failure_memo_ab: Object.freeze({
      paths_screened: 12,
      fixed_and_rigid_outcomes_identical: 12,
      additional_rigid_memo_hits: 0,
      observed_fixed_elapsed_ms: 52371,
      observed_rigid_elapsed_ms: 57996,
      observed_elapsed_ratio: 1.107406770922839,
      production_default: "fixed",
      report: "data/lattice-polyhedron-failure-memo-ab-2026-08-19.json"
    }),
    complementary_nogood_screen: Object.freeze({
      paths_screened: 12,
      improved_paths: 5,
      equal_paths: 1,
      worsened_paths: 6,
      target_hits: 1,
      learned_clauses: 68628,
      exact_prunes: 35154,
      checkpoint_checks_completed: 1109,
      checkpoint_checks_timed_out: 0,
      periodic_certificates_found: 0,
      new_rigid_motion_fingerprints: 823,
      combined_rigid_motion_fingerprints: 1874,
      policy_decision: "complementary_proof_lane",
      report: "data/lattice-polyhedron-nogood-proof-portfolio-2026-08-19.json"
    }),
    delayed_nogood_screen: Object.freeze({
      paths_screened: 12,
      activation_failure_states: 25,
      improved_over_immediate_paths: 2,
      equal_to_immediate_paths: 10,
      worsened_from_immediate_paths: 0,
      target_hits: 2,
      learned_clauses: 66585,
      exact_prunes: 34908,
      checkpoint_checks_completed: 1116,
      checkpoint_checks_timed_out: 0,
      periodic_certificates_found: 0,
      new_rigid_motion_fingerprints: 199,
      combined_rigid_motion_fingerprints: 2073,
      policy_decision: "replace_immediate_nogood_lane_with_delayed_25",
      report: "data/lattice-polyhedron-delayed-nogood-screen-2026-08-19.json"
    }),
    holdout_screen: Object.freeze({
      seeds: Object.freeze([4, 5, 6, 7, 8]),
      paths_per_policy: 20,
      total_policy_paths: 60,
      delayed_better_than_immediate: 5,
      delayed_equal_to_immediate: 14,
      delayed_worse_than_immediate: 1,
      baseline_target_hits: 1,
      immediate_target_hits: 1,
      delayed_target_hits: 2,
      checkpoint_checks_completed: 5540,
      checkpoint_checks_timed_out: 0,
      periodic_certificates_found: 0,
      new_rigid_motion_fingerprints: 2758,
      expanded_rigid_motion_fingerprints: 4831,
      policy_decision: "retain_delayed_25_as_complementary_holdout_supported_lane",
      report: "data/lattice-polyhedron-holdout-screen-2026-08-19.json"
    }),
    stagnation_nogood_ab: Object.freeze({
      training_thresholds: Object.freeze([10, 25, 50]),
      selected_holdout_threshold: 10,
      training_paths_per_policy: 12,
      holdout_paths: 20,
      training_10_better_than_fixed_delayed_25: 0,
      training_10_equal_to_fixed_delayed_25: 11,
      training_10_worse_than_fixed_delayed_25: 1,
      training_10_target_hits: 2,
      holdout_10_better_than_fixed_delayed_25: 0,
      holdout_10_equal_to_fixed_delayed_25: 16,
      holdout_10_worse_than_fixed_delayed_25: 4,
      holdout_10_target_hits: 1,
      fixed_delayed_25_holdout_target_hits: 2,
      policy_decision: "reject_stagnation_gate_retain_fixed_delayed_25",
      report: "data/lattice-polyhedron-stagnation-nogood-ab-2026-08-19.json"
    })
  })
});

const GCTS_PROOF_SCREENING_RESULTS = Object.freeze({
  "10_16113": Object.freeze({ outcome: "focused_target_patch", robust_largest_patch: 21, median_largest_patch: 22, best_largest_patch: 27, target_hits: 0, trials: 3, focused_target_witness: true, focused_seed: 3, focused_visited_nodes: 2312, focused_witness_hash: "b4c8e0c893b1eb7c", checkpoint_quotient_checks: 39, checkpoint_quotient_certificates: 0, distinct_checkpoint_paths: 3, distinct_checkpoint_eligible_states: 1837, distinct_checkpoint_checks: 306, distinct_checkpoint_max_size: 27, distinct_checkpoint_certificates: 0, distinct_checkpoint_timeouts: 0, distinct_checkpoint_sampling_skips: 1302, distinct_checkpoint_duplicate_skips: 51, distinct_checkpoint_cap_skips: 229, global_checkpoint_states: 295, repeated_checkpoint_path_pairs: 11, nogood_robust_largest_patch: 26, nogood_median_largest_patch: 28, nogood_best_largest_patch: 31, nogood_target_hits: 0, portfolio_robust_largest_patch: 27, portfolio_median_largest_patch: 28, portfolio_best_largest_patch: 31, portfolio_target_hits: 0, nogood_checkpoint_checks: 374, nogood_checkpoint_distinct: 358, nogood_new_checkpoint_states: 71, combined_checkpoint_states: 676, holdout_trials: 5, holdout_nogood_robust_largest_patch: 26, holdout_nogood_median_largest_patch: 30, holdout_nogood_best_largest_patch: 40, holdout_nogood_target_hits: 1, holdout_checkpoint_checks: 1838, holdout_new_checkpoint_states: 892, expanded_checkpoint_states: 1568 }),
  "10_45026": Object.freeze({ outcome: "focused_target_patch", robust_largest_patch: 14, median_largest_patch: 16, best_largest_patch: 17, target_hits: 0, trials: 3, focused_target_witness: true, focused_seed: 1, focused_seeded_tie_breaks: false, focused_visited_nodes: 4278, focused_witness_hash: "e16dbe38a0165b93", checkpoint_quotient_checks: 39, checkpoint_quotient_certificates: 0, distinct_checkpoint_paths: 3, distinct_checkpoint_eligible_states: 1287, distinct_checkpoint_checks: 215, distinct_checkpoint_max_size: 17, distinct_checkpoint_certificates: 0, distinct_checkpoint_timeouts: 0, distinct_checkpoint_sampling_skips: 916, distinct_checkpoint_duplicate_skips: 160, distinct_checkpoint_cap_skips: 156, global_checkpoint_states: 192, repeated_checkpoint_path_pairs: 23, nogood_robust_largest_patch: 14, nogood_median_largest_patch: 17, nogood_best_largest_patch: 20, nogood_target_hits: 0, portfolio_robust_largest_patch: 14, portfolio_median_largest_patch: 17, portfolio_best_largest_patch: 20, portfolio_target_hits: 0, nogood_checkpoint_checks: 235, nogood_checkpoint_distinct: 212, nogood_new_checkpoint_states: 48, combined_checkpoint_states: 411, holdout_trials: 5, holdout_nogood_robust_largest_patch: 14, holdout_nogood_median_largest_patch: 16, holdout_nogood_best_largest_patch: 21, holdout_nogood_target_hits: 0, holdout_checkpoint_checks: 1129, holdout_new_checkpoint_states: 648, expanded_checkpoint_states: 1059 }),
  "10_45033": Object.freeze({ outcome: "focused_target_patch", robust_largest_patch: 23, median_largest_patch: 27, best_largest_patch: 36, target_hits: 0, trials: 3, focused_target_witness: true, focused_seed: 2, focused_visited_nodes: 1162, focused_witness_hash: "deb51611a30f25b5", checkpoint_quotient_checks: 39, checkpoint_quotient_certificates: 0, distinct_checkpoint_paths: 3, distinct_checkpoint_eligible_states: 1221, distinct_checkpoint_checks: 262, distinct_checkpoint_max_size: 36, distinct_checkpoint_certificates: 0, distinct_checkpoint_timeouts: 0, distinct_checkpoint_sampling_skips: 762, distinct_checkpoint_duplicate_skips: 44, distinct_checkpoint_cap_skips: 197, global_checkpoint_states: 256, repeated_checkpoint_path_pairs: 6, nogood_robust_largest_patch: 21, nogood_median_largest_patch: 40, nogood_best_largest_patch: 40, nogood_target_hits: 2, portfolio_robust_largest_patch: 27, portfolio_median_largest_patch: 40, portfolio_best_largest_patch: 40, portfolio_target_hits: 2, nogood_checkpoint_checks: 291, nogood_checkpoint_distinct: 285, nogood_new_checkpoint_states: 72, combined_checkpoint_states: 535, holdout_trials: 5, holdout_nogood_robust_largest_patch: 21, holdout_nogood_median_largest_patch: 32, holdout_nogood_best_largest_patch: 40, holdout_nogood_target_hits: 1, holdout_checkpoint_checks: 1361, holdout_new_checkpoint_states: 635, expanded_checkpoint_states: 1170 }),
  "9_11683": Object.freeze({ outcome: "focused_target_patch", robust_largest_patch: 19, median_largest_patch: 25, best_largest_patch: 32, target_hits: 0, trials: 3, focused_target_witness: true, focused_seed: 3, focused_visited_nodes: 591, focused_witness_hash: "5ab75954f9e80239", checkpoint_quotient_checks: 39, checkpoint_quotient_certificates: 0, distinct_checkpoint_paths: 3, distinct_checkpoint_eligible_states: 1399, distinct_checkpoint_checks: 310, distinct_checkpoint_max_size: 32, distinct_checkpoint_certificates: 0, distinct_checkpoint_timeouts: 0, distinct_checkpoint_sampling_skips: 970, distinct_checkpoint_duplicate_skips: 22, distinct_checkpoint_cap_skips: 119, global_checkpoint_states: 308, repeated_checkpoint_path_pairs: 2, nogood_robust_largest_patch: 15, nogood_median_largest_patch: 16, nogood_best_largest_patch: 19, nogood_target_hits: 0, portfolio_robust_largest_patch: 19, portfolio_median_largest_patch: 25, portfolio_best_largest_patch: 32, portfolio_target_hits: 0, nogood_checkpoint_checks: 216, nogood_checkpoint_distinct: 213, nogood_new_checkpoint_states: 8, combined_checkpoint_states: 451, holdout_trials: 5, holdout_nogood_robust_largest_patch: 13, holdout_nogood_median_largest_patch: 16, holdout_nogood_best_largest_patch: 25, holdout_nogood_target_hits: 0, holdout_checkpoint_checks: 1212, holdout_new_checkpoint_states: 583, expanded_checkpoint_states: 1034 })
});

const rejected = (certificate, motifTiles, periodVectors) => ({
  status: "exact_rejection",
  certificate,
  motif_tiles: motifTiles,
  period_vectors: periodVectors
});

export const LATTICE_POLYHEDRON_CENSUS_POOL = [
  { id: "8_2480", vertices: [[0,0,2],[0,1,0],[1,0,0],[1,1,2],[1,2,0],[2,1,0]], screening: rejected("translational", 2, [[-1,-1,0],[-1,0,-2],[0,-1,-2]]) },
  { id: "9_9043", vertices: [[0,0,1],[0,1,0],[1,1,2],[1,2,1],[2,0,1],[2,1,0]], screening: rejected("translational", 2, [[0,-1,-1],[-1,-1,1],[-1,1,-1]]) },
  { id: "9_11679", vertices: [[-1,-1,0],[-1,0,1],[0,-1,0],[0,0,-1],[0,0,1],[0,1,0],[1,0,0],[1,1,-1]], screening: rejected("translational", 2, [[0,-1,-1],[0,-1,1],[-2,-1,0]]) },
  { id: "10_27010", vertices: [[0,0,0],[0,1,1],[1,0,1],[1,1,2],[1,2,0],[2,0,0],[2,1,1]], screening: rejected("isohedral_periodic_quotient", 24, [[0,0,-4],[-4,0,0],[0,-4,0]]) },
  { id: "10_24235", vertices: [[-1,0,0],[-1,0,2],[0,-1,0],[0,1,0],[0,1,2],[1,0,0]], screening: rejected("translational", 2, [[-1,-1,0],[-1,1,0],[0,0,-2]]) },
  { id: "9_3239", vertices: [[-1,-1,0],[-1,0,-2],[0,-1,-2],[0,0,2],[0,1,0],[1,0,0]], screening: rejected("translational", 2, [[-1,0,-2],[0,-1,-2],[-1,-1,2]]) },
  { id: "10_16113", priority: 1, vertices: [[0,1,0],[0,2,1],[1,0,-1],[1,0,2],[1,1,-1],[2,1,0]], screening: { status: "inconclusive" } },
  { id: "10_44867", vertices: [[0,1,0],[0,1,1],[1,0,0],[1,0,1],[1,1,2],[1,2,0],[2,1,0],[2,2,1]], screening: rejected("translational", 2, [[-1,1,0],[-1,-1,-1],[-1,0,2]]) },
  { id: "10_45035", vertices: [[0,0,1],[0,1,0],[0,1,2],[0,2,1],[1,0,0],[1,0,1],[1,1,0],[1,1,1],[2,0,0]], screening: rejected("translational", 2, [[0,-1,-1],[0,-1,1],[-2,0,-1]]) },
  { id: "8_2431", vertices: [[-1,0,-1],[0,-1,-1],[0,0,2],[0,1,0],[1,0,0],[1,1,3]], screening: rejected("translational", 2, [[-1,-1,1],[-1,0,3],[0,-1,3]]) },
  { id: "10_24775", vertices: [[-1,-1,0],[-1,1,1],[0,0,2],[0,1,-1],[1,0,0],[1,2,1]], screening: rejected("translational", 3, [[-1,-1,2],[-1,-2,-1],[-2,1,-1]]) },
  { id: "10_26470", vertices: [[-1,0,0],[-1,0,1],[0,-1,0],[0,1,0],[0,1,2],[1,0,0],[1,0,1]], screening: rejected("translational", 8, [[-2,-2,0],[-2,0,2],[-2,2,0]]) },
  { id: "10_44266", vertices: [[0,0,2],[0,1,0],[1,0,0],[1,1,2],[1,2,-1],[1,2,0],[2,1,-1],[2,1,0]], screening: rejected("translational", 2, [[-1,-1,0],[-1,1,0],[-1,-2,-3]]) },
  { id: "10_45026", priority: 2, vertices: [[0,0,2],[0,1,1],[1,0,1],[1,1,0],[1,1,2],[1,2,0],[1,2,1],[2,1,0],[2,1,1]], screening: { status: "inconclusive" } },
  { id: "10_45033", priority: 3, vertices: [[0,0,0],[0,0,1],[0,1,1],[1,0,1],[1,1,0],[1,1,2],[1,2,1],[2,1,1],[2,2,2]], screening: { status: "inconclusive" } },
  { id: "9_11683", priority: 4, vertices: [[0,1,0],[0,1,1],[1,0,1],[1,1,0],[1,1,2],[1,2,1],[2,0,2],[2,1,1]], screening: { status: "inconclusive" } }
];

export const classifyLatticeCandidateScreen = ({ translational, isohedral }) => {
  if (translational?.provenImpossible || isohedral?.provenImpossible) return "reject_certified_non_tiler";
  if (translational?.certified) return "reject_certified_periodic";
  if (isohedral?.certified) return "reject_certified_isohedral";
  if (translational?.incomplete || isohedral?.incomplete) return "inconclusive";
  return "survives_completed_bounded_screens";
};

export const LATTICE_POLYHEDRON_SURVIVORS = LATTICE_POLYHEDRON_CENSUS_POOL
  .filter(candidate => candidate.screening.status === "inconclusive")
  .sort((left, right) => left.priority - right.priority)
  .map(candidate => ({
    ...candidate,
    lattice_points: Number(candidate.id.split("_")[0]),
    registry_id: `census_${candidate.id}`,
    name: `Candidate ${candidate.id}`,
    survivor_priority: candidate.priority,
    survivor_count: 4,
    last_screening: LATTICE_POLYHEDRON_SCREENING,
    gcts_proof_screening: GCTS_PROOF_SCREENING_RESULTS[candidate.id],
    description: `Unresolved Blanco–Santos census candidate ${candidate.id}; survivor ${candidate.priority} of 4 after GCTS checkpoint quotient screening of the original 16-tile pool.`
  }));
