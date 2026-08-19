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
    }),
    budget_order_screen: Object.freeze({
      target_tiles: 60,
      training_seeds: Object.freeze([1, 2, 3]),
      holdout_seeds: Object.freeze([4, 5, 6, 7, 8]),
      baseline_node_limits: Object.freeze([1000, 2000]),
      balanced_1000_target_hits: 1,
      balanced_2000_target_hits: 4,
      balanced_2000_exact_target_checks: 4,
      frontier_order_decision: "retain_mrv",
      crystal_better_than_balanced: 21,
      crystal_equal_to_balanced: 0,
      crystal_worse_than_balanced: 11,
      balanced_target_hits: 1,
      crystal_target_hits: 7,
      exact_target_checks_completed: 8,
      exact_target_checks_timed_out: 0,
      periodic_certificates_found: 0,
      distinct_candidate_target_witnesses: 6,
      policy_decision: "add_crystal_as_complementary_proof_lane_retain_balanced",
      report: "data/lattice-polyhedron-budget-order-screen-2026-08-19.json"
    }),
    internal_period_screen: Object.freeze({
      target_tiles: 60,
      seeds: Object.freeze([1, 2, 3, 4, 5, 6, 7, 8]),
      breadth_time_limit_ms: 5000,
      configured_node_limit: 1000,
      internal_period_vector_limit: 48,
      breadth_paths: 32,
      geometric_rank_3_paths: 32,
      repeated_translation_rank_3_paths: 28,
      breadth_target_hits: 0,
      focused_candidate: "10_16113",
      focused_seed: 6,
      focused_search_time_limit_ms: 30000,
      focused_target_checks_completed: 1,
      focused_candidate_bases_tested: 9139,
      focused_periodic_certificates_found: 0,
      legacy_target_witnesses_checked: 7,
      highly_collinear_10_45026_witnesses: 4,
      positive_control: "10_24775",
      positive_control_motif_tiles: 3,
      policy_decision: "replace_affine_rank_gate_with_repeated_translation_rank",
      report: "data/lattice-polyhedron-internal-period-screen-2026-08-19.json"
    }),
    global_extension_screen: Object.freeze({
      target_tiles: 60,
      seeds: Object.freeze([1, 2, 3]),
      configured_node_limit: 1000,
      trials: 12,
      target_hits: 12,
      distinct_witnesses: 9,
      geometric_rank_3_witnesses: 12,
      repeated_translation_rank_3_witnesses: 12,
      exact_target_checks_completed: 12,
      exact_target_checks_timed_out: 0,
      internal_period_bases_tested: 148471,
      periodic_certificates_found: 0,
      search_correction: "global_face_extensions_and_applied_placement_node_accounting",
      supersedes_vertex_mrv_depth_comparisons: true,
      report: "data/lattice-polyhedron-global-extension-screen-2026-08-19.json"
    }),
    complete_shell_screen: Object.freeze({
      maximum_target_shell: 7,
      seeds: Object.freeze([1, 2, 3]),
      time_limit_ms: 60000,
      configured_node_limit: 2000000,
      cascade: true,
      shell_definition: "minimum face-adjacency distance from the root among owners of exposed faces",
      global_zero_face_pruning: true,
      zero_face_rule: "a fixed exposed face with no legal face-mate is permanently unfillable",
      rejected_candidates: Object.freeze(["10_16113", "10_45026", "9_11683"]),
      surviving_candidate: null,
      periodic_candidate: "10_45033",
      robust_completed_shell: 4,
      maximum_completed_shell: 7,
      shell_five_hits: 1,
      shell_five_trials: 3,
      shell_five_witness_tiles: 464,
      shell_six_hits: 2,
      shell_six_trials: 3,
      shell_six_witness_tiles: 764,
      shell_seven_hits: 1,
      shell_seven_trials: 3,
      shell_seven_witness_tiles: 1174,
      report: "data/lattice-polyhedron-extendable-shell-screen-2026-08-19.json",
      continuation_report: "data/lattice-polyhedron-10_45033-shell-continuation-2026-08-19.json",
      periodic_certificate_report: "data/lattice-polyhedron-10_45033-periodic-certificate-2026-08-19.json"
    })
  })
});

