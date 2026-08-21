import { polycubeKey, polycubeOrientations } from "./polycube-enumerator.js";

const mod = (value, modulus) => ((value % modulus) + modulus) % modulus;
const cross = (left, right) => [
  left[1] * right[2] - left[2] * right[1],
  left[2] * right[0] - left[0] * right[2],
  left[0] * right[1] - left[1] * right[0]
];
const dot = (left, right) => left.reduce((sum, value, index) => sum + value * right[index], 0);

export const polycubePeriodicResumeHnfIndex = periodicFast => Math.max(0, Number(
  periodicFast?.active_hnf_index
  ?? ((periodicFast?.hnf_skipped ?? 0) + (periodicFast?.hnf_visited ?? 1) - 1)
));

/**
 * Find a one-copy periodic quotient. A bijection from the oriented tile cells
 * to Z/nZ proves that translates by the kernel of the homomorphism partition
 * all of Z^3. This is sufficient, not necessary, and runs in O(orientations*n^3).
 */
export function findPolycubeCyclicTiling(voxels, options = {}) {
  const includeReflections = !!options.includeReflections;
  const orientations = options.orientations
    ?? polycubeOrientations(voxels, { includeReflections });
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

const hnfCandidateCache = new Map();

const hnfCandidates = volume => {
  if (hnfCandidateCache.has(volume)) return hnfCandidateCache.get(volume);
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
  const sorted = out.sort((left, right) => left.span - right.span || left.skew - right.skew
    || left.a - right.a || left.d - right.d || left.f - right.f
    || left.b - right.b || left.c - right.c || left.e - right.e);
  hnfCandidateCache.set(volume, sorted);
  return sorted;
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

// JavaScript's integer bitwise operators are substantially faster than
// BigInt for the small quotients that dominate the census. Keep bit 31 out of
// the representation so every mask remains a non-negative signed integer.
const quotientNumberMask = (cells, translation, hnf) => {
  let mask = 0;
  for (const cell of cells) {
    const [x, y, z] = reduceHnf([
      cell[0] + translation[0],
      cell[1] + translation[1],
      cell[2] + translation[2]
    ], hnf);
    const index = x + hnf.a * (y + hnf.d * z);
    const bit = 2 ** index;
    if (mask & bit) return null;
    mask |= bit;
  }
  return mask;
};

const quotientIndex = (cell, translation, hnf) => {
  const [x, y, z] = reduceHnf([
    cell[0] + translation[0],
    cell[1] + translation[1],
    cell[2] + translation[2]
  ], hnf);
  return x + hnf.a * (y + hnf.d * z);
};

/** Find a periodic torus certificate in the requested inclusive copy range. */
export function findPolycubePeriodicTiling(voxels, options = {}) {
  const maxCopies = Math.max(1, Math.floor(Number(options.maxCopies) || 4));
  const minCopies = Math.max(1, Math.min(maxCopies,
    Math.floor(Number(options.minCopies) || 1)));
  const includeReflections = !!options.includeReflections;
  const hnfStartIndex = Math.max(0, Math.floor(Number(options.hnfStartIndex) || 0));
  const hnfEndIndex = options.hnfEndIndex == null
    ? Infinity
    : Math.max(hnfStartIndex, Math.floor(Number(options.hnfEndIndex) || 0));
  const assumeHnfPrefixExhausted = !!options.assumeHnfPrefixExhausted;
  const orientations = polycubeOrientations(voxels, { includeReflections });
  const cyclic = minCopies <= 1
    ? findPolycubeCyclicTiling(voxels, { ...options, orientations })
    : null;
  if (cyclic?.certified) return cyclic;
  const timeLimitMs = Math.max(1, Number(options.timeLimitMs) || 1000);
  const nodeLimit = Math.max(1, Math.floor(Number(options.nodeLimit) || 100000));
  const startedAt = performance.now();
  const cpuBudgetEnabled = options.timeBudgetMode === "cpu"
    && typeof process !== "undefined"
    && typeof process.cpuUsage === "function";
  const cpuStartedAt = cpuBudgetEnabled ? process.cpuUsage() : null;
  const budgetMilliseconds = () => {
    if (!cpuBudgetEnabled) return performance.now() - startedAt;
    const usage = process.cpuUsage(cpuStartedAt);
    return (usage.user + usage.system) / 1000;
  };
  const rootOrientationIndex = Math.max(0, orientations.findIndex(orientation =>
    orientation.key === polycubeKey(voxels)
  ));
  let nodes = 0;
  let hnfVisited = 0;
  let hnfSkipped = 0;
  const hnfExhaustedByCopies = {};
  const overBudget = () => nodes >= nodeLimit || budgetMilliseconds() >= timeLimitMs;

  for (let copies = minCopies; copies <= maxCopies; copies++) {
    const volume = voxels.length * copies;
    const useNumberMasks = volume <= 30;
    const allMask = useNumberMasks ? 2 ** volume - 1 : (1n << BigInt(volume)) - 1n;
    const makeMask = useNumberMasks ? quotientNumberMask : quotientMask;
    const bitAt = useNumberMasks
      ? index => 2 ** index
      : index => 1n << BigInt(index);
    let hnfAtCopies = 0;
    const candidatesAtCopies = hnfCandidates(volume);
    const rangeStartAtCopies = copies === minCopies
      ? Math.min(hnfStartIndex, candidatesAtCopies.length)
      : 0;
    const rangeEndAtCopies = copies === minCopies
      ? Math.max(rangeStartAtCopies, Math.min(hnfEndIndex, candidatesAtCopies.length))
      : candidatesAtCopies.length;
    const fullPrefixKnownAtCopies = rangeStartAtCopies === 0 || assumeHnfPrefixExhausted;
    hnfSkipped += rangeStartAtCopies;
    for (let hnfIndex = rangeStartAtCopies; hnfIndex < rangeEndAtCopies; hnfIndex++) {
      const hnf = candidatesAtCopies[hnfIndex];
      hnfVisited += 1;
      hnfAtCopies += 1;
      if (overBudget()) return {
        kind: "periodic_torus_search", certified: false, can_tile: null,
        stopped_by: nodes >= nodeLimit ? "node_limit" : "time_limit",
        nodes, hnf_visited: hnfVisited, hnf_skipped: hnfSkipped,
        active_hnf_index: hnfIndex,
        hnf_range_start: rangeStartAtCopies,
        hnf_range_end_exclusive: rangeEndAtCopies,
        hnf_range_total: rangeEndAtCopies - rangeStartAtCopies,
        hnf_range_exhausted: false,
        min_copies: minCopies,
        max_copies: maxCopies, hnf_exhausted_by_copies: hnfExhaustedByCopies,
        active_copies: copies, active_hnf_visited: rangeStartAtCopies + hnfAtCopies,
        milliseconds: Math.round(performance.now() - startedAt)
      };
      const rootMask = makeMask(voxels, [0, 0, 0], hnf);
      if (rootMask === null) continue;
      const translations = [];
      for (let x = 0; x < hnf.a; x++) for (let y = 0; y < hnf.d; y++) {
        for (let z = 0; z < hnf.f; z++) translations.push([x, y, z]);
      }
      // Reduction modulo a skew HNF lattice is the expensive part of mask
      // construction. Compute its translation action once per quotient, then
      // assemble every oriented placement by table lookup.
      const translatedBits = translations.map(translation =>
        Array.from({ length: volume }, (_, index) => {
          const cell = [index % hnf.a,
            Math.floor(index / hnf.a) % hnf.d,
            Math.floor(index / (hnf.a * hnf.d))];
          return bitAt(quotientIndex(cell, translation, hnf));
        })
      );
      const placementByMask = new Map();
      for (let orientationIndex = 0; orientationIndex < orientations.length; orientationIndex++) {
        const orientation = orientations[orientationIndex];
        const baseIndices = orientation.voxels.map(cell =>
          quotientIndex(cell, [0, 0, 0], hnf)
        );
        if (new Set(baseIndices).size !== baseIndices.length) continue;
        for (let translationIndex = 0; translationIndex < translations.length; translationIndex++) {
          let mask = useNumberMasks ? 0 : 0n;
          for (const index of baseIndices) mask |= translatedBits[translationIndex][index];
          if (mask & rootMask) continue;
          if (!placementByMask.has(mask)) placementByMask.set(mask, {
            mask, orientation_index: orientationIndex,
            orientation_key: orientation.key,
            translation: translations[translationIndex]
          });
        }
      }
      const placements = [...placementByMask.values()];
      const remainingAfterRoot = allMask ^ rootMask;
      let solution = null;
      if (copies === 1) {
        solution = !remainingAfterRoot ? [] : null;
      } else if (copies === 2) {
        // With the root fixed, the only other tile must equal the complement.
        // This is the complete exact-cover test; no tree search is needed.
        nodes += 1;
        const complement = placementByMask.get(remainingAfterRoot);
        solution = complement ? [complement] : null;
      } else if (copies === 3) {
        // With only two placements left, exact cover is a two-sum lookup on
        // bitmasks. This replaces thousands of repeated MRV/filter scans.
        for (const placement of placements) {
          if (overBudget()) break;
          nodes += 1;
          if ((placement.mask & remainingAfterRoot) !== placement.mask) continue;
          const complement = placementByMask.get(remainingAfterRoot ^ placement.mask);
          if (!complement) continue;
          solution = [placement, complement];
          break;
        }
      } else {
        const byCell = Array.from({ length: volume }, () => []);
        for (const placement of placements) for (let index = 0; index < volume; index++) {
          if (placement.mask & bitAt(index)) byCell[index].push(placement);
        }
        const failed = new Set();
        const chosen = [];
        const search = remaining => {
          if (!remaining) return chosen.length === copies - 1 ? chosen.slice() : null;
          if (chosen.length >= copies - 1 || overBudget()) return null;
          nodes += 1;
          if (failed.has(remaining)) return null;
          let pivotCell = -1;
          let pivotSize = Infinity;
          for (let index = 0; index < volume; index++) {
            const bit = bitAt(index);
            if (!(remaining & bit)) continue;
            let optionsForCell = 0;
            for (const placement of byCell[index]) {
              if ((placement.mask & remaining) === placement.mask) optionsForCell += 1;
            }
            if (!optionsForCell) { failed.add(remaining); return null; }
            if (optionsForCell < pivotSize) {
              pivotCell = index;
              pivotSize = optionsForCell;
              if (pivotSize === 1) break;
            }
          }
          for (const placement of pivotCell < 0 ? [] : byCell[pivotCell]) {
            if ((placement.mask & remaining) !== placement.mask) continue;
            chosen.push(placement);
            const found = search(remaining ^ placement.mask);
            if (found) return found;
            chosen.pop();
          }
          failed.add(remaining);
          return null;
        };
        solution = search(remainingAfterRoot);
      }
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
        hnf_skipped: hnfSkipped,
        hnf_range_start: rangeStartAtCopies,
        hnf_range_end_exclusive: rangeEndAtCopies,
        hnf_range_total: rangeEndAtCopies - rangeStartAtCopies,
        hnf_range_exhausted: false,
        min_copies: minCopies,
        max_copies: maxCopies,
        hnf_exhausted_by_copies: hnfExhaustedByCopies,
        milliseconds: Math.round(performance.now() - startedAt)
      };
    }
    const rangeExhausted = hnfAtCopies === rangeEndAtCopies - rangeStartAtCopies;
    if (rangeExhausted && fullPrefixKnownAtCopies && rangeEndAtCopies === candidatesAtCopies.length) {
      hnfExhaustedByCopies[copies] = candidatesAtCopies.length;
    }
    if (copies === maxCopies) {
      return {
        kind: "periodic_torus_search", certified: false, can_tile: null,
        stopped_by: null, nodes, hnf_visited: hnfVisited, hnf_skipped: hnfSkipped,
        hnf_range_start: rangeStartAtCopies,
        hnf_range_end_exclusive: rangeEndAtCopies,
        hnf_range_total: rangeEndAtCopies - rangeStartAtCopies,
        hnf_range_exhausted: rangeExhausted,
        min_copies: minCopies, max_copies: maxCopies,
        hnf_exhausted_by_copies: hnfExhaustedByCopies,
        milliseconds: Math.round(performance.now() - startedAt)
      };
    }
  }
  throw new Error("unreachable periodic HNF range completion");
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
