// Blanco–Santos lattice 3-polytopes retained after the first local screen.
// The isohedral screen below demotes every tile that reached a 24-tile patch;
// a long patch is a screening witness, not by itself a proof of space tiling.
const LATTICE_POLYHEDRON_CENSUS = [
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
];

const ISOHEDRAL_SCREEN_TILES = new Map([
  ["8_2480", 53],
  ["9_9043", 34],
  ["9_11679", 32],
  ["10_27010", 24],
  ["10_24235", 26],
  ["9_3239", 237],
  ["10_16113", 24],
  ["10_44867", 26],
  ["10_45035", 110],
  ["8_2431", 239]
]);

const SURVIVOR_PRIORITY = new Map([
  ["10_24775", 1],
  ["10_26470", 2],
  ["10_44266", 3],
  ["10_45026", 4],
  ["10_45033", 5],
  ["9_11683", 6]
]);

export const LATTICE_POLYHEDRON_CENSUS_TILES = LATTICE_POLYHEDRON_CENSUS.map(candidate => ({
  ...candidate,
  lattice_points: Number(candidate.id.split("_")[0]),
  registry_id: `census_${candidate.id}`,
  name: `Candidate ${candidate.id}`,
  screen_status: ISOHEDRAL_SCREEN_TILES.has(candidate.id) ? "isohedral_grower" : "unresolved",
  isohedral_screen_tiles: ISOHEDRAL_SCREEN_TILES.get(candidate.id) ?? null,
  survivor_priority: SURVIVOR_PRIORITY.get(candidate.id) ?? null,
  description: ISOHEDRAL_SCREEN_TILES.has(candidate.id)
    ? `Screened out after reaching ${ISOHEDRAL_SCREEN_TILES.get(candidate.id)} tiles in bounded isohedral growth.`
    : `Unresolved Blanco–Santos census candidate ${candidate.id}; survivor ${SURVIVOR_PRIORITY.get(candidate.id)} of 6 after bounded isohedral screening.`
}));
