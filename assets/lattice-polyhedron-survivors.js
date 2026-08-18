// Blanco–Santos lattice 3-polytopes that survived the bounded face-to-face
// cubic-orientation screen through size ten. They are research candidates,
// not known tilers and not evidence of aperiodicity.
export const LATTICE_POLYHEDRON_SURVIVORS = [
  { id: "8_2480", priority: 1, vertices: [[0,0,2],[0,1,0],[1,0,0],[1,1,2],[1,2,0],[2,1,0]] },
  { id: "9_9043", priority: 2, vertices: [[0,0,1],[0,1,0],[1,1,2],[1,2,1],[2,0,1],[2,1,0]] },
  { id: "9_11679", priority: 3, vertices: [[-1,-1,0],[-1,0,1],[0,-1,0],[0,0,-1],[0,0,1],[0,1,0],[1,0,0],[1,1,-1]] },
  { id: "10_27010", priority: 4, vertices: [[0,0,0],[0,1,1],[1,0,1],[1,1,2],[1,2,0],[2,0,0],[2,1,1]] },
  { id: "10_24235", priority: 5, vertices: [[-1,0,0],[-1,0,2],[0,-1,0],[0,1,0],[0,1,2],[1,0,0]] },
  { id: "9_3239", priority: 6, vertices: [[-1,-1,0],[-1,0,-2],[0,-1,-2],[0,0,2],[0,1,0],[1,0,0]] },
  { id: "10_16113", priority: 7, vertices: [[0,1,0],[0,2,1],[1,0,-1],[1,0,2],[1,1,-1],[2,1,0]] },
  { id: "10_44867", priority: 8, vertices: [[0,1,0],[0,1,1],[1,0,0],[1,0,1],[1,1,2],[1,2,0],[2,1,0],[2,2,1]] },
  { id: "10_45035", priority: 9, vertices: [[0,0,1],[0,1,0],[0,1,2],[0,2,1],[1,0,0],[1,0,1],[1,1,0],[1,1,1],[2,0,0]] },
  { id: "8_2431", priority: 10, vertices: [[-1,0,-1],[0,-1,-1],[0,0,2],[0,1,0],[1,0,0],[1,1,3]] },
  { id: "10_24775", priority: 11, vertices: [[-1,-1,0],[-1,1,1],[0,0,2],[0,1,-1],[1,0,0],[1,2,1]] },
  { id: "10_26470", priority: 12, vertices: [[-1,0,0],[-1,0,1],[0,-1,0],[0,1,0],[0,1,2],[1,0,0],[1,0,1]] },
  { id: "10_44266", priority: 13, vertices: [[0,0,2],[0,1,0],[1,0,0],[1,1,2],[1,2,-1],[1,2,0],[2,1,-1],[2,1,0]] },
  { id: "10_45026", priority: 14, vertices: [[0,0,2],[0,1,1],[1,0,1],[1,1,0],[1,1,2],[1,2,0],[1,2,1],[2,1,0],[2,1,1]] },
  { id: "10_45033", priority: 15, vertices: [[0,0,0],[0,0,1],[0,1,1],[1,0,1],[1,1,0],[1,1,2],[1,2,1],[2,1,1],[2,2,2]] },
  { id: "9_11683", priority: 16, vertices: [[0,1,0],[0,1,1],[1,0,1],[1,1,0],[1,1,2],[1,2,1],[2,0,2],[2,1,1]] }
].map(candidate => ({
  ...candidate,
  lattice_points: Number(candidate.id.split("_")[0]),
  registry_id: `census_${candidate.id}`,
  name: `Candidate ${candidate.id}`,
  description: `Unresolved Blanco–Santos census candidate ${candidate.id}; priority ${candidate.priority} of 16 after bounded local, periodic, and first-corona screening.`
}));
