import {a2Add,a2Sub} from '../assets/a2-tiling-engine.js';
// Independent finite-capacity DFS: pre-enumerate all candidates touching the
// core, then recompute every domain from integer sums at each recursive node.
export function reference(learner,pair){
 const core=learner.corePoints(pair),sums=new Map(),used=new Set(pair.map(p=>`${p.tile}:${p.orientation}:${p.translation}`)),pool=new Map();
 for(const spec of pair)for(const e of learner.materialize(spec).orientation.occupancy.values()){const key=a2Add(e.point,spec.translation).join();sums.set(key,(sums.get(key)||0)+e.weight);}
 for(const point of core)for(const o of learner.orientations)for(const a of o.occupancy.values()){
  const shift=a2Sub(point,a.point),id=`${o.tile}:${o.index}:${shift}`;if(pool.has(id)||used.has(id))continue;
  const entries=[...o.occupancy.values()].map(e=>({key:a2Add(e.point,shift).join(),value:e.weight}));if(entries.some(e=>(sums.get(e.key)||0)+e.value>12))continue;
  pool.set(id,{id,entries,keys:new Set(entries.map(e=>e.key))});
 }
 let nodes=0;
 function dfs(){
  if(++nodes>100000)throw new Error('Reference solver budget exhausted');
  const open=core.map(p=>p.join()).filter(p=>(sums.get(p)||0)<12);if(!open.length)return true;
  const legal=[...pool.values()].filter(p=>!used.has(p.id)&&p.entries.every(e=>(sums.get(e.key)||0)+e.value<=12));
  const domains=open.map(point=>legal.filter(p=>p.keys.has(point))).sort((a,b)=>a.length-b.length);if(!domains[0].length)return false;
  for(const p of domains[0]){used.add(p.id);for(const e of p.entries)sums.set(e.key,(sums.get(e.key)||0)+e.value);if(dfs())return true;for(const e of p.entries)sums.set(e.key,sums.get(e.key)-e.value);used.delete(p.id);}return false;
 }
 return dfs();
}