const GCTS_PROOF_SCREENING_RESULTS = Object.freeze({
  "10_16113": Object.freeze({ outcome: "focused_target_patch", robust_largest_patch: 21, median_largest_patch: 22, best_largest_patch: 27, target_hits: 0, trials: 3, focused_target_witness: true, focused_seed: 3, focused_visited_nodes: 2312, focused_witness_hash: "b4c8e0c893b1eb7c", checkpoint_quotient_checks: 39, checkpoint_quotient_certificates: 0, distinct_checkpoint_paths: 3, distinct_checkpoint_eligible_states: 1837, distinct_checkpoint_checks: 306, distinct_checkpoint_max_size: 27, distinct_checkpoint_certificates: 0, distinct_checkpoint_timeouts: 0, distinct_checkpoint_sampling_skips: 1302, distinct_checkpoint_duplicate_skips: 51, distinct_checkpoint_cap_skips: 229, global_checkpoint_states: 295, repeated_checkpoint_path_pairs: 11, nogood_robust_largest_patch: 26, nogood_median_largest_patch: 28, nogood_best_largest_patch: 31, nogood_target_hits: 0, portfolio_robust_largest_patch: 27, portfolio_median_largest_patch: 28, portfolio_best_largest_patch: 31, portfolio_target_hits: 0, nogood_checkpoint_checks: 374, nogood_checkpoint_distinct: 358, nogood_new_checkpoint_states: 71, combined_checkpoint_states: 676, holdout_trials: 5, holdout_nogood_robust_largest_patch: 26, holdout_nogood_median_largest_patch: 30, holdout_nogood_best_largest_patch: 40, holdout_nogood_target_hits: 1, holdout_checkpoint_checks: 1838, holdout_new_checkpoint_states: 892, expanded_checkpoint_states: 1568, crystal_trials: 8, crystal_better_than_balanced: 5, crystal_equal_to_balanced: 0, crystal_worse_than_balanced: 3, crystal_robust_largest_patch: 29, crystal_median_largest_patch: 38, crystal_best_largest_patch: 52, crystal_target_hits: 0, crystal_distinct_target_witnesses: 0 }),
  "10_45026": Object.freeze({ outcome: "focused_target_patch", robust_largest_patch: 14, median_largest_patch: 16, best_largest_patch: 17, target_hits: 0, trials: 3, focused_target_witness: true, focused_seed: 1, focused_seeded_tie_breaks: false, focused_visited_nodes: 4278, focused_witness_hash: "e16dbe38a0165b93", checkpoint_quotient_checks: 39, checkpoint_quotient_certificates: 0, distinct_checkpoint_paths: 3, distinct_checkpoint_eligible_states: 1287, distinct_checkpoint_checks: 215, distinct_checkpoint_max_size: 17, distinct_checkpoint_certificates: 0, distinct_checkpoint_timeouts: 0, distinct_checkpoint_sampling_skips: 916, distinct_checkpoint_duplicate_skips: 160, distinct_checkpoint_cap_skips: 156, global_checkpoint_states: 192, repeated_checkpoint_path_pairs: 23, nogood_robust_largest_patch: 14, nogood_median_largest_patch: 17, nogood_best_largest_patch: 20, nogood_target_hits: 0, portfolio_robust_largest_patch: 14, portfolio_median_largest_patch: 17, portfolio_best_largest_patch: 20, portfolio_target_hits: 0, nogood_checkpoint_checks: 235, nogood_checkpoint_distinct: 212, nogood_new_checkpoint_states: 48, combined_checkpoint_states: 411, holdout_trials: 5, holdout_nogood_robust_largest_patch: 14, holdout_nogood_median_largest_patch: 16, holdout_nogood_best_largest_patch: 21, holdout_nogood_target_hits: 0, holdout_checkpoint_checks: 1129, holdout_new_checkpoint_states: 648, expanded_checkpoint_states: 1059, crystal_trials: 8, crystal_better_than_balanced: 7, crystal_equal_to_balanced: 0, crystal_worse_than_balanced: 1, crystal_robust_largest_patch: 20, crystal_median_largest_patch: 60, crystal_best_largest_patch: 60, crystal_target_hits: 4, crystal_distinct_target_witnesses: 2 }),
  "10_45033": Object.freeze({ outcome: "focused_target_patch", robust_largest_patch: 23, median_largest_patch: 27, best_largest_patch: 36, target_hits: 0, trials: 3, focused_target_witness: true, focused_seed: 2, focused_visited_nodes: 1162, focused_witness_hash: "deb51611a30f25b5", checkpoint_quotient_checks: 39, checkpoint_quotient_certificates: 0, distinct_checkpoint_paths: 3, distinct_checkpoint_eligible_states: 1221, distinct_checkpoint_checks: 262, distinct_checkpoint_max_size: 36, distinct_checkpoint_certificates: 0, distinct_checkpoint_timeouts: 0, distinct_checkpoint_sampling_skips: 762, distinct_checkpoint_duplicate_skips: 44, distinct_checkpoint_cap_skips: 197, global_checkpoint_states: 256, repeated_checkpoint_path_pairs: 6, nogood_robust_largest_patch: 21, nogood_median_largest_patch: 40, nogood_best_largest_patch: 40, nogood_target_hits: 2, portfolio_robust_largest_patch: 27, portfolio_median_largest_patch: 40, portfolio_best_largest_patch: 40, portfolio_target_hits: 2, nogood_checkpoint_checks: 291, nogood_checkpoint_distinct: 285, nogood_new_checkpoint_states: 72, combined_checkpoint_states: 535, holdout_trials: 5, holdout_nogood_robust_largest_patch: 21, holdout_nogood_median_largest_patch: 32, holdout_nogood_best_largest_patch: 40, holdout_nogood_target_hits: 1, holdout_checkpoint_checks: 1361, holdout_new_checkpoint_states: 635, expanded_checkpoint_states: 1170, crystal_trials: 8, crystal_better_than_balanced: 7, crystal_equal_to_balanced: 0, crystal_worse_than_balanced: 1, crystal_robust_largest_patch: 32, crystal_median_largest_patch: 41, crystal_best_largest_patch: 60, crystal_target_hits: 1, crystal_distinct_target_witnesses: 1 }),
  "9_11683": Object.freeze({ outcome: "focused_target_patch", robust_largest_patch: 19, median_largest_patch: 25, best_largest_patch: 32, target_hits: 0, trials: 3, focused_target_witness: true, focused_seed: 3, focused_visited_nodes: 591, focused_witness_hash: "5ab75954f9e80239", checkpoint_quotient_checks: 39, checkpoint_quotient_certificates: 0, distinct_checkpoint_paths: 3, distinct_checkpoint_eligible_states: 1399, distinct_checkpoint_checks: 310, distinct_checkpoint_max_size: 32, distinct_checkpoint_certificates: 0, distinct_checkpoint_timeouts: 0, distinct_checkpoint_sampling_skips: 970, distinct_checkpoint_duplicate_skips: 22, distinct_checkpoint_cap_skips: 119, global_checkpoint_states: 308, repeated_checkpoint_path_pairs: 2, nogood_robust_largest_patch: 15, nogood_median_largest_patch: 16, nogood_best_largest_patch: 19, nogood_target_hits: 0, portfolio_robust_largest_patch: 19, portfolio_median_largest_patch: 25, portfolio_best_largest_patch: 32, portfolio_target_hits: 0, nogood_checkpoint_checks: 216, nogood_checkpoint_distinct: 213, nogood_new_checkpoint_states: 8, combined_checkpoint_states: 451, holdout_trials: 5, holdout_nogood_robust_largest_patch: 13, holdout_nogood_median_largest_patch: 16, holdout_nogood_best_largest_patch: 25, holdout_nogood_target_hits: 0, holdout_checkpoint_checks: 1212, holdout_new_checkpoint_states: 583, expanded_checkpoint_states: 1034, crystal_trials: 8, crystal_better_than_balanced: 2, crystal_equal_to_balanced: 0, crystal_worse_than_balanced: 6, crystal_robust_largest_patch: 18, crystal_median_largest_patch: 29, crystal_best_largest_patch: 60, crystal_target_hits: 2, crystal_distinct_target_witnesses: 2 })
});

