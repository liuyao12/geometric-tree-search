import { GeometricFailureMemo } from "../../assets/geometric-failure-memo.js";

const vecKey = (point) => point.map(value => Math.round(value * 1e9) / 1e9).join(",");

const clonePlacement = (placement) => ({
  prototile_idx: placement.prototile_idx,
  translation: placement.translation.slice(),
  orient: placement.orient
});

const multiply = (matrix, vector) => matrix.map(row =>
  row[0] * vector[0] + row[1] * vector[1] + row[2] * vector[2]
);

const transposeMultiply = (matrix, vector) => [0, 1, 2].map(column =>
  matrix[0][column] * vector[0] + matrix[1][column] * vector[1] + matrix[2][column] * vector[2]
);

const localToGlobal = (placement, point) => {
  const matrix = placement.orient.__mark_matrix;
  const shift = placement.orient.__mark_shift;
  const oriented = multiply(matrix, point).map((value, axis) => value - shift[axis]);
  return oriented.map((value, axis) => value + placement.translation[axis]);
};

const globalToLocal = (placement, point) => {
  const matrix = placement.orient.__mark_matrix;
  const shift = placement.orient.__mark_shift;
  const oriented = point.map((value, axis) => value - placement.translation[axis] + shift[axis]);
  return transposeMultiply(matrix, oriented);
};

const siteKey = (prototileIndex, point) => `${prototileIndex}:${vecKey(point)}`;

class DisjointSet {
  constructor(values) {
    this.parent = new Map([...values].map(value => [value, value]));
  }
  find(value) {
    const parent = this.parent.get(value);
    if (parent === value) return value;
    const root = this.find(parent);
    this.parent.set(value, root);
    return root;
  }
  union(left, right) {
    const a = this.find(left), b = this.find(right);
    if (a !== b) this.parent.set(b, a);
  }
}

/**
 * A transactional, equivariant marking learner for lattice placements.
 *
 * The support starts empty.  A failed branch contributes one disequality
 * clause.  Previously surviving prefixes contribute equality constraints.
 * A proposal is committed only when every protected prefix still replays and
 * every earlier failure remains rejected.
 */
export class OnlineFailureMarking {
  constructor({ max_reach = null, enable_pair_marking = false } = {}) {
    this.maxReach = Number.isFinite(max_reach) ? Math.max(0, max_reach | 0) : null;
    this.enablePairMarking = !!enable_pair_marking;
    this.support = new Map();
    this.failures = [];
    this.failureLedger = [];
    this.pendingFailures = [];
    this.protectedPatches = [];
    this.revision = 0;
    this.unencodable = 0;
    this.geometricMemo = new GeometricFailureMemo({
      describePlacement: placement => placement?.orient && placement?.translation ? {
        kind: String(placement.prototile_idx),
        orientation: placement.orient.__orientation_id
          ?? placement.orient.__mark_matrix?.flat().join(",")
          ?? "unknown",
        translation: placement.translation
      } : null
    });
  }

  snapshotPlacements(placements) {
    return placements.map(clonePlacement);
  }

  marksForPlacement(placement, support = this.support) {
    const marks = new Map();
    for (const [key, entry] of support) {
      if (entry.prototile_idx !== placement.prototile_idx) continue;
      marks.set(vecKey(localToGlobal(placement, entry.point)), { key, color: entry.color });
    }
    return marks;
  }

  compatible(candidate, context, support = this.support) {
    if (support === this.support && !this.geometricMemo.compatible(candidate, context)) return false;
    if (!this.enablePairMarking) return true;
    if (!support.size) return true;
    const candidateMarks = this.marksForPlacement(candidate, support);
    for (const placement of context) {
      const existingMarks = this.marksForPlacement(placement, support);
      for (const [globalKey, mark] of candidateMarks) {
        const other = existingMarks.get(globalKey);
        if (other && other.color !== mark.color) return false;
      }
    }
    return true;
  }

  patchCompatible(patch, support) {
    for (let index = 0; index < patch.length; index++) {
      if (!this.compatible(patch[index], patch.slice(0, index), support)) return false;
    }
    return true;
  }

  overlappingVariablePairs(candidate, context, support) {
    const candidateMarks = this.marksForPlacement(candidate, support);
    const pairs = [];
    for (const placement of context) {
      for (const [globalKey, other] of this.marksForPlacement(placement, support)) {
        const mark = candidateMarks.get(globalKey);
        if (mark) pairs.push([mark.key, other.key]);
      }
    }
    return pairs;
  }

