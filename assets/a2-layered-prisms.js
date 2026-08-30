import * as A2Tiling from "./a2-tiling-engine.js?v=20260830-occupancy-v2";

const { A2_TILE_LOOPS } = A2Tiling;

// Keep the 3D catalogue compatible with a browser-cached copy of the A2
// engine from before a2PolygonOccupancy became public.
const fallbackPolygonOccupancy = loop => {
  const key = point => point.join(",");
  const area2 = loop.reduce((sum, point, index) => {
    const next = loop[(index + 1) % loop.length];
    return sum + point[0] * next[1] - next[0] * point[1];
  }, 0);
  const projected = ([x, y]) => [x + y * 0.5, y * Math.sqrt(3) / 2];
  const projectedLoop = loop.map(projected);
  const result = new Map();
  const gcd = (left, right) => {
    let a = Math.abs(left), b = Math.abs(right);
    while (b) [a, b] = [b, a % b];
    return a || 1;
  };
  const pointInPolygon = ([x, y]) => {
    let inside = false;
    for (let i = 0, j = loop.length - 1; i < loop.length; j = i++) {
      const [ax, ay] = loop[i], [bx, by] = loop[j];
      if ((ay > y) !== (by > y) && x < (bx - ax) * (y - ay) / (by - ay) + ax) inside = !inside;
    }
    return inside;
  };
  loop.forEach((point, index) => {
    const previous = projectedLoop[(index - 1 + loop.length) % loop.length];
    const current = projectedLoop[index];
    const next = projectedLoop[(index + 1) % loop.length];
    const incoming = [current[0] - previous[0], current[1] - previous[1]];
    const outgoing = [next[0] - current[0], next[1] - current[1]];
    let turn = Math.atan2(
      incoming[0] * outgoing[1] - incoming[1] * outgoing[0],
      incoming[0] * outgoing[0] + incoming[1] * outgoing[1]
    );
    if (area2 < 0) turn = -turn;
    let interior = Math.PI - turn;
    if (interior <= 0) interior += Math.PI * 2;
    result.set(key(point), { point: point.slice(), weight: Math.round(interior * 6 / Math.PI) });
    const following = loop[(index + 1) % loop.length];
    const delta = following.map((value, axis) => value - point[axis]);
    const steps = gcd(gcd(delta[0], delta[1]), delta[2]);
    for (let step = 1; step < steps; step += 1) {
      const latticePoint = point.map((value, axis) => value + delta[axis] * step / steps);
      result.set(key(latticePoint), { point: latticePoint, weight: 6 });
    }
  });
  const xs = loop.map(point => point[0]), ys = loop.map(point => point[1]);
  for (let x = Math.min(...xs); x <= Math.max(...xs); x += 1) {
    for (let y = Math.min(...ys); y <= Math.max(...ys); y += 1) {
      const point = [x, y, -x - y];
      if (!result.has(key(point)) && pointInPolygon(point)) {
        result.set(key(point), { point, weight: 12 });
      }
    }
  }
  return result;
};
const a2PolygonOccupancy = A2Tiling.a2PolygonOccupancy ?? fallbackPolygonOccupancy;

const add = (left, right) => left.map((value, axis) => value + right[axis]);

const occupancyKind = (planarWeight, endpoint) => {
  if (endpoint) {
    if (planarWeight === 12) return "face";
    if (planarWeight === 6) return "edge";
    return "vertex";
  }
  if (planarWeight === 12) return "interior";
  if (planarWeight === 6) return "face";
  return "edge";
};

/**
 * Extrude an A2 lattice polygon normally through integral (1,1,1) layers.
 *
 * The A2 engine measures planar angles in twelfths of a full turn.  A point
 * on either end face sees half of that cone, hence weight 2a in the 3D
 * forty-eighth convention; an intermediate section sees the full cone and
 * has weight 4a.  This produces an exact GCTS-I lattice function even for a
 * non-convex polygon such as the hat or turtle.
 */
export function makeA2LayeredPrism(loop, { layers = 1, geometryModel = "lattice_function" } = {}) {
  if (!Array.isArray(loop) || loop.length < 3) throw new Error("A2 prism needs a polygon loop");
  if (!loop.every(point => point.length === 3 && point.every(Number.isInteger) && point[0] + point[1] + point[2] === 0)) {
    throw new Error("A2 prism vertices must be integral and lie on x+y+z=0");
  }
  const layerCount = Math.max(1, Math.floor(Number(layers) || 1));
  const height = [layerCount, layerCount, layerCount];
  const signedArea2 = loop.reduce((sum, point, index) => {
    const next = loop[(index + 1) % loop.length];
    return sum + point[0] * next[1] - next[0] * point[1];
  }, 0);
  const base = (signedArea2 < 0 ? [...loop].reverse() : loop).map(point => point.slice());
  const top = base.map(point => add(point, height));
  const vertices = [...base, ...top];
  const size = base.length;
  const faces = [
    { v: Array.from({ length: size }, (_, index) => size - 1 - index), type: "A2_END" },
    { v: Array.from({ length: size }, (_, index) => size + index), type: "A2_END" },
    ...Array.from({ length: size }, (_, index) => ({
      v: [index, (index + 1) % size, size + (index + 1) % size, size + index],
      type: "A2_SIDE"
    }))
  ];
  const planar = a2PolygonOccupancy(base);
  const occupancy = [];
  for (let layer = 0; layer <= layerCount; layer += 1) {
    const endpoint = layer === 0 || layer === layerCount;
    const shift = [layer, layer, layer];
    for (const entry of planar.values()) {
      occupancy.push([
        add(entry.point, shift),
        entry.weight * (endpoint ? 2 : 4),
        null,
        null,
        occupancyKind(entry.weight, endpoint)
      ]);
    }
  }
  return {
    v: vertices,
    f_data: faces,
    occ: occupancy,
    skip_winding: true,
    solid_angle: { kind: "rational", max_value: 48 },
    geometry_model: geometryModel,
    lattice_symmetry: "a2_layers",
    layer_normal: [1, 1, 1],
    layer_sums: [0, 3 * layerCount]
  };
}

export const A2_LAYERED_PRISM_SPECS = Object.freeze([
  {
    id: "a2_hexagonal_prism",
    name: "A2 Hexagonal Prism",
    loop: A2_TILE_LOOPS.hexagon,
    geometry_model: "convex_polyhedron",
    role: "periodic control"
  },
  {
    id: "a2_hat_prism",
    name: "A2 Hat Prism",
    loop: A2_TILE_LOOPS.hat,
    geometry_model: "lattice_function",
    role: "layered aperiodic lead"
  },
  {
    id: "a2_turtle_prism",
    name: "A2 Turtle Prism",
    loop: A2_TILE_LOOPS.turtle,
    geometry_model: "lattice_function",
    role: "layered aperiodic lead"
  }
]);
