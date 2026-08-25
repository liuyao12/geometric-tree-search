const rounded = value => Math.round(Number(value) * 1e9) / 1e9;
const vectorKey = vector => vector.map(value => value === 0 ? 0 : rounded(value)).join(",");
const weightKey = value => String(rounded(value));

const identity = Object.freeze([
  Object.freeze([1, 0, 0]),
  Object.freeze([0, 1, 0]),
  Object.freeze([0, 0, 1])
]);

const transform = (matrix, vector) => [
  matrix[0][0] * vector[0] + matrix[0][1] * vector[1] + matrix[0][2] * vector[2],
  matrix[1][0] * vector[0] + matrix[1][1] * vector[1] + matrix[1][2] * vector[2],
  matrix[2][0] * vector[0] + matrix[2][1] * vector[1] + matrix[2][2] * vector[2]
];

/**
 * Cold-start GCTS-I failure markings for lattice tilings.
 *
 * A terminal frontier obstruction is represented by the placed tiles in the
 * complete geometric influence neighbourhood of its unfillable lattice point.
 * Coordinates are relative to that point.  Trying every configured lattice
 * rotation makes the representation equivariant, while subset matching lets
 * the same obstruction reject a later state containing harmless extra tiles.
 *
 * `reach` must cover the maximum axis span of every candidate tile.  Then a
 * placement outside the marked neighbourhood cannot intersect any candidate
 * covering the frontier point, so the recorded obstruction is an exact local
 * nogood rather than a learned guess.
 */
export class GeometricFrontierMarking {
  constructor({
    rotations = [identity],
    reach,
    maxClauses = 20000,
    minContext = 1,
    maxContext = Infinity,
    activationFailures = 0,
    usePivotIndex = true
  } = {}) {
    if (!Number.isFinite(reach) || reach < 0) throw new Error("GeometricFrontierMarking needs a finite non-negative reach");
    this.rotations = rotations?.length ? rotations : [identity];
    this.reach = reach;
    this.maxClauses = Math.max(0, Math.floor(maxClauses));
    this.minContext = Math.max(0, Math.floor(minContext));
    this.maxContext = Number.isFinite(maxContext) ? Math.max(this.minContext, Math.floor(maxContext)) : Infinity;
    this.activationFailures = Math.max(0, Math.floor(activationFailures));
    this.usePivotIndex = usePivotIndex !== false;
    this.clauses = [];
    this.signatures = new Set();
    this.byWeight = new Map();
    this.byWeightPivot = new Map();
    this.tokenFrequency = new Map();
    this.observedFailures = 0;
    this.duplicates = 0;
    this.skippedSmall = 0;
    this.skippedLarge = 0;
    this.capacityReached = false;
    this.frontierChecks = 0;
    this.clauseChecks = 0;
    this.linearClauseChecks = 0;
    this.prunes = 0;
    this.contextTokens = 0;
    this.maxContextTokens = 0;
    this.payloadBytes = 0;
  }

  placementBounds(placement) {
    const translation = placement.translation ?? [0, 0, 0];
    const vertices = placement.orient?.verts ?? placement.vertices ?? [];
    if (!vertices.length) return null;
    const mins = [Infinity, Infinity, Infinity];
    const maxs = [-Infinity, -Infinity, -Infinity];
    for (const vertex of vertices) {
      for (let axis = 0; axis < 3; axis += 1) {
        const coordinate = vertex[axis] + translation[axis];
        mins[axis] = Math.min(mins[axis], coordinate);
        maxs[axis] = Math.max(maxs[axis], coordinate);
      }
    }
    return { mins, maxs };
  }

  isLocal(placement, point) {
    const bounds = this.placementBounds(placement);
    if (!bounds) return false;
    for (let axis = 0; axis < 3; axis += 1) {
      const distance = point[axis] < bounds.mins[axis]
        ? bounds.mins[axis] - point[axis]
        : point[axis] > bounds.maxs[axis]
          ? point[axis] - bounds.maxs[axis]
          : 0;
      if (distance > this.reach + 1e-9) return false;
    }
    return true;
  }

  localPlacements(placements, point) {
    return placements.filter(placement => this.isLocal(placement, point));
  }

  placementToken(placement, point, rotation) {
    const translation = placement.translation ?? [0, 0, 0];
    const vertices = placement.orient?.verts ?? placement.vertices ?? [];
    const transformedVertices = vertices.map(vertex => transform(rotation, [
      vertex[0] + translation[0] - point[0],
      vertex[1] + translation[1] - point[1],
      vertex[2] + translation[2] - point[2]
    ]));
    transformedVertices.sort((left, right) => vectorKey(left).localeCompare(vectorKey(right)));
    return `${placement.prototile_idx ?? 0}|${transformedVertices.map(vectorKey).join("/")}`;
  }

  variants(local, point) {
    return this.rotations.map(rotation =>
      local.map(placement => this.placementToken(placement, point, rotation)).sort()
    );
  }

