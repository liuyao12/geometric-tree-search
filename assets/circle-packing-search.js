export const BOUNDARY = -1;

const circleRadius = denominator => 1 / denominator;
const distance = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);

export class CirclePackingSearch {
  constructor(denominators, options = {}) {
    this.denominators = [...new Set(denominators)].sort((a, b) => a - b);
    if (!this.denominators.length || this.denominators.some(n => !Number.isInteger(n) || n < 2)) {
      throw new Error("Enter a nonempty set of integers, each at least 2.");
    }
    this.tolerance = options.tolerance ?? 1e-9;
    this.areaBound = Math.max(...this.denominators) ** 2;
    this.maxCircles = Math.min(options.maxCircles ?? this.areaBound, this.areaBound);
    this.nodeLimit = options.nodeLimit ?? 100000;
    if (!Number.isInteger(this.maxCircles) || this.maxCircles < this.denominators.length) {
      throw new Error("The circle horizon must be an integer large enough to use every radius.");
    }
    if (!Number.isInteger(this.nodeLimit) || this.nodeLimit < 1) {
      throw new Error("The node limit must be a positive integer.");
    }
    this.reset();
  }

  reset() {
    this.status = "running";
    this.nodes = 0;
    this.maxDepth = 0;
    this.candidateAttempts = 0;
    this.deadBranches = 0;
    this.duplicateStates = 0;
    this.seen = new Set();
    this.solution = null;
    this.current = null;
    this.best = null;
    this.bestScore = -Infinity;
    this.stack = [...this.denominators].reverse().map(denominator => {
      const radius = circleRadius(denominator);
      return { circles: [{ denominator, radius, x: 1 - radius, y: 0 }], lastAction: null };
    });
    if (this.denominators.reduce((sum, n) => sum + 1 / (n * n), 0) > 1 + this.tolerance) {
      this.status = "exhausted";
      this.stack = [];
    }
  }

  step(budget = 1) {
    let advanced = 0;
    while (advanced < budget && this.status === "running") {
      if (this.nodes >= this.nodeLimit) {
        this.status = "node_limit";
        break;
      }
      const state = this.stack.pop();
      if (!state) {
        this.status = "exhausted";
        break;
      }
      const key = this.stateKey(state.circles);
      if (this.seen.has(key)) {
        this.duplicateStates += 1;
        continue;
      }
      this.seen.add(key);
      this.nodes += 1;
      advanced += 1;
      this.current = state;
      this.maxDepth = Math.max(this.maxDepth, state.circles.length);
      const contacts = this.contacts(state.circles);
      const score = this.stateScore(state.circles, contacts);
      if (score > this.bestScore) {
        this.bestScore = score;
        this.best = { ...state, contacts };
      }
      if (this.isVictory(state.circles, contacts)) {
        this.solution = { ...state, contacts };
        this.best = this.solution;
        this.status = "found";
        break;
      }
      if (state.circles.length >= this.maxCircles) continue;

      const actions = this.actions(state.circles, contacts);
      for (let index = actions.length - 1; index >= 0; index -= 1) {
        const action = actions[index];
        this.stack.push({
          circles: [...state.circles, action.circle],
          lastAction: { a: action.a, b: action.b, denominator: action.circle.denominator },
        });
      }
    }
    return this.snapshot();
  }

  snapshot() {
    const shown = this.solution ?? this.current ?? this.best;
    return {
      status: this.status,
      nodes: this.nodes,
      maxDepth: this.maxDepth,
      frontierStates: this.stack.length,
      candidateAttempts: this.candidateAttempts,
      deadBranches: this.deadBranches,
      duplicateStates: this.duplicateStates,
      circles: shown?.circles ?? [],
      contacts: shown?.contacts ?? this.contacts(shown?.circles ?? []),
      lastAction: shown?.lastAction ?? null,
      maxCircles: this.maxCircles,
      areaBound: this.areaBound,
    };
  }

