import {blindPenroseProblem} from './penrose-blind-problem.js';
import {makeCyclotomicProblem} from './cyclotomic-tile-catalog.js?v=20260908-sets';
import {LOCAL_TEMPLATES} from './penrose-local-templates.js';
export const TILE_KINDS=['thick','thin','kite','dart','p5','p3','p2','diamond','boat','star'];
export const TILE_PRESETS={P3:['thick','thin'],P2:['kite','dart'],P1:['p5','p3','p2','diamond','boat','star'],all:TILE_KINDS};
export function selectedPenroseProblem(kinds=TILE_PRESETS.P3){
 if(!Array.isArray(kinds)||!kinds.length||kinds.some(k=>!TILE_KINDS.includes(k)))throw Error('Choose at least one tile');
 const selected=[...new Set(kinds)];
 if(selected.every(k=>k==='thick'||k==='thin'))return blindPenroseProblem({kinds:selected});
 // Use the same colored boundary-port convention on both sides of mixed edges.
 const templates=TILE_KINDS.filter(k=>selected.includes(k)).map(k=>LOCAL_TEMPLATES.find(t=>t.kind===k));
 return makeCyclotomicProblem(templates,{fullWeight:10});
}