const INTERNAL_PERIOD_SCREENING_RESULTS = Object.freeze({
  "10_16113": Object.freeze({ internal_period_trials: 8, internal_period_robust_largest_patch: 27, internal_period_median_largest_patch: 32, internal_period_best_largest_patch: 41, internal_period_geometric_rank_3_paths: 8, internal_period_repeated_translation_rank_3_paths: 8, internal_period_target_hits: 0, internal_period_focused_target: true, internal_period_focused_seed: 6, internal_period_focused_witness_hash: "c978bfa88e0dfc9e", internal_period_candidate_bases_tested: 9139, internal_period_max_translation_support: 5, internal_period_certificate_found: false }),
  "10_45026": Object.freeze({ internal_period_trials: 8, internal_period_robust_largest_patch: 14, internal_period_median_largest_patch: 18, internal_period_best_largest_patch: 22, internal_period_geometric_rank_3_paths: 8, internal_period_repeated_translation_rank_3_paths: 8, internal_period_target_hits: 0 }),
  "10_45033": Object.freeze({ internal_period_trials: 8, internal_period_robust_largest_patch: 21, internal_period_median_largest_patch: 32, internal_period_best_largest_patch: 37, internal_period_geometric_rank_3_paths: 8, internal_period_repeated_translation_rank_3_paths: 8, internal_period_target_hits: 0 }),
  "9_11683": Object.freeze({ internal_period_trials: 8, internal_period_robust_largest_patch: 18, internal_period_median_largest_patch: 35, internal_period_best_largest_patch: 43, internal_period_geometric_rank_3_paths: 8, internal_period_repeated_translation_rank_3_paths: 4, internal_period_target_hits: 0 })
});