  actions(circles, contacts = this.contacts(circles)) {
    const used = new Set(circles.map(circle => circle.denominator));
    const missing = new Set(this.denominators.filter(n => !used.has(n)));
    const actions = [];
    const emitted = new Set();
    for (const [a, b] of this.orientedCorners(circles, contacts)) {
      for (const denominator of this.denominators) {
        this.candidateAttempts += 1;
        const attempt = this.placeAtCorner(circles, a, b, denominator);
        if (!attempt.circle) {
          if (attempt.reason === "overlap" || attempt.reason === "outside") this.deadBranches += 1;
          continue;
        }
        const key = this.circleKey(attempt.circle);
        if (emitted.has(key)) continue;
        emitted.add(key);
        const trial = [...circles, attempt.circle];
        const newDegree = this.contacts(trial).at(-1).size;
        actions.push({
          a, b, circle: attempt.circle, newDegree,
          missing: missing.has(denominator),
        });
      }
    }
    actions.sort((left, right) =>
      Number(right.missing) - Number(left.missing)
      || right.newDegree - left.newDegree
      || left.circle.denominator - right.circle.denominator
    );
    return actions;
  }

  contacts(circles) {
    const result = circles.map(() => new Set());
    circles.forEach((circle, i) => {
      if (Math.abs(Math.hypot(circle.x, circle.y) - (1 - circle.radius)) <= this.tolerance) {
        result[i].add(BOUNDARY);
      }
      for (let j = 0; j < i; j += 1) {
        if (Math.abs(distance(circle, circles[j]) - circle.radius - circles[j].radius) <= this.tolerance) {
          result[i].add(j);
          result[j].add(i);
        }
      }
    });
    return result;
  }

  isVictory(circles, contacts = this.contacts(circles)) {
    const used = new Set(circles.map(circle => circle.denominator));
    return this.denominators.every(n => used.has(n)) && contacts.every(neighbors => neighbors.size >= 3);
  }

  orientedCorners(circles, contacts = this.contacts(circles)) {
    const pairs = [];
    contacts.forEach((neighbors, i) => {
      for (const neighbor of neighbors) {
        if (neighbor === BOUNDARY || neighbor < i) {
          pairs.push([neighbor, i], [i, neighbor]);
        }
      }
    });
    return pairs;
  }

  placeAtCorner(circles, a, b, denominator) {
    const radius = circleRadius(denominator);
    const supportA = this.supportGeometry(circles, a, radius);
    const supportB = this.supportGeometry(circles, b, radius);
    const dx = supportB.x - supportA.x;
    const dy = supportB.y - supportA.y;
    const separation = Math.hypot(dx, dy);
    if (separation <= this.tolerance) return { circle: null, reason: "degenerate" };
    const along = (supportA.offset ** 2 - supportB.offset ** 2 + separation ** 2) / (2 * separation);
    const heightSquared = supportA.offset ** 2 - along ** 2;
    if (heightSquared < -this.tolerance) return { circle: null, reason: "no-intersection" };
    const height = Math.sqrt(Math.max(0, heightSquared));
    const ux = dx / separation;
    const uy = dy / separation;
    const circle = {
      denominator,
      radius,
      x: supportA.x + along * ux - height * uy,
      y: supportA.y + along * uy + height * ux,
    };
    if (Math.hypot(circle.x, circle.y) > 1 - radius + this.tolerance) {
      return { circle: null, reason: "outside" };
    }
    if (circles.some(other => distance(circle, other) < radius + other.radius - this.tolerance)) {
      return { circle: null, reason: "overlap" };
    }
    return { circle, reason: "legal" };
  }

  supportGeometry(circles, support, newRadius) {
    if (support === BOUNDARY) return { x: 0, y: 0, offset: 1 - newRadius };
    const circle = circles[support];
    return { x: circle.x, y: circle.y, offset: circle.radius + newRadius };
  }

  stateScore(circles, contacts) {
    const used = new Set(circles.map(circle => circle.denominator)).size;
    const satisfied = contacts.filter(neighbors => neighbors.size >= 3).length;
    const contactProgress = contacts.reduce((sum, neighbors) => sum + Math.min(3, neighbors.size), 0);
    return used * 10000 + satisfied * 1000 + contactProgress * 10 + circles.length;
  }

  circleKey(circle) {
    const quantum = Math.max(this.tolerance * 8, 1e-12);
    return `${circle.denominator}:${Math.round(circle.x / quantum)}:${Math.round(circle.y / quantum)}`;
  }

  stateKey(circles) {
    return circles.map(circle => this.circleKey(circle)).sort().join("|");
  }
}
