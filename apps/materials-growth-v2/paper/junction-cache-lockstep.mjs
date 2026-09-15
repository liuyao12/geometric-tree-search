import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
import {junctionMarkingClass as Original} from './junction-marking-filter.mjs';
import {junctionMarkingClass as Cached} from './junction-marking-cached-filter.mjs';
import {branchExclusionClass} from './branch-local-exclusions.mjs';
import {linearFrontierClass} from './linear-frontier-decision.mjs';
const [compiledPath,junctionPath,kernel]=process.argv.slice(2);
const compiled=JSON.parse(readFileSync(compiledPath)),junctions=JSON.parse(readFileSync(junctionPath));
const {PointSearch}=await import(pathToFileURL(kernel));
for(const input of compiled.models.filter(x=>[2,5].includes(x.fold))){
 const model={capacity:input.capacity,required:input.required,candidates:input.candidates.map(c=>({...c,m:c.m.filter(x=>x.channel==='0')}))},nodes=junctions.folds[input.fold].nodes;
 const A=linearFrontierClass(branchExclusionClass(Original(PointSearch,nodes,model))),B=linearFrontierClass(branchExclusionClass(Cached(PointSearch,nodes,model))),a=new A(model),b=new B(model);
 const root=JSON.stringify(a.semanticState());let steps=0;
 for(;steps<600;steps++){
  assert.deepEqual(a.decision(),b.decision());const x=a.advance(),y=b.advance();assert.deepEqual(x,y);
  if(steps%100===0)assert.deepEqual(a.semanticState(),b.semanticState());
  if(['complete','exhausted'].includes(x.kind))break;
 }
 assert.deepEqual(a.semanticState(),b.semanticState());a.undo(0);b.undo(0);assert.equal(JSON.stringify(a.semanticState()),root);assert.equal(JSON.stringify(b.semanticState()),root);
 console.log(JSON.stringify({file:input.file,advances:steps,decisionsIdentical:true,checkedStatesIdentical:true,rootRollback:true}));
}
