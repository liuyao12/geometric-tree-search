import { VARIANTS, FACE_DIRECTIONS, add, sub, key, markPoint, markValue, worldMarks } from './chair44.js';
export { CANONICAL_CHILDREN, FACE_DIRECTIONS, chairLeaves, localCells } from './chair44.js';

// Integer cell-center t=1; doubled-grid panel-center equality m-values.
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
export function selectFrontier(points) {
  const dead=points.find(p=>p.candidates.size===0);
  const forced=points.find(p=>p.candidates.size===1);
  const earliest=[...points].sort((a,b)=>a.generation-b.generation||a.candidates.size-b.candidates.size||a.id.localeCompare(b.id))[0];
  return {dead,forced,selected:dead??forced??earliest};
}
export function enumerateGrowthCandidates(state) {
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
export function createGrowthState(level=2) {
  return {catalog:{variants:VARIANTS,targetCount:8**level},placements:[{variantId:0,origin:[0,0,0],generation:0}],
    history:[],stack:[],tested:0,rejected:0,solverBacktracks:0,forcedPlacements:0,branchDecisions:0,complete:false,status:'ready'};
}
function place(state,candidate,graph) {
  const generations=candidate.cells.map(k=>graph.frontier.get(k)?.generation).filter(g=>g!==undefined);
  return {...state,placements:[...state.placements,{variantId:candidate.variantId,origin:candidate.origin,generation:1+Math.min(...generations)}]};
}
export function growOne(previous) {
  if(previous.complete && previous.status !== 'consistent finite patch') return previous;
  let state={...previous,complete:false,history:[...previous.history,previous]};
  if(previous.complete) state.catalog={...previous.catalog,targetCount:previous.catalog.targetCount+64};
  for(let attempt=0;attempt<32;attempt++) {
    const graph=enumerateGrowthCandidates(state);
    state={...state,tested:state.tested+graph.tested,rejected:state.rejected+graph.markingRejected,frontierCount:graph.frontierCount};
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
