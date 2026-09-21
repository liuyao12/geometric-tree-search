// Experimental finite feasibility test. No known-marking data or browser changes.
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {mkdirSync,mkdtempSync,writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {resolve,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createCoronaLearner,parity} from '../assets/tile-corona-learning.js';
import {a2Add,a2Transform} from '../assets/a2-tiling-engine.js';
globalThis.requestAnimationFrame=cb=>setImmediate(cb);
const root=fileURLToPath(new URL('../',import.meta.url)),out=resolve(process.argv[2]??mkdtempSync(resolve(tmpdir(),'gcts-hat-direction-')));
if((out+sep).startsWith(root))throw new Error('Keep generated markings outside the repository');
mkdirSync(out,{recursive:true});
for(const lattice of ['A2','turtle-sublattice']){
 const learner=createCoronaLearner('hat',{lattice}),report=await learner.collect();assert.equal(report.counts.unresolved,0);
 const support=learner.pointDomain('hat',2).flatMap(point=>[0,1,2].map(component=>({tile:'hat',point,component})));
 const lineKeys=new Map(),lines=support.map(e=>{const [j,k]=[0,1,2].filter(i=>i!==e.component),key=`${e.component}:${e.point[j]-e.point[k]}`;if(!lineKeys.has(key))lineKeys.set(key,lineKeys.size);return lineKeys.get(key);});
 const rows=report.connections.map(row=>{const contacts=new Map(),pairs=[];for(const spec of [row.root,row.attachment]){const sym=learner.materialize(spec).orientation.symmetry,s=parity(sym.permutation);support.forEach((e,i)=>{const at=`${a2Add(a2Transform(e.point,sym),spec.translation)}|${sym.permutation.indexOf(e.component)}`,old=contacts.get(at);if(old)pairs.push([i,old.i,s*old.sign]);else contacts.set(at,{i,sign:s});});}return{status:row.status,pairs};});
 const answer=JSON.parse(execFileSync(process.env.PYTHON??'python3',[fileURLToPath(new URL('./solve-directional-components.py',import.meta.url))],{input:JSON.stringify({support,lines,lineCount:lineKeys.size,rows}),encoding:'utf8',timeout:30000}));
 const result={lattice,halo:2,palette:[-1,0,1],...answer};
 if(answer.result==='sat'){
  // Replay geometry/transforms independently of the solver's contact indices.
  const lineValues=new Map();for(const e of answer.support){assert.ok([-1,0,1].includes(e.value));const [j,k]=[0,1,2].filter(i=>i!==e.component),key=`${e.component}:${e.point[j]-e.point[k]}`;if(lineValues.has(key))assert.equal(lineValues.get(key),e.value);lineValues.set(key,e.value);}
  for(const row of report.connections)assert.equal(learner.verifyPatch([row.root,row.attachment],answer.support).compatible,row.status==='valid');
  result.positivePassed=report.counts.valid;result.negativeBlocked=report.counts.invalid;
  const growth=await learner.grow({support:answer.support,target:24,budget:5000,audit:true});assert.ok(learner.verifyPatch(growth.placements,answer.support).compatible);
  result.growth={result:growth.result,tiles: growth.placements.length,nodes:growth.nodes};
 }
 writeFileSync(resolve(out,`hat-directional-${lattice}.json`),JSON.stringify(result,null,2));
 console.log({...result,support:undefined,output:out});
}