const GLOBAL_EXTENSION_SCREENING_RESULTS = Object.freeze({
  "10_16113": Object.freeze({ global_extension_trials: 3, global_extension_target_hits: 3, global_extension_distinct_witnesses: 1, global_extension_minimum_isotropy: 0.9374999999999999, global_extension_max_candidates: 111, global_extension_exact_target_checks: 3, global_extension_internal_period_bases_tested: 12180, global_extension_periodic_certificates: 0 }),
  "10_45026": Object.freeze({ global_extension_trials: 3, global_extension_target_hits: 3, global_extension_distinct_witnesses: 2, global_extension_minimum_isotropy: 1, global_extension_max_candidates: 210, global_extension_exact_target_checks: 3, global_extension_internal_period_bases_tested: 51888, global_extension_periodic_certificates: 0 }),
  "10_45033": Object.freeze({ global_extension_trials: 3, global_extension_target_hits: 3, global_extension_distinct_witnesses: 3, global_extension_minimum_isotropy: 1, global_extension_max_candidates: 448, global_extension_exact_target_checks: 3, global_extension_internal_period_bases_tested: 51888, global_extension_periodic_certificates: 0 }),
  "9_11683": Object.freeze({ global_extension_trials: 3, global_extension_target_hits: 3, global_extension_distinct_witnesses: 3, global_extension_minimum_isotropy: 1, global_extension_max_candidates: 229, global_extension_exact_target_checks: 3, global_extension_internal_period_bases_tested: 32515, global_extension_periodic_certificates: 0 })
});

const rejected = (certificate, motifTiles, periodVectors, periodicTemplate = null) => ({
  status: "exact_rejection",
  certificate,
  motif_tiles: motifTiles,
  period_vectors: periodVectors,
  ...(periodicTemplate ? { periodic_template: periodicTemplate } : {})
});
const shellRejected = shellDepth => ({
  status: "exact_rejection",
  certificate: "finite_extendable_shell_obstruction",
  shell_depth: shellDepth,
  report: "data/lattice-polyhedron-extendable-shell-screen-2026-08-19.json"
});

