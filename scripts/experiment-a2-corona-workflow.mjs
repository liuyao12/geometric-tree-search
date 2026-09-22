#!/usr/bin/env node
import fs from 'node:fs';
import {pathToFileURL} from 'node:url';
import {A2_TILE_LOOPS,tileOrientations,SparseA2Marking,a2Transform} from '../assets/a2-tiling-engine.js';
import {createConnectionLearner,parity} from '../assets/tile-connection-learning.js';
import {reduceMarking} from '../assets/marking-reduction.js';
import {enumerateCoronas,verifyCoronaPatch,onIndex3} from './experiment-a2-corona-consensus.mjs';

export function workflowModel(tile,support=[]){
 const oriented=tileOrientations(tile,A2_TILE_LOOPS[tile]),marking=new SparseA2Marking(support);
 return {capacity:12,allowReflections:true,tile,rank:3,lattice:'index3',placementDomain:{kind:'a2_slab',index3:true},required:[],baseSupport:support,oriented,
  orientations:oriented.map((o,oi)=>({type:0,index:oi,cells:[...o.occupancy.values()].filter(c=>onIndex3(c.point)).map(c=>({pos:c.point,weight:c.weight})),marks:[...marking.entries({tile,orientation:o,translation:[0,0,0],id:`${tile}:${oi}:0`})].map(([k,value])=>{const [p,c]=k.split('|');return {pos:p.split(',').map(Number),component:+c,value};})}))};
}
export const placementKey=p=>`${p.oi}:${p.translation}`;
export function learningProblem(tile,catalog){
 if(!catalog.complete||!catalog.solutions)throw Error('Learning needs a complete nonempty unmarked catalogue');
 const learner=createConnectionLearner(tile,{lattice:'turtle-sublattice'}),model=workflowModel(tile),spec=p=>({tile,orientation:p.oi,translation:p.translation});
 // Every allowed prototype point lies in the t-support footprint of EVERY
 // original one-corona, and within one lattice step of the prototype.
 let footprint=null;
 for(const patch of catalog.patches){const covered=new Set(patch.flatMap(p=>model.orientations[p.oi].cells.map(c=>c.pos.map((v,i)=>v+p.translation[i]).join())));if(footprint===null)footprint=covered;else for(const k of footprint)if(!covered.has(k))footprint.delete(k);}
 const domain=learner.pointDomain(tile,1).filter(p=>footprint.has(p.join())).flatMap(point=>[0,1,2].map(component=>({tile,point,component})));
 function contacts(patch){const field=new Map(),pairs=[];for(const p of patch){const sym=model.oriented[p.oi].symmetry,sign=parity(sym.permutation);domain.forEach((e,i)=>{const k=`${a2Transform(e.point,sym).map((v,j)=>v+p.translation[j])}|${sym.permutation.indexOf(e.component)}`;if(!field.has(k))field.set(k,[]);for(const old of field.get(k))pairs.push([i,old.i,sign*old.sign]);field.get(k).push({i,sign});});}return pairs;}
 const equalityMap=new Map();for(const patch of catalog.patches)for(let [a,b,s]of contacts(patch)){if(a>b)[a,b]=[b,a];equalityMap.set(`${a}:${b}:${s}`,[a,b,s]);}
 const positive=new Set(catalog.patches.flatMap(p=>p.slice(1).map(placementKey)));
 const pairs=learner.connections().map(p=>({patch:[{oi:0,translation:[0,0,0]},{oi:p.attachment.orientation,translation:p.attachment.translation}],positive:positive.has(`${p.attachment.orientation}:${p.attachment.translation}`)}));
 for(const pair of pairs)pair.contacts=contacts(pair.patch);
 return {tile,domain,equalities:[...equalityMap.values()],pairs,positives:positive.size,negatives:pairs.length-positive.size,catalog,learner,spec};
}
export function fitSupport(problem,active){
 const n=problem.domain.length,parent=Array.from({length:n},(_,i)=>i),sign=Array(n).fill(1),zero=Array(n).fill(false);
 const find=i=>{if(parent[i]!==i){const [r,s]=find(parent[i]);sign[i]*=s;parent[i]=r;}return [parent[i],sign[i]];};
 for(const [i,j,s]of problem.equalities){if(!active[i]||!active[j])continue;const[a,x]=find(i),[b,y]=find(j);if(a===b){if(x!==s*y)zero[a]=true;}else{parent[b]=a;sign[b]=s*x*y;zero[a]||=zero[b];}}
 const labels=new Map(),values=Array(n).fill(null);for(let i=0;i<n;i++)if(active[i]){const[r,s]=find(i);if(!labels.has(r))labels.set(r,labels.size+1);values[i]=zero[r]?0:s*labels.get(r);}
 const decisions=problem.pairs.map(p=>p.contacts.some(([i,j,s])=>active[i]&&active[j]&&values[i]!==s*values[j]));
 if(problem.pairs.some((p,i)=>p.positive&&decisions[i]))throw Error('Synthesis rejected a positive pair');
 return {active:[...active],values,support:problem.domain.flatMap((e,i)=>active[i]?[{...e,value:values[i]}]:[]),blocked:decisions.filter(Boolean).length,signature:decisions.map(Number).join('')};
}
export function learnFamily(problem,{starts=24,seed=9173}={}){
 let state=seed>>>0;const random=()=>((state=(Math.imul(state,1664525)+1013904223)>>>0)/4294967296),n=problem.domain.length;
 const candidates=[],seen=new Set();let fits=0;
 const fit=a=>{fits++;return fitSupport(problem,a);};
 const save=m=>{if(!seen.has(m.signature)){seen.add(m.signature);candidates.push(m);}};
 const dense=fit(Array(n).fill(true));save(dense);
 // Coordinate search is bounded, not complete SAT/model enumeration. Refit
 // signed equalities after EVERY support change; never erase after unioning.
 for(let start=0;start<starts;start++){
  let current=fit(Array.from({length:n},()=>start===0||random()<[.3,.5,.7][start%3]));
  for(let round=0;round<6;round++){
   let best=current;const order=Array.from({length:n},(_,i)=>i);for(let j=n-1;j>0;j--){const k=Math.floor(random()*(j+1));[order[j],order[k]]=[order[k],order[j]];}
   for(const i of order){const a=[...current.active];a[i]=!a[i];const next=fit(a);if(next.blocked>best.blocked||(next.blocked===best.blocked&&next.support.length<best.support.length))best=next;}
   if(best===current)break;current=best;
  }
  save(current);
 }
 candidates.sort((a,b)=>b.blocked-a.blocked||a.support.length-b.support.length);
 return {dense,candidates, fits,seed,starts};
}
export function compactSupport(tile,support){return reduceMarking({tile,tiles:[tile],allowReflections:true,lattice:'turtle-sublattice',support}).reducedSupport;}
export function summary(r){const {support,patches,inputSupport,compactSupport,priorAttempts,...s}=r;return {...s,points:new Set(support.map(e=>e.point.join())).size};}

