export const BOUNDARY = -1;

const circleRadius = bend => 1 / bend;
const distance = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);

export class CirclePackingSearch {
  constructor(bends, options = {}) {
    this.bends = [...new Set(bends)].sort((a, b) => a - b);
    if (!this.bends.length || this.bends.some(b => !Number.isInteger(b) || b < 2)) {
      throw new Error("Enter a nonempty set of integers, each at least 2.");
    }
    this.tolerance = options.tolerance ?? 1e-9;
    this.areaBound = Math.max(...this.bends) ** 2;
    this.maxCircles = Math.min(options.maxCircles ?? this.areaBound, this.areaBound);
    this.nodeLimit = options.nodeLimit ?? 100000;
    if (!Number.isInteger(this.maxCircles) || this.maxCircles < this.bends.length) {
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
    this.symmetryPrunes = 0;
    this.seen = new Set();
    this.solution = null;
    this.current = null;
    this.best = null;
    this.bestScore = -Infinity;
    this.stack = [...this.bends].reverse().map(bend => {
      const radius = circleRadius(bend);
      return { circles: [{ bend, radius, x: 1 - radius, y: 0 }], lastAction: null };
    });
    this.pending = new Set(this.stack.map(state => this.stateKey(state.circles)));
    if (this.bends.reduce((sum, bend) => sum + 1 / (bend * bend), 0) > 1 + this.tolerance) {
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
      this.pending.delete(key);
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
        if (this.seen.has(action.key) || this.pending.has(action.key)) {
          this.duplicateStates += 1;
          continue;
        }
        this.pending.add(action.key);
        this.stack.push({
          circles: [...state.circles, action.circle],
          lastAction: { a: action.a, b: action.b, bend: action.circle.bend },
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
      symmetryPrunes: this.symmetryPrunes,
      circles: shown?.circles ?? [],
      contacts: shown?.contacts ?? this.contacts(shown?.circles ?? []),
      lastAction: shown?.lastAction ?? null,
      maxCircles: this.maxCircles,
      areaBound: this.areaBound,
    };
  }

  actions(circles, contacts = this.contacts(circles)) {
    const used = new Set(circles.map(circle => circle.bend));
    const missing = new Set(this.bends.filter(bend => !used.has(bend)));
    const actions = [];
    const emittedChildren = new Set();
    for (const [a, b] of this.orientedCorners(circles, contacts)) {
      for (const bend of this.bends) {
        this.candidateAttempts += 1;
        const attempt = this.placeAtCorner(circles, a, b, bend);
        if (!attempt.circle) {
          if (attempt.reason === "overlap" || attempt.reason === "outside") this.deadBranches += 1;
          continue;
        }
        const trial = [...circles, attempt.circle];
        const key = this.stateKey(trial);
        if (emittedChildren.has(key)) {
          this.symmetryPrunes += 1;
          continue;
        }
        emittedChildren.add(key);
        const trialContacts = this.contacts(trial);
        const newDegree = trialContacts.at(-1).size;
        const heldCount = trialContacts.filter((_, index) => this.isHeld(trial, index, trialContacts)).length;
        actions.push({
          a, b, circle: attempt.circle, newDegree, heldCount, key,
          missing: missing.has(bend),
        });
      }
    }
    actions.sort((left, right) =>
      Number(right.missing) - Number(left.missing)
      || right.heldCount - left.heldCount
      || right.newDegree - left.newDegree
      || left.circle.bend - right.circle.bend
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
    const used = new Set(circles.map(circle => circle.bend));
    return this.bends.every(bend => used.has(bend))
      && contacts.every((_, index) => this.isHeld(circles, index, contacts));
  }

  contactAngles(circles, index, contacts = this.contacts(circles)) {
    const circle = circles[index];
    return [...contacts[index]].map(neighbor => {
      if (neighbor === BOUNDARY) return Math.atan2(circle.y, circle.x);
      const other = circles[neighbor];
      return Math.atan2(other.y - circle.y, other.x - circle.x);
    }).map(angle => angle < 0 ? angle + 2 * Math.PI : angle).sort((a, b) => a - b);
  }

  largestContactGap(circles, index, contacts = this.contacts(circles)) {
    const angles = this.contactAngles(circles, index, contacts);
    if (angles.length < 2) return 2 * Math.PI;
    let largest = angles[0] + 2 * Math.PI - angles.at(-1);
    for (let i = 1; i < angles.length; i += 1) {
      largest = Math.max(largest, angles[i] - angles[i - 1]);
    }
    return largest;
  }

  isHeld(circles, index, contacts = this.contacts(circles)) {
    return contacts[index].size >= 3
      && this.largestContactGap(circles, index, contacts) < Math.PI - this.tolerance;
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

  placeAtCorner(circles, a, b, bend) {
    const radius = circleRadius(bend);
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
      bend,
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
    const used = new Set(circles.map(circle => circle.bend)).size;
    const satisfied = contacts.filter((_, index) => this.isHeld(circles, index, contacts)).length;
    const contactProgress = contacts.reduce((sum, neighbors) => sum + Math.min(3, neighbors.size), 0);
    return used * 10000 + satisfied * 1000 + contactProgress * 10 + circles.length;
  }

  transformedCircleKey(circle, cosine, sine, reflection) {
    const quantum = Math.max(this.tolerance * 8, 1e-12);
    const x = circle.x * cosine + circle.y * sine;
    const y = (-circle.x * sine + circle.y * cosine) * reflection;
    return `${circle.bend}:${Math.round(x / quantum)}:${Math.round(y / quantum)}`;
  }

  stateKey(circles) {
    if (!circles.length) return "";
    const keys = [];
    for (const anchor of circles) {
      const norm = Math.hypot(anchor.x, anchor.y);
      if (norm <= this.tolerance) continue;
      const cosine = anchor.x / norm;
      const sine = anchor.y / norm;
      for (const reflection of [1, -1]) {
        keys.push(circles
          .map(circle => this.transformedCircleKey(circle, cosine, sine, reflection))
          .sort()
          .join("|"));
      }
    }
    return keys.length ? keys.sort()[0] : circles.map(circle => `${circle.bend}:0:0`).sort().join("|");
  }
}
