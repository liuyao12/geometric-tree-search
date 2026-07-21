const rounded = value => Math.round(value * 1e9) / 1e9;
const vectorKey = vector => vector.map(rounded).join(",");

/**
 * Translation-equivariant geometric nogoods.
 *
 * Each clause stores a failed candidate and its complete placed context in
 * coordinates relative to that candidate. Absolute position is discarded, so
 * translated copies are recognized; requiring the complete recorded context
 * keeps the clause exact and monotone when more tiles have been placed.
 */
export class GeometricFailureMemo {
  constructor({ describePlacement, contextMatch = "subset" }) {
    this.describePlacement = describePlacement;
    this.contextMatch = contextMatch;
    this.clauses = [];
    this.byCandidate = new Map();
    this.signatures = new Set();
    this.prunes = 0;
  }

  representation(context, candidate) {
    const head = this.describePlacement(candidate);
    if (!head) return null;
    const required = [];
    for (const placement of context) {
      const descriptor = this.describePlacement(placement);
      if (!descriptor) continue;
      const relative = descriptor.translation.map((value, axis) => value - head.translation[axis]);
      required.push(`${descriptor.kind}|${descriptor.orientation}|${vectorKey(relative)}`);
    }
    required.sort();
    return { candidate: `${head.kind}|${head.orientation}`, required };
  }

  encode(context, candidate, metadata = {}) {
    const representation = this.representation(context, candidate);
    if (!representation) return { encoded: false, reason: "missing-geometric-descriptor" };
    const signature = `${representation.candidate}=>${representation.required.join(";")}`;
    if (this.signatures.has(signature)) {
      return { encoded: true, duplicate: true, clauses: this.clauses.length, signature };
    }
    const clause = { ...representation, signature, metadata: { ...metadata } };
    this.signatures.add(signature);
    this.clauses.push(clause);
    if (!this.byCandidate.has(clause.candidate)) this.byCandidate.set(clause.candidate, []);
    this.byCandidate.get(clause.candidate).push(clause);
    return { encoded: true, duplicate: false, clauses: this.clauses.length, signature };
  }

  compatible(candidate, context, count = true) {
    const representation = this.representation(context, candidate);
    if (!representation) return true;
    const clauses = this.byCandidate.get(representation.candidate);
    if (!clauses?.length) return true;
    const available = new Set(representation.required);
    for (const clause of clauses) {
      if (clause.required.length > available.size) continue;
      if (this.contextMatch === "exact" && clause.required.length !== available.size) continue;
      if (!clause.required.every(token => available.has(token))) continue;
      if (count) this.prunes += 1;
      return false;
    }
    return true;
  }

  stats() {
    return { clauses: this.clauses.length, prunes: this.prunes };
  }
}
