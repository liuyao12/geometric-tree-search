// Growth-layer checkpoints on the active point domain, not physical radii or
// certificates of complete continuous-space coverage. Never changes decisions.
export class CoronaCheckpoints {
  constructor() {
    this.next = 3;
    this.last = null;
  }
  progress(engine) {
    let minimum = Infinity,
      blocked = false;
    for (const [id, candidates] of engine.graph) {
      minimum = Math.min(minimum, engine.points.get(id).generation);
      if (!candidates.size) blocked = true;
    }
    return {
      next: this.next,
      last: this.last,
      completed: Number.isFinite(minimum) ? Math.max(0, minimum - 1) : null,
      blocked,
      scope:
        "active-frontier generations; not certified continuous-space coverage",
    };
  }
  check(engine) {
    const p = this.progress(engine);
    if (p.blocked || p.completed === null || p.completed < this.next)
      return null;
    this.last = this.next;
    // A transaction may cross several thresholds; do not pause repeatedly on
    // the same state. Continue targets the next uncompleted odd generation.
    do {
      this.next += 2;
    } while (this.next <= p.completed);
    return {
      kind: "corona",
      corona: this.last,
      message: `Corona ${this.last} completed on the active frontier; next pause at ${this.next}`,
    };
  }
}
