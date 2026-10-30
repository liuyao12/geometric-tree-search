import {SparseA2Marking} from './a2-tiling-engine.js?v=20260921-viable-corona';

// Explicit comparison control requested for display, not a cold-trained model.
// Candidate 26: finite-csp boundary screen, 2026-10-30. All omitted components
// are *, including every interior point. Numeric zero remains assigned.
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

export function provisionalHatSupport(){
  return PROVISIONAL_HAT_POINTS.flatMap(({point,values})=>values.flatMap((value,component)=>value==='*'?[]:[{tile:'hat',point:[...point],component,value}]));
}

export function createProvisionalHatMarking(){
  return new SparseA2Marking(provisionalHatSupport(),{label:'Provisional Hat candidate 26',valueAction:'signed-permutation'});
}
