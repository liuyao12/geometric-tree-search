import {SparseA2Marking} from './a2-tiling-engine.js?v=20260921-viable-corona';

// Explicit comparison control requested for display, not a cold-trained model.
// Candidate 26: finite-csp boundary screen, 2026-10-30. In the base marking,
// omitted components are *, including interior points. Zero remains assigned.
// Compatible with the sampled Hat patches and extracted Turtle incursions;
// preservation of every Hat tiling and full mixed compatibility are unproved.
export const PROVISIONAL_HAT_ID = 'hat-candidate-26';
export const PROVISIONAL_HAT_POINTS = Object.freeze([
  [[0,0,0],['*',-1,'*']], [[1,0,-1],[0,0,0]],
  [[1,1,-2],[-1,1,'*']], [[3,0,-3],[0,0,0]],
  [[4,1,-5],['*',-1,'*']], [[3,2,-5],[0,0,0]],
  [[3,3,-6],['*',-1,-1]], [[1,4,-5],[0,0,0]],
  [[0,6,-6],['*','*','*']], [[-1,6,-5],[0,0,0]],
  [[-1,5,-4],[-1,'*','*']], [[-1,4,-3],[0,0,0]],
  [[0,3,-3],[1,'*',-1]], [[-1,2,-1],[0,0,0]]
].map(([point,values])=>Object.freeze({point:Object.freeze(point),values:Object.freeze(values)})));

// Every newly excluded Hat pair (43 for more, 47 for alternate) is independently
// certified impossible by exhaustive integer-capacity forced/dead-point checks.
// Thus these additions preserve ALL infinite Hat tilings admitted by the base
// marking. The base marking itself, and full mixed compatibility, remain
// provisional. Combining the patterns or extending two steps rejects known
// H7/H8 patches. Also checked on all 9 level-3 Hat/Turtle incursion patterns.
export const HAT_EXTENSION_MAXIMUM = 1;
export const HAT_EXTENSION_PATTERNS = Object.freeze({
  more:Object.freeze([
    Object.freeze({point:Object.freeze([2,2,-4]),component:2,value:-1}),
    Object.freeze({point:Object.freeze([2,2,-4]),component:0,value:1}),
    Object.freeze({point:Object.freeze([-2,4,-2]),component:0,value:1})
  ]),
  alternate:Object.freeze([
    Object.freeze({point:Object.freeze([2,5,-7]),component:1,value:-1})
  ])
});

export function normalizedHatExtent(value){
  const n=Number.parseInt(value,10);
  return Number.isFinite(n)?Math.max(0,Math.min(HAT_EXTENSION_MAXIMUM,n)):0;
}

export function provisionalHatSupport({extent=0,pattern='more'}={}){
  const base=PROVISIONAL_HAT_POINTS.flatMap(({point,values})=>values.flatMap((value,component)=>value==='*'?[]:[{tile:'hat',point:[...point],component,value}]));
  if(normalizedHatExtent(extent))for(const entry of HAT_EXTENSION_PATTERNS[pattern]??HAT_EXTENSION_PATTERNS.more)base.push({tile:'hat',point:[...entry.point],component:entry.component,value:entry.value});
  return base;
}

export function createProvisionalHatMarking(options={}){
  return new SparseA2Marking(provisionalHatSupport(options),{label:'Provisional Hat candidate 26',valueAction:'signed-permutation'});
}
