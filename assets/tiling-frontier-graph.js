// Base tiling bookkeeping. Geometry, markings and branch policies are adapters;
// none of them may bypass zero-degree detection or forced-point propagation.
export function createFrontierGraph({ enumerate, legal, compatibleWithAddition, footprint }) {
  const points = new Map(), candidates = new Map(), buckets = new Map(), incidence = new Map();
  let trail = null;
  const counters = { fullBuilds: 0, updates: 0, rollbacks: 0, candidateChecks: 0 };
  const set = (map, key, value) => { const had = map.has(key), old = map.get(key); trail?.push(() => had ? map.set(key, old) : map.delete(key)); map.set(key, value); };
  const del = (map, key) => { if (!map.has(key)) return; const old = map.get(key); trail?.push(() => map.set(key, old)); map.delete(key); };
  const add = (set, key) => { if (set.has(key)) return; trail?.push(() => set.delete(key)); set.add(key); };
  const drop = (set, key) => { if (!set.has(key)) return; trail?.push(() => set.add(key)); set.delete(key); };
  function cells(bounds) {
    const result = [];
    for (let x = Math.floor((bounds.x0 - 1e-8) / 4); x <= Math.floor((bounds.x1 + 1e-8) / 4); x++)
      for (let y = Math.floor((bounds.y0 - 1e-8) / 4); y <= Math.floor((bounds.y1 + 1e-8) / 4); y++) result.push(`${x},${y}`);
    return result;
  }
  function link(record, key) {
    const point = points.get(key); if (!point) return;
    add(record.points, key); if (record.legal) add(point.legal, record.tile.id);
  }
  function ensure(tile) {
    let record = candidates.get(tile.id);
    if (!record) {
      counters.candidateChecks++;
      record = { tile, legal: legal(tile), points: new Set() };
      set(candidates, tile.id, record);
      for (const key of tile.vertices) { if (!incidence.has(key)) set(incidence, key, new Set()); add(incidence.get(key), tile.id); }
      // Only currently legal candidates can be invalidated by adding a tile.
      if (record.legal) for (const cell of cells(footprint(tile))) {
        if (!buckets.has(cell)) set(buckets, cell, new Set());
        add(buckets.get(cell), tile.id);
      }
    }
    for (const key of tile.vertices) link(record, key);
  }
  function sync(frontier) {
    const next = new Map(frontier.map(p => [p.key, p]));
    for (const [key, point] of points) if (!next.has(key)) {
      // Reverse incidence also records illegal candidates, so remove all links.
      for (const id of incidence.get(key) || []) drop(candidates.get(id).points, key);
      del(points, key);
    }
    const fresh = [];
    for (const [key, meta] of next) {
      const old = points.get(key);
      if (old) { if (old.depth !== meta.depth || old.total !== meta.total) set(points, key, { ...meta, legal: old.legal }); }
      else { set(points, key, { ...meta, legal: new Set() }); fresh.push(meta); }
    }
    for (const point of fresh) for (const tile of enumerate(point)) ensure(tile);
  }
  function build(frontier) { if (counters.fullBuilds) throw Error('Graph already initialized'); sync(frontier); counters.fullBuilds++; }
  function push(tile, frontier) {
    if (trail) throw Error('Nested graph transaction');
    trail = [];
    const affected = new Set(cells(footprint(tile)).flatMap(c => [...(buckets.get(c) || [])]));
    for (const id of affected) {
      const record = candidates.get(id); if (!record?.legal) continue;
      counters.candidateChecks++;
      if (compatibleWithAddition(record.tile, tile)) continue;
      trail.push(() => { record.legal = true; }); record.legal = false;
      for (const key of record.points) if (points.has(key)) drop(points.get(key).legal, id);
    }
    sync(frontier);
    const delta = trail; trail = null; counters.updates++; return delta;
  }
  // Reversible pruning after a learned constraint or an exhausted child.
  // Callers append this delta to the current placement frame's undo trail.
  function refine(allowed) {
    if(trail)throw Error('Cannot refine an open graph transaction');trail=[];
    for(const record of candidates.values())if(record.legal&&!allowed(record.tile)){
      trail.push(()=>{record.legal=true;});record.legal=false;
      for(const key of record.points)if(points.has(key))drop(points.get(key).legal,record.tile.id);
    }
    const delta=trail;trail=null;return delta;
  }
  function pop(delta) { if (trail) throw Error('Cannot roll back an open update'); for (let i = delta.length - 1; i >= 0; i--) delta[i](); counters.rollbacks++; }
  function choose(compare = (a, b) => a.depth - b.depth || a.key.localeCompare(b.key)) {
    const frontier = [...points.values()];
    const dead = frontier.find(p => p.legal.size === 0);
    if (dead) return { point: dead, candidates: [], forced: false, dead: true };
    const forced = frontier.filter(p => p.legal.size === 1).sort(compare);
    const selected = forced[0] || frontier.sort((a, b) => a.legal.size - b.legal.size || compare(a, b))[0];
    return selected ? { point: selected, candidates: [...selected.legal].map(id => candidates.get(id).tile), forced: selected.legal.size === 1, dead: false } : null;
  }
  function summary() {
    let incidences = 0, forcedPoints = 0, deadPoints = 0; const live = new Set();
    for (const p of points.values()) { incidences += p.legal.size; forcedPoints += +(p.legal.size === 1); deadPoints += +(p.legal.size === 0); for (const id of p.legal) live.add(id); }
    return { points: points.size, candidates: live.size, incidences, forcedPoints, deadPoints, ...counters };
  }
  // Read-only copies for tests and policy adapters; no engine state escapes.
  function inspect() { return [...points.values()].map(p => ({ key: p.key, depth: p.depth, total: p.total, candidates: [...p.legal].sort() })).sort((a,b) => a.key.localeCompare(b.key)); }
  function candidateRecords() { return [...candidates.values()].filter(r => r.points.size > 0).map(r => ({tile:r.tile,legal:r.legal})); }
  return { build, push, pop, refine, choose, summary, inspect, candidateRecords };
}
