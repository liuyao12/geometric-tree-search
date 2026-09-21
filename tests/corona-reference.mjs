import {a2Add,a2Sub} from '../assets/a2-tiling-engine.js';
// Independent integer-capacity enumerator. It does not use the engine's graph,
// candidate caches, branch exclusions or the learner's frontier verifier.
function pointProblem(learner,placements){
 const sums=new Map(),used=new Set(placements.map(p=>`${p.tile}:${p.orientation}:${p.translation}`)),cache=new Map();
 for(const spec of placements)for(const e of learner.materialize(spec).orientation.occupancy.values()){const key=a2Add(e.point,spec.translation).join();sums.set(key,(sums.get(key)||0)+e.weight);}
 const candidates=point=>{
  const key=point.join();if(cache.has(key))return cache.get(key);
  const pool=new Map();
  for(const o of learner.orientations)for(const a of o.occupancy.values()){
   const shift=a2Sub(point,a.point),id=`${o.tile}:${o.index}:${shift}`;if(pool.has(id))continue;
   const entries=[...o.occupancy.values()].map(e=>({key:a2Add(e.point,shift).join(),value:e.weight}));
   pool.set(id,{id,entries});
  }
  const result=[...pool.values()];cache.set(key,result);return result;
 };
 const legal=p=>!used.has(p.id)&&p.entries.every(e=>(sums.get(e.key)||0)+e.value<=12);
 const frontier=()=>[...sums].filter(([,n])=>n>0&&n<12).map(([p])=>p.split(',').map(Number));
 return {sums,used,candidates,legal,frontier};
}
export function frontierReference(learner,placements){
 const problem=pointProblem(learner,placements),frontier=problem.frontier();
 return {frontierPoints:frontier.length,deadPoints:frontier.filter(p=>!problem.candidates(p).some(problem.legal))};
}
// Branch only on the finite core; outer points must have at least one candidate
// but are not recursively filled (which would be a stronger, different test).
export function reference(learner,pair){
 const {sums,used,candidates,legal,frontier}=pointProblem(learner,pair),core=learner.corePoints(pair);let nodes=0;
 function dfs(){
  if(++nodes>100000)throw new Error('Reference solver budget exhausted');
  if(frontier().some(p=>!candidates(p).some(legal)))return false;
  const open=core.filter(p=>(sums.get(p.join())||0)<12);if(!open.length)return true;
  const domains=open.map(p=>candidates(p).filter(legal)).sort((a,b)=>a.length-b.length);if(!domains[0].length)return false;
  for(const p of domains[0]){used.add(p.id);for(const e of p.entries)sums.set(e.key,(sums.get(e.key)||0)+e.value);if(dfs())return true;for(const e of p.entries)sums.set(e.key,sums.get(e.key)-e.value);used.delete(p.id);}return false;
 }
 return dfs();
}