  solve(entries, protectedPatches, failures) {
    const support = new Map(entries.map(entry => [entry.key, { ...entry, point: entry.point.slice(), color: 0 }]));
    const dsu = new DisjointSet(support.keys());
    for (const patch of protectedPatches) {
      for (let index = 1; index < patch.length; index++) {
        for (const [left, right] of this.overlappingVariablePairs(patch[index], patch.slice(0, index), support)) {
          dsu.union(left, right);
        }
      }
    }
    for (const failure of failures) {
      const pairs = this.overlappingVariablePairs(failure.candidate, failure.context, support);
      if (!pairs.some(([left, right]) => dsu.find(left) !== dsu.find(right))) return null;
    }
    const roots = [...new Set([...support.keys()].map(key => dsu.find(key)))].sort();
    const colors = new Map(roots.map((root, index) => [root, index + 1]));
    for (const [key, entry] of support) entry.color = colors.get(dsu.find(key));
    if (!protectedPatches.every(patch => this.patchCompatible(patch, support))) return null;
    if (!failures.every(failure => !this.compatible(failure.candidate, failure.context, support))) return null;
    return support;
  }

  candidateProbePoints(reach) {
    if (reach === 0) return [[0, 0, 0]];
    const points = [];
    for (let axis = 0; axis < 3; axis++) {
      for (const sign of [-1, 1]) {
        const point = [0, 0, 0];
        point[axis] = sign * reach;
        points.push(point);
      }
    }
    return points;
  }

  failedBranchReach(context, candidate) {
    // D grows only to the spatial extent represented by this failed branch.
    // This replaces the former arbitrary global radius of 64.
    let reach = 0;
    for (const placement of context) {
      const candidateLocal = globalToLocal(candidate, placement.translation);
      const contextLocal = globalToLocal(placement, candidate.translation);
      reach = Math.max(reach, ...candidateLocal.map(Math.abs), ...contextLocal.map(Math.abs));
    }
    return Math.max(0, Math.ceil(reach));
  }

  learn(contextPlacements, failedCandidate) {
    const context = this.snapshotPlacements(contextPlacements);
    const candidate = clonePlacement(failedCandidate);
    const certificate = { context, candidate };
    this.failureLedger.push(certificate);
    const geometric = this.geometricMemo.encode(context, candidate, { failure: this.failureLedger.length });
    if (!this.enablePairMarking) {
      if (!geometric.duplicate) this.revision += 1;
      return {
        committed: true,
        geometric_only: true,
        revision: this.revision,
        reach: 0,
        support_sites: 0,
        failures: this.failureLedger.length,
        observed_failures: this.failureLedger.length,
        pending_failures: 0,
        geometric_clauses: this.geometricMemo.clauses.length
      };
    }
    const protectedPatches = [...this.protectedPatches, context];
    const failures = [...this.failures, certificate];
    const reachLimit = this.maxReach ?? this.failedBranchReach(context, candidate);

    for (let reach = 0; reach <= reachLimit; reach++) {
      for (const candidatePoint of this.candidateProbePoints(reach)) {
        const globalPoint = localToGlobal(candidate, candidatePoint);
        for (const placement of context) {
          const existingPoint = globalToLocal(placement, globalPoint);
          if (!existingPoint.every(Number.isInteger)) continue;
          const additions = [
            { key: siteKey(candidate.prototile_idx, candidatePoint), prototile_idx: candidate.prototile_idx, point: candidatePoint },
            { key: siteKey(placement.prototile_idx, existingPoint), prototile_idx: placement.prototile_idx, point: existingPoint }
          ];
          const entries = [...this.support.values()].map(entry => ({ ...entry, point: entry.point.slice() }));
          const known = new Set(entries.map(entry => entry.key));
          for (const entry of additions) if (!known.has(entry.key)) { entries.push(entry); known.add(entry.key); }
          const solved = this.solve(entries, protectedPatches, failures);
          if (!solved) continue;
          this.support = solved;
          this.protectedPatches = protectedPatches;
          this.failures = failures;
          this.pendingFailures = this.pendingFailures.filter(failure =>
            this.compatible(failure.candidate, failure.context, this.support)
          );
          this.revision += 1;
          return {
            committed: true,
            revision: this.revision,
            reach,
            support_sites: this.support.size,
            failures: this.failures.length,
            observed_failures: this.failureLedger.length,
            pending_failures: this.pendingFailures.length
          };
        }
      }
    }
    this.unencodable += 1;
    this.pendingFailures.push(certificate);
    return { committed: false, reason: "no_safe_mark_extension", unencodable: this.unencodable, observed_failures: this.failureLedger.length, pending_failures: this.pendingFailures.length, reach_limit: reachLimit };
  }

  stats() {
    const geometric = this.geometricMemo.stats();
    return {
      revision: this.revision,
      support_sites: this.support.size,
      learned_failures: this.failureLedger.length,
      observed_failures: this.failureLedger.length,
      encoded_failures: this.failureLedger.length,
      pending_failures: 0,
      pair_encoded_failures: this.enablePairMarking ? this.failures.length : 0,
      pair_pending_failures: this.enablePairMarking ? this.pendingFailures.length : 0,
      geometric_clauses: geometric.clauses,
      geometric_prunes: geometric.prunes,
      pair_marking_enabled: this.enablePairMarking,
      protected_prefixes: this.protectedPatches.length,
      unencodable: this.unencodable
    };
  }
}
