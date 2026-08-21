import { polycubeKey, polycubeOrientations } from "./polycube-enumerator.js";

const mod = (value, modulus) => ((value % modulus) + modulus) % modulus;
const cross = (left, right) => [
  left[1] * right[2] - left[2] * right[1],
  left[2] * right[0] - left[0] * right[2],
  left[0] * right[1] - left[1] * right[0]
];
const dot = (left, right) => left.reduce((sum, value, index) => sum + value * right[index], 0);

/**
 * Find a one-copy periodic quotient. A bijection from the oriented tile cells
 * to Z/nZ proves that translates by the kernel of the homomorphism partition
 * all of Z^3. This is sufficient, not necessary, and runs in O(orientations*n^3).
 */
export function findPolycubeCyclicTiling(voxels, options = {}) {
  const includeReflections = !!options.includeReflections;
  const orientations = polycubeOrientations(voxels, { includeReflections });
  const modulus = voxels.length;
  let tests = 0;
  const startedAt = performance.now();
  for (let orientationIndex = 0; orientationIndex < orientations.length; orientationIndex++) {
    const orientation = orientations[orientationIndex];
    for (let b = 0; b < modulus; b++) for (let c = 0; c < modulus; c++) {
      tests += 1;
      const residues = new Set(orientation.voxels.map(([x, y, z]) =>
        mod(x + b * y + c * z, modulus)
      ));
      if (residues.size !== modulus) continue;
      return {
        kind: "one_tile_cyclic_quotient",
        certified: true,
        can_tile: true,
        copies: 1,
        orientation_index: orientationIndex,
        orientation_key: orientation.key,
        coefficients: [1, b, c],
        modulus,
        period_vectors: [[modulus, 0, 0], [-b, 1, 0], [-c, 0, 1]],
        quotient_cells: [...residues].sort((left, right) => left - right),
        isohedral: { certified: true, tile_orbits: 1 },
        tests,
        milliseconds: Math.round(performance.now() - startedAt)
      };
    }
  }
  return {
    kind: "cyclic_quotient_search",
    certified: false,
    can_tile: null,
    tests,
    milliseconds: Math.round(performance.now() - startedAt)
  };
}

const hnfCandidates = volume => {
  const out = [];
  for (let a = 1; a <= volume; a++) {
    if (volume % a) continue;
    for (let d = 1; d <= volume / a; d++) {
      if (volume % (a * d)) continue;
      const f = volume / (a * d);
      for (let b = 0; b < a; b++) for (let c = 0; c < a; c++) for (let e = 0; e < d; e++) {
        out.push({
          a, b, c, d, e, f,
          vectors: [[a, 0, 0], [b, d, 0], [c, e, f]],
          span: Math.max(a, d, f) - Math.min(a, d, f),
          skew: b + c + e
        });
      }
    }
  }
  return out.sort((left, right) => left.span - right.span || left.skew - right.skew
    || left.a - right.a || left.d - right.d || left.f - right.f
    || left.b - right.b || left.c - right.c || left.e - right.e);
};

const reduceHnf = ([inputX, inputY, inputZ], hnf) => {
  let x = inputX;
  let y = inputY;
  let z = inputZ;
  let q = Math.floor(z / hnf.f);
  x -= q * hnf.c;
  y -= q * hnf.e;
  z -= q * hnf.f;
  q = Math.floor(y / hnf.d);
  x -= q * hnf.b;
  y -= q * hnf.d;
  q = Math.floor(x / hnf.a);
  x -= q * hnf.a;
  return [mod(x, hnf.a), mod(y, hnf.d), mod(z, hnf.f)];
};

const quotientMask = (cells, translation, hnf) => {
  let mask = 0n;
  for (const cell of cells) {
    const [x, y, z] = reduceHnf([
      cell[0] + translation[0],
      cell[1] + translation[1],
      cell[2] + translation[2]
    ], hnf);
    const index = x + hnf.a * (y + hnf.d * z);
    const bit = 1n << BigInt(index);
    if (mask & bit) return null;
    mask |= bit;
  }
  return mask;
};

