// Ported from https://observablehq.com/@liuyao12/3d-lattice-tiler
// This module removes Observable runtime wrappers; app-level rendering lives in app.js.

import { buildFrontierCandidateGraph, classifyFrontierCandidateGraph } from "../../assets/frontier-candidate-graph.js";
import { GeometricFailureMemo } from "../../assets/geometric-failure-memo.js?v=20260818-nogood-pivot-v49";
import { LATTICE_POLYHEDRON_GCTS_EXAMPLES } from "../../assets/lattice-polyhedron-survivors.js?v=20260820-size13-v104";
import { POLYCUBE_GCTS_CANDIDATES } from "../../assets/polycube-census-candidates.js?v=20260822-volume10-v58";
import { normalizeProposalProgram } from "./proposal-learner.js";

export const GCTS_CATALOG_MIN_PERIODIC_MOTIF_TILES = 5;

export function isGctsFigureVisibleInCatalog(figure) {
  const candidate = figure?.census_candidate;
  if (!candidate) return true;
  const certificate = candidate.screening?.certificate;
  if (!["translational", "isohedral_periodic_quotient"].includes(certificate)) return true;
  return candidate.screening?.motif_tiles >= GCTS_CATALOG_MIN_PERIODIC_MOTIF_TILES;
}

const permutations = values => {
  if (values.length <= 1) return [values.slice()];
  const out = [];
  for (let index = 0; index < values.length; index++) {
    const rest = values.slice(0, index).concat(values.slice(index + 1));
    for (const suffix of permutations(rest)) out.push([values[index], ...suffix]);
  }
  return out;
};
const matrixDeterminant = matrix =>
  matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
  - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
  + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0]);
export const PROPER_CUBIC_ROTATIONS = Object.freeze((() => {
  const rotations = [];
  for (const permutation of permutations([0, 1, 2])) {
    for (const sx of [-1, 1]) for (const sy of [-1, 1]) for (const sz of [-1, 1]) {
      const signs = [sx, sy, sz];
      const matrix = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
      for (let row = 0; row < 3; row++) matrix[row][permutation[row]] = signs[permutation[row]];
      if (matrixDeterminant(matrix) === 1) {
        rotations.push(Object.freeze(matrix.map(row => Object.freeze(row))));
      }
    }
  }
  return rotations;
})());
const patchMatrixVector = (matrix, vector) => [
  matrix[0][0] * vector[0] + matrix[0][1] * vector[1] + matrix[0][2] * vector[2],
  matrix[1][0] * vector[0] + matrix[1][1] * vector[1] + matrix[1][2] * vector[2],
  matrix[2][0] * vector[0] + matrix[2][1] * vector[1] + matrix[2][2] * vector[2]
];
const canonicalPatchCoordinate = value => value === 0 ? 0 : value;
export const canonicalLatticePatchStateKey = (placements, { rooted = false } = {}) => {
  if (!placements?.length) return "";
  const rootPlacement = placements[0];
  let canonical = null;
  for (const rotation of PROPER_CUBIC_ROTATIONS) {
    const rotatedPlacements = placements.map(placement => {
      const translation = placement.translation ?? [0, 0, 0];
      return {
        prototile_idx: placement.prototile_idx ?? 0,
        is_root: rooted && placement === rootPlacement,
        vertices: (placement.orient?.verts ?? placement.vertices ?? []).map(vertex =>
          patchMatrixVector(rotation, [
            vertex[0] + translation[0],
            vertex[1] + translation[1],
            vertex[2] + translation[2]
          ])
        )
      };
    });
    const allVertices = rotatedPlacements.flatMap(placement => placement.vertices);
    const minima = [0, 1, 2].map(axis => Math.min(...allVertices.map(vertex => vertex[axis])));
    const key = rotatedPlacements.map(placement => {
      const vertices = placement.vertices.map(vertex => vertex.map((coordinate, axis) =>
        canonicalPatchCoordinate(coordinate - minima[axis])
      ).join(",")).sort().join("|");
      const rootLabel = placement.is_root ? "@root" : "";
      return `${placement.prototile_idx}${rootLabel}::${vertices}`;
    }).sort().join(";;");
    if (canonical === null || key < canonical) canonical = key;
  }
  return canonical ?? "";
};
export const latticePatchFingerprint = stateKey => {
  let hash = 0x6c62272e07bb014262b821756295c58dn;
  const prime = 0x0000000001000000000000000000013bn;
  const text = String(stateKey ?? "");
  for (let index = 0; index < text.length; index++) {
    hash ^= BigInt(text.charCodeAt(index));
    hash = BigInt.asUintN(128, hash * prime);
  }
  return hash.toString(16).padStart(32, "0");
};

export const createTilingStream = (() => {
  return async function* createTilingStream(config, tileSpecs, stopToken = { stop: false }) {
    const SCALE = tileSpecs.SCALE;
    const COLOR_PALETTE = tileSpecs.COLOR_PALETTE;
    const BASE_COLOR_PALETTE_SIZE = tileSpecs.BASE_COLOR_PALETTE_SIZE ?? 10;
    const TRANSLATIONAL_CELL_COLOR_OFFSET =
      tileSpecs.TRANSLATIONAL_CELL_COLOR_OFFSET ?? BASE_COLOR_PALETTE_SIZE;

    const tick = () => new Promise(resolve => {
      if (typeof requestAnimationFrame === "function") requestAnimationFrame(resolve);
      else setTimeout(resolve, 0);
    });
    const uiYieldIntervalMs = Math.max(8, +config.ui_yield_interval_ms || 24);
    let lastUiYield = performance.now();
    const yieldToBrowser = async (force = false) => {
      if (stopToken.stop) return;
      const now = performance.now();
      if (!force && now - lastUiYield < uiYieldIntervalMs) return;
      lastUiYield = now;
      await tick();
    };

    const treeTileName = (rawName) => tileSpecs.displayTileName?.(rawName) ?? String(rawName ?? "Tile");

    const compareFaceVertices = (left, right) =>
      left[0] - right[0] || left[1] - right[1] || left[2] - right[2];
    const faceKeyFromSortedVertices = (verts, translation = null) => {
      const tx = translation?.[0] ?? 0;
      const ty = translation?.[1] ?? 0;
      const tz = translation?.[2] ?? 0;
      let key = "";
      for (let index = 0; index < verts.length; index++) {
        const vertex = verts[index];
        if (index) key += "|";
        key += `${vertex[0] + tx},${vertex[1] + ty},${vertex[2] + tz}`;
      }
      return key;
    };
    const keyFace = (verts) => faceKeyFromSortedVertices(
      [...verts].sort(compareFaceVertices)
    );
    const orientedFaceKeyVertexCache = new WeakMap();
    const translatedOrientedFaceKey = (orient, faceIndex, translation) => {
      let faces = orientedFaceKeyVertexCache.get(orient);
      if (!faces) {
        faces = orient.faces.map(face => face
          .map(vertexIndex => orient.verts[vertexIndex])
          .sort(compareFaceVertices));
        orientedFaceKeyVertexCache.set(orient, faces);
      }
      return faceKeyFromSortedVertices(faces[faceIndex], translation);
    };

    const faceSignature = (verts) => {
      const n = verts.length;
      const edges = [];
      for (let i = 0; i < n; i++) {
        const a = verts[i], b = verts[(i + 1) % n];
        edges.push([b[0] - a[0], b[1] - a[1], b[2] - a[2]]);
      }
      const lengths = edges.map(e => e[0] * e[0] + e[1] * e[1] + e[2] * e[2]);
      const dots = edges.map((e, i) => {
        const f = edges[(i + 1) % n];
        return e[0] * f[0] + e[1] * f[1] + e[2] * f[2];
      });
      const combined = lengths.map((L, i) => [L, dots[i]]);
      const rotate = (arr, k) => arr.slice(k).concat(arr.slice(0, k));
      let best = combined;
      for (let k = 1; k < n; k++) {
        const r = rotate(combined, k);
        let better = false;
        for (let i = 0; i < n; i++) {
          if (r[i][0] !== best[i][0]) { better = r[i][0] < best[i][0]; break; }
          if (r[i][1] !== best[i][1]) { better = r[i][1] < best[i][1]; break; }
        }
        if (better) best = r;
      }
      return best.map(p => `${p[0]},${p[1]}`).join("|");
    };

    const faceSignatureUndirected = (verts) => {
      const a = faceSignature(verts);
      const b = faceSignature([...verts].slice().reverse());
      return (a < b) ? a : b;
    };

    const isCyclicPermutation = (a, b) => {
      if (a.length !== b.length) return false;
      const n = a.length;
      const a0 = a[0];
      let start = -1;
      for (let i = 0; i < n; i++) {
        if (b[i][0] === a0[0] && b[i][1] === a0[1] && b[i][2] === a0[2]) {
          start = i;
          break;
        }
      }
      if (start < 0) return false;
      for (let i = 0; i < n; i++) {
        const ai = a[i], bi = b[(start + i) % n];
        if (ai[0] !== bi[0] || ai[1] !== bi[1] || ai[2] !== bi[2]) return false;
      }
      return true;
    };

    const translatedReverseFaceMatches = (source, target, translation) => {
      if (source.length !== target.length) return false;
      const n = source.length;
      const source0 = source[0];
      const translated0 = [
        source0[0] + translation[0],
        source0[1] + translation[1],
        source0[2] + translation[2]
      ];
      let targetStart = -1;
      for (let i = 0; i < n; i++) {
        if (
          target[i][0] === translated0[0]
          && target[i][1] === translated0[1]
          && target[i][2] === translated0[2]
        ) {
          targetStart = i;
          break;
        }
      }
      if (targetStart < 0) return false;
      for (let i = 1; i < n; i++) {
        const sourceVertex = source[i];
        const targetVertex = target[(targetStart - i + n) % n];
        if (
          sourceVertex[0] + translation[0] !== targetVertex[0]
          || sourceVertex[1] + translation[1] !== targetVertex[1]
          || sourceVertex[2] + translation[2] !== targetVertex[2]
        ) return false;
      }
      return true;
    };

    const add3 = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
    const gcd = (a, b) => {
      a = Math.abs(a | 0); b = Math.abs(b | 0);
      while (b) [a, b] = [b, a % b];
      return a || 1;
    };
    // --- Build Prototiles First (to ensure correct order and cache key) ---
    const { mode_key } = config;
    const includeMirrors = !!config.include_mirrors;
    const normalizePolycubeLattice = tileSpecs.normalizePolycubeLattice ?? ((value) => value === "fcc" || value === "d3" || value === "half" ? (value === "d3" ? "fcc" : value) : "z3");
    const polycubeLattice = normalizePolycubeLattice(config.polycube_lattice ?? config.custom_system?.polycube_lattice);
    const customSystem = config.custom_system
      ? { ...config.custom_system, polycube_lattice: polycubeLattice }
      : null;
    const modeDef = customSystem
      ? tileSpecs.buildCustomSystem(customSystem)
      : tileSpecs.TILING_REGISTRY[mode_key];
    if (!modeDef) throw new Error(`Unknown mode_key: ${mode_key}`);

    const buildBaseTiles = () => modeDef.build();
    const baseTiles = tileSpecs.withPolycubeLattice
      ? tileSpecs.withPolycubeLattice(polycubeLattice, buildBaseTiles)
      : buildBaseTiles();
    const prototiles = (() => {
      const out = [];
      for (const t of baseTiles) {
        out.push(t);
        if (includeMirrors && t.is_chiral) {
          const m = t.get_mirror_copy?.();
          if (m) {
            if (t.name.startsWith("reflected ")) {
              m.name = t.name.substring(10);
            } else {
              m.name = `reflected ${t.name}`;
            }
            m.__is_mirror = true;
            out.push(m);
          }
        }
      }
      return out;
    })();
    prototiles.forEach((tile, prototileIndex) => {
      tile.unique_orientations?.forEach((orient, orientIndex) => {
        orient.__orientation_id = `${prototileIndex}:${orientIndex}`;
      });
    });

    const determinant3 = (vectors) => {
      const [a, b, c] = vectors;
      return a[0] * (b[1] * c[2] - b[2] * c[1])
        - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0]);
    };
    // Sum oriented boundary tetrahedra, taking the absolute value only after
    // the complete surface integral.  Taking an absolute value per triangle
    // works only when the chosen center sees every face from the inside; it
    // overcounts concave polycubes and makes valid periodic quotients fail the
    // covolume check (volume-9 p9-43172 was previously reported as 10.754...).
    const closedPolyhedronVolume = (orient) => {
      if (!orient?.verts?.length || !orient?.faces?.length) return 0;
      let signedSixVolume = 0;
      for (const face of orient.faces) {
        const a = orient.verts[face[0]];
        for (let i = 1; i < face.length - 1; i++) {
          signedSixVolume += determinant3([a, orient.verts[face[i]], orient.verts[face[i + 1]]]);
        }
      }
      return Math.abs(signedSixVolume) / 6;
    };
    const tileVolumes = prototiles.map(tile => closedPolyhedronVolume(tile.unique_orientations?.[0] ?? tile));
    const rawRegion = config.target_region;
    const targetRegion = (() => {
      if (!rawRegion || rawRegion.type === "none") return null;
      const epsilon = Math.max(1e-9, Number(rawRegion.epsilon) || 1e-9);
      if (rawRegion.type === "box") {
        const center = (rawRegion.center ?? [0, 0, 0]).map(Number);
        const size = (rawRegion.size ?? [4, 4, 4]).map(value => Math.max(epsilon, Number(value)));
        const min = rawRegion.min?.map(Number) ?? center.map((value, axis) => value - size[axis] / 2);
        const max = rawRegion.max?.map(Number) ?? center.map((value, axis) => value + size[axis] / 2);
        return {
          type: "box",
          center: min.map((value, axis) => (value + max[axis]) / 2),
          volume: (max[0] - min[0]) * (max[1] - min[1]) * (max[2] - min[2]),
          contains: point => point.every((value, axis) => value >= min[axis] - epsilon && value <= max[axis] + epsilon),
          boundary: point => point.some((value, axis) =>
            Math.abs(value - min[axis]) <= epsilon || Math.abs(value - max[axis]) <= epsilon
          )
        };
      }
      if (rawRegion.type === "sphere") {
        const center = (rawRegion.center ?? [0, 0, 0]).map(Number);
        const radius = Math.max(epsilon, Number(rawRegion.radius) || 1);
        return {
          type: "sphere",
          center,
          volume: Number(rawRegion.volume) || 4 * Math.PI * radius ** 3 / 3,
          contains: point => point.reduce((sum, value, axis) => sum + (value - center[axis]) ** 2, 0) <= radius ** 2 + epsilon,
          boundary: point => Math.abs(
            point.reduce((sum, value, axis) => sum + (value - center[axis]) ** 2, 0) - radius ** 2
          ) <= epsilon
        };
      }
      if (rawRegion.type === "halfspaces") {
        const planes = (rawRegion.planes ?? []).map(plane => ({
          normal: plane.normal.map(Number),
          offset: Number(plane.offset)
        }));
        if (!planes.length || !(Number(rawRegion.volume) > 0)) {
          throw new Error("A halfspace region needs planes and a positive exact volume");
        }
        return {
          type: "halfspaces",
          center: (rawRegion.center ?? [0, 0, 0]).map(Number),
          volume: Number(rawRegion.volume),
          contains: point => planes.every(plane =>
            plane.normal.reduce((sum, value, axis) => sum + value * point[axis], 0) <= plane.offset + epsilon
          ),
          boundary: point => planes.some(plane => Math.abs(
            plane.normal.reduce((sum, value, axis) => sum + value * point[axis], 0) - plane.offset
          ) <= epsilon)
        };
      }
      throw new Error(`Unknown target region type: ${rawRegion.type}`);
    })();
    const moveFitsRegion = (orient, translation) =>
      !targetRegion || orient.verts.every(vertex => targetRegion.contains(add3(vertex, translation)));

    const affineRank = (verts) => {
      if (!verts?.length) return 0;
      const base = verts[0];
      const diffs = verts.slice(1).map(v => [v[0] - base[0], v[1] - base[1], v[2] - base[2]]).filter(v => v.some(Boolean));
      if (!diffs.length) return 0;
      const first = diffs[0];
      const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
      const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
      let normal = null;
      for (const diff of diffs.slice(1)) {
        const c = cross(first, diff);
        if (c.some(Boolean)) { normal = c; break; }
      }
      if (!normal) return 1;
      return diffs.some(diff => dot(normal, diff) !== 0) ? 3 : 2;
    };
    const tilingDimension = Math.max(1, ...prototiles.map(tile => affineRank(tile.verts)));
    const convexEdgeAngleObstruction = (() => {
      // A reflected copy of a sole prototile has exactly the same edge lengths
      // and interior dihedral angles.  Enabling mirrors therefore does not
      // invalidate this local certificate; only genuinely multiple base tiles
      // can introduce a different edge-angle spectrum.
      if (baseTiles.length !== 1 || prototiles[0].is_polycube) return null;
      const tile = prototiles[0];
      if (typeof tileSpecs.convexEdgeAngleObstruction === "function") {
        return tileSpecs.convexEdgeAngleObstruction(tile.verts, tile.faces);
      }
      if (!tile.faces?.length || tile.faces.some(face => face.length < 3)) return null;
      const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
      const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
      const cross = (a, b) => [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0]
      ];
      const normalized = vector => {
        const length = Math.sqrt(dot(vector, vector));
        return length > 1e-12 ? vector.map(value => value / length) : null;
      };
      const normals = tile.faces.map(face =>
        normalized(cross(
          sub(tile.verts[face[1]], tile.verts[face[0]]),
          sub(tile.verts[face[2]], tile.verts[face[0]])
        ))
      );
      if (normals.some(normal => !normal)) return null;
      // Only use the certificate for a convex closed boundary. This excludes
      // compounds and concave catalog entries for which edge-angle arithmetic
      // would not be a sufficient local model.
      for (let faceIndex = 0; faceIndex < tile.faces.length; faceIndex++) {
        const face = tile.faces[faceIndex];
        const normal = normals[faceIndex];
        const origin = tile.verts[face[0]];
        if (tile.verts.some(vertex => dot(normal, sub(vertex, origin)) > 1e-8)) return null;
      }
      const incidentFaces = new Map();
      for (let faceIndex = 0; faceIndex < tile.faces.length; faceIndex++) {
        const face = tile.faces[faceIndex];
        for (let index = 0; index < face.length; index++) {
          const a = face[index];
          const b = face[(index + 1) % face.length];
          const edgeKey = a < b ? `${a},${b}` : `${b},${a}`;
          if (!incidentFaces.has(edgeKey)) incidentFaces.set(edgeKey, []);
          incidentFaces.get(edgeKey).push(faceIndex);
        }
      }
      if ([...incidentFaces.values()].some(faces => faces.length !== 2)) return null;
      const edgeGroups = new Map();
      for (const [edgeKey, faces] of incidentFaces) {
        const [aIndex, bIndex] = edgeKey.split(",").map(Number);
        const edgeVector = sub(tile.verts[bIndex], tile.verts[aIndex]);
        const lengthSquared = dot(edgeVector, edgeVector);
        const cosine = Math.max(-1, Math.min(1, dot(normals[faces[0]], normals[faces[1]])));
        const interiorAngle = Math.PI - Math.acos(cosine);
        // Coplanar triangulation edges are not edges of the convex solid.
        if (Math.abs(interiorAngle - Math.PI) < 1e-8) continue;
        const lengthKey = String(Math.round(lengthSquared * 1e9) / 1e9);
        if (!edgeGroups.has(lengthKey)) edgeGroups.set(lengthKey, []);
        edgeGroups.get(lengthKey).push({ edge: [aIndex, bIndex], angle: interiorAngle });
      }
      const angleCanClose = (targetAngle, availableAngles) => {
        const tolerance = 1e-7;
        const uniqueAngles = [];
        for (const angle of availableAngles) {
          if (!uniqueAngles.some(existing => Math.abs(existing - angle) < tolerance)) uniqueAngles.push(angle);
        }
        uniqueAngles.sort((a, b) => b - a);
        const minimumAngle = Math.min(...uniqueAngles);
        const maxDepth = Math.ceil((2 * Math.PI) / minimumAngle) + 1;
        const memo = new Set();
        const fill = (remaining, startIndex, depth) => {
          if (Math.abs(remaining) < tolerance) return true;
          if (remaining < -tolerance || depth >= maxDepth) return false;
          const memoKey = `${Math.round(remaining / tolerance)}:${startIndex}:${depth}`;
          if (memo.has(memoKey)) return false;
          memo.add(memoKey);
          for (let index = startIndex; index < uniqueAngles.length; index++) {
            if (fill(remaining - uniqueAngles[index], index, depth + 1)) return true;
          }
          return false;
        };
        return fill(2 * Math.PI - targetAngle, 0, 1);
      };
      for (const [lengthSquared, edges] of edgeGroups) {
        const angles = edges.map(edge => edge.angle);
        for (const edge of edges) {
          if (angleCanClose(edge.angle, angles)) continue;
          return {
            kind: "local_edge_obstruction",
            certified: true,
            can_tile: false,
            model: "face_to_face_congruent_copies",
            edge: edge.edge,
            edge_length_squared: Number(lengthSquared),
            interior_dihedral_radians: edge.angle,
            note: "No multiset of matching tile-edge dihedral angles sums to 2π around this edge."
          };
        }
      }
      return null;
    })();
    const configuredSharedVertices = Number(config.min_shared_vertices);
    const minSharedVertices = Number.isFinite(configuredSharedVertices) && configuredSharedVertices > 0
      ? configuredSharedVertices
      : tilingDimension <= 2 ? 2 : 3;

    const isPolycubeSystem = (modeDef.category ?? []).includes("Polycubes");
    const lcm = (a, b) => Math.abs(a * b) / gcd(a, b);
    const tileAngleMaxima = prototiles.map(tile => Math.max(1, tile.solid_angle?.max_value ?? tileSpecs.LEGACY_SOLID_ANGLE_MAX));
    const MAX_SOLID_ANGLE = tileAngleMaxima.reduce((acc, value) => lcm(acc, value), 1);
    const SOLID_ANGLE_EPSILON = Math.max(1e-9, MAX_SOLID_ANGLE * 1e-9);
    for (const tile of prototiles) tile.rescaleOccupancyWeights?.(MAX_SOLID_ANGLE);
    const protoInfo = prototiles.map(p => {
      return {
        name: p.name,
        verts: p.verts,
        faces: p.faces,
        lattice_points: isPolycubeSystem ? [] : p.occupancy_points.map(o => o.pos),
        solid_angle: p.solid_angle,
        solid_angles: tileSpecs.solidAngleValues?.(p) ?? [],
        is_polycube: !!p.is_polycube,
        polycube_lattice: p.polycube_lattice ?? null,
        is_chiral: !!p.is_chiral,
        is_mirror: !!p.__is_mirror
      };
    });

    let global_center = [0, 0, 0], global_radius = 5;
    const allUnscaled = [];
    protoInfo.forEach(p => p.verts.forEach(v => allUnscaled.push([v[0]/SCALE, v[1]/SCALE, v[2]/SCALE])));
    if (allUnscaled.length) {
      const mins = [Infinity, Infinity, Infinity], maxs = [-Infinity, -Infinity, -Infinity];
      for (const v of allUnscaled) {
        for (let i = 0; i < 3; i++) { mins[i] = Math.min(mins[i], v[i]); maxs[i] = Math.max(maxs[i], v[i]); }
      }
      global_center = [(mins[0] + maxs[0]) / 2, (mins[1] + maxs[1]) / 2, (mins[2] + maxs[2]) / 2];
      const dx = maxs[0] - global_center[0], dy = maxs[1] - global_center[1], dz = maxs[2] - global_center[2];
      global_radius = Math.sqrt(dx * dx + dy * dy + dz * dz) || 2;
    }

    yield { type: "palette", colors: COLOR_PALETTE };
    yield {
      type: "prototile_info",
      tiles: protoInfo,
      scale: SCALE,
      global_center,
      global_radius,
      default_opacities: modeDef.default_viz?.opacities ?? [],
      default_internal: !!modeDef.default_viz?.internal
    };

    const conwayFigureRefs = customSystem?.figure_refs ?? [];
    const isDirectConwaySystem = !includeMirrors && config.tiling_strategy === "free_range" && (
      mode_key === "scd_conway"
      || (conwayFigureRefs.length === 1 && conwayFigureRefs[0] === "scd_conway::0")
    );
    if (isDirectConwaySystem) {
      // The general lattice search uses only the 24 orientation-preserving
      // symmetries of Z^3. SCD layers require successive rotations by
      // -atan(3/4), so emit the published layered construction directly.
      const target = Math.max(1, Number(config.target_val) || 80);
      const tile = prototiles[0];
      const layerAngle = -Math.atan2(3, 4);
      const latticeA = [10, 0, 0];
      const latticeB = [6, 8, 0];
      const topOffset = [3, 4, 2];
      const positions = [];
      for (let radius = 0; positions.length < target; radius += 1) {
        for (let layer = -radius; layer <= radius; layer += 1) {
          for (let i = -radius; i <= radius; i += 1) {
            for (let j = -radius; j <= radius; j += 1) {
              if (Math.max(Math.abs(layer), Math.abs(i), Math.abs(j)) !== radius) continue;
              positions.push({ layer, i, j });
            }
          }
        }
      }
      positions.sort((a, b) =>
        (a.layer * a.layer + a.i * a.i + a.j * a.j)
        - (b.layer * b.layer + b.i * b.i + b.j * b.j)
        || a.layer - b.layer || a.i - b.i || a.j - b.j
      );

      const transformVertex = (vertex, placement) => {
        const x = vertex[0] - topOffset[0] + placement.i * latticeA[0] + placement.j * latticeB[0];
        const y = vertex[1] - topOffset[1] + placement.i * latticeA[1] + placement.j * latticeB[1];
        const z = vertex[2] - topOffset[2] + placement.i * latticeA[2] + placement.j * latticeB[2];
        const angle = placement.layer * layerAngle;
        const cos = Math.cos(angle);
        const sin = Math.sin(angle);
        return [
          cos * x - sin * y,
          sin * x + cos * y,
          z + 2 * placement.layer
        ];
      };
      const pointKey = point => point.map(value => Math.round(value * 1e8)).join(",");
      const conwaySnapshot = count => {
        const faces = [];
        const faceGroups = new Map();
        const centers = [];
        for (let index = 0; index < count; index += 1) {
          const placement = positions[index];
          const transformed = tile.verts.map(vertex => transformVertex(vertex, placement));
          centers.push([0, 1, 2].map(axis =>
            transformed.reduce((sum, vertex) => sum + vertex[axis], 0) / transformed.length
          ));
          for (const faceIndices of tile.faces) {
            const vertices = faceIndices.map(vertexIndex => transformed[vertexIndex]);
            const face = {
              v: vertices,
              color: COLOR_PALETTE[((placement.layer % BASE_COLOR_PALETTE_SIZE) + BASE_COLOR_PALETTE_SIZE) % BASE_COLOR_PALETTE_SIZE],
              color_id: ((placement.layer % BASE_COLOR_PALETTE_SIZE) + BASE_COLOR_PALETTE_SIZE) % BASE_COLOR_PALETTE_SIZE,
              prototile_idx: 0,
              internal: false
            };
            const key = vertices.map(pointKey).sort().join("|");
            const group = faceGroups.get(key) ?? [];
            group.push(face);
            faceGroups.set(key, group);
            faces.push(face);
          }
        }
        for (const group of faceGroups.values()) {
          if (group.length > 1) for (const face of group) face.internal = true;
        }
        const spans = [0, 1, 2].map(axis =>
          Math.max(...centers.map(center => center[axis])) - Math.min(...centers.map(center => center[axis]))
        );
        const maxSpan = Math.max(...spans);
        return {
          type: "full_update",
          tile_count: count,
          tile_counts: [{ type_idx: 0, name: "Conway Biprism", color: COLOR_PALETTE[0], count }],
          faces,
          frontier_points: [],
          frontier_stats: { point_count: 0, count: 0, min_gen: Math.max(0, ...positions.slice(0, count).map(item => Math.abs(item.layer))) },
          search_stats: {
            tiling_strategy: "scd_layered_construction",
            visited_nodes: count,
            forced_total: Math.max(0, count - 1),
            branch_choices_visited: 0,
            backtracks: 0,
            growth_axis_rank: spans.filter(span => span > 1e-9).length,
            growth_spans: spans,
            growth_isotropy: maxSpan > 0 ? Math.min(...spans) / maxSpan : 0,
            visited_percent: 100,
            progress_depth: 0,
            progress_completed_paths_label: "1",
            progress_total_paths_label: "1"
          }
        };
      };

      for (let count = 1; count <= target; count += 1) {
        if (stopToken.stop) return;
        yield conwaySnapshot(count);
        await yieldToBrowser();
      }
      const finalSnapshot = conwaySnapshot(target);
      yield {
        type: "finished",
        tile_count: target,
        search_stats: finalSnapshot.search_stats,
        success: true,
        result_kind: "known_aperiodic_construction",
        can_tile: true,
        search_incomplete: false,
        tiling_evidence: {
          kind: "schmitt_conway_danzer_layered_construction",
          certified: true,
          can_tile: true,
          translational_symmetry: false,
          layer_rotation_radians: layerAngle
        }
      };
      return;
    }

    const state = {
      placements: [],
      frontier: new Map(),
      lattice: new Map(),
      viz_faces: new Map(),
      frontier_point_depths: new Map(),
      vertex_candidate_cache: new Map(),
      placed_volume: 0
    };

    let faceCounter = 0;
    let nodeCounter = 0;
    let searchWorkCounter = 1;
    let stateVersion = 0;
    let latestFrontierGraph = null;
    let latestFrontierGraphVersion = -1;
    const randomSeed = (Math.floor(Number(config.random_seed) || 1) >>> 0) || 1;
    let randomState = randomSeed;
    const nextRandom = () => {
      randomState = (randomState + 0x6d2b79f5) >>> 0;
      let value = randomState;
      value = Math.imul(value ^ (value >>> 15), value | 1);
      value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
      return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
    };
    const seededTieBreaks = config.seeded_tie_breaks === true;
    const seededTieValue = key => {
      let hash = (2166136261 ^ randomSeed) >>> 0;
      const text = String(key ?? "");
      for (let index = 0; index < text.length; index++) {
        hash = Math.imul(hash ^ text.charCodeAt(index), 16777619) >>> 0;
      }
      hash ^= hash >>> 16;
      hash = Math.imul(hash, 0x7feb352d) >>> 0;
      hash ^= hash >>> 15;
      hash = Math.imul(hash, 0x846ca68b) >>> 0;
      return (hash ^ (hash >>> 16)) >>> 0;
    };
    const nowId = () => (++nodeCounter);
    const normalizedStrategy = ["freestyle", "free_range", "learning_free_range"].includes(config.tiling_strategy)
      ? "generic"
      : config.tiling_strategy;
    const searchStats = {
      tiling_strategy: ["translational", "isohedral", "generic"].includes(normalizedStrategy)
        ? normalizedStrategy
        : "auto",
      random_seed: randomSeed,
      seeded_tie_breaks: seededTieBreaks,
      termination_reason: null,
      move_order: null,
      forced_total: 0,
      forced_throttles: 0,
      generation_band_deferrals: 0,
      generic_failure_memo_enabled: false,
      generic_failure_memo_states: 0,
      generic_failure_memo_hits: 0,
      generic_failure_memo_capacity: 0,
      generic_failure_memo_capacity_reached: false,
      generic_failure_memo_key_equivalence: "disabled",
      generic_connected_patch_enumeration: false,
      generic_connected_patch_candidate_states: 0,
      generic_connected_patch_max_candidates: 0,
      generic_complete_shell_enumeration: false,
      generic_global_extension_candidate_states: 0,
      generic_global_extension_max_candidates: 0,
      generic_global_zero_face_pruning: false,
      generic_global_zero_face_dead_ends: 0,
      max_complete_shell_depth: 0,
      initial_patch_requested_tiles: 0,
      initial_patch_applied_tiles: 0,
      initial_patch_base_shell_depth: 0,
      generic_geometric_nogood_enabled: false,
      generic_geometric_nogood_disable_reason: null,
      generic_geometric_nogood_clauses: 0,
      generic_geometric_nogood_prunes: 0,
      generic_geometric_nogood_failure_states: 0,
      generic_geometric_nogood_activation_failure_states: 0,
      generic_geometric_nogood_activation_stagnation_failure_states: 0,
      generic_geometric_nogood_failures_since_growth: 0,
      generic_geometric_nogood_growth_mark_tiles: 1,
      generic_geometric_nogood_activated: false,
      generic_geometric_nogood_capacity: 0,
      generic_geometric_nogood_capacity_reached: false,
      generic_geometric_nogood_pivot_index: false,
      generic_geometric_nogood_compatibility_checks: 0,
      generic_geometric_nogood_clause_checks: 0,
      generic_geometric_nogood_linear_clause_checks: 0,
      generic_geometric_nogood_avoided_clause_checks: 0,
      periodic_repeat_throttles: 0,
      periodic_motif_nodes: 0,
      periodic_motif_states: 0,
      generic_periodic_certificate_attempted: false,
      generic_periodic_certificate_completed: false,
      generic_periodic_certificate_timed_out: false,
      generic_periodic_certificate_found: false,
      generic_periodic_certificate_patch_size: 0,
      generic_periodic_certificate_elapsed_ms: 0,
      generic_periodic_certificate_checks_attempted: 0,
      generic_periodic_certificate_checks_completed: 0,
      generic_periodic_certificate_checks_timed_out: 0,
      generic_periodic_certificate_check_sizes: [],
      generic_periodic_certificate_check_sources: [],
      generic_periodic_certificate_total_elapsed_ms: 0,
      generic_periodic_certificate_distinct_patch_mode: false,
      generic_periodic_certificate_checkpoint_sampling_policy: "prefix",
      generic_periodic_certificate_checkpoint_sampling_stride: 1,
      generic_periodic_certificate_checkpoint_sampling_prefix: 0,
      generic_periodic_certificate_checkpoint_eligible_states: 0,
      generic_periodic_certificate_checkpoint_sampling_skips: 0,
      generic_periodic_certificate_duplicate_states_skipped: 0,
      generic_periodic_certificate_per_size_cap_skips: 0,
      generic_periodic_certificate_total_cap_skips: 0,
      generic_periodic_certificate_checkpoint_time_budget_skips: 0,
      generic_periodic_certificate_checkpoint_time_budget_exhausted: false,
      generic_periodic_certificate_target_attempted: false,
      generic_periodic_certificate_target_completed: false,
      generic_periodic_certificate_target_timed_out: false,
      generic_periodic_certificate_target_found: false,
      generic_periodic_certificate_method: "boundary_first",
      generic_periodic_internal_motif_attempted: false,
      generic_periodic_internal_motif_found: false,
      generic_periodic_internal_motif_vector_count: 0,
      generic_periodic_internal_motif_bases_tested: 0,
      generic_periodic_internal_motif_max_translation_support: 0,
      generic_periodic_internal_motif_top_translations: [],
      reflection_continuations_seen: 0,
      branch_choices_visited: 0,
      failed_leaves: 0,
      backtracks: 0,
      max_depth: 0,
      max_live_tiles: 1,
      isohedral_transforms_discovered: 0,
      isohedral_patch_copies_applied: 0,
      isohedral_tiles_propagated: 0,
      isohedral_patch_conflicts: 0,
      isohedral_newer_layer_deferrals: 0,
      isohedral_certificate_attempts: 0,
      isohedral_certificate_patch_size: 0,
      isohedral_certificate_patch_sizes_tried: [],
      isohedral_certificate_duplicate_states_skipped: 0,
      isohedral_search_horizon_tiles: null,
      // Kept as zero-valued compatibility counters for existing headless
      // consumers. This standalone engine does not install a GCTS runtime.
      marking_observed_failures: 0,
      marking_geometric_clauses: 0,
      proposal_program_id: config.proposal_program?.id ?? null,
      proposal_patch_size: 0,
      proposal_sequence_steps_used: 0,
      proposal_patch_tiles_replayed: 0,
      proposal_patch_conflicts: 0,
      proposal_patch_conflict_index: null,
      proposal_patch_conflict_reason: null,
      backtracking_enabled: false
    };
    const branchStack = [];
    const MAX_PATH_COUNT = 1e12;
    const MAX_PATH_LOG = Math.log(MAX_PATH_COUNT);
    const capCount = (value) => Math.min(MAX_PATH_COUNT, Math.max(0, value));
    const pathCountLabel = (value) => String(Math.max(0, Math.round(value)));
    const logCountLabel = (logValue) => {
      if (!Number.isFinite(logValue)) return "0";
      if (logValue <= MAX_PATH_LOG) return pathCountLabel(Math.exp(logValue));
      const log10 = logValue / Math.LN10;
      let exponent = Math.floor(log10);
      let mantissa = Math.pow(10, log10 - exponent);
      if (mantissa >= 9.95) {
        mantissa = 1;
        exponent += 1;
      }
      return `~${mantissa.toFixed(1)}e${exponent}`;
    };
    const setBranchCursor = (depth, width, nextIndex) => {
      const safeWidth = Math.max(1, width | 0);
      const safeIndex = Math.max(0, Math.min(safeWidth, nextIndex | 0));
      branchStack.length = depth + 1;
      branchStack[depth] = { width: safeWidth, next_index: safeIndex };
      searchStats.max_depth = Math.max(searchStats.max_depth, depth + 1);
    };
    const estimateBranchProgress = () => {
      const active = branchStack.filter(Boolean);
      if (!active.length) {
        const forcedOnlyProgress =
          searchStats.forced_total > 0
          && searchStats.branch_choices_visited === 0
          && searchStats.backtracks === 0
          && searchStats.failed_leaves === 0;
        return {
          depth: 0,
          completed: forcedOnlyProgress ? 1 : 0,
          total: 1,
          percent: forcedOnlyProgress ? 100 : 0,
          completed_label: forcedOnlyProgress ? "1" : "0",
          total_label: "1",
          completed_capped: false,
          total_capped: false,
          widths: [],
          next_indices: []
        };
      }

      let totalLog = 0;
      const suffixProducts = new Array(active.length + 1).fill(1);
      for (let i = active.length - 1; i >= 0; i--) {
        totalLog += Math.log(active[i].width);
        suffixProducts[i] = capCount(suffixProducts[i + 1] * active[i].width);
      }

      let completed = 0;
      let completedFraction = 0;
      let prefixLog = 0;
      for (let i = 0; i < active.length; i++) {
        completed = capCount(completed + active[i].next_index * suffixProducts[i + 1]);
        prefixLog += Math.log(active[i].width);
        if (active[i].next_index > 0) {
          const termLog = Math.log(active[i].next_index) - prefixLog;
          if (termLog > -745) completedFraction += Math.exp(termLog);
        }
      }
      completedFraction = Math.max(0, Math.min(1, completedFraction));
      const total = Math.max(1, Math.round(suffixProducts[0]));
      const roundedCompleted = Math.max(0, Math.min(total, Math.round(completed)));
      const totalCapped = totalLog > MAX_PATH_LOG;
      const completedLog = completedFraction > 0 ? totalLog + Math.log(completedFraction) : -Infinity;
      const completedCapped = completedLog > MAX_PATH_LOG;
      return {
        depth: active.length,
        completed: roundedCompleted,
        total,
        percent: completedFraction >= 1 ? 100 : completedFraction * 100,
        completed_label: completedCapped ? logCountLabel(completedLog) : pathCountLabel(roundedCompleted),
        total_label: totalCapped ? logCountLabel(totalLog) : pathCountLabel(total),
        completed_capped: completedCapped,
        total_capped: totalCapped,
        widths: active.map(item => item.width),
        next_indices: active.map(item => item.next_index)
      };
    };
    let periodicTranslationRank = () => 0;
    const searchStatsSnapshot = () => {
      const forcedOnPath = state.placements.reduce((sum, placement) => sum + (placement.is_forced ? 1 : 0), 0);
      const branchProgress = estimateBranchProgress();
      const growth = growthStats();
      return {
        ...searchStats,
        isohedral_certificate_patch_sizes_tried:
          searchStats.isohedral_certificate_patch_sizes_tried.slice(),
        generic_periodic_certificate_check_sizes:
          searchStats.generic_periodic_certificate_check_sizes.slice(),
        generic_periodic_certificate_check_sources:
          searchStats.generic_periodic_certificate_check_sources.slice(),
        growth_axis_rank: growth.axis_rank,
        growth_spans: growth.spans,
        growth_isotropy: growth.isotropy,
        periodic_translation_rank: periodicTranslationRank(),
        placed_volume: state.placed_volume,
        target_volume: targetRegion?.volume ?? null,
        region_type: targetRegion?.type ?? null,
        forced_on_path: forcedOnPath,
        progress_depth: branchProgress.depth,
        progress_completed_paths: branchProgress.completed,
        progress_total_paths: branchProgress.total,
        progress_completed_paths_label: branchProgress.completed_label,
        progress_total_paths_label: branchProgress.total_label,
        progress_paths_capped: branchProgress.completed_capped || branchProgress.total_capped,
        branch_widths: branchProgress.widths,
        branch_next_indices: branchProgress.next_indices,
        // Actual work performed. The path estimate can saturate at 1e12 after
        // only a modest number of genuinely visited search nodes.
        visited_nodes: searchWorkCounter,
        estimated_nodes_at_depth: branchProgress.total,
        visited_percent: branchProgress.percent
      };
    };

    const branchSet = (parent, branches) => ({ type: "branch_set", parent, branches });
    const nodeStatus = (id, status, append_text = "", extra = {}) =>
      ({ type: "node_status", id, status, text: append_text, ...extra });
    const exhaustive = !!config.exhaustive;
    const criterion = config.criterion ?? "count";
    const targetVal = Math.max(1, +config.target_val || 50);
    const rawSnapshotEvery = +config.snapshot_every;
    const snapshotEvery = rawSnapshotEvery <= 0 ? Infinity : Math.max(1, rawSnapshotEvery || 1);
    const placementDetails = !!config.placement_details;
    const shouldSnapshot = (force = false) =>
      force || (Number.isFinite(snapshotEvery) &&
        (snapshotEvery <= 1 || state.placements.length <= 2 || state.placements.length % snapshotEvery === 0));
    let bestSnapshot = null;

    const cloneSnapshot = (snap) => ({
      ...snap,
      frontier_stats: snap.frontier_stats ? { ...snap.frontier_stats } : snap.frontier_stats,
      search_stats: snap.search_stats ? { ...snap.search_stats } : snap.search_stats,
      tile_counts: (snap.tile_counts ?? []).map(item => ({ ...item })),
      placements: (snap.placements ?? []).map(item => ({
        ...item,
        translation: item.translation?.slice()
      })),
      frontier_points: (snap.frontier_points ?? []).map(point => ({
        ...point,
        pos: point.pos?.slice()
      })),
      faces: (snap.faces ?? []).map(face => ({
        ...face,
        v: (face.v ?? []).map(vertex => vertex.slice())
      }))
    });

    const isBetterSnapshot = (candidate, current) => {
      if (!current) return true;
      const candidateLayer = candidate.frontier_stats?.min_gen ?? 0;
      const currentLayer = current.frontier_stats?.min_gen ?? 0;
      const candidateShell = candidate.frontier_stats?.complete_shell_depth ?? 0;
      const currentShell = current.frontier_stats?.complete_shell_depth ?? 0;
      const candidateTiles = candidate.tile_count ?? 0;
      const currentTiles = current.tile_count ?? 0;
      if (criterion === "layer" && candidateLayer !== currentLayer) return candidateLayer > currentLayer;
      if (criterion === "shell" && candidateShell !== currentShell) return candidateShell > currentShell;
      if (candidateTiles !== currentTiles) return candidateTiles > currentTiles;
      return criterion === "shell" ? candidateShell > currentShell : candidateLayer > currentLayer;
    };

    const recordBestSnapshot = (snap) => {
      if (isBetterSnapshot(snap, bestSnapshot)) bestSnapshot = cloneSnapshot(snap);
    };

    const placementCenter = (placement) => {
      const verts = placement.orient?.verts ?? [];
      return [0, 1, 2].map(axis =>
        verts.reduce((sum, vertex) => sum + vertex[axis], 0) / Math.max(1, verts.length)
        + placement.translation[axis]
      );
    };
    const growthStats = () => {
      if (!state.placements.length) return { axis_rank: 0, spans: [0, 0, 0], isotropy: 0 };
      const centers = state.placements.map(placementCenter);
      const spans = [0, 1, 2].map(axis =>
        Math.max(...centers.map(center => center[axis]))
        - Math.min(...centers.map(center => center[axis]))
      );
      const maxSpan = Math.max(...spans);
      return {
        axis_rank: spans.filter(span => span > 1e-9).length,
        spans,
        isotropy: maxSpan > 1e-9 ? Math.min(...spans) / maxSpan : 0
      };
    };

    const tileCounts = () => {
      const countMap = new Map();
      for (const placement of state.placements) {
        const typeIndex = placement.prototile_idx ?? 0;
        const entry = countMap.get(typeIndex) ?? {
          type_idx: typeIndex,
          name: treeTileName(prototiles[typeIndex]?.name),
          color: COLOR_PALETTE[(placement.color_id ?? typeIndex) % COLOR_PALETTE.length],
          count: 0
        };
        entry.count += 1;
        countMap.set(typeIndex, entry);
      }
      return [...countMap.values()].sort((a, b) => a.type_idx - b.type_idx);
    };

    const snapshotMeta = (node_id = null) => ({
      type: "snapshot_meta",
      tile_count: state.placements.length,
      tile_counts: tileCounts(),
      node_id,
      frontier_stats: frontierStatsWithCandidateCount(),
      search_stats: searchStatsSnapshot()
    });

    const snapshot = (node_id = null) => {
      const faces = [];
      for (const stack of state.viz_faces.values()) for (const f of stack) faces.push(f);
      const snap = {
        type: "full_update",
        tile_count: state.placements.length,
        tile_counts: tileCounts(),
        faces,
        frontier_points: frontierPointSnapshot(),
        node_id,
        frontier_stats: frontierStatsWithCandidateCount(),
        search_stats: searchStatsSnapshot()
      };
      if (placementDetails) {
        snap.placements = state.placements.map((placement, index) => ({
          index,
          prototile_idx: placement.prototile_idx ?? 0,
          name: treeTileName(prototiles[placement.prototile_idx ?? 0]?.name),
          translation: placement.translation?.slice() ?? [0, 0, 0],
          center: [0, 1, 2].map(axis =>
            (placement.orient?.verts ?? []).reduce(
              (sum, vertex) => sum + vertex[axis],
              0
            ) / Math.max(1, placement.orient?.verts?.length ?? 0)
            + (placement.translation?.[axis] ?? 0)
          ),
          orientation_id: placement.orient?.__orientation_id ?? null,
          orientation_signature: [
            ...(placement.orient?.verts ?? []).map(vertex => `v:${vertex.join(",")}`),
            ...(placement.orient?.occupancy ?? []).map(point => `o:${point.pos.join(",")}:${point.weight}`)
          ].sort().join("|"),
          orientation_index: prototiles[placement.prototile_idx ?? 0]?.unique_orientations?.indexOf(placement.orient) ?? null,
          color_id: placement.color_id ?? 0,
          periodic_motif_index: placement._periodic_motif_index ?? null,
          periodic_base_color_id: placement._periodic_base_color_id ?? null,
          periodic_cell: placement._periodic_cell?.slice() ?? null,
          layer: placement.layer ?? 0,
          is_forced: !!placement.is_forced
        }));
      }
      recordBestSnapshot(snap);
      return snap;
    };
    const nodeSnapshot = (node_id) => ({ type: "node_snapshot", node_id, snapshot: snapshotMeta(node_id) });
    const cloneFace = (face) => ({
      ...face,
      v: (face.v ?? []).map(vertex => vertex.slice())
    });
    const latticeUpdatesForMove = (move) => {
      const updates = new Map();
      for (const occupancy of move?.occupancy_data ?? []) {
        const key = occupancy.pos.join(",");
        const weight = latticeGet(occupancy.pos);
        const frontier = weight > 0 && weight < MAX_SOLID_ANGLE;
        updates.set(key, {
          pos: occupancy.pos.slice(),
          weight,
          max_value: MAX_SOLID_ANGLE,
          layer: frontier ? frontierPointLayer(key) : null,
          frontier
        });
      }
      return [...updates.values()];
    };
    const placementDelta = (action, move, rb, node_id = null, extra = {}) => {
      const coveredKeys = (rb?.removed ?? []).map(([key]) => key);
      const newKeys = rb?.added ?? [];
      const message = {
        type: "placement_delta",
        action,
        node_id,
        prototile_idx: move?.prototile_idx ?? 0,
        color_id: move?.color_id ?? 0,
        tile_count: state.placements.length,
        tile_counts: tileCounts(),
        frontier_face_keys: newKeys,
        covered_face_keys: coveredKeys,
        lattice_updates: latticeUpdatesForMove(move),
        frontier_stats: extra.frontier_stats ?? frontierStatsWithCandidateCount(),
        search_stats: searchStatsSnapshot()
      };
      if (Number.isFinite(move?.generation_lag)) message.generation_lag = move.generation_lag;
      if (action === "add") {
        message.faces = [...newKeys, ...coveredKeys]
          .map(key => state.viz_faces.get(key)?.at(-1))
          .filter(Boolean)
          .map(cloneFace);
      }
      return message;
    };
    const fastPlacementDelta = (move, rb, node_id = null) => {
      const coveredKeys = (rb?.removed ?? []).map(([key]) => key);
      const newKeys = rb?.added ?? [];
      return {
        type: "placement_delta",
        action: "add",
        node_id,
        prototile_idx: move?.prototile_idx ?? 0,
        color_id: move?.color_id ?? 0,
        tile_count: state.placements.length,
        frontier_face_keys: newKeys,
        covered_face_keys: coveredKeys,
        lattice_updates: latticeUpdatesForMove(move),
        faces: [...newKeys, ...coveredKeys]
          .map(key => state.viz_faces.get(key)?.at(-1))
          .filter(Boolean)
          .map(cloneFace)
      };
    };

    const latticeGet = (pos) => state.lattice.get(pos.join(",")) ?? 0;
    const latticeAdd = (pos, w) => {
      const k = pos.join(",");
      const oldWeight = state.lattice.get(k) ?? 0;
      const nextWeight = oldWeight + w;
      if (nextWeight <= 0) {
        state.lattice.delete(k);
        state.frontier_point_depths.delete(k);
        return;
      }
      state.lattice.set(k, nextWeight);
      if (oldWeight <= 0) state.frontier_point_depths.set(k, Math.max(0, state.placements.length - 1));
    };

    const faceCenterPoint = (verts) => {
      if (!verts?.length) return null;
      const center = [0, 0, 0];
      for (const vertex of verts) {
        center[0] += vertex[0];
        center[1] += vertex[1];
        center[2] += vertex[2];
      }
      center[0] /= verts.length;
      center[1] /= verts.length;
      center[2] /= verts.length;
      return center.every(Number.isInteger) ? center : null;
    };
    const candidateCachePointKey = (cacheKey) => cacheKey.split("::", 1)[0];
    let frontierPointLayerCache = null;
    let frontierPointLayerCacheVersion = -1;
    const frontierEntryPointKeys = (entry) => {
      const keys = new Set();
      const verts = entry?.ordered_verts ?? [];
      for (const vertex of verts) {
        if (latticeGet(vertex) > 0) keys.add(vertex.join(","));
      }
      const center = faceCenterPoint(verts);
      if (center && latticeGet(center) > 0) keys.add(center.join(","));
      return keys;
    };
    const frontierPointLayerMap = () => {
      if (frontierPointLayerCache && frontierPointLayerCacheVersion === stateVersion) return frontierPointLayerCache;
      const layers = new Map();
      for (const entry of state.frontier.values()) {
        const layer = Number.isFinite(entry.layer) ? entry.layer : (entry.gen ?? 0);
        for (const key of frontierEntryPointKeys(entry)) {
          const current = layers.get(key);
          if (current == null || layer < current) layers.set(key, layer);
        }
      }
      frontierPointLayerCache = layers;
      frontierPointLayerCacheVersion = stateVersion;
      return frontierPointLayerCache;
    };
    const frontierPointKeys = () => frontierPointLayerMap().keys();
    const frontierPointLayer = (pointKey) => frontierPointLayerMap().get(pointKey) ?? 0;
    const minFrontierPointLayer = () => {
      let minLayer = Infinity;
      for (const layer of frontierPointLayerMap().values()) minLayer = Math.min(minLayer, layer);
      return minLayer === Infinity ? 0 : minLayer;
    };
    const frontierPointLayerStats = () => {
      const layers = frontierPointLayerMap();
      let minLayer = Infinity;
      for (const layer of layers.values()) minLayer = Math.min(minLayer, layer);
      if (minLayer === Infinity) return { min_layer: 0, min_layer_point_count: 0, point_count: 0 };
      let count = 0;
      for (const layer of layers.values()) if (layer === minLayer) count += 1;
      return { min_layer: minLayer, min_layer_point_count: count, point_count: layers.size };
    };
    const frontierPointSnapshot = () => {
      const points = [];
      for (const [key, layer] of frontierPointLayerMap()) {
        const pos = key.split(",").map(Number);
        const weight = latticeGet(pos);
        if (weight <= 0 || weight >= MAX_SOLID_ANGLE) continue;
        points.push({
          pos,
          weight,
          max_value: MAX_SOLID_ANGLE,
          layer,
          frontier: true
        });
      }
      return points;
    };
    let shellDepthCache = null;
    let shellDepthCacheVersion = -1;
    const completeShellDepthStats = () => {
      if (shellDepthCache && shellDepthCacheVersion === stateVersion) return shellDepthCache;
      const placementIndex = new Map(state.placements.map((placement, index) => [placement, index]));
      const adjacency = state.placements.map(() => []);
      const firstOwnerByFace = new Map();
      for (let placementIdx = 0; placementIdx < state.placements.length; placementIdx += 1) {
        const placement = state.placements[placementIdx];
        for (let faceIdx = 0; faceIdx < placement.orient.faces.length; faceIdx += 1) {
          const faceKey = translatedOrientedFaceKey(placement.orient, faceIdx, placement.translation);
          const previousOwner = firstOwnerByFace.get(faceKey);
          if (previousOwner == null) firstOwnerByFace.set(faceKey, placementIdx);
          else if (previousOwner !== placementIdx) {
            adjacency[previousOwner].push(placementIdx);
            adjacency[placementIdx].push(previousOwner);
          }
        }
      }
      const distances = Array(state.placements.length).fill(Infinity);
      if (distances.length) distances[0] = 0;
      const queue = distances.length ? [0] : [];
      for (let cursor = 0; cursor < queue.length; cursor += 1) {
        const current = queue[cursor];
        for (const neighbor of adjacency[current]) {
          if (distances[neighbor] <= distances[current] + 1) continue;
          distances[neighbor] = distances[current] + 1;
          queue.push(neighbor);
        }
      }
      let minDepth = Infinity;
      let minDepthFaceCount = 0;
      let rootExposedFaceCount = 0;
      let unreachableExposedFaceCount = 0;
      for (const entry of state.frontier.values()) {
        const depth = distances[placementIndex.get(entry.owner_placement)] ?? Infinity;
        if (depth === 0) rootExposedFaceCount += 1;
        if (!Number.isFinite(depth)) unreachableExposedFaceCount += 1;
        if (depth < minDepth) {
          minDepth = depth;
          minDepthFaceCount = 1;
        } else if (depth === minDepth) {
          minDepthFaceCount += 1;
        }
      }
      const maxTileDepth = distances.reduce((maximum, depth) =>
        Number.isFinite(depth) ? Math.max(maximum, depth) : maximum, 0);
      if (minDepth === Infinity) minDepth = maxTileDepth + 1;
      shellDepthCache = {
        complete_shell_depth: minDepth,
        min_shell_face_count: minDepthFaceCount,
        max_tile_shell_depth: maxTileDepth,
        root_exposed_face_count: rootExposedFaceCount,
        unreachable_exposed_face_count: unreachableExposedFaceCount,
        shell_reachable_tiles: distances.filter(Number.isFinite).length,
        owner_depth_by_placement: new Map(state.placements.map((placement, index) => [placement, distances[index]]))
      };
      shellDepthCacheVersion = stateVersion;
      searchStats.max_complete_shell_depth = Math.max(
        searchStats.max_complete_shell_depth,
        minDepth
      );
      return shellDepthCache;
    };
    let candidateInfluenceOffsets = null;
    const candidateInfluenceOffsetKeys = () => {
      if (candidateInfluenceOffsets) return candidateInfluenceOffsets;
      const offsets = new Set(["0,0,0"]);
      for (const tile of prototiles) {
        for (const orient of tile.unique_orientations) {
          for (const anchor of orient.occupancy) {
            for (const occ of orient.occupancy) {
              offsets.add([
                anchor.pos[0] - occ.pos[0],
                anchor.pos[1] - occ.pos[1],
                anchor.pos[2] - occ.pos[2]
              ].join(","));
            }
          }
        }
      }
      candidateInfluenceOffsets = [...offsets].map(key => key.split(",").map(Number));
      return candidateInfluenceOffsets;
    };
    const candidateInfluencePointKeys = (positions) => {
      if (!positions?.length) return null;
      const keys = new Set();
      const offsets = candidateInfluenceOffsetKeys();
      // Precise invalidation is counterproductive for large polycubes: the
      // Cartesian product can contain millions of keys and block deadline
      // checks. Clearing the comparatively small cache is cheaper and exact.
      if (offsets.length * positions.length > 50000) return null;
      if (overBudget()) {
        noteIncompleteSearch();
        return null;
      }
      let generated = 0;
      for (const pos of positions) {
        for (const offset of offsets) {
          generated += 1;
          if ((generated & 255) === 0 && overBudget()) {
            noteIncompleteSearch();
            return null;
          }
          keys.add([pos[0] + offset[0], pos[1] + offset[1], pos[2] + offset[2]].join(","));
        }
      }
      return keys;
    };
    const invalidateCandidateCaches = (changedPositions = null) => {
      const affectedPointKeys = candidateInfluencePointKeys(changedPositions);
      if (!affectedPointKeys) {
        state.vertex_candidate_cache.clear();
        return;
      }
      for (const cacheKey of state.vertex_candidate_cache.keys()) {
        if (affectedPointKeys.has(candidateCachePointKey(cacheKey))) state.vertex_candidate_cache.delete(cacheKey);
      }
    };

    const allSystemTilesAreConvexPolyhedra = prototiles.every(tile => !tile.is_polycube);
    const convexPlacementGeometryCache = new WeakMap();
    const convexPlacementGeometry = placement => {
      const cached = convexPlacementGeometryCache.get(placement);
      if (cached) return cached;
      const subtract = (left, right) => [
        left[0] - right[0], left[1] - right[1], left[2] - right[2]
      ];
      const cross = (left, right) => [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0]
      ];
      const vertices = placement.orient.verts.map(vertex => add3(vertex, placement.translation));
      const edges = new Map();
      const normals = [];
      for (const face of placement.orient.faces) {
        for (let index = 0; index < face.length; index++) {
          const vector = subtract(vertices[face[(index + 1) % face.length]], vertices[face[index]]);
          const reverse = vector.map(value => -value);
          const vectorKey = vector.join(",");
          const reverseKey = reverse.join(",");
          const canonical = vectorKey < reverseKey ? vector : reverse;
          if (canonical.some(Boolean)) edges.set(canonical.join(","), canonical);
        }
        const origin = vertices[face[0]];
        for (let index = 1; index + 1 < face.length; index++) {
          const normal = cross(
            subtract(vertices[face[index]], origin),
            subtract(vertices[face[index + 1]], origin)
          );
          if (!normal.some(Boolean)) continue;
          normals.push(normal);
          break;
        }
      }
      const geometry = {
        vertices,
        edges: [...edges.values()],
        normals,
        minima: [0, 1, 2].map(axis => Math.min(...vertices.map(vertex => vertex[axis]))),
        maxima: [0, 1, 2].map(axis => Math.max(...vertices.map(vertex => vertex[axis])))
      };
      convexPlacementGeometryCache.set(placement, geometry);
      return geometry;
    };
    const convexPlacementInteriorsOverlap = (leftPlacement, rightPlacement) => {
      const left = convexPlacementGeometry(leftPlacement);
      const right = convexPlacementGeometry(rightPlacement);
      for (let coordinate = 0; coordinate < 3; coordinate++) {
        if (
          left.maxima[coordinate] <= right.minima[coordinate] + 1e-9
          || right.maxima[coordinate] <= left.minima[coordinate] + 1e-9
        ) return false;
      }
      const dot = (vertex, axis) =>
        vertex[0] * axis[0] + vertex[1] * axis[1] + vertex[2] * axis[2];
      const cross = (leftVector, rightVector) => [
        leftVector[1] * rightVector[2] - leftVector[2] * rightVector[1],
        leftVector[2] * rightVector[0] - leftVector[0] * rightVector[2],
        leftVector[0] * rightVector[1] - leftVector[1] * rightVector[0]
      ];
      const axes = [...left.normals, ...right.normals];
      for (const leftEdge of left.edges) {
        for (const rightEdge of right.edges) {
          const axis = cross(leftEdge, rightEdge);
          if (axis.some(Boolean)) axes.push(axis);
        }
      }
      for (const axis of axes) {
        const leftValues = left.vertices.map(vertex => dot(vertex, axis));
        const rightValues = right.vertices.map(vertex => dot(vertex, axis));
        if (
          Math.max(...leftValues) <= Math.min(...rightValues) + 1e-9
          || Math.max(...rightValues) <= Math.min(...leftValues) + 1e-9
        ) return false;
      }
      return true;
    };

    const isMoveValid = (move) => {
      const { orient, translation } = move;
      if (overBudget()) {
        noteIncompleteSearch();
        return { ok: false, budget: true, reason: "budget" };
      }
      if (!moveFitsRegion(orient, translation)) return { ok: false, reason: "region" };
      const moveVolume = tileVolumes[move.prototile_idx] ?? 0;
      if (targetRegion && state.placed_volume + moveVolume > targetRegion.volume + 1e-8) {
        return { ok: false, reason: "region-volume" };
      }
      if (allSystemTilesAreConvexPolyhedra) {
        for (const placement of state.placements) {
          if (convexPlacementInteriorsOverlap(placement, move)) {
            return { ok: false, reason: "convex-interior-overlap" };
          }
        }
      } else {
        for (let occupancyIndex = 0; occupancyIndex < orient.occupancy.length; occupancyIndex++) {
          if (occupancyIndex > 0 && (occupancyIndex & 31) === 0 && overBudget()) {
            noteIncompleteSearch();
            return { ok: false, budget: true, reason: "budget" };
          }
          const pt = orient.occupancy[occupancyIndex];
          const g = add3(pt.pos, translation);
          if (latticeGet(g) + pt.weight > MAX_SOLID_ANGLE + SOLID_ANGLE_EPSILON) {
            return { ok: false, reason: "occupancy", position: g };
          }
        }
      }
      for (let f_idx = 0; f_idx < orient.faces.length; f_idx++) {
        if (f_idx > 0 && (f_idx & 31) === 0 && overBudget()) {
          noteIncompleteSearch();
          return { ok: false, budget: true, reason: "budget" };
        }
        const fIdx = orient.faces[f_idx];
        const k = translatedOrientedFaceKey(orient, f_idx, translation);
        const existing = state.frontier.get(k);
        if (existing) {
          const poly = fIdx.map(i => add3(orient.verts[i], translation));
          const rev = [...existing.ordered_verts].slice().reverse();
          if (!isCyclicPermutation(poly, rev)) return { ok: false, reason: "face-orientation" };
        }
      }
      const occData = orient.occupancy.map(pt => ({ pos: add3(pt.pos, translation), weight: pt.weight }));
      return { ok: true, occData };
    };

    const sharedFrontierPoints = (move) => {
      if (move._shared_frontier_points && move._shared_frontier_version === stateVersion) return move._shared_frontier_points;
      const points = new Map();
      const activeFrontierPointLayers = frontierPointLayerMap();
      for (const pt of move.orient.occupancy) {
        const g = add3(pt.pos, move.translation);
        const key = vecKey(g);
        if (activeFrontierPointLayers.has(key)) points.set(key, g);
      }
      const out = [...points.values()];
      move._shared_frontier_points = out;
      move._shared_frontier_version = stateVersion;
      return out;
    };
    const candidateTouchesPoint = (move, pointKey) => {
      for (const pt of move.orient.occupancy) {
        const g = add3(pt.pos, move.translation);
        if (vecKey(g) === pointKey) return true;
      }
      return false;
    };
    const placementGeometryKey = (move) => {
      const vertsKey = move.orient.verts
        .map(vertex => vecKey(add3(vertex, move.translation)))
        .sort()
        .join("|");
      return `${move.prototile_idx}::${vertsKey}`;
    };
    // Polycube lattice tiers are represented in integer coordinates: z3 uses
    // unit cube steps, fcc uses the even-sum half-grid, and half uses all
    // half-grid translations.
    const isPolycubeTranslationVector = (tile, translation) => {
      if (!translation.every(Number.isInteger)) return false;
      if (tile.polycube_lattice === "fcc") return translation.reduce((sum, value) => sum + value, 0) % 2 === 0;
      return true;
    };
    const isPolycubeMoveTranslation = (tile, translation) =>
      isPolycubeTranslationVector(tile, vecSub(translation, startTrans));
    const checkMoveViability = (move) => {
      const validCheck = isMoveValid(move);
      if (!validCheck.ok) return null;
      // A polyhedron can occupy a previously empty angular sector even when
      // every sampled vertex/edge point has already been touched. Requiring a
      // wholly new occupancy point is valid for polycube interior samples, but
      // incorrectly removes legal tetrahedral-honeycomb continuations.
      if (
        prototiles[move.prototile_idx].is_polycube
        && !validCheck.occData.some(o => latticeGet(o.pos) === 0)
      ) return null;
      const sharedPoints = sharedFrontierPoints(move);
      if (sharedPoints.length < minSharedVertices) return null;
      // In 3D, attachment must be by three non-collinear active frontier points;
      // merely touching along a line leaves the next placement underconstrained.
      if (tilingDimension >= 3 && affineRank(sharedPoints) < 2) return null;
      return validCheck;
    };
    const orientedFacesBySignature = new Map();
    for (let prototileIndex = 0; prototileIndex < prototiles.length; prototileIndex++) {
      const tile = prototiles[prototileIndex];
      for (const orient of tile.unique_orientations) {
        for (const face of orient.faces) {
          const vertices = face.map(index => orient.verts[index]);
          const signature = faceSignatureUndirected(vertices);
          if (!orientedFacesBySignature.has(signature)) orientedFacesBySignature.set(signature, []);
          orientedFacesBySignature.get(signature).push({
            prototile_idx: prototileIndex,
            tile,
            orient,
            vertices
          });
        }
      }
    }
    const relativeFaceVertexSetKey = (vertices, anchor) => vertices
      .map(vertex => [
        vertex[0] - anchor[0],
        vertex[1] - anchor[1],
        vertex[2] - anchor[2]
      ].join(","))
      .sort()
      .join("|");
    // Once an oriented face is fixed, attachment can only translate it. Index
    // every possible anchor by its translation-normalized vertex set so an
    // exact shell obligation does not rescan every congruent face and anchor.
    let orientedFaceAnchorsByRelativeVertexSet = null;
    const ensureOrientedFaceAnchorIndex = () => {
      if (orientedFaceAnchorsByRelativeVertexSet) return orientedFaceAnchorsByRelativeVertexSet;
      orientedFaceAnchorsByRelativeVertexSet = new Map();
      for (const entries of orientedFacesBySignature.values()) {
        for (const entry of entries) {
          for (const anchor of entry.vertices) {
            const key = relativeFaceVertexSetKey(entry.vertices, anchor);
            if (!orientedFaceAnchorsByRelativeVertexSet.has(key)) {
              orientedFaceAnchorsByRelativeVertexSet.set(key, []);
            }
            orientedFaceAnchorsByRelativeVertexSet.get(key).push({ entry, anchor });
          }
        }
      }
      return orientedFaceAnchorsByRelativeVertexSet;
    };
    let faceCandidateIndexVersion = -1;
    let faceCandidateIndex = new Map();
    let frontierFaceCandidateIndex = new Map();
    let shellFaceCandidateIndexVersion = -1;
    let shellFaceCandidateIndex = new Map();
    const candidatesForRequiredShellFace = (frontierFaceKey, frontierEntry) => {
      if (shellFaceCandidateIndexVersion !== stateVersion) {
        shellFaceCandidateIndexVersion = stateVersion;
        shellFaceCandidateIndex = new Map();
      }
      if (shellFaceCandidateIndex.has(frontierFaceKey)) {
        return shellFaceCandidateIndex.get(frontierFaceKey);
      }
      searchStats.generic_shell_required_faces_scanned =
        (searchStats.generic_shell_required_faces_scanned ?? 0) + 1;
      const frontierVertices = frontierEntry.ordered_verts;
      const relativeVertexSetKey = relativeFaceVertexSetKey(frontierVertices, frontierVertices[0]);
      const faceAnchorIndex = ensureOrientedFaceAnchorIndex();
      const candidates = new Map();
      candidateScan:
      for (const { entry, anchor } of faceAnchorIndex.get(relativeVertexSetKey) ?? []) {
        searchStats.generic_shell_face_match_attempts =
          (searchStats.generic_shell_face_match_attempts ?? 0) + 1;
        if (overBudget()) {
          noteIncompleteSearch();
          break candidateScan;
        }
        const translation = vecSub(frontierVertices[0], anchor);
        if (entry.tile.is_polycube
          ? !isPolycubeMoveTranslation(entry.tile, translation)
          : !translation.every(Number.isInteger)) continue;
        if (!translatedReverseFaceMatches(entry.vertices, frontierVertices, translation)) continue;
        const move = {
          prototile_idx: entry.prototile_idx,
          translation,
          orient: entry.orient
        };
        const geometryKey = placementGeometryKey(move);
        if (candidates.has(geometryKey)) continue;
        const validity = isMoveValid(move);
        if (!validity.ok) continue;
        candidates.set(geometryKey, {
          ...move,
          occupancy_data: validity.occData,
          dedup_key: geometryKey,
          _matched_frontier_face_keys: new Set([frontierFaceKey])
        });
      }
      const result = [...candidates.values()]
        .sort((left, right) => left.dedup_key.localeCompare(right.dedup_key));
      shellFaceCandidateIndex.set(frontierFaceKey, result);
      return result;
    };
    const faceCandidatesByFrontierPoint = () => {
      if (faceCandidateIndexVersion === stateVersion) return faceCandidateIndex;
      const candidateByGeometry = new Map();
      let faceMatchAttempts = 0;
      candidateScan:
      for (const [frontierFaceKey, frontierEntry] of state.frontier.entries()) {
        if (overBudget()) {
          noteIncompleteSearch();
          break;
        }
        const frontierVertices = frontierEntry.ordered_verts;
        const signature = faceSignatureUndirected(frontierVertices);
        for (const entry of orientedFacesBySignature.get(signature) ?? []) {
          for (const anchor of entry.vertices) {
            faceMatchAttempts += 1;
            if ((faceMatchAttempts & 31) === 0 && overBudget()) {
              noteIncompleteSearch();
              break candidateScan;
            }
            const translation = vecSub(frontierVertices[0], anchor);
            if (entry.tile.is_polycube
              ? !isPolycubeMoveTranslation(entry.tile, translation)
              : !translation.every(Number.isInteger)) continue;
            // Cyclic equality against the reversed frontier is stronger than
            // comparing the unordered canonical face key: it proves both the
            // same vertex set and the required opposing orientation. Compare
            // translated coordinates in place because this loop runs for every
            // oriented face at every search state.
            if (!translatedReverseFaceMatches(entry.vertices, frontierVertices, translation)) continue;
            const move = {
              prototile_idx: entry.prototile_idx,
              translation,
              orient: entry.orient
            };
            const geometryKey = placementGeometryKey(move);
            if (candidateByGeometry.has(geometryKey)) {
              candidateByGeometry.get(geometryKey)._matched_frontier_face_keys.add(frontierFaceKey);
              continue;
            }
            const validity = genericGlobalExtensionEnumeration
              ? isMoveValid(move)
              : checkMoveViability(move);
            if (!validity || validity.ok === false) continue;
            candidateByGeometry.set(geometryKey, {
              ...move,
              occupancy_data: validity.occData,
              dedup_key: geometryKey,
              _matched_frontier_face_keys: new Set([frontierFaceKey])
            });
          }
        }
      }
      const byPoint = new Map();
      for (const candidate of candidateByGeometry.values()) {
        for (const point of sharedFrontierPoints(candidate)) {
          const pointKey = vecKey(point);
          if (!byPoint.has(pointKey)) byPoint.set(pointKey, []);
          byPoint.get(pointKey).push(candidate);
        }
      }
      for (const candidates of byPoint.values()) {
        candidates.sort((left, right) => left.dedup_key.localeCompare(right.dedup_key));
      }
      const byFace = new Map();
      for (const candidate of candidateByGeometry.values()) {
        for (const faceKey of candidate._matched_frontier_face_keys) {
          if (!byFace.has(faceKey)) byFace.set(faceKey, []);
          byFace.get(faceKey).push(candidate);
        }
      }
      for (const candidates of byFace.values()) {
        candidates.sort((left, right) => left.dedup_key.localeCompare(right.dedup_key));
      }
      faceCandidateIndex = byPoint;
      frontierFaceCandidateIndex = byFace;
      faceCandidateIndexVersion = stateVersion;
      return faceCandidateIndex;
    };
    const candidateMoveLayer = (move) => {
      if (move._candidate_layer != null && move._candidate_layer_version === stateVersion) return move._candidate_layer;
      const sharedPoints = sharedFrontierPoints(move);
      let minLayer = Infinity;
      for (const point of sharedPoints) {
        minLayer = Math.min(minLayer, frontierPointLayer(point.join(",")));
      }
      const layer = minLayer === Infinity ? 0 : minLayer + 1;
      move._candidate_layer = layer;
      move._candidate_layer_version = stateVersion;
      return layer;
    };
    const moveLayerLagInfo = (move) => {
      const minLayer = minFrontierPointLayer();
      const moveLayer = candidateMoveLayer(move);
      return {
        move_layer: moveLayer,
        min_frontier_layer: minLayer,
        layer_lag: Math.max(0, moveLayer - minLayer),
        limit: forcedMoveLayerLagCap
      };
    };
    const minimumLayerCompletionScore = (move) => {
      const minimumLayer = minFrontierPointLayer();
      let completedPoints = 0;
      let addedWeight = 0;
      let touchedPoints = 0;
      for (const occupancy of move.orient.occupancy) {
        const position = vecAdd(occupancy.pos, move.translation);
        const pointKey = vecKey(position);
        if (frontierPointLayer(pointKey) !== minimumLayer) continue;
        const currentWeight = latticeGet(position);
        if (currentWeight <= 0 || currentWeight >= MAX_SOLID_ANGLE) continue;
        touchedPoints += 1;
        addedWeight += Math.min(occupancy.weight, MAX_SOLID_ANGLE - currentWeight);
        if (currentWeight + occupancy.weight >= MAX_SOLID_ANGLE) completedPoints += 1;
      }
      return completedPoints * 1e6 + touchedPoints * 1e3 + addedWeight;
    };
    const minimumShellCompletionScore = (move) => {
      const shell = completeShellDepthStats();
      let oldestFacesCovered = 0;
      let totalFacesCovered = 0;
      for (let faceIdx = 0; faceIdx < move.orient.faces.length; faceIdx += 1) {
        const faceKey = translatedOrientedFaceKey(move.orient, faceIdx, move.translation);
        const entry = state.frontier.get(faceKey);
        if (!entry) continue;
        totalFacesCovered += 1;
        const ownerDepth = shell.owner_depth_by_placement.get(entry.owner_placement);
        if (ownerDepth === shell.complete_shell_depth) oldestFacesCovered += 1;
      }
      return oldestFacesCovered * 1e6 + totalFacesCovered;
    };

    const applyMove = (move, { countWork = true } = {}) => {
      if (countWork) searchWorkCounter += 1;
      const moveLayer = Number.isFinite(move.layer) ? move.layer : candidateMoveLayer(move);
      move.layer = moveLayer;
      state.placements.push(move);
      searchStats.max_live_tiles = Math.max(searchStats.max_live_tiles, state.placements.length);
      state.placed_volume += tileVolumes[move.prototile_idx] ?? 0;
      stateVersion += 1;
      const changedOccupancyPositions = move.occupancy_data.map(o => o.pos);
      for (const o of move.occupancy_data) latticeAdd(o.pos, o.weight);

      const gVerts = move.orient.verts.map(v => add3(v, move.translation));
      const neighborColors = new Set();
      const coveredGens = [];
      for (let f_idx = 0; f_idx < move.orient.faces.length; f_idx++) {
        const k = translatedOrientedFaceKey(move.orient, f_idx, move.translation);
        if (state.frontier.has(k)) {
          neighborColors.add(state.frontier.get(k).color_id);
          coveredGens.push(state.frontier.get(k).gen);
        }
      }
      const newGen = moveLayer;
      const available = Array.from({ length: BASE_COLOR_PALETTE_SIZE }, (_, index) => index)
        .filter(index => !neighborColors.has(index));
      const periodicColorId = Array.isArray(move._periodic_cell)
        ? TRANSLATIONAL_CELL_COLOR_OFFSET
          + (move._periodic_base_color_id ?? 0) * 8
          + move._periodic_cell.reduce((colorIndex, coordinate, axis) => {
            const parity = ((Math.round(coordinate) % 2) + 2) % 2;
            return colorIndex + parity * (2 ** axis);
          }, 0)
        : null;
      move.color_id = periodicColorId
        ?? (available.length ? available[Math.floor(nextRandom() * available.length)] : 0);

      const added = [], removed = [], modified_gens = [];

      for (let f_idx = 0; f_idx < move.orient.faces.length; f_idx++) {
        const fIdx = move.orient.faces[f_idx];
        const poly = fIdx.map(i => gVerts[i]);
        const k = translatedOrientedFaceKey(move.orient, f_idx, move.translation);
        if (state.frontier.has(k)) {
          removed.push([k, state.frontier.get(k)]);
          state.frontier.delete(k);
          if (!state.viz_faces.has(k)) state.viz_faces.set(k, []);
          state.viz_faces.get(k).push({ key: k, v: poly, color: COLOR_PALETTE[move.color_id], internal: true, type_idx: move.prototile_idx });
          for (const vf of state.viz_faces.get(k)) vf.internal = true;
        } else {
          faceCounter += 1;
          state.frontier.set(k, { type: move.prototile_idx, face_idx: f_idx, ordered_verts: poly, color_id: move.color_id, id: faceCounter, gen: newGen, layer: moveLayer, owner_placement: move });
          added.push(k);
          const viz = { key: k, v: poly, color: COLOR_PALETTE[move.color_id], internal: false, type_idx: move.prototile_idx };
          if (!state.viz_faces.has(k)) state.viz_faces.set(k, []);
          state.viz_faces.get(k).push(viz);
        }
      }

      invalidateCandidateCaches(changedOccupancyPositions);

      if (added.length) {
        const activeVerts = new Set();
        for (const k of added) for (const v of state.frontier.get(k).ordered_verts) activeVerts.add(v.join(","));
        const vertToKeys = new Map();
        for (const [k, entry] of state.frontier.entries()) {
          for (const v of entry.ordered_verts) {
            const kk = v.join(",");
            if (activeVerts.has(kk)) { if (!vertToKeys.has(kk)) vertToKeys.set(kk, []); vertToKeys.get(kk).push(k); }
          }
        }
        const q = [...added];
        while (q.length) {
          const curr = q.shift();
          const ce = state.frontier.get(curr);
          if (!ce) continue;
          for (const v of ce.ordered_verts) {
            for (const nk of (vertToKeys.get(v.join(",")) ?? [])) {
              if (nk === curr) continue;
              const ne = state.frontier.get(nk);
              if (ne && ne.gen > ce.gen + 1) { modified_gens.push([nk, ne.gen]); ne.gen = ce.gen + 1; q.push(nk); }
            }
          }
        }
      }
      return { added, removed, modified_gens };
    };

    const undoMove = (move, rb, { captureBest = true } = {}) => {
      // Live placement deltas can show a useful patch even when snapshots are
      // configured as "Final only". Preserve a new high-water mark before
      // backtracking so the terminal update does not collapse to the root tile.
      if (captureBest && state.placements.length > (bestSnapshot?.tile_count ?? 0)) {
        snapshot(move.node_id ?? null);
      }
      for (const [k, oldGen] of (rb.modified_gens ?? [])) { const e = state.frontier.get(k); if(e) e.gen = oldGen; }
      const changedOccupancyPositions = move.occupancy_data.map(o => o.pos);
      for (const [k, val] of rb.removed) {
        state.frontier.set(k, val);
        const stack = state.viz_faces.get(k);
        if (stack) { stack.pop(); if (stack.length === 1) stack[0].internal = false; if (stack.length === 0) state.viz_faces.delete(k); }
      }
      invalidateCandidateCaches(changedOccupancyPositions);
      for (const k of rb.added) {
        state.frontier.delete(k);
        const stack = state.viz_faces.get(k);
        if (stack) { stack.pop(); if (stack.length === 0) state.viz_faces.delete(k); }
      }
      for (const o of move.occupancy_data) latticeAdd(o.pos, -o.weight);
      state.placements.pop();
      state.placed_volume -= tileVolumes[move.prototile_idx] ?? 0;
      stateVersion += 1;
    };

    const p0 = prototiles[0];
    const startOrient = p0.unique_orientations[0];
    const startCenter = [0, 1, 2].map(axis =>
      startOrient.verts.reduce((sum, vertex) => sum + vertex[axis], 0) / startOrient.verts.length
    );
    const desiredCenter = targetRegion?.center ?? [0, 0, 0];
    let startTrans = startCenter.map((value, axis) => Math.round(desiredCenter[axis] - value));
    if (targetRegion && !moveFitsRegion(startOrient, startTrans)) {
      const span = [0, 1, 2].map(axis => {
        const coordinates = startOrient.verts.map(vertex => vertex[axis]);
        return Math.max(...coordinates) - Math.min(...coordinates);
      });
      const radius = Math.max(2, ...span.map(Math.ceil));
      const alternatives = [];
      for (let dx = -radius; dx <= radius; dx++) {
        for (let dy = -radius; dy <= radius; dy++) {
          for (let dz = -radius; dz <= radius; dz++) {
            const translation = [startTrans[0] + dx, startTrans[1] + dy, startTrans[2] + dz];
            if (!moveFitsRegion(startOrient, translation)) continue;
            const centerError = translation.reduce((sum, value, axis) => {
              const delta = startCenter[axis] + value - desiredCenter[axis];
              return sum + delta * delta;
            }, 0);
            alternatives.push({ translation, centerError });
          }
        }
      }
      alternatives.sort((left, right) =>
        left.centerError - right.centerError
        || left.translation[0] - right.translation[0]
        || left.translation[1] - right.translation[1]
        || left.translation[2] - right.translation[2]
      );
      if (alternatives.length) startTrans = alternatives[0].translation;
    }
    if (!moveFitsRegion(startOrient, startTrans)) {
      throw new Error("The initial tile does not fit inside the target region");
    }
    const startOcc = startOrient.occupancy.map(pt => ({ pos: add3(pt.pos, startTrans), weight: pt.weight }));

    const frontierPointStats = () => {
      let pointCount = 0;
      for (const weight of state.lattice.values()) {
        if (weight > 0 && weight < MAX_SOLID_ANGLE) pointCount += 1;
      }
      return { point_count: pointCount };
    };
    const calculateFrontierStats = () => {
      const pointLayerStats = frontierPointLayerStats();
      const shellStats = completeShellDepthStats();
      return {
        min_gen: pointLayerStats.min_layer,
        min_layer: pointLayerStats.min_layer,
        count: pointLayerStats.min_layer_point_count,
        total_faces: state.frontier.size,
        ...frontierPointStats(),
        layered_point_count: pointLayerStats.point_count,
        complete_shell_depth: shellStats.complete_shell_depth,
        min_shell_face_count: shellStats.min_shell_face_count,
        max_tile_shell_depth: shellStats.max_tile_shell_depth,
        root_exposed_face_count: shellStats.root_exposed_face_count,
        unreachable_exposed_face_count: shellStats.unreachable_exposed_face_count,
        shell_reachable_tiles: shellStats.shell_reachable_tiles
      };
    };
    const frontierGraphPayload = (graph) => ({
      frontier_points: graph.frontier_points,
      candidates: graph.candidates,
      candidate_count: graph.candidate_count,
      association_count: graph.association_count
    });
    const frontierStatsFromGraph = (graph) => ({
      ...calculateFrontierStats(),
      point_count: graph.frontier_points.length,
      candidate_count: graph.candidate_count,
      association_count: graph.association_count
    });
    const rememberFrontierGraph = (graph) => {
      latestFrontierGraph = graph;
      latestFrontierGraphVersion = stateVersion;
      return frontierStatsFromGraph(graph);
    };
    const frontierStatsWithCandidateCount = () => {
      if (latestFrontierGraph && latestFrontierGraphVersion === stateVersion) {
        return frontierStatsFromGraph(latestFrontierGraph);
      }
      return {
        ...calculateFrontierStats(),
        candidate_count: 0,
        association_count: 0
      };
    };

    const startMove = { prototile_idx: 0, translation: startTrans, occupancy_data: startOcc, orient: startOrient, color_id: 0, layer: 0 };
    state.placements.push(startMove);
    state.placed_volume = tileVolumes[0] ?? 0;
    for (const o of startMove.occupancy_data) latticeAdd(o.pos, o.weight);

    const gVerts0 = startOrient.verts.map(v => add3(v, startTrans));
    for (let f_idx = 0; f_idx < startOrient.faces.length; f_idx++) {
      const fIdx = startOrient.faces[f_idx];
      const poly = fIdx.map(i => gVerts0[i]);
      const k = keyFace(poly);
      faceCounter += 1;
      state.frontier.set(k, { type: 0, face_idx: f_idx, ordered_verts: poly, color_id: 0, id: faceCounter, gen: 0, layer: 0, owner_placement: startMove });
      state.viz_faces.set(k, [{ key: k, v: poly, color: COLOR_PALETTE[0], internal: false, type_idx: 0 }]);
    }
    
    const rootId = nowId();
    const rootStats = frontierStatsWithCandidateCount();
    yield branchSet(null, [{ id: rootId, text: treeTileName(p0.name), frontier_stats: rootStats }]);
    yield nodeStatus(rootId, "working", "", { color_id: 0, frontier_stats: rootStats });
    yield snapshot(rootId);
    await tick();

    const branchCap = Math.max(1, +config.branch_cap || Infinity);
    const agentExhaustive = !!config.agent_exhaustive;
    const agentBranchCap = agentExhaustive
      ? Infinity
      : Math.max(1, +config.agent_branch_cap || (Number.isFinite(branchCap) ? branchCap : 6));
    const nodeLimit = Math.max(1, +config.node_limit || Infinity);
    const candidateCap = Math.max(1, +config.candidate_cap || Infinity);
    const timeLimitMs = Math.max(1, +config.time_limit_ms || Infinity);
    const cpuTimeBudget = config.time_budget_clock === "cpu"
      && typeof process !== "undefined"
      && typeof process.cpuUsage === "function";
    const tilingStrategy = ["translational", "isohedral", "generic"].includes(normalizedStrategy)
      ? normalizedStrategy
      : "auto";
    const requestedMoveOrder = config.move_order ?? "balanced";
    const moveOrder = tilingStrategy === "isohedral" ? "isohedral" : requestedMoveOrder;
    searchStats.move_order = moveOrder;
    const greedyNoBacktrack = !!config.greedy_no_backtrack;
    searchStats.backtracking_enabled = !greedyNoBacktrack;
    const proposalProgram = moveOrder === "proposal"
      ? normalizeProposalProgram(config.proposal_program)
      : null;
    if (proposalProgram) searchStats.proposal_patch_size = proposalProgram.patch_size;
    const usePolicyAgent = moveOrder === "rl" || moveOrder === "agent" || moveOrder === "periodic_agent";
    const faceOrder = config.face_order ?? "coverage";
    searchStats.face_order = faceOrder;
    const configuredForcedLagCap = Number(config.forced_move_layer_lag_cap);
    const forcedMoveLayerLagCap = Number.isFinite(configuredForcedLagCap)
      ? configuredForcedLagCap > 0 ? configuredForcedLagCap : Infinity
      : 2;
    searchStats.generation_lag_cap = forcedMoveLayerLagCap;
    // A proof that no connected count-target patch exists must branch over
    // every legal tile that can be attached through any exposed face. An
    // incomplete frontier vertex with no immediate candidate is not a dead
    // end: growth elsewhere can expose a face that supplies a candidate later.
    // Likewise, a vertex's sole current candidate is not logically forced.
    // The heuristic vertex-MRV search remains useful for witness finding, but
    // only this global extension enumeration is branch-complete.
    const genericConnectedPatchEnumeration = config.generic_connected_patch_enumeration === true
      && tilingStrategy === "generic"
      && criterion === "count"
      && exhaustive
      && !Number.isFinite(forcedMoveLayerLagCap)
      && !Number.isFinite(candidateCap)
      && !greedyNoBacktrack
      && (!usePolicyAgent || agentExhaustive)
      && !proposalProgram;
    searchStats.generic_connected_patch_enumeration = genericConnectedPatchEnumeration;
    // A complete shell of depth r has no exposed face owned by a tile whose
    // face-adjacency distance from the root is less than r. Every infinite
    // face-to-face tiling contains such a shell for every finite r. Unlike the
    // insertion-time point layer, this depth is recomputed from the current
    // patch, so it is independent of the order used to reach the state.
    const genericCompleteShellEnumeration = config.generic_complete_shell_enumeration === true
      && tilingStrategy === "generic"
      && criterion === "shell"
      && exhaustive
      && !Number.isFinite(forcedMoveLayerLagCap)
      && !Number.isFinite(candidateCap)
      && !greedyNoBacktrack
      && (!usePolicyAgent || agentExhaustive)
      && !proposalProgram;
    const genericGlobalExtensionEnumeration = genericConnectedPatchEnumeration
      || genericCompleteShellEnumeration;
    // The complete global enumerators branch from the exact face-extension
    // index below; the much larger frontier point/candidate graph is only a
    // diagnostic visualization.  Headless proof runs may disable that graph
    // without changing the explored tree or the resulting certificate.
    const genericGlobalFrontierGraph = genericGlobalExtensionEnumeration
      && config.generic_global_frontier_graph !== false;
    const genericGlobalZeroFacePruning = genericGlobalExtensionEnumeration
      && config.generic_global_zero_face_pruning === true;
    searchStats.generic_complete_shell_enumeration = genericCompleteShellEnumeration;
    searchStats.generic_global_frontier_graph = genericGlobalFrontierGraph;
    searchStats.generic_global_zero_face_pruning = genericGlobalZeroFacePruning;
    const configuredFailureMemoCapacity = Number(config.generic_failure_memo_max_states);
    const genericFailureMemoCapacity = Number.isFinite(configuredFailureMemoCapacity)
      ? Math.max(0, Math.floor(configuredFailureMemoCapacity))
      : 200000;
    const genericFailureMemoEnabled = config.generic_failure_memo !== false
      && tilingStrategy === "generic"
      && exhaustive
      && !Number.isFinite(forcedMoveLayerLagCap)
      && !Number.isFinite(candidateCap)
      && !greedyNoBacktrack
      && (!usePolicyAgent || agentExhaustive)
      && !proposalProgram
      && genericFailureMemoCapacity > 0;
    const genericFailureMemo = new Set();
    searchStats.generic_failure_memo_enabled = genericFailureMemoEnabled;
    searchStats.generic_failure_memo_capacity = genericFailureMemoEnabled ? genericFailureMemoCapacity : 0;
    const requestedFailureMemoSymmetry = config.generic_failure_memo_symmetry === "rigid"
      ? "rigid"
      : "fixed";
    const genericFailureMemoRigidMotion = genericFailureMemoEnabled
      && requestedFailureMemoSymmetry === "rigid"
      && !targetRegion;
    searchStats.generic_failure_memo_key_equivalence = genericFailureMemoEnabled
      ? genericFailureMemoRigidMotion
        ? criterion === "shell"
          ? "rooted_orientation_preserving_cubic_rigid_motion"
          : "orientation_preserving_cubic_rigid_motion"
        : requestedFailureMemoSymmetry === "rigid" && targetRegion
          ? "fixed_frame_region_guard"
          : "fixed_frame"
      : "disabled";
    const genericFailureStateKey = genericFailureMemoRigidMotion
      ? () => canonicalLatticePatchStateKey(state.placements, { rooted: criterion === "shell" })
      : () => state.placements.map(placementGeometryKey).sort().join("||");
    const configuredGeometricNogoodCapacity = Number(config.generic_geometric_nogood_max_clauses);
    const genericGeometricNogoodCapacity = Number.isFinite(configuredGeometricNogoodCapacity)
      ? Math.max(0, Math.floor(configuredGeometricNogoodCapacity))
      : 20000;
    const genericGeometricNogoodRequested = config.generic_geometric_nogood === true;
    const genericGeometricNogoodEnabled = genericGeometricNogoodRequested
      && genericFailureMemoEnabled
      && !targetRegion
      && genericGeometricNogoodCapacity > 0;
    const genericGeometricNogoodPivotIndex = config.generic_geometric_nogood_index !== false;
    const configuredGeometricNogoodActivationFailures = Number(
      config.generic_geometric_nogood_activation_failure_states
    );
    const genericGeometricNogoodActivationFailures = Number.isFinite(configuredGeometricNogoodActivationFailures)
      ? Math.max(0, Math.floor(configuredGeometricNogoodActivationFailures))
      : 0;
    const configuredGeometricNogoodStagnationFailures = Number(
      config.generic_geometric_nogood_activation_stagnation_failure_states
    );
    const genericGeometricNogoodStagnationFailures = Number.isFinite(configuredGeometricNogoodStagnationFailures)
      ? Math.max(0, Math.floor(configuredGeometricNogoodStagnationFailures))
      : 0;
    let genericGeometricNogoodGrowthMarkTiles = searchStats.max_live_tiles;
    let genericGeometricNogoodFailuresAtLastGrowth = 0;
    const genericGeometricNogood = new GeometricFailureMemo({
      contextMatch: "subset",
      usePivotIndex: genericGeometricNogoodPivotIndex,
      describePlacement: placement => placement?.orient && Array.isArray(placement.translation)
        ? {
            kind: String(placement.prototile_idx),
            orientation: placement.orient.__orientation_id
              ?? placement.orient.verts.map(vecKey).sort().join("/"),
            translation: placement.translation
          }
        : null
    });
    searchStats.generic_geometric_nogood_enabled = genericGeometricNogoodEnabled;
    searchStats.generic_geometric_nogood_disable_reason = genericGeometricNogoodEnabled
      ? null
      : !genericGeometricNogoodRequested
        ? "not_requested"
        : targetRegion
          ? "finite_target_region"
          : !genericFailureMemoEnabled
            ? "exact_failure_memo_disabled"
            : genericGeometricNogoodCapacity <= 0
              ? "zero_capacity"
              : "disabled";
    searchStats.generic_geometric_nogood_pivot_index = genericGeometricNogoodEnabled
      && genericGeometricNogoodPivotIndex;
    searchStats.generic_geometric_nogood_activation_failure_states = genericGeometricNogoodEnabled
      ? genericGeometricNogoodActivationFailures
      : 0;
    searchStats.generic_geometric_nogood_activation_stagnation_failure_states = genericGeometricNogoodEnabled
      ? genericGeometricNogoodStagnationFailures
      : 0;
    searchStats.generic_geometric_nogood_growth_mark_tiles = genericGeometricNogoodGrowthMarkTiles;
    searchStats.generic_geometric_nogood_activated = genericGeometricNogoodEnabled
      && genericGeometricNogoodActivationFailures === 0
      && genericGeometricNogoodStagnationFailures === 0;
    searchStats.generic_geometric_nogood_capacity = genericGeometricNogoodEnabled
      ? genericGeometricNogoodCapacity
      : 0;
    const updateGeometricNogoodStats = () => {
      const stats = genericGeometricNogood.stats();
      searchStats.generic_geometric_nogood_clauses = stats.clauses;
      searchStats.generic_geometric_nogood_prunes = stats.prunes;
      searchStats.generic_geometric_nogood_pivot_index = stats.pivot_index_enabled;
      searchStats.generic_geometric_nogood_compatibility_checks = stats.compatibility_checks;
      searchStats.generic_geometric_nogood_clause_checks = stats.clause_checks;
      searchStats.generic_geometric_nogood_linear_clause_checks = stats.linear_clause_checks;
      searchStats.generic_geometric_nogood_avoided_clause_checks = stats.avoided_clause_checks;
    };
    const rememberGenericFailure = (key, placements) => {
      if (genericFailureMemoEnabled && key && !genericFailureMemo.has(key)) {
        if (genericFailureMemo.size >= genericFailureMemoCapacity) {
          searchStats.generic_failure_memo_capacity_reached = true;
        } else {
          genericFailureMemo.add(key);
          searchStats.generic_failure_memo_states = genericFailureMemo.size;
        }
      }
      if (!genericGeometricNogoodEnabled || !placements?.length) return;
      let encoded = 0;
      for (let anchorIndex = 0; anchorIndex < placements.length; anchorIndex++) {
        if (genericGeometricNogood.clauses.length >= genericGeometricNogoodCapacity) {
          searchStats.generic_geometric_nogood_capacity_reached = true;
          break;
        }
        const result = genericGeometricNogood.encode(
          placements.filter((_, index) => index !== anchorIndex),
          placements[anchorIndex],
          { target_tiles: targetVal, failed_patch_tiles: placements.length }
        );
        if (result.encoded && !result.duplicate) encoded += 1;
      }
      if (encoded) searchStats.generic_geometric_nogood_failure_states += 1;
      updateGeometricNogoodStats();
    };
    const candidatePassesGeometricNogoods = candidate => {
      if (!genericGeometricNogoodEnabled) return true;
      if (!searchStats.generic_geometric_nogood_activated) {
        if (searchStats.max_live_tiles > genericGeometricNogoodGrowthMarkTiles) {
          genericGeometricNogoodGrowthMarkTiles = searchStats.max_live_tiles;
          genericGeometricNogoodFailuresAtLastGrowth = searchStats.generic_geometric_nogood_failure_states;
          searchStats.generic_geometric_nogood_growth_mark_tiles = genericGeometricNogoodGrowthMarkTiles;
        }
        searchStats.generic_geometric_nogood_failures_since_growth = Math.max(
          0,
          searchStats.generic_geometric_nogood_failure_states - genericGeometricNogoodFailuresAtLastGrowth
        );
        if (
          searchStats.generic_geometric_nogood_failure_states < genericGeometricNogoodActivationFailures
          || searchStats.generic_geometric_nogood_failures_since_growth < genericGeometricNogoodStagnationFailures
        ) {
          return true;
        }
        searchStats.generic_geometric_nogood_activated = true;
      }
      const compatible = genericGeometricNogood.compatible(candidate, state.placements);
      updateGeometricNogoodStats();
      return compatible;
    };
    const moveWithinGenerationBand = (move) => {
      const layerLag = moveLayerLagInfo(move);
      move.generation_lag = layerLag.layer_lag;
      return !Number.isFinite(forcedMoveLayerLagCap)
        || layerLag.layer_lag <= forcedMoveLayerLagCap;
    };
    const branchDetails = !!config.branch_details;
    const startedAt = performance.now();
    const cpuStartedAt = cpuTimeBudget ? process.cpuUsage() : null;
    const budgetElapsedMilliseconds = () => {
      if (!cpuTimeBudget) return performance.now() - startedAt;
      const usage = process.cpuUsage(cpuStartedAt);
      return (usage.user + usage.system) / 1000;
    };
    searchStats.time_budget_clock = cpuTimeBudget ? "cpu" : "wall";
    const configuredSafetyMax = Number(config.safety_max_tiles);
    const minimumTileVolume = Math.min(...tileVolumes.filter(volume => volume > 0));
    const regionTileUpperBound = targetRegion && Number.isFinite(minimumTileVolume)
      ? Math.ceil(targetRegion.volume / minimumTileVolume)
      : 2000;
    const defaultSafetyMax = criterion === "count"
      ? Math.max(2000, Math.ceil(targetVal))
      : criterion === "region" ? Math.max(1, regionTileUpperBound) : 2000;
    const safetyMax = Number.isFinite(configuredSafetyMax) && configuredSafetyMax > 0
      ? Math.max(criterion === "count" ? Math.ceil(targetVal) : 1, Math.floor(configuredSafetyMax))
      : defaultSafetyMax;
    const overNodeLimit = () => {
      const reached = Number.isFinite(nodeLimit) && searchWorkCounter >= nodeLimit;
      if (reached && !searchStats.termination_reason) searchStats.termination_reason = "node_limit";
      return reached;
    };
    const overTimeLimit = () => {
      const reached = Number.isFinite(timeLimitMs) && budgetElapsedMilliseconds() >= timeLimitMs;
      if (reached && !searchStats.termination_reason) searchStats.termination_reason = "time_limit";
      return reached;
    };
    const overBudget = () => overNodeLimit() || overTimeLimit();
    const budgetText = () => overNodeLimit() ? "Node limit" : "Time limit";
    let searchIncomplete = false;
    const noteIncompleteSearch = () => { searchIncomplete = true; };
    const goalMet = () => {
      if (criterion === "count") return state.placements.length >= targetVal;
      if (criterion === "layer") return calculateFrontierStats().min_gen >= targetVal;
      if (criterion === "shell") return completeShellDepthStats().complete_shell_depth >= targetVal;
      if (criterion === "region") return !!targetRegion && Math.abs(state.placed_volume - targetRegion.volume) <= 1e-8;
      return false;
    };
    const frontierPointNorm = (option) => Math.abs(option.point[0]) + Math.abs(option.point[1]) + Math.abs(option.point[2]);
    const frontierPointOptions = () => {
      const options = [];
      for (const pointKey of frontierPointKeys()) {
        const weight = state.lattice.get(pointKey) ?? 0;
        if (weight <= 0 || weight >= MAX_SOLID_ANGLE) continue;
        options.push({
          pointKey,
          point: pointKey.split(",").map(Number),
          weight,
          added_depth: frontierPointLayer(pointKey)
        });
      }
      return options.sort((left, right) =>
        left.added_depth - right.added_depth
        || frontierPointNorm(left) - frontierPointNorm(right)
        || left.weight - right.weight
        || left.pointKey.localeCompare(right.pointKey)
      );
    };
    const optionCandidateCount = (option) => (option?.unique_candidates ?? option?.candidates ?? []).length;
    const frontierOptionOrder = (left, right) =>
      left.added_depth - right.added_depth
      || frontierPointNorm(left) - frontierPointNorm(right)
      || optionCandidateCount(left) - optionCandidateCount(right)
      || left.pointKey.localeCompare(right.pointKey);
    const throttledForcedBranchAnalysis = (analysis) => {
      const options = analysis?.options ?? [];
      const nonSingletonBranches = options.filter(option => optionCandidateCount(option) > 1);
      const fallbackBranches = options.filter(option => optionCandidateCount(option) > 0);
      const branches = (nonSingletonBranches.length ? nonSingletonBranches : fallbackBranches)
        .slice()
        .sort(frontierOptionOrder);
      return {
        ...analysis,
        forced: [],
        branches,
        forced_throttled: true,
        forced_throttle_released_singletons: nonSingletonBranches.length > 0
      };
    };

    const moveCoverage = (m) => {
      if (m._coverage != null && m._coverage_version === stateVersion) return m._coverage;
      const shared = sharedFrontierPoints(m);
      const coverage = shared.reduce((sum, point) => sum + Math.min(MAX_SOLID_ANGLE, latticeGet(point)) / MAX_SOLID_ANGLE, 0);
      m._coverage = coverage;
      m._coverage_version = stateVersion;
      return coverage;
    };
    const rootOrientations = prototiles.map(t => t.unique_orientations?.[0] ?? null);
    const sameRootOrientation = (move) => move.orient === rootOrientations[move.prototile_idx] ? 1 : 0;
    const vecSub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
    const vecNeg = (a) => [-a[0], -a[1], -a[2]];
    const vecAdd = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
    const vecEq = (a, b) => a[0] === b[0] && a[1] === b[1] && a[2] === b[2];
    const vecKey = (a) => a.join(",");
    const vecDot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
    const vecCross = (a, b) => [
      a[1] * b[2] - a[2] * b[1],
      a[2] * b[0] - a[0] * b[2],
      a[0] * b[1] - a[1] * b[0]
    ];
    let growthBoundsCacheVersion = -1;
    let growthBoundsCache = null;
    const placementGrowthBounds = () => {
      if (growthBoundsCacheVersion === stateVersion && growthBoundsCache) return growthBoundsCache;
      const mins = [Infinity, Infinity, Infinity];
      const maxs = [-Infinity, -Infinity, -Infinity];
      for (const placement of state.placements) {
        const center = placementCenter(placement);
        for (let axis = 0; axis < 3; axis++) {
          mins[axis] = Math.min(mins[axis], center[axis]);
          maxs[axis] = Math.max(maxs[axis], center[axis]);
        }
      }
      growthBoundsCache = { mins, maxs };
      growthBoundsCacheVersion = stateVersion;
      return growthBoundsCache;
    };
    const prospectiveGrowthShape = (move) => {
      const current = placementGrowthBounds();
      const center = placementCenter(move);
      const spans = [0, 1, 2].map(axis =>
        Math.max(current.maxs[axis], center[axis])
        - Math.min(current.mins[axis], center[axis])
      ).sort((a, b) => a - b);
      const maxSpan = Math.max(spans[2], 1e-9);
      return {
        axis_rank: spans.filter(span => span > 1e-9).length,
        axis_isotropy: spans[0] / maxSpan,
        axis_planarity: spans[1] / maxSpan,
        max_span: spans[2]
      };
    };
    const placementFrame = (placement) => `${placement.prototile_idx}::${placement.orient.__orientation_id ?? ""}`;
    let translationCacheVersion = -1;
    let translationCache = new Map();
    const observedTranslations = () => {
      if (translationCacheVersion === stateVersion) return translationCache;
      const byFrame = new Map();
      const out = new Map();
      for (const placement of state.placements) {
        const frame = placementFrame(placement);
        if (!byFrame.has(frame)) byFrame.set(frame, []);
        byFrame.get(frame).push(placement.translation);
      }
      for (const [frame, translations] of byFrame.entries()) {
        const vectors = new Set();
        for (let i = 0; i < translations.length; i++) {
          for (let j = i + 1; j < translations.length; j++) {
            const v = vecSub(translations[j], translations[i]);
            vectors.add(vecKey(v));
            vectors.add(vecKey(vecNeg(v)));
          }
        }
        out.set(frame, vectors);
      }
      translationCacheVersion = stateVersion;
      translationCache = out;
      return translationCache;
    };
    let pairTranslationCacheVersion = -1;
    let pairTranslationCache = new Map();
    let vectorCountCacheVersion = -1;
    let vectorCountCache = new Map();
    let periodicTranslationRankCacheVersion = -1;
    let periodicTranslationRankCache = 0;
    let positionSetCacheVersion = -1;
    let positionSetCache = new Set();
    let vertexSetCacheVersion = -1;
    let vertexSetCache = new Set();
    const observedPairTranslations = () => {
      if (pairTranslationCacheVersion === stateVersion) return pairTranslationCache;
      const out = new Map();
      for (let i = 0; i < state.placements.length; i++) {
        const a = state.placements[i];
        const aFrame = placementFrame(a);
        for (let j = 0; j < state.placements.length; j++) {
          if (i === j) continue;
          const b = state.placements[j];
          const key = `${aFrame}=>${placementFrame(b)}`;
          if (!out.has(key)) out.set(key, new Set());
          out.get(key).add(vecKey(vecSub(b.translation, a.translation)));
        }
      }
      pairTranslationCacheVersion = stateVersion;
      pairTranslationCache = out;
      return pairTranslationCache;
    };
    const observedVectorCounts = () => {
      if (vectorCountCacheVersion === stateVersion) return vectorCountCache;
      const out = new Map();
      for (let i = 0; i < state.placements.length; i++) {
        for (let j = 0; j < state.placements.length; j++) {
          if (i === j) continue;
          const key = vecKey(vecSub(state.placements[j].translation, state.placements[i].translation));
          out.set(key, (out.get(key) ?? 0) + 1);
        }
      }
      vectorCountCacheVersion = stateVersion;
      vectorCountCache = out;
      return vectorCountCache;
    };
    const placementPositionSet = () => {
      if (positionSetCacheVersion === stateVersion) return positionSetCache;
      positionSetCache = new Set(state.placements.map(placement => vecKey(placement.translation)));
      positionSetCacheVersion = stateVersion;
      return positionSetCache;
    };
    periodicTranslationRank = () => {
      if (periodicTranslationRankCacheVersion === stateVersion) return periodicTranslationRankCache;
      const vectors = [];
      for (const frameVectors of observedTranslations().values()) {
        for (const key of frameVectors) vectors.push(key.split(",").map(Number));
      }
      periodicTranslationRankCache = affineRank([[0, 0, 0], ...vectors]);
      periodicTranslationRankCacheVersion = stateVersion;
      return periodicTranslationRankCache;
    };
    const periodicRankGain = (move) => {
      const currentRank = periodicTranslationRank();
      if (currentRank >= 3) return 0;
      const vectors = [[0, 0, 0]];
      for (const frameVectors of observedTranslations().values()) {
        for (const key of frameVectors) vectors.push(key.split(",").map(Number));
      }
      const frame = placementFrame(move);
      for (const placement of state.placements) {
        if (placementFrame(placement) !== frame) continue;
        vectors.push(vecSub(move.translation, placement.translation));
      }
      const nextRank = affineRank(vectors);
      return Math.max(0, nextRank - currentRank);
    };
    const placementVertexSet = () => {
      if (vertexSetCacheVersion === stateVersion) return vertexSetCache;
      const vertices = new Set();
      for (const placement of state.placements) {
        for (const vertex of placement.orient.verts) vertices.add(vecKey(vecAdd(vertex, placement.translation)));
      }
      vertexSetCache = vertices;
      vertexSetCacheVersion = stateVersion;
      return vertexSetCache;
    };
    const sharedVertexCount = (move) => {
      if (move._shared_vertex_count != null && move._shared_vertex_version === stateVersion) return move._shared_vertex_count;
      const existingVertices = placementVertexSet();
      const count = move.orient.verts.reduce((sum, vertex) => sum + (existingVertices.has(vecKey(vecAdd(vertex, move.translation))) ? 1 : 0), 0);
      move._shared_vertex_count = count;
      move._shared_vertex_version = stateVersion;
      return count;
    };
    const periodicContinuation = (move) => {
      const frame = placementFrame(move);
      const seen = observedTranslations().get(frame);
      if (!seen?.size) return 0;
      for (const placement of state.placements) {
        if (placement.prototile_idx !== move.prototile_idx || placement.orient !== move.orient) continue;
        if (seen.has(vecKey(vecSub(move.translation, placement.translation)))) return 1;
      }
      return 0;
    };
    const pairPeriodicContinuation = (move) => {
      const targetFrame = placementFrame(move);
      const pairs = observedPairTranslations();
      if (!pairs.size) return 0;
      const hits = new Set();
      for (const placement of state.placements) {
        const key = `${placementFrame(placement)}=>${targetFrame}`;
        const seen = pairs.get(key);
        if (!seen?.size) continue;
        const delta = vecKey(vecSub(move.translation, placement.translation));
        if (seen.has(delta)) hits.add(`${key}::${delta}`);
      }
      return hits.size;
    };
    const vectorRepeatScore = (move) => {
      const counts = observedVectorCounts();
      if (!counts.size) return 0;
      const hits = new Set();
      for (const placement of state.placements) {
        const delta = vecKey(vecSub(move.translation, placement.translation));
        if (counts.has(delta)) hits.add(delta);
      }
      return hits.size;
    };
    const vectorOrbitKey = (vector) => vector.map(value => Math.abs(value)).sort((a, b) => a - b).join(",");
    let firstCoronaCacheVersion = -1;
    let firstCoronaNeighborhoodRules = new Set();
    const firstCoronaOrbits = () => {
      if (firstCoronaCacheVersion === stateVersion) return firstCoronaNeighborhoodRules;
      const root = state.placements[0];
      const rules = new Set();
      if (root) {
        const rootVertices = new Set(root.orient.verts.map(vertex => vecKey(vecAdd(vertex, root.translation))));
        for (const placement of state.placements.slice(1)) {
          let shared = 0;
          for (const vertex of placement.orient.verts) {
            if (rootVertices.has(vecKey(vecAdd(vertex, placement.translation)))) shared += 1;
          }
          if (shared >= minSharedVertices) {
            rules.add(`${placement.prototile_idx}:${vectorOrbitKey(vecSub(placement.translation, root.translation))}`);
          }
        }
      }
      firstCoronaNeighborhoodRules = rules;
      firstCoronaCacheVersion = stateVersion;
      return firstCoronaNeighborhoodRules;
    };
    const isohedralCoronaScore = (move) => {
      const rules = firstCoronaOrbits();
      if (!rules.size) return 0;
      const hits = new Set();
      for (const placement of state.placements) {
        const orbit = vectorOrbitKey(vecSub(move.translation, placement.translation));
        const rule = `${move.prototile_idx}:${orbit}`;
        if (rules.has(rule)) hits.add(rule);
      }
      return hits.size;
    };
    const parallelogramCompletionScore = (move) => {
      const positions = placementPositionSet();
      if (positions.size < 3) return 0;
      const translations = state.placements.map(placement => placement.translation);
      const hits = new Set();
      for (let i = 0; i < translations.length; i++) {
        for (let j = i + 1; j < translations.length; j++) {
          const fourth = vecSub(vecAdd(translations[i], translations[j]), move.translation);
          const fourthKey = vecKey(fourth);
          if (!positions.has(fourthKey)) continue;
          const key = [
            vecKey(translations[i]),
            vecKey(translations[j]),
            fourthKey
          ].sort().join("|");
          hits.add(key);
        }
      }
      return hits.size;
    };
    const coveredFrontierFaceScore = (move, targetGen = null) => {
      const gVerts = move.orient.verts.map(v => vecAdd(v, move.translation));
      let score = 0;
      for (const fIdx of move.orient.faces) {
        const poly = fIdx.map(i => gVerts[i]);
        const entry = state.frontier.get(keyFace(poly));
        if (!entry) continue;
        if (targetGen != null && entry.gen !== targetGen) continue;
        score += 1;
      }
      return score;
    };
    const reflectVerticesAcrossFace = (vertices, faceVertices) => {
      if (faceVertices.length < 3) return null;
      const a = faceVertices[0];
      const normal = vecCross(vecSub(faceVertices[1], a), vecSub(faceVertices[2], a));
      const normalSquared = vecDot(normal, normal);
      if (normalSquared <= 0) return null;
      return vertices.map(vertex => {
        const factor = 2 * vecDot(normal, vecSub(vertex, a)) / normalSquared;
        return vertex.map((value, axis) => {
          const reflectedValue = value - factor * normal[axis];
          const rounded = Math.round(reflectedValue);
          return Math.abs(reflectedValue - rounded) < 1e-8 ? rounded : reflectedValue;
        });
      });
    };
    const reflectedOwnerMatchScore = (move) => {
      if (prototiles.length !== 1) return 0;
      const candidateVertices = move.orient.verts.map(vertex => vecAdd(vertex, move.translation));
      const candidateKey = keyFace(candidateVertices);
      let score = 0;
      for (const face of move.orient.faces) {
        const globalFace = face.map(index => candidateVertices[index]);
        const frontierEntry = state.frontier.get(keyFace(globalFace));
        const owner = frontierEntry?.owner_placement;
        if (!owner || owner.prototile_idx !== move.prototile_idx || globalFace.length < 3) continue;
        const ownerVertices = owner.orient.verts.map(vertex => vecAdd(vertex, owner.translation));
        const reflected = reflectVerticesAcrossFace(ownerVertices, globalFace);
        if (reflected && keyFace(reflected) === candidateKey) score += 1;
      }
      if (score > 0) searchStats.reflection_continuations_seen += 1;
      return score;
    };
    const euclideanMod = (value, modulus) => ((value % modulus) + modulus) % modulus;
    const orientationBounds = (orient) => {
      const mins = [Infinity, Infinity, Infinity];
      const maxs = [-Infinity, -Infinity, -Infinity];
      for (const vertex of orient.verts) {
        for (let axis = 0; axis < 3; axis++) {
          mins[axis] = Math.min(mins[axis], vertex[axis]);
          maxs[axis] = Math.max(maxs[axis], vertex[axis]);
        }
      }
      return { mins, maxs };
    };
    const axisAlignedFaceInfo = (orient, face) => {
      const verts = face.map(index => orient.verts[index]);
      for (let axis = 0; axis < 3; axis++) {
        const coord = verts[0][axis];
        if (!verts.every(vertex => vertex[axis] === coord)) continue;
        const otherAxes = [0, 1, 2].filter(item => item !== axis);
        const mins = [Infinity, Infinity, Infinity];
        const maxs = [-Infinity, -Infinity, -Infinity];
        for (const vertex of verts) {
          for (const other of otherAxes) {
            mins[other] = Math.min(mins[other], vertex[other]);
            maxs[other] = Math.max(maxs[other], vertex[other]);
          }
        }
        return { axis, coord, mins, maxs, otherAxes };
      }
      return null;
    };
    const polycubeCellsForOrient = (orient) => {
      if (orient._polycube_cells) return orient._polycube_cells;
      const xFaces = [];
      for (const face of orient.faces ?? []) {
        const info = axisAlignedFaceInfo(orient, face);
        if (info?.axis === 0) xFaces.push(info);
      }
      const { mins, maxs } = orientationBounds(orient);
      const cells = [];
      for (let x = Math.floor(mins[0]); x < Math.ceil(maxs[0]); x++) {
        for (let y = Math.floor(mins[1]); y < Math.ceil(maxs[1]); y++) {
          for (let z = Math.floor(mins[2]); z < Math.ceil(maxs[2]); z++) {
            const center = [x + 0.5, y + 0.5, z + 0.5];
            let crossings = 0;
            for (const face of xFaces) {
              if (face.coord <= center[0]) continue;
              const [a, b] = face.otherAxes;
              if (center[a] > face.mins[a] && center[a] < face.maxs[a] &&
                  center[b] > face.mins[b] && center[b] < face.maxs[b]) {
                crossings += 1;
              }
            }
            if (crossings % 2 === 1) cells.push([x, y, z]);
          }
        }
      }
      orient._polycube_cells = cells;
      return cells;
    };
    const hnfCandidates = (volume) => {
      const candidates = [];
      for (let a = 1; a <= volume; a++) {
        if (volume % a !== 0) continue;
        for (let d = 1; d <= volume / a; d++) {
          if (volume % (a * d) !== 0) continue;
          const f = volume / (a * d);
          for (let b = 0; b < a; b++) {
            for (let c = 0; c < a; c++) {
              for (let e = 0; e < d; e++) {
                const vectors = [[a, 0, 0], [b, d, 0], [c, e, f]];
                const skew = Math.abs(b) + Math.abs(c) + Math.abs(e);
                const span = Math.max(a, d, f) - Math.min(a, d, f);
                candidates.push({ a, d, f, b, c, e, vectors, skew, span });
              }
            }
          }
        }
      }
      return candidates.sort((left, right) =>
        left.span - right.span
        || left.skew - right.skew
        || left.a - right.a
        || left.d - right.d
        || left.f - right.f
        || left.b - right.b
        || left.c - right.c
        || left.e - right.e
      );
    };
    const hnfFundamentalCells = (hnf) => {
      const cells = [];
      for (let x = 0; x < hnf.a; x++) {
        for (let y = 0; y < hnf.d; y++) {
          for (let z = 0; z < hnf.f; z++) cells.push([x, y, z]);
        }
      }
      return cells;
    };
    const hnfReducePoint = (point, hnf) => {
      let [x, y, z] = point;
      let q = Math.floor(z / hnf.f);
      x -= q * hnf.c;
      y -= q * hnf.e;
      z -= q * hnf.f;
      q = Math.floor(y / hnf.d);
      x -= q * hnf.b;
      y -= q * hnf.d;
      q = Math.floor(x / hnf.a);
      x -= q * hnf.a;
      return [euclideanMod(x, hnf.a), euclideanMod(y, hnf.d), euclideanMod(z, hnf.f)];
    };
    const cellSetInQuotient = (cells, hnf, translation = [0, 0, 0]) => {
      const out = new Set();
      for (const cell of cells) {
        const key = vecKey(hnfReducePoint(vecAdd(cell, translation), hnf));
        if (out.has(key)) return null;
        out.add(key);
      }
      return out;
    };
    const translatedFaceVector = (source, target) => {
      if (source.length !== target.length || source.length < 3) return null;
      const targetKeys = new Set(target.map(vecKey));
      for (const targetVertex of target) {
        const translation = vecSub(targetVertex, source[0]);
        if (translation.every(value => value === 0)) continue;
        if (source.every(vertex => targetKeys.has(vecKey(vecAdd(vertex, translation))))) {
          return translation;
        }
      }
      return null;
    };
    const convexPolyhedronVolume = (orient) => {
      const center = [0, 1, 2].map(axis =>
        orient.verts.reduce((sum, vertex) => sum + vertex[axis], 0) / orient.verts.length
      );
      let volume = 0;
      for (const face of orient.faces) {
        const a = vecSub(orient.verts[face[0]], center);
        for (let i = 1; i < face.length - 1; i++) {
          const b = vecSub(orient.verts[face[i]], center);
          const c = vecSub(orient.verts[face[i + 1]], center);
          volume += Math.abs(determinant3([a, b, c])) / 6;
        }
      }
      return volume;
    };
    const isClosedConvexPolyhedron = (orient) => {
      const edgeCounts = new Map();
      const usedVertices = new Set();
      for (const face of orient.faces) {
        if (new Set(face).size !== face.length) return false;
        for (let i = 0; i < face.length; i++) {
          const a = face[i];
          const b = face[(i + 1) % face.length];
          usedVertices.add(a);
          usedVertices.add(b);
          const edgeKey = a < b ? `${a},${b}` : `${b},${a}`;
          edgeCounts.set(edgeKey, (edgeCounts.get(edgeKey) ?? 0) + 1);
        }
        const origin = orient.verts[face[0]];
        let normal = null;
        for (let i = 1; i < face.length - 1 && !normal; i++) {
          const a = vecSub(orient.verts[face[i]], origin);
          const b = vecSub(orient.verts[face[i + 1]], origin);
          const candidate = [
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]
          ];
          if (candidate.some(Boolean)) normal = candidate;
        }
        if (!normal) return false;
        const faceSet = new Set(face);
        let side = 0;
        for (let vertexIndex = 0; vertexIndex < orient.verts.length; vertexIndex++) {
          const delta = vecSub(orient.verts[vertexIndex], origin);
          const signedDistance = normal[0] * delta[0] + normal[1] * delta[1] + normal[2] * delta[2];
          if (faceSet.has(vertexIndex)) {
            if (signedDistance !== 0) return false;
            continue;
          }
          if (signedDistance === 0) continue;
          const vertexSide = Math.sign(signedDistance);
          if (side && vertexSide !== side) return false;
          side = vertexSide;
        }
        if (!side) return false;
      }
      return usedVertices.size === orient.verts.length
        && [...edgeCounts.values()].every(count => count === 2);
    };
    const findTranslationalPolyhedronTemplate = () => {
      if (prototiles.length !== 1 || prototiles[0].is_polycube) return null;
      const tile = prototiles[0];
      const orientationIndex = tile.unique_orientations.indexOf(startOrient);
      if (orientationIndex < 0 || startOrient.faces.length % 2 !== 0) return null;
      if (!isClosedConvexPolyhedron(startOrient)) return null;
      const faceVertices = startOrient.faces.map(face => face.map(index => startOrient.verts[index]));
      const unused = new Set(faceVertices.map((_, index) => index));
      const facePairs = [];
      while (unused.size) {
        const sourceIndex = unused.values().next().value;
        unused.delete(sourceIndex);
        let match = null;
        for (const targetIndex of unused) {
          const translation = translatedFaceVector(faceVertices[sourceIndex], faceVertices[targetIndex]);
          if (!translation) continue;
          match = { source_face: sourceIndex, target_face: targetIndex, translation };
          break;
        }
        if (!match) return null;
        unused.delete(match.target_face);
        facePairs.push(match);
      }
      const polyhedronVolume = convexPolyhedronVolume(startOrient);
      const tolerance = 1e-9 * Math.max(1, polyhedronVolume);
      let periodVectors = null;
      let latticeDeterminant = null;
      for (let i = 0; i < facePairs.length && !periodVectors; i++) {
        for (let j = i + 1; j < facePairs.length && !periodVectors; j++) {
          for (let k = j + 1; k < facePairs.length; k++) {
            const basis = [
              facePairs[i].translation,
              facePairs[j].translation,
              facePairs[k].translation
            ];
            const determinant = determinant3(basis);
            if (Math.abs(determinant) <= 1e-9) continue;
            if (Math.abs(Math.abs(determinant) - polyhedronVolume) > tolerance) continue;
            const allTranslationsInLattice = facePairs.every(pair => {
              const vector = pair.translation;
              const coordinates = [
                determinant3([vector, basis[1], basis[2]]) / determinant,
                determinant3([basis[0], vector, basis[2]]) / determinant,
                determinant3([basis[0], basis[1], vector]) / determinant
              ];
              return coordinates.every(value => Math.abs(value - Math.round(value)) <= 1e-9);
            });
            if (!allTranslationsInLattice) continue;
            periodVectors = basis.map(vector => vector.slice());
            latticeDeterminant = Math.abs(determinant);
            break;
          }
        }
      }
      if (!periodVectors) return null;
      const isParallelepiped = startOrient.verts.length === 8
        && startOrient.faces.length === 6
        && startOrient.faces.every(face => face.length === 4);
      return {
        kind: isParallelepiped
          ? "one_tile_translational_parallelepiped"
          : "one_tile_translational_lattice_polyhedron",
        tile_volume: polyhedronVolume,
        tile_volumes: [polyhedronVolume],
        cell_volume: latticeDeterminant,
        period_vectors: periodVectors,
        motif: [{
          prototile_idx: 0,
          orientation_index: orientationIndex,
          orientation_id: startOrient.__orientation_id ?? null,
          translation: [0, 0, 0]
        }],
        mixed_prototile: false,
        prototile_counts: [{ prototile_idx: 0, count: 1 }],
        proof: {
          method: "paired_facets_integral_lattice_and_equal_covolume",
          face_pairs: facePairs,
          polyhedron_volume: polyhedronVolume,
          lattice_determinant: latticeDeterminant
        }
      };
    };
    const findPeriodicTemplate = (requestedPeriod) => {
      requestedPeriod = Math.max(1, Math.floor(+requestedPeriod || 1));
      // Refined FCC and 1/2 Z³ coordinates multiply polycube cell volumes by
      // eight. A cap of 64 silently excluded ordinary catalog tiles such as
      // Letter O and 2-Cross before the quotient checker even ran.
      const maxCellVolume = config.periodic_patch_unbounded
        ? Infinity
        : Math.max(1, +config.periodic_template_max_volume || 512);
      const translationalPolyhedronTemplate = findTranslationalPolyhedronTemplate();
      if (translationalPolyhedronTemplate) return translationalPolyhedronTemplate;
      const requireAllTypes = prototiles.length > 1 && config.periodic_require_all_types !== false;
      if (requireAllTypes && prototiles.length > requestedPeriod) return null;
      if (!prototiles.every(tile => tile.is_polycube)) return null;
      if (new Set(prototiles.map(tile => tile.polycube_lattice)).size > 1) return null;
      const orientationGroups = prototiles.map((tile, prototileIndex) =>
        tile.unique_orientations
          .map((orient, orientationIndex) => ({
            prototileIndex,
            orient,
            orientationIndex,
            cells: polycubeCellsForOrient(orient)
          }))
          .filter(entry => entry.cells.length > 0)
      );
      if (orientationGroups.some(group => group.length === 0)) return null;
      const tileVolumes = orientationGroups.map(group => group[0].cells.length);
      if (orientationGroups.some((group, prototileIndex) =>
        group.some(entry => entry.cells.length !== tileVolumes[prototileIndex])
      )) return null;
      const rootOrientationIndex = prototiles[0].unique_orientations.indexOf(startOrient);
      if (rootOrientationIndex < 0) return null;
      const rootEntry = orientationGroups[0].find(entry => entry.orientationIndex === rootOrientationIndex);
      if (!rootEntry) return null;
      const rootVolume = rootEntry.cells.length;
      if (requestedPeriod === 1 && prototiles.length === 1) {
        // Fast exact test for lattice tiles whose quotient is cyclic. This
        // catches cross-shaped polycubes efficiently and avoids enumerating
        // thousands of Hermite normal forms. A bijection from the tile cells
        // to Z/nZ proves that translates by the homomorphism kernel partition
        // every integer cell exactly once.
        const n = rootVolume;
        for (let b = 0; b < n; b++) {
          for (let c = 0; c < n; c++) {
            if (overBudget()) {
              noteIncompleteSearch();
              return null;
            }
            const residues = new Set(rootEntry.cells.map(([x, y, z]) =>
              euclideanMod(x + b * y + c * z, n)
            ));
            if (residues.size !== n) continue;
            const periodVectors = [
              [n, 0, 0],
              [-b, 1, 0],
              [-c, 0, 1]
            ];
            if (periodVectors.some(vector =>
              !isPolycubeTranslationVector(prototiles[0], vector)
            )) continue;
            return {
              kind: "one_tile_cyclic_quotient",
              tile_volume: n,
              tile_volumes: [n],
              cell_volume: n,
              period_vectors: periodVectors,
              motif: [{
                prototile_idx: 0,
                orientation_index: rootOrientationIndex,
                orientation_id: rootEntry.orient.__orientation_id ?? null,
                translation: [0, 0, 0],
                quotient_cells: [...residues].sort((left, right) => left - right)
              }],
              mixed_prototile: false,
              prototile_counts: [{ prototile_idx: 0, count: 1 }],
              proof: {
                method: "cyclic_quotient_bijection",
                modulus: n,
                coefficients: [1, b, c]
              }
            };
          }
        }
      }
      const candidateCellVolumes = new Set();
      const enumerateCellVolumes = (slotsLeft, volume, usedTypes) => {
        if (slotsLeft === 0) {
          if (!requireAllTypes || usedTypes.size === prototiles.length) candidateCellVolumes.add(volume);
          return;
        }
        for (let prototileIndex = 0; prototileIndex < prototiles.length; prototileIndex++) {
          const nextTypes = new Set(usedTypes);
          nextTypes.add(prototileIndex);
          enumerateCellVolumes(slotsLeft - 1, volume + tileVolumes[prototileIndex], nextTypes);
        }
      };
      enumerateCellVolumes(requestedPeriod - 1, rootVolume, new Set([0]));
      const allOrientations = orientationGroups.flat();
      const minimumTileVolume = Math.min(...tileVolumes);
      const maximumTileVolume = Math.max(...tileVolumes);
      const configuredHnfLimit = Number(config.periodic_hnf_candidate_limit);
      const hnfCandidateLimit = Number.isFinite(configuredHnfLimit) && configuredHnfLimit > 0
        ? Math.floor(configuredHnfLimit)
        : 20000;
      let hnfCandidatesVisited = 0;
      for (const cellVolume of [...candidateCellVolumes].filter(volume => volume <= maxCellVolume).sort((a, b) => a - b)) {
        for (const hnf of hnfCandidates(cellVolume)) {
        hnfCandidatesVisited += 1;
        if (hnfCandidatesVisited > hnfCandidateLimit || overBudget()) {
          noteIncompleteSearch();
          return null;
        }
        if (hnf.vectors.some(vector =>
          prototiles.some(tile => !isPolycubeTranslationVector(tile, vector))
        )) continue;
        const fundamentalCells = hnfFundamentalCells(hnf);
        const universe = new Set(fundamentalCells.map(vecKey));
        const rootSet = cellSetInQuotient(rootEntry.cells, hnf);
        if (!rootSet || rootSet.size !== rootVolume) continue;
        const complement = new Set();
        for (const key of universe) if (!rootSet.has(key)) complement.add(key);
        const candidatesBySignature = new Map();
        for (const entry of allOrientations) {
          for (const translation of fundamentalCells) {
            if (!isPolycubeTranslationVector(prototiles[entry.prototileIndex], translation)) continue;
            const candidateSet = cellSetInQuotient(entry.cells, hnf, translation);
            if (!candidateSet || candidateSet.size !== tileVolumes[entry.prototileIndex]) continue;
            let containedInComplement = true;
            for (const key of candidateSet) {
              if (!complement.has(key)) { containedInComplement = false; break; }
            }
            if (!containedInComplement) continue;
            const signature = `${entry.prototileIndex}::${[...candidateSet].sort().join("|")}`;
            if (!candidatesBySignature.has(signature)) {
              candidatesBySignature.set(signature, {
                cells: candidateSet,
                motif: {
                  prototile_idx: entry.prototileIndex,
                  orientation_index: entry.orientationIndex,
                  orientation_id: entry.orient.__orientation_id ?? null,
                  translation: translation.slice()
                }
              });
            }
          }
        }
        const candidates = [...candidatesBySignature.values()];
        const byCell = new Map();
        for (const candidate of candidates) {
          for (const key of candidate.cells) {
            if (!byCell.has(key)) byCell.set(key, []);
            byCell.get(key).push(candidate);
          }
        }
        const exactCover = (remaining, chosen, usedTypes) => {
          if (overBudget()) {
            noteIncompleteSearch();
            return null;
          }
          const slotsLeft = requestedPeriod - 1 - chosen.length;
          if (!remaining.size) {
            return slotsLeft === 0 && (!requireAllTypes || usedTypes.size === prototiles.length)
              ? chosen
              : null;
          }
          if (slotsLeft <= 0) return null;
          if (remaining.size < slotsLeft * minimumTileVolume || remaining.size > slotsLeft * maximumTileVolume) return null;
          if (requireAllTypes) {
            let missingTypes = 0;
            for (let typeIndex = 0; typeIndex < prototiles.length; typeIndex++) {
              if (!usedTypes.has(typeIndex)) missingTypes += 1;
            }
            if (missingTypes > slotsLeft) return null;
          }
          let pivotCandidates = null;
          for (const key of remaining) {
            const options = (byCell.get(key) ?? []).filter(candidate =>
              [...candidate.cells].every(cell => remaining.has(cell))
            );
            if (!options.length) return null;
            if (!pivotCandidates || options.length < pivotCandidates.length) pivotCandidates = options;
          }
          for (const candidate of pivotCandidates ?? []) {
            const nextRemaining = new Set(remaining);
            for (const key of candidate.cells) nextRemaining.delete(key);
            const nextTypes = new Set(usedTypes);
            nextTypes.add(candidate.motif.prototile_idx);
            const solution = exactCover(nextRemaining, [...chosen, candidate], nextTypes);
            if (solution) return solution;
          }
          return null;
        };
        const solution = exactCover(complement, [], new Set([0]));
        if (!solution) continue;
        const motif = [
          {
            prototile_idx: 0,
            orientation_index: rootOrientationIndex,
            orientation_id: rootEntry.orient.__orientation_id ?? null,
            translation: [0, 0, 0],
            quotient_cells: [...rootSet].sort()
          },
          ...solution.map(candidate => ({
            ...candidate.motif,
            quotient_cells: [...candidate.cells].sort()
          }))
        ];
        const prototileCounts = new Map();
        for (const item of motif) {
          prototileCounts.set(item.prototile_idx, (prototileCounts.get(item.prototile_idx) ?? 0) + 1);
        }
        return {
          kind: requestedPeriod === 2
            ? "two_tile_periodic_torus"
            : `${requestedPeriod}_tile_periodic_torus`,
          tile_volume: cellVolume / requestedPeriod,
          tile_volumes: tileVolumes.slice(),
          cell_volume: cellVolume,
          period_vectors: hnf.vectors.map(vector => vector.slice()),
          motif,
          mixed_prototile: prototileCounts.size > 1,
          prototile_counts: [...prototileCounts.entries()]
            .sort((left, right) => left[0] - right[0])
            .map(([prototile_idx, count]) => ({ prototile_idx, count }))
        };
      }
      }
      return null;
    };
    const axisNormalForFace = (verts) => {
      if (!verts || verts.length < 3) return null;
      const p0 = verts[0];
      for (let i = 1; i < verts.length - 1; i++) {
        const a = vecSub(verts[i], p0);
        const b = vecSub(verts[i + 1], p0);
        const cross = [
          a[1] * b[2] - a[2] * b[1],
          a[2] * b[0] - a[0] * b[2],
          a[0] * b[1] - a[1] * b[0]
        ];
        const abs = cross.map(Math.abs);
        const axis = abs.indexOf(Math.max(...abs));
        if (!abs[axis]) continue;
        if (abs.some((value, idx) => idx !== axis && value !== 0)) return null;
        const normal = [0, 0, 0];
        normal[axis] = Math.sign(cross[axis]);
        return normal;
      }
      return null;
    };
    const faceCenter = (verts) => {
      const center = [0, 0, 0];
      for (const v of verts) for (let i = 0; i < 3; i++) center[i] += v[i];
      for (let i = 0; i < 3; i++) {
        center[i] /= verts.length;
        if (Math.abs(center[i] - Math.round(center[i])) > 1e-9) return null;
        center[i] = Math.round(center[i]);
      }
      return center;
    };
    const neighborCellDirs = [
      [2, 0, 0], [-2, 0, 0],
      [0, 2, 0], [0, -2, 0],
      [0, 0, 2], [0, 0, -2]
    ];
    const facePocketInfo = (faceKey) => {
      const entry = state.frontier.get(faceKey);
      if (!entry) return { score: 0, weight: 0 };
      const normal = axisNormalForFace(entry.ordered_verts);
      const center = faceCenter(entry.ordered_verts);
      if (!normal || !center) return { score: 0, weight: 0 };
      const plus = vecAdd(center, normal);
      const minus = vecSub(center, normal);
      const plusWeight = latticeGet(plus);
      const minusWeight = latticeGet(minus);
      const outsideDir = plusWeight <= minusWeight ? normal : vecNeg(normal);
      const outside = vecAdd(center, outsideDir);
      const insideStep = vecNeg(outsideDir).map(n => n * 2);
      let score = 0;
      let weight = 0;
      for (const dir of neighborCellDirs) {
        if (vecEq(dir, insideStep)) continue;
        const neighborWeight = latticeGet(vecAdd(outside, dir));
        if (neighborWeight > 0) {
          score += 1;
          weight += Math.min(MAX_SOLID_ANGLE, neighborWeight) / MAX_SOLID_ANGLE;
        }
      }
      return { score, weight, outside };
    };
    const reflectedFeatureKey = (feature, centerSums, axes) => {
      const center = feature.center.slice();
      const normal = feature.normal.slice();
      for (const axis of axes) {
        center[axis] = centerSums[axis] - center[axis];
        normal[axis] = -normal[axis];
      }
      return `${center.join(",")}::${normal.join(",")}`;
    };
    const frontierSymmetryInfo = () => {
      const features = [];
      const mins = [Infinity, Infinity, Infinity];
      const maxs = [-Infinity, -Infinity, -Infinity];
      for (const entry of state.frontier.values()) {
        const center = faceCenter(entry.ordered_verts);
        if (!center) continue;
        const normal = axisNormalForFace(entry.ordered_verts);
        if (!normal) continue;
        const pocket = facePocketInfo(keyFace(entry.ordered_verts));
        const feature = { center, normal: pocket.outside ? vecSub(pocket.outside, center) : normal };
        features.push(feature);
        for (let i = 0; i < 3; i++) {
          mins[i] = Math.min(mins[i], center[i]);
          maxs[i] = Math.max(maxs[i], center[i]);
        }
      }
      if (!features.length) return { score: 0, best_ratio: 0, average_ratio: 0, balance: 0, face_count: 0 };
      const centerSums = mins.map((min, i) => min + maxs[i]);
      const keys = new Set(features.map(feature => `${feature.center.join(",")}::${feature.normal.join(",")}`));
      const transforms = [[0], [1], [2], [0, 1, 2]];
      const ratios = transforms.map(axes => {
        let paired = 0;
        for (const feature of features) {
          if (keys.has(reflectedFeatureKey(feature, centerSums, axes))) paired += 1;
        }
        return paired / features.length;
      });
      const spans = maxs.map((max, i) => max - mins[i]);
      const maxSpan = Math.max(...spans, 1);
      const minSpan = Math.min(...spans);
      const balance = minSpan / maxSpan;
      const bestRatio = Math.max(...ratios);
      const averageRatio = ratios.reduce((sum, value) => sum + value, 0) / ratios.length;
      return {
        score: bestRatio + 0.25 * averageRatio + 0.1 * balance,
        best_ratio: bestRatio,
        average_ratio: averageRatio,
        balance,
        face_count: features.length
      };
    };
    const previewMoveStats = (move) => {
      const rb = applyMove(move, { countWork: false });
      const stats = calculateFrontierStats();
      undoMove(move, rb, { captureBest: false });
      return stats;
    };
    const previewMoveSymmetry = (move) => {
      if (move._symmetry_info) return move._symmetry_info;
      const rb = applyMove(move, { countWork: false });
      const info = frontierSymmetryInfo();
      undoMove(move, rb, { captureBest: false });
      move._symmetry_info = info;
      return info;
    };
    const moveAgentFeatures = (move, option = null) => {
      if (!option && move._agent_features && move._agent_features_version === stateVersion) return move._agent_features;
      const growthShape = prospectiveGrowthShape(move);
      const features = {
        coverage: moveCoverage(move),
        root_corona_faces: coveredFrontierFaceScore(move, 0),
        frontier_faces: coveredFrontierFaceScore(move),
        isohedral_corona: isohedralCoronaScore(move),
        pair_periodic: pairPeriodicContinuation(move),
        vector_repeat: vectorRepeatScore(move),
        periodic_continuation: periodicContinuation(move),
        parallelogram_completion: parallelogramCompletionScore(move),
        periodic_rank_gain: periodicRankGain(move),
        periodic_rank: periodicTranslationRank(),
        growth_axis_rank: growthShape.axis_rank,
        growth_isotropy: growthShape.axis_isotropy,
        growth_planarity: growthShape.axis_planarity,
        growth_max_span: growthShape.max_span,
        same_root_orientation: sameRootOrientation(move),
        ...moveLayerLagInfo(move),
        mrv_width: option?.unique_candidates?.length ?? option?.candidate_keys?.length ?? Infinity
      };
      features.periodic_evidence =
        features.pair_periodic
        + features.parallelogram_completion;
      features.linear_repeat = features.vector_repeat + features.periodic_continuation;
      features.isohedral_evidence = features.isohedral_corona;
      features.orientation_diversity = features.same_root_orientation ? 0 : 1;
      if (!option) {
        move._agent_features = features;
        move._agent_features_version = stateVersion;
      }
      return features;
    };
    const proposalFeatureValue = (feature, move) => {
      const growth = () => prospectiveGrowthShape(move);
      if (feature === "coverage") return moveCoverage(move);
      if (feature === "oldest_layer_completion") return minimumLayerCompletionScore(move) / 1e6;
      if (feature === "growth_axis_rank") return growth().axis_rank;
      if (feature === "growth_isotropy") return growth().axis_isotropy;
      if (feature === "growth_planarity") return growth().axis_planarity;
      if (feature === "growth_compactness") return -growth().max_span;
      if (feature === "same_orientation") return sameRootOrientation(move);
      if (feature === "root_corona") return coveredFrontierFaceScore(move, 0);
      if (feature === "isohedral_reuse") return isohedralCoronaScore(move);
      if (feature === "vector_repeat") return vectorRepeatScore(move);
      if (feature === "pair_periodic") return pairPeriodicContinuation(move);
      if (feature === "periodic_continuation") return periodicContinuation(move);
      if (feature === "parallelogram_completion") return parallelogramCompletionScore(move);
      if (feature === "frontier_reduction") {
        const current = calculateFrontierStats();
        const preview = move._preview_stats ?? (move._preview_stats = previewMoveStats(move));
        return (current.point_count ?? current.count ?? 0) - (preview.point_count ?? preview.count ?? 0);
      }
      return 0;
    };
    const proposalScore = (move) => {
      if (!proposalProgram) return 0;
      const sequence = proposalProgram.sequence?.length
        ? proposalProgram.sequence
        : [proposalProgram];
      const stepIndex = Math.max(0, state.placements.length - 1) % sequence.length;
      const step = sequence[stepIndex];
      let score = 0;
      for (const feature of step.active_features) {
        score += step.weights[feature] * proposalFeatureValue(feature, move);
      }
      move._proposal_step_index = stepIndex;
      searchStats.proposal_sequence_steps_used = Math.max(
        searchStats.proposal_sequence_steps_used,
        stepIndex + 1
      );
      return score;
    };
    const rlAgent = (() => {
      const values = new Map();
      const tagsFor = (features) => {
        const tags = [];
        if (features.periodic_evidence > 0) tags.push("periodic");
        if (features.isohedral_corona > 0) tags.push("isohedral-reuse");
        if (features.root_corona_faces > 0) tags.push("root-corona");
        if (features.same_root_orientation > 0) tags.push("same-orientation");
        if (!tags.length) tags.push("fallback");
        return tags;
      };
      const learnedValue = (features) =>
        tagsFor(features).reduce((sum, tag) => sum + (values.get(tag)?.value ?? 0), 0);
      return {
        score(move, option = null) {
          const features = moveAgentFeatures(move, option);
          const learned = learnedValue(features);
          // Lexicographic priority: try full-rank periodic evidence first, then
          // build/reuse an isohedral corona. Same-direction vector repetition is
          // useful, but it is deliberately weaker so the agent does not merely
          // grow an infinite one-dimensional stack.
          return [
            features.periodic_rank_gain,
            features.growth_axis_rank,
            features.growth_isotropy,
            features.growth_planarity,
            -features.growth_max_span,
            features.periodic_evidence > 0 ? 1 : 0,
            features.periodic_evidence,
            features.isohedral_evidence > 0 ? 1 : 0,
            features.isohedral_evidence,
            features.orientation_diversity,
            features.root_corona_faces,
            features.frontier_faces,
            learned,
            features.coverage,
            features.linear_repeat * 0.1,
            Number.isFinite(features.mrv_width) ? -features.mrv_width : -1e9
          ];
        },
        observe(move, success) {
          const features = move._agent_proposal_features ?? moveAgentFeatures(move);
          const reward = success ? 1 : -0.2;
          for (const tag of tagsFor(features)) {
            const current = values.get(tag) ?? { value: 0, count: 0 };
            current.count += 1;
            current.value += (reward - current.value) / current.count;
            values.set(tag, current);
          }
        }
      };
    })();
    const moveScore = (move) => {
      const coverage = moveCoverage(move);
      const repeat = () => sameRootOrientation(move);
      const periodic = () => periodicContinuation(move);
      const pairPeriodic = () => pairPeriodicContinuation(move);
      const vectorRepeat = () => vectorRepeatScore(move);
      const parallelogram = () => parallelogramCompletionScore(move);
      if (moveOrder === "no_brainer") {
        const growth = prospectiveGrowthShape(move);
        return [
          minimumLayerCompletionScore(move),
          coverage,
          growth.axis_rank,
          growth.axis_isotropy,
          growth.axis_planarity,
          -growth.max_span
        ];
      }
      if (moveOrder === "proposal") return [proposalScore(move)];
      if (moveOrder === "global") return rlAgent.score(move);
      if (moveOrder === "shell") {
        const growth = prospectiveGrowthShape(move);
        return [
          minimumShellCompletionScore(move),
          growth.axis_rank,
          growth.axis_isotropy,
          growth.axis_planarity,
          -growth.max_span,
          coverage
        ];
      }
      if (moveOrder === "symmetric") {
        const symmetry = previewMoveSymmetry(move);
        return [
          symmetry.score,
          symmetry.best_ratio,
          symmetry.balance,
          periodic(),
          repeat(),
          coverage
        ];
      }
      if (moveOrder === "crystal") {
        return [
          periodicRankGain(move),
          parallelogram(),
          vectorRepeat(),
          pairPeriodic(),
          periodic(),
          repeat(),
          coverage
        ];
      }
      if (moveOrder === "isohedral") {
        const growth = prospectiveGrowthShape(move);
        return [
          minimumLayerCompletionScore(move),
          growth.axis_rank,
          growth.axis_isotropy,
          growth.axis_planarity,
          -growth.max_span,
          reflectedOwnerMatchScore(move),
          isohedralCoronaScore(move),
          pairPeriodic(),
          vectorRepeat(),
          periodic(),
          repeat(),
          coverage
        ];
      }
      if (usePolicyAgent) return rlAgent.score(move);
      if (moveOrder === "periodic") return [periodic(), repeat(), coverage];
      if (moveOrder === "repeat") return [repeat(), coverage];
      if (moveOrder === "layer" || moveOrder === "balanced") {
        if (!move._preview_stats) move._preview_stats = previewMoveStats(move);
        const stats = move._preview_stats;
        const symmetry = moveOrder === "balanced" ? previewMoveSymmetry(move) : null;
        return [
          stats.min_gen,
          -stats.count,
          -(stats.point_count ?? stats.count ?? 0),
          moveOrder === "balanced" ? symmetry.score : 0,
          moveOrder === "balanced" ? symmetry.best_ratio : 0,
          moveOrder === "balanced" ? repeat() : 0,
          moveOrder === "balanced" ? pairPeriodic() : 0,
          moveOrder === "balanced" ? periodic() : 0,
          coverage
        ];
      }
      return [coverage, repeat()];
    };
    const compareMoves = (a, b) => {
      const as = moveScore(a);
      const bs = moveScore(b);
      for (let i = 0; i < Math.max(as.length, bs.length); i++) {
        const diff = (bs[i] ?? 0) - (as[i] ?? 0);
        if (diff) return diff;
      }
      if (seededTieBreaks) {
        return seededTieValue(b.dedup_key ?? placementGeometryKey(b))
          - seededTieValue(a.dedup_key ?? placementGeometryKey(a));
      }
      if (moveOrder === "no_brainer" || moveOrder === "proposal") {
        if (!Number.isFinite(a._random_tie)) a._random_tie = nextRandom();
        if (!Number.isFinite(b._random_tie)) b._random_tie = nextRandom();
        return b._random_tie - a._random_tie;
      }
      return 0;
    };
    const isBetterScore = (candidate, current) => {
      if (!current) return true;
      for (let i = 0; i < Math.max(candidate.length, current.length); i++) {
        const diff = (candidate[i] ?? 0) - (current[i] ?? 0);
        if (diff) return diff > 0;
      }
      return false;
    };
    const describeMove = (move) => branchDetails ? {
      prototile_idx: move.prototile_idx,
      translation: move.translation,
      coverage: moveCoverage(move),
      same_root_orientation: sameRootOrientation(move),
      periodic_continuation: periodicContinuation(move),
      pair_periodic_continuation: pairPeriodicContinuation(move),
      vector_repeat: vectorRepeatScore(move),
      isohedral_corona: isohedralCoronaScore(move),
      agent_features: usePolicyAgent ? moveAgentFeatures(move) : null,
      agent_score: usePolicyAgent ? rlAgent.score(move) : null,
      parallelogram_completion: parallelogramCompletionScore(move),
      target_face_pocket: move._target_face_pocket ?? null,
      symmetry: move._symmetry_info ?? null,
      periodic_template: move._periodic_template ?? null,
      periodic_cell: move._periodic_cell ?? null,
      layer: Number.isFinite(move.layer) ? move.layer : candidateMoveLayer(move),
      layer_lag: moveLayerLagInfo(move),
      score: moveScore(move),
      preview_frontier_stats: move._preview_stats ?? null
    } : {};
    const compareScoreVectors = (a, b) => {
      for (let i = 0; i < Math.max(a.length, b.length); i++) {
        const diff = (b[i] ?? 0) - (a[i] ?? 0);
        if (diff) return diff;
      }
      return 0;
    };
    const policyAgentProposals = (analysis) => {
      if (!usePolicyAgent) return [];
      const dedup = new Map();
      for (const option of analysis?.branches ?? []) {
        const moves = option.unique_candidates ?? [];
        for (const candidate of moves) {
          const move = {
            ...candidate,
            translation: candidate.translation?.slice() ?? [0, 0, 0],
            occupancy_data: candidate.occupancy_data
          };
          const features = moveAgentFeatures(move, option);
          if (!moveWithinGenerationBand(move)) {
            searchStats.generation_band_deferrals += 1;
            continue;
          }
          const score = rlAgent.score(move, option);
          move._agent_proposal_features = features;
          move._agent_proposal_score = score;
          move._agent_source_point_key = option.point_key;
          const key = move.dedup_key ?? placementGeometryKey(move);
          const current = dedup.get(key);
          if (!current || compareScoreVectors(score, current.score) < 0) dedup.set(key, { move, score });
        }
      }
      const proposals = [...dedup.values()]
        .sort((left, right) => compareScoreVectors(left.score, right.score));
      return (Number.isFinite(agentBranchCap) ? proposals.slice(0, agentBranchCap) : proposals)
        .map(item => item.move);
    };
    const preflightEnabled = config.template_preflight !== false;
    // An exact quotient certificate is a proof, not a search heuristic. Use it
    // ahead of every move-order policy unless a diagnostic explicitly disables
    // periodic preflight. Ordinary frontier search handles uncertified systems.
    const periodicPreflightEnabled = preflightEnabled
      && config.periodic_preflight !== false
      && (tilingStrategy === "auto" || tilingStrategy === "translational");
    const isohedralPreflightEnabled = preflightEnabled
      && (tilingStrategy === "auto" || tilingStrategy === "isohedral");
    let tilingEvidence = null;

    const vectorCoordinatesInBasis = (vector, basis) => {
      const determinant = determinant3(basis);
      if (Math.abs(determinant) <= 1e-9) return null;
      return [
        determinant3([vector, basis[1], basis[2]]) / determinant,
        determinant3([basis[0], vector, basis[2]]) / determinant,
        determinant3([basis[0], basis[1], vector]) / determinant
      ];
    };
    const vectorIsInBasisLattice = (vector, basis) => {
      const coordinates = vectorCoordinatesInBasis(vector, basis);
      return coordinates?.every(value => Math.abs(value - Math.round(value)) <= 1e-9) ?? false;
    };
    const translatedReverseFaceVector = (source, target) => {
      if (source.length !== target.length || source.length < 3) return null;
      for (const targetVertex of target) {
        const translation = vecSub(targetVertex, source[0]);
        if (translation.every(value => value === 0)) continue;
        if (translatedReverseFaceMatches(source, target, translation)) return translation;
      }
      return null;
    };
    const motifFromCurrentPatch = () => {
      const rootTranslation = state.placements[0].translation;
      return state.placements.map(placement => {
        const tile = prototiles[placement.prototile_idx];
        const orientationIndex = tile.unique_orientations.indexOf(placement.orient);
        return {
          prototile_idx: placement.prototile_idx,
          orientation_index: orientationIndex,
          orientation_id: placement.orient.__orientation_id ?? null,
          translation: vecSub(placement.translation, rootTranslation)
        };
      });
    };
    const periodicTranslationNeighborhoodIsValid = (
      basis,
      motifPlacements = state.placements,
      budgetExceeded = () => false
    ) => {
      const vertices = motifPlacements.flatMap(globalPlacementVertices);
      if (!vertices.length) return false;
      const minima = [0, 1, 2].map(axis => Math.min(...vertices.map(vertex => vertex[axis])));
      const maxima = [0, 1, 2].map(axis => Math.max(...vertices.map(vertex => vertex[axis])));
      const spans = maxima.map((value, axis) => value - minima[axis]);
      const determinant = determinant3(basis);
      if (Math.abs(determinant) < 1e-12) return false;
      const reciprocalNumerators = [
        vecCross(basis[1], basis[2]),
        vecCross(basis[2], basis[0]),
        vecCross(basis[0], basis[1])
      ];
      // If two motif cells overlap, their relative translation lies inside the
      // motif bounding-box difference. Cramer's rule therefore gives a finite,
      // complete coefficient box for every lattice shift which can overlap.
      const radii = reciprocalNumerators.map(vector => Math.ceil(
        vector.reduce((sum, value, axis) => sum + Math.abs(value) * spans[axis], 0)
        / Math.abs(determinant)
      ));
      const localLattice = new Map();
      const localFrontier = new Map();
      const localPlacementKeys = new Set();
      const localConvexPlacements = [];
      const addPlacement = (placement, shift) => {
        const translation = vecAdd(placement.translation, shift);
        const placementKey = `${placement.prototile_idx}::${placement.orient.__orientation_id ?? ""}::${vecKey(translation)}`;
        if (localPlacementKeys.has(placementKey)) {
          searchStats.periodic_neighborhood_last_rejection = "duplicate_periodic_placement";
          return false;
        }
        localPlacementKeys.add(placementKey);
        const translatedPlacement = { ...placement, translation };
        if (!allSystemTilesAreConvexPolyhedra) {
          for (const point of placement.orient.occupancy) {
            const position = add3(point.pos, translation);
            const key = vecKey(position);
            const weight = (localLattice.get(key) ?? 0) + point.weight;
            if (weight > MAX_SOLID_ANGLE + SOLID_ANGLE_EPSILON) {
              searchStats.periodic_neighborhood_last_rejection = "discrete_occupancy_overlap";
              return false;
            }
            localLattice.set(key, weight);
          }
        } else {
          for (const existing of localConvexPlacements) {
            if (convexPlacementInteriorsOverlap(existing, translatedPlacement)) {
              searchStats.periodic_neighborhood_last_rejection = "convex_interior_overlap";
              return false;
            }
          }
          localConvexPlacements.push(translatedPlacement);
        }
        for (let faceIndex = 0; faceIndex < placement.orient.faces.length; faceIndex += 1) {
          const face = placement.orient.faces[faceIndex];
          const key = translatedOrientedFaceKey(placement.orient, faceIndex, translation);
          const orderedVertices = face.map(index => add3(placement.orient.verts[index], translation));
          const existing = localFrontier.get(key);
          if (!existing) {
            localFrontier.set(key, orderedVertices);
            continue;
          }
          if (!isCyclicPermutation(orderedVertices, [...existing].reverse())) {
            searchStats.periodic_neighborhood_last_rejection = "face_orientation_overlap";
            return false;
          }
          localFrontier.delete(key);
        }
        return true;
      };
      for (let a = -radii[0]; a <= radii[0]; a++) {
        for (let b = -radii[1]; b <= radii[1]; b++) {
          for (let c = -radii[2]; c <= radii[2]; c++) {
            if (a === 0 && b === 0 && c === 0) continue;
            if (budgetExceeded()) return false;
            const shift = [0, 1, 2].map(axis =>
              a * basis[0][axis] + b * basis[1][axis] + c * basis[2][axis]
            );
            if (shift.some((value, axis) => Math.abs(value) > spans[axis] + 1e-9)) continue;
            for (const placement of motifPlacements) if (!addPlacement(placement, shift)) return false;
          }
        }
      }
      for (const placement of motifPlacements) {
        if (!addPlacement(placement, [0, 0, 0])) return false;
      }
      searchStats.periodic_neighborhood_last_rejection = null;
      searchStats.periodic_neighborhood_last_rejection_detail = null;
      return true;
    };
    const findBoundaryPeriodicTemplate = (requestedPeriod, options = {}) => {
      if (state.placements.length !== requestedPeriod || !state.frontier.size) return null;
      const certificateBudgetExceeded = options.budget_exceeded ?? overBudget;
      const recordCertificateBudgetExceeded = options.on_budget_exceeded ?? noteIncompleteSearch;
      const stopForCertificateBudget = () => {
        if (!certificateBudgetExceeded()) return false;
        recordCertificateBudgetExceeded();
        return true;
      };
      const requireAllTypes = prototiles.length > 1 && config.periodic_require_all_types !== false;
      const usedTypes = new Set(state.placements.map(placement => placement.prototile_idx));
      if (requireAllTypes && usedTypes.size !== prototiles.length) return null;

      const boundaryFaces = [...state.frontier.values()].map((entry, index) => ({
        index,
        vertices: entry.ordered_verts,
        signature: faceSignatureUndirected(entry.ordered_verts)
      }));
      const faceTranslations = Array.from({ length: boundaryFaces.length }, () => []);
      const uniqueVectors = new Map();
      let facePairChecks = 0;
      for (let left = 0; left < boundaryFaces.length; left++) {
        for (let right = left + 1; right < boundaryFaces.length; right++) {
          facePairChecks += 1;
          if ((facePairChecks & 255) === 0 && stopForCertificateBudget()) return null;
          if (boundaryFaces[left].signature !== boundaryFaces[right].signature) continue;
          const translation = translatedReverseFaceVector(
            boundaryFaces[left].vertices,
            boundaryFaces[right].vertices
          );
          if (!translation || !translation.every(Number.isInteger)) continue;
          const reverse = translation.map(value => -value);
          faceTranslations[left].push({ face: right, vector: translation });
          faceTranslations[right].push({ face: left, vector: reverse });
          uniqueVectors.set(vecKey(translation), translation);
          uniqueVectors.set(vecKey(reverse), reverse);
        }
      }
      if (faceTranslations.some(options => options.length === 0)) return null;

      const motifVolume = state.placements.reduce(
        (sum, placement) => sum + (tileVolumes[placement.prototile_idx] ?? 0),
        0
      );
      const tolerance = 1e-8 * Math.max(1, motifVolume);
      const vectors = [...uniqueVectors.values()]
        .sort((left, right) =>
          left.reduce((sum, value) => sum + value * value, 0)
          - right.reduce((sum, value) => sum + value * value, 0)
          || vecKey(left).localeCompare(vecKey(right))
        );
      for (let first = 0; first < vectors.length; first++) {
        for (let second = first + 1; second < vectors.length; second++) {
          for (let third = second + 1; third < vectors.length; third++) {
            if (stopForCertificateBudget()) return null;
            const basis = [vectors[first], vectors[second], vectors[third]];
            const determinant = determinant3(basis);
            if (Math.abs(Math.abs(determinant) - motifVolume) > tolerance) continue;
            if (basis.some(vector => prototiles.some(tile =>
              tile.is_polycube && !isPolycubeTranslationVector(tile, vector)
            ))) continue;
            const allowedMatches = faceTranslations.map(options => options.filter(option =>
              vectorIsInBasisLattice(option.vector, basis)
            ));
            if (allowedMatches.some(options => options.length === 0)) continue;
            const matchBoundary = (remaining, chosen) => {
              if (stopForCertificateBudget()) return null;
              if (!remaining.size) return chosen;
              let pivot = null;
              let pivotOptions = null;
              for (const faceIndex of remaining) {
                const options = allowedMatches[faceIndex].filter(option => remaining.has(option.face));
                if (!options.length) return null;
                if (!pivotOptions || options.length < pivotOptions.length) {
                  pivot = faceIndex;
                  pivotOptions = options;
                }
              }
              for (const option of pivotOptions) {
                const next = new Set(remaining);
                next.delete(pivot);
                next.delete(option.face);
                const result = matchBoundary(next, [...chosen, {
                  source_face: pivot,
                  target_face: option.face,
                  translation: option.vector.slice(),
                  lattice_coordinates: vectorCoordinatesInBasis(option.vector, basis).map(Math.round)
                }]);
                if (result) return result;
              }
              return null;
            };
            const boundaryPairing = matchBoundary(
              new Set(boundaryFaces.map((_, index) => index)),
              []
            );
            if (!boundaryPairing) continue;
            if (!periodicTranslationNeighborhoodIsValid(
              basis,
              state.placements,
              stopForCertificateBudget
            )) continue;

            const motif = motifFromCurrentPatch();
            if (motif.some(item => item.orientation_index < 0)) return null;
            const prototileCounts = new Map();
            for (const item of motif) {
              prototileCounts.set(item.prototile_idx, (prototileCounts.get(item.prototile_idx) ?? 0) + 1);
            }
            return {
              kind: requestedPeriod === 1
                ? "one_tile_boundary_quotient"
                : `${requestedPeriod}_tile_boundary_quotient`,
              tile_volume: motifVolume / requestedPeriod,
              tile_volumes: tileVolumes.slice(),
              cell_volume: Math.abs(determinant),
              period_vectors: basis.map(vector => vector.slice()),
              motif,
              mixed_prototile: prototileCounts.size > 1,
              prototile_counts: [...prototileCounts.entries()]
                .sort((left, right) => left[0] - right[0])
                .map(([prototile_idx, count]) => ({ prototile_idx, count })),
              proof: {
                method: "face_paired_boundary_equal_covolume",
                overlap_validation: "complete_lattice_translation_neighborhood",
                boundary_face_count: boundaryFaces.length,
                boundary_pairing: boundaryPairing,
                motif_volume: motifVolume,
                lattice_determinant: Math.abs(determinant)
              }
            };
          }
        }
      }
      return null;
    };
    const periodicPatchStateKey = () => canonicalLatticePatchStateKey(state.placements);
    const periodicMotifCandidates = () => {
      const candidates = new Map();
      for (const moves of faceCandidatesByFrontierPoint().values()) {
        for (const move of moves) candidates.set(move.dedup_key ?? placementGeometryKey(move), move);
      }
      return [...candidates.values()].sort(compareMoves);
    };
    const findPeriodicMotifByBoundarySearch = requestedPeriod => {
      if (requestedPeriod < state.placements.length) return null;
      const seenBySize = Array.from({ length: requestedPeriod + 1 }, () => new Set());
      const configuredNodeLimit = Number(config.periodic_motif_node_limit);
      const nodeLimit = Number.isFinite(configuredNodeLimit) && configuredNodeLimit > 0
        ? Math.floor(configuredNodeLimit)
        : Infinity;
      let localNodes = 0;
      const visit = () => {
        if (overBudget() || localNodes >= nodeLimit) {
          noteIncompleteSearch();
          return null;
        }
        localNodes += 1;
        searchStats.periodic_motif_nodes += 1;
        const size = state.placements.length;
        const stateKey = periodicPatchStateKey();
        if (seenBySize[size].has(stateKey)) return null;
        seenBySize[size].add(stateKey);
        searchStats.periodic_motif_states += 1;
        if (size === requestedPeriod) return findBoundaryPeriodicTemplate(requestedPeriod);

        for (const move of periodicMotifCandidates()) {
          if (overBudget() || localNodes >= nodeLimit) {
            noteIncompleteSearch();
            return null;
          }
          const validity = checkMoveViability(move);
          if (!validity) continue;
          move.occupancy_data = validity.occData;
          const rollback = applyMove(move);
          const template = visit();
          undoMove(move, rollback, { captureBest: false });
          if (template) return template;
        }
        return null;
      };
      return visit();
    };
    const vectorScaleAdd = (base, vector, scale) => [
      base[0] + vector[0] * scale,
      base[1] + vector[1] * scale,
      base[2] + vector[2] * scale
    ];
    const templateTranslation = (template, motif, cell) => {
      let translation = vecAdd(state.placements[0].translation, motif.translation);
      for (let axis = 0; axis < 3; axis++) translation = vectorScaleAdd(translation, template.period_vectors[axis], cell[axis]);
      return translation;
    };
    const templateMove = (template, motif, cell) => {
      const tile = prototiles[motif.prototile_idx];
      const orient = tile?.unique_orientations?.[motif.orientation_index];
      if (!tile || !orient) return null;
      const translation = templateTranslation(template, motif, cell);
      if (tile.is_polycube ? !isPolycubeMoveTranslation(tile, translation) : !translation.every(Number.isInteger)) return null;
      return {
        prototile_idx: motif.prototile_idx,
        orient,
        translation,
        _periodic_template: template,
        _periodic_cell: cell.slice()
      };
    };
    const periodicTemplateCells = (template) => {
      const countGoal = criterion === "count"
        ? targetVal
        : criterion === "region"
          ? Math.max(1, Math.ceil(targetRegion.volume / Math.max(1e-9, Math.min(...tileVolumes.filter(volume => volume > 0)))))
          : Math.max(24, targetVal * 24);
      const motifCount = Math.max(1, template.motif?.length ?? (+config.periodic_tile_count || 2));
      const requiredCells = Math.max(1, Math.ceil(countGoal / motifCount));
      const configuredRadius = Number(config.periodic_template_radius);
      const vectorLengths = template.period_vectors.map(vector =>
        Math.hypot(vector[0], vector[1], vector[2])
      );
      const [v0, v1, v2] = template.period_vectors;
      const periodMatrix = [
        [v0[0], v1[0], v2[0]],
        [v0[1], v1[1], v2[1]],
        [v0[2], v1[2], v2[2]]
      ];
      const determinant =
        periodMatrix[0][0] * (periodMatrix[1][1] * periodMatrix[2][2] - periodMatrix[1][2] * periodMatrix[2][1])
        - periodMatrix[0][1] * (periodMatrix[1][0] * periodMatrix[2][2] - periodMatrix[1][2] * periodMatrix[2][0])
        + periodMatrix[0][2] * (periodMatrix[1][0] * periodMatrix[2][1] - periodMatrix[1][1] * periodMatrix[2][0]);
      const inverse = [
        [
          (periodMatrix[1][1] * periodMatrix[2][2] - periodMatrix[1][2] * periodMatrix[2][1]) / determinant,
          (periodMatrix[0][2] * periodMatrix[2][1] - periodMatrix[0][1] * periodMatrix[2][2]) / determinant,
          (periodMatrix[0][1] * periodMatrix[1][2] - periodMatrix[0][2] * periodMatrix[1][1]) / determinant
        ],
        [
          (periodMatrix[1][2] * periodMatrix[2][0] - periodMatrix[1][0] * periodMatrix[2][2]) / determinant,
          (periodMatrix[0][0] * periodMatrix[2][2] - periodMatrix[0][2] * periodMatrix[2][0]) / determinant,
          (periodMatrix[0][2] * periodMatrix[1][0] - periodMatrix[0][0] * periodMatrix[1][2]) / determinant
        ],
        [
          (periodMatrix[1][0] * periodMatrix[2][1] - periodMatrix[1][1] * periodMatrix[2][0]) / determinant,
          (periodMatrix[0][1] * periodMatrix[2][0] - periodMatrix[0][0] * periodMatrix[2][1]) / determinant,
          (periodMatrix[0][0] * periodMatrix[1][1] - periodMatrix[0][1] * periodMatrix[1][0]) / determinant
        ]
      ];
      const desiredPhysicalHalfSpan = Math.cbrt(countGoal * template.tile_volume) / 2;
      const radii = inverse.map(row =>
        Math.max(1, Math.ceil(desiredPhysicalHalfSpan * row.reduce((sum, value) => sum + Math.abs(value), 0)))
      );
      if (Number.isFinite(configuredRadius) && configuredRadius > 0) {
        radii.fill(Math.floor(configuredRadius));
      } else {
        const targetCellBudget = Math.ceil(requiredCells * 1.5);
        const cellCount = () => radii.reduce((product, radius) => product * (2 * radius + 1), 1);
        while (cellCount() < targetCellBudget) {
          let shortestAxis = 0;
          for (let axis = 1; axis < 3; axis++) {
            const reach = (radii[axis] + 0.5) * vectorLengths[axis];
            const shortestReach = (radii[shortestAxis] + 0.5) * vectorLengths[shortestAxis];
            if (reach < shortestReach) shortestAxis = axis;
          }
          radii[shortestAxis] += 1;
        }
      }
      const cells = [];
      for (let a = -radii[0]; a <= radii[0]; a++) {
        for (let b = -radii[1]; b <= radii[1]; b++) {
          for (let c = -radii[2]; c <= radii[2]; c++) {
            cells.push([a, b, c]);
          }
        }
      }
      return cells.sort((left, right) =>
        (Math.abs(left[0]) + Math.abs(left[1]) + Math.abs(left[2])) -
        (Math.abs(right[0]) + Math.abs(right[1]) + Math.abs(right[2]))
        || left[0] - right[0]
        || left[1] - right[1]
        || left[2] - right[2]
      );
    };
    const preflightStatusPayload = (template = null) => ({
      frontier_stats: frontierStatsWithCandidateCount(),
      search_stats: searchStatsSnapshot(),
      periodic_template: template
    });
    const genericPeriodicCertificateEnabled = config.generic_periodic_certificate === true
      && criterion === "count"
      && tilingStrategy === "generic";
    const genericPeriodicCheckpointEnabled = genericPeriodicCertificateEnabled
      && config.generic_periodic_certificate_check_new_maximum === true;
    const genericPeriodicDistinctPatchMode = genericPeriodicCheckpointEnabled
      && config.generic_periodic_certificate_check_distinct_patches === true;
    searchStats.generic_periodic_certificate_distinct_patch_mode = genericPeriodicDistinctPatchMode;
    const configuredGenericPeriodicSamplingPolicy =
      config.generic_periodic_certificate_checkpoint_sampling_policy;
    const genericPeriodicSamplingPolicy = genericPeriodicDistinctPatchMode
      && ["spread", "hybrid"].includes(configuredGenericPeriodicSamplingPolicy)
      ? configuredGenericPeriodicSamplingPolicy
      : "prefix";
    const configuredGenericPeriodicSamplingStride = Number(
      config.generic_periodic_certificate_checkpoint_sampling_stride
    );
    const genericPeriodicSamplingStride = genericPeriodicSamplingPolicy === "spread"
      || genericPeriodicSamplingPolicy === "hybrid"
      ? Number.isFinite(configuredGenericPeriodicSamplingStride)
        ? Math.max(2, Math.floor(configuredGenericPeriodicSamplingStride))
        : 16
      : 1;
    const configuredGenericPeriodicMin = Number(config.generic_periodic_certificate_checkpoint_min_tiles);
    const genericPeriodicCheckpointMin = Number.isFinite(configuredGenericPeriodicMin)
      ? Math.max(1, Math.floor(configuredGenericPeriodicMin))
      : 2;
    const configuredGenericPeriodicMax = Number(config.generic_periodic_certificate_checkpoint_max_tiles);
    const genericPeriodicCheckpointMax = Number.isFinite(configuredGenericPeriodicMax)
      ? Math.max(genericPeriodicCheckpointMin, Math.floor(configuredGenericPeriodicMax))
      : targetVal;
    const configuredGenericPeriodicPerSizeCap = Number(
      config.generic_periodic_certificate_checkpoint_max_checks_per_size
    );
    const genericPeriodicPerSizeCap = Number.isFinite(configuredGenericPeriodicPerSizeCap)
      ? Math.max(1, Math.floor(configuredGenericPeriodicPerSizeCap))
      : 4;
    const configuredGenericPeriodicSamplingPrefix = Number(
      config.generic_periodic_certificate_checkpoint_sampling_prefix
    );
    const genericPeriodicSamplingPrefix = genericPeriodicSamplingPolicy === "hybrid"
      ? Number.isFinite(configuredGenericPeriodicSamplingPrefix)
        ? Math.max(1, Math.floor(configuredGenericPeriodicSamplingPrefix))
        : 4
      : genericPeriodicSamplingPolicy === "prefix"
        ? genericPeriodicPerSizeCap
        : 1;
    searchStats.generic_periodic_certificate_checkpoint_sampling_policy = genericPeriodicSamplingPolicy;
    searchStats.generic_periodic_certificate_checkpoint_sampling_stride = genericPeriodicSamplingStride;
    searchStats.generic_periodic_certificate_checkpoint_sampling_prefix = genericPeriodicSamplingPrefix;
    const configuredGenericPeriodicTotalCap = Number(
      config.generic_periodic_certificate_checkpoint_max_total_checks
    );
    const genericPeriodicTotalCap = Number.isFinite(configuredGenericPeriodicTotalCap)
      ? Math.max(1, Math.floor(configuredGenericPeriodicTotalCap))
      : 160;
    const configuredGenericPeriodicCheckpointTimeBudget = Number(
      config.generic_periodic_certificate_checkpoint_total_time_limit_ms
    );
    const genericPeriodicCheckpointTimeBudgetMs = Number.isFinite(configuredGenericPeriodicCheckpointTimeBudget)
      ? Math.max(1, configuredGenericPeriodicCheckpointTimeBudget)
      : 10000;
    const genericPeriodicSizesAttempted = new Set();
    const genericPeriodicStatesSeen = new Set();
    const genericPeriodicStatesAttempted = new Set();
    const genericPeriodicEligibleBySize = new Map();
    const genericPeriodicAttemptsBySize = new Map();
    let genericPeriodicCheckpointChecksAttempted = 0;
    let genericPeriodicCheckpointElapsedMs = 0;
    let genericPeriodicLargestSizeSeen = 0;
    async function* tryGenericPeriodicCertificate(source) {
      if (!genericPeriodicCertificateEnabled || tilingEvidence) return null;
      const patchSize = state.placements.length;
      let checkpointStateKey = null;
      if (source === "generic_growth_checkpoint") {
        if (
          !genericPeriodicCheckpointEnabled
          || patchSize < genericPeriodicCheckpointMin
          || patchSize > genericPeriodicCheckpointMax
        ) return null;
        if (!genericPeriodicDistinctPatchMode) {
          if (patchSize <= genericPeriodicLargestSizeSeen) return null;
          genericPeriodicLargestSizeSeen = patchSize;
        }
      }
      if (genericPeriodicDistinctPatchMode) {
        const stateKey = periodicPatchStateKey();
        checkpointStateKey = stateKey;
        if (source === "generic_growth_checkpoint" && genericPeriodicStatesSeen.has(stateKey)) {
          searchStats.generic_periodic_certificate_duplicate_states_skipped += 1;
          return null;
        }
        if (source !== "generic_growth_checkpoint" && genericPeriodicStatesAttempted.has(stateKey)) return null;
        if (source === "generic_growth_checkpoint") {
          genericPeriodicStatesSeen.add(stateKey);
          const eligibleOrdinal = (genericPeriodicEligibleBySize.get(patchSize) ?? 0) + 1;
          genericPeriodicEligibleBySize.set(patchSize, eligibleOrdinal);
          searchStats.generic_periodic_certificate_checkpoint_eligible_states += 1;
          const attemptsAtSize = genericPeriodicAttemptsBySize.get(patchSize) ?? 0;
          if (attemptsAtSize >= genericPeriodicPerSizeCap) {
            searchStats.generic_periodic_certificate_per_size_cap_skips += 1;
            return null;
          }
          const selectedByPrefix = eligibleOrdinal <= genericPeriodicSamplingPrefix;
          const selectedByStride = (eligibleOrdinal - 1) % genericPeriodicSamplingStride === 0;
          if (genericPeriodicSamplingPolicy !== "prefix" && !selectedByPrefix && !selectedByStride) {
            searchStats.generic_periodic_certificate_checkpoint_sampling_skips += 1;
            return null;
          }
          if (genericPeriodicCheckpointChecksAttempted >= genericPeriodicTotalCap) {
            searchStats.generic_periodic_certificate_total_cap_skips += 1;
            return null;
          }
          if (genericPeriodicCheckpointElapsedMs >= genericPeriodicCheckpointTimeBudgetMs) {
            searchStats.generic_periodic_certificate_checkpoint_time_budget_skips += 1;
            searchStats.generic_periodic_certificate_checkpoint_time_budget_exhausted = true;
            return null;
          }
          genericPeriodicAttemptsBySize.set(patchSize, attemptsAtSize + 1);
          genericPeriodicCheckpointChecksAttempted += 1;
        }
        genericPeriodicStatesAttempted.add(stateKey);
      } else {
        if (genericPeriodicSizesAttempted.has(patchSize)) return null;
        genericPeriodicSizesAttempted.add(patchSize);
      }

      searchStats.generic_periodic_certificate_attempted = true;
      searchStats.generic_periodic_certificate_patch_size = patchSize;
      searchStats.generic_periodic_certificate_checks_attempted += 1;
      searchStats.generic_periodic_certificate_check_sizes.push(patchSize);
      searchStats.generic_periodic_certificate_check_sources.push(source);
      const patchFingerprint = latticePatchFingerprint(checkpointStateKey ?? periodicPatchStateKey());
      const certificateStartedAt = performance.now();
      const configuredCertificateTimeLimit = Number(config.generic_periodic_certificate_time_limit_ms);
      const certificateTimeLimitMs = Number.isFinite(configuredCertificateTimeLimit)
        ? Math.max(1, configuredCertificateTimeLimit)
        : 2000;
      let certificateTimedOut = false;
      const certificateBudgetExceeded = () =>
        performance.now() - certificateStartedAt >= certificateTimeLimitMs;
      const noteCertificateTimeout = () => { certificateTimedOut = true; };
      const requestedCertificateMethod = config.generic_periodic_certificate_method;
      const certificateMethod = ["internal_first", "internal_only"].includes(requestedCertificateMethod)
        ? requestedCertificateMethod
        : "boundary_first";
      searchStats.generic_periodic_certificate_method = certificateMethod;
      const mineInternalTemplate = () => {
        searchStats.generic_periodic_internal_motif_attempted = true;
        const internalTemplate = minePeriodicTemplateFromCurrentPatch({
          budget_exceeded: certificateBudgetExceeded,
          on_budget_exceeded: noteCertificateTimeout,
          on_vectors: (count, translations) => {
            searchStats.generic_periodic_internal_motif_vector_count = Math.max(
              searchStats.generic_periodic_internal_motif_vector_count,
              count
            );
            searchStats.generic_periodic_internal_motif_max_translation_support = Math.max(
              searchStats.generic_periodic_internal_motif_max_translation_support,
              translations[0]?.support ?? 0
            );
            searchStats.generic_periodic_internal_motif_top_translations = translations;
          },
          on_basis: () => { searchStats.generic_periodic_internal_motif_bases_tested += 1; }
        });
        searchStats.generic_periodic_internal_motif_found = !!internalTemplate;
        return internalTemplate;
      };
      const findBoundaryTemplate = () => findBoundaryPeriodicTemplate(patchSize, {
        budget_exceeded: certificateBudgetExceeded,
        on_budget_exceeded: noteCertificateTimeout
      });
      let template = certificateMethod === "boundary_first"
        ? findBoundaryTemplate()
        : mineInternalTemplate();
      if (!template && !certificateBudgetExceeded()) {
        if (certificateMethod === "boundary_first") template = mineInternalTemplate();
        else if (certificateMethod === "internal_first") template = findBoundaryTemplate();
      }
      if (!template && certificateBudgetExceeded()) {
        noteCertificateTimeout();
      }
      const preciseElapsed = performance.now() - certificateStartedAt;
      const elapsed = Math.round(preciseElapsed);
      if (source === "generic_growth_checkpoint") genericPeriodicCheckpointElapsedMs += preciseElapsed;
      searchStats.generic_periodic_certificate_elapsed_ms = elapsed;
      searchStats.generic_periodic_certificate_total_elapsed_ms += elapsed;
      if (certificateTimedOut) searchStats.generic_periodic_certificate_checks_timed_out += 1;
      else searchStats.generic_periodic_certificate_checks_completed += 1;
      searchStats.generic_periodic_certificate_timed_out =
        searchStats.generic_periodic_certificate_checks_timed_out > 0;
      searchStats.generic_periodic_certificate_completed =
        searchStats.generic_periodic_certificate_checks_completed
        === searchStats.generic_periodic_certificate_checks_attempted;
      searchStats.generic_periodic_certificate_found = !!template;
      if (patchSize >= targetVal) {
        searchStats.generic_periodic_certificate_target_attempted = true;
        searchStats.generic_periodic_certificate_target_completed = !certificateTimedOut;
        searchStats.generic_periodic_certificate_target_timed_out = certificateTimedOut;
        searchStats.generic_periodic_certificate_target_found = !!template;
      }
      yield {
        type: "translational_check",
        source,
        patch_size: patchSize,
        patch_fingerprint: patchFingerprint,
        certified: !!template,
        check_completed: !certificateTimedOut,
        periodic_template: template,
        frontier_stats: frontierStatsWithCandidateCount(),
        search_stats: searchStatsSnapshot()
      };
      if (!template) return null;
      tilingEvidence = {
        kind: "translational_certificate",
        certified: true,
        can_tile: true,
        strategy: "generic",
        source: source === "generic_growth_checkpoint"
          ? "gcts_growth_checkpoint"
          : "gcts_target_patch",
        patch_size: template.motif.length,
        certificate_kind: template.kind,
        period_vectors: template.period_vectors.map(vector => vector.slice()),
        periodic_template: template
      };
      return template;
    }
    const certifiedPeriodicMoveViability = (candidate) => {
      // The quotient proof already establishes global non-overlap and exact
      // coverage for every translated motif placement. For finite growth we
      // therefore need only a shared frontier face to keep the selected patch
      // connected. Rechecking every occupied vertex and face for every member
      // of the radial selection window would redundantly re-prove the torus
      // certificate thousands of times.
      const { faceKeys } = candidate;
      const moveVolume = tileVolumes[candidate.move.prototile_idx] ?? 0;
      if (!moveFitsRegion(candidate.move.orient, candidate.move.translation)) return null;
      if (targetRegion && state.placed_volume + moveVolume > targetRegion.volume + 1e-8) return null;
      const sharesFrontierFace = faceKeys.some(faceKey => state.frontier.has(faceKey));
      return sharesFrontierFace ? { ok: true } : null;
    };
    const certifyConfiguredPeriodicTemplate = rawTemplate => {
      if (!rawTemplate?.motif?.length || !Array.isArray(rawTemplate.period_vectors)) return null;
      const placements = [];
      for (const descriptor of rawTemplate.motif) {
        const prototileIdx = descriptor.prototile_idx ?? 0;
        const tile = prototiles[prototileIdx];
        const orient = descriptor.orientation_id
          ? tile?.unique_orientations?.find(item => item.__orientation_id === descriptor.orientation_id)
          : tile?.unique_orientations?.[descriptor.orientation_index ?? 0];
        if (!tile || !orient || !Array.isArray(descriptor.translation)) return null;
        placements.push({
          prototile_idx: prototileIdx,
          orient,
          translation: vecAdd(startMove.translation, descriptor.translation)
        });
      }
      if (
        placements[0].prototile_idx !== startMove.prototile_idx
        || placements[0].orient !== startMove.orient
        || !vecEq(placements[0].translation, startMove.translation)
      ) return null;
      if (placements.length === 1) {
        const oneTileTemplate = findTranslationalPolyhedronTemplate();
        const configuredBasis = rawTemplate.period_vectors;
        if (oneTileTemplate
          && configuredBasis.every(vector => vectorIsInBasisLattice(vector, oneTileTemplate.period_vectors))
          && oneTileTemplate.period_vectors.every(vector => vectorIsInBasisLattice(vector, configuredBasis))) {
          return oneTileTemplate;
        }
      }
      return certifyPeriodicPlacementMotif(placements, rawTemplate.period_vectors);
    };
    async function* tryPeriodicTemplatePatch(parentId, { force = false } = {}) {
      if (!periodicPreflightEnabled || (!force && goalMet())) return false;
      let template = certifyConfiguredPeriodicTemplate(config.known_periodic_template);
      if (config.known_periodic_template) {
        yield {
          type: "translational_check",
          source: "configured_verified_template",
          patch_size: config.known_periodic_template.motif?.length ?? 0,
          certified: !!template,
          periodic_template: template,
          frontier_stats: frontierStatsWithCandidateCount(),
          search_stats: searchStatsSnapshot()
        };
      }
      const progressiveMax = Number(config.periodic_patch_max_tiles);
      const unbounded = !!config.periodic_patch_unbounded;
      const maximumPatchSize = unbounded
        ? Infinity
        : Number.isFinite(progressiveMax)
          ? Math.max(1, Math.floor(progressiveMax))
          : Math.max(1, Math.floor(+config.periodic_tile_count || 2));
      for (let patchSize = 1; !template && patchSize <= maximumPatchSize && !overBudget(); patchSize++) {
        yield nodeStatus(
          parentId,
          "working",
          `checking ${patchSize}-tile translational patch`,
          preflightStatusPayload()
        );
        template = findPeriodicTemplate(patchSize);
        if (!template) template = findPeriodicMotifByBoundarySearch(patchSize);
        yield {
          type: "translational_check",
          patch_size: patchSize,
          certified: !!template,
          periodic_template: template,
          frontier_stats: frontierStatsWithCandidateCount(),
          search_stats: searchStatsSnapshot()
        };
        if (template) break;
        await tick();
      }
      if (!template && overBudget()) noteIncompleteSearch();
      if (!template) return false;
      const motifBaseColorIds = [0];
      let availableBaseColors = Array.from(
        { length: Math.max(0, BASE_COLOR_PALETTE_SIZE - 1) },
        (_, index) => index + 1
      );
      for (let motifIndex = 1; motifIndex < template.motif.length; motifIndex++) {
        if (!availableBaseColors.length) {
          availableBaseColors = Array.from(
            { length: BASE_COLOR_PALETTE_SIZE },
            (_, index) => index
          );
        }
        const selectedIndex = Math.floor(nextRandom() * availableBaseColors.length);
        motifBaseColorIds.push(availableBaseColors.splice(selectedIndex, 1)[0]);
      }
      state.placements[0]._periodic_motif_index = 0;
      state.placements[0]._periodic_base_color_id = motifBaseColorIds[0];
      state.placements[0]._periodic_cell = [0, 0, 0];
      state.placements[0].color_id =
        TRANSLATIONAL_CELL_COLOR_OFFSET + motifBaseColorIds[0] * 8;
      for (const frontierEntry of state.frontier.values()) {
        frontierEntry.color_id = TRANSLATIONAL_CELL_COLOR_OFFSET;
      }
      for (const faceStack of state.viz_faces.values()) {
        for (const face of faceStack) {
          face.color = COLOR_PALETTE[TRANSLATIONAL_CELL_COLOR_OFFSET];
        }
      }
      tilingEvidence = {
        kind: "translational_certificate",
        certified: true,
        can_tile: true,
        strategy: "translational",
        patch_size: template.motif?.length ?? 1,
        certificate_kind: template.kind,
        period_vectors: template.period_vectors?.map(vector => vector.slice()) ?? [],
        periodic_template: template
      };
      const cells = periodicTemplateCells(template);
      const existing = new Set(state.placements.map(placement => placementGeometryKey(placement)));
      const candidatesByFace = new Map();
      const placedMotifsByCell = new Map([["0,0,0", 1]]);
      const motifTypeCounts = new Map(
        template.prototile_counts?.map(entry => [entry.prototile_idx, entry.count])
        ?? template.motif.map(item => [item.prototile_idx, 1])
      );
      const placedTypeCounts = new Map();
      for (const placement of state.placements) {
        placedTypeCounts.set(
          placement.prototile_idx,
          (placedTypeCounts.get(placement.prototile_idx) ?? 0) + 1
        );
      }
      const periodicCompositionScore = move => {
        const projectedTotal = state.placements.length + 1;
        let deviation = 0;
        for (const [prototileIndex, motifCount] of motifTypeCounts) {
          const expected = projectedTotal * motifCount / template.motif.length;
          const projected = (placedTypeCounts.get(prototileIndex) ?? 0)
            + (move.prototile_idx === prototileIndex ? 1 : 0);
          deviation += Math.abs(projected - expected);
        }
        return -deviation;
      };
      for (const cell of cells) {
        for (let motifIndex = 0; motifIndex < template.motif.length; motifIndex++) {
          if (cell[0] === 0 && cell[1] === 0 && cell[2] === 0 && motifIndex === 0) continue;
          const move = templateMove(template, template.motif[motifIndex], cell);
          if (!move) continue;
          move._periodic_motif_index = motifIndex;
          move._periodic_base_color_id = motifBaseColorIds[motifIndex];
          move._periodic_cell = cell.slice();
          const globalVertices = move.orient.verts.map(vertex => vecAdd(vertex, move.translation));
          const faceKeys = move.orient.faces.map(face =>
            keyFace(face.map(index => globalVertices[index]))
          );
          const candidate = {
            move,
            key: placementGeometryKey(move),
            cell,
            cell_key: cell.join(","),
            motif_index: motifIndex,
            faceKeys,
            radial_priority: template.period_vectors.reduce((offset, vector, axis) => [
              offset[0] + vector[0] * cell[axis],
              offset[1] + vector[1] * cell[axis],
              offset[2] + vector[2] * cell[axis]
            ], [0, 0, 0]).reduce((sum, coordinate) => sum + coordinate * coordinate, 0),
            queued: false,
            consumed: false
          };
          for (const faceKey of faceKeys) {
            if (!candidatesByFace.has(faceKey)) candidatesByFace.set(faceKey, []);
            candidatesByFace.get(faceKey).push(candidate);
          }
        }
      }
      const activeCandidates = [];
      const heapBefore = (left, right) =>
        left.radial_priority < right.radial_priority
        || (left.radial_priority === right.radial_priority && left.key < right.key);
      const heapPush = candidate => {
        candidate.queued = true;
        activeCandidates.push(candidate);
        let index = activeCandidates.length - 1;
        while (index > 0) {
          const parent = Math.floor((index - 1) / 2);
          if (!heapBefore(activeCandidates[index], activeCandidates[parent])) break;
          [activeCandidates[index], activeCandidates[parent]] = [activeCandidates[parent], activeCandidates[index]];
          index = parent;
        }
      };
      const heapPop = () => {
        if (!activeCandidates.length) return null;
        const first = activeCandidates[0];
        const last = activeCandidates.pop();
        if (activeCandidates.length) {
          activeCandidates[0] = last;
          let index = 0;
          while (true) {
            const left = index * 2 + 1;
            const right = left + 1;
            let best = index;
            if (left < activeCandidates.length && heapBefore(activeCandidates[left], activeCandidates[best])) best = left;
            if (right < activeCandidates.length && heapBefore(activeCandidates[right], activeCandidates[best])) best = right;
            if (best === index) break;
            [activeCandidates[index], activeCandidates[best]] = [activeCandidates[best], activeCandidates[index]];
            index = best;
          }
        }
        first.queued = false;
        return first;
      };
      const activateFaceNeighbors = faceKey => {
        for (const candidate of candidatesByFace.get(faceKey) ?? []) {
          if (!existing.has(candidate.key) && !candidate.queued && !candidate.consumed) heapPush(candidate);
        }
      };
      for (const faceKey of state.frontier.keys()) activateFaceNeighbors(faceKey);
      let applied = 0;
      const appliedMoves = [];
      const initialPeriodicBounds = placementGrowthBounds();
      const periodicGrowthBounds = {
        mins: initialPeriodicBounds.mins.slice(),
        maxs: initialPeriodicBounds.maxs.slice()
      };
      const periodicProspectiveGrowthShape = move => {
        const center = placementCenter(move);
        const spans = [0, 1, 2].map(axis =>
          Math.max(periodicGrowthBounds.maxs[axis], center[axis])
          - Math.min(periodicGrowthBounds.mins[axis], center[axis])
        ).sort((a, b) => a - b);
        const maxSpan = Math.max(spans[2], 1e-9);
        return {
          axis_rank: spans.filter(span => span > 1e-9).length,
          axis_isotropy: spans[0] / maxSpan,
          axis_planarity: spans[1] / maxSpan,
          max_span: spans[2]
        };
      };
      const configuredSelectionWindow = Number(config.periodic_selection_window);
      const periodicSelectionWindow = Number.isFinite(configuredSelectionWindow) && configuredSelectionWindow > 0
        ? Math.floor(configuredSelectionWindow)
        : 64;
      const periodicNodeId = nowId();
      yield branchSet(parentId, [{
        id: periodicNodeId,
        text: "certified forced growth",
        is_forced: true,
        frontier_stats: frontierStatsWithCandidateCount()
      }]);
      yield nodeStatus(periodicNodeId, "working", "periodic certificate", preflightStatusPayload(template));
      while (!goalMet() && state.placements.length < safetyMax) {
        if (stopToken.stop || overBudget()) {
          noteIncompleteSearch();
          break;
        }
        let best = null;
        let bestKey = null;
        let bestCandidate = null;
        let bestScore = null;
        let cappedRepeat = null;
        const retainedCandidates = [];
        while (activeCandidates.length && !best) {
          const candidateWindow = [];
          while (activeCandidates.length && candidateWindow.length < periodicSelectionWindow) {
            candidateWindow.push(heapPop());
          }
          for (const candidate of candidateWindow) {
            const { move, key, cell } = candidate;
            if (existing.has(key)) {
              candidate.consumed = true;
              continue;
            }
            const validity = certifiedPeriodicMoveViability(candidate);
            if (!validity) {
              candidate.consumed = true;
              continue;
            }
            const layerLag = criterion === "count"
              ? {
                  move_layer: Math.max(Math.abs(cell[0]), Math.abs(cell[1]), Math.abs(cell[2])),
                  min_frontier_layer: 0,
                  layer_lag: 0,
                  limit: forcedMoveLayerLagCap
                }
              : moveLayerLagInfo(move);
            move.layer = layerLag.move_layer;
            if (criterion !== "count" && Number.isFinite(forcedMoveLayerLagCap) && layerLag.layer_lag > forcedMoveLayerLagCap) {
              cappedRepeat ??= { move, layerLag };
              retainedCandidates.push(candidate);
              continue;
            }
            const growthShape = periodicProspectiveGrowthShape(move);
            const score = [
              periodicCompositionScore(move),
              periodicRankGain(move),
              growthShape.axis_rank,
              growthShape.axis_isotropy,
              growthShape.axis_planarity,
              -growthShape.max_span,
              placedMotifsByCell.has(candidate.cell_key) ? 1 : 0,
              // Grow a centered crystal in period-cell coordinates. Repeated
              // contacts are useful only after the nearest cell shell has
              // been preferred; otherwise a valid template can degenerate
              // into a fast one-dimensional tendril.
              -Math.max(Math.abs(cell[0]), Math.abs(cell[1]), Math.abs(cell[2])),
              -Math.abs(cell[0]) - Math.abs(cell[1]) - Math.abs(cell[2])
            ];
            if (isBetterScore(score, bestScore)) {
              best = move;
              bestKey = key;
              bestCandidate = candidate;
              bestScore = score;
            }
            retainedCandidates.push(candidate);
          }
          if (best) break;
        }
        for (const candidate of retainedCandidates) {
          if (candidate !== bestCandidate && !candidate.consumed && !candidate.queued) heapPush(candidate);
        }
        if (!best) {
          if (cappedRepeat) {
            searchStats.periodic_repeat_throttles += 1;
            yield nodeStatus(periodicNodeId, "working", "periodic cap", {
              ...preflightStatusPayload(template),
              forced_cap: {
                reason: "periodic-repeat-layer-lag",
                ...cappedRepeat.layerLag,
                released_branch_count: 0,
                released_singletons: false
              }
            });
          }
          break;
        }
        best.node_id = periodicNodeId;
        best.is_forced = true;
        best.occupancy_data = best.orient.occupancy.map(point => ({
          pos: vecAdd(point.pos, best.translation),
          weight: point.weight
        }));
        searchStats.forced_total += 1;
        const rollback = applyMove(best);
        const bestCenter = placementCenter(best);
        for (let axis = 0; axis < 3; axis++) {
          periodicGrowthBounds.mins[axis] = Math.min(periodicGrowthBounds.mins[axis], bestCenter[axis]);
          periodicGrowthBounds.maxs[axis] = Math.max(periodicGrowthBounds.maxs[axis], bestCenter[axis]);
        }
        existing.add(bestKey);
        bestCandidate.consumed = true;
        placedMotifsByCell.set(
          bestCandidate.cell_key,
          (placedMotifsByCell.get(bestCandidate.cell_key) ?? 0) + 1
        );
        placedTypeCounts.set(
          best.prototile_idx,
          (placedTypeCounts.get(best.prototile_idx) ?? 0) + 1
        );
        for (const faceKey of rollback.added ?? []) activateFaceNeighbors(faceKey);
        appliedMoves.push({ move: best, rollback });
        applied += 1;
        yield fastPlacementDelta(best, rollback, periodicNodeId);
        if (shouldSnapshot()) {
          yield snapshot(periodicNodeId);
          await tick();
        } else if (applied % 32 === 0) {
          yield nodeStatus(periodicNodeId, "working", `[${state.placements.length}] certified forced`);
        }
        await yieldToBrowser();
      }
      if (goalMet()) {
        yield nodeStatus(periodicNodeId, "success", `+ ${applied} certified forced`);
        return true;
      }
      while (appliedMoves.length) {
        const entry = appliedMoves.pop();
        undoMove(entry.move, entry.rollback);
        yield placementDelta("remove", entry.move, entry.rollback, periodicNodeId);
      }
      searchStats.forced_total = Math.max(0, searchStats.forced_total - applied);
      yield nodeStatus(periodicNodeId, "fail", "periodic preflight rolled back");
      return false;
    }
    const preflightFaceCandidatesForOption = async (option, maxCandidates = Infinity) => {
      const dedup = new Map();
      const localCandidateCap = Math.min(maxCandidates, candidateCap);
      for (const frontierEntry of state.frontier.values()) {
        if (!frontierEntryPointKeys(frontierEntry).has(option.pointKey)) continue;
        if (overBudget()) {
          noteIncompleteSearch();
          break;
        }
        const frontierVertices = frontierEntry.ordered_verts;
        const signature = faceSignatureUndirected(frontierVertices);
        for (const entry of orientedFacesBySignature.get(signature) ?? []) {
          if (overBudget()) {
            noteIncompleteSearch();
            return [...dedup.values()];
          }
          for (const anchor of entry.vertices) {
            const translation = vecSub(frontierVertices[0], anchor);
            if (entry.tile.is_polycube
              ? !isPolycubeMoveTranslation(entry.tile, translation)
              : !translation.every(Number.isInteger)) continue;
            if (!translatedReverseFaceMatches(entry.vertices, frontierVertices, translation)) continue;
            const move = { prototile_idx: entry.prototile_idx, translation, orient: entry.orient };
            const geometryKey = placementGeometryKey(move);
            if (dedup.has(geometryKey)) continue;
            const validity = checkMoveViability(move);
            if (!validity) continue;
            dedup.set(geometryKey, {
              ...move,
              occupancy_data: validity.occData,
              dedup_key: geometryKey,
              _source_point_key: option.pointKey
            });
            if (Number.isFinite(localCandidateCap) && dedup.size >= localCandidateCap) {
              return [...dedup.values()];
            }
          }
        }
        await yieldToBrowser();
      }
      return [...dedup.values()];
    };
    async function* tryIsohedralCoronaSeed(parentId) {
      if (!isohedralPreflightEnabled || goalMet()) return false;
      let activeParent = parentId;
      let applied = 0;
      const appliedMoves = [];
      const configuredMaxSteps = Number(config.isohedral_preflight_max_steps);
      const naturalMaxSteps = Math.min(
        safetyMax - state.placements.length,
        Math.max(
          1,
          criterion === "count"
            ? targetVal - state.placements.length
            : safetyMax - state.placements.length
        )
      );
      const maxSteps = Number.isFinite(configuredMaxSteps) && configuredMaxSteps >= 0
        ? Math.min(naturalMaxSteps, Math.floor(configuredMaxSteps))
        : naturalMaxSteps;
      while (!goalMet() && applied < maxSteps) {
        if (stopToken.stop || overBudget()) {
          noteIncompleteSearch();
          break;
        }
        const candidates = [];
        const seedCandidateLimit = Math.max(12, agentBranchCap * 3);
        for (const option of frontierPointOptions()) {
          const moves = await preflightFaceCandidatesForOption(
            option,
            seedCandidateLimit - candidates.length
          );
          for (const move of moves) {
            if (!moveWithinGenerationBand(move)) {
              searchStats.generation_band_deferrals += 1;
              continue;
            }
            const rootScore = coveredFrontierFaceScore(move, 0);
            if (
              rootScore <= 0
              && reflectedOwnerMatchScore(move) <= 0
              && isohedralCoronaScore(move) <= 0
            ) continue;
            move._isohedral_seed = true;
            candidates.push(move);
            if (candidates.length >= seedCandidateLimit) break;
          }
          if (candidates.length >= seedCandidateLimit) break;
        }
        if (!candidates.length) break;
        const isohedralSeedScore = move => {
          const growthShape = prospectiveGrowthShape(move);
          return [
            minimumLayerCompletionScore(move),
            coveredFrontierFaceScore(move, 0),
            growthShape.axis_rank,
            growthShape.axis_isotropy,
            growthShape.axis_planarity,
            -growthShape.max_span,
            reflectedOwnerMatchScore(move),
            isohedralCoronaScore(move),
            moveCoverage(move),
            sameRootOrientation(move)
          ];
        };
        candidates.sort((left, right) =>
          compareScoreVectors(isohedralSeedScore(left), isohedralSeedScore(right))
        );
        const move = candidates[0];
        const nodeId = nowId();
        move.node_id = nodeId;
        const payload = { id: nodeId, text: "isohedral corona", ...describeMove(move) };
        yield branchSet(activeParent, [payload]);
        const rollback = applyMove(move);
        appliedMoves.push({ move, rollback, nodeId });
        applied += 1;
        yield nodeStatus(nodeId, "success", `[${state.placements.length}] isohedral corona`, preflightStatusPayload());
        if (shouldSnapshot()) {
          yield snapshot(nodeId);
          await tick();
        } else {
          yield nodeSnapshot(nodeId);
        }
        activeParent = nodeId;
        await yieldToBrowser();
      }
      if (goalMet()) return true;
      if (tilingStrategy === "isohedral" && appliedMoves.length) {
        yield nodeStatus(activeParent, "working", `seeded ${applied} reusable neighborhood placements`, preflightStatusPayload());
        return false;
      }
      while (appliedMoves.length) {
        const entry = appliedMoves.pop();
        undoMove(entry.move, entry.rollback);
        yield nodeStatus(entry.nodeId, "fail", "isohedral preflight rolled back");
        yield placementDelta("remove", entry.move, entry.rollback, entry.nodeId);
      }
      return false;
    }

    const ISOHEDRAL_EPSILON = 1e-8;
    const isohedralRotations = (() => {
      const permutations = values => {
        if (values.length <= 1) return [values.slice()];
        const out = [];
        for (let index = 0; index < values.length; index++) {
          const rest = values.slice(0, index).concat(values.slice(index + 1));
          for (const suffix of permutations(rest)) out.push([values[index], ...suffix]);
        }
        return out;
      };
      const determinant = matrix =>
        matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
        - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
        + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0]);
      const rotations = [];
      for (const permutation of permutations([0, 1, 2])) {
        for (const sx of [-1, 1]) for (const sy of [-1, 1]) for (const sz of [-1, 1]) {
          const signs = [sx, sy, sz];
          const matrix = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
          for (let row = 0; row < 3; row++) matrix[row][permutation[row]] = signs[permutation[row]];
          const det = determinant(matrix);
          if (det === 1 || includeMirrors) rotations.push({ matrix, determinant: det });
        }
      }
      return rotations;
    })();
    const isohedralCoordinate = value => {
      const rounded = Math.round(value);
      if (Math.abs(value - rounded) <= ISOHEDRAL_EPSILON) return rounded;
      return Math.round(value / ISOHEDRAL_EPSILON) * ISOHEDRAL_EPSILON;
    };
    const isohedralPointKey = point => point.map(isohedralCoordinate).join(",");
    const isohedralVertexCloudKey = vertices =>
      vertices.map(isohedralPointKey).sort().join("|");
    const isohedralMatrixVector = (matrix, vector) => [
      matrix[0][0] * vector[0] + matrix[0][1] * vector[1] + matrix[0][2] * vector[2],
      matrix[1][0] * vector[0] + matrix[1][1] * vector[1] + matrix[1][2] * vector[2],
      matrix[2][0] * vector[0] + matrix[2][1] * vector[1] + matrix[2][2] * vector[2]
    ];
    const isohedralTransformPoint = (transform, point) =>
      vecAdd(isohedralMatrixVector(transform.rotation, point), transform.translation)
        .map(isohedralCoordinate);
    const isohedralTransformKey = transform =>
      `${transform.rotation.flat().join(",")}::${isohedralPointKey(transform.translation)}`;
    const globalPlacementVertices = placement =>
      placement.orient.verts.map(vertex => vecAdd(vertex, placement.translation));
    const isohedralOrientationMaps = prototiles.map(tile => {
      const orientations = new Map();
      for (const orient of tile.unique_orientations ?? []) {
        const mins = [0, 1, 2].map(axis => Math.min(...orient.verts.map(vertex => vertex[axis])));
        const normalized = orient.verts.map(vertex =>
          vertex.map((coordinate, axis) => isohedralCoordinate(coordinate - mins[axis]))
        );
        orientations.set(isohedralVertexCloudKey(normalized), orient);
      }
      return orientations;
    });
    const isohedralRootTransformsTo = placement => {
      const root = state.placements[0];
      if (!root) return [];
      const sourceVertices = globalPlacementVertices(root);
      const targetVertices = globalPlacementVertices(placement);
      const sourceCenter = [0, 1, 2].map(axis =>
        sourceVertices.reduce((sum, vertex) => sum + vertex[axis], 0) / sourceVertices.length
      );
      const targetCenter = [0, 1, 2].map(axis =>
        targetVertices.reduce((sum, vertex) => sum + vertex[axis], 0) / targetVertices.length
      );
      const targetKey = isohedralVertexCloudKey(targetVertices);
      const transforms = new Map();
      for (const { matrix: rotation, determinant } of isohedralRotations) {
        const rotatedCenter = isohedralMatrixVector(rotation, sourceCenter);
        const translation = targetCenter.map((coordinate, axis) =>
          isohedralCoordinate(coordinate - rotatedCenter[axis])
        );
        const transformedKey = isohedralVertexCloudKey(
          sourceVertices.map(vertex => isohedralTransformPoint({ rotation, translation }, vertex))
        );
        if (transformedKey !== targetKey) continue;
        const transform = {
          rotation: rotation.map(row => row.slice()),
          translation,
          determinant
        };
        transforms.set(isohedralTransformKey(transform), transform);
      }
      return [...transforms.values()];
    };
    const isohedralTransformPlacement = (placement, transform) => {
      const transformedVertices = globalPlacementVertices(placement)
        .map(vertex => isohedralTransformPoint(transform, vertex));
      const mins = [0, 1, 2].map(axis =>
        Math.min(...transformedVertices.map(vertex => vertex[axis]))
      );
      const normalized = transformedVertices.map(vertex =>
        vertex.map((coordinate, axis) => isohedralCoordinate(coordinate - mins[axis]))
      );
      const normalizedKey = isohedralVertexCloudKey(normalized);
      const targetPrototileIndices = isohedralOrientationMaps
        .map((orientations, prototileIdx) => orientations.has(normalizedKey) ? prototileIdx : -1)
        .filter(prototileIdx => prototileIdx >= 0);
      if (!targetPrototileIndices.length) return null;
      // Proper motions normally stay in the same internal prototile. A
      // reflection of a chiral lattice tile lands in the mirrored internal
      // copy instead. Prefer the original index when both descriptions are
      // geometrically identical so existing placements keep stable keys.
      const prototileIdx = targetPrototileIndices.includes(placement.prototile_idx)
        ? placement.prototile_idx
        : targetPrototileIndices[0];
      if (prototileIdx !== placement.prototile_idx) {
        searchStats.isohedral_cross_prototile_images =
          (searchStats.isohedral_cross_prototile_images ?? 0) + 1;
      }
      const tile = prototiles[prototileIdx];
      const orient = isohedralOrientationMaps[prototileIdx].get(normalizedKey);
      const translation = mins.map(isohedralCoordinate);
      if (tile.is_polycube
        ? !isPolycubeMoveTranslation(tile, translation)
        : !translation.every(Number.isInteger)) return null;
      return {
        prototile_idx: prototileIdx,
        orient,
        translation,
        _isohedral_transform: transform
      };
    };
    const periodicCosetKey = (placement, basis, rootTranslation) => {
      const determinant = determinant3(basis);
      const modulus = Math.abs(Math.round(determinant));
      if (!modulus || Math.abs(determinant - Math.round(determinant)) > ISOHEDRAL_EPSILON) return null;
      const delta = vecSub(placement.translation, rootTranslation);
      const numerators = [
        determinant3([delta, basis[1], basis[2]]),
        determinant3([basis[0], delta, basis[2]]),
        determinant3([basis[0], basis[1], delta])
      ];
      if (numerators.some(value => Math.abs(value - Math.round(value)) > ISOHEDRAL_EPSILON)) return null;
      const residues = numerators.map(value => euclideanMod(Math.round(value), modulus));
      return `${placement.prototile_idx}:${placement.orient.__orientation_id ?? ""}::${residues.join(",")}`;
    };
    const quotientFaceTranslation = (source, target) => {
      if (source.length !== target.length || source.length < 3) return null;
      for (const targetVertex of target) {
        const translation = vecSub(targetVertex, source[0]);
        if (translatedReverseFaceMatches(source, target, translation)) return translation;
      }
      return null;
    };
    const certifyPeriodicPlacementMotif = (placements, basis) => {
      const reject = reason => {
        searchStats.periodic_certificate_last_rejection = reason;
        return null;
      };
      const determinant = determinant3(basis);
      const cellVolume = Math.abs(determinant);
      if (cellVolume <= ISOHEDRAL_EPSILON) return reject("singular_period_basis");
      const motifVolume = placements.reduce(
        (sum, placement) => sum + (tileVolumes[placement.prototile_idx] ?? 0),
        0
      );
      if (Math.abs(cellVolume - motifVolume) > 1e-8 * Math.max(1, motifVolume)) {
        return reject("motif_volume_does_not_equal_cell_volume");
      }
      if (basis.some(vector => prototiles.some(tile =>
        tile.is_polycube && !isPolycubeTranslationVector(tile, vector)
      ))) return reject("period_vector_off_lattice");

      const faces = [];
      for (const placement of placements) {
        const vertices = globalPlacementVertices(placement);
        for (const face of placement.orient.faces) {
          faces.push(face.map(index => vertices[index]));
        }
      }
      const allowed = Array.from({ length: faces.length }, () => []);
      for (let left = 0; left < faces.length; left++) {
        for (let right = left + 1; right < faces.length; right++) {
          if (faceSignatureUndirected(faces[left]) !== faceSignatureUndirected(faces[right])) continue;
          const translation = quotientFaceTranslation(faces[left], faces[right]);
          if (!translation || !vectorIsInBasisLattice(translation, basis)) continue;
          allowed[left].push({ face: right, vector: translation });
          allowed[right].push({ face: left, vector: translation.map(value => -value) });
        }
      }
      if (allowed.some(options => options.length === 0)) return reject("unpaired_quotient_face");
      const matchFaces = (remaining, chosen) => {
        if (!remaining.size) return chosen;
        let pivot = null;
        let options = null;
        for (const faceIndex of remaining) {
          const available = allowed[faceIndex].filter(option => remaining.has(option.face));
          if (!available.length) return null;
          if (!options || available.length < options.length) {
            pivot = faceIndex;
            options = available;
          }
        }
        for (const option of options) {
          const next = new Set(remaining);
          next.delete(pivot);
          next.delete(option.face);
          const result = matchFaces(next, [...chosen, {
            source_face: pivot,
            target_face: option.face,
            translation: option.vector.slice()
          }]);
          if (result) return result;
        }
        return null;
      };
      const facePairing = matchFaces(new Set(faces.map((_, index) => index)), []);
      if (!facePairing) return reject("no_complete_quotient_face_pairing");
      if (!periodicTranslationNeighborhoodIsValid(basis, placements)) {
        return reject("translated_motif_neighborhood_overlap");
      }

      const rootTranslation = placements[0].translation;
      const motif = [];
      for (const placement of placements) {
        const orientationIndex = prototiles[placement.prototile_idx].unique_orientations.indexOf(placement.orient);
        if (orientationIndex < 0) return reject("unknown_motif_orientation");
        motif.push({
          prototile_idx: placement.prototile_idx,
          orientation_index: orientationIndex,
          orientation_id: placement.orient.__orientation_id ?? null,
          translation: vecSub(placement.translation, rootTranslation)
        });
      }
      const prototileCounts = new Map();
      for (const item of motif) {
        prototileCounts.set(item.prototile_idx, (prototileCounts.get(item.prototile_idx) ?? 0) + 1);
      }
      searchStats.periodic_certificate_last_rejection = null;
      return {
        kind: `${motif.length}_tile_periodic_symmetry_quotient`,
        tile_volume: motifVolume / motif.length,
        tile_volumes: tileVolumes.slice(),
        cell_volume: cellVolume,
        period_vectors: basis.map(vector => vector.slice()),
        motif,
        mixed_prototile: prototileCounts.size > 1,
        prototile_counts: [...prototileCounts.entries()]
          .map(([prototile_idx, count]) => ({ prototile_idx, count })),
        proof: {
          method: "quotient_face_pairing_equal_covolume",
          overlap_validation: "complete_lattice_translation_neighborhood",
          face_pairing: facePairing,
          motif_volume: motifVolume,
          lattice_determinant: cellVolume
        }
      };
    };
    const isohedralSymmetryCertificate = (template, placements) => {
      if (!placements.length) return null;
      const basis = template.period_vectors;
      const rootTranslation = placements[0].translation;
      const motifKeys = new Set(placements.map(placement =>
        periodicCosetKey(placement, basis, rootTranslation)
      ));
      if (motifKeys.has(null) || motifKeys.size !== placements.length) return null;
      const orbitTransforms = [];
      for (const target of placements) {
        let witness = null;
        for (const transform of isohedralRootTransformsTo(target)) {
          if (basis.some(vector =>
            !vectorIsInBasisLattice(isohedralMatrixVector(transform.rotation, vector), basis)
          )) continue;
          let preservesMotif = true;
          for (const placement of placements) {
            const image = isohedralTransformPlacement(placement, transform);
            const imageKey = image && periodicCosetKey(image, basis, rootTranslation);
            if (!imageKey || !motifKeys.has(imageKey)) {
              preservesMotif = false;
              break;
            }
          }
          if (!preservesMotif) continue;
          witness = transform;
          break;
        }
        if (!witness) return null;
        orbitTransforms.push(witness);
      }
      return {
        ...template,
        kind: `${placements.length}_tile_isohedral_periodic_quotient`,
        proof: {
          ...template.proof,
          isohedral_method: "tile_transitive_quotient_symmetry_group",
          orbit_transforms: orbitTransforms
        }
      };
    };
    const minePeriodicTemplateFromCurrentPatch = (options = {}) => {
      if (state.placements.length < 2) return null;
      const tileVolume = tileVolumes[0];
      if (!Number.isFinite(tileVolume) || tileVolume <= 0) return null;
      if (tileVolumes.some(volume => Math.abs(volume - tileVolume) > 1e-8 * Math.max(1, tileVolume))) {
        return null;
      }
      const certificateBudgetExceeded = options.budget_exceeded ?? overBudget;
      const recordCertificateBudgetExceeded = options.on_budget_exceeded ?? noteIncompleteSearch;
      const stopForCertificateBudget = () => {
        if (!certificateBudgetExceeded()) return false;
        recordCertificateBudgetExceeded();
        return true;
      };
      const rootTranslation = state.placements[0].translation;
      const vectorsByKey = new Map();
      for (let left = 0; left < state.placements.length; left++) {
        for (let right = left + 1; right < state.placements.length; right++) {
          const a = state.placements[left];
          const b = state.placements[right];
          if (a.prototile_idx !== b.prototile_idx || a.orient !== b.orient) continue;
          const vector = vecSub(b.translation, a.translation);
          if (!vector.some(Boolean) || !vector.every(Number.isInteger)) continue;
          const reverse = vector.map(value => -value);
          const canonical = vecKey(vector) < vecKey(reverse) ? vector : reverse;
          const key = vecKey(canonical);
          const existing = vectorsByKey.get(key);
          if (existing) existing.support += 1;
          else vectorsByKey.set(key, { vector: canonical, support: 1 });
        }
      }
      const configuredVectorLimit = Number(
        options.vector_limit ?? config.generic_periodic_vector_limit ?? config.isohedral_period_vector_limit
      );
      const vectorLimit = Number.isFinite(configuredVectorLimit) && configuredVectorLimit > 0
        ? Math.floor(configuredVectorLimit)
        : 48;
      const rankedTranslations = [...vectorsByKey.values()].sort((left, right) =>
        right.support - left.support
        || left.vector.reduce((sum, value) => sum + value * value, 0)
          - right.vector.reduce((sum, value) => sum + value * value, 0)
        || vecKey(left.vector).localeCompare(vecKey(right.vector))
      ).slice(0, vectorLimit);
      const vectors = rankedTranslations.map(entry => entry.vector);
      options.on_vectors?.(
        vectors.length,
        rankedTranslations.slice(0, 12).map(entry => ({
          vector: entry.vector.slice(),
          support: entry.support
        }))
      );
      for (let first = 0; first < vectors.length; first++) {
        for (let second = first + 1; second < vectors.length; second++) {
          for (let third = second + 1; third < vectors.length; third++) {
            if (stopForCertificateBudget()) return null;
            options.on_basis?.();
            const basis = [vectors[first], vectors[second], vectors[third]];
            const determinant = Math.abs(determinant3(basis));
            const motifSize = Math.round(determinant / tileVolume);
            if (!motifSize || motifSize > state.placements.length) continue;
            if (Math.abs(determinant - motifSize * tileVolume) > 1e-8 * Math.max(1, determinant)) continue;
            const representatives = new Map();
            for (const placement of state.placements) {
              const key = periodicCosetKey(placement, basis, rootTranslation);
              if (!key) break;
              if (!representatives.has(key)) representatives.set(key, placement);
            }
            if (representatives.size !== motifSize) continue;
            const placements = [...representatives.values()];
            const periodic = certifyPeriodicPlacementMotif(placements, basis);
            if (!periodic) continue;
            const accepted = options.accept_periodic
              ? options.accept_periodic(periodic, placements)
              : periodic;
            if (accepted) return accepted;
          }
        }
      }
      return null;
    };
    const mineIsohedralPeriodicTemplate = () => minePeriodicTemplateFromCurrentPatch({
      accept_periodic: (periodic, placements) =>
        isohedralSymmetryCertificate(periodic, placements)
    });
    let isohedralLargestCertificatePatchTried = 0;
    const isohedralCertificateStatesTried = new Set();
    const tryMineIsohedralCertificate = ({ force = false } = {}) => {
      if (state.placements.length < 2) return null;
      if (growthStats().axis_rank < Math.min(3, tilingDimension)) return null;
      const configuredCertificateStride = Number(config.isohedral_certificate_stride);
      const certificateStride = Number.isFinite(configuredCertificateStride) && configuredCertificateStride > 0
        ? Math.floor(configuredCertificateStride)
        : 8;
      if (!force && state.placements.length < isohedralLargestCertificatePatchTried + certificateStride) {
        return null;
      }
      const stateKey = periodicPatchStateKey();
      if (isohedralCertificateStatesTried.has(stateKey)) {
        searchStats.isohedral_certificate_duplicate_states_skipped += 1;
        return null;
      }
      isohedralCertificateStatesTried.add(stateKey);
      isohedralLargestCertificatePatchTried = Math.max(
        isohedralLargestCertificatePatchTried,
        state.placements.length
      );
      searchStats.isohedral_certificate_attempts += 1;
      searchStats.isohedral_certificate_patch_sizes_tried.push(state.placements.length);
      return mineIsohedralPeriodicTemplate();
    };
    const rollbackIsohedralMoves = applied => {
      while (applied.length) {
        const entry = applied.pop();
        undoMove(entry.move, entry.rollback, { captureBest: false });
      }
    };
    const buildIsohedralPatchImage = (transform, sourcePatch) => {
      const existing = new Set(state.placements.map(placementGeometryKey));
      const pending = [];
      const pendingKeys = new Set();
      for (const placement of sourcePatch) {
        const move = isohedralTransformPlacement(placement, transform);
        if (!move) return null;
        const geometryKey = placementGeometryKey(move);
        if (existing.has(geometryKey) || pendingKeys.has(geometryKey)) continue;
        pendingKeys.add(geometryKey);
        pending.push(move);
      }
      return pending;
    };
    const moveOldestFrontierTouches = move => {
      const oldestLayer = minFrontierPointLayer();
      return sharedFrontierPoints(move).reduce((count, point) =>
        count + (frontierPointLayer(vecKey(point)) === oldestLayer ? 1 : 0), 0);
    };
    const isohedralPatchImagePriority = pending => {
      let oldestLayer = Infinity;
      let oldestTouches = 0;
      for (const move of pending) {
        for (const point of sharedFrontierPoints(move)) {
          const layer = frontierPointLayer(vecKey(point));
          if (layer < oldestLayer) {
            oldestLayer = layer;
            oldestTouches = 1;
          } else if (layer === oldestLayer) {
            oldestTouches += 1;
          }
        }
      }
      const centers = [
        ...state.placements.map(placementCenter),
        ...pending.map(placementCenter)
      ];
      const spans = [0, 1, 2].map(axis =>
        Math.max(...centers.map(center => center[axis]))
        - Math.min(...centers.map(center => center[axis]))
      );
      const maximumSpan = Math.max(...spans);
      return {
        oldest_layer: oldestLayer,
        oldest_touches: oldestTouches,
        axis_rank: spans.filter(span => span > 1e-9).length,
        isotropy: maximumSpan > 1e-9 ? Math.min(...spans) / maximumSpan : 0,
        maximum_span: maximumSpan
      };
    };
    const applyIsohedralPatchImage = pending => {
      if (!pending.length) return [];
      const applied = [];
      for (const move of pending) {
        const validity = checkMoveViability(move);
        if (!validity) {
          rollbackIsohedralMoves(applied);
          return null;
        }
        move.occupancy_data = validity.occData;
        move.layer = candidateMoveLayer(move);
        move.is_forced = true;
        const rollback = applyMove(move);
        applied.push({ move, rollback });
      }
      return applied;
    };
    const isohedralGoalMet = () => {
      if (criterion !== "count") return goalMet();
      const configuredHorizon = Number(config.isohedral_search_horizon_tiles);
      const proofHorizon = Number.isFinite(configuredHorizon) && configuredHorizon > 0
        ? Math.floor(configuredHorizon)
        : targetVal;
      searchStats.isohedral_search_horizon_tiles = proofHorizon;
      if (state.placements.length < proofHorizon) return false;
      const growth = growthStats();
      const configuredMinimum = Number(config.growth_isotropy_min);
      const minimumIsotropy = Number.isFinite(configuredMinimum)
        ? Math.max(0, Math.min(1, configuredMinimum))
        : 0.5;
      return growth.axis_rank >= Math.min(3, tilingDimension)
        && growth.isotropy >= minimumIsotropy;
    };
    async function* propagateIsohedralPatch(parentId) {
      const applied = [];
      const attempted = new Set();
      applied.inconsistent = false;
      let madeProgress = true;
      let firstPass = true;
      while (madeProgress && (firstPass || !isohedralGoalMet())) {
        firstPass = false;
        madeProgress = false;
        const sourcePatch = state.placements.slice();
        const transforms = new Map();
        for (const anchor of sourcePatch) {
          for (const transform of isohedralRootTransformsTo(anchor)) {
            const transformKey = isohedralTransformKey(transform);
            transforms.set(transformKey, transform);
            if (transform.determinant < 0) searchStats.reflection_continuations_seen += 1;
          }
        }
        searchStats.isohedral_transforms_discovered = Math.max(
          searchStats.isohedral_transforms_discovered,
          transforms.size
        );
        const imageCandidates = [];
        for (const [transformKey, transform] of transforms) {
          const attemptKey = `${transformKey}@${sourcePatch.length}`;
          if (attempted.has(attemptKey)) continue;
          const pending = buildIsohedralPatchImage(transform, sourcePatch);
          if (pending === null || !pending.length) continue;
          imageCandidates.push({
            attemptKey,
            transform,
            pending,
            priority: isohedralPatchImagePriority(pending)
          });
        }
        imageCandidates.sort((left, right) =>
          left.priority.oldest_layer - right.priority.oldest_layer
          || right.priority.oldest_touches - left.priority.oldest_touches
          || right.priority.axis_rank - left.priority.axis_rank
          || right.priority.isotropy - left.priority.isotropy
          || left.priority.maximum_span - right.priority.maximum_span
          || left.pending.length - right.pending.length
        );
        const oldestFrontierLayer = minFrontierPointLayer();
        const eligible = imageCandidates.filter(candidate =>
          candidate.priority.oldest_layer === oldestFrontierLayer
        );
        searchStats.isohedral_newer_layer_deferrals += imageCandidates.length - eligible.length;
        for (const candidate of eligible) {
          attempted.add(candidate.attemptKey);
          const additions = applyIsohedralPatchImage(candidate.pending);
          if (additions === null) {
            searchStats.isohedral_patch_conflicts += 1;
            continue;
          }
          madeProgress = additions.length > 0;
          if (!madeProgress) continue;
          searchStats.isohedral_patch_copies_applied += 1;
          searchStats.isohedral_tiles_propagated += additions.length;
          searchStats.forced_total += additions.length;
          for (const entry of additions) {
            applied.push(entry);
            yield placementDelta("add", entry.move, entry.rollback, parentId);
          }
          yield nodeStatus(
            parentId,
            "working",
            `oldest-layer patch: +${additions.length}`,
            preflightStatusPayload()
          );
          if (shouldSnapshot()) {
            yield snapshot(parentId);
            await tick();
          }
          await yieldToBrowser();
          break;
        }
      }
      return applied;
    }
    async function* searchIsohedral(parentId, depth = 0) {
      if (stopToken.stop) { noteIncompleteSearch(); return false; }
      if (overBudget()) {
        noteIncompleteSearch();
        yield nodeStatus(parentId, "fail", budgetText());
        return false;
      }
      const propagated = yield* propagateIsohedralPatch(parentId);
      const rollbackPropagated = function* () {
        while (propagated.length) {
          const entry = propagated.pop();
          undoMove(entry.move, entry.rollback);
          searchStats.forced_total = Math.max(0, searchStats.forced_total - 1);
          yield placementDelta("remove", entry.move, entry.rollback, parentId);
        }
      };
      if (propagated.inconsistent) {
        searchStats.failed_leaves += 1;
        yield nodeStatus(parentId, "fail", "Patch cannot be lifted onto every tile");
        yield* rollbackPropagated();
        return false;
      }
      // Quotient certification is a proof obligation, not a visualization
      // milestone. Mine at bounded live-patch checkpoints and at the separate
      // proof horizon; otherwise raising the requested preview count can hide
      // a certificate that was already present in a smaller patch.
      const template = tryMineIsohedralCertificate({ force: isohedralGoalMet() });
      if (template) {
        searchStats.isohedral_certificate_patch_size = state.placements.length;
        tilingEvidence = {
          kind: "isohedral_certificate",
          certified: true,
          strategy: "isohedral",
          patch_size: template.motif.length,
          certificate_kind: template.kind,
          period_vectors: template.period_vectors.map(vector => vector.slice()),
          periodic_template: template
        };
        yield nodeStatus(parentId, "success", "certified tile-transitive quotient", preflightStatusPayload(template));
        return true;
      }
      if (isohedralGoalMet()) {
        yield nodeStatus(parentId, "fail", "finite isohedral-looking patch has no exact quotient certificate");
        yield* rollbackPropagated();
        return false;
      }
      if (frontierPointOptions().length === 0) {
        searchStats.failed_leaves += 1;
        yield nodeStatus(parentId, "fail", "finite closed patch does not tile 3-space");
        yield* rollbackPropagated();
        return false;
      }

      const candidateMap = new Map();
      for (const option of frontierPointOptions()) {
        const moves = await preflightFaceCandidatesForOption(option, candidateCap);
        for (const move of moves) {
          if (!moveWithinGenerationBand(move)) {
            searchStats.generation_band_deferrals += 1;
            continue;
          }
          // Mirrored copies of a chiral tile are separate internal prototiles,
          // but they belong to the same tile orbit under full isometries.
          // Test actual root congruence instead of comparing implementation
          // indices, which also keeps genuinely different species excluded.
          if (!isohedralRootTransformsTo(move).length) continue;
          if (moveOldestFrontierTouches(move) === 0) continue;
          candidateMap.set(move.dedup_key ?? placementGeometryKey(move), move);
        }
        await yieldToBrowser();
      }
      let candidates = [...candidateMap.values()].sort((left, right) => {
        const leftShape = prospectiveGrowthShape(left);
        const rightShape = prospectiveGrowthShape(right);
        return compareScoreVectors([
          minimumLayerCompletionScore(left),
          coveredFrontierFaceScore(left, 0),
          leftShape.axis_rank,
          leftShape.axis_isotropy,
          leftShape.axis_planarity,
          -leftShape.max_span,
          moveCoverage(left)
        ], [
          minimumLayerCompletionScore(right),
          coveredFrontierFaceScore(right, 0),
          rightShape.axis_rank,
          rightShape.axis_isotropy,
          rightShape.axis_planarity,
          -rightShape.max_span,
          moveCoverage(right)
        ]);
      });
      if (Number.isFinite(branchCap)) candidates = candidates.slice(0, branchCap);
      if (!candidates.length) {
        searchStats.failed_leaves += 1;
        yield nodeStatus(parentId, "fail", "No tile-transitive continuation");
        yield* rollbackPropagated();
        return false;
      }

      const payload = candidates.map(move => ({
        id: nowId(),
        text: "isohedral seed relation",
        ...describeMove(move)
      }));
      for (let index = 0; index < candidates.length; index++) candidates[index].node_id = payload[index].id;
      setBranchCursor(depth, candidates.length, 0);
      yield branchSet(parentId, payload);

      for (let index = 0; index < candidates.length; index++) {
        const move = candidates[index];
        const validity = checkMoveViability(move);
        if (!validity) {
          setBranchCursor(depth, candidates.length, index + 1);
          continue;
        }
        move.occupancy_data = validity.occData;
        move.is_forced = false;
        move.layer = candidateMoveLayer(move);
        searchStats.branch_choices_visited += 1;
        searchStats.max_depth = Math.max(searchStats.max_depth, depth + 1);
        setBranchCursor(depth, candidates.length, index);
        const rollback = applyMove(move);
        yield placementDelta("add", move, rollback, move.node_id);
        yield nodeStatus(move.node_id, "working", `[${state.placements.length}] seed relation`);
        if (shouldSnapshot()) yield snapshot(move.node_id);

        const child = yield* searchIsohedral(move.node_id, depth + 1);
        if (child) {
          yield nodeStatus(move.node_id, "success", "tile-transitive patch");
          return true;
        }
        searchStats.backtracks += 1;
        undoMove(move, rollback);
        yield placementDelta("remove", move, rollback, move.node_id);
        yield nodeStatus(move.node_id, "fail", "isohedral relation failed");
        setBranchCursor(depth, candidates.length, index + 1);
      }
      yield* rollbackPropagated();
      yield nodeStatus(parentId, "fail", "Isohedral branch exhausted");
      return false;
    }

    async function* search(parentId, depth = 0) {
      if (stopToken.stop) { noteIncompleteSearch(); return false; }
      if (goalMet()) {
        yield nodeStatus(parentId, "success");
        return true;
      }
      if (overBudget()) {
        noteIncompleteSearch();
        yield nodeStatus(parentId, "fail", budgetText());
        return false;
      }
      if (genericPeriodicCheckpointEnabled) {
        const checkpointTemplate = yield* tryGenericPeriodicCertificate("generic_growth_checkpoint");
        if (checkpointTemplate) {
          yield nodeStatus(
            parentId,
            "success",
            `GCTS ${state.placements.length}-tile checkpoint is an exact translational quotient`,
            preflightStatusPayload(checkpointTemplate)
          );
          return true;
        }
      }
      const entryFailureKey = genericFailureMemoEnabled ? genericFailureStateKey() : null;
      const entryFailurePlacements = genericFailureMemoEnabled ? state.placements.slice() : null;
      const forcedBatch = [];
      const doReturn = async function* (retval) {
        // Exhaustive controls whether failure is a certificate; it must not
        // continue a satisfiability search after finding a witness.
        if (retval) return true;
        while (forcedBatch.length) {
          const [mv, rb] = forcedBatch.pop();
          undoMove(mv, rb);
          yield placementDelta("remove", mv, rb);
        }
        if (!searchIncomplete) rememberGenericFailure(entryFailureKey, entryFailurePlacements);
        return retval;
      };
      if (entryFailureKey && genericFailureMemo.has(entryFailureKey)) {
        searchStats.generic_failure_memo_hits += 1;
        yield nodeStatus(parentId, "fail", "Known dead state");
        return yield* doReturn(false);
      }
      const node_candidate_cache = new Map();
      const screenCachedVertexCandidates = (option, candidates, maxCandidates) => {
        const dedup = new Map();
        const localCandidateCap = Math.min(maxCandidates, candidateCap);
        for (const candidate of candidates ?? []) {
          if (!candidateTouchesPoint(candidate, option.pointKey)) continue;
          if (!candidatePassesGeometricNogoods(candidate)) continue;
          const validity = checkMoveViability(candidate);
          if (!validity) continue;
          const key = candidate.dedup_key ?? placementGeometryKey(candidate);
          if (!dedup.has(key)) dedup.set(key, { ...candidate, occupancy_data: validity.occData });
          if (Number.isFinite(localCandidateCap) && dedup.size >= localCandidateCap) break;
        }
        return [...dedup.values()];
      };

      const candidatesForVertexOption = async (option, maxCandidates = 2) => {
        const cacheKey = `${option.pointKey}::${maxCandidates}`;
        const cached = state.vertex_candidate_cache.get(cacheKey);
        if (cached) return cached;

        // Any connected face-to-face continuation covers at least one active
        // frontier face. Index those exact reversed-face matches once per
        // state instead of trying every occupied-cell anchor at every vertex.
        // The index already viability-checks and geometry-deduplicates moves.
        const indexed = faceCandidatesByFrontierPoint().get(option.pointKey) ?? [];
        const localCandidateCap = Math.min(maxCandidates, candidateCap);
        const out = Number.isFinite(localCandidateCap)
          ? indexed.slice(0, localCandidateCap)
          : indexed.slice();
        state.vertex_candidate_cache.set(cacheKey, out);
        return out;
      };
      const nodeCandidatesForVertexOption = async (option, maxCandidates = 2) => {
        const cacheKey = `${option.pointKey}::${maxCandidates}`;
        const cached = node_candidate_cache.get(cacheKey);
        if (cached) {
          const screened = screenCachedVertexCandidates(option, cached, maxCandidates);
          if (screened.length) {
            node_candidate_cache.set(cacheKey, screened);
            return screened;
          }
        }
        const candidates = await candidatesForVertexOption(option, maxCandidates);
        const screened = genericGeometricNogoodEnabled
          ? screenCachedVertexCandidates(option, candidates, maxCandidates)
          : candidates;
        node_candidate_cache.set(cacheKey, screened);
        return screened;
      };
      const analyzeFrontierGraph = async () => {
        if (latestFrontierGraph && latestFrontierGraphVersion === stateVersion) return latestFrontierGraph;
        const graph = await buildFrontierCandidateGraph(
          frontierPointOptions(),
          option => nodeCandidatesForVertexOption(option, candidateCap),
          {
            frontierKey: option => option.pointKey,
            frontierNode: option => ({
              point: option.point.slice(),
              weight: option.weight,
              added_depth: option.added_depth
            }),
            candidateKey: candidate => candidate.dedup_key ?? placementGeometryKey(candidate),
            candidateNode: candidate => ({
              prototile_idx: candidate.prototile_idx,
              translation: candidate.translation?.slice() ?? [0, 0, 0]
            })
          }
        );
        if (criterion !== "region" || !targetRegion?.boundary) {
          return classifyFrontierCandidateGraph(graph, frontierOptionOrder);
        }
        const options = graph.options.filter(option =>
          option.unique_candidates.length > 0 || !targetRegion.boundary(option.point)
        );
        const pointKeys = new Set(options.map(option => option.pointKey));
        const frontierPoints = graph.frontier_points.filter(point => pointKeys.has(point.point_key));
        const regionGraph = {
          ...graph,
          options,
          frontier_points: frontierPoints,
          association_count: frontierPoints.reduce((sum, point) => sum + point.candidate_keys.length, 0)
        };
        return classifyFrontierCandidateGraph(regionGraph, frontierOptionOrder);
      };
      const allLegalFaceExtensions = () => {
        const dedup = new Map();
        for (const candidates of faceCandidatesByFrontierPoint().values()) {
          for (const candidate of candidates) {
            const key = candidate.dedup_key ?? placementGeometryKey(candidate);
            if (!dedup.has(key)) dedup.set(key, candidate);
          }
        }
        const candidates = [...dedup.values()];
        if (genericConnectedPatchEnumeration) {
          searchStats.generic_connected_patch_candidate_states += 1;
          searchStats.generic_connected_patch_max_candidates = Math.max(
            searchStats.generic_connected_patch_max_candidates,
            candidates.length
          );
        }
        searchStats.generic_global_extension_candidate_states += 1;
        searchStats.generic_global_extension_max_candidates = Math.max(
          searchStats.generic_global_extension_max_candidates,
          candidates.length
        );
        return candidates;
      };
      const pendingShellFaceExtensions = () => {
        // Select a required obligation, not a heuristic growth direction.
        // Every exposed face owned below the requested shell depth must be
        // covered in any successful shell. Candidate choice at that face is
        // still exhaustively branched. Unlike a frontier vertex, growth
        // elsewhere cannot create a new legal mate for this face; additional
        // tiles can only remove candidates. MRV over every pending interior
        // face therefore exposes zero-candidate contradictions immediately.
        const shell = completeShellDepthStats();
        // A mate for a fixed exposed face has fixed geometry. Adding tiles
        // elsewhere can invalidate such a mate through overlap, but can never
        // create a new one. This is a contradiction only when the face is an
        // obligation of the shell currently being completed. An unfillable
        // outer face may belong to a branch which can still witness the finite
        // inner shell, so pruning it here would make shell exhaustion unsound.
        let selectedFaceKey = null;
        let selectedFaceDepth = Infinity;
        let selectedCandidates = null;
        for (const [faceKey, entry] of state.frontier.entries()) {
          const ownerDepth = shell.owner_depth_by_placement.get(entry.owner_placement);
          if (!Number.isFinite(ownerDepth) || ownerDepth >= targetVal) continue;
          const candidates = candidatesForRequiredShellFace(faceKey, entry);
          if (!candidates.length && genericGlobalZeroFacePruning) {
            searchStats.generic_global_zero_face_dead_ends += 1;
            searchStats.generic_global_extension_candidate_states += 1;
            return [];
          }
          if (
            selectedCandidates === null
            || ownerDepth < selectedFaceDepth
            || (ownerDepth === selectedFaceDepth && candidates.length < selectedCandidates.length)
            || (
              ownerDepth === selectedFaceDepth
              && candidates.length === selectedCandidates.length
              && faceKey < selectedFaceKey
            )
          ) {
            selectedFaceKey = faceKey;
            selectedFaceDepth = ownerDepth;
            selectedCandidates = candidates;
          }
        }
        const candidates = selectedCandidates ?? [];
        searchStats.generic_global_extension_candidate_states += 1;
        searchStats.generic_global_extension_max_candidates = Math.max(
          searchStats.generic_global_extension_max_candidates,
          candidates.length
        );
        return candidates;
      };
      let forcedCount = 0;
      let branchAnalysis = null;
      while (!genericGlobalExtensionEnumeration) {
        await yieldToBrowser();
        if (stopToken.stop) { noteIncompleteSearch(); return yield* doReturn(false); }
        if (overBudget()) {
          noteIncompleteSearch();
          yield nodeStatus(parentId, "fail", budgetText());
          return yield* doReturn(false);
        }
        if (frontierPointOptions().length === 0) {
          yield nodeStatus(parentId, "success"); return yield* doReturn(true);
        }

        const analysis = await analyzeFrontierGraph();
        const frontierDual = frontierGraphPayload(analysis);
        const analysisStats = rememberFrontierGraph(analysis);
        if (overBudget()) { noteIncompleteSearch(); yield nodeStatus(parentId, "fail", budgetText()); return yield* doReturn(false); }
        if (analysis.deadEnd) {
          searchStats.failed_leaves += 1;
          yield nodeStatus(parentId, "fail", "Dead End", { frontier_stats: analysisStats, frontier_dual: frontierDual });
          return yield* doReturn(false);
        }
        yield nodeStatus(parentId, "working", "", { frontier_stats: analysisStats, frontier_dual: frontierDual });
        if (analysis.forced?.length) {
          const option = analysis.forced[0];
          const mv = option.unique_candidates[0];
          const layerLag = moveLayerLagInfo(mv);
          mv.generation_lag = layerLag.layer_lag;
          if (Number.isFinite(forcedMoveLayerLagCap) && layerLag.layer_lag > forcedMoveLayerLagCap) {
            branchAnalysis = throttledForcedBranchAnalysis(analysis);
            searchStats.forced_throttles += 1;
            yield nodeStatus(parentId, "working", "forced cap", {
              frontier_stats: analysisStats,
              frontier_dual: frontierDual,
              forced_cap: {
                reason: "forced-layer-lag",
                forced_count: forcedCount,
                ...layerLag,
                released_branch_count: branchAnalysis.branches?.length ?? 0,
                released_singletons: !!branchAnalysis.forced_throttle_released_singletons
              }
            });
            break;
          }
          mv.layer = layerLag.move_layer;
          mv.is_forced = true;
          searchStats.forced_total += 1;
          const rb = applyMove(mv);
          yield placementDelta("add", mv, rb);
          node_candidate_cache.clear();
          forcedBatch.push([mv, rb]);
          forcedCount += 1;
          if (genericPeriodicCheckpointEnabled) {
            const checkpointTemplate = yield* tryGenericPeriodicCertificate("generic_growth_checkpoint");
            if (checkpointTemplate) {
              yield nodeStatus(
                parentId,
                "success",
                `GCTS ${state.placements.length}-tile checkpoint is an exact translational quotient`,
                preflightStatusPayload(checkpointTemplate)
              );
              return yield* doReturn(true);
            }
          }
          const forcedAnalysis = await analyzeFrontierGraph();
          const forcedStats = rememberFrontierGraph(forcedAnalysis);
          const forcedDual = frontierGraphPayload(forcedAnalysis);
          yield nodeStatus(parentId, "working", "", { frontier_stats: forcedStats, frontier_dual: forcedDual });
          if (shouldSnapshot()) {
            yield snapshot(null);
            await tick();
          }
          if (goalMet() || state.placements.length >= safetyMax) {
            yield nodeStatus(parentId, "success");
            return yield* doReturn(true);
          }
          continue;
        }
        branchAnalysis = analysis;
        break;
      }

      if (genericGlobalExtensionEnumeration) {
        const analysis = genericGlobalFrontierGraph
          ? await analyzeFrontierGraph()
          : null;
        const frontierDual = analysis ? frontierGraphPayload(analysis) : null;
        const analysisStats = analysis
          ? rememberFrontierGraph(analysis)
          : calculateFrontierStats();
        if (overBudget()) {
          noteIncompleteSearch();
          yield nodeStatus(parentId, "fail", budgetText());
          return yield* doReturn(false);
        }
        // Retain the frontier dual for diagnosis and visualization, but do not
        // infer dead ends or forced moves from this instantaneous vertex view.
        yield nodeStatus(parentId, "working", "", {
          frontier_stats: analysisStats,
          ...(frontierDual ? { frontier_dual: frontierDual } : {})
        });
        branchAnalysis = analysis;
      }

      if (forcedCount > 0) {
        const postForcedStats = frontierStatsWithCandidateCount();
        const forcedNodeId = nowId();
        if (shouldSnapshot()) {
          yield snapshot(forcedNodeId);
          await tick();
        } else {
          yield nodeSnapshot(forcedNodeId);
        }
        yield branchSet(parentId, [{ id: forcedNodeId, text: `+ ${forcedCount} forced`, is_forced: true, frontier_stats: postForcedStats }]);
        yield nodeStatus(forcedNodeId, "success", "", { frontier_stats: postForcedStats });
      }

      const branchOptions = branchAnalysis?.branches ?? [];
      let bestMoves = genericGlobalExtensionEnumeration
        ? genericCompleteShellEnumeration
          ? pendingShellFaceExtensions()
          : allLegalFaceExtensions()
        : policyAgentProposals(branchAnalysis);
      let bestOption = null;
      let bestOptionMoves = [];
      if (!genericGlobalExtensionEnumeration && !bestMoves.length && branchOptions.length) {
        let bestPointScore = null;
        for (const option of branchOptions) {
          await yieldToBrowser();
          const optionMoves = option.unique_candidates ?? await nodeCandidatesForVertexOption(option, candidateCap);
          const moves = optionMoves.filter(moveWithinGenerationBand);
          searchStats.generation_band_deferrals += optionMoves.length - moves.length;
          if (!moves.length) continue;
          let bestCoverage = -1;
          for (const m of moves) bestCoverage = Math.max(bestCoverage, moveCoverage(m));
          const score = faceOrder === "mrv"
            ? [-moves.length, -(option.added_depth ?? 0), -frontierPointNorm(option), bestCoverage, seededTieBreaks ? seededTieValue(`point:${option.pointKey}`) : 0]
            : faceOrder === "pocket"
            ? [-(option.added_depth ?? 0), -frontierPointNorm(option), option.weight, -moves.length, bestCoverage, seededTieBreaks ? seededTieValue(`point:${option.pointKey}`) : 0]
            : faceOrder === "constrained"
              ? [-(option.added_depth ?? 0), -frontierPointNorm(option), -moves.length, bestCoverage, seededTieBreaks ? seededTieValue(`point:${option.pointKey}`) : 0]
              : [-(option.added_depth ?? 0), -frontierPointNorm(option), bestCoverage, -moves.length, seededTieBreaks ? seededTieValue(`point:${option.pointKey}`) : 0];
          if (isBetterScore(score, bestPointScore)) {
            bestPointScore = score;
            bestOption = option;
            bestOptionMoves = moves;
          }
        }
        if (!bestOption) {
          for (const option of branchOptions) {
            await yieldToBrowser();
            const optionMoves = option.unique_candidates ?? await nodeCandidatesForVertexOption(option, candidateCap);
            const moves = optionMoves.filter(moveWithinGenerationBand);
            searchStats.generation_band_deferrals += optionMoves.length - moves.length;
            if (moves.length) { bestOption = option; bestOptionMoves = moves; break; }
          }
        }
      }

      if (!bestMoves.length && !bestOption) {
        searchStats.failed_leaves += 1;
        yield nodeStatus(parentId, "fail", "Dead End");
        return yield* doReturn(false);
      }

      if (!bestMoves.length) bestMoves = bestOptionMoves.sort(compareMoves);
      else if (!usePolicyAgent) bestMoves = bestMoves.sort(compareMoves);
      else bestMoves = bestMoves.sort((left, right) =>
        compareScoreVectors(
          left._agent_proposal_score ?? rlAgent.score(left),
          right._agent_proposal_score ?? rlAgent.score(right)
        )
      );
      bestMoves = bestMoves.filter(moveWithinGenerationBand);
      if (!usePolicyAgent && !exhaustive && Number.isFinite(branchCap) && bestMoves.length > branchCap) {
        bestMoves = bestMoves.slice(0, branchCap);
      }
      if (greedyNoBacktrack && bestMoves.length > 1) bestMoves = [bestMoves[0]];
      const payload = bestMoves.map(move => ({ id: nowId(), text: "", ...describeMove(move) }));
      for (let i = 0; i < bestMoves.length; i++) bestMoves[i].node_id = payload[i].id;
      setBranchCursor(depth, bestMoves.length, 0);
      
      yield branchSet(parentId, payload);

      for (let i = 0; i < bestMoves.length; i++) {
        await yieldToBrowser();
        if (overBudget()) {
          noteIncompleteSearch();
          yield nodeStatus(parentId, "fail", budgetText());
          return yield* doReturn(false);
        }
        const mv = bestMoves[i];
        if (!candidatePassesGeometricNogoods(mv)) {
          yield nodeStatus(mv.node_id, "fail", "Geometric nogood");
          setBranchCursor(depth, bestMoves.length, i + 1);
          continue;
        }
        const refreshedValidity = checkMoveViability(mv);
        if (!refreshedValidity) {
          yield nodeStatus(mv.node_id, "fail", "Marked mismatch");
          setBranchCursor(depth, bestMoves.length, i + 1);
          continue;
        }
        mv.occupancy_data = refreshedValidity.occData;
        mv.is_forced = false;
        setBranchCursor(depth, bestMoves.length, i);
        searchStats.branch_choices_visited += 1;
        searchStats.max_depth = Math.max(searchStats.max_depth, depth + 1);
        const rb = applyMove(mv);
        yield placementDelta("add", mv, rb, mv.node_id);
        const postMoveAnalysis = genericGlobalExtensionEnumeration && !genericGlobalFrontierGraph
          ? null
          : await analyzeFrontierGraph();
        const postMoveStats = postMoveAnalysis
          ? rememberFrontierGraph(postMoveAnalysis)
          : calculateFrontierStats();
        const postMoveDual = postMoveAnalysis ? frontierGraphPayload(postMoveAnalysis) : null;
        
        yield nodeStatus(mv.node_id, "working", `[${state.placements.length}] ${treeTileName(prototiles[mv.prototile_idx].name)} (${i+1}/${bestMoves.length})`, {
          color_id: mv.color_id,
          frontier_stats: postMoveStats,
          ...(postMoveDual ? { frontier_dual: postMoveDual } : {})
        });
        if (shouldSnapshot()) {
          yield snapshot(mv.node_id);
          await tick();
        } else {
          yield nodeSnapshot(mv.node_id);
        }

        const child = yield* search(mv.node_id, depth + 1);
        if (usePolicyAgent) rlAgent.observe(mv, child);
        if (child) {
          yield nodeStatus(mv.node_id, "success");
          return yield* doReturn(true);
        } else {
          searchStats.backtracks += 1;
          yield nodeStatus(mv.node_id, "fail");
        }
        undoMove(mv, rb);
        yield placementDelta("remove", mv, rb, mv.node_id);
        setBranchCursor(depth, bestMoves.length, i + 1);
      }

      yield nodeStatus(parentId, "fail");
      return yield* doReturn(false);
    }

    async function* replayLearnedProposalPatch(parentId) {
      if (
        !proposalProgram?.patch?.length
        || proposalProgram.patch.length < 2
        || config.proposal_patch_replay === false
      ) return 0;
      const root = proposalProgram.patch[0];
      if (
        root.prototile_idx !== startMove.prototile_idx
        || (root.orientation_id && root.orientation_id !== startMove.orient.__orientation_id)
      ) {
        searchStats.proposal_patch_conflicts += 1;
        return 0;
      }
      let replayed = 0;
      for (const descriptor of proposalProgram.patch.slice(1)) {
        if (goalMet() || overBudget() || state.placements.length >= safetyMax) break;
        const tile = prototiles[descriptor.prototile_idx];
        const orient = descriptor.orientation_signature
          ? tile?.unique_orientations?.find(item =>
              [
                ...item.verts.map(vertex => `v:${vertex.join(",")}`),
                ...item.occupancy.map(point => `o:${point.pos.join(",")}:${point.weight}`)
              ].sort().join("|") === descriptor.orientation_signature
            )
          : descriptor.orientation_index != null
            ? tile?.unique_orientations?.[descriptor.orientation_index]
            : descriptor.orientation_id
              ? tile?.unique_orientations?.find(item => item.__orientation_id === descriptor.orientation_id)
              : tile?.unique_orientations?.[0];
        if (!tile || !orient) {
          searchStats.proposal_patch_conflicts += 1;
          break;
        }
        const translation = vecAdd(startMove.translation, descriptor.translation);
        if (tile.is_polycube ? !isPolycubeMoveTranslation(tile, translation) : !translation.every(Number.isInteger)) {
          searchStats.proposal_patch_conflicts += 1;
          break;
        }
        const move = {
          prototile_idx: descriptor.prototile_idx,
          orient,
          translation,
          layer: candidateMoveLayer({ prototile_idx: descriptor.prototile_idx, orient, translation }),
          is_forced: false,
          _learned_patch_index: descriptor.index
        };
        // The proposal was recorded from a previously validated search path.
        // Recheck the actual geometric constraints while allowing cavity-
        // closing steps that no longer satisfy the frontier candidate
        // generator's minimum exposed-contact heuristic.
        const validity = isMoveValid(move);
        if (!validity.ok) {
          searchStats.proposal_patch_conflicts += 1;
          searchStats.proposal_patch_conflict_index = descriptor.index;
          searchStats.proposal_patch_conflict_reason = validity.reason ?? "invalid";
          break;
        }
        move.occupancy_data = validity.occData;
        if (!moveWithinGenerationBand(move)) {
          searchStats.generation_band_deferrals += 1;
          searchStats.proposal_patch_conflicts += 1;
          searchStats.proposal_patch_conflict_index = descriptor.index;
          searchStats.proposal_patch_conflict_reason = "generation-band";
          break;
        }
        const rollback = applyMove(move);
        replayed += 1;
        searchStats.proposal_patch_tiles_replayed += 1;
        yield placementDelta("add", move, rollback, parentId, {
          proposal_patch_index: descriptor.index
        });
        if (shouldSnapshot()) yield snapshot(parentId);
        if ((replayed & 15) === 0) await tick();
      }
      if (replayed) {
        yield nodeStatus(
          parentId,
          "success",
          `learned patch: +${replayed}`,
          { search_stats: searchStatsSnapshot() }
        );
      }
      return replayed;
    }

    const initialPatchDescriptors = Array.isArray(config.initial_patch?.placements)
      ? config.initial_patch.placements
      : Array.isArray(config.initial_patch)
        ? config.initial_patch
        : [];
    const resolvePatchOrientation = descriptor => {
      const tile = prototiles[descriptor?.prototile_idx ?? 0];
      if (!tile) return null;
      if (descriptor.orientation_id) {
        return tile.unique_orientations.find(item => item.__orientation_id === descriptor.orientation_id) ?? null;
      }
      if (Number.isInteger(descriptor.orientation_index)) {
        return tile.unique_orientations[descriptor.orientation_index] ?? null;
      }
      return tile.unique_orientations[0] ?? null;
    };
    const applyInitialPatch = () => {
      if (!initialPatchDescriptors.length) return;
      searchStats.initial_patch_requested_tiles = initialPatchDescriptors.length;
      const root = initialPatchDescriptors[0];
      const rootOrient = resolvePatchOrientation(root);
      if ((root.prototile_idx ?? 0) !== startMove.prototile_idx || rootOrient !== startMove.orient) {
        throw new Error("The initial patch root does not match the normalized root tile");
      }
      for (let index = 1; index < initialPatchDescriptors.length; index += 1) {
        const descriptor = initialPatchDescriptors[index];
        const prototileIdx = descriptor.prototile_idx ?? 0;
        const tile = prototiles[prototileIdx];
        const orient = resolvePatchOrientation(descriptor);
        if (!tile || !orient || !Array.isArray(descriptor.translation) || descriptor.translation.length !== 3) {
          throw new Error(`Invalid initial patch placement ${index}`);
        }
        const translation = config.initial_patch_relative_to_root === false
          ? descriptor.translation.slice()
          : vecAdd(startMove.translation, descriptor.translation);
        if (tile.is_polycube ? !isPolycubeMoveTranslation(tile, translation) : !translation.every(Number.isInteger)) {
          throw new Error(`Initial patch placement ${index} is off the configured lattice`);
        }
        const move = { prototile_idx: prototileIdx, orient, translation, is_forced: false };
        const sharesFrontierFace = orient.faces.some((_, faceIdx) =>
          state.frontier.has(translatedOrientedFaceKey(orient, faceIdx, translation))
        );
        if (!sharesFrontierFace) {
          throw new Error(`Initial patch placement ${index} is not face-connected to its prefix`);
        }
        const validity = isMoveValid(move);
        if (!validity.ok) {
          throw new Error(`Initial patch placement ${index} is invalid: ${validity.reason ?? "geometry"}`);
        }
        move.occupancy_data = validity.occData;
        applyMove(move, { countWork: false });
      }
      searchStats.initial_patch_applied_tiles = state.placements.length;
      searchStats.initial_patch_base_shell_depth = completeShellDepthStats().complete_shell_depth;
      searchStats.max_live_tiles = Math.max(searchStats.max_live_tiles, state.placements.length);
    };

    applyInitialPatch();
    if (initialPatchDescriptors.length) {
      yield nodeStatus(rootId, "working", `resumed ${state.placements.length}-tile patch`, {
        frontier_stats: frontierStatsWithCandidateCount(),
        search_stats: searchStatsSnapshot()
      });
      yield snapshot(rootId);
      await tick();
    }

    let success = false;
    if (convexEdgeAngleObstruction) {
      tilingEvidence = {
        ...convexEdgeAngleObstruction,
        strategy: tilingStrategy
      };
      yield nodeStatus(rootId, "fail", "Local edge-angle obstruction");
    } else if (tilingStrategy === "translational") {
      success = yield* tryPeriodicTemplatePatch(rootId, { force: true });
      if (!success) {
        yield nodeStatus(rootId, "fail", "No exact translational patch certificate found");
      }
    } else if (tilingStrategy === "isohedral") {
      success = goalMet() || (yield* searchIsohedral(rootId));
    } else if (tilingStrategy === "generic") {
      if (proposalProgram) yield* replayLearnedProposalPatch(rootId);
      success = goalMet() || (yield* search(rootId));
    } else {
      yield* tryPeriodicTemplatePatch(rootId);
      if (!goalMet()) yield* tryIsohedralCoronaSeed(rootId);
      success = goalMet() || (yield* search(rootId));
    }
    if (
      success
      && criterion === "count"
      && tilingStrategy === "generic"
      && config.generic_periodic_certificate === true
      && !tilingEvidence
    ) {
      const template = yield* tryGenericPeriodicCertificate("generic_target_patch");
      if (template) {
        yield nodeStatus(
          rootId,
          "success",
          "GCTS target patch is an exact translational quotient",
          preflightStatusPayload(template)
        );
      }
    }
    // A periodic exact-cover certificate proves an infinite tiling even when the
    // bounded visualization patch did not reach the requested display count.
    success = success || !!(tilingEvidence?.certified && tilingEvidence?.can_tile === true);
    if (
      !success
      && exhaustive
      && !searchIncomplete
      && (
        Number.isFinite(candidateCap)
        || greedyNoBacktrack
        || (usePolicyAgent && !agentExhaustive)
        || (proposalProgram && searchStats.proposal_patch_tiles_replayed > 0)
      )
    ) {
      noteIncompleteSearch();
      searchStats.termination_reason = "configured_branch_pruning";
    }
    if (!success && !searchIncomplete && searchStats.generation_band_deferrals > 0) {
      noteIncompleteSearch();
      searchStats.termination_reason = "generation_band_pruning";
    }
    if (
      !success
      && tilingStrategy === "generic"
      && exhaustive
      && genericGlobalExtensionEnumeration
      && !searchIncomplete
      && !Number.isFinite(candidateCap)
      && !greedyNoBacktrack
      && (!usePolicyAgent || agentExhaustive)
      && !(proposalProgram && searchStats.proposal_patch_tiles_replayed > 0)
      && !tilingEvidence
    ) {
      const restrictedToInitialPatch = searchStats.initial_patch_applied_tiles > 1;
      const usedDeadFacePruning = searchStats.generic_global_zero_face_dead_ends > 0;
      tilingEvidence = criterion === "shell"
        ? {
            kind: restrictedToInitialPatch
              ? "finite_shell_extension_obstruction"
              : usedDeadFacePruning
                ? "finite_extendable_shell_obstruction"
                : "finite_shell_obstruction",
            certified: true,
            can_tile: restrictedToInitialPatch ? null : false,
            strategy: tilingStrategy,
            target_shell_depth: targetVal,
            ...(restrictedToInitialPatch
              ? {
                  initial_patch_tiles: searchStats.initial_patch_applied_tiles,
                  initial_patch_shell_depth: searchStats.initial_patch_base_shell_depth
                }
              : {}),
            model: `face-to-face tiling by the configured ${includeMirrors ? "full lattice isometries" : "proper lattice orientations"}`,
            note: restrictedToInitialPatch
              ? `Exhaustive global face-extension search found no extension of the supplied ${searchStats.initial_patch_applied_tiles}-tile patch completing combinatorial shell ${targetVal}; this does not exclude other shell-${targetVal} patches.`
              : usedDeadFacePruning
                ? `Exhaustive global face-extension search proved that every route toward combinatorial shell ${targetVal} encounters a permanently unfillable exposed face; such a face can never occur in an infinite tiling.`
                : `Exhaustive global face-extension search found no patch completing combinatorial shell ${targetVal} around the normalized root tile.`
          }
        : {
            kind: "finite_patch_obstruction",
            certified: true,
            can_tile: false,
            strategy: tilingStrategy,
            target_tiles: targetVal,
            model: `connected face-to-face tiling by the configured ${includeMirrors ? "full lattice isometries" : "proper lattice orientations"}`,
            note: `Exhaustive global face-extension search found no connected ${targetVal}-tile patch containing the normalized root tile.`
          };
    }
    yield nodeStatus(rootId, success ? "success" : "fail");
    const terminalSnapshot = snapshot(null);
    const retainBestEffortSnapshot = tilingStrategy !== "isohedral";
    const finalSnapshot = retainBestEffortSnapshot
      && bestSnapshot
      && isBetterSnapshot(bestSnapshot, terminalSnapshot)
      ? {
          ...cloneSnapshot(bestSnapshot),
          node_id: null,
          // Keep the best geometry for inspection, but never roll terminal
          // counters and stop reasons back to the moment that patch appeared.
          search_stats: terminalSnapshot.search_stats
        }
      : terminalSnapshot;
    yield finalSnapshot;
    await tick();
    if (success && criterion === "region") {
      tilingEvidence = {
        kind: "exact_region_fill",
        certified: true,
        strategy: tilingStrategy,
        region_type: targetRegion?.type ?? null,
        placed_volume: state.placed_volume,
        target_volume: targetRegion?.volume ?? null
      };
    } else if (success && !tilingEvidence) {
      tilingEvidence = {
        kind: criterion === "shell" ? "finite_complete_shell" : "finite_patch",
        certified: false,
        strategy: tilingStrategy,
        ...(criterion === "shell" ? { completed_shell_depth: targetVal } : {}),
        note: criterion === "shell"
          ? "A complete finite combinatorial shell is necessary for a face-to-face space tiling, but is not sufficient to prove one."
          : "A locally legal finite patch is not a proof that all of 3-space can be tiled."
      };
    }
    const provenImpossible = tilingEvidence?.can_tile === false || (
      !success
      && criterion === "region"
      && exhaustive
      && !searchIncomplete
    );
    const extensionImpossible = tilingEvidence?.kind === "finite_shell_extension_obstruction";
    const resultKind = provenImpossible
      ? "no_tiling"
      : extensionImpossible
        ? "patch_extension_impossible"
      : tilingEvidence?.certified
        ? "certified_tiling"
      : success
        ? "patch_found"
        : provenImpossible
          ? "no_tiling"
          : searchIncomplete
            ? "search_incomplete"
            : "no_tiling_found";
    yield {
      type: "finished",
      tile_count: finalSnapshot.tile_count,
      search_stats: finalSnapshot.search_stats,
      success,
      best_effort: !success && (finalSnapshot.tile_count ?? 0) > state.placements.length,
      result_kind: resultKind,
      tiling_evidence: tilingEvidence,
      can_tile: tilingEvidence?.can_tile === null
        ? null
        : typeof tilingEvidence?.can_tile === "boolean"
        ? tilingEvidence.can_tile
        : tilingEvidence?.certified
          ? true
          : provenImpossible
            ? false
            : null,
      search_incomplete: searchIncomplete
    };
  };
})();

export const tileSpecs = (() => {
  const SCALE = 1;
  const POLYCUBE_REFINED_COORD_SCALE = 2;
  const POLYCUBE_SOLID_ANGLE_MAX = 8;
  let activePolycubeLattice = "z3";
  const normalizePolycubeLattice = (value) => {
    const key = String(value ?? "").toLowerCase();
    if (key === "fcc" || key === "d3") return "fcc";
    if (key === "half" || key === "half-z3" || key === "z3/2") return "half";
    return "z3";
  };
  const withPolycubeLattice = (lattice, builder) => {
    const previous = activePolycubeLattice;
    activePolycubeLattice = normalizePolycubeLattice(lattice);
    try {
      return builder();
    } finally {
      activePolycubeLattice = previous;
    }
  };
  const LEGACY_SOLID_ANGLE_MAX = 48;

  const BASE_COLOR_PALETTE = [
    "#e74c3c","#3498db","#f1c40f","#2ecc71","#9b59b6",
    "#e67e22","#1abc9c","#34495e","#d35400","#7f8c8d"
  ];
  const BASE_COLOR_PALETTE_SIZE = BASE_COLOR_PALETTE.length;
  const TRANSLATIONAL_CELL_COLOR_OFFSET = BASE_COLOR_PALETTE.length;
  const TRANSLATIONAL_CELL_COLORS = BASE_COLOR_PALETTE.flatMap(baseColor => {
    const baseChannels = [1, 3, 5].map(index =>
      Number.parseInt(baseColor.slice(index, index + 2), 16)
    );
    return Array.from({ length: 8 }, (_, parityIndex) => {
      const channels = baseChannels.map((channel, axis) =>
        (channel + 128 * ((parityIndex >> axis) & 1)) % 256
      );
      return `#${channels.map(channel => channel.toString(16).padStart(2, "0")).join("")}`;
    });
  });
  const COLOR_PALETTE = [...BASE_COLOR_PALETTE, ...TRANSLATIONAL_CELL_COLORS];

  // --- Z^3 lattice signed-permutation isometries: all 48 (det = ±1)
  const Z3_MATRICES_ALL = (() => {
    const perms = (arr) => {
      if (arr.length <= 1) return [arr.slice()];
      const out = [];
      for (let i = 0; i < arr.length; i++) {
        const rest = arr.slice(0, i).concat(arr.slice(i + 1));
        for (const p of perms(rest)) out.push([arr[i], ...p]);
      }
      return out;
    };

    const det3 = (M) =>
      M[0][0]*(M[1][1]*M[2][2]-M[1][2]*M[2][1]) -
      M[0][1]*(M[1][0]*M[2][2]-M[1][2]*M[2][0]) +
      M[0][2]*(M[1][0]*M[2][1]-M[1][1]*M[2][0]);

    const mats = [];
    for (const p of perms([0,1,2])) {
      const P = [[0,0,0],[0,0,0],[0,0,0]];
      for (let i = 0; i < 3; i++) P[i][p[i]] = 1;

      for (const sx of [-1,1]) for (const sy of [-1,1]) for (const sz of [-1,1]) {
        const S = [[sx,0,0],[0,sy,0],[0,0,sz]];
        const M = [
          [P[0][0]*S[0][0] + P[0][1]*S[1][0] + P[0][2]*S[2][0],
           P[0][0]*S[0][1] + P[0][1]*S[1][1] + P[0][2]*S[2][1],
           P[0][0]*S[0][2] + P[0][1]*S[1][2] + P[0][2]*S[2][2]],
          [P[1][0]*S[0][0] + P[1][1]*S[1][0] + P[1][2]*S[2][0],
           P[1][0]*S[0][1] + P[1][1]*S[1][1] + P[1][2]*S[2][1],
           P[1][0]*S[0][2] + P[1][1]*S[1][2] + P[1][2]*S[2][2]],
          [P[2][0]*S[0][0] + P[2][1]*S[1][0] + P[2][2]*S[2][0],
           P[2][0]*S[0][1] + P[2][1]*S[1][1] + P[2][2]*S[2][1],
           P[2][0]*S[0][2] + P[2][1]*S[1][2] + P[2][2]*S[2][2]],
        ];
        const det = det3(M);
        mats.push({ M, det });
      }
    }
    return mats;
  })();

  const Z3_MATRICES_DET1 = Z3_MATRICES_ALL.filter(x => x.det === 1);

  const add3 = (a,b) => [a[0]+b[0], a[1]+b[1], a[2]+b[2]];
  const sub3 = (a,b) => [a[0]-b[0], a[1]-b[1], a[2]-b[2]];
  const dot3 = (a,b) => a[0]*b[0] + a[1]*b[1] + a[2]*b[2];
  const cross3 = (a,b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
  const norm3 = (a) => Math.sqrt(dot3(a, a));
  const normalize3 = (a) => {
    const n = norm3(a);
    return n === 0 ? a : [a[0]/n, a[1]/n, a[2]/n];
  };

  // Generic function to compute solid angle of a cone spanned by three vectors
  const computeSolidAngle = (v1, v2, v3) => {
    const u = normalize3(v1);
    const v = normalize3(v2);
    const w = normalize3(v3);
    const triple = dot3(u, cross3(v, w));
    const uv = dot3(u, v);
    const vw = dot3(v, w);
    const wu = dot3(w, u);
    const denom = 1 + uv + vw + wu;
    const omega = 2 * Math.atan2(Math.abs(triple), denom);
    return Math.abs(omega) < 1e-12 ? 0 : omega;
  };

  const computeDihedralAngle = (v1, v2, v3, v4) => {
    const a = sub3(v3, v1);
    const b = sub3(v2, v1);
    const c = sub3(v4, v1);
    const n1 = cross3(a, b);
    const n2 = cross3(b, c);
    const n1_norm = norm3(n1);
    const n2_norm = norm3(n2);
    if (n1_norm < 1e-12 || n2_norm < 1e-12) return 0;
    const cosAngle = dot3(n1, n2) / (n1_norm * n2_norm);
    const clampedCos = Math.max(-1, Math.min(1, cosAngle));
    const angle = Math.acos(clampedCos);
    return Math.PI - angle;
  };

  const computeNormalizedAngleWeight = (angle, fullAngle, maxValue = LEGACY_SOLID_ANGLE_MAX) => {
    // Preserve the measured angle unless it is genuinely an integer count on
    // maxValue. Earlier versions rounded every vertex/edge assignment, which
    // made some non-rational solid angles look like exact lattice fractions.
    const exact = (angle / fullAngle) * maxValue;
    const rounded = Math.round(exact);
    return Math.abs(exact - rounded) < 1e-9 ? rounded : exact;
  };

  const getTetrahedronWeights = () => {
    const verts = [[0,0,0],[1,1,0],[1,0,1],[0,1,1]];
    const v0 = verts[0];
    const v1 = sub3(verts[1], v0);
    const v2 = sub3(verts[2], v0);
    const v3 = sub3(verts[3], v0);
    const solidAngle = computeSolidAngle(v1, v2, v3);
    const dihedralAngle = computeDihedralAngle(verts[0], verts[1], verts[2], verts[3]);
    const fullSphere = 4 * Math.PI;
    const fullCircle = 2 * Math.PI;
    return {
      vertexWeight: computeNormalizedAngleWeight(solidAngle, fullSphere),
      edgeWeight: computeNormalizedAngleWeight(dihedralAngle, fullCircle),
      faceWeight: 24,
      interiorWeight: LEGACY_SOLID_ANGLE_MAX
    };
  };

  const getTetragonalDisphenoidWeights = () => {
    const verts = [[0,0,1],[0,0,-1],[1,1,0],[1,-1,0]];
    const v0 = verts[0];
    const v1 = sub3(verts[1], v0);
    const v2 = sub3(verts[2], v0);
    const v3 = sub3(verts[3], v0);
    const solidAngle = computeSolidAngle(v1, v2, v3);
    const longDihedral = computeDihedralAngle(verts[0], verts[1], verts[2], verts[3]);
    const shortDihedral = computeDihedralAngle(verts[0], verts[2], verts[1], verts[3]);
    const fullSphere = 4 * Math.PI;
    const fullCircle = 2 * Math.PI;
    return {
      vertexWeight: computeNormalizedAngleWeight(solidAngle, fullSphere),
      longEdgeWeight: computeNormalizedAngleWeight(longDihedral, fullCircle),
      shortEdgeWeight: computeNormalizedAngleWeight(shortDihedral, fullCircle),
      faceWeight: 24,
      interiorWeight: LEGACY_SOLID_ANGLE_MAX
    };
  };

  const computeTetrahedronWeights = (verts, isTetragonalDisphenoid = false) => {
    if (isTetragonalDisphenoid) return getTetragonalDisphenoidWeights();
    return getTetrahedronWeights();
  };

  const computeHullFaces = (verts) => {
    const pts = verts.map(v => v.slice());
    const N = pts.length;
    const sum = pts.reduce((acc,v)=>add3(acc,v), [0,0,0]);
    const faces = [];
    const seen = new Set();

    for (let i=0;i<N;i++) for (let j=i+1;j<N;j++) for (let k=j+1;k<N;k++) {
      const p1 = pts[i], p2 = pts[j], p3 = pts[k];
      const n = cross3(sub3(p2,p1), sub3(p3,p1));
      if (n[0]===0 && n[1]==0 && n[2]===0) continue;
      const Np1_minus_sum = sub3([N*p1[0],N*p1[1],N*p1[2]], sum);
      let nn = n;
      if (dot3(nn, Np1_minus_sum) < 0) nn = [-nn[0],-nn[1],-nn[2]];

      let ok = true;
      const onPlane = [];
      for (let m=0;m<N;m++) {
        const d = dot3(sub3(pts[m], p1), nn);
        if (d > 0) { ok = false; break; }
        if (d === 0) onPlane.push(m);
      }
      if (!ok || onPlane.length < 3) continue;

      const facePts = onPlane.map(idx => pts[idx]);
      const c = facePts.reduce((acc,v)=>add3(acc,v), [0,0,0]).map(x => x / facePts.length);
      const nz = (() => {
        const len = Math.sqrt(nn[0]*nn[0]+nn[1]*nn[1]+nn[2]*nn[2]);
        return [nn[0]/len, nn[1]/len, nn[2]/len];
      })();
      let xax = sub3(facePts[0].map(Number), c);
      const xlen = Math.sqrt(xax[0]*xax[0]+xax[1]*xax[1]+xax[2]*xax[2]) || 1;
      xax = [xax[0]/xlen, xax[1]/xlen, xax[2]/xlen];
      const yax = cross3(nz, xax);

      const withAng = onPlane.map((idx) => {
        const v = sub3(pts[idx].map(Number), c);
        const ang = Math.atan2(dot3(v, yax), dot3(v, xax));
        return { idx, ang };
      }).sort((a,b)=>a.ang-b.ang);

      const ordered = withAng.map(o => o.idx);
      const h = ordered.slice().sort((a,b)=>a-b).join(",");
      if (!seen.has(h)) {
        seen.add(h);
        faces.push(ordered);
      }
    }
    return faces;
  };

  const computeTetrahedronOccupancy = (vertsScaled, faces, isTetragonalDisphenoid = false) => {
    const unitVerts = vertsScaled.map(v => [v[0]/SCALE, v[1]/SCALE, v[2]/SCALE]);
    const fullSphere = 4 * Math.PI;
    const fullCircle = 2 * Math.PI;
    const vertexWeights = unitVerts.map((vertex, index) => {
      const others = unitVerts.filter((_, otherIndex) => otherIndex !== index).map(other => sub3(other, vertex));
      return computeNormalizedAngleWeight(computeSolidAngle(others[0], others[1], others[2]), fullSphere);
    });
    const edgeWeight = (i, j) => {
      const opposite = [0, 1, 2, 3].filter(index => index !== i && index !== j);
      return computeNormalizedAngleWeight(computeDihedralAngle(unitVerts[i], unitVerts[j], unitVerts[opposite[0]], unitVerts[opposite[1]]), fullCircle);
    };

    const minB = [Infinity, Infinity, Infinity];
    const maxB = [-Infinity, -Infinity, -Infinity];
    for (const v of vertsScaled) {
      for (let i = 0; i < 3; i++) {
        minB[i] = Math.min(minB[i], v[i]);
        maxB[i] = Math.max(maxB[i], v[i]);
      }
    }

    const occ = [];
    const vertKeyToIndex = new Map(vertsScaled.map((v, index) => [v.join(','), index]));
    const edgeMidpointWeights = new Map();
    for (let i = 0; i < vertsScaled.length; i++) {
      for (let j = i + 1; j < vertsScaled.length; j++) {
        const mid = [
          (vertsScaled[i][0] + vertsScaled[j][0]) / 2,
          (vertsScaled[i][1] + vertsScaled[j][1]) / 2,
          (vertsScaled[i][2] + vertsScaled[j][2]) / 2
        ];
        if (mid.every(Number.isInteger)) edgeMidpointWeights.set(mid.join(','), edgeWeight(i, j));
      }
    }

    for (let x = minB[0]; x <= maxB[0]; x++) {
      for (let y = minB[1]; y <= maxB[1]; y++) {
        for (let z = minB[2]; z <= maxB[2]; z++) {
          const p = [x, y, z];
          const key = p.join(',');

          if (vertKeyToIndex.has(key)) {
            occ.push([p, vertexWeights[vertKeyToIndex.get(key)], null, null, "vertex"]);
            continue;
          }

          if (edgeMidpointWeights.has(key)) {
            occ.push([p, edgeMidpointWeights.get(key), null, null, "edge"]);
            continue;
          }

          const EPS = 1e-7;
          const pu = [p[0]/SCALE, p[1]/SCALE, p[2]/SCALE];
          const [v0, v1, v2, v3] = unitVerts;

          const v0v1 = sub3(v1, v0);
          const v0v2 = sub3(v2, v0);
          const v0v3 = sub3(v3, v0);
          const v0p = sub3(pu, v0);

          const d00 = dot3(v0v1, v0v1);
          const d01 = dot3(v0v1, v0v2);
          const d02 = dot3(v0v1, v0v3);
          const d03 = dot3(v0v1, v0p);
          const d11 = dot3(v0v2, v0v2);
          const d12 = dot3(v0v2, v0v3);
          const d13 = dot3(v0v2, v0p);
          const d22 = dot3(v0v3, v0v3);
          const d23 = dot3(v0v3, v0p);

          const denom = d00 * (d11 * d22 - d12 * d12) -
                       d01 * (d01 * d22 - d12 * d02) +
                       d02 * (d01 * d12 - d11 * d02);

          if (Math.abs(denom) < 1e-12) continue;

          const invDenom = 1 / denom;
          const u = (d11 * d22 - d12 * d12) * d03 - (d01 * d22 - d12 * d02) * d13 + (d01 * d12 - d11 * d02) * d23;
          const v = -(d01 * d22 - d12 * d02) * d03 + (d00 * d22 - d02 * d02) * d13 - (d00 * d12 - d01 * d02) * d23;
          const w = (d01 * d12 - d11 * d02) * d03 - (d00 * d12 - d01 * d02) * d13 + (d00 * d11 - d01 * d01) * d23;

          const baryU = u * invDenom;
          const baryV = v * invDenom;
          const baryW = w * invDenom;
          const baryT = 1 - baryU - baryV - baryW;

          if (baryU > -EPS && baryV > -EPS && baryW > -EPS && baryT > -EPS &&
              baryU < 1+EPS && baryV < 1+EPS && baryW < 1+EPS && baryT < 1+EPS) {
            const nearZero = [baryU, baryV, baryW, baryT].filter(value => Math.abs(value) < EPS).length;
            if (nearZero === 1) occ.push([p, LEGACY_SOLID_ANGLE_MAX / 2, null, null, "face"]);
            else if (nearZero === 0) occ.push([p, LEGACY_SOLID_ANGLE_MAX, null, null, "interior"]);
          }
        }
      }
    }
    return occ;
  };

  const triangleSolidAngle = (a, b, c) => {
    const la = norm3(a), lb = norm3(b), lc = norm3(c);
    if (la < 1e-12 || lb < 1e-12 || lc < 1e-12) return 0;
    const numerator = dot3(a, cross3(b, c));
    const denominator = la * lb * lc + dot3(a, b) * lc + dot3(b, c) * la + dot3(c, a) * lb;
    return 2 * Math.atan2(numerator, denominator);
  };

  const orientConvexFaces = (verts, faces) => {
    const center = verts.reduce((acc, v) => add3(acc, v), [0, 0, 0]).map(value => value / verts.length);
    return faces.map(face => {
      if (face.length < 3) return face.slice();
      const a = verts[face[0]], b = verts[face[1]], c = verts[face[2]];
      const normal = cross3(sub3(b, a), sub3(c, a));
      return dot3(normal, sub3(center, a)) > 0 ? face.slice().reverse() : face.slice();
    });
  };

  const convexPlanes = (verts, faces) => {
    const oriented = orientConvexFaces(verts, faces);
    return oriented
      .filter(face => face.length >= 3)
      .map(face => {
        const a = verts[face[0]], b = verts[face[1]], c = verts[face[2]];
        const n = cross3(sub3(b, a), sub3(c, a));
        return { face, n, d: dot3(n, a) };
      });
  };

  const pointInConvexPolyhedron = (point, planes, eps = 1e-9) => {
    for (const plane of planes) {
      if (dot3(plane.n, point) - plane.d > eps) return false;
    }
    return true;
  };

  const convexSolidAngleAtPoint = (point, verts, orientedFaces, center, planes) => {
    const activeNormals = planes
      .filter(plane => Math.abs(dot3(plane.n, point) - plane.d) < 1e-9)
      .map(plane => normalize3(plane.n));
    let nudged = point.slice();
    if (activeNormals.length) {
      const outward = normalize3(activeNormals.reduce((sum, n) => add3(sum, n), [0, 0, 0]));
      nudged = point.map((value, axis) => value + outward[axis] * 1e-6);
    }
    let omega = 0;
    for (const face of orientedFaces) {
      if (face.length < 3) continue;
      const base = sub3(verts[face[0]], nudged);
      for (let i = 1; i < face.length - 1; i++) {
        omega += triangleSolidAngle(
          base,
          sub3(verts[face[i]], nudged),
          sub3(verts[face[i + 1]], nudged)
        );
      }
    }
    return Math.abs(omega);
  };

  const vertexConeSolidAngle = (point, verts, planes) => {
    const activeAtPoint = planes.filter(plane => Math.abs(dot3(plane.n, point) - plane.d) < 1e-9);
    const rays = [];
    const seen = new Set();
    for (const vertex of verts) {
      const delta = sub3(vertex, point);
      const length = norm3(delta);
      if (length < 1e-9) continue;
      const sharedPlanes = activeAtPoint.filter(plane => Math.abs(dot3(plane.n, vertex) - plane.d) < 1e-9).length;
      if (sharedPlanes < 2) continue;
      const ray = delta.map(value => value / length);
      const key = ray.map(value => Math.round(value * 1e9)).join(",");
      if (seen.has(key)) continue;
      seen.add(key);
      rays.push(ray);
    }
    if (rays.length < 3) return null;
    const axis = normalize3(rays.reduce((sum, ray) => add3(sum, ray), [0, 0, 0]));
    if (norm3(axis) < 1e-9) return null;
    let basisU = cross3(axis, [1, 0, 0]);
    if (norm3(basisU) < 1e-9) basisU = cross3(axis, [0, 1, 0]);
    basisU = normalize3(basisU);
    const basisV = normalize3(cross3(axis, basisU));
    const ordered = rays
      .map(ray => ({ ray, angle: Math.atan2(dot3(ray, basisV), dot3(ray, basisU)) }))
      .sort((a, b) => a.angle - b.angle)
      .map(item => item.ray);
    let omega = 0;
    for (let i = 0; i < ordered.length; i++) {
      omega += computeSolidAngle(axis, ordered[i], ordered[(i + 1) % ordered.length]);
    }
    return Math.abs(omega);
  };

  const computeConvexOccupancy = (verts, faces, maxValue = LEGACY_SOLID_ANGLE_MAX) => {
    const minB = [Infinity, Infinity, Infinity];
    const maxB = [-Infinity, -Infinity, -Infinity];
    for (const v of verts) for (let i = 0; i < 3; i++) {
      minB[i] = Math.min(minB[i], v[i]);
      maxB[i] = Math.max(maxB[i], v[i]);
    }
    const orientedFaces = orientConvexFaces(verts, faces);
    const planes = convexPlanes(verts, orientedFaces);
    const center = verts.reduce((acc, v) => add3(acc, v), [0, 0, 0]).map(value => value / verts.length);
    const occ = [];
    for (let x = Math.ceil(minB[0]); x <= Math.floor(maxB[0]); x++) {
      for (let y = Math.ceil(minB[1]); y <= Math.floor(maxB[1]); y++) {
        for (let z = Math.ceil(minB[2]); z <= Math.floor(maxB[2]); z++) {
          const p = [x, y, z];
          if (!pointInConvexPolyhedron(p, planes)) continue;
          const active = planes.filter(plane => Math.abs(dot3(plane.n, p) - plane.d) < 1e-9);
          let weight;
          let kind;
          if (active.length === 0) {
            weight = maxValue;
            kind = "interior";
          } else if (active.length === 1) {
            weight = maxValue / 2;
            kind = "face";
          } else if (active.length === 2) {
            const n0 = normalize3(active[0].n);
            const n1 = normalize3(active[1].n);
            const cos = Math.max(-1, Math.min(1, dot3(n0, n1)));
            weight = computeNormalizedAngleWeight(Math.PI - Math.acos(cos), 2 * Math.PI, maxValue);
            kind = "edge";
          } else {
            const omega = vertexConeSolidAngle(p, verts, planes) ?? convexSolidAngleAtPoint(p, verts, orientedFaces, center, planes);
            weight = Math.max(1, Math.min(maxValue, computeNormalizedAngleWeight(omega, 4 * Math.PI, maxValue)));
            kind = "vertex";
          }
          if (weight > 0) occ.push([p, weight, null, null, kind]);
        }
      }
    }
    return occ;
  };

  const createScaledTileData = (unitVerts, faceTemplate, autoHull=false, isTetragonalDisphenoid=false) => {
    const vertsScaled = unitVerts.map(v => v.map(c => Math.round(c * SCALE)));
    const rawFaces = autoHull ? computeHullFaces(vertsScaled) : faceTemplate.map(f => f.v.slice());
    const faces = orientConvexFaces(vertsScaled, rawFaces);
    const faceData = autoHull
      ? faces.map(f => ({ v: f, type: "default" }))
      : faces.map((face, index) => ({ v: face, type: faceTemplate[index].type }));
    let occ;
    if (unitVerts.length === 4 && faceTemplate.length === 4 && faceTemplate.every(f => f.v.length === 3)) {
      occ = computeTetrahedronOccupancy(vertsScaled, faces, isTetragonalDisphenoid);
    } else {
      occ = computeConvexOccupancy(vertsScaled, faceData.map(f => f.v));
    }
    return { v: vertsScaled, f_data: faceData, occ, skip_winding: false, solid_angle: { kind: "rational", max_value: LEGACY_SOLID_ANGLE_MAX } };
  };

  const generatePolycubeData = (voxels, options = {}) => {
    const lattice = normalizePolycubeLattice(options.polycube_lattice ?? activePolycubeLattice);
    const useRefinedCoords = lattice !== "z3";
    const polycubeCoordScale = useRefinedCoords ? POLYCUBE_REFINED_COORD_SCALE : 1;
    const voxelSet = new Set(voxels.map(v => v.map(Number).join(",")));
    const vox = voxels.map(v => v.map(Number));
    const uniqueVerts = new Set();
    for (const v of vox) {
      for (const dx of [0,1]) for (const dy of [0,1]) for (const dz of [0,1]) {
        uniqueVerts.add([v[0]+dx, v[1]+dy, v[2]+dz].join(","));
      }
    }
    const vertsList = [...uniqueVerts].map(s => s.split(",").map(Number))
      .sort((a,b)=>a[0]-b[0]||a[1]-b[1]||a[2]-b[2]);
    const vertMap = new Map(vertsList.map((v,i)=>[v.join(","), i]));
    const faceDefs = [
      [[ 1,0,0],  [[1,0,0],[1,1,0],[1,1,1],[1,0,1]]],
      [[-1,0,0],  [[0,0,0],[0,0,1],[0,1,1],[0,1,0]]],
      [[ 0,1,0],  [[0,1,0],[0,1,1],[1,1,1],[1,1,0]]],
      [[ 0,-1,0], [[0,0,0],[1,0,0],[1,0,1],[0,0,1]]],
      [[ 0,0,1],  [[0,0,1],[1,0,1],[1,1,1],[0,1,1]]],
      [[ 0,0,-1], [[0,0,0],[0,1,0],[1,1,0],[1,0,0]]],
    ];
    const faces = [];
    for (const v of vox) {
      const [vx,vy,vz] = v;
      for (const [nrm, deltas] of faceDefs) {
        const nb = [vx+nrm[0], vy+nrm[1], vz+nrm[2]].join(",");
        if (!voxelSet.has(nb)) {
          const idxs = deltas.map(([dx,dy,dz]) => vertMap.get([vx+dx,vy+dy,vz+dz].join(",")));
          faces.push(idxs);
        }
      }
    }
    const scaledVerts = vertsList.map(v => v.map(c => Math.round(c * polycubeCoordScale * SCALE)));
    const occ = new Map();
    const addOcc = (pos, weight) => {
      const key = pos.map(c => Math.round(c * polycubeCoordScale * SCALE)).join(",");
      occ.set(key, (occ.get(key) ?? 0) + weight);
    };
    for (const v of vox) {
      const [x, y, z] = v;
      if (lattice === "half") {
        for (const dx of [0, 0.5, 1]) for (const dy of [0, 0.5, 1]) for (const dz of [0, 0.5, 1]) {
          const halfCount = (dx === 0.5 ? 1 : 0) + (dy === 0.5 ? 1 : 0) + (dz === 0.5 ? 1 : 0);
          addOcc([x + dx, y + dy, z + dz], 2 ** halfCount);
        }
      } else {
        for (const dx of [0,1]) for (const dy of [0,1]) for (const dz of [0,1]) {
          addOcc([x + dx, y + dy, z + dz], 1);
        }
      }
      if (lattice === "fcc") {
        for (const fixed of [0, 1]) {
          addOcc([x + fixed, y + 0.5, z + 0.5], 4);
          addOcc([x + 0.5, y + fixed, z + 0.5], 4);
          addOcc([x + 0.5, y + 0.5, z + fixed], 4);
        }
      }
    }
    const polycubeKind = (weight) => {
      if (weight >= POLYCUBE_SOLID_ANGLE_MAX) return "interior";
      if (weight >= 4) return "face";
      if (weight >= 2) return "edge";
      return "vertex";
    };
    const occList = [...occ.entries()].map(([k,weight]) => [k.split(",").map(Number), weight, null, null, polycubeKind(weight)]);
    const faceData = faces.map(f => ({ v: f.slice(), type: "default" }));
    return { v: scaledVerts, f_data: faceData, occ: occList, skip_winding: true, polycube_lattice: lattice, solid_angle: { kind: "rational", max_value: POLYCUBE_SOLID_ANGLE_MAX } };
  };

  class Prototile3D {
    constructor(name, vertices, face_data, occupancy_map, skip_winding=false, is_mirror=false, solid_angle={ kind: "rational", max_value: LEGACY_SOLID_ANGLE_MAX }, metadata = {}) {
      this.name = name;
      this.is_mirror = is_mirror;
      this.verts = vertices.map(v => v.slice());
      this.faces = face_data.map(f => f.v.slice());
      this.face_types = face_data.map(f => f.type);
      this.occupancy_points = (occupancy_map || []).map(([pt,w,symbolic,display_symbolic,kind]) => ({ pos: pt.slice(), weight: w, symbolic, display_symbolic, kind }));
      this.solid_angle = { kind: solid_angle.kind ?? "numeric", max_value: solid_angle.max_value ?? LEGACY_SOLID_ANGLE_MAX, symbols: [...(solid_angle.symbols ?? [])] };
      this.polycube_lattice = metadata.polycube_lattice ?? null;
      this.is_polycube = this.solid_angle.max_value === POLYCUBE_SOLID_ANGLE_MAX;
      if (!skip_winding) this._fixWinding();
      this.unique_orientations = [];
      this.is_chiral = false;
      this._calcSymmetries();
      if (!is_mirror) this._checkChirality();
    }
    _fixWinding() {
      const inside = [
        this.verts.reduce((s,v)=>s+v[0],0)/this.verts.length,
        this.verts.reduce((s,v)=>s+v[1],0)/this.verts.length,
        this.verts.reduce((s,v)=>s+v[2],0)/this.verts.length,
      ];
      const newFaces = [];
      for (const f of this.faces) {
        if (f.length < 3) { newFaces.push(f); continue; }
        const v0 = this.verts[f[0]], v1 = this.verts[f[1]], v2 = this.verts[f[2]];
        let n = cross3(sub3(v1,v0), sub3(v2,v0));
        const inward = sub3(inside, v0);
        if (dot3(n, inward) > 0) newFaces.push(f.slice().reverse());
        else newFaces.push(f.slice());
      }
      this.faces = newFaces;
    }
    _calcSymmetries() {
      const mul = (M,v) => ([
        M[0][0]*v[0]+M[0][1]*v[1]+M[0][2]*v[2],
        M[1][0]*v[0]+M[1][1]*v[1]+M[1][2]*v[2],
        M[2][0]*v[0]+M[2][1]*v[1]+M[2][2]*v[2],
      ]);
      const buildFrom = (matList) => {
        const seen = new Set();
        const out = [];
        for (let iso_idx = 0; iso_idx < matList.length; iso_idx++) {
          const { M, det } = matList[iso_idx];
          let tVerts = this.verts.map(v => mul(M,v));
          const shift = [Infinity,Infinity,Infinity];
          for (const v of tVerts) for (let i=0;i<3;i++) shift[i]=Math.min(shift[i], v[i]);
          tVerts = tVerts.map(v => [v[0]-shift[0], v[1]-shift[1], v[2]-shift[2]]);
          const vIndex = new Map(tVerts.map((v,i)=>[v.join(","), i]));
          const tOcc = this.occupancy_points.map(pt => {
            const mp = mul(M, pt.pos);
            return { pos: [mp[0]-shift[0], mp[1]-shift[1], mp[2]-shift[2]], weight: pt.weight, symbolic: pt.symbolic, display_symbolic: pt.display_symbolic, kind: pt.kind };
          });
          const newFaces = [];
          const newFaceTypes = [];
          for (let fi = 0; fi < this.faces.length; fi++) {
            const face = this.faces[fi];
            const mapped = face.map(oldIdx => {
              const mv = mul(M, this.verts[oldIdx]);
              const key = [mv[0]-shift[0], mv[1]-shift[1], mv[2]-shift[2]].join(",");
              return vIndex.get(key);
            });
            const fixed = (det === -1) ? mapped.slice().reverse() : mapped;
            newFaces.push(fixed);
            newFaceTypes.push(this.face_types[fi]);
          }
          const vHash = tVerts.map(v=>v.join(",")).sort().join("|");
          const oHash = tOcc.map(p=>`${p.pos.join(",")}:${p.weight}`).sort().join("|");
          const fHash = newFaces.map(f => f.slice().sort((a,b)=>a-b).join(",")).sort().join("|");
          const geomHash = `${vHash}@@${oHash}@@${fHash}`;
          if (seen.has(geomHash)) continue;
          seen.add(geomHash);
          out.push({
            iso_idx,
            det,
            __mark_matrix: M.map(row => row.slice()),
            __mark_shift: shift.slice(),
            verts: tVerts,
            faces: newFaces,
            face_types: newFaceTypes,
            occupancy: tOcc,
            vertsForFace: (fIdx) => fIdx.map(i => tVerts[i])
          });
        }
        return out;
      };
      this.orientations24 = buildFrom(Z3_MATRICES_DET1);
      this.unique_orientations = this.orientations24;
    }
    _checkChirality() {
      const mirror = this.verts.map(v => [-v[0], v[1], v[2]]);
      const minv = [Infinity,Infinity,Infinity];
      for (const v of mirror) for (let i=0;i<3;i++) minv[i]=Math.min(minv[i], v[i]);
      const tVerts = mirror.map(v => sub3(v, minv));
      const tOcc = this.occupancy_points.map(pt => ({ pos: sub3([-pt.pos[0], pt.pos[1], pt.pos[2]], minv), weight: pt.weight, symbolic: pt.symbolic, display_symbolic: pt.display_symbolic, kind: pt.kind }));
      const vHash = tVerts.map(v=>v.join(",")).sort().join("|");
      const oHash = tOcc.map(p=>`${p.pos.join(",")}:${p.weight}`).sort().join("|");
      const mirrorHash = `${vHash}@@${oHash}`;
      const baseNoFaces = new Set();
      for (const o of this.unique_orientations) {
        const vh = o.verts.map(v=>v.join(",")).sort().join("|");
        const oh = o.occupancy.map(p=>`${p.pos.join(",")}:${p.weight}`).sort().join("|");
        baseNoFaces.add(`${vh}@@${oh}`);
      }
      this.is_chiral = !baseNoFaces.has(mirrorHash);
    }
    rescaleOccupancyWeights(targetMax) {
      const sourceMax = this.solid_angle?.max_value ?? LEGACY_SOLID_ANGLE_MAX;
      if (targetMax === sourceMax) return;
      const scale = targetMax / sourceMax;
      const convert = (weight) => {
        const scaled = weight * scale;
        const rounded = Math.round(scaled);
        return Math.abs(scaled - rounded) < 1e-9 ? rounded : scaled;
      };
      this.occupancy_points = this.occupancy_points.map(pt => ({ ...pt, weight: convert(pt.weight) }));
      for (const orient of this.unique_orientations ?? []) {
        orient.occupancy = orient.occupancy.map(pt => ({ ...pt, weight: convert(pt.weight) }));
      }
      this.solid_angle = { ...this.solid_angle, max_value: targetMax };
    }
    get_mirror_copy() {
      if (!this.is_chiral) return null;
      const mirrorVerts = this.verts.map(v => [-v[0], v[1], v[2]]);
      const minv = [Infinity,Infinity,Infinity];
      for (const v of mirrorVerts) for (let i=0;i<3;i++) minv[i]=Math.min(minv[i], v[i]);
      const tVerts = mirrorVerts.map(v => sub3(v, minv));
      const mirrorOcc = this.occupancy_points.map(p => [sub3([-p.pos[0],p.pos[1],p.pos[2]], minv), p.weight, p.symbolic, p.display_symbolic, p.kind]);
      const faceData = this.faces.map((f,i)=>({ v: f.slice(), type: this.face_types[i] }));
      return new Prototile3D(`reflected ${this.name}`, tVerts, faceData, mirrorOcc, false, true, this.solid_angle, { polycube_lattice: this.polycube_lattice });
    }
  }

  const make_tile = (name, data) => {
    return new Prototile3D(name, data.v, data.f_data, data.occ, !!data.skip_winding, false, data.solid_angle, { polycube_lattice: data.polycube_lattice });
  };

  const withSymbolicSolidAngles = (occ, rules) => occ.map(([pos, weight, _symbol, _display, kind]) => {
    const symbolic = rules(weight, kind);
    return [pos, weight, symbolic?.symbol ?? symbolic, symbolic?.display ?? symbolic, kind];
  });

  const gen_tetrahedron_data = () => {
    const verts = [[0,0,0],[1,1,0],[1,0,1],[0,1,1]];
    const data = createScaledTileData(
      verts,
      [ { v:[0,1,2], type:"default" }, { v:[0,2,3], type:"default" }, { v:[0,3,1], type:"default" }, { v:[1,3,2], type:"default" } ],
      false, false
    );
    data.occ = withSymbolicSolidAngles(data.occ, weight => {
      if (weight === LEGACY_SOLID_ANGLE_MAX) return { symbol: "1", display: "1" };
      if (weight <= 3) return { symbol: "α", display: "(3 arccos(1/3) - π)/(4π)" };
      return { symbol: "(1 + 4α)/6", display: "(1 + 4((3 arccos(1/3) - π)/(4π)))/6" };
    });
    data.solid_angle = { kind: "symbolic", max_value: LEGACY_SOLID_ANGLE_MAX, symbols: ["α = (3 arccos(1/3) - π)/(4π)"] };
    return data;
  };

  const gen_tetragonal_disphenoid_data = () => {
    const verts = [[0,0,1],[0,0,-1],[1,1,0],[1,-1,0]];
    return createScaledTileData(
      verts,
      [ { v:[0,2,3], type:"default" }, { v:[1,3,2], type:"default" }, { v:[0,3,1], type:"default" }, { v:[0,1,2], type:"default" } ],
      false, true
    );
  };

  const gen_octahedron_data = () => {
    const data = createScaledTileData(
      [[ 1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]],
      [
        {v:[0,2,4], type:"default"}, {v:[2,1,4], type:"default"}, {v:[1,3,4], type:"default"}, {v:[3,0,4], type:"default"},
        {v:[0,5,2], type:"default"}, {v:[2,5,1], type:"default"}, {v:[1,5,3], type:"default"}, {v:[3,5,0], type:"default"},
      ], false
    );
    const vertexWeight = computeNormalizedAngleWeight(4 * Math.asin(1 / 3), 4 * Math.PI);
    const edgeWeight = computeNormalizedAngleWeight(Math.acos(-1 / 3), 2 * Math.PI);
    const occ = new Map();
    for (const v of data.v) occ.set(v.join(','), [vertexWeight, 'vertex']);
    for (let i = 0; i < data.v.length; i++) {
      for (let j = i + 1; j < data.v.length; j++) {
        const a = data.v[i], b = data.v[j];
        const d2 = (a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2;
        if (d2 === 8) occ.set([(a[0]+b[0])/2, (a[1]+b[1])/2, (a[2]+b[2])/2].join(','), [edgeWeight, 'edge']);
      }
    }
    occ.set('0,0,0', [LEGACY_SOLID_ANGLE_MAX, 'interior']);
    data.occ = [...occ.entries()].map(([key, item]) => {
      const [weight, kind] = item;
      return [key.split(',').map(Number), weight,
        weight === LEGACY_SOLID_ANGLE_MAX ? "1" : (weight === vertexWeight ? "(1 - 8α)/6" : "(1 - 2α)/3"),
        weight === LEGACY_SOLID_ANGLE_MAX ? "1" : (weight === vertexWeight ? "(1 - 8((3 arccos(1/3) - π)/(4π)))/6" : "(1 - 2((3 arccos(1/3) - π)/(4π)))/3"),
        kind
      ];
    });
    data.solid_angle = { kind: "symbolic", max_value: LEGACY_SOLID_ANGLE_MAX, symbols: ["α = (3 arccos(1/3) - π)/(4π)"] };
    return data;
  };

  const gen_corner_tetra_data = () =>
    createScaledTileData(
      [[0,0,0],[1,0,0],[0,1,0],[0,0,1]],
      [
        { v:[0,2,1], type:"default" },
        { v:[0,1,3], type:"default" },
        { v:[0,3,2], type:"default" },
        { v:[1,2,3], type:"default" }
      ], false
    );

  const gen_big_corner_tetra_data = () => {
    const verts = [
      [0,0,0], [2,0,0], [0,2,0], [0,0,2],
      [1,1,0], [1,0,1], [0,1,1], [1,0,0], [0,1,0], [0,0,1]
    ];
    const faces = [
      // z = 0 face
      [0,7,8], [7,1,4], [8,4,2], [7,4,8],
      // y = 0 face
      [0,9,7], [9,3,5], [7,5,1], [9,5,7],
      // x = 0 face
      [0,8,9], [8,2,6], [9,6,3], [8,6,9],
      // slanted face x + y + z = 2
      [1,4,5], [4,2,6], [5,6,3], [4,6,5]
    ];
    const scaledVerts = verts.map(v => v.map(c => Math.round(c * SCALE)));
    const cornerOnly = [[0,0,0],[2,0,0],[0,2,0],[0,0,2]].map(v => v.map(c => Math.round(c * SCALE)));
    const cornerFaces = [[0,2,1], [0,1,3], [0,3,2], [1,2,3]];
    return {
      v: scaledVerts,
      f_data: faces.map(v => ({ v, type: "default" })),
      occ: computeTetrahedronOccupancy(cornerOnly, cornerFaces, false),
      skip_winding: false,
      solid_angle: { kind: "rational", max_value: LEGACY_SOLID_ANGLE_MAX }
    };
  };

  const gen_cuboctahedron_data = () => {
    const set = new Set();
    for (const x of [-1,1]) for (const y of [-1,1]) set.add([x,y,0].join(","));
    for (const x of [-1,1]) for (const z of [-1,1]) set.add([x,0,z].join(","));
    for (const y of [-1,1]) for (const z of [-1,1]) set.add([0,y,z].join(","));
    return createScaledTileData([...set].map(s => s.split(",").map(Number)), [], true);
  };

  const gen_elongated_square_bipyramid = () => {
    const verts = [];
    for (const x of [-1,1]) for (const y of [-1,1]) for (const z of [-1,1]) verts.push([x,y,z]);
    verts.push([0,0,2],[0,0,-2]);
    return createScaledTileData(verts, [], true);
  };

  const gen_n_cross_data = (arm) => {
    const vox = [[0,0,0]];
    const dirs = [[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]];
    for (const d of dirs) for (let i=1;i<=arm;i++) vox.push([i*d[0], i*d[1], i*d[2]]);
    return generatePolycubeData(vox);
  };

  const gen_n_semicross_data = (arm) => {
    const vox = [[0,0,0]];
    const dirs = [[1,0,0],[0,1,0],[0,0,1]];
    for (const d of dirs) for (let i=1;i<=arm;i++) vox.push([i*d[0], i*d[1], i*d[2]]);
    return generatePolycubeData(vox);
  };

  const gen_double_ring_data = () =>
    generatePolycubeData([ [0,0,0],[0,0,1], [1,0,0],[1,1,0],[1,1,1],[0,1,1], [-1,0,0],[-1,-1,0],[-1,-1,1],[0,-1,1] ]);
  const gen_buckled_ring_data = () => generatePolycubeData([[0,0,0],[1,0,0],[1,1,0],[1,1,1],[0,1,1],[0,0,1]]);
  const gen_large_buckled_ring_data = () => generatePolycubeData([ [0,0,0],[1,0,0],[2,0,0],[2,1,0],[2,2,0], [2,2,1],[2,2,2],[1,2,2],[0,2,2],[0,1,2],[0,0,2],[0,0,1] ]);
  const gen_tuning_fork = () => {
    const vox = [];
    for (let x=0;x<3;x++) for (let y=0;y<12;y++) {
      if (!(x===1 && (y<3 || (6<=y && y<9)))) vox.push([x,y,0]);
    }
    return generatePolycubeData(vox);
  };
  const gen_twisted_h_data = () => generatePolycubeData([[0,0,0],[0,0,1],[1,0,1],[-1,0,1],[0,0,-1],[0,1,-1],[0,-1,-1]]);
  const gen_cube_data = () => generatePolycubeData([[0,0,0]]);
  const gen_s_tetracube = () => generatePolycubeData([[0,0,0],[1,0,0],[1,1,0],[1,1,1]]);
  const gen_knuckle_pentacube = () => generatePolycubeData([[0,0,0],[1,0,0],[-1,0,0],[0,1,0],[0,0,1]]);

  const gen_rhombic_robust = () => {
    const set = new Set();
    const perms = (arr) => {
      if (arr.length<=1) return [arr.slice()];
      const out=[];
      for (let i=0;i<arr.length;i++) {
        const rest=arr.slice(0,i).concat(arr.slice(i+1));
        for (const p of perms(rest)) out.push([arr[i],...p]);
      }
      return out;
    };
    for (const p of perms([2,0,0])) { set.add(p.join(",")); set.add(p.map(x=>-x).join(",")); }
    for (const sx of [-1,1]) for (const sy of [-1,1]) for (const sz of [-1,1]) set.add([sx,sy,sz].join(","));
    return createScaledTileData([...set].map(s => s.split(",").map(Number)), [], true);
  };

  const gen_trunc_oct_robust = () => {
    const set = new Set();
    const perms = (arr) => {
      if (arr.length<=1) return [arr.slice()];
      const out=[];
      for (let i=0;i<arr.length;i++) {
        const rest=arr.slice(0,i).concat(arr.slice(i+1));
        for (const p of perms(rest)) out.push([arr[i],...p]);
      }
      return out;
    };
    for (const p of perms([2,1,0])) {
      for (const s1 of [-1,1]) for (const s2 of [-1,1]) {
        const pt = [0,0,0]; pt[p[0]] = 2*s1; pt[p[1]] = 1*s2; set.add(pt.join(","));
      }
    }
    return createScaledTileData([...set].map(s => s.split(",").map(Number)), [], true);
  };

  const gen_elongated_dodecahedron = () => {
    const verts = [[2,0,0],[-2,0,0],[0,2,0],[0,-2,0],[0,0,4],[0,0,-4]];
    for (const x of [-1,1]) for (const y of [-1,1]) for (const z of [-1,1]) verts.push([x,y,2*z]);
    return createScaledTileData(verts, [], true);
  };

  const gen_hex_prism = () => {
    const perms = (arr) => {
      if (arr.length<=1) return [arr.slice()];
      const out=[];
      for (let i=0;i<arr.length;i++) {
        const rest=arr.slice(0,i).concat(arr.slice(i+1));
        for (const p of perms(rest)) out.push([arr[i],...p]);
      }
      return out;
    };
    const verts = [];
    for (const p of perms([1,-1,0])) verts.push([p[0]+1,p[1]+1,p[2]+1]);
    for (const p of perms([1,-1,0])) verts.push([p[0]-1,p[1]-1,p[2]-1]);
    return createScaledTileData(verts, [], true);
  };

  const gen_orthoscheme_robust = () => {
    const data = createScaledTileData(
      [[0,0,0],[2,0,0],[2,2,0],[2,2,2],[1,1,0],[2,1,1]],
      [
        {v:[0,1,4], type:"default"}, {v:[1,2,4], type:"default"},
        {v:[1,2,5], type:"default"}, {v:[2,3,5], type:"default"},
        {v:[0,1,3], type:"default"}, {v:[0,2,3], type:"default"},
      ], false
    );
    data.solid_angle = { kind: "rational", max_value: LEGACY_SOLID_ANGLE_MAX };
    return data;
  };

  const gen_gyrobifastigium_data = () => {
    const verts = [[1,1,0],[1,-1,0],[-1,-1,0],[-1,1,0],[0,1,2],[0,-1,2],[1,0,-2],[-1,0,-2]];
    return createScaledTileData(verts, [], true);
  };

  const gen_trunc_tetra_friauf = () => {
    const tips = [[0,0,0],[3,3,0],[3,0,3],[0,3,3]];
    const verts = [];
    for (let i=0;i<4;i++) for (let j=0;j<4;j++) if (j!==i) {
      const a=tips[i], b=tips[j];
      verts.push([a[0]+((b[0]-a[0])/3), a[1]+((b[1]-a[1])/3), a[2]+((b[2]-a[2])/3)]);
    }
    const uniq = new Map();
    for (const v of verts) uniq.set(v.join(","), v);
    const temp = createScaledTileData([...uniq.values()], [], true);
    temp.f_data = temp.f_data.map(f => ({ ...f, type: (f.v.length===3 ? "TRI_FACE" : "HEX_FACE") }));
    return temp;
  };

  const gen_escher_solid_data = () => {
    const core = gen_rhombic_robust();
    const verts = core.v.map(v => v.slice());
    const faces = [];
    const occ = new Map();
    const addOcc = (items) => {
      for (const [pos, weight] of items ?? []) {
        const key = pos.join(",");
        occ.set(key, (occ.get(key) ?? 0) + weight);
      }
    };
    addOcc(core.occ);

    for (const face of core.f_data) {
      const base = face.v.map(index => verts[index]);
      const center = base
        .reduce((sum, v) => add3(sum, v), [0, 0, 0])
        .map(c => Math.round(c / base.length));
      const apex = center.map(c => c * 2);
      const apexIndex = verts.length;
      verts.push(apex);

      for (let i = 0; i < face.v.length; i++) {
        faces.push({
          v: [face.v[i], face.v[(i + 1) % face.v.length], apexIndex],
          type: "ESCHER_SPIKE_WALL"
        });
      }

      const localVerts = base.map(v => v.slice()).concat([apex]);
      const localFaces = [
        [0, 1, 2, 3],
        [0, 1, 4],
        [1, 2, 4],
        [2, 3, 4],
        [3, 0, 4]
      ];
      addOcc(computeConvexOccupancy(localVerts, localFaces));
    }

    return {
      v: verts,
      f_data: faces,
      occ: [...occ.entries()].map(([key, weight]) => [key.split(",").map(Number), weight]),
      skip_winding: false
    };
  };

  const gen_letter_o_data = () => {
    const vox = [];
    for (let x = 0; x < 3; x++) for (let y = 0; y < 4; y++) {
      if (x === 1 && (y === 1 || y === 2)) continue;
      vox.push([x, y, 0]);
    }
    const data = generatePolycubeData(vox);
    const hollowSet = new Set(['1,1,0', '1,2,0']);
    const voxelSet = new Set(vox.map(v => v.join(',')));
    const dirs = [[1,0,0], [-1,0,0],[0,1,0], [0,-1,0],[0,0,1], [0,0,-1]];
    const faceInfo = new Map();
    const getFaceType = (vx, vy, vz, dx, dy, dz, neighbor) => {
      if (hollowSet.has(neighbor)) {
        if ((vy === 0 && dy === 1) || (vy === 3 && dy === -1)) return "inner_single";
        else return "inner_double";
      }
      const isOnPerimeter = (vx === 0 && dx === -1) || (vx === 2 && dx === 1) || (vy === 0 && dy === -1) || (vy === 3 && dy === 1) || (vz === 0 && dz === -1) || (vz === 0 && dz === 1);
      if (isOnPerimeter) return "outer_rim"; else return "outer_side";
    };
    for (const v of vox) {
      const [vx, vy, vz] = v;
      for (let d = 0; d < dirs.length; d++) {
        const [dx, dy, dz] = dirs[d];
        const nb = [vx + dx, vy + dy, vz + dz];
        const nbKey = nb.join(',');
        if (hollowSet.has(nbKey) || !voxelSet.has(nbKey)) {
          const faceType = getFaceType(vx, vy, vz, dx, dy, dz, nbKey);
          const key = `${vx},${vy},${vz},${dx},${dy},${dz}`;
          faceInfo.set(key, { voxel: v, normal: [dx, dy, dz], type: faceType });
        }
      }
    }
    const faceCenter = (faceIndices, vertices) => {
      const verts = faceIndices.map(i => vertices[i]);
      const sum = verts.reduce((acc, v) => [acc[0]+v[0], acc[1]+v[1], acc[2]+v[2]], [0,0,0]);
      return sum.map(c => c / verts.length);
    };
    const estimateNormal = (faceIndices, vertices) => {
      if (faceIndices.length < 3) return [0,0,0];
      const v0 = vertices[faceIndices[0]], v1 = vertices[faceIndices[1]], v2 = vertices[faceIndices[2]];
      const e1 = [v1[0]-v0[0], v1[1]-v0[1], v1[2]-v0[2]];
      const e2 = [v2[0]-v0[0], v2[1]-v0[1], v2[2]-v0[2]];
      const nx = e1[1]*e2[2] - e1[2]*e2[1], ny = e1[2]*e2[0] - e1[0]*e2[2], nz = e1[0]*e2[1] - e1[1]*e2[0];
      const len = Math.sqrt(nx*nx + ny*ny + nz*nz);
      if (len < 0.0001) return [0,0,0];
      return [nx/len, ny/len, nz/len];
    };
    for (let i = 0; i < data.f_data.length; i++) {
      const face = data.f_data[i];
      const center = faceCenter(face.v, data.v);
      const normal = estimateNormal(face.v, data.v);
      let matched = false;
      for (const [key, info] of faceInfo.entries()) {
        const [vx, vy, vz, dx, dy, dz] = key.split(',').map(Number);
        const facePos = [vx + (dx > 0 ? 1 : dx < 0 ? 0 : 0.5), vy + (dy > 0 ? 1 : dy < 0 ? 0 : 0.5), vz + (dz > 0 ? 1 : dz < 0 ? 0 : 0.5)].map(p => p * 2);
        const dist = Math.sqrt(Math.pow(center[0] - facePos[0], 2) + Math.pow(center[1] - facePos[1], 2) + Math.pow(center[2] - facePos[2], 2));
        const dot = normal[0]*dx + normal[1]*dy + normal[2]*dz;
        if (dist < 1.0 && dot > 0.7) { face.type = info.type; matched = true; break; }
      }
      if (!matched) {
        const voxelCenter = center.map(c => Math.round(c / 2));
        const isNearPerimeter = voxelCenter[0] === 0 || voxelCenter[0] === 3 || voxelCenter[1] === 0 || voxelCenter[1] === 4 || voxelCenter[2] === 0 || voxelCenter[2] === 1;
        if (isNearPerimeter) face.type = "outer_rim"; else face.type = "outer_side";
      }
    }
    return data;
  };

  const gen_1cross_plus_data = () => generatePolycubeData([[0,0,0],[1,0,0], [-1,0,0],[0,1,0], [0,-1,0],[0,0,1], [0,0,-1],[2,0,0]]);

  // --- Barlow Packing Generators (FCC/HCP Voronoi Cells) ---
  const gen_barlow_polyhedra = () => {
    // 1. Rhombic Dodecahedron (FCC)
    // Vertices scaled x3 to avoid fractions during reflection
    // Standard RD vertices: perms of (±2,0,0) -> (±6,0,0) and (±1,±1,±1) -> (±3,±3,±3)
    const rd_verts = [
      [3,3,3], [-3,-3,-3], // Poles
      [6,0,0], [0,6,0], [0,0,6], // Top Shoulders
      [-6,0,0], [0,-6,0], [0,0,-6], // Bottom Shoulders
      [3,3,-3], [3,-3,3], [-3,3,3], // Top Waist (Equator)
      [-3,-3,3], [-3,3,-3], [3,-3,-3] // Bottom Waist
    ];
    const rd_data = createScaledTileData(rd_verts, [], true);
    
    // 2. Trapezo-Rhombic Dodecahedron (HCP)
    // Construct by taking Top Half of RD and Reflecting it across x+y+z=0
    // Reflection formula: v' = v - 2 * (dot(v,n)/dot(n,n)) * n, where n=[1,1,1], dot(n,n)=3
    // v' = v - 2/3 * sum(v) * [1,1,1]
    const trd_verts = [];
    
    // Add Top Half (including equator)
    trd_verts.push([3,3,3]); // Pole
    trd_verts.push([6,0,0], [0,6,0], [0,0,6]); // Top Shoulders
    trd_verts.push([3,3,-3], [3,-3,3], [-3,3,3]); // Top Waist (Equator)

    // Reflect Top Half to create Bottom Half
    const reflect = (v) => {
      const sum = v[0]+v[1]+v[2];
      const k = (2 * sum) / 3;
      return [v[0]-k, v[1]-k, v[2]-k];
    };
    trd_verts.push(reflect([3,3,-3]), reflect([3,-3,3]), reflect([-3,3,3])); // Bottom Waist
    trd_verts.push(reflect([6,0,0]), reflect([0,6,0]), reflect([0,0,6])); // Bottom Shoulders
    trd_verts.push(reflect([3,3,3])); // Bottom Pole

    const trd_data = createScaledTileData(trd_verts, [], true);
    trd_data.f_data.forEach(f => {
      if (f.v.length === 4) f.type = "TRD_TRAP"; else f.type = "TRD_RHOMB";
    });

    return { rd: rd_data, trd: trd_data };
  };

  // --- Registry (complete) ---
  const TILING_REGISTRY = {
    ...Object.fromEntries(POLYCUBE_GCTS_CANDIDATES.map(candidate => [candidate.registry_id, {
      name: candidate.name,
      category: [candidate.screening.status === "inconclusive"
        ? "Unresolved Polycube Candidates"
        : ["translational", "isohedral_periodic_quotient"].includes(candidate.screening.certificate)
          ? "GCTS Periodic Controls"
          : "GCTS Shell-Obstruction Controls", "Polycubes"],
      census_candidate: candidate,
      build: () => [make_tile(candidate.name, generatePolycubeData(candidate.voxels))]
    }])),
    ...Object.fromEntries(LATTICE_POLYHEDRON_GCTS_EXAMPLES.map(candidate => [candidate.registry_id, {
      name: candidate.name,
      category: [candidate.screening.status === "inconclusive"
        ? "Unresolved Lattice Candidates"
        : ["translational", "isohedral_periodic_quotient"].includes(candidate.screening.certificate)
          ? "GCTS Periodic Controls"
          : "GCTS Shell-Obstruction Controls"],
      census_candidate: candidate,
      build: () => [make_tile(candidate.name, createScaledTileData(candidate.vertices, [], true))]
    }])),
    "scd_conway": {
      name: "Schmitt–Conway–Danzer Biprism",
      category: ["Aperiodic Monotiles"],
      aperiodic_tile: {
        kind: "weakly aperiodic",
        lattice_realization: "3–4–5 incommensurate SCD biprism",
        reflections_forbidden: true
      },
      // Twice the standard construction with a=(5,0,0), b=(3,4,0),
      // lambda=1/2 and height=1. The vertices are integral while the layer
      // rotation phi=atan(3/4) is incommensurate with pi.
      build: () => [make_tile("Conway Biprism", createScaledTileData([
        [0,0,0], [10,0,0], [6,8,0], [16,8,0],
        [3,4,2], [13,4,2], [5,0,-2], [11,8,-2]
      ], [], true))]
    },
    "1_cross": { name:"1-Cross (Heptacube)", category:["Polycubes"], build: () => [make_tile("1-Cross", gen_n_cross_data(1))] },
    "2_cross": { name:"2-Cross (Tridecacube)", category:["Polycubes"], build: () => [make_tile("2-Cross", gen_n_cross_data(2))] },
    "3_cross": { name:"3-Cross (Nonadecacube)", category:["Polycubes"], build: () => [make_tile("3-Cross", gen_n_cross_data(3))] },
    "t_cross": { name:"T-Cross", category:["Polycubes"], build: () => [make_tile("T-Cross", (() => {
      const arm = 3;
      const vox = new Set();
      const dirs = [[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]];
      vox.add([0,0,0].join(","));
      const basis = [[0,1,0],[0,0,1],[1,0,0]];
      for (const d of dirs) {
        for (let i=1;i<=arm;i++) vox.add([i*d[0],i*d[1],i*d[2]].join(","));
        const end = [arm*d[0],arm*d[1],arm*d[2]];
        const bar = basis.find(b => Math.abs(dot3(b,d)) < 0.1);
        vox.add([end[0]+bar[0], end[1]+bar[1], end[2]+bar[2]].join(","));
        vox.add([end[0]-bar[0], end[1]-bar[1], end[2]-bar[2]].join(","));
      }
      return generatePolycubeData([...vox].map(s => s.split(",").map(Number)));
    })())] },
    "1_semicross": { name:"1-Semicross (Tripod)", category:["Polycubes"], build: () => [make_tile("1-Semi", gen_n_semicross_data(1))] },
    "2_semicross": { name:"2-Semicross (Corner)", category:["Polycubes"], build: () => [make_tile("2-Semi", gen_n_semicross_data(2))] },
    "buckled_ring": { name:"Buckled Ring", category:["Polycubes"], build: () => [make_tile("BuckledRing", gen_buckled_ring_data())] },
    "large_buckled_ring": { name:"Large Buckled Ring", category:["Polycubes"], build: () => [make_tile("LargeRing", gen_large_buckled_ring_data())] },
    "double_ring": { name:"Double Buckled Ring", category:["Polycubes"], build: () => [make_tile("DoubleRing", gen_double_ring_data())] },
    "tuning_fork": { name:"Tuning Fork (Reinhardt)", category:["Polycubes"], build: () => [make_tile("Fork", gen_tuning_fork())] },
    "twisted_h": { name:"Letter H (Twisted)", category:["Polycubes"], build: () => [make_tile("TwistedH", gen_twisted_h_data())] },
    "cube": { name:"Cube", category:["Fedorov Solids","Polycubes"], build: () => [make_tile("Cube", gen_cube_data())] },
    "letter_o": {
      name: "Letter O", category: ["Polycubes"],
      build: () => [make_tile("LetterO", gen_letter_o_data())]
    },
    "1_cross_plus": { name:"1-Cross + 1", category:["Polycubes"], build: () => [make_tile("1CrossPlus", gen_1cross_plus_data())] },
    "hex_prism": { name:"Hexagonal Prism", category:["Fedorov Solids"], build: () => [make_tile("HexPrism", gen_hex_prism())] },
    "rhombic": { name:"Rhombic Dodecahedron", category:["Fedorov Solids"], build: () => [make_tile("RhombicDod", gen_rhombic_robust())] },
    "elongated_dod": { name:"Elongated Dodecahedron", category:["Fedorov Solids"], build: () => [make_tile("ElongatedDod", gen_elongated_dodecahedron())] },
    "trunc_oct": { name:"Truncated Octahedron", category:["Fedorov Solids"], build: () => [make_tile("TruncOct", gen_trunc_oct_robust())] },
    "twist": { name:"Twist (Tetracube)", category:["Polycubes"], build: () => [make_tile("Twist", gen_s_tetracube())] },
    "knuckle": { name:"Knuckle (Pentacube)", category:["Polycubes"], build: () => [make_tile("Knuckle", gen_knuckle_pentacube())] },
    "tet_oct": { name:"Tetrahedron + Octahedron", category:["Platonic Solids"], build: () => [ make_tile("Tetrahedron", gen_tetrahedron_data()), make_tile("Octahedron", gen_octahedron_data()) ] },
    "tetragonal_disphenoid": { name:"Tetragonal Disphenoid (B₃ alcove)", category:["Space Fillers"], build: () => [make_tile("Disphenoid", gen_tetragonal_disphenoid_data())] },
    "corner_tetra": { name:"Corner Tetrahedron", category:["Space Fillers"], build: () => [make_tile("CornerTetra", gen_corner_tetra_data())] },
    "big_corner_tetra": { name:"Big Corner Tetrahedron", category:["Space Fillers"], build: () => [make_tile("BigCornerTetra", gen_big_corner_tetra_data())] },
    "diamond_lattice": {
      name:"Double FCC Lattice (Diamond)", category:["Platonic Solids"],
      build: () => [ make_tile("Tetrahedron", gen_tetrahedron_data()), make_tile("Octahedron", gen_octahedron_data()), make_tile("CornerTetra", gen_corner_tetra_data()) ],
      default_viz: { opacities:[0.9,0.1,0.1], internal:true }
    },
    "perovskite": { name:"Perovskite (Cuboctahedron + Octa)", category:["Platonic Solids"], build: () => [ make_tile("Cuboctahedron", gen_cuboctahedron_data()), make_tile("Octahedron", gen_octahedron_data()) ], default_viz: { opacities:[0.5,0.9], internal:true } },
    "orthoscheme": { name:"Orthoscheme (B̃₃ alcove)", category:["Space Fillers"], build: () => [make_tile("Orthoscheme", gen_orthoscheme_robust())], default_viz: { opacities:[0.6], internal:true } },
    "elongated_sq_bipyramid": { name:"Elongated Bipyramid (J15)", category:["Space Fillers"], build: () => [make_tile("Johnson15", gen_elongated_square_bipyramid())] },
    "gyrobifastigium": { name:"Gyrobifastigium (J26)", category:["Space Fillers"], build: () => [make_tile("Johnson26", gen_gyrobifastigium_data())] },
    "laves_c15": { name:"Laves C15 (Truncated Tetra + Tetra))", category:["Platonic Solids"], build: () => [ make_tile("TruncTetra", gen_trunc_tetra_friauf()), make_tile("Tetra", gen_tetrahedron_data()) ], default_viz: { opacities:[0.4,1.0], internal:true } },
    "escher_compound": {
      name:"Escher Solid", category:["Space Fillers"],
      build: () => [make_tile("EscherSolid", gen_escher_solid_data())],
      default_viz: { opacities:[0.85], internal:true }
    },
    "fcc_pure": {
      name: "FCC (Pure Rhombic Dodecahedron)",
      category: ["Sphere Packings"],
      build: () => {
        const { rd } = gen_barlow_polyhedra();
        return [make_tile("Rhombic_Dodecahedron_(FCC)", rd)];
      },
      default_viz: { opacities: [0.9], internal: true }
    },
    "hcp_pure": {
      name: "HCP (Pure Trapezo-Rhombic Dodecahedron)",
      category: ["Sphere Packings"],
      build: () => {
        const { trd } = gen_barlow_polyhedra();
        return [make_tile("Trapezo_Rhombic_Dodecahedron_(HCP)", trd)];
      },
      default_viz: { opacities: [0.9], internal: true }
    },
    "barlow_fcc": {
      name: "Barlow Packing (Root: FCC)",
      category: ["Sphere Packings"],
      build: () => {
        const { rd, trd } = gen_barlow_polyhedra();
        return [
          make_tile("Rhombic_Dodecahedron_(FCC)", rd),
          make_tile("Trapezo_Rhombic_Dodecahedron_(HCP)", trd)
        ];
      },
      default_viz: { opacities: [0.8, 0.8], internal: true }
    },
    "barlow_hcp": {
      name: "Barlow Packing (Root: HCP)",
      category: ["Sphere Packings"],
      build: () => {
        const { rd, trd } = gen_barlow_polyhedra();
        return [
          make_tile("Trapezo_Rhombic_Dodecahedron_(HCP)", trd),
          make_tile("Rhombic_Dodecahedron_(FCC)", rd)
        ];
      },
      default_viz: { opacities: [0.8, 0.8], internal: true }
    }
  };

  const latticeFaceSignature = (verts) => {
    const mins = [Infinity, Infinity, Infinity];
    for (const v of verts) for (let i = 0; i < 3; i++) mins[i] = Math.min(mins[i], v[i]);
    return verts
      .map(v => [v[0] - mins[0], v[1] - mins[1], v[2] - mins[2]].join(","))
      .sort()
      .join("|");
  };

  const tileFaceSignatures = (tile) => {
    const signatures = new Set();
    for (const orient of tile.unique_orientations ?? []) {
      for (const face of orient.faces ?? []) {
        signatures.add(latticeFaceSignature(face.map(i => orient.verts[i])));
      }
    }
    return [...signatures].sort();
  };

  const displayTileNameMap = new Map([
    ["Tetra", "Tetrahedron"],
    ["Octa", "Octahedron"],
    ["BuckledRing", "Buckled Ring"],
    ["LargeRing", "Large Buckled Ring"],
    ["DoubleRing", "Double Buckled Ring"],
    ["Fork", "Tuning Fork"],
    ["TwistedH", "Letter H"],
    ["LetterO", "Letter O"],
    ["1CrossPlus", "1-Cross + 1"],
    ["HexPrism", "Hexagonal Prism"],
    ["RhombicDod", "Rhombic Dodecahedron"],
    ["ElongatedDod", "Elongated Dodecahedron"],
    ["TruncOct", "Truncated Octahedron"],
    ["Disphenoid", "Tetragonal Disphenoid"],
    ["CornerTetra", "Corner Tetrahedron"],
    ["BigCornerTetra", "Big Corner Tetrahedron"],
    ["Johnson15", "Elongated Bipyramid"],
    ["Johnson26", "Gyrobifastigium"],
    ["TruncTetra", "Truncated Tetrahedron"],
    ["EscherSolid", "Escher Solid"],
    ["Rhombic_Dodecahedron_(FCC)", "Rhombic Dodecahedron"],
    ["Trapezo_Rhombic_Dodecahedron_(HCP)", "Trapezo-Rhombic Dodecahedron"]
  ]);

  const displayTileName = (name) => {
    const sourceName = String(name ?? "Tile");
    const reflected = sourceName.startsWith("reflected ");
    const baseName = reflected ? sourceName.slice("reflected ".length) : sourceName;
    const cleaned = /^Candidate \d+_\d+$/u.test(baseName)
      ? baseName
      : displayTileNameMap.get(baseName)
      ?? baseName
        .replace(/_\((FCC|HCP)\)$/i, "")
        .replace(/\s*\((FCC|HCP|Root:\s*(FCC|HCP))\)\s*$/i, "")
        .replace(/_/g, " ");
    return `${reflected ? "reflected " : ""}${cleaned}`;
  };

  const canonicalFigureName = displayTileName;

  const solidAngleValues = (tile) => {
    const maxValue = tile?.solid_angle?.max_value ?? LEGACY_SOLID_ANGLE_MAX;
    return (tile?.occupancy_points ?? [])
      .map(point => ({ weight: point.weight, symbolic: point.symbolic, display_symbolic: point.display_symbolic, kind: point.kind }))
      .filter(item => Number.isFinite(item.weight))
      .sort((a, b) => a.weight - b.weight)
      .map(item => ({ weight: item.weight, max_value: maxValue, value: item.weight / maxValue, symbolic: item.symbolic, display_symbolic: item.display_symbolic, kind: item.kind }));
  };

  const tileGeometryKey = (tile) => {
    const verts = (tile.verts ?? []).map(v => v.join(",")).sort().join("|");
    const faces = (tile.faces ?? [])
      .map(face => face.map(i => tile.verts[i].join(",")).sort().join(";"))
      .sort()
      .join("|");
    const occupancy = (tile.occupancy_points ?? [])
      .map(point => `${point.pos.join(",")}:${point.weight}`)
      .sort()
      .join("|");
    return `${verts}@@${faces}@@${occupancy}`;
  };

  const metadata = {};
  for (const [k,v] of Object.entries(TILING_REGISTRY)) {
    const tiles = v.build();
    metadata[k] = { name: v.name, category: v.category || [], census_candidate: v.census_candidate || null, aperiodic_tile: v.aperiodic_tile || null, is_chiral: !!tiles[0]?.is_chiral, default_viz: v.default_viz || {} };
  }
  const categories = new Map();
  for (const [k,meta] of Object.entries(metadata)) {
    for (const c of (meta.category || ["Other"])) {
      if (!categories.has(c)) categories.set(c, []);
      categories.get(c).push({ id: k, name: meta.name });
    }
  }
  const options = [...categories.entries()]
    .sort((a,b)=>a[0].localeCompare(b[0]))
    .map(([group, tiles]) => ({ group, tiles: tiles.sort((a,b)=>a.name.localeCompare(b.name)) }));

  const figureCatalog = [];
  const figureDedupe = new Map();
  const figureAliases = new Map();
  for (const [modeKey, entry] of Object.entries(TILING_REGISTRY)) {
    const tiles = entry.build();
    tiles.forEach((tile, tileIndex) => {
      const sourceId = `${modeKey}::${tileIndex}`;
      const name = canonicalFigureName(tile.name);
      const key = `${name}@@${tileGeometryKey(tile)}`;
      let figure = figureDedupe.get(key);
      if (!figure) {
        figure = {
          id: sourceId,
          mode_key: modeKey,
          tile_index: tileIndex,
          name,
          system_name: entry.name,
          system_names: [entry.name],
          category: [...(entry.category || ["Other"])],
          census_candidate: entry.census_candidate || null,
          aperiodic_tile: entry.aperiodic_tile || null,
          is_chiral: !!tile.is_chiral,
          solid_angle: tile.solid_angle,
          solid_angles: solidAngleValues(tile),
          signatures: tileFaceSignatures(tile),
          aliases: [sourceId]
        };
        figureDedupe.set(key, figure);
        figureCatalog.push(figure);
      } else {
        figure.aliases.push(sourceId);
        if (!figure.system_names.includes(entry.name)) figure.system_names.push(entry.name);
        for (const category of (entry.category || ["Other"])) {
          if (!figure.category.includes(category)) figure.category.push(category);
        }
        figure.is_chiral = figure.is_chiral || !!tile.is_chiral;
      }
      figureAliases.set(sourceId, figure);
    });
  }

  const figuresShareLatticeFace = (a, b) => {
    const signatures = new Set(a.signatures ?? []);
    return (b.signatures ?? []).some(sig => signatures.has(sig));
  };
  for (const figure of figureCatalog) {
    figure.compatible_ids = figureCatalog
      .filter(other => figuresShareLatticeFace(figure, other))
      .map(other => other.id);
  }

  const figureMetadata = figureAliases;

  const addMirrorsIfChiral = (tiles) => {
    const out = tiles.slice();
    for (const t of tiles) {
      if (t.is_chiral) {
        const m = t.get_mirror_copy();
        if (m) out.push(m);
      }
    }
    return out;
  };

  const normalizeVoxels = (voxels) => {
    const unique = new Map();
    for (const voxel of voxels ?? []) {
      if (!Array.isArray(voxel) || voxel.length < 3) continue;
      const v = voxel.slice(0, 3).map(n => Math.trunc(Number(n)));
      if (v.some(n => !Number.isFinite(n))) continue;
      unique.set(v.join(","), v);
    }
    const out = [...unique.values()];
    if (!out.length) return [[0, 0, 0]];
    const mins = [Infinity, Infinity, Infinity];
    for (const v of out) for (let i = 0; i < 3; i++) mins[i] = Math.min(mins[i], v[i]);
    return out.map(v => [v[0] - mins[0], v[1] - mins[1], v[2] - mins[2]]);
  };

  const buildPolycubeTile = (name, voxels, options = {}) =>
    make_tile(name || "CustomPolycube", generatePolycubeData(normalizeVoxels(voxels), options));

  const convexEdgeAngleObstruction = (vertices, suppliedFaces = null) => {
    const verts = (vertices ?? []).map(vertex => vertex.slice(0, 3).map(Number));
    if (verts.length < 4 || verts.some(vertex => vertex.some(value => !Number.isFinite(value)))) return null;
    const rawFaces = suppliedFaces?.length
      ? suppliedFaces.map(face => (Array.isArray(face) ? face : face?.v).map(Number))
      : computeHullFaces(verts);
    if (!rawFaces.length || rawFaces.some(face => face.length < 3)) return null;
    const faces = orientConvexFaces(verts, rawFaces);
    const normals = faces.map(face => normalize3(cross3(
      sub3(verts[face[1]], verts[face[0]]),
      sub3(verts[face[2]], verts[face[0]])
    )));
    if (normals.some(normal => norm3(normal) < 1e-12)) return null;
    for (let faceIndex = 0; faceIndex < faces.length; faceIndex++) {
      const face = faces[faceIndex];
      const normal = normals[faceIndex];
      const origin = verts[face[0]];
      if (verts.some(vertex => dot3(normal, sub3(vertex, origin)) > 1e-8)) return null;
    }
    const incidentFaces = new Map();
    for (let faceIndex = 0; faceIndex < faces.length; faceIndex++) {
      const face = faces[faceIndex];
      for (let index = 0; index < face.length; index++) {
        const a = face[index];
        const b = face[(index + 1) % face.length];
        const edgeKey = a < b ? `${a},${b}` : `${b},${a}`;
        if (!incidentFaces.has(edgeKey)) incidentFaces.set(edgeKey, []);
        incidentFaces.get(edgeKey).push(faceIndex);
      }
    }
    if ([...incidentFaces.values()].some(faceIndices => faceIndices.length !== 2)) return null;
    const edgeGroups = new Map();
    for (const [edgeKey, faceIndices] of incidentFaces) {
      const [aIndex, bIndex] = edgeKey.split(",").map(Number);
      const edgeVector = sub3(verts[bIndex], verts[aIndex]);
      const lengthSquared = dot3(edgeVector, edgeVector);
      const cosine = Math.max(-1, Math.min(1, dot3(normals[faceIndices[0]], normals[faceIndices[1]])));
      const interiorAngle = Math.PI - Math.acos(cosine);
      if (Math.abs(interiorAngle - Math.PI) < 1e-8) continue;
      const lengthKey = String(Math.round(lengthSquared * 1e9) / 1e9);
      if (!edgeGroups.has(lengthKey)) edgeGroups.set(lengthKey, []);
      edgeGroups.get(lengthKey).push({ edge: [aIndex, bIndex], angle: interiorAngle });
    }
    const angleCanClose = (targetAngle, availableAngles) => {
      const tolerance = 1e-7;
      const uniqueAngles = [];
      for (const angle of availableAngles) {
        if (!uniqueAngles.some(existing => Math.abs(existing - angle) < tolerance)) uniqueAngles.push(angle);
      }
      uniqueAngles.sort((left, right) => right - left);
      const minimumAngle = Math.min(...uniqueAngles);
      const maxDepth = Math.ceil((2 * Math.PI) / minimumAngle) + 1;
      const memo = new Set();
      const fill = (remaining, startIndex, depth) => {
        if (Math.abs(remaining) < tolerance) return true;
        if (remaining < -tolerance || depth >= maxDepth) return false;
        const memoKey = `${Math.round(remaining / tolerance)}:${startIndex}:${depth}`;
        if (memo.has(memoKey)) return false;
        memo.add(memoKey);
        for (let index = startIndex; index < uniqueAngles.length; index++) {
          if (fill(remaining - uniqueAngles[index], index, depth + 1)) return true;
        }
        return false;
      };
      return fill(2 * Math.PI - targetAngle, 0, 1);
    };
    for (const [lengthSquared, edges] of edgeGroups) {
      const angles = edges.map(edge => edge.angle);
      for (const edge of edges) {
        if (angleCanClose(edge.angle, angles)) continue;
        return {
          kind: "local_edge_obstruction",
          certified: true,
          can_tile: false,
          model: "face_to_face_congruent_copies",
          edge: edge.edge,
          edge_length_squared: Number(lengthSquared),
          interior_dihedral_radians: edge.angle,
          note: "No multiset of matching tile-edge dihedral angles sums to 2π around this edge."
        };
      }
    }
    return null;
  };

  const buildLatticePolyhedronTile = (name, vertices, faces = null) => {
    const normalizedVertices = (vertices ?? []).map((vertex, index) => {
      if (!Array.isArray(vertex) || vertex.length < 3) {
        throw new Error(`Custom polyhedron vertex ${index} must contain three coordinates`);
      }
      const point = vertex.slice(0, 3).map(Number);
      if (point.some(value => !Number.isFinite(value) || !Number.isInteger(value))) {
        throw new Error(`Custom polyhedron vertex ${index} must lie on the integer lattice`);
      }
      return point;
    });
    const hasVolume = (() => {
      if (normalizedVertices.length < 4) return false;
      const base = normalizedVertices[0];
      const vectors = normalizedVertices.slice(1).map(vertex => sub3(vertex, base));
      for (let i = 0; i < vectors.length; i++) {
        for (let j = i + 1; j < vectors.length; j++) {
          for (let k = j + 1; k < vectors.length; k++) {
            if (dot3(vectors[i], cross3(vectors[j], vectors[k])) !== 0) return true;
          }
        }
      }
      return false;
    })();
    if (!hasVolume) {
      throw new Error("Custom polyhedron needs at least four non-coplanar lattice vertices");
    }

    const normalizedFaces = faces?.map((face, faceIndex) => {
      const indices = Array.isArray(face) ? face : face?.v;
      if (!Array.isArray(indices) || indices.length < 3) {
        throw new Error(`Custom polyhedron face ${faceIndex} needs at least three vertex indices`);
      }
      const normalized = indices.map(Number);
      if (normalized.some(index =>
        !Number.isInteger(index)
        || index < 0
        || index >= normalizedVertices.length
      )) {
        throw new Error(`Custom polyhedron face ${faceIndex} contains an invalid vertex index`);
      }
      return { v: normalized, type: face?.type ?? "default" };
    }) ?? [];
    if (normalizedFaces.length) {
      const edgeCounts = new Map();
      const usedVertices = new Set();
      for (let faceIndex = 0; faceIndex < normalizedFaces.length; faceIndex++) {
        const face = normalizedFaces[faceIndex].v;
        if (new Set(face).size !== face.length) {
          throw new Error(`Custom polyhedron face ${faceIndex} repeats a vertex`);
        }
        for (let i = 0; i < face.length; i++) {
          const a = face[i];
          const b = face[(i + 1) % face.length];
          usedVertices.add(a);
          usedVertices.add(b);
          const edgeKey = a < b ? `${a},${b}` : `${b},${a}`;
          edgeCounts.set(edgeKey, (edgeCounts.get(edgeKey) ?? 0) + 1);
        }
        const origin = normalizedVertices[face[0]];
        let normal = null;
        for (let i = 1; i < face.length - 1 && !normal; i++) {
          const candidate = cross3(
            sub3(normalizedVertices[face[i]], origin),
            sub3(normalizedVertices[face[i + 1]], origin)
          );
          if (candidate.some(Boolean)) normal = candidate;
        }
        if (!normal) throw new Error(`Custom polyhedron face ${faceIndex} is degenerate`);
        const faceSet = new Set(face);
        let side = 0;
        for (let vertexIndex = 0; vertexIndex < normalizedVertices.length; vertexIndex++) {
          const signedDistance = dot3(normal, sub3(normalizedVertices[vertexIndex], origin));
          if (faceSet.has(vertexIndex)) {
            if (signedDistance !== 0) throw new Error(`Custom polyhedron face ${faceIndex} is not planar`);
            continue;
          }
          if (signedDistance === 0) continue;
          const vertexSide = Math.sign(signedDistance);
          if (side && vertexSide !== side) {
            throw new Error(`Custom polyhedron face ${faceIndex} is not a convex supporting face`);
          }
          side = vertexSide;
        }
        if (!side) throw new Error(`Custom polyhedron face ${faceIndex} does not bound a volume`);
      }
      if (
        usedVertices.size !== normalizedVertices.length
        || [...edgeCounts.values()].some(count => count !== 2)
      ) {
        throw new Error("Custom polyhedron faces must form one closed convex shell");
      }
    }

    const data = createScaledTileData(
      normalizedVertices,
      normalizedFaces,
      normalizedFaces.length === 0
    );
    return make_tile(name || "CustomPolyhedron", data);
  };

  const buildCustomSystem = (customSystem = {}) => {
    const figureRefs = [...new Map(
      [...new Set(customSystem.figure_refs ?? [])]
        .map(id => figureMetadata.get(id))
        .filter(Boolean)
        .map(ref => [ref.id, ref])
    ).values()];
    const tileIds = [...new Set(customSystem.tile_ids ?? [])].filter(id => TILING_REGISTRY[id]);
    const customPolycubes = customSystem.polycubes ?? [];
    const customPolyhedra = customSystem.polyhedra ?? [];
    const customName = customSystem.name || "Mixed system";
    const polycubeLattice = normalizePolycubeLattice(customSystem.polycube_lattice);
    return {
      name: customName,
      category: ["Mixed"],
      default_viz: { opacities: [], internal: false },
      build: () => withPolycubeLattice(polycubeLattice, () => {
        const built = [];
        if (figureRefs.length) {
          for (const ref of figureRefs) {
            const tiles = TILING_REGISTRY[ref.mode_key].build();
            const tile = tiles[ref.tile_index];
            if (tile) built.push(tile);
          }
        } else {
          for (const id of tileIds) built.push(...TILING_REGISTRY[id].build());
        }
        customPolycubes.forEach((poly, index) => {
          const name = poly?.name || `CustomPolycube${index + 1}`;
          built.push(buildPolycubeTile(name, poly?.voxels ?? [[0, 0, 0]], { polycube_lattice: polycubeLattice }));
        });
        customPolyhedra.forEach((polyhedron, index) => {
          const name = polyhedron?.name || `CustomPolyhedron${index + 1}`;
          built.push(buildLatticePolyhedronTile(
            name,
            polyhedron?.vertices,
            polyhedron?.faces
          ));
        });
        return built.length ? built : TILING_REGISTRY.cube.build();
      })
    };
  };

  return {
    SCALE,
    POLYCUBE_SOLID_ANGLE_MAX,
    LEGACY_SOLID_ANGLE_MAX,
    COLOR_PALETTE,
    BASE_COLOR_PALETTE_SIZE,
    TRANSLATIONAL_CELL_COLOR_OFFSET,
    TILING_REGISTRY,
    metadata,
    options,
    figureCatalog,
    normalizePolycubeLattice,
    displayTileName,
    solidAngleValues,
    addMirrorsIfChiral,
    withPolycubeLattice,
    buildPolycubeTile,
    buildLatticePolyhedronTile,
    convexEdgeAngleObstruction,
    buildCustomSystem
  };
})();
