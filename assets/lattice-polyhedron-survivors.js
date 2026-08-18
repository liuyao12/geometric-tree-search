// Blanco–Santos lattice 3-polytopes that remain after the 2026-08-17 rerun of
// the exact translational and exact tile-transitive quotient screens. These
// five searches were still resource-limited, so they are unresolved rather
// than certified non-periodic or evidence of aperiodicity.
export const LATTICE_POLYHEDRON_SURVIVORS = [
  { id: "10_16113", priority: 1, vertices: [[0,1,0],[0,2,1],[1,0,-1],[1,0,2],[1,1,-1],[2,1,0]] },
  { id: "10_26470", priority: 2, vertices: [[-1,0,0],[-1,0,1],[0,-1,0],[0,1,0],[0,1,2],[1,0,0],[1,0,1]] },
  { id: "10_45026", priority: 3, vertices: [[0,0,2],[0,1,1],[1,0,1],[1,1,0],[1,1,2],[1,2,0],[1,2,1],[2,1,0],[2,1,1]] },
  { id: "10_45033", priority: 4, vertices: [[0,0,0],[0,0,1],[0,1,1],[1,0,1],[1,1,0],[1,1,2],[1,2,1],[2,1,1],[2,2,2]] },
  { id: "9_11683", priority: 5, vertices: [[0,1,0],[0,1,1],[1,0,1],[1,1,0],[1,1,2],[1,2,1],[2,0,2],[2,1,1]] }
].map(candidate => ({
  ...candidate,
  lattice_points: Number(candidate.id.split("_")[0]),
  registry_id: `census_${candidate.id}`,
  name: `Candidate ${candidate.id}`,
  survivor_priority: candidate.priority,
  survivor_count: 5,
  description: `Unresolved Blanco–Santos census candidate ${candidate.id}; survivor ${candidate.priority} of 5 after exact quotient rescreening of the original 16-tile pool.`
}));