if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 const args=Object.fromEntries(process.argv.slice(2).map(a=>a.replace(/^--/,'').split('='))),tile=args.tile??'turtle',out=args.out??'/tmp/a2-corona-workflow';fs.mkdirSync(out,{recursive:true});
 const budget=+(args.ms??60000),started=performance.now();
 if(args.retry){
  const [i,radius]=args.retry.split(':').map(Number),file=`${out}/${tile}-m${i}-c${radius}.json`,previous=JSON.parse(fs.readFileSync(file));
  if(previous.complete)throw Error('Retry is only for an incomplete stage');
  const model=workflowModel(tile,previous.inputSupport),r=enumerateCoronas(model,{radius,timeMs:budget,nodeLimit:1000000,solutionLimit:100000,onProgress:s=>console.log(JSON.stringify({tile,model:i,progress:s}))});
  for(const patch of r.patches)if(!verifyCoronaPatch(model,patch,radius).ok)throw Error('Retry corona replay failed');
  const compact=r.complete&&r.solutions?compactSupport(tile,r.support):null,priorAttempts=[...(previous.priorAttempts??[]),summary(previous)];
  fs.writeFileSync(file,JSON.stringify({...r,inputSupport:previous.inputSupport,compactSupport:compact,priorAttempts}));
  const workflowFile=`${out}/${tile}-workflow.json`,workflow=JSON.parse(fs.readFileSync(workflowFile)),stage={...summary(r),compactValues:compact?.length??null,compactPoints:compact?new Set(compact.map(e=>e.point.join())).size:null,priorAttempts};
  workflow.results[i].stages=workflow.results[i].stages.map(s=>s.radius===radius?stage:s);workflow.elapsedMs+=performance.now()-started;
  fs.writeFileSync(workflowFile,JSON.stringify(workflow,null,2));console.log(JSON.stringify(stage));process.exit(0);
 }
 const catalog=enumerateCoronas(workflowModel(tile),{radius:1,timeMs:budget,nodeLimit:1000000,solutionLimit:100000});
 for(const patch of catalog.patches)if(!verifyCoronaPatch(workflowModel(tile),patch,1).ok)throw Error('Unmarked corona replay failed');
 fs.writeFileSync(`${out}/${tile}-unmarked-c1.json`,JSON.stringify(catalog));
 const problem=learningProblem(tile,catalog),fitStarted=performance.now(),family=learnFamily(problem,{starts:+(args.starts??32)}),fitMs=performance.now()-fitStarted;
 const models=family.candidates.slice(0,+(args.family??3));
 console.log(JSON.stringify({tile,catalog:summary(catalog),domain:problem.domain.length,equalities:problem.equalities.length,positive:problem.positives,negative:problem.negatives,fitMs,fits:family.fits,distinct:family.candidates.length,denseBlocked:family.dense.blocked,models:models.map(m=>({values:m.support.length,blocked:m.blocked}))}));
 fs.writeFileSync(`${out}/${tile}-family.json`,JSON.stringify({tile,catalog:summary(catalog),domain:problem.domain.length,positive:problem.positives,negative:problem.negatives,fitMs,fits:family.fits,distinct:family.candidates.length,denseBlocked:family.dense.blocked,models}));
 if(args.phase==='learn')process.exit(0);
 const results=[];
 for(const [i,m]of models.entries()){
  // Independent whole-corona marking replay; the learner fits entire patches,
  // including boundary-to-boundary and marking-only overlaps.
  for(const patch of catalog.patches)if(!problem.learner.verifyPatch(patch.map(problem.spec),m.support).compatible)throw Error('Positive corona rejected');
  let support=compactSupport(tile,m.support);const initial=support,stages=[];
  for(const radius of [1,2,3]){
   const input=support,model=workflowModel(tile,input),r=enumerateCoronas(model,{radius,timeMs:budget,nodeLimit:1000000,solutionLimit:100000,onProgress:s=>console.log(JSON.stringify({tile,model:i,progress:s}))});
   for(const patch of r.patches)if(!verifyCoronaPatch(model,patch,radius).ok)throw Error('Marked corona replay failed');
   let compact=null;if(r.complete&&r.solutions)compact=compactSupport(tile,r.support);
   const stage={...summary(r),compactValues:compact?.length??null,compactPoints:compact?new Set(compact.map(e=>e.point.join())).size:null};stages.push(stage);
   fs.writeFileSync(`${out}/${tile}-m${i}-c${radius}.json`,JSON.stringify({...r,inputSupport:input,compactSupport:compact}));console.log(JSON.stringify({tile,model:i,stage}));
   if(!compact)break;support=compact;
  }
  results.push({id:i,initialValues:initial.length,initialPoints:new Set(initial.map(e=>e.point.join())).size,blocked:m.blocked,stages});
 }
 fs.writeFileSync(`${out}/${tile}-workflow.json`,JSON.stringify({tile,catalog:summary(catalog),domain:problem.domain.length,positive:problem.positives,negative:problem.negatives,fitMs,fits:family.fits,distinct:family.candidates.length,denseBlocked:family.dense.blocked,results,elapsedMs:performance.now()-started},null,2));
}
