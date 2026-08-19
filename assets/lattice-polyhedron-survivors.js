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
      globally_distinct_candidate_states: 1053,
      repeated_state_path_pairs: 40,
      global_uniqueness_rate: 0.9634034766697164,
      report: "data/lattice-polyhedron-hybrid-checkpoint-screen-2026-08-19.json",
      overlap_report: "data/lattice-polyhedron-global-checkpoint-overlap-2026-08-19.json",
      prior_prefix_report: "data/lattice-polyhedron-distinct-checkpoint-screen-2026-08-18.json"
    })
  })
});

const GCTS_PROOF_SCREENING_RESULTS = Object.freeze({
  "10_16113": Object.freeze({ outcome: "focused_target_patch", robust_largest_patch: 21, median_largest_patch: 22, best_largest_patch: 27, target_hits: 0, trials: 3, focused_target_witness: true, focused_seed: 3, focused_visited_nodes: 2312, focused_witness_hash: "b4c8e0c893b1eb7c", checkpoint_quotient_checks: 39, checkpoint_quotient_certificates: 0, distinct_checkpoint_paths: 3, distinct_checkpoint_eligible_states: 1837, distinct_checkpoint_checks: 306, distinct_checkpoint_max_size: 27, distinct_checkpoint_certificates: 0, distinct_checkpoint_timeouts: 0, distinct_checkpoint_sampling_skips: 1302, distinct_checkpoint_duplicate_skips: 51, distinct_checkpoint_cap_skips: 229, global_checkpoint_states: 295, repeated_checkpoint_path_pairs: 11 }),
  "10_45026": Object.freeze({ outcome: "focused_target_patch", robust_largest_patch: 14, median_largest_patch: 16, best_largest_patch: 17, target_hits: 0, trials: 3, focused_target_witness: true, focused_seed: 1, focused_seeded_tie_breaks: false, focused_visited_nodes: 4278, focused_witness_hash: "e16dbe38a0165b93", checkpoint_quotient_checks: 39, checkpoint_quotient_certificates: 0, distinct_checkpoint_paths: 3, distinct_checkpoint_eligible_states: 1287, distinct_checkpoint_checks: 215, distinct_checkpoint_max_size: 17, distinct_checkpoint_certificates: 0, distinct_checkpoint_timeouts: 0, distinct_checkpoint_sampling_skips: 916, distinct_checkpoint_duplicate_skips: 160, distinct_checkpoint_cap_skips: 156, global_checkpoint_states: 192, repeated_checkpoint_path_pairs: 23 }),
  "10_45033": Object.freeze({ outcome: "focused_target_patch", robust_largest_patch: 23, median_largest_patch: 27, best_largest_patch: 36, target_hits: 0, trials: 3, focused_target_witness: true, focused_seed: 2, focused_visited_nodes: 1162, focused_witness_hash: "deb51611a30f25b5", checkpoint_quotient_checks: 39, checkpoint_quotient_certificates: 0, distinct_checkpoint_paths: 3, distinct_checkpoint_eligible_states: 1221, distinct_checkpoint_checks: 262, distinct_checkpoint_max_size: 36, distinct_checkpoint_certificates: 0, distinct_checkpoint_timeouts: 0, distinct_checkpoint_sampling_skips: 762, distinct_checkpoint_duplicate_skips: 44, distinct_checkpoint_cap_skips: 197, global_checkpoint_states: 258, repeated_checkpoint_path_pairs: 4 }),
  "9_11683": Object.freeze({ outcome: "focused_target_patch", robust_largest_patch: 19, median_largest_patch: 25, best_largest_patch: 32, target_hits: 0, trials: 3, focused_target_witness: true, focused_seed: 3, focused_visited_nodes: 591, focused_witness_hash: "5ab75954f9e80239", checkpoint_quotient_checks: 39, checkpoint_quotient_certificates: 0, distinct_checkpoint_paths: 3, distinct_checkpoint_eligible_states: 1399, distinct_checkpoint_checks: 310, distinct_checkpoint_max_size: 32, distinct_checkpoint_certificates: 0, distinct_checkpoint_timeouts: 0, distinct_checkpoint_sampling_skips: 970, distinct_checkpoint_duplicate_skips: 22, distinct_checkpoint_cap_skips: 119, global_checkpoint_states: 308, repeated_checkpoint_path_pairs: 2 })
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
