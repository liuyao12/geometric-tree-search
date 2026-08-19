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
  constructor({ describePlacement, contextMatch = "subset", usePivotIndex = true }) {
    this.describePlacement = describePlacement;
    this.contextMatch = contextMatch;
    this.usePivotIndex = usePivotIndex;
    this.clauses = [];
    this.byCandidate = new Map();
    this.byCandidatePivot = new Map();
    this.tokenFrequency = new Map();
    this.signatures = new Set();
    this.prunes = 0;
    this.compatibilityChecks = 0;
    this.clauseChecks = 0;
    this.linearClauseChecks = 0;
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
    const frequencies = this.tokenFrequency.get(representation.candidate) ?? new Map();
    const pivot = representation.required.length
      ? representation.required.reduce((best, token) => {
          const tokenFrequency = frequencies.get(token) ?? 0;
          const bestFrequency = frequencies.get(best) ?? 0;
          return tokenFrequency < bestFrequency || (tokenFrequency === bestFrequency && token < best)
            ? token
            : best;
        })
      : null;
    const clause = { ...representation, pivot, signature, metadata: { ...metadata } };
    this.signatures.add(signature);
    this.clauses.push(clause);
    if (!this.byCandidate.has(clause.candidate)) this.byCandidate.set(clause.candidate, []);
    this.byCandidate.get(clause.candidate).push(clause);
    if (!this.byCandidatePivot.has(clause.candidate)) this.byCandidatePivot.set(clause.candidate, new Map());
    const pivotMap = this.byCandidatePivot.get(clause.candidate);
    const pivotKey = pivot ?? "";
    if (!pivotMap.has(pivotKey)) pivotMap.set(pivotKey, []);
    pivotMap.get(pivotKey).push(clause);
    for (const token of representation.required) frequencies.set(token, (frequencies.get(token) ?? 0) + 1);
    this.tokenFrequency.set(representation.candidate, frequencies);
    return { encoded: true, duplicate: false, clauses: this.clauses.length, signature };
  }

  compatible(candidate, context, count = true) {
    const representation = this.representation(context, candidate);
    if (!representation) return true;
    const allClauses = this.byCandidate.get(representation.candidate);
    if (!allClauses?.length) return true;
    const available = new Set(representation.required);
    const clauses = this.usePivotIndex
      ? [
          ...(this.byCandidatePivot.get(representation.candidate)?.get("") ?? []),
          ...[...available].flatMap(token =>
            this.byCandidatePivot.get(representation.candidate)?.get(token) ?? []
          )
        ]
      : allClauses;
    this.compatibilityChecks += 1;
    this.linearClauseChecks += allClauses.length;
    for (const clause of clauses) {
      this.clauseChecks += 1;
      if (clause.required.length > available.size) continue;
      if (this.contextMatch === "exact" && clause.required.length !== available.size) continue;
      if (!clause.required.every(token => available.has(token))) continue;
      if (count) this.prunes += 1;
      return false;
    }
    return true;
  }

  stats() {
    return {
      clauses: this.clauses.length,
      prunes: this.prunes,
      pivot_index_enabled: this.usePivotIndex,
      compatibility_checks: this.compatibilityChecks,
      clause_checks: this.clauseChecks,
      linear_clause_checks: this.linearClauseChecks,
      avoided_clause_checks: this.linearClauseChecks - this.clauseChecks
    };
  }
}
