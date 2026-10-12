// Reidemeister tiles, exact diagram seams, and a finite point-value pilot.
export const VERSION = 'reidemeister-seams-v1';
const clone = w => w.map(x => ({ ...x }));
export const count = w => w.length / 2;
export function canonical(word) {
  if (!word.length) return '';
  const keys = [];
  for (const w of [word, [...word].reverse()]) for (let start = 0; start < w.length; start++) {
    const ids = new Map();
    keys.push(Array.from({ length: w.length }, (_, k) => {
      const x = w[(k + start) % w.length];
      if (!ids.has(x.id)) ids.set(x.id, ids.size + 1);
      return `${x.over ? 'O' : 'U'}${ids.get(x.id)}${x.sign > 0 ? '+' : '-'}`;
    }).join(' '));
  }
  return keys.sort()[0];
}
export function parse(text) {
  if (!text.trim()) return [];
  const w = text.trim().split(/\s+/).map(token => {
    const m = /^([OU])(\d+)([+-])$/.exec(token);
    if (!m) throw Error(`Invalid token ${token}; use O1+ or U1-.`);
    return { id: Number(m[2]), over: m[1] === 'O', sign: m[3] === '+' ? 1 : -1 };
  });
  topology(w); return w;
}
// alpha joins outgoing to next incoming dart. sigma is CCW rotation at a crossing.
// Positive sign means det(projected over tangent, projected under tangent) > 0.
export function topology(w) {
  if (!w.length) return { faces: [[]], genus: 0, alpha: [], sigma: [] };
  const groups = new Map(), sigma = [], alpha = [];
  w.forEach((x, i) => {
    if (!Number.isSafeInteger(x.id) || ![1, -1].includes(x.sign) || typeof x.over !== 'boolean') throw Error('Invalid crossing data.');
    if (!groups.has(x.id)) groups.set(x.id, []);
    groups.get(x.id).push(i);
    const j = (i + 1) % w.length;
    alpha[2 * i + 1] = 2 * j; alpha[2 * j] = 2 * i + 1;
  });
  for (const indices of groups.values()) {
    if (indices.length !== 2) throw Error('Each crossing must occur exactly twice.');
    const [a, b] = indices;
    if (w[a].over === w[b].over || w[a].sign !== w[b].sign) throw Error('Crossing over/under or signs disagree.');
    const o = w[a].over ? a : b, u = w[a].over ? b : a;
    const darts = w[a].sign > 0 ? [2 * o + 1, 2 * u + 1, 2 * o, 2 * u] : [2 * o + 1, 2 * u, 2 * o, 2 * u + 1];
    darts.forEach((d, k) => sigma[d] = darts[(k + 1) % 4]);
  }
  const seen = new Set(), faces = [];
  for (let d = 0; d < 2 * w.length; d++) if (!seen.has(d)) {
    const face = []; let p = d;
    do { face.push(p); seen.add(p); p = sigma[alpha[p]]; } while (p !== d);
    faces.push(face);
  }
  const genus = (2 + groups.size - faces.length) / 2;
  if (genus !== 0) throw Error(`Gauss word is not a planar knot diagram (ribbon genus ${genus}).`);
  return { faces, genus, alpha, sigma };
}
function reductions(w) {
  const { faces, alpha } = topology(w), out = [];
  for (const f of faces) {
    const ids = new Set(f.flatMap(d => [w[Math.floor(d / 2)].id, w[Math.floor(alpha[d] / 2)].id]));
    if (f.length === 1 && ids.size === 1) out.push({ kind: 'I−', patch: f, removed: [...ids], after: w.filter(x => !ids.has(x.id)) });
    if (f.length === 2 && ids.size === 2) {
      const [a, b] = [...ids];
      const sameStrand = f.every(d => w[Math.floor(d / 2)].over === w[Math.floor(alpha[d] / 2)].over);
      if (sameStrand && w.find(x => x.id === a).sign !== w.find(x => x.id === b).sign)
        out.push({ kind: 'II−', patch: f, removed: [...ids], after: w.filter(x => !ids.has(x.id)) });
    }
    if (f.length === 3 && ids.size === 3) {
      const pairs = f.map(d => [Math.floor(d / 2), Math.floor(alpha[d] / 2)]);
      if (new Set(pairs.flat()).size !== 6) continue;
      const types = pairs.map(([a, b]) => Number(w[a].over) + Number(w[b].over));
      if (!types.includes(0) || !types.includes(2)) continue; // no cyclic over/under triangle
      const after = clone(w);
      for (const [a, b] of pairs) [after[a], after[b]] = [after[b], after[a]];
      out.push({ kind: 'III', patch: f, after });
    }
  }
  return out;
}
export function moves(w, crossingCap = 4) {
  topology(w);
  if (!Number.isInteger(crossingCap) || crossingCap < count(w)) throw Error('Crossing cap is below the input.');
  const out = reductions(w), n = w.length, gaps = Math.max(1, n), next = Math.max(0, ...w.map(x => x.id)) + 1;
  if (count(w) + 1 <= crossingCap) for (let gap = 0; gap < gaps; gap++) for (const sign of [1, -1]) for (const over of [true, false]) {
    const pair = [{ id: next, over, sign }, { id: next, over: !over, sign }];
    out.push({ kind: 'I+', patch: [gap], after: [...w.slice(0, gap), ...pair, ...w.slice(gap)] });
  }
  if (count(w) + 2 <= crossingCap) for (let a = 0; a < gaps; a++) for (let b = 0; b < gaps; b++) for (const sign of [1, -1]) for (const reversed of [true, false]) for (const underFirst of a === b ? [true, false] : [false]) {
    const over = [{ id: next, over: true, sign }, { id: next + 1, over: true, sign: -sign }];
    const under = over.map(x => ({ ...x, over: false })); if (reversed) under.reverse();
    const after = [];
    for (let k = 0; k < gaps; k++) {
      if (underFirst && k === b) after.push(...under);
      if (k === a) after.push(...over);
      if (!underFirst && k === b) after.push(...under);
      if (n) after.push(w[k]);
    }
    try {
      topology(after);
      // Planarity alone is insufficient: certify the inserted pair bounds a cancellable bigon.
      if (reductions(after).some(m => m.kind === 'II−' && m.removed.includes(next) && m.removed.includes(next + 1) && canonical(m.after) === canonical(w))) out.push({ kind: 'II+', patch: [a, b], after });
    } catch { /* invalid disk placement */ }
  }
  const unique = new Map();
  for (const m of out) {
    topology(m.after); const key = canonical(m.after);
    if (key !== canonical(w) && !unique.has(key)) unique.set(key, { ...m, before: clone(w), key });
  }
  return [...unique.values()];
}
export function verifyMovie(certificate) {
  if (certificate.version !== VERSION) throw Error('Unsupported certificate version.');
  let w = parse(certificate.source);
  for (const step of certificate.steps) {
    const m = moves(w, certificate.crossingCap).find(x => x.kind === step.kind && x.key === step.after);
    if (!m) throw Error(`Invalid Reidemeister tile ${step.kind}.`);
    w = parse(step.after);
  }
  if (canonical(w) !== canonical(parse(certificate.target))) throw Error('Movie has the wrong endpoint.');
  return true;
}
export function colorDimension(w, prime = 3) {
  topology(w);
  if (!w.length) return 1;
  const unders = w.map((x, i) => !x.over ? i : -1).filter(i => i >= 0), n = unders.length;
  const matrix = unders.map((pos, i) => {
    const row = Array(n).fill(0), over = w.findIndex(x => x.id === w[pos].id && x.over);
    const overArc = (unders.filter(k => k < over).length - 1 + n) % n;
    row[overArc] += 2; row[(i - 1 + n) % n]--; row[i]--; return row.map(x => (x % prime + prime) % prime);
  });
  let rank = 0;
  for (let col = 0; col < n; col++) {
    const pivot = matrix.findIndex((r, i) => i >= rank && r[col]); if (pivot < 0) continue;
    [matrix[rank], matrix[pivot]] = [matrix[pivot], matrix[rank]];
    const inv = Array.from({ length: prime - 1 }, (_, i) => i + 1).find(k => k * matrix[rank][col] % prime === 1);
    matrix[rank] = matrix[rank].map(x => x * inv % prime);
    for (let i = 0; i < n; i++) if (i !== rank) {
      const mul = matrix[i][col]; matrix[i] = matrix[i].map((x, j) => ((x - mul * matrix[rank][j]) % prime + prime) % prime);
    }
    rank++;
  }
  return n - rank;
}
// Complete finite catalog of diagram-state transitions, including identity holds.
export function catalog(source, target, { depth = 3, crossingCap = 3, stateCap = 1500 } = {}) {
  topology(source); topology(target);
  if (!Number.isInteger(depth) || depth < 1 || depth > 8 || !Number.isInteger(crossingCap) || crossingCap < Math.max(count(source), count(target)) || crossingCap > 8 || !Number.isInteger(stateCap) || stateCap < 1) throw Error('Invalid finite search bounds.');
  const states = [new Map([[canonical(source), clone(source)]])], tiles = [], slots = [], targetKey = canonical(target);
  let stateCount = 1;
  for (let t = 0; t < depth; t++) {
    states[t + 1] = new Map(); slots[t] = [];
    for (const [before, w] of states[t]) {
      const candidates = [...moves(w, crossingCap), { kind: 'hold', after: clone(w), key: before, patch: [] }];
      for (const m of candidates) {
        if (!states[t + 1].has(m.key)) {
          states[t + 1].set(m.key, m.after); stateCount++;
          if (stateCount > stateCap) return { complete: false, reason: 'catalog-state-budget', stateCount, depth, crossingCap };
        }
        const id = tiles.length;
        tiles.push({ id, time: t, kind: m.kind, before, after: m.key, patch: m.patch,
          t: new Map([[t, 1]]), m: new Map([[`seam:${t}`, before], [`seam:${t + 1}`, m.key]]) });
        slots[t].push(id);
      }
    }
  }
  return { complete: true, states, tiles, slots, stateCount, depth, crossingCap, targetKey, sourceKey: canonical(source) };
}
// Exhaustive backwards extension labels, with an inspectable finite proof DAG.
// Failure guards are genuine assigned m-values; the point engine never scans a nogood table.
export function learnSeamMarkings(cat) {
  const viable = Array.from({ length: cat.depth + 1 }, () => new Set()), failures = [];
  viable[cat.depth].add(cat.targetKey);
  for (let t = cat.depth - 1; t >= 0; t--) for (const id of cat.slots[t]) {
    const tile = cat.tiles[id]; if (viable[t + 1].has(tile.after)) viable[t].add(tile.before);
  }
  const boundary = new Map([[`seam:0`, cat.sourceKey], [`seam:${cat.depth}`, cat.targetKey]]);
  const tiles = cat.tiles.map(x => ({ ...x, m: new Map(x.m) }));
  for (let t = 1; t <= cat.depth; t++) for (const state of cat.states[t].keys()) if (!viable[t].has(state)) {
    const p = `failure:${t}:${state}`; boundary.set(p, 0);
    const affected = [];
    for (const tile of tiles) if (tile.time + 1 === t && tile.after === state) { tile.m.set(p, 1); affected.push(tile.id); }
    failures.push({ time: t, state, outgoing: (cat.slots[t] || []).filter(id => cat.tiles[id].before === state), affected });
  }
  return { tiles, boundary, failures, viable, version: VERSION, scope: { depth: cat.depth, crossingCap: cat.crossingCap, target: cat.targetKey }, assignedValues: tiles.reduce((a, t) => a + t.m.size - 2, 0) + failures.length };
}
// Full re-enumeration after each placement is intentional in this small pilot.
// Both incidence directions, mark-only dependencies, global scheduling and rollback are explicit.
export function pointSearch(cat, { learned = null, nodeCap = 10000, order = null } = {}) {
  const tiles = learned?.tiles || cat.tiles;
  const fixed = learned?.boundary || new Map([[`seam:0`, cat.sourceKey], [`seam:${cat.depth}`, cat.targetKey]]);
  const stats = { nodes: 0, attempts: 0, forced: 0, branches: 0, backtracks: 0, markingEliminations: 0, graphBuilds: 0, peakIncidences: 0 };
  function graph(selected) {
    stats.graphBuilds++;
    const totals = Array(cat.depth).fill(0), marks = new Map(fixed), generations = Array(cat.depth).fill(0);
    for (const id of selected) for (const [p, v] of tiles[id].m) { if (marks.has(p) && marks.get(p) !== v) throw Error('Selected marking mismatch.'); marks.set(p, v); }
    for (const id of selected) for (const [p, v] of tiles[id].t) totals[p] += v;
    const forward = new Map(), reverse = new Map();
    for (let p = 0; p < cat.depth; p++) if (totals[p] < 1) forward.set(p, []);
    for (const tile of tiles) {
      if (selected.includes(tile.id) || [...tile.t].some(([p, v]) => totals[p] + v > 1)) continue;
      if ([...tile.m].some(([p, v]) => marks.has(p) && marks.get(p) !== v)) { stats.markingEliminations++; continue; }
      for (const [p, v] of tile.t) if (v > 0 && forward.has(p)) {
        forward.get(p).push(tile.id); if (!reverse.has(tile.id)) reverse.set(tile.id, []); reverse.get(tile.id).push(p);
      }
    }
    stats.peakIncidences = Math.max(stats.peakIncidences, [...forward.values()].reduce((a, x) => a + x.length, 0));
    return { totals, marks, generations, forward, reverse, placements: tiles, selected: new Set(selected) };
  }
  function visit(prefix) {
    if (stats.nodes >= nodeCap) return { status: 'unknown', reason: 'search-node-budget' };
    stats.nodes++;
    let selected = [...prefix];
    while (true) {
      const g = graph(selected);
      if ([...g.forward.values()].some(x => !x.length)) return { status: 'exhausted-finite-search' };
      if (!g.forward.size) return { status: 'equivalent', selected };
      const singleton = [...g.forward].find(([, x]) => x.length === 1);
      if (singleton) { selected.push(singleton[1][0]); stats.forced++; continue; }
      const [p, options] = [...g.forward].sort((a, b) => g.generations[a[0]] - g.generations[b[0]] || a[1].length - b[1].length || a[0] - b[0])[0];
      stats.branches++;
      const ranked = order ? order(options.map(id => tiles[id]), p, g) : options.map(id => tiles[id]);
      if (ranked.length !== options.length || new Set(ranked.map(x => x.id)).size !== options.length || ranked.some(x => !options.includes(x.id))) throw Error('Policy changed the complete candidate domain.');
      for (const tile of ranked) {
        stats.attempts++;
        const result = visit([...selected, tile.id]);
        if (result.status !== 'exhausted-finite-search') return result;
        stats.backtracks++;
      }
      return { status: 'exhausted-finite-search' };
    }
  }
  return { ...visit([]), stats };
}
export class ClusterPolicy {
  constructor(seed = 7) { this.q = new Map(); this.seed = seed >>> 0; this.training = { episodes: 0, validatedBaseMoves: 0, proposals: 0, proposalValidations: 0, proposalRejections: 0 }; }
  random() { this.seed = (1664525 * this.seed + 1013904223) >>> 0; return this.seed / 4294967296; }
  feature(w, m) { return `${count(w)}:${m.kind}`; }
  train(episodes = 40, crossingCap = 3) {
    for (let e = 0; e < episodes; e++) {
      let w = [];
      for (let k = 0; k < 3; k++) { const ms = moves(w, crossingCap); if (!ms.length) break; w = ms[Math.floor(this.random() * ms.length)].after; }
      for (let k = 0; k < 12 && w.length; k++) {
        const ms = moves(w, crossingCap);
        ms.sort((a, b) => (this.q.get(this.feature(w, b)) || 0) - (this.q.get(this.feature(w, a)) || 0));
        const m = ms[this.random() < .25 ? Math.floor(this.random() * ms.length) : 0]; if (!m) break;
        const key = this.feature(w, m), old = this.q.get(key) || 0;
        const next = moves(m.after, crossingCap), future = Math.max(0, ...next.map(x => this.q.get(this.feature(m.after, x)) || 0));
        const reward = m.after.length ? -.1 : 5;
        this.q.set(key, old + .2 * (reward + .9 * future - old));
        this.training.validatedBaseMoves++; w = m.after;
      }
      this.training.episodes++;
    }
  }
  propose(w, crossingCap, length = 3) {
    const expansion = []; let current = clone(w);
    for (let k = 0; k < length; k++) {
      const ms = moves(current, crossingCap);
      ms.sort((a, b) => (this.q.get(this.feature(current, b)) || 0) - (this.q.get(this.feature(current, a)) || 0));
      if (!ms.length || !current.length) break;
      const m = ms[0]; expansion.push({ kind: m.kind, before: canonical(current), after: m.key }); current = m.after;
    }
    this.training.proposals++; return expansion;
  }
  order(tiles, _point, graph, cap) {
    const scores = new Map();
    for (const tile of tiles) {
      const w = parse(tile.before), expansion = this.propose(w, cap, Math.min(3, graph.totals.length - tile.time));
      // Proposal is a preference only; constituents are replayed and never redefine degree.
      let valid = true, current = w;
      const aggregateT = new Map(), aggregateM = new Map(graph.marks), members = new Set();
      for (let k = 0; k < expansion.length; k++) {
        const part = expansion[k];
        const m = moves(current, cap).find(x => x.kind === part.kind && x.key === part.after);
        if (!m) { valid = false; break; } current = m.after;
        const base = graph.placements.find(x => x.time === tile.time + k && x.before === part.before && x.after === part.after);
        if (!base) { valid = false; break; }
        if (members.has(base.id)) continue; members.add(base.id);
        for (const [p, v] of base.m) {
          if (aggregateM.has(p) && aggregateM.get(p) !== v) valid = false;
          aggregateM.set(p, v);
        }
        if (!graph.selected.has(base.id)) for (const [p, v] of base.t) {
          aggregateT.set(p, (aggregateT.get(p) || 0) + v);
          if (graph.totals[p] + aggregateT.get(p) > 1) valid = false;
        }
        if (!valid) break;
      }
      this.training.proposalValidations++; if (!valid) this.training.proposalRejections++;
      scores.set(tile.id, valid && expansion[0]?.after === tile.after ? 1 : 0);
    }
    return [...tiles].sort((a, b) => scores.get(b.id) - scores.get(a.id) || a.id - b.id);
  }
}
export function solve(source, target = [], options = {}) {
  const started = performance.now();
  if (colorDimension(source) !== colorDimension(target)) return { status: 'inequivalent', reason: 'Fox-3-coloring-dimension', sourceDimension: colorDimension(source), targetDimension: colorDimension(target), totalMs: performance.now() - started };
  if (canonical(source) === canonical(target)) return { status: 'equivalent', certificate: { version: VERSION, source: canonical(source), target: canonical(target), crossingCap: options.crossingCap || count(source), steps: [] }, totalMs: performance.now() - started };
  const cat = catalog(source, target, options), catalogMs = performance.now() - started;
  if (!cat.complete) return { status: 'unknown', ...cat, totalMs: performance.now() - started };
  let learned = null, learningMs = 0;
  if (options.lane !== 'baseline') { const t = performance.now(); learned = learnSeamMarkings(cat); learningMs = performance.now() - t; }
  let policy = null, trainingMs = 0;
  if (options.lane === 'gcts+rl') { const t = performance.now(); policy = new ClusterPolicy(options.seed); policy.train(options.episodes || 20, options.crossingCap || 3); trainingMs = performance.now() - t; }
  const t = performance.now(), result = pointSearch(cat, { learned, nodeCap: options.nodeCap, order: policy ? (ts, p, g) => policy.order(ts, p, g, cat.crossingCap) : null });
  const searchMs = performance.now() - t;
  const summary = { ...result, catalogMs, learningMs, trainingMs, searchMs, states: cat.stateCount, tiles: cat.tiles.length, learnedFailures: learned?.failures.length || 0, assignedMarkValues: learned?.assignedValues || 0, training: policy?.training || null };
  if (result.status === 'equivalent') {
    summary.certificate = { version: VERSION, source: canonical(source), target: canonical(target), crossingCap: cat.crossingCap,
      steps: result.selected.map(id => cat.tiles[id]).sort((a, b) => a.time - b.time).filter(x => x.kind !== 'hold').map(x => ({ kind: x.kind, after: x.after, patch: x.patch })) };
    verifyMovie(summary.certificate);
  } else if (result.status === 'exhausted-finite-search') summary.knotEquivalence = 'unknown';
  return { ...summary, totalMs: performance.now() - started };
}
export const examples = {
  curl: 'O1+ U1+',
  bigon: 'O1+ O2- U2- U1+',
  trefoil: 'O1+ U2+ O3+ U1+ O2+ U3+',
};
