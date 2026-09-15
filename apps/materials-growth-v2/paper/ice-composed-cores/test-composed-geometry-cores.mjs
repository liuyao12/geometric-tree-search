import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {deriveGeometryCore} from './composed-geometry-core.mjs';
import {verifiedGeometryCoreClass} from './verified-geometry-cores.mjs';
const {PointSearch}=await import(pathToFileURL(process.argv[2]));
let seed=52743,proofs=0,composed=0,solutionsChecked=0;const random=n=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return(seed>>>16)%n;};
for(let trial=0;trial<100;trial++){
 const required=['p','q','r','s'],capacity=1+random(2),candidates=[];
 for(let i=0;i<7;i++){let t=required.filter(()=>random(2)).map(point=>({point,value:1}));if(!t.length)t=[{point:required[random(4)],value:1}];candidates.push({id:`g${i}`,base:`g${i}`,t,m:[]});}
 const model={capacity,required,candidates,complete:true},states=[];
 for(let mask=0;mask<128;mask++){
  const rows=candidates.filter((_,i)=>mask&(1<<i)),totals=required.map(p=>rows.reduce((a,c)=>a+c.t.filter(t=>t.point===p).length,0));
  if(totals.every(t=>t<=capacity))states.push({owners:rows.map(c=>c.base),complete:totals.every(t=>t===capacity)});
 }
 const solutions=states.filter(s=>s.complete);if(!solutions.length)continue;
 const cores=[];
 for(const state of states)for(const p of required){
  if(cores.length>=8)break;
  const core=deriveGeometryCore(model,state.owners,p,cores);if(!core)continue;
  verifiedGeometryCoreClass(PointSearch,model,[...cores,core]);
  for(const solution of solutions){assert(!core.owners.every(g=>solution.owners.includes(g)));solutionsChecked++;}
  if(core.dependencies.length){composed++;assert.throws(()=>verifiedGeometryCoreClass(PointSearch,model,[core]),/Unverified/);}
  cores.push(core);proofs++;
 }
}
assert(proofs>0&&composed>0&&solutionsChecked>0);
console.log(JSON.stringify({proofs,composed,solutionsChecked,status:'exhaustive solution preservation and missing-ancestor rejection passed'}));
