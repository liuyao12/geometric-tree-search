import { PointSearch, verify } from "./kernel.mjs?v=observed-overlaps-1";
import { overlapConstraint, verifyOverlaps } from "./overlap-rules.mjs";
import { centralSeed } from "./seed.mjs";
import {
  PointRegistry,
  transform,
  compose,
  I,
  axisAngle,
  product,
  distance,
} from "./geometry.mjs?v=correspondence-branches-1";

export class MaterialExperiment {
  constructor(
    grammar,
    marking,
    {
      marked = true,
      seedMode = "single",
      angularReach = 0,
      positionError = grammar.epsilon,
      completeCrop = true,
      maximumPoints = 1600,
      maximumCandidates = 40000,
      softMemory = false,
    } = {},
  ) {
    this.grammar = grammar;
    this.marking = marking;
    this.options = {
      seedMode,
      marked,
      angularReach,
      positionError,
      completeCrop,
      maximumPoints,
      maximumCandidates,
      softMemory,
    };
    this.registry = new PointRegistry(positionError);
    this.seed = new Map();
    this.expanded = new Set();
    this.events = [];
    this.best = null;
    this.unresolved = 0;
    this.correspondences = {
      ambiguousSites: 0,
      alternatives: 0,
      truncatedPoses: 0,
    };
    this.memoryCheckpoint = false;
    if (!["single", "patch"].includes(seedMode))
      throw Error("Unknown seed mode");
    this.seedOrigin = centralSeed(grammar.atoms);
    this.observation =
      seedMode === "single" ? [this.seedOrigin.atom] : grammar.atoms;
    this.options.completeCrop = seedMode === "patch" && completeCrop;
    this.observation.forEach((a) => {
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
    this.overlapFilter =
      marked && marking.overlapRules
        ? overlapConstraint(grammar, marking.overlapRules, this.registry)
        : null;
    this.engine = new PointSearch({
      constraint: this.overlapFilter,
      preference: (c) =>
        (c.meta.sources || []).filter((id) => this.engine.placed.has(id))
          .length +
        (seedMode === "single"
          ? grammar.types[c.meta.type].occurrences.length * 1e-6
          : 0),
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
      if (this.registry.points.length > this.options.maximumPoints) {
        if (!this.options.softMemory)
          throw Error("Point memory budget reached — unknown");
        this.memoryCheckpoint = true;
      }
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
      const observed = this.observation.filter(
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
    // Multiple nearby fixed cache points are correspondence alternatives, not
    // a fatal error and not permission to pick an arbitrary nearest point.
    // Compile each injective assignment into the ordinary candidate graph.
    const section = this.marking.sections[type.id];
    const choices = section.sites.map((s) => {
      const p = transform(pose, s.position),
        matches = this.registry.matches(p);
      if (matches.length > 1) this.correspondences.ambiguousSites++;
      return matches.length ? matches.map((m) => m.id) : [this.point(p)];
    });
    let count = 0;
    const sites = [],
      used = new Set();
    const visit = (i) => {
      if (count >= 4096) return false;
      if (i === choices.length) {
        count++;
        this.emitAssignment(type, pose, [...sites], source);
        return true;
      }
      for (const id of choices[i]) {
        if (used.has(id)) continue;
        sites.push(id);
        used.add(id);
        if (!visit(i + 1)) return false;
        sites.pop();
        used.delete(id);
      }
      return true;
    };
    if (!visit(0)) this.correspondences.truncatedPoses++;
    this.correspondences.alternatives += Math.max(0, count - 1);
  }
  emitAssignment(type, pose, sites, source) {
    const section = this.marking.sections[type.id],
      anchor = sites[0];
    const id = JSON.stringify([type.id, sites]);
    if (this.engine.candidates.has(id)) {
      const c = this.engine.candidates.get(id);
      if (source && !c.meta.sources.includes(source))
        c.meta.sources.push(source);
      return;
    }
    if (this.engine.candidates.size >= this.options.maximumCandidates) {
      if (!this.options.softMemory)
        throw Error("Candidate memory budget reached — unknown");
      this.memoryCheckpoint = true;
    }
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
    if (this.memoryCheckpoint) return this.memoryPause();
    const checkpoint = this.engine.trail.length;
    try {
      const event = this.nextStep();
      if (event.id) this.transport(event.id);
      // Quotas pause only after a full transaction, never halfway through
      // domain expansion or after consuming an untried branch alternative.
      if (this.memoryCheckpoint) return this.memoryPause();
      return event;
    } catch (error) {
      this.engine.undo(checkpoint);
      const kind = /budget/i.test(error.message) ? "budget" : "unknown";
      this.engine.status =
        kind === "budget" ? "budget / unresolved" : "unresolved geometry";
      return { kind, message: error.message };
    }
  }
  memoryPause() {
    this.engine.status = "working-memory checkpoint";
    return {
      kind: "budget",
      resumable: true,
      message:
        "Working budget reached. Continue expands it and resumes this search.",
    };
  }
  continueWithMoreMemory() {
    if (!this.memoryCheckpoint) return;
    this.options.maximumPoints = Math.ceil(
      Math.max(this.options.maximumPoints, this.registry.points.length) * 2,
    );
    this.options.maximumCandidates = Math.ceil(
      Math.max(this.options.maximumCandidates, this.engine.candidates.size) * 2,
    );
    this.memoryCheckpoint = false;
    this.engine.status = "searching";
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
      return {
        ...d,
        message:
          "No continuation found among the sampled candidates. More training configurations or additional pose proposals are needed.",
      };
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
    const overlapValidation = this.overlapFilter
      ? verifyOverlaps(
          this.grammar,
          this.marking.overlapRules,
          this.registry,
          this.engine.candidates,
          selected,
        )
      : null;
    if (overlapValidation && !overlapValidation.legal) validation.legal = false;
    return {
      schema: "materials-growth-v2/1",
      seedOrigin: this.seedOrigin,
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
      correspondences: {
        ...this.correspondences,
        scope:
          "Injective assignments to fixed points within tolerance; at most 4096 assignments per proposed pose. Later cache insertions do not exhaustively regenerate old poses. Domains remain incomplete, never certified dead or forced.",
      },
      validation,
      overlapValidation,
      overlapChecks: this.overlapFilter
        ? { ...this.overlapFilter.counters }
        : null,
      connectionPolicy: this.overlapFilter
        ? "observed-only"
        : "occupancy-only ablation",
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
