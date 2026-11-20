import {selectPointBranch} from '../../assets/gcts-point-branching.js';
import {markId, pointOrder, worldMark} from './model.mjs';

export function rng(seed) {
  let state = seed >>> 0;
  return () => ((state = (Math.imul(1664525,state)+1013904223)>>>0) / 4294967296);
}
// Only requirements in targets must finish. Every incidence that can help fill
// one is enumerated, including translated tiles spilling outside the window.
export function fill(model,targets,fixed,marks,random,limit,onFailure,exhausted=new Set()) {
  const obligations = [...new Map(targets.map(q=>[String(q),q])).values()].sort(pointOrder)
    .map(q=>({key:String(q),placements:model.incident(q)}));
  const totals=new Map(), values=new Map(), moved=new Set(), stack=[], cache=new Map();
  function entries(p) {
    if (!cache.has(p.id)) cache.set(p.id,marks.map(m=>{
      const v=worldMark(p,m); return [markId(v),v.value];
    }));
    return cache.get(p.id);
  }
  function fits(p) {
    return !moved.has(p.id) && p.rows.every(r=>(totals.get(r.key)??0n)+r.w<=model.capacity)
      && entries(p).every(([k,v])=>!values.has(k)||values.get(k).v===v);
  }
  function push(p) {
    stack.push(p); moved.add(p.id);
    for (const r of p.rows) totals.set(r.key,(totals.get(r.key)??0n)+r.w);
    for (const [k,v] of entries(p)) values.set(k,{v,n:(values.get(k)?.n??0)+1});
  }
  function pop(p) {
    stack.pop(); moved.delete(p.id);
    for (const r of p.rows) {
      const n=totals.get(r.key)-r.w;
      if (n) totals.set(r.key,n); else totals.delete(r.key);
    }
    for (const [k] of entries(p)) if (!--values.get(k).n) values.delete(k);
  }
  let nodes=0, failures=0, backtracks=0;
  function choose() {
    const frontier=[];
    for (const {key,placements} of obligations) {
      if (totals.get(key)===model.capacity) continue;
      frontier.push({point:key,introducedAt:0,legal:placements.filter(fits)});
    }
    if (!frontier.length) return null;
    const last=stack.at(-1);
    const branch=selectPointBranch(frontier,random,{
      isAdjacent:p=>!!last && p.rows.some(r=>last.keys.has(r.key))
    });
    return branch.moves;
  }
  for (const p of fixed) {
    if (!fits(p)) return {status:'exhausted',nodes,backtracks,failures,placements:[]};
    push(p);
  }
  // Frames own their sibling order. No recursion limit on the patch depth.
  const frames=[];
  let status;
  while (!status) {
    const key=[...moved].sort().join(';');
    const known=exhausted.has(key);
    const moves=known?[]:choose();
    if (!moves) { status='covered'; break; }
    frames.push({moves,next:0,depth:stack.length,key,known});
    while (frames.length) {
      const frame=frames.at(-1);
      if (stack.length>frame.depth) { pop(stack.at(-1)); backtracks++; }
      if (frame.next<frame.moves.length) {
        if (nodes>=limit) { status='unknown'; break; }
        nodes++; push(frame.moves[frame.next++].placement); break;
      }
      frames.pop();
      status='exhausted';
      if (!frame.known) {
        failures++;
        exhausted.add(frame.key);
        if (onFailure?.(stack)) status='revised';
      }
      if (status==='revised' || !frames.length) break;
      status=null;
    }
  }
  return {status,nodes,backtracks,failures,placements:status==='covered'?stack.slice():[]};
}
