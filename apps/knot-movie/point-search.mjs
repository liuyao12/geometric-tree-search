// Domain-independent point search. No diagram parser, move names, or knot invariants.
// Full re-enumeration after each placement is intentional in this small pilot.
// Both incidence directions, mark-only dependencies, global scheduling and rollback are explicit.
export function pointSearch(cat, { learned = null, nodeCap = 10000, order = null, initialSelected = [] } = {}) {
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
  return { ...visit(initialSelected), stats };
}

// Learn only after observed branch failures. A fresh unmarked exhaustive probe
// with just the candidate fixed checks whether its rejection is context-free.
// A budget stop supplies no negative label. Proven guards become ordinary
// assigned point values; every activation rebuilds the whole live graph.
export function onlinePointSearch(cat, { nodeCap = 10000, learn = true,
  proofNodeCap = 10000, learningAttemptCap = 64, seed = 31 } = {}) {
  const baseBoundary = new Map([[`seam:0`, cat.sourceKey], [`seam:${cat.depth}`, cat.targetKey]]);
  const tiles = cat.tiles.map(x => ({ ...x, m: new Map(x.m) }));
  const boundary = new Map(baseBoundary), tested = new Set(), events = [];
  const occupiedPoints=new Set([...boundary.keys(),...tiles.flatMap(x=>[...x.m.keys()])]);
  const learnedPoints=new Set();
  const ids=tiles.map(x=>x.id); let randomState=(seed ?? 0)>>>0;
  // Neutral permutation prevents the inventory author's grouping by move type
  // from becoming an implicit search heuristic. No semantic fields are read.
  if (seed!==null) for (let i=ids.length-1;i>0;i--) {
    randomState=(1664525*randomState+1013904223)>>>0;
    const j=Math.floor(randomState/4294967296*(i+1));[ids[i],ids[j]]=[ids[j],ids[i]];
  }
  const ranks=new Map(ids.map((id,i)=>[id,i]));
  const stats = { nodes: 0, attempts: 0, forced: 0, branches: 0, backtracks: 0,
    markingEliminations: 0, learnedMarkingEliminations: 0, graphBuilds: 0,
    peakIncidences: 0, learningAttempts: 0, learningNodes: 0,
    unresolvedLabels: 0, contextDependentFailures: 0, markingVersion: 0 };
  function graph(selected, excluded) {
    stats.graphBuilds++;
    const totals = Array(cat.depth).fill(0), marks = new Map(boundary);
    for (const id of selected) {
      for (const [p, v] of tiles[id].t) totals[p] += v;
      for (const [p, v] of tiles[id].m) {
        if (marks.has(p) && marks.get(p) !== v) throw Error('Prefix invalid after marking update.');
        marks.set(p, v);
      }
    }
    const forward = new Map(), reverse = new Map();
    for (let p = 0; p < cat.depth; p++) if (totals[p] < 1) forward.set(p, []);
    for (const tile of tiles) {
      if (selected.includes(tile.id) || excluded.has(tile.id) || [...tile.t].some(([p,v]) => totals[p]+v>1)) continue;
      const mismatches = [...tile.m].filter(([p,v]) => marks.has(p) && marks.get(p)!==v);
      if (mismatches.length) {
        stats.markingEliminations++;
        if (mismatches.some(([p])=>learnedPoints.has(p))) stats.learnedMarkingEliminations++;
        continue;
      }
      for (const [p,v] of tile.t) if (v>0 && forward.has(p)) {
        forward.get(p).push(tile.id);
        if (!reverse.has(tile.id)) reverse.set(tile.id, []);
        reverse.get(tile.id).push(p);
      }
    }
    stats.peakIncidences=Math.max(stats.peakIncidences,[...forward.values()].reduce((n,x)=>n+x.length,0));
    return { forward, reverse };
  }
  function observe(tile, selected) {
    if (!learn || tested.has(tile.id) || stats.learningAttempts>=learningAttemptCap) return;
    tested.add(tile.id); stats.learningAttempts++;
    const began=performance.now();
    const probe=pointSearch(cat,{initialSelected:[tile.id],nodeCap:proofNodeCap,
      order:options=>[...options].sort((a,b)=>ranks.get(a.id)-ranks.get(b.id))});
    stats.learningNodes+=probe.stats.nodes;
    const event={candidate:tile.id,observedPrefix:[...selected],outcome:probe.status,
      proofNodes:probe.stats.nodes,proofMs:performance.now()-began};
    if (probe.status==='exhausted-finite-search') {
      let point=`learned:${stats.markingVersion+1}:${tile.id}`;
      while (occupiedPoints.has(point)) point+=':';
      occupiedPoints.add(point); learnedPoints.add(point);
      boundary.set(point,0); tile.m.set(point,1); stats.markingVersion++;
      event.marking={point,boundaryValue:0,candidateValue:1,version:stats.markingVersion};
    } else if (probe.status==='unknown') stats.unresolvedLabels++;
    else stats.contextDependentFailures++;
    events.push(event);
  }
  function visit(prefix) {
    if (stats.nodes>=nodeCap) return {status:'unknown',reason:'search-node-budget'};
    stats.nodes++;
    const selected=[...prefix],excluded=new Set(); let branching=false;
    while (true) {
      const g=graph(selected,excluded);
      if ([...g.forward.values()].some(x=>!x.length)) return {status:'exhausted-finite-search'};
      if (!g.forward.size) return {status:'equivalent',selected};
      const singleton=[...g.forward].find(([,x])=>x.length===1);
      if (singleton) {selected.push(singleton[1][0]);stats.forced++;branching=false;continue;}
      // All required obligations are roots of generation zero in this reduction.
      const [,options]=[...g.forward].sort((a,b)=>a[1].length-b[1].length||a[0]-b[0])[0];
      if (!branching) {stats.branches++;branching=true;}
      const id=[...options].sort((a,b)=>ranks.get(a)-ranks.get(b))[0]; stats.attempts++;
      const result=visit([...selected,id]);
      if (result.status!=='exhausted-finite-search') return result;
      stats.backtracks++;
      const priorVersion=stats.markingVersion;
      observe(tiles[id],selected);
      // Context-only failure stays local. Re-enter global dead/forced checks.
      if (stats.markingVersion===priorVersion) excluded.add(id);
    }
  }
  const result=visit([]);
  return {...result,stats,learning:{cold:true,initialAssignedValues:0,
    failures:events.filter(x=>x.marking).length,assignedValues:stats.markingVersion*2,
    events,scope:'this exact finite point problem; no transfer to other bounds or targets',
    proofNodeCap,learningAttemptCap,seed,candidateOrder:seed===null?'input order':'content-free seeded permutation',
    attemptBudgetReached:learn&&stats.learningAttempts>=learningAttemptCap}};
}
