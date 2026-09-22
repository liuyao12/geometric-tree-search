#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {FixedA2Marking,A2_TILE_LOOPS,tileOrientations} from '../assets/a2-tiling-engine.js';
import {GrowthGraph,verifyGrowth} from '../apps/3d-lattice-tiler/growth-search.js';
export const onIndex3=p=>(p[0]-p[1])%3===0&&(p[1]-p[2])%3===0;
export function pointModel({tile='turtle',rank=3,lattice='index3',extent=1,support=null}={}){
 const filter=lattice==='index3'?onIndex3:()=>true;
 const marking=new FixedA2Marking(extent,{rank,tiles:[tile],pointFilter:filter});if(support)marking.support=support;
 const oriented=tileOrientations(tile,A2_TILE_LOOPS[tile]);
 const orientations=oriented.map((o,oi)=>{const entries=marking.entries({tile,orientation:o,translation:[0,0,0],id:`${tile}:${oi}:0`});return {type:0,index:oi,cells:[...o.occupancy.values()].filter(c=>filter(c.point)).map(c=>({pos:c.point,weight:c.weight})),marks:[...entries].map(([k,value])=>{const [p,c]=k.split('|');return {pos:p.split(',').map(Number),component:+c,value};}),vertices:o.loop,faces:[o.loop.map((_,i)=>i)]};});
 return {capacity:12,allowReflections:true,orientations,required:[],placementDomain:{kind:'a2_slab',index3:lattice==='index3'},tile,rank,lattice,oriented,baseSupport:marking.support};
}
export function coronaCore(model,placements,radius){
 const support=placements.map(p=>model.orientations[p.oi].cells.map(c=>c.pos.map((v,i)=>v+p.translation[i]).join(','))),owners=new Map();
 support.forEach((keys,i)=>{for(const k of keys){if(!owners.has(k))owners.set(k,[]);owners.get(k).push(i);}});
 const distance=placements.map(()=>Infinity),queue=[0];distance[0]=0;
 for(let n=0;n<queue.length;n++){const i=queue[n];for(const k of support[i])for(const j of owners.get(k))if(distance[j]===Infinity){distance[j]=distance[i]+1;queue.push(j);}}
 const core=new Set();support.forEach((keys,i)=>{if(distance[i]<radius)for(const k of keys)core.add(k);});
 return {core,distance};
}
export function enumerateCoronas(model,{radius=1,nodeLimit=100000,timeMs=30000,solutionLimit=10000,retain=true,onProgress=()=>{}}={}){
 const started=performance.now(),root={oi:0,translation:[0,0,0]},graph=new GrowthGraph(model,{fixed:[root],candidateLimit:300000,dependencyLimit:5000000});
 let nodes=0,dead=0,duplicates=0,reason=null,consensus=null,solutions=0,lastProgress=0;const visited=new Set(),patches=[];
 const stopped=()=>{if(nodes>=nodeLimit)reason='node limit';else if(performance.now()-started>=timeMs)reason='time limit';else if(solutions>=solutionLimit)reason='solution limit';return !!reason;};
 function visit(){
  if(stopped())return;
  const key=graph.selected.map(c=>c.id).sort().join(';');if(visited.has(key)){duplicates++;return;}visited.add(key);
  const all=graph.schedule();if(all.kind==='dead'){dead++;return;}
  const placements=graph.descriptors(),{core}=coronaCore(model,placements,radius),obligations=[...core].filter(k=>(graph.totals.get(k)??0)<model.capacity).map(k=>graph.points.get(k));
  if(!obligations.length){
   const field=new Map([...graph.section].map(([k,v])=>[k,JSON.parse(v.value)]));
   if(consensus===null)consensus=field;else for(const [k,v] of consensus)if(!field.has(k)||field.get(k)!==v)consensus.delete(k);
   if(retain)patches.push(placements);solutions++;return;
  }
  const generation=p=>Math.min(...graph.generations.get(p.k).keys());
  obligations.sort((a,b)=>Number(b.degree===1)-Number(a.degree===1)||generation(a)-generation(b)||a.degree-b.degree||(a.k<b.k?-1:1));
  for(const c of obligations[0].incident){if(!c.valid)continue;if(stopped())return;nodes++;const undo=graph.apply(c);visit();graph.rollback(undo);if(reason)return;}
  if(performance.now()-lastProgress>2000){lastProgress=performance.now();onProgress({radius,nodes,solutions,commonValues:consensus?.size??0});}
 }
 try{graph.apply(root,{root:true});visit();}catch(e){if(e.kind!=='resource_limit')throw e;reason=e.message;}
 const base=new Map(model.orientations[0].marks.map(m=>[`${m.pos}|${m.component}`,m.value]));
 if(consensus)for(const [k,v] of base)if(consensus.get(k)!==v)throw Error('Consensus lost a root marking');
 const additions=[...(consensus??[])].filter(([k])=>!base.has(k));
 const support=[...(consensus??[])].map(([k,value])=>{const [p,c]=k.split('|');return {tile:model.tile,point:p.split(',').map(Number),component:+c,value};});
 return {tile:model.tile,rank:model.rank,lattice:model.lattice,radius,complete:!reason,reason,nodes,dead,duplicates,states:visited.size,solutions,elapsedMs:performance.now()-started,baseValues:base.size,commonValues:consensus?.size??0,addedValues:additions.length,addedPoints:new Set(additions.map(([k])=>k.split('|')[0])).size,support,patches};
}
export function verifyCoronaPatch(model,patch,radius){
 const check=verifyGrowth(model,patch),{core,distance}=coronaCore(model,patch,radius),totals=new Map();
 for(const p of patch)for(const c of model.orientations[p.oi].cells){const k=c.pos.map((v,i)=>v+p.translation[i]).join();totals.set(k,(totals.get(k)??0)+c.weight);}
 return {...check,ok:check.ok&&distance.every(d=>d<=radius)&&[...core].every(k=>totals.get(k)===model.capacity),corePoints:core.size};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 const args=Object.fromEntries(process.argv.slice(2).map(s=>s.replace(/^--/,'').split('=')));
 const tile=args.tile??'turtle',rank=+(args.rank??(tile==='turtle'?3:1)),lattice=args.lattice??'index3',radius=+(args.radius??1),out=args.out??'/tmp/a2-corona-consensus';
 fs.mkdirSync(out,{recursive:true});const model=pointModel({tile,rank,lattice});
 const result=enumerateCoronas(model,{radius,nodeLimit:+(args.nodes??100000),timeMs:+(args.ms??30000),solutionLimit:+(args.solutions??10000),onProgress:e=>console.log(JSON.stringify({progress:e}))});
 fs.writeFileSync(path.join(out,`${tile}-r${rank}-${lattice}-c${radius}.json`),JSON.stringify(result));const {support,patches,...summary}=result;console.log(JSON.stringify(summary));
}
