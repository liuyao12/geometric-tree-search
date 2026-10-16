const rounded = value => Math.round(value * 1e9) / 1e9;
const vectorKey = vector => vector.map(rounded).join(",");
const matrixKey = matrix => matrix.flat().map(rounded).join(",");
const transposeVector = (matrix, vector) => [0, 1, 2].map(column =>
  matrix[0][column] * vector[0] + matrix[1][column] * vector[1] + matrix[2][column] * vector[2]
);
const transposeMatrix = (left, right) => [0, 1, 2].map(row =>
  [0, 1, 2].map(column =>
    left[0][row] * right[0][column]
    + left[1][row] * right[1][column]
    + left[2][row] * right[2][column]
  )
);

/**
 * Translation-equivariant geometric nogoods.
 *
 * Each clause stores a failed candidate and its complete placed context in
 * coordinates relative to that candidate. Absolute position is discarded, so
 * translated copies are recognized; requiring the complete recorded context
 * keeps the clause exact and monotone when more tiles have been placed.
 */
export class GeometricFailureMemo {
  constructor({ describePlacement, contextMatch = "subset", allAnchors = false }) {
    this.describePlacement = describePlacement;
    this.contextMatch = contextMatch;
    this.allAnchors = allAnchors;
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
      const delta = descriptor.translation.map((value, axis) => value - head.translation[axis]);
      if (head.frame && descriptor.frame) {
        const relative = transposeVector(head.frame, delta);
        const relativeFrame = transposeMatrix(head.frame, descriptor.frame);
        required.push(`${descriptor.kind}|${matrixKey(relativeFrame)}|${vectorKey(relative)}`);
      } else {
        required.push(`${descriptor.kind}|${descriptor.orientation}|${vectorKey(delta)}`);
      }
    }
    required.sort();
    return {
      candidate: head.frame ? `${head.kind}|local-frame` : `${head.kind}|${head.orientation}`,
      required
    };
  }

  encode(context, candidate, metadata = {}) {
    const patch = [...context, candidate];
    const rawVariants = this.allAnchors
      ? patch.map((anchor, index) => this.representation(patch.filter((_, other) => other !== index), anchor))
      : [this.representation(context, candidate)];
    if (rawVariants.some(representation => !representation)) {
      return { encoded: false, reason: "missing-geometric-descriptor" };
    }
    const variantsBySignature = new Map();
    for (const representation of rawVariants) {
      const variantSignature = `${representation.candidate}=>${representation.required.join(";")}`;
      if (!variantsBySignature.has(variantSignature)) {
        variantsBySignature.set(variantSignature, { ...representation, signature: variantSignature });
      }
    }
    const variants = [...variantsBySignature.values()];
    const signature = variants.map(variant => variant.signature).sort()[0];
    if (this.signatures.has(signature)) {
      return {
        encoded: true,
        duplicate: true,
        clauses: this.clauses.length,
        indexedVariants: this.indexedVariantCount(),
        signature
      };
    }
    const clause = { ...variants[0], variants, signature, metadata: { ...metadata } };
    this.signatures.add(signature);
    this.clauses.push(clause);
    for (const variant of variants) {
      if (!this.byCandidate.has(variant.candidate)) this.byCandidate.set(variant.candidate, []);
      this.byCandidate.get(variant.candidate).push(variant);
    }
    return {
      encoded: true,
      duplicate: false,
      clauses: this.clauses.length,
      indexedVariants: this.indexedVariantCount(),
      signature
    };
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

  indexedVariantCount() {
    let count = 0;
    for (const variants of this.byCandidate.values()) count += variants.length;
    return count;
  }

  stats() {
    return {
      clauses: this.clauses.length,
      indexedVariants: this.indexedVariantCount(),
      prunes: this.prunes
    };
  }
}
