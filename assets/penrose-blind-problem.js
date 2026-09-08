import {num,add} from './penrose-polygon.js';
import {arrowStates} from './penrose-arrows.js';
import {makeCyclotomicProblem} from './cyclotomic-tile-catalog.js';
// Standalone shape/optional-arrow input. This fixture does not import or query
// Ammann templates, the live marked variant catalog, or a reference tiling.
export function blindPenroseProblem({arrows=true,kinds=['thick','thin']}={}){
 const templates=[];
 for(const [kind,w,z]of[['thick',2,{coeff:[0,1,0,0],denominator:1}],['thin',4,{coeff:[0,0,1,0],denominator:1}]]){
  if(!kinds.includes(kind))continue;
  const tile={kind,exactPoints:[num(0),num(1),add(num(1),z),z],weights:[w,5-w,w,5-w]};
  if(arrows)for(const state of arrowStates(tile))templates.push({...tile,labels:state.arrows.map(a=>({code:String(a.type),from:a.from,to:a.to}))});
  else templates.push(tile);
 }
 return makeCyclotomicProblem(templates,{fullWeight:10});
}
