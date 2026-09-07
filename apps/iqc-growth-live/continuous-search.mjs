import {
  I,
  compose,
  posePoint,
  keySites,
  SpatialSites,
  distance,
} from "./continuous-geometry.mjs";

// Iterative DFS, as in GCTS-I's analyze -> trial -> accept -> recurse -> undo.
// A terminal finite frontier is a failed continuation, not proof of a material's
// impossibility. Time and memory limits suspend the current branch exactly.
export class ContinuousSearch {
  constructor(
    grammar,
    {
      marking = null,
      policy = "frequency",
      maximumAtoms = 20000,
      maximumCandidates = 20000,
      maximumFrames = 10000,
      boundary = null,
    } = {},
  ) {
    if (!["frequency", "unmarked", "marking", "rl"].includes(policy))
      throw Error("Unknown search policy.");
    if (
      ![maximumAtoms, maximumCandidates, maximumFrames].every(
        (v) => Number.isInteger(v) && v > 0,
      )
    )
      throw Error("Search memory budgets must be positive integers.");
    this.grammar = grammar;
    this.policy = policy;
    this.marking = marking;
    if (
      marking &&
      marking.grammarKey !== grammar.types.map((t) => t.key).join("/")
    )
      throw Error("Marking belongs to a different cluster vocabulary.");
    this.maximumAtoms = maximumAtoms;
    this.maximumCandidates = maximumCandidates;
    this.maximumFrames = maximumFrames;
    this.boundary = boundary;
    this.spatial = new SpatialSites(
      grammar.tolerance,
      Math.max(grammar.tolerance * 2, grammar.minimum * 0.68),
    );
    grammar.atoms.forEach((s) => this.spatial.insert(s));
    this.placements = grammar.occurrences.map((o) => ({
      type: o.type,
      pose: o.pose,
      seed: true,
    }));
    this.ports = new Map();
    grammar.ports.forEach((p) => {
      if (!this.ports.has(p.parent)) this.ports.set(p.parent, []);
      this.ports.get(p.parent).push(p);
    });
    this.frames = [];
    this.pending = null;
    this.status = "ready";
    this.values = new Map();
    this.visits = new Map();
    this.stats = {
      checks: 0,
      accepted: 0,
      backtracks: 0,
      collisions: 0,
      redundant: 0,
      expanded: 0,
      boundary: 0,
      molecularConflicts: 0,
      bestAtoms: grammar.atoms.length,
      depth: 0,
      maxDepth: 0,
    };
    this.best = this.spatial.records.map((s) => ({
      ...s,
      position: [...s.position],
    }));
    this.events = [];
  }
  score(action) {
    if (this.policy === "unmarked") return 0;
    if (this.policy === "marking")
      return this.marking?.scores[action.port.id] ?? 0;
    if (this.policy === "rl") {
      const n = this.visits.get(action.port.id) || 0;
      return (
        (this.values.get(action.port.id) || 0) +
        Math.sqrt((2 * Math.log(2 + this.stats.accepted)) / (1 + n))
      );
    }
    return Math.log1p(action.port.count);
  }
  inspect(sites, molecularGroups = []) {
    let novel = 0;
    for (const site of sites) {
      if (this.boundary && !this.boundary(site.position)) {
        this.stats.boundary++;
        return null;
      }
      const result = this.spatial.inspect(site);
      if (result.conflict) {
        this.stats.collisions++;
        return null;
      }
      if (!result.match) novel++;
    }
    if (novel && this.grammar.molecularCutoff) {
      for (const ids of molecularGroups) {
        const molecule = ids.map((i) => sites[i]);
        for (const site of molecule)
          for (const existing of this.spatial.nearby(
            site.position,
            this.grammar.molecularCutoff,
          ))
            if (
              distance(site.position, existing.position) <=
                this.grammar.molecularCutoff &&
              !molecule.some(
                (s) =>
                  s.species === existing.species &&
                  distance(s.position, existing.position) <=
                    this.grammar.tolerance,
              )
            ) {
              this.stats.molecularConflicts++;
              return null;
            }
      }
    }
    return novel;
  }
  *enumerate() {
    const choices = [],
      seen = new Set();
    let work = 0;
    for (let parent = 0; parent < this.placements.length; parent++) {
      const placed = this.placements[parent],
        type = this.grammar.types[placed.type];
      for (const port of this.ports.get(placed.type) || [])
        for (const r of type.symmetries) {
          const pose = compose(
            placed.pose,
            compose({ r, t: [0, 0, 0] }, port.pose),
          );
          const sites = this.grammar.types[port.child].sites.map((s) => ({
            species: s.species,
            position: posePoint(pose, s.position),
          }));
          const key = keySites(sites, this.grammar.tolerance);
          if (seen.has(key)) continue;
          seen.add(key);
          this.stats.checks++;
          const novel = this.inspect(
            sites,
            this.grammar.types[port.child].molecularGroups,
          );
          if (novel === 0) this.stats.redundant++;
          else if (novel !== null)
            choices.push({ key, parent, port, pose, sites, novel });
          if (choices.length > this.maximumCandidates) {
            this.status = "candidate memory limit";
            return null;
          }
          if (++work % 128 === 0)
            yield { type: "evaluating", candidates: choices.length };
        }
    }
    // Grouping by parent implements a most-constrained positive frontier
    // preference; all legal actions remain alternatives in the DFS frame.
    const counts = new Map();
    choices.forEach((a) =>
      counts.set(a.parent, (counts.get(a.parent) || 0) + 1),
    );
    choices.sort(
      (a, b) =>
        counts.get(a.parent) - counts.get(b.parent) ||
        this.score(b) - this.score(a) ||
        a.key.localeCompare(b.key),
    );
    return choices;
  }
  reward(port, reward) {
    const id = port.id,
      n = (this.visits.get(id) || 0) + 1,
      q = this.values.get(id) || 0;
    this.visits.set(id, n);
    this.values.set(id, q + (reward - q) / n);
  }
  undo() {
    const frame = this.frames.at(-1);
    this.spatial.truncate(frame.atomCount);
    this.placements.length = frame.placementCount;
    this.stats.backtracks++;
    this.stats.depth = this.frames.length - 1;
    if (frame.last && this.policy === "rl") this.reward(frame.last.port, -1);
    return {
      type: "backtrack",
      depth: this.stats.depth,
      atoms: this.spatial.records.length,
    };
  }
  step() {
    if (this.status === "exhausted" || this.status.endsWith("limit"))
      return { type: "paused", reason: this.status };
    this.status = "searching";
    let choices = [];
    if (!this.retryFrame) {
      if (!this.pending) this.pending = this.enumerate();
      const next = this.pending.next();
      if (!next.done) return next.value;
      this.pending = null;
      choices = next.value;
      if (choices === null) return { type: "paused", reason: this.status };
      this.stats.expanded++;
      if (choices.length) {
        if (this.frames.length >= this.maximumFrames) {
          this.status = "branch memory limit";
          return { type: "paused", reason: this.status };
        }
        this.frames.push({
          choices,
          index: 0,
          atomCount: this.spatial.records.length,
          placementCount: this.placements.length,
          last: null,
        });
      } else if (this.frames.length) this.events.push(this.undo());
    }
    this.retryFrame = false;
    while (this.frames.length) {
      const frame = this.frames.at(-1);
      if (frame.index >= frame.choices.length) {
        this.frames.pop();
        if (this.frames.length) {
          const event = this.undo();
          this.events.push(event);
        }
        continue;
      }
      const action = frame.choices[frame.index];
      if (this.spatial.records.length + action.novel > this.maximumAtoms) {
        this.retryFrame = true;
        this.status = "atom memory limit";
        return { type: "paused", reason: this.status };
      }
      frame.index++;
      frame.last = action;
      for (const site of action.sites)
        if (!this.spatial.inspect(site).match) this.spatial.insert(site);
      this.placements.push({
        type: action.port.child,
        pose: action.pose,
        seed: false,
      });
      this.stats.accepted++;
      this.stats.depth = this.frames.length;
      this.stats.maxDepth = Math.max(this.stats.maxDepth, this.stats.depth);
      if (this.policy === "rl")
        this.reward(action.port, action.novel / action.sites.length);
      if (this.spatial.records.length > this.stats.bestAtoms) {
        this.stats.bestAtoms = this.spatial.records.length;
        this.best = this.spatial.records.map((s) => ({
          species: s.species,
          position: [...s.position],
        }));
      }
      return {
        type: "accept",
        novel: action.novel,
        depth: this.frames.length,
        forced: frame.choices.length === 1,
        key: action.key,
        sites: action.sites,
      };
    }
    this.status = "exhausted";
    return { type: "exhausted" };
  }
  // Called after reaching a leaf; rollback to the retained parent's next choice.
  advance() {
    const event = this.step();
    // step() handles all frame transitions. Keep events available for playback.
    return event;
  }
  setAtomBudget(value) {
    if (!Number.isInteger(value) || value < this.spatial.records.length)
      throw Error("Budget cannot be smaller than the current structure.");
    this.maximumAtoms = value;
    if (this.status === "atom memory limit") this.status = "ready";
  }
  receipt() {
    return {
      schema: "continuous-gcts-search/1",
      status: this.status,
      stats: { ...this.stats },
      policy: this.policy,
      seedAtoms: this.grammar.atoms.length,
      currentAtoms: this.spatial.records.length,
      bestAtoms: this.best.length,
      markingId: this.marking?.id ?? null,
      geometry: "continuous proper SE(3)",
      latticeUsed: false,
      targetUsed: false,
      rollback: true,
      molecularSupportClosure: !!this.grammar.molecularCutoff,
      molecularComponentCutoffAngstrom: this.grammar.molecularCutoff ?? null,
      searchComplete: this.status === "exhausted",
      physicalValidityEstablished: false,
      matchingToleranceAngstrom: this.grammar.tolerance,
      distanceExclusionAngstrom: this.spatial.exclusion,
      exclusionRule:
        "0.68 × minimum observed spacing, at least 2 × matching tolerance",
      candidateCatalogueCompleteOverSE3: false,
      limits: {
        maximumAtoms: this.maximumAtoms,
        maximumCandidates: this.maximumCandidates,
        maximumFrames: this.maximumFrames,
      },
      rlReward:
        this.policy === "rl"
          ? "local novel-site fraction, minus one on rollback"
          : null,
    };
  }
}
