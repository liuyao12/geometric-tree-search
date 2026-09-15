import { A2_TILE_LOOPS, FixedTurtleMarking, tileOrientations, SparseA2Marking, a2Transform, a2Add } from './a2-tiling-engine.js';
export const VERSION = 'turtle-point-fit-v1';
export const ORIENTATIONS = tileOrientations('turtle', A2_TILE_LOOPS.turtle);
export const TURTLE = ORIENTATIONS[0];
function examples() {
  const points = new Map();
  const get = point => {
    const key = point.join(',');
    if (!points.has(key)) points.set(key, { point: [...point], t: 0, occupied: false, m: [null, null, null] });
    return points.get(key);
  };
  for (const e of TURTLE.occupancy.values()) Object.assign(get(e.point), { t: e.weight / 12, occupied: true });
  for (const e of new FixedTurtleMarking(1).support) get(e.point).m[e.component] = e.value;
  return [...points.values()];
}
export function createModel(seed = 7) {
  let state = seed >>> 0;
  const random = () => ((state = (Math.imul(state, 1664525) + 1013904223) >>> 0) / 4294967296);
  return { version: VERSION, seed, step: 0, anchors: examples().map(target => {
    const x = target.point[0] + (random() - .5) * 1.3, y = target.point[1] + (random() - .5) * 1.3;
    return { target, point: [x, y, -x-y], t: target.occupied ? random() : 0,
      m: target.m.map(v => v === null ? null : random() * 2 - 1) };
  }) };
}
export function loss(model) {
  let sum = 0, count = 0;
  for (const a of model.anchors) {
    for (let i = 0; i < 2; i++) { sum += (a.point[i] - a.target.point[i]) ** 2; count++; }
    if (a.target.occupied) { sum += (a.t - a.target.t) ** 2; count++; }
    for (let c = 0; c < 3; c++) if (a.m[c] !== null) { sum += (a.m[c] - a.target.m[c]) ** 2; count++; }
  }
  return sum / count;
}
// Gradient descent on supervised squared error. The example contains the known
// Turtle data; this visual does not claim to discover its matching rules.
export function trainStep(model) {
  for (const a of model.anchors) {
    for (let i = 0; i < 2; i++) a.point[i] -= .09 * (a.point[i] - a.target.point[i]);
    a.point[2] = -a.point[0] - a.point[1];
    if (a.target.occupied) a.t -= .09 * (a.t - a.target.t);
    for (let c = 0; c < 3; c++) if (a.m[c] !== null) a.m[c] -= .09 * (a.m[c] - a.target.m[c]);
  }
  model.step++;
}
export function freezeModel(model) {
  if (model.version !== VERSION || model.anchors.length !== examples().length) throw new Error('Invalid Turtle model');
  const support = [], points = [], seen = new Set();
  for (const a of model.anchors) {
    const point = a.point.map(v => Math.round(v) || 0), units = Math.round(a.t * 12);
    if (a.point.some((v, i) => !Number.isFinite(v) || Math.abs(v - point[i]) > .025) || point.reduce((s,v)=>s+v,0) !== 0)
      throw new Error('Keep training: anchors have not reached the A₂ lattice.');
    const key = point.join(',');
    if (seen.has(key)) throw new Error('Two fitted anchors coincide.');
    seen.add(key);
    if (!Number.isFinite(a.t) || Math.abs(a.t - units / 12) > .025 || units !== (TURTLE.occupancy.get(key)?.weight ?? 0))
      throw new Error('Keep training: t-values do not yet reproduce the Turtle.');
    points.push({ point, units });
    for (let component = 0; component < 3; component++) if (a.m[component] !== null) {
      const value = Math.round(a.m[component]) || 0;
      if (!Number.isFinite(a.m[component]) || Math.abs(a.m[component] - value) > .025 || Math.abs(value) > 1)
        throw new Error('Keep training: marking values are not ready.');
      support.push({ tile: 'turtle', point: [...point], component, value });
    }
  }
  const fitted = new Map(support.map(e=>[`${e.point}|${e.component}`,e.value]));
  const expected = new Map(new FixedTurtleMarking(1).support.map(e=>[`${e.point}|${e.component}`,e.value]));
  if (fitted.size !== expected.size || [...expected].some(([k,v])=>fitted.get(k)!==v)) throw new Error('The fitted marking does not yet reproduce the Turtle example.');
  return { version: VERSION, points, support, seed: model.seed, steps: model.step, loss: loss(model) };
}
export function makeMarking(frozen) {
  return new SparseA2Marking(frozen.support, { label: 'Fitted Turtle example', learnedRevisions: 0 });
}
export function verifyPatch(frozen, placements) {
  const totals = new Map(), contacts = new Map(), seen = new Set();
  let matched = 0;
  for (const p of placements) {
    const orientation = ORIENTATIONS.find(o=>o.index===p.orientation.index);
    if (!orientation || p.tile !== 'turtle' || p.translation.length !== 3 || !p.translation.every(Number.isInteger) || p.translation.reduce((s,v)=>s+v,0)!==0) throw new Error('Invalid Turtle placement');
    const key = `${orientation.index}:${p.translation}`;
    if (seen.has(key)) throw new Error('Duplicate Turtle placement');
    seen.add(key);
    for (const e of frozen.points) if (e.units > 0) {
      const q = a2Add(a2Transform(e.point, orientation.symmetry), p.translation).join(',');
      const next = (totals.get(q) || 0) + e.units;
      if (next > 12) throw new Error('Turtle t-values overflow');
      totals.set(q, next);
    }
    const perm = orientation.symmetry.permutation;
    const sign = ((perm[0]>perm[1])+(perm[0]>perm[2])+(perm[1]>perm[2]))%2 ? -1 : 1;
    for (const e of frozen.support) {
      const q = `${a2Add(a2Transform(e.point,orientation.symmetry),p.translation)}|${perm.indexOf(e.component)}`, value = sign * e.value;
      if (contacts.has(q)) { if (contacts.get(q)!==value) throw new Error('Turtle marking conflict'); matched++; }
      contacts.set(q,value);
    }
  }
  return { tiles: placements.length, completePoints: [...totals.values()].filter(v=>v===12).length,
    frontierPoints: [...totals.values()].filter(v=>v<12).length, matched, label: 'Consistent finite Turtle patch' };
}