/** Find a periodic torus certificate in the requested inclusive copy range. */
export function findPolycubePeriodicTiling(voxels, options = {}) {
  const maxCopies = Math.max(1, Math.floor(Number(options.maxCopies) || 4));
  const minCopies = Math.max(1, Math.min(maxCopies,
    Math.floor(Number(options.minCopies) || 1)));
  const cyclic = minCopies <= 1 ? findPolycubeCyclicTiling(voxels, options) : null;
  if (cyclic?.certified) return cyclic;
  const includeReflections = !!options.includeReflections;
  const timeLimitMs = Math.max(1, Number(options.timeLimitMs) || 1000);
  const nodeLimit = Math.max(1, Math.floor(Number(options.nodeLimit) || 100000));
  const startedAt = performance.now();
  const orientations = polycubeOrientations(voxels, { includeReflections });
  const rootOrientationIndex = Math.max(0, orientations.findIndex(orientation =>
    orientation.key === polycubeKey(voxels)
  ));
  let nodes = 0;
  let hnfVisited = 0;
  const hnfExhaustedByCopies = {};
  const overBudget = () => nodes >= nodeLimit || performance.now() - startedAt >= timeLimitMs;

  for (let copies = minCopies; copies <= maxCopies; copies++) {
    const volume = voxels.length * copies;
    const allMask = (1n << BigInt(volume)) - 1n;
    let hnfAtCopies = 0;
    for (const hnf of hnfCandidates(volume)) {
      hnfVisited += 1;
      hnfAtCopies += 1;
      if (overBudget()) return {
        kind: "periodic_torus_search", certified: false, can_tile: null,
        stopped_by: nodes >= nodeLimit ? "node_limit" : "time_limit",
        nodes, hnf_visited: hnfVisited, min_copies: minCopies,
        max_copies: maxCopies, hnf_exhausted_by_copies: hnfExhaustedByCopies,
        active_copies: copies, active_hnf_visited: hnfAtCopies,
        milliseconds: Math.round(performance.now() - startedAt)
      };
      const rootMask = quotientMask(voxels, [0, 0, 0], hnf);
      if (rootMask === null) continue;
      const placementByMask = new Map();
      for (let orientationIndex = 0; orientationIndex < orientations.length; orientationIndex++) {
        const orientation = orientations[orientationIndex];
        for (let x = 0; x < hnf.a; x++) for (let y = 0; y < hnf.d; y++) for (let z = 0; z < hnf.f; z++) {
          const translation = [x, y, z];
          const mask = quotientMask(orientation.voxels, translation, hnf);
          if (mask === null || (mask & rootMask)) continue;
          if (!placementByMask.has(mask)) placementByMask.set(mask, {
            mask, orientation_index: orientationIndex,
            orientation_key: orientation.key, translation
          });
        }
      }
      const placements = [...placementByMask.values()];
      const byCell = Array.from({ length: volume }, () => []);
      for (const placement of placements) for (let index = 0; index < volume; index++) {
        if (placement.mask & (1n << BigInt(index))) byCell[index].push(placement);
      }
      const failed = new Set();
      const chosen = [];
      const search = remaining => {
        if (!remaining) return chosen.length === copies - 1 ? chosen.slice() : null;
        if (chosen.length >= copies - 1 || overBudget()) return null;
        nodes += 1;
        if (failed.has(remaining)) return null;
        let pivot = null;
        for (let index = 0; index < volume; index++) {
          const bit = 1n << BigInt(index);
          if (!(remaining & bit)) continue;
          const optionsForCell = byCell[index].filter(placement =>
            (placement.mask & remaining) === placement.mask
          );
          if (!optionsForCell.length) { failed.add(remaining); return null; }
          if (!pivot || optionsForCell.length < pivot.length) pivot = optionsForCell;
        }
        for (const placement of pivot ?? []) {
          chosen.push(placement);
          const solution = search(remaining ^ placement.mask);
          if (solution) return solution;
          chosen.pop();
        }
        failed.add(remaining);
        return null;
      };
      const solution = search(allMask ^ rootMask);
      if (!solution) continue;
      return {
        kind: copies === 2 ? "two_tile_periodic_torus" : `${copies}_tile_periodic_torus`,
        certified: true,
        can_tile: true,
        copies,
        period_vectors: hnf.vectors,
        placements: [
          {
            orientation_index: rootOrientationIndex,
            orientation_key: orientations[rootOrientationIndex].key,
            translation: [0, 0, 0]
          },
          ...solution.map(({ mask: _mask, ...placement }) => placement)
        ],
        isohedral: { certified: copies === 1, tile_orbits: null },
        nodes,
        hnf_visited: hnfVisited,
        min_copies: minCopies,
        max_copies: maxCopies,
        hnf_exhausted_by_copies: hnfExhaustedByCopies,
        milliseconds: Math.round(performance.now() - startedAt)
      };
    }
    hnfExhaustedByCopies[copies] = hnfAtCopies;
  }
  return {
    kind: "periodic_torus_search", certified: false, can_tile: null,
    stopped_by: null, nodes, hnf_visited: hnfVisited,
    min_copies: minCopies, max_copies: maxCopies,
    hnf_exhausted_by_copies: hnfExhaustedByCopies,
    milliseconds: Math.round(performance.now() - startedAt)
  };
}

