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
    generation_band: false,
    exact_failure_memo: true,
    translation_equivariant_nogoods: false,
    mirrors: false,
    report: "data/lattice-polyhedron-proof-screen-2026-08-18.json"
  })
});

const GCTS_PROOF_SCREENING_RESULTS = Object.freeze({
  "10_16113": Object.freeze({ outcome: "bounded_below_target", robust_largest_patch: 21, median_largest_patch: 21, best_largest_patch: 21, target_hits: 0, trials: 3 }),
  "10_26470": Object.freeze({ outcome: "robust_target_patch", robust_largest_patch: 40, median_largest_patch: 40, best_largest_patch: 40, target_hits: 3, trials: 3 }),
  "10_45026": Object.freeze({ outcome: "bounded_below_target", robust_largest_patch: 21, median_largest_patch: 21, best_largest_patch: 21, target_hits: 0, trials: 3 }),
  "10_45033": Object.freeze({ outcome: "bounded_below_target", robust_largest_patch: 25, median_largest_patch: 25, best_largest_patch: 25, target_hits: 0, trials: 3 }),
  "9_11683": Object.freeze({ outcome: "bounded_below_target", robust_largest_patch: 21, median_largest_patch: 21, best_largest_patch: 21, target_hits: 0, trials: 3 })
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
  { id: "10_26470", priority: 2, vertices: [[-1,0,0],[-1,0,1],[0,-1,0],[0,1,0],[0,1,2],[1,0,0],[1,0,1]], screening: { status: "inconclusive" } },
  { id: "10_44266", vertices: [[0,0,2],[0,1,0],[1,0,0],[1,1,2],[1,2,-1],[1,2,0],[2,1,-1],[2,1,0]], screening: rejected("translational", 2, [[-1,-1,0],[-1,1,0],[-1,-2,-3]]) },
  { id: "10_45026", priority: 3, vertices: [[0,0,2],[0,1,1],[1,0,1],[1,1,0],[1,1,2],[1,2,0],[1,2,1],[2,1,0],[2,1,1]], screening: { status: "inconclusive" } },
  { id: "10_45033", priority: 4, vertices: [[0,0,0],[0,0,1],[0,1,1],[1,0,1],[1,1,0],[1,1,2],[1,2,1],[2,1,1],[2,2,2]], screening: { status: "inconclusive" } },
  { id: "9_11683", priority: 5, vertices: [[0,1,0],[0,1,1],[1,0,1],[1,1,0],[1,1,2],[1,2,1],[2,0,2],[2,1,1]], screening: { status: "inconclusive" } }
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
    survivor_count: 5,
    last_screening: LATTICE_POLYHEDRON_SCREENING,
    gcts_proof_screening: GCTS_PROOF_SCREENING_RESULTS[candidate.id],
    description: `Unresolved Blanco–Santos census candidate ${candidate.id}; survivor ${candidate.priority} of 5 after exact quotient rescreening of the original 16-tile pool.`
  }));
