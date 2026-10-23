// One shared origin in the two triangular integer coefficient bases.
export const COORDINATE_ORIGIN = Object.freeze([4, 0, 3, -2]);
export const PLANE_NORMALS = Object.freeze([[-8, -13, 16, 0], [13, 5, 0, 16]]);
export function shiftedTile(vertices, ids) {
  return ids.map(id => vertices[id].map((x, k) => x - COORDINATE_ORIGIN[k]));
}
export function latticeWindow(center, steps) {
  const points = [];
  for (let p = -steps; p <= steps; p++) for (let q = -steps; q <= steps; q++)
    for (let r = -steps; r <= steps; r++) for (let s = -steps; s <= steps; s++)
      points.push([center[0] + p, center[1] + q, center[2] + r, center[3] + s]);
  return points;
}