const PERIODIC_TEMPLATE_10_45033 = Object.freeze({
  kind: "6_tile_periodic_symmetry_quotient",
  period_vectors: Object.freeze([[-2,-2,2],[0,-1,3],[-3,0,1]].map(Object.freeze)),
  motif: Object.freeze([
    { prototile_idx: 0, orientation_index: 0, orientation_id: "0:0", translation: [0,0,0] },
    { prototile_idx: 0, orientation_index: 14, orientation_id: "0:14", translation: [0,1,1] },
    { prototile_idx: 0, orientation_index: 17, orientation_id: "0:17", translation: [1,0,1] },
    { prototile_idx: 0, orientation_index: 21, orientation_id: "0:21", translation: [1,2,-1] },
    { prototile_idx: 0, orientation_index: 6, orientation_id: "0:6", translation: [2,1,-1] },
    { prototile_idx: 0, orientation_index: 11, orientation_id: "0:11", translation: [2,2,0] }
  ].map(entry => Object.freeze({ ...entry, translation: Object.freeze(entry.translation) })))
});

const frozenPeriodicTemplate = (periodVectors, motif) => Object.freeze({
  kind: `${motif.length}_tile_periodic_symmetry_quotient`,
  period_vectors: Object.freeze(periodVectors.map(vector => Object.freeze(vector))),
  motif: Object.freeze(motif.map(([orientation_index, translation]) => Object.freeze({
    prototile_idx: 0,
    orientation_index,
    orientation_id: `0:${orientation_index}`,
    translation: Object.freeze(translation)
  })))
});

const SIZE11_PERIODIC_TEMPLATES = Object.freeze({
  "11_38606": frozenPeriodicTemplate([[-1,1,1],[-2,-1,0],[0,-1,2]], [[0,[0,0,0]],[21,[0,-1,0]]]),
  "11_57333": frozenPeriodicTemplate([[0,-1,0],[-1,-1,-4],[-1,1,4]], [[0,[0,0,0]],[1,[0,-1,-4]]]),
  "11_60154": frozenPeriodicTemplate([[-2,0,0],[0,-2,0],[0,0,-2]], [[0,[0,0,0]],[2,[-1,-1,0]],[1,[0,-1,-1]]]),
  "11_146131": frozenPeriodicTemplate([[-1,-1,0],[-1,1,0],[-1,0,4]], [[0,[0,0,0]],[11,[-1,0,1]]]),
  "11_151715": frozenPeriodicTemplate([[0,-1,1],[-1,1,1],[-6,-3,-5]], [[0,[0,0,0]],[7,[-1,-2,0]],[7,[1,0,2]],[0,[-2,-2,-2]],[0,[2,2,2]]]),
  "11_155503": frozenPeriodicTemplate([[-1,-1,0],[-1,1,0],[-1,0,-3]], [[0,[0,0,0]],[11,[0,0,-3]]])
});

export const LATTICE_POLYHEDRON_SIZE11_SCREENING = Object.freeze({
  screen_date: "2026-08-19",
  source_pool_size: 156464,
  source_parts: 16,
  local_edge_obstructions: 156400,
  extendable_shell_one_obstructions: 56,
  shell_one_survivors: 8,
  shell_three_non_tilers: 2,
  certified_periodic_tilers: 6,
  unresolved: 0,
  model: "face-to-face congruent lattice-polyhedron tilings using integer translations and proper cubic rotations",
  first_stage_report: "data/lattice-polyhedron-size11-first-stage-2026-08-19.json",
  shell_report: "data/lattice-polyhedron-size11-shell3-2026-08-19.json",
  periodic_report: "data/lattice-polyhedron-size11-periodic-summary-2026-08-19.json"
});

