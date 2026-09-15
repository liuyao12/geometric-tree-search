// Controlled moving-support calibration. The smooth loss is NOT an exact tiling test.
export const CORNERS = [[0, 0], [1, 0], [1, 1], [0, 1]];
const SIGNS = [1, -1, 1, -1];
export const VERSION = 'moving-anchors-v1';
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

export function createModel(seed = 7) {
  let state = seed >>> 0;
  const random = () => {
    state = (Math.imul(1664525, state) + 1013904223) >>> 0;
    return state / 4294967296;
  };
  return { version: VERSION, seed, step: 0, anchors: CORNERS.map(([x, y], i) => ({
    x: x + (random() - .5) * .5, y: y + (random() - .5) * .5,
    t: .12 + random() * .25, m: SIGNS[i] * (.25 + random()),
  })) };
}

// A square contact graph is supplied as supervision: copies translated by a unit
// in x/y must identify their shared corners. Only the prototype anchors are learned.
// Center gauge removes the unobservable common translation; D4 t-symmetry and
// unit marking norm remove underdetermined values and the all-zero marking solution.
export function objective(model) {
  const a = model.anchors;
  const grad = a.map(() => ({ x: 0, y: 0, t: 0, m: 0 }));
  const terms = { contact: 0, gauge: 0, coverage: 0, symmetry: 0, marking: 0, amplitude: 0 };
  const edges = [[0, 1, 1, 0], [3, 2, 1, 0], [0, 3, 0, 1], [1, 2, 0, 1]];
  for (const [i, j, dx, dy] of edges) {
    for (const [axis, delta] of [['x', dx], ['y', dy]]) {
      const r = a[j][axis] - a[i][axis] - delta;
      terms.contact += r * r;
      grad[j][axis] += 2 * r; grad[i][axis] -= 2 * r;
    }
    // Unit translations act on scalar markings by sign reversal.
    const r = a[i].m + a[j].m;
    terms.marking += r * r;
    grad[i].m += 2 * r; grad[j].m += 2 * r;
  }
  for (const axis of ['x', 'y']) {
    const r = a.reduce((s, p) => s + p[axis], 0) / 4 - .5;
    terms.gauge += 4 * r * r;
    for (const g of grad) g[axis] += 2 * r;
  }
  const sum = a.reduce((s, p) => s + p.t, 0), residual = sum - 1;
  terms.coverage = residual * residual;
  const norm = a.reduce((s, p) => s + p.m * p.m, 0) / 4 - 1;
  terms.amplitude = norm * norm;
  a.forEach((p, i) => {
    const r = p.t - sum / 4;
    terms.symmetry += r * r;
    grad[i].t += 2 * residual + 2 * r;
    grad[i].m += norm * p.m;
  });
  return { loss: Object.values(terms).reduce((s, x) => s + x, 0), terms, grad };
}

export function trainStep(model, { moveAnchors = true, rate = .06 } = {}) {
  const { grad } = objective(model);
  model.anchors.forEach((p, i) => {
    if (moveAnchors) { p.x -= rate * grad[i].x; p.y -= rate * grad[i].y; }
    p.t = clamp(p.t - rate * grad[i].t, 0, 1);
    p.m = clamp(p.m - rate * grad[i].m, -2, 2);
  });
  model.step++;
  return objective(model);
}

export function compileModel(model) {
  const a = model.anchors;
  if (a.length !== 4 || a.some(p => !['x', 'y', 't', 'm'].every(k => Number.isFinite(p[k]))))
    return { ok: false, reason: 'Invalid anchor data.' };
  const error = Math.max(...a.flatMap((p, i) => [Math.abs(p.x - CORNERS[i][0]),
    Math.abs(p.y - CORNERS[i][1]), Math.abs(p.t - .25), Math.abs(Math.abs(p.m) - 1)]));
  if (error > .025) return { ok: false, reason: 'Not ready: anchors, t or marking amplitude are over 0.025 from the square model.', error };
  const points = a.map(p => ({ x: Math.round(p.x), y: Math.round(p.y),
    units: Math.round(p.t * 12), mark: Math.sign(p.m) }));
  const phase = points[0].mark;
  if (points.some((p, i) => p.units !== 3 || p.mark !== phase * SIGNS[i]))
    return { ok: false, reason: 'Rounded values fail square symmetry or marking agreement.', error };
  return { ok: true, version: VERSION, capacity: 12, points, error,
    semantics: 'Projected square hypothesis: integer coordinates, t in twelfths, m in {-1,+1}.' };
}

