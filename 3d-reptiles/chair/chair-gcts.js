import { selectFrontier } from './frontier-order.js';
export { selectFrontier } from './frontier-order.js';
import { createReliefPointModel } from './relief-points.js';
import { VARIANTS, FACE_DIRECTIONS, add, sub, key, markPoint, markValue, worldMarks, verifyPatch } from './chair44.js';
export { CANONICAL_CHILDREN, FACE_DIRECTIONS, chairLeaves, localCells } from './chair44.js';

// Arrow control: integer cell-center t=1 and panel-center equality m-values.
// Relief modes: exact cell and panel-probe t-occupancy, without m-values.
// Rebuild the complete point/candidate graph on each step. No collared inventory,
// substitution witness, target boundary, or precomputed growth plan is supplied.
const compiled = new Map();
function candidateAt(variantId,origin) {
  const id=`${variantId}@${key(origin)}`;
  if(!compiled.has(id)) {
    const variant=VARIANTS[variantId], placement={variantId,origin};
    compiled.set(id,{...placement,id,cells:variant.cells.map(c=>key(add(c,origin))),
      marks:worldMarks(placement).map(m=>[key(markPoint(m)),key(markValue(m))])});
  }
  return compiled.get(id);
}
function indexState(state) {
  const occupied=new Map(), marks=new Map(), frontier=new Map();
  for(const p of state.placements) {
    const c=candidateAt(p.variantId,p.origin);
    c.cells.forEach(k=>occupied.set(k,p.generation));
    c.marks.forEach(([k,v])=>marks.set(k,v));
  }
  for(const [k,generation] of occupied) for(const d of FACE_DIRECTIONS) {
    const point=add(k.split(',').map(Number),d), id=key(point);
    if(!occupied.has(id)) {
      const old=frontier.get(id);
      if(!old || generation<old.generation) frontier.set(id,{id,point,generation,candidates:new Set()});
    }
  }
  return {occupied,marks,frontier};
}
const reliefModels = {
  'relief-offset': createReliefPointModel(),
  'relief-centered': createReliefPointModel({centered:true})
};
function checkRule(rule) {
  if (rule !== 'arrows' && !reliefModels[rule]) throw new Error('Unknown Chair44 matching rule');
}
export function enumerateGrowthCandidates(state) {
  const rule = state.rule ?? 'arrows';
  checkRule(rule);
  if (reliefModels[rule]) {
    const graph = reliefModels[rule].graphFor(state.placements);
    return {frontier:graph.frontier,candidateNodes:graph.candidates,frontierCount:graph.frontier.size,
      tested:graph.tested,occupancyRejected:graph.rejected,markingRejected:0,
      dead:Boolean(graph.dead),deadPoint:graph.dead,forced:!graph.dead&&graph.forced,candidates:graph.choices};
  }
  const index=indexState(state), candidates=new Map(), seen=new Set();
  let tested=0, occupancyRejected=0, markingRejected=0;
  for(const point of index.frontier.values()) for(const variant of VARIANTS) for(const cell of variant.cells) {
    const c=candidateAt(variant.id,sub(point.point,cell));
    if(seen.has(c.id)) continue;
    seen.add(c.id); tested++;
    if(c.cells.some(k=>index.occupied.has(k))) {occupancyRejected++;continue;}
    if(c.marks.some(([k,v])=>index.marks.has(k)&&index.marks.get(k)!==v)) {markingRejected++;continue;}
    candidates.set(c.id,c);
    for(const k of c.cells) index.frontier.get(k)?.candidates.add(c.id);
  }
  const points=[...index.frontier.values()];
  const {dead,forced,selected}=selectFrontier(points);
  const choices=dead?[]:[...(selected?.candidates??[])].map(id=>candidates.get(id));
  choices.sort((a,b)=>a.origin.reduce((s,v)=>s+v*v,0)-b.origin.reduce((s,v)=>s+v*v,0)||a.id.localeCompare(b.id));
  return {frontier:index.frontier,candidateNodes:candidates,frontierCount:points.length,tested,
    occupancyRejected,markingRejected,dead:Boolean(dead),forced:!dead&&Boolean(forced),candidates:choices};
}
export function createGrowthState(level=2,rule='arrows') {
  checkRule(rule);
  return {rule,catalog:{variants:VARIANTS,targetCount:8**level},placements:[{variantId:0,origin:[0,0,0],generation:0}],
    history:[],stack:[],tested:0,rejected:0,solverBacktracks:0,forcedPlacements:0,branchDecisions:0,complete:false,status:'ready'};
}
// An imported patch is the fixed root of a new local search. Its tiles have
// generation zero and no branch frames, so rollback cannot remove them.
export function createGrowthStateFromPatch(placements,rule='arrows') {
  checkRule(rule);
  if (!placements.length) throw new Error('Invalid starting Chair44 patch');
  if (reliefModels[rule]) {
    try { reliefModels[rule].indexState(placements); }
    catch { throw new Error('Invalid starting Chair44 patch: relief overlaps'); }
  } else if (!verifyPatch(placements).valid) throw new Error('Invalid starting Chair44 patch');
  const state = createGrowthState(2,rule);
  return {...state,
    catalog: {...state.catalog, targetCount: 64 * (Math.floor(placements.length / 64) + 1)},
    placements: placements.map(({variantId, origin}) => ({variantId, origin: [...origin], generation: 0}))};
}
function place(state,candidate,graph) {
  const generations=candidate.cells.map(k=>graph.frontier.get(k)?.generation).filter(g=>g!==undefined);
  return {...state,placements:[...state.placements,{variantId:candidate.variantId,origin:candidate.origin,generation:candidate.generation??(1+Math.min(...generations))}]};
}
export function growOne(previous) {
  // Bound geometric placement caches to one resumable batch of search work.
  reliefModels[previous.rule]?.clearCache();
  if(previous.complete && previous.status !== 'consistent finite patch') return previous;
  let state={...previous,complete:false,history:[...previous.history,previous]};
  if(previous.complete) state.catalog={...previous.catalog,targetCount:previous.catalog.targetCount+64};
  for(let attempt=0;attempt<32;attempt++) {
    const graph=enumerateGrowthCandidates(state);
    state={...state,tested:state.tested+graph.tested,rejected:state.rejected+graph.markingRejected+(reliefModels[state.rule]?graph.occupancyRejected:0),frontierCount:graph.frontierCount};
    if(graph.dead) {
      let frame;
      const stack=[...state.stack];
      while(stack.length && !frame) {const next=stack.pop();if(next.remaining.length) frame=next;}
      if(!frame) return {...state,complete:true,status:'exhausted'};
      const [candidate,...remaining]=frame.remaining;
      state={...state,placements:frame.placements,stack:[...stack,{...frame,remaining}],solverBacktracks:state.solverBacktracks+1};
      state=place(state,candidate,enumerateGrowthCandidates(state));
      continue;
    }
    // Check the whole frontier before accepting even a finite growth checkpoint.
    if(state.placements.length>=state.catalog.targetCount) return {...state,complete:true,status:'consistent finite patch'};
    const [candidate,...remaining]=graph.candidates;
    if(!candidate) return {...state,complete:true,status:'no active obligations'};
    if(!graph.forced) state={...state,stack:[...state.stack,{placements:state.placements,remaining}],branchDecisions:state.branchDecisions+1};
    else state={...state,forcedPlacements:state.forcedPlacements+1};
    state=place(state,candidate,graph);
    const after=enumerateGrowthCandidates(state);
    if(!after.dead) return {...state,frontierCount:after.frontierCount,complete:state.placements.length>=state.catalog.targetCount,
      status:state.placements.length>=state.catalog.targetCount?'consistent finite patch':'growing'};
  }
  return {...state,status:'searching; step budget reached'};
}
export function shrinkOne(state) {return state.history.at(-1)??state;}
export function exposedMarks(state) {
  const occupied=new Set(state.placements.flatMap(p=>candidateAt(p.variantId,p.origin).cells));
  return state.placements.flatMap(worldMarks).filter(m=>!occupied.has(key(add(m.cell,m.direction))));
}