const SIZE11_CANDIDATE_GEOMETRY = Object.freeze([
  { id: "11_34718", vertices: [[-1,0,-1],[0,-1,-1],[0,0,5],[0,1,0],[1,0,0],[1,1,6]], obstruction_shell: 3 },
  { id: "11_34757", vertices: [[-1,0,0],[0,-1,0],[0,0,5],[0,1,0],[1,-1,5],[1,0,0]], obstruction_shell: 3 },
  { id: "11_38606", vertices: [[-1,0,-1],[-1,1,1],[0,-1,0],[0,0,2],[1,1,-1],[2,0,0]] },
  { id: "11_57333", vertices: [[-1,0,0],[-1,1,0],[0,-1,4],[0,0,4],[1,0,0],[1,1,0]] },
  { id: "11_60154", vertices: [[0,1,0],[0,1,2],[1,0,1],[1,2,1],[2,1,0],[2,1,2]] },
  { id: "11_146131", vertices: [[-1,0,-1],[-1,0,0],[0,-1,-1],[0,-1,0],[0,0,3],[0,1,0],[1,0,0],[1,1,3]] },
  { id: "11_151715", vertices: [[0,1,0],[0,2,1],[1,0,1],[1,1,-2],[1,1,2],[1,2,-1],[2,0,-1],[2,1,0]] },
  { id: "11_155503", vertices: [[0,0,2],[0,0,3],[0,1,0],[0,1,1],[1,0,0],[1,0,1],[1,1,2],[1,2,0],[2,1,0]] }
]);

export const LATTICE_POLYHEDRON_SIZE11_CONTROLS = SIZE11_CANDIDATE_GEOMETRY.map(candidate => {
  const template = SIZE11_PERIODIC_TEMPLATES[candidate.id];
  const screening = template
    ? {
        ...rejected("translational", template.motif.length, template.period_vectors, template),
        periodic_source: "exact quotient found after the complete-shell screen",
        report: LATTICE_POLYHEDRON_SIZE11_SCREENING.periodic_report
      }
    : {
        ...shellRejected(candidate.obstruction_shell),
        report: LATTICE_POLYHEDRON_SIZE11_SCREENING.shell_report
      };
  return Object.freeze({
    id: candidate.id,
    vertices: candidate.vertices,
    lattice_points: 11,
    registry_id: `census_${candidate.id}`,
    name: `Candidate ${candidate.id}`,
    screening: Object.freeze(screening),
    last_screening: LATTICE_POLYHEDRON_SIZE11_SCREENING,
    shell_screening: Object.freeze(template
      ? { deepest_completed_shell: candidate.id === "11_57333" || candidate.id === "11_155503" ? 5 : 4, periodic_motif_tiles: template.motif.length }
      : { deepest_completed_shell: 2, obstruction_shell: 3, robust: true, obstruction_kind: "permanently_unfillable_face" }),
    gcts_proof_screening: Object.freeze({}),
    description: template
      ? `Size-11 periodic control ${candidate.id}; exact GCTS screening found a ${template.motif.length}-tile translational quotient.`
      : `Size-11 non-tiler control ${candidate.id}; exhaustive GCTS reaches shell 2 but proves shell 3 impossible.`
  });
});