/**
 * Replay a periodic certificate without using the HNF search implementation.
 * Quotient classes are computed from Cramer's rule for the three supplied
 * period vectors, so this also verifies skew and cyclic quotient bases.
 */
export function verifyPolycubePeriodicCertificate(voxels, certificate, options = {}) {
  const fail = reason => ({ verified: false, reason });
  if (!certificate?.certified || certificate.can_tile !== true) return fail("not_a_certificate");
  const basis = certificate.period_vectors;
  if (!Array.isArray(basis) || basis.length !== 3
    || basis.some(vector => !Array.isArray(vector) || vector.length !== 3
      || vector.some(value => !Number.isInteger(value)))) {
    return fail("invalid_period_basis");
  }
  const signedDeterminant = dot(basis[0], cross(basis[1], basis[2]));
  const determinant = Math.abs(signedDeterminant);
  if (!determinant) return fail("singular_period_basis");
  const copies = Math.max(1, Math.floor(Number(certificate.copies) || 1));
  if (determinant !== voxels.length * copies) return fail("covolume_mismatch");
  const orientations = polycubeOrientations(voxels, {
    includeReflections: !!options.includeReflections
  });
  const placements = certificate.placements ?? [{
    orientation_index: certificate.orientation_index,
    orientation_key: certificate.orientation_key,
    translation: [0, 0, 0]
  }];
  if (placements.length !== copies) return fail("copy_count_mismatch");
  const quotientClasses = new Set();
  const numerators = [
    cross(basis[1], basis[2]),
    cross(basis[2], basis[0]),
    cross(basis[0], basis[1])
  ];
  for (const placement of placements) {
    const orientation = orientations.find(item => item.key === placement.orientation_key)
      ?? orientations[placement.orientation_index];
    if (!orientation) return fail("unknown_orientation");
    if (!Array.isArray(placement.translation) || placement.translation.length !== 3
      || placement.translation.some(value => !Number.isInteger(value))) {
      return fail("invalid_translation");
    }
    for (const cell of orientation.voxels) {
      const point = cell.map((value, axis) => value + placement.translation[axis]);
      const signature = numerators.map(vector => mod(dot(point, vector), determinant)).join(",");
      if (quotientClasses.has(signature)) return fail("quotient_overlap");
      quotientClasses.add(signature);
    }
  }
  if (quotientClasses.size !== determinant) return fail("quotient_not_full");
  return {
    verified: true,
    determinant,
    copies,
    quotient_classes: quotientClasses.size,
    method: "cramers_rule_quotient_partition"
  };
}
