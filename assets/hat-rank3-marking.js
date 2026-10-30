import {SparseA2Marking} from './a2-tiling-engine.js?v=20260921-viable-corona';

// Official Hat rank-3 comparison rule, promoted from candidate 26.
// Internal stripe values stay fixed. Extent counts only extra lattice sites
// outside the positive-t Hat domain along the selected outward continuation.
// Extent 1 is exactly the previously certified extended rule. Extents 2 and 3
// are restricted experiments: they reject known Hat patches. Preservation of
// every unmarked Hat tiling by the underlying rule itself remains unproved.
export const HAT_RANK3_ID='hat-rank3';
export const HAT_RANK3_MAX_EXTENT=3;
export const HAT_RANK3_CERTIFIED_EXTENT=1;
export const HAT_RANK3_POINTS=Object.freeze([
  [[0,0,0],['*',-1,'*']], [[1,0,-1],[0,0,0]],
  [[1,1,-2],[-1,1,'*']], [[3,0,-3],[0,0,0]],
  [[4,1,-5],['*',-1,'*']], [[3,2,-5],[0,0,0]],
  [[3,3,-6],['*',-1,-1]], [[1,4,-5],[0,0,0]],
  [[0,6,-6],['*','*','*']], [[-1,6,-5],[0,0,0]],
  [[-1,5,-4],[-1,'*','*']], [[-1,4,-3],[0,0,0]],
  [[0,3,-3],[1,'*',-1]], [[-1,2,-1],[0,0,0]]
].map(([point,values])=>Object.freeze({point:Object.freeze(point),values:Object.freeze(values)})));

export const HAT_RANK3_PATTERNS=Object.freeze({
  more:Object.freeze({
    interior:Object.freeze([
      Object.freeze({point:Object.freeze([2,2,-4]),component:2,value:-1}),
      Object.freeze({point:Object.freeze([2,2,-4]),component:0,value:1})
    ]),
    boundary:Object.freeze([0,3,-3]),direction:Object.freeze([-2,1,1]),component:0,value:1
  }),
  alternate:Object.freeze({interior:Object.freeze([]),boundary:Object.freeze([3,3,-6]),direction:Object.freeze([-1,2,-1]),component:1,value:-1})
});

export function normalizeHatRank3Extent(value){
  const n=Number.parseInt(value,10);
  return Number.isFinite(n)?Math.max(0,Math.min(HAT_RANK3_MAX_EXTENT,n)):1;
}

export function hatRank3Support({extent=1,pattern='more'}={}){
  const selected=HAT_RANK3_PATTERNS[pattern]??HAT_RANK3_PATTERNS.more;
  const entries=HAT_RANK3_POINTS.flatMap(({point,values})=>values.flatMap((value,component)=>value==='*'?[]:[{tile:'hat',point:[...point],component,value}]));
  for(const entry of selected.interior)entries.push({tile:'hat',point:[...entry.point],component:entry.component,value:entry.value});
  for(let step=1;step<=normalizeHatRank3Extent(extent);step++)entries.push({tile:'hat',point:selected.boundary.map((v,i)=>v+step*selected.direction[i]),component:selected.component,value:selected.value});
  return entries;
}

export function createHatRank3Marking(options={}){
  const extent=normalizeHatRank3Extent(options.extent??1);
  return new SparseA2Marking(hatRank3Support({...options,extent}),{label:`Hat rank 3 · outside extent ${extent}`,valueAction:'signed-permutation',version:'hat-rank3-outside-v1'});
}
