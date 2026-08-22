export function selectFeedbackBatch(items, limit) {
  return limit ? items.slice(0, limit) : items.slice();
}

export function retainSuccessfulFeedbackBatches({
  current,
  attempted,
  applied,
  z3Status,
  backoffCount
}) {
  const next = { ...current };
  let reduced = false;
  if (z3Status === "unknown" || backoffCount < 1) return { next, reduced };
  if (applied.clauses < attempted.clauses) {
    next.clauses = applied.clauses;
    reduced = true;
  }
  if (applied.cells < attempted.cells) {
    next.cells = applied.cells;
    reduced = true;
  }
  return { next, reduced };
}
