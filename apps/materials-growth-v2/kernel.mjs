// Geometry-free point-value engine. Integers are capacity units; markings are
// closed intervals. The material adapter, not this kernel, defines point IDs.
export class PointSearch {
  constructor({
    capacity = 1,
    required = [],
    initial = [],
    fixedMarks = [],
    candidates = [],
    complete = true,
    expand = null,
    version = "1",
    preference = () => 0,
    constraint = null,
  }) {
    this.capacity = capacity;
    this.version = version;
    this.expand = expand;
    this.preference = preference;
    this.constraint = constraint;
    if (!Number.isSafeInteger(capacity) || capacity < 1)
      throw Error("Positive integer capacity required");
    this.points = new Map();
    this.candidates = new Map();
    this.dependencies = new Map();
    this.graph = new Map();
    this.reverse = new Map();
    this.reasons = new Map();
    this.trail = [];
    this.stack = [];
    this.placed = new Map();
    this.defaultComplete = complete;
    this.stats = {
      attempts: 0,
      accepted: 0,
      forced: 0,
      branches: 0,
      backtracks: 0,
      eliminated: 0,
      checks: 0,
    };
    this.status = "ready";
    this.events = [];
    for (const p of required)
      this.ensure(typeof p === "string" ? p : p.id, {
        active: true,
        root: 0,
        complete: typeof p === "string" ? complete : (p.complete ?? complete),
      });
    for (const row of fixedMarks) {
      const p = this.ensure(row.point);
      const key = row.channel ?? "0";
      if (!p.marks.has(key)) p.marks.set(key, []);
      p.marks.get(key).push({ lo: row.lo, hi: row.hi, owner: "fixed" });
    }
    for (const c of candidates) this.addCandidate(c);
    for (const id of initial) this.apply(id, true);
    this.trail = [];
    this.refresh(new Set(this.points.keys()));
  }
  ensure(
    id,
    { active = false, root = Infinity, complete = this.defaultComplete } = {},
  ) {
    if (!this.points.has(id))
      this.points.set(id, {
        id,
        total: 0,
        active,
        root,
        generation: root,
        complete,
        marks: new Map(),
      });
    return this.points.get(id);
  }
  addCandidate(input) {
    if (this.candidates.has(input.id)) return;
    const c = {
      ...input,
      t: input.t.map((x) => ({ ...x })),
      m: (input.m || []).map((x) => ({ ...x, channel: x.channel ?? "0" })),
    };
    if (
      !c.t.length ||
      c.t.some(
        (x) =>
          !Number.isSafeInteger(x.value) ||
          x.value <= 0 ||
          x.value > this.capacity,
      )
    )
      throw Error("Invalid positive t-support");
    if (new Set(c.t.map((x) => x.point)).size !== c.t.length)
      throw Error("Duplicate positive-support point");
    if (
      c.m.some(
        (x) => !Number.isFinite(x.lo) || !Number.isFinite(x.hi) || x.lo > x.hi,
      )
    )
      throw Error("Invalid marking interval");
    this.candidates.set(c.id, c);
    for (const id of new Set([
      ...c.t.map((x) => x.point),
      ...c.m.map((x) => x.point),
    ])) {
      this.ensure(id);
      if (!this.dependencies.has(id)) this.dependencies.set(id, new Set());
      this.dependencies.get(id).add(c.id);
    }
    this.updateCandidate(c.id);
  }
  reason(c) {
    this.stats.checks++;
    if (this.placed.has(c.id)) return "selected";
    for (const x of c.t)
      if (this.points.get(x.point).total + x.value > this.capacity)
        return "capacity";
    const intervals = new Map();
    for (const x of c.m) {
      const key = JSON.stringify([x.point, x.channel]);
      let pair = intervals.get(key);
      if (!pair) {
        pair = [-Infinity, Infinity];
        for (const a of this.points.get(x.point).marks.get(x.channel) || []) {
          pair[0] = Math.max(pair[0], a.lo);
          pair[1] = Math.min(pair[1], a.hi);
        }
        intervals.set(key, pair);
      }
      pair[0] = Math.max(pair[0], x.lo);
      pair[1] = Math.min(pair[1], x.hi);
      if (pair[0] > pair[1]) return "marking";
    }
    return this.constraint?.(c, this) || null;
  }
  updateCandidate(id) {
    const c = this.candidates.get(id),
      old = this.reasons.get(id),
      reason = this.reason(c);
    if (!old && reason && reason !== "selected") this.stats.eliminated++;
    this.reasons.set(id, reason);
    for (const p of this.reverse.get(id) || []) this.graph.get(p)?.delete(id);
    const incident = new Set();
    if (!reason)
      for (const x of c.t) {
        const p = this.points.get(x.point);
        if (p.active && p.total < this.capacity) {
          if (!this.graph.has(p.id)) this.graph.set(p.id, new Map());
          this.graph.get(p.id).set(id, x.value);
          incident.add(p.id);
        }
      }
    this.reverse.set(id, incident);
  }
  refresh(changed) {
    const affected = new Set();
    for (const id of changed) {
      const p = this.points.get(id);
      if (p.active && p.total < this.capacity) {
        if (!this.graph.has(id)) this.graph.set(id, new Map());
      } else this.graph.delete(id);
      for (const c of this.dependencies.get(id) || []) affected.add(c);
    }
    for (const id of affected) this.updateCandidate(id);
  }
  activate(id, generation) {
    const p = this.ensure(id);
    if (p.active) return;
    const before = { active: p.active, generation: p.generation, root: p.root };
    this.trail.push(
      Object.assign(() => Object.assign(p, before), { points: [id] }),
    );
    p.active = true;
    p.generation = generation;
    this.expand?.(id, this);
  }
  apply(id, seed = false) {
    const c = this.candidates.get(id);
    if (!c || this.reason(c)) throw Error("Illegal placement " + id);
    const checkpoint = this.trail.length;
    const generations = c.t
      .map((x) => this.points.get(x.point).generation)
      .filter(Number.isFinite);
    const generation = seed
      ? 0
      : generations.length
        ? Math.min(...generations) + 1
        : 0;
    const touched = new Set([
      ...c.t.map((x) => x.point),
      ...c.m.map((x) => x.point),
      ...(c.activate || []),
    ]);
    this.trail.push(
      Object.assign(() => this.placed.delete(id), { points: [...touched] }),
    );
    this.placed.set(id, { generation });
    for (const x of c.t) {
      const p = this.points.get(x.point),
        before = { total: p.total, generation: p.generation, active: p.active };
      this.trail.push(
        Object.assign(() => Object.assign(p, before), { points: [x.point] }),
      );
      p.total += x.value;
      p.generation = Math.min(p.generation, generation);
      p.active = true;
    }
    for (const x of c.m) {
      const p = this.points.get(x.point);
      if (!p.marks.has(x.channel)) p.marks.set(x.channel, []);
      const rows = p.marks.get(x.channel);
      rows.push({ ...x, owner: id });
      this.trail.push(
        Object.assign(
          () => {
            rows.pop();
            if (!rows.length) p.marks.delete(x.channel);
          },
          { points: [x.point] },
        ),
      );
    }
    try {
      for (const p of c.activate || []) this.activate(p, generation);
    } catch (error) {
      this.undo(checkpoint);
      throw error;
    }
    this.refresh(touched);
    return checkpoint;
  }
  undo(checkpoint) {
    const changed = new Set();
    while (this.trail.length > checkpoint) {
      const undo = this.trail.pop();
      for (const p of undo.points || []) changed.add(p);
      undo();
    }
    // Revalidate precisely the dependency closure of restored values. Immutable
    // proposal caches may grow; unaffected domains and incidences are retained.
    this.refresh(changed);
  }
  decision() {
    const frontier = [...this.graph].map(([id, cs]) => ({
      point: this.points.get(id),
      ids: [...cs.keys()],
    }));
    const dead = frontier.find((x) => !x.ids.length && x.point.complete);
    if (dead) return { kind: "dead", point: dead.point.id };
    const order = (a, b) =>
      a.point.generation - b.point.generation ||
      a.ids.length - b.ids.length ||
      a.point.id.localeCompare(b.point.id);
    const forced = frontier
      .filter((x) => x.ids.length === 1 && x.point.complete)
      .sort(order)[0];
    if (forced)
      return { kind: "forced", point: forced.point.id, ids: forced.ids };
    const unknown = frontier.find((x) => !x.ids.length && !x.point.complete);
    if (unknown)
      return {
        kind: "unknown",
        point: unknown.point.id,
        reason: "unresolved continuous pose domain",
      };
    const branch = frontier.sort(order)[0];
    if (!branch) return { kind: "complete" };
    branch.ids.sort(
      (a, b) =>
        this.preference(this.candidates.get(b)) -
          this.preference(this.candidates.get(a)) || a.localeCompare(b),
    );
    return {
      kind: "branch",
      point: branch.point.id,
      ids: branch.ids,
      provisional: !branch.point.complete,
    };
  }
  advance() {
    if (this.status === "exhausted") return { kind: "exhausted" };
    const d = this.decision();
    if (d.kind === "unknown") {
      this.status = "unknown";
      return d;
    }
    if (d.kind === "complete") {
      this.status = "consistent finite patch";
      return d;
    }
    if (d.kind === "dead") {
      while (this.stack.length) {
        const f = this.stack.at(-1);
        this.undo(f.checkpoint);
        this.stats.backtracks++;
        if (f.index < f.ids.length) {
          const id = f.ids[f.index++];
          this.stats.attempts++;
          this.apply(id);
          this.stats.accepted++;
          this.status = "searching";
          return { kind: "alternative", id, point: f.point };
        }
        this.stack.pop();
      }
      this.undo(0);
      this.status = "exhausted";
      return { kind: "exhausted", reason: "declared candidate model" };
    }
    if (d.kind === "branch") {
      this.stack.push({
        checkpoint: this.trail.length,
        ids: d.ids,
        index: 1,
        point: d.point,
      });
      this.stats.branches++;
    } else this.stats.forced++;
    const id = d.ids[0];
    this.stats.attempts++;
    this.apply(id);
    this.stats.accepted++;
    this.status = "searching";
    return { ...d, id };
  }
  semanticState() {
    return {
      placed: [...this.placed].sort(),
      points: [...this.points.values()]
        .filter((p) => p.active || p.total || p.marks.size)
        .map((p) => ({
          id: p.id,
          total: p.total,
          generation: p.generation,
          active: p.active,
          marks: [...p.marks].map(([k, v]) => [k, v.map((x) => ({ ...x }))]),
        }))
        .sort((a, b) => a.id.localeCompare(b.id)),
      graph: [...this.graph].map(([p, cs]) => [p, [...cs].sort()]).sort(),
    };
  }
  auditGraph() {
    const rebuilt = new Map();
    for (const c of this.candidates.values())
      if (!this.reason(c))
        for (const t of c.t) {
          const p = this.points.get(t.point);
          if (p.active && p.total < this.capacity) {
            if (!rebuilt.has(p.id)) rebuilt.set(p.id, []);
            rebuilt.get(p.id).push([c.id, t.value]);
          }
        }
    for (const p of this.points.values()) {
      const expected = rebuilt.get(p.id) || [];
      if (
        JSON.stringify(expected.sort()) !==
        JSON.stringify([...(this.graph.get(p.id) || [])].sort())
      )
        throw Error("Incidence mismatch " + p.id);
    }
    return true;
  }
}

