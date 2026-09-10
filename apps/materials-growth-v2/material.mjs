import { PointSearch, verify } from "./kernel.mjs";
import {
  PointRegistry,
  transform,
  compose,
  I,
  axisAngle,
  product,
  distance,
} from "./geometry.mjs";

export class MaterialExperiment {
  constructor(
    grammar,
    marking,
    {
      marked = true,
      angularReach = 0,
      positionError = grammar.epsilon,
      completeCrop = true,
      maximumPoints = 1600,
      maximumCandidates = 40000,
    } = {},
  ) {
    this.grammar = grammar;
    this.marking = marking;
    this.options = {
      marked,
      angularReach,
      positionError,
      completeCrop,
      maximumPoints,
      maximumCandidates,
    };
    this.registry = new PointRegistry(positionError);
    this.seed = new Map();
    this.expanded = new Set();
    this.events = [];
    this.best = null;
    this.unresolved = 0;
    grammar.atoms.forEach((a) => {
      const id = this.registry.intern(a.position);
      if (this.seed.has(id))
        throw Error("Input positions merge within the chosen error");
      this.seed.set(id, a.species);
    });
    this.lo = [0, 1, 2].map((k) =>
      Math.min(...grammar.atoms.map((a) => a.position[k])),
    );
    this.hi = [0, 1, 2].map((k) =>
      Math.max(...grammar.atoms.map((a) => a.position[k])),
    );
    this.orientations = grammar.types.map((t) => {
      const out = [],
        seen = new Set();
      for (const o of t.occurrences) {
        const key = o.pose.r
          .flat()
          .map((x) => Math.round(x / 1e-5))
          .join();
        if (!seen.has(key)) {
          seen.add(key);
          out.push(o.pose.r);
        }
      }
      return out;
    });
    const fixedMarks = [];
    for (const [point, label] of this.seed)
      marking.labels.forEach((s, c) =>
        fixedMarks.push({
          point,
          channel: String(c),
          lo: +(s === label),
          hi: +(s === label),
        }),
      );
    this.engine = new PointSearch({
      preference: (c) =>
        (c.meta.sources || []).filter((id) => this.engine.placed.has(id))
          .length,
      required: [...this.seed.keys()].map((id) => ({ id, complete: false })),
      fixedMarks,
      complete: false,
      version: marking.version,
      expand: (id) => this.expand(id),
    });
    for (const id of this.seed.keys()) this.expand(id);
    this.engine.refresh(new Set(this.engine.points.keys()));
  }
  point(position) {
    const before = this.registry.points.length,
      id = this.registry.intern(position);
    if (before !== this.registry.points.length) {
      if (this.registry.points.length > this.options.maximumPoints)
        throw Error("Point memory budget reached — unknown");
      const p = this.engine.ensure(id);
      const inside = position.every(
        (v, k) =>
          v >= this.lo[k] - this.grammar.epsilon &&
          v <= this.hi[k] + this.grammar.epsilon,
      );
      // The box is an explicit observation mask, never inferred empty space.
      // Empty values constrain m even before the point becomes a t obligation.
      if (this.options.completeCrop && inside)
        for (let c = 0; c < this.marking.labels.length; c++)
          p.marks.set(String(c), [{ lo: 0, hi: 0, owner: "observation-mask" }]);
    }
    return id;
  }
  emit(type, pose, source = null) {
    // Reject against the immutable observation before growing the point cache.
    for (const [i, s] of this.marking.sections[type.id].sites.entries()) {
      if (!this.options.marked && i) continue;
      const position = transform(pose, s.position);
      const observed = this.grammar.atoms.filter(
        (a) => distance(a.position, position) <= this.options.positionError,
      );
      if (observed.length > 1) return;
      const inside = position.every(
        (v, k) =>
          v >= this.lo[k] - this.grammar.epsilon &&
          v <= this.hi[k] + this.grammar.epsilon,
      );
      if (this.options.completeCrop && inside && !observed.length) return;
      if (
        observed.length &&
        s.intervals.some(([lo, hi], c) => {
          const v = +(observed[0].species === this.marking.labels[c]);
          return v < lo || v > hi;
        })
      )
        return;
    }
    const section = this.marking.sections[type.id],
      sites = section.sites.map((s) => this.point(transform(pose, s.position))),
      anchor = sites[0];
    if (new Set(sites).size !== sites.length) return;
    const id = JSON.stringify([type.id, sites]);
    if (this.engine.candidates.has(id)) {
      const c = this.engine.candidates.get(id);
      if (source && !c.meta.sources.includes(source))
        c.meta.sources.push(source);
      return;
    }
    if (this.engine.candidates.size >= this.options.maximumCandidates)
      throw Error("Candidate memory budget reached — unknown");
    const m = [];
    section.sites.forEach((s, i) => {
      if (!this.options.marked && i) return;
      s.intervals.forEach(([lo, hi], c) =>
        m.push({ point: sites[i], channel: String(c), lo, hi }),
      );
    });
    this.engine.addCandidate({
      id,
      t: [{ point: anchor, value: 1 }],
      m,
      activate: sites,
      meta: {
        type: type.id,
        pose,
        sites,
        label: type.sites[0].species,
        sources: source ? [source] : [],
      },
    });
  }
  expand(id) {
    if (this.expanded.has(id)) return;
    this.expanded.add(id);
    const point = this.registry.points[Number(id.slice(1))];
    for (const type of this.grammar.types)
      for (const r of this.orientations[type.id]) {
        const base = {
          r,
          t: point.position.map(
            (v, k) =>
              v - transform({ r, t: [0, 0, 0] }, type.sites[0].position)[k],
          ),
        };
        this.emit(type, base);
        if (this.options.angularReach)
          for (const axis of [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
          ])
            for (const sign of [-1, 1]) {
              const rr = product(
                r,
                axisAngle(
                  axis,
                  (sign * this.options.angularReach * Math.PI) / 180,
                ),
              );
              this.emit(type, { r: rr, t: point.position });
            }
      }
  }
  step() {
    const checkpoint = this.engine.trail.length;
    try {
      const event = this.nextStep();
      if (event.id) this.transport(event.id);
      return event;
    } catch (error) {
      this.engine.undo(checkpoint);
      const kind = /budget/i.test(error.message) ? "budget" : "unknown";
      this.engine.status =
        kind === "budget" ? "budget / unresolved" : "unresolved geometry";
      return { kind, message: error.message };
    }
  }
  nextStep() {
    let d = this.engine.decision();
    if (d.kind === "unknown") {
      // An empty sampled domain is unresolved, not a proved dead end. Explore
      // retained alternatives but retain this uncertainty in every result.
      this.unresolved++;
      while (this.engine.stack.length) {
        const f = this.engine.stack.at(-1);
        this.engine.undo(f.checkpoint);
        this.engine.stats.backtracks++;
        if (f.index < f.ids.length) {
          const id = f.ids[f.index++];
          this.engine.apply(id);
          this.engine.stats.accepted++;
          return { kind: "provisional-backtrack", id };
        }
        this.engine.stack.pop();
      }
      this.engine.status = "unknown";
      return d;
    }
    return this.engine.advance();
  }
  transport(id) {
    const c = this.engine.candidates.get(id),
      type = this.grammar.types[c.meta.type];
    // Transport observed relative poses by the current arbitrary real pose.
    for (const connection of this.grammar.connections)
      if (connection.parent === type.id)
        this.emit(
          this.grammar.types[connection.child],
          compose(c.meta.pose, connection.pose),
          id,
        );
  }
  snapshot(includeModel = true) {
    const atoms = [...this.seed].map(([id, species]) => ({
      species,
      position: this.registry.points[Number(id.slice(1))].position,
    }));
    for (const [id] of this.engine.placed) {
      const c = this.engine.candidates.get(id),
        p = c.t[0].point;
      if (!this.seed.has(p))
        atoms.push({
          species: c.meta.label,
          position: this.registry.points[Number(p.slice(1))].position,
        });
    }
    const model = {
      capacity: 1,
      required: [...this.engine.points.values()]
        .filter((p) => p.active)
        .map((p) => p.id),
      fixedMarks: [...this.engine.points.values()].flatMap((p) =>
        [...p.marks].flatMap(([channel, rows]) =>
          rows
            .filter(
              (r) => r.owner === "fixed" || r.owner === "observation-mask",
            )
            .map((r) => ({ point: p.id, channel, lo: r.lo, hi: r.hi })),
        ),
      ),
      candidates: [...this.engine.candidates.values()],
    };
    const selected = [...this.engine.placed.keys()],
      validation = verify(model, selected);
    return {
      schema: "materials-growth-v2/1",
      atoms,
      seedAtoms: this.seed.size,
      seedCovered: [...this.seed.keys()].filter(
        (p) => this.engine.points.get(p).total === 1,
      ).length,
      status: this.engine.status,
      stats: { ...this.engine.stats },
      frontier: [...this.engine.graph].map(([id, cs]) => ({
        point: id,
        degree: cs.size,
        generation: this.engine.points.get(id).generation,
        complete: false,
      })),
      pointCount: this.registry.points.length,
      candidateCount: this.engine.candidates.size,
      unresolved: this.unresolved,
      validation,
      scope:
        "approximate continuous-space adaptation; finite pose evidence is not exhaustive",
      options: this.options,
      ...(includeModel
        ? {
            observation: this.grammar.atoms,
            grammar: this.grammar,
            marking: this.marking,
            points: this.registry.points,
            model,
            selected,
          }
        : {}),
    };
  }
}