export function makeProblem(compiled, size = 4) {
  if (!compiled.ok || !Number.isInteger(size) || size < 4 || size % 2)
    throw new Error('An exact compiled model and an even torus size >= 4 are required.');
  const key = (x, y) => ((y % size + size) % size) * size + ((x % size + size) % size);
  const candidates = [];
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) for (const phase of [1, -1]) {
    candidates.push({ id: candidates.length, x, y, phase,
      points: compiled.points.map(p => ({ p: key(x + p.x, y + p.y), units: p.units,
        mark: p.mark * phase * ((x + y) % 2 ? -1 : 1) })) });
  }
  return { size, capacity: 12, count: size * size, candidates };
}

// Rebuild both incidence directions exhaustively for this deliberately tiny target.
// State is copied at each branch, so exclusions, totals and markings roll back exactly.
export function graph(problem, selected) {
  const totals = Array(problem.count).fill(0), marks = Array(problem.count).fill(null);
  for (const id of selected) for (const q of problem.candidates[id].points) {
    totals[q.p] += q.units;
    if (marks[q.p] !== null && marks[q.p] !== q.mark) throw new Error('Inconsistent selected marking');
    marks[q.p] = q.mark;
  }
  const frontier = new Map(totals.flatMap((t, p) => t < problem.capacity ? [[p, []]] : []));
  const reverse = new Map();
  let markingEliminations = 0, capacityEliminations = 0;
  for (const c of problem.candidates) {
    if (selected.includes(c.id)) continue;
    if (c.points.some(q => totals[q.p] + q.units > problem.capacity)) { capacityEliminations++; continue; }
    if (c.points.some(q => marks[q.p] !== null && marks[q.p] !== q.mark)) { markingEliminations++; continue; }
    const incidence = c.points.filter(q => frontier.has(q.p));
    if (!incidence.length) continue;
    reverse.set(c.id, incidence);
    for (const q of incidence) frontier.get(q.p).push(c.id);
  }
  return { totals, marks, frontier, reverse, markingEliminations, capacityEliminations };
}

export function decision(g) {
  const points = [...g.frontier.entries()];
  if (!points.length) return { kind: 'complete' };
  if (points.some(([, ids]) => ids.length === 0)) return { kind: 'dead' };
  const forced = points.find(([, ids]) => ids.length === 1);
  if (forced) return { kind: 'forced', point: forced[0], ids: forced[1] };
  // Every target point is an explicitly activated root of generation 0.
  points.sort((a, b) => a[1].length - b[1].length || a[0] - b[0]);
  return { kind: 'branch', point: points[0][0], ids: points[0][1] };
}

// Independent result verifier: reconstruct coordinates/values from the frozen
// prototype and transforms, not graph totals or cached candidate point lists.
export function verify(compiled, size, placements) {
  if (!compiled.ok || !Number.isInteger(size) || size < 4 || size % 2) return false;
  const totals = new Map(), marks = new Map(), seen = new Set();
  for (const c of placements) {
    if (![c.x, c.y].every(v => Number.isInteger(v) && v >= 0 && v < size) || ![1, -1].includes(c.phase)) return false;
    const id = `${c.x},${c.y},${c.phase}`;
    if (seen.has(id)) return false;
    seen.add(id);
    for (const a of compiled.points) {
      const p = `${(c.x + a.x + size) % size},${(c.y + a.y + size) % size}`;
      const m = a.mark * c.phase * ((c.x + c.y) % 2 ? -1 : 1);
      totals.set(p, (totals.get(p) || 0) + a.units);
      if (marks.has(p) && marks.get(p) !== m) return false;
      marks.set(p, m);
    }
  }
  return totals.size === size * size && [...totals.values()].every(v => v === 12);
}

export function* search(compiled, { size = 4, budget = 2000 } = {}) {
  const problem = makeProblem(compiled, size);
  const stats = { attempts: 0, forced: 0, branches: 0, backtracks: 0, accepted: 0 };
  let cutoff = false;
  function* visit(selected) {
    const g = graph(problem, selected), next = decision(g);
    yield { kind: next.kind, selected: [...selected], graph: g, stats: { ...stats }, problem };
    if (next.kind === 'complete') return verify(compiled, size, selected.map(id => problem.candidates[id])) ? selected : null;
    if (next.kind === 'dead') return null;
    if (stats.attempts >= budget) { cutoff = true; return null; }
    if (next.kind === 'branch') stats.branches++;
    for (const id of next.ids) {
      if (stats.attempts >= budget) { cutoff = true; break; }
      stats.attempts++;
      if (next.kind === 'forced') stats.forced++;
      const result = yield* visit([...selected, id]);
      if (result) return result;
      stats.backtracks++;
      if (cutoff) break;
    }
    return null;
  }
  const result = yield* visit([]);
  stats.accepted = result?.length || 0;
  return { status: result ? 'finite exact tiling on a torus' : cutoff ? 'unknown: budget exhausted' : 'restricted-model failure',
    placements: result ? result.map(id => problem.candidates[id]) : [], stats, size, compiled };
}