// Independent verifier: does not consult graph, totals, legal flags or trail.
export function verify(
  model,
  selected,
  required = model.required.map((p) => (typeof p === "string" ? p : p.id)),
) {
  const totals = new Map(),
    marks = new Map(),
    errors = [],
    ids = new Set();
  const addMark = (x) => {
    const k = JSON.stringify([x.point, x.channel ?? "0"]);
    const v = marks.get(k) || [-Infinity, Infinity];
    v[0] = Math.max(v[0], x.lo);
    v[1] = Math.min(v[1], x.hi);
    marks.set(k, v);
    if (v[0] > v[1]) errors.push("marking " + k);
  };
  for (const m of model.fixedMarks || []) addMark(m);
  for (const id of selected) {
    if (ids.has(id)) {
      errors.push("duplicate " + id);
      continue;
    }
    ids.add(id);
    const c = model.candidates.find((c) => c.id === id);
    if (!c) {
      errors.push("missing " + id);
      continue;
    }
    for (const t of c.t)
      totals.set(t.point, (totals.get(t.point) || 0) + t.value);
    for (const m of c.m || []) addMark(m);
  }
  for (const [p, v] of totals)
    if (v > (model.capacity || 1)) errors.push("overflow " + p);
  const missing = required.filter(
    (p) => (totals.get(p) || 0) !== (model.capacity || 1),
  );
  return {
    legal: !errors.length,
    complete: !errors.length && !missing.length,
    errors,
    missing,
  };
}