  encode(point, weight, placements, metadata = {}) {
    this.observedFailures += 1;
    const local = this.localPlacements(placements, point);
    if (local.length < this.minContext) {
      this.skippedSmall += 1;
      return { encoded: false, reason: "context-too-small" };
    }
    if (local.length > this.maxContext) {
      // Never truncate an obstruction: that would turn a sound marking into
      // an unsupported generalization.
      this.skippedLarge += 1;
      return { encoded: false, reason: "context-too-large" };
    }
    if (this.clauses.length >= this.maxClauses) {
      this.capacityReached = true;
      return { encoded: false, reason: "capacity" };
    }
    const key = weightKey(weight);
    const variants = [...new Map(this.variants(local, point).map(required => [required.join(";"), required])).values()];
    const fresh = variants.filter(required => !this.signatures.has(`${key}=>${required.join(";")}`));
    if (!fresh.length) {
      this.duplicates += 1;
      return { encoded: true, duplicate: true };
    }
    if (this.clauses.length + fresh.length > this.maxClauses) {
      this.capacityReached = true;
      return { encoded: false, reason: "capacity" };
    }
    const frequencies = this.tokenFrequency.get(key) ?? new Map();
    for (const required of fresh) {
      const signature = `${key}=>${required.join(";")}`;
      const pivot = required.length
        ? required.reduce((best, token) => {
            const frequency = frequencies.get(token) ?? 0;
            const bestFrequency = frequencies.get(best) ?? 0;
            return frequency < bestFrequency || (frequency === bestFrequency && token < best) ? token : best;
          })
        : null;
      const clause = {
        id: this.clauses.length,
        weight: key,
        required,
        pivot,
        signature,
        metadata: { ...metadata }
      };
      this.signatures.add(signature);
      this.clauses.push(clause);
      // The JSON payload is a deterministic lower-bound proxy for retained
      // marking memory. It excludes JavaScript container/object overhead.
      this.payloadBytes += JSON.stringify(clause).length;
      if (!this.byWeight.has(key)) this.byWeight.set(key, []);
      this.byWeight.get(key).push(clause);
      if (!this.byWeightPivot.has(key)) this.byWeightPivot.set(key, new Map());
      const pivotMap = this.byWeightPivot.get(key);
      const pivotKey = pivot ?? "";
      if (!pivotMap.has(pivotKey)) pivotMap.set(pivotKey, []);
      pivotMap.get(pivotKey).push(clause);
      for (const token of required) frequencies.set(token, (frequencies.get(token) ?? 0) + 1);
      this.contextTokens += required.length;
      this.maxContextTokens = Math.max(this.maxContextTokens, required.length);
    }
    this.tokenFrequency.set(key, frequencies);
    return { encoded: true, duplicate: false, clauses_added: fresh.length, context: fresh[0]?.length ?? 0 };
  }

  compatible(point, weight, placements, count = true) {
    if (this.observedFailures < this.activationFailures || !this.clauses.length) return true;
    const key = weightKey(weight);
    const allClauses = this.byWeight.get(key);
    if (!allClauses?.length) return true;
    const local = this.localPlacements(placements, point);
    if (local.length < this.minContext) return true;
    this.frontierChecks += 1;
    // Every symmetry image was indexed at encode time, so a query needs only
    // one coordinate frame. This preserves full equivariance without paying
    // for 24 transformed context scans at every search node.
    for (const tokens of this.variants(local, point).slice(0, 1)) {
      const available = new Set(tokens);
      const clauses = this.usePivotIndex
        ? [
            ...(this.byWeightPivot.get(key)?.get("") ?? []),
            ...tokens.flatMap(token => this.byWeightPivot.get(key)?.get(token) ?? [])
          ]
        : allClauses;
      const seen = new Set();
      this.linearClauseChecks += allClauses.length;
      for (const clause of clauses) {
        if (seen.has(clause.id)) continue;
        seen.add(clause.id);
        this.clauseChecks += 1;
        if (clause.required.length > available.size) continue;
        if (!clause.required.every(token => available.has(token))) continue;
        if (count) this.prunes += 1;
        return false;
      }
    }
    return true;
  }

  firstConflict(frontierOptions, placements, count = true) {
    for (const option of frontierOptions) {
      const point = option.point ?? String(option.pointKey ?? option.point_key).split(",").map(Number);
      if (!this.compatible(point, option.weight, placements, count)) return option;
    }
    return null;
  }

  stats() {
    return {
      observed_failures: this.observedFailures,
      clauses: this.clauses.length,
      duplicates: this.duplicates,
      skipped_small: this.skippedSmall,
      skipped_large: this.skippedLarge,
      capacity_reached: this.capacityReached,
      activated: this.observedFailures >= this.activationFailures,
      reach: this.reach,
      rotations: this.rotations.length,
      pivot_index_enabled: this.usePivotIndex,
      frontier_checks: this.frontierChecks,
      clause_checks: this.clauseChecks,
      linear_clause_checks: this.linearClauseChecks,
      avoided_clause_checks: this.linearClauseChecks - this.clauseChecks,
      prunes: this.prunes,
      average_context_tokens: this.clauses.length ? this.contextTokens / this.clauses.length : 0,
      max_context_tokens: this.maxContextTokens,
      context_tokens: this.contextTokens,
      payload_bytes: this.payloadBytes
    };
  }
}