export const LATTICE_POLYHEDRON_CENSUS_POOL = [
  { id: "8_2480", vertices: [[0,0,2],[0,1,0],[1,0,0],[1,1,2],[1,2,0],[2,1,0]], screening: rejected("translational", 2, [[-1,-1,0],[-1,0,-2],[0,-1,-2]]) },
  { id: "9_9043", vertices: [[0,0,1],[0,1,0],[1,1,2],[1,2,1],[2,0,1],[2,1,0]], screening: rejected("translational", 2, [[0,-1,-1],[-1,-1,1],[-1,1,-1]]) },
  { id: "9_11679", vertices: [[-1,-1,0],[-1,0,1],[0,-1,0],[0,0,-1],[0,0,1],[0,1,0],[1,0,0],[1,1,-1]], screening: rejected("translational", 2, [[0,-1,-1],[0,-1,1],[-2,-1,0]]) },
  { id: "10_27010", vertices: [[0,0,0],[0,1,1],[1,0,1],[1,1,2],[1,2,0],[2,0,0],[2,1,1]], screening: rejected("isohedral_periodic_quotient", 24, [[0,0,-4],[-4,0,0],[0,-4,0]]) },
  { id: "10_24235", vertices: [[-1,0,0],[-1,0,2],[0,-1,0],[0,1,0],[0,1,2],[1,0,0]], screening: rejected("translational", 2, [[-1,-1,0],[-1,1,0],[0,0,-2]]) },
  { id: "9_3239", vertices: [[-1,-1,0],[-1,0,-2],[0,-1,-2],[0,0,2],[0,1,0],[1,0,0]], screening: rejected("translational", 2, [[-1,0,-2],[0,-1,-2],[-1,-1,2]]) },
  { id: "10_16113", priority: 1, vertices: [[0,1,0],[0,2,1],[1,0,-1],[1,0,2],[1,1,-1],[2,1,0]], screening: shellRejected(1) },
  { id: "10_44867", vertices: [[0,1,0],[0,1,1],[1,0,0],[1,0,1],[1,1,2],[1,2,0],[2,1,0],[2,2,1]], screening: rejected("translational", 2, [[-1,1,0],[-1,-1,-1],[-1,0,2]]) },
  { id: "10_45035", vertices: [[0,0,1],[0,1,0],[0,1,2],[0,2,1],[1,0,0],[1,0,1],[1,1,0],[1,1,1],[2,0,0]], screening: rejected("translational", 2, [[0,-1,-1],[0,-1,1],[-2,0,-1]]) },
  { id: "8_2431", vertices: [[-1,0,-1],[0,-1,-1],[0,0,2],[0,1,0],[1,0,0],[1,1,3]], screening: rejected("translational", 2, [[-1,-1,1],[-1,0,3],[0,-1,3]]) },
  { id: "10_24775", vertices: [[-1,-1,0],[-1,1,1],[0,0,2],[0,1,-1],[1,0,0],[1,2,1]], screening: rejected("translational", 3, [[-1,-1,2],[-1,-2,-1],[-2,1,-1]]) },
  { id: "10_26470", vertices: [[-1,0,0],[-1,0,1],[0,-1,0],[0,1,0],[0,1,2],[1,0,0],[1,0,1]], screening: rejected("translational", 8, [[-2,-2,0],[-2,0,2],[-2,2,0]]) },
  { id: "10_44266", vertices: [[0,0,2],[0,1,0],[1,0,0],[1,1,2],[1,2,-1],[1,2,0],[2,1,-1],[2,1,0]], screening: rejected("translational", 2, [[-1,-1,0],[-1,1,0],[-1,-2,-3]]) },
  { id: "10_45026", priority: 2, vertices: [[0,0,2],[0,1,1],[1,0,1],[1,1,0],[1,1,2],[1,2,0],[1,2,1],[2,1,0],[2,1,1]], screening: shellRejected(1) },
  { id: "10_45033", priority: 3, vertices: [[0,0,0],[0,0,1],[0,1,1],[1,0,1],[1,1,0],[1,1,2],[1,2,1],[2,1,1],[2,2,2]], screening: rejected("translational", 6, [[-2,-2,2],[0,-1,3],[-3,0,1]], PERIODIC_TEMPLATE_10_45033) },
  { id: "9_11683", priority: 4, vertices: [[0,1,0],[0,1,1],[1,0,1],[1,1,0],[1,1,2],[1,2,1],[2,0,2],[2,1,1]], screening: shellRejected(1) }
];

export const classifyLatticeCandidateScreen = ({ translational, isohedral, shell }) => {
  if (translational?.provenImpossible || isohedral?.provenImpossible || shell?.provenImpossible) return "reject_certified_non_tiler";
  if (translational?.certified) return "reject_certified_periodic";
  if (isohedral?.certified) return "reject_certified_isohedral";
  if (translational?.incomplete || isohedral?.incomplete) return "inconclusive";
  return "survives_completed_bounded_screens";
};

