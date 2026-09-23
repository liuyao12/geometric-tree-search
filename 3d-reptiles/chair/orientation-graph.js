// Directions of the missing cube, not individual elements of SO(3).
// The cubic rotation group acts transitively on these eight directions;
// each direction has a three-element stabilizer.
export const directionKey = missing => missing[0] + 2 * missing[1] + 4 * missing[2];
export const DIRECTION_NODES = Array.from({ length: 8 }, (_, id) => ({
  id,
  corner: [id & 1, (id >> 1) & 1, (id >> 2) & 1],
  vector: [0, 1, 2].map(axis => ((id >> axis) & 1) ? 1 : -1)
}));
export const QUARTER_TURNS = [
  [[1,0,0],[0,0,-1],[0,1,0]],
  [[0,0,1],[0,1,0],[-1,0,0]],
  [[0,-1,0],[1,0,0],[0,0,1]]
];
// Undirected simple Schreier graph of these proper quarter-turn generators.
// Its underlying graph is a cube; no coordinate reflection is performed.
const edges = new Map();
for (const node of DIRECTION_NODES) for (const rotation of QUARTER_TURNS) {
  const transformed = rotation.map(row => row.reduce((sum, value, axis) => sum + value * node.vector[axis], 0));
  const target = directionKey(transformed.map(value => (value + 1) / 2));
  const pair = [node.id, target].sort((a, b) => a - b);
  edges.set(pair.join(','), pair);
}
export const DIRECTION_EDGES = [...edges.values()];
