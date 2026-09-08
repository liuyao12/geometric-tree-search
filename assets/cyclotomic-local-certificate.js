import {latticeKey,canonical,cycloAdd} from './cyclotomic-five.js?v=20260908-speed';
const sub=(a,b)=>cycloAdd(a,{...canonical(b),coeff:canonical(b).coeff.map(n=>-n)});
// Exhaustive finite completion of ONE prescribed point. Other frontier points
// are deliberately relaxed. Thus failure is sound; success proves only this
// local relaxation, not extendibility of the patch. A cap is inconclusive.
export function pointCompletion(problem,tiles,point,{nodeLimit=1000}={}){
 const key=latticeKey(point),weight=t=>t.weights[t.vertices.indexOf(key)]||0;
 const total=tiles.reduce((s,t)=>s+weight(t),0),target=problem.fullWeight;
 if(!(total>0&&total<target))return{status:'not-applicable',nodes:0};
 const candidates=problem.movesAt(point).filter(t=>weight(t)>0&&weight(t)+total<=target&&tiles.every(a=>problem.pairAllowed(a,t)));
 let nodes=0,stopped=false,solution=null;
 function dfs(sum,start,chosen){
  if(sum===target){solution=chosen.slice();return true;}
  for(let i=start;i<candidates.length;i++){
   if(nodeLimit&&nodes>=nodeLimit){stopped=true;return false;}
   const t=candidates[i],w=weight(t);if(sum+w>target||!chosen.every(a=>problem.pairAllowed(a,t)))continue;
   nodes++;chosen.push(t);if(dfs(sum+w,i+1,chosen))return true;chosen.pop();if(stopped)return false;
  }
  return false;
 }
 dfs(total,0,[]);return{status:solution?'fillable':stopped?'inconclusive':'impossible',nodes,solution};
}
export function createLocalPairTeacher(problem,{nodeLimit=256}={}){
 const cache=new Map(),stats={calls:0,nodes:0,hits:0,inconclusive:0,proofs:0};
 return{learn(point,tiles,marking){
  const key=latticeKey(point),near=tiles.filter(t=>t.vertices.includes(key));
  for(let i=near.length-1;i>=0;i--)for(let j=0;j<i;j++){
   const a=near[i],b=near[j],cacheKey=a.type+'|'+b.type+'|'+latticeKey(sub(b.origin,a.origin))+'|'+latticeKey(sub(point,a.origin));
   let result=cache.get(cacheKey);if(result)stats.hits++;else{stats.calls++;const checked=pointCompletion(problem,[a,b],point,{nodeLimit});result={status:checked.status,nodes:checked.nodes};stats.nodes+=result.nodes;stats.inconclusive+=+(result.status==='inconclusive');cache.set(cacheKey,result);}
   if(result.status==='impossible'&&marking.learnPair(a,b,point,'point-closure')){stats.proofs++;return true;}
  }
  return false;
 },snapshot:()=>({...stats,cached:cache.size})};
}