const PRE_SHELL_IDS = Object.freeze(["10_16113", "10_45026", "10_45033", "9_11683"]);
const SHELL_RESULTS = Object.freeze({
  "10_16113": Object.freeze({ deepest_completed_shell: 0, obstruction_shell: 1, robust: true, obstruction_kind: "permanently_unfillable_face" }),
  "10_45026": Object.freeze({ deepest_completed_shell: 0, obstruction_shell: 1, robust: true }),
  "10_45033": Object.freeze({ deepest_completed_shell: 7, robust_completed_shell: 4, shell_five_hits: 1, shell_five_trials: 3, shell_five_witness_tiles: 464, shell_six_hits: 2, shell_six_trials: 3, shell_six_witness_tiles: 764, shell_seven_hits: 1, shell_seven_trials: 3, shell_seven_witness_tiles: 1174, periodic_motif_tiles: 6 }),
  "9_11683": Object.freeze({ deepest_completed_shell: 0, obstruction_shell: 1, robust: true })
});
const enrichCandidate = candidate => ({
  ...candidate,
  lattice_points: Number(candidate.id.split("_")[0]),
  registry_id: `census_${candidate.id}`,
  name: `Candidate ${candidate.id}`,
  last_screening: LATTICE_POLYHEDRON_SCREENING,
  shell_screening: SHELL_RESULTS[candidate.id],
  gcts_proof_screening: Object.freeze({
    ...GCTS_PROOF_SCREENING_RESULTS[candidate.id],
    ...INTERNAL_PERIOD_SCREENING_RESULTS[candidate.id],
    ...GLOBAL_EXTENSION_SCREENING_RESULTS[candidate.id]
  })
});

export const LATTICE_POLYHEDRON_PRE_SHELL_CANDIDATES = LATTICE_POLYHEDRON_CENSUS_POOL
  .filter(candidate => PRE_SHELL_IDS.includes(candidate.id))
  .sort((left, right) => left.priority - right.priority)
  .map(enrichCandidate);

export const LATTICE_POLYHEDRON_SHELL_REJECTS = LATTICE_POLYHEDRON_PRE_SHELL_CANDIDATES
  .filter(candidate => candidate.screening.certificate === "finite_extendable_shell_obstruction")
  .map(candidate => ({
    ...candidate,
    description: `GCTS non-tiler control ${candidate.id}; exhaustive face-obligation search proves that every route toward shell ${candidate.screening.shell_depth} encounters a permanently unfillable exposed face in the configured face-to-face proper-lattice model.`
  }));

export const LATTICE_POLYHEDRON_PERIODIC_REJECTS = LATTICE_POLYHEDRON_PRE_SHELL_CANDIDATES
  .filter(candidate => candidate.screening.certificate === "translational")
  .map(candidate => ({
    ...candidate,
    description: `Periodic control ${candidate.id}; a ${candidate.screening.motif_tiles}-tile exact translational quotient was mined from the shell-7 witness and independently replayed.`
  }));

export const LATTICE_POLYHEDRON_SURVIVORS = LATTICE_POLYHEDRON_PRE_SHELL_CANDIDATES
  .filter(candidate => candidate.screening.status === "inconclusive")
  .map((candidate, index, survivors) => ({
    ...candidate,
    survivor_priority: index + 1,
    survivor_count: survivors.length,
    description: `Unresolved Blanco–Santos census candidate ${candidate.id}; the sole survivor after exact quotient screening and complete-shell GCTS screening of the original 16-tile pool.`
  }));

export const LATTICE_POLYHEDRON_GCTS_EXAMPLES = Object.freeze([
  ...LATTICE_POLYHEDRON_SURVIVORS,
  ...LATTICE_POLYHEDRON_PERIODIC_REJECTS,
  ...LATTICE_POLYHEDRON_SHELL_REJECTS,
  ...LATTICE_POLYHEDRON_SIZE11_CONTROLS
]);
