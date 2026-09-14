// Check representation-only decision equivalence on the stored material models.
// Count repeated placement sets as a diagnostic, not a sound memoization rule:
// different branch stacks can carry different remaining alternatives.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {linearFrontierClass} from './linear-frontier-decision.mjs';
const {PointSearch}=await import(pathToFileURL(process.argv[2]));
const hash=x=>createHash('sha256').update(x).digest('hex'),results=[];
for(const fold of [2,5])for(const marked of [false,true]){
 const raw=readFileSync(`${process.argv[3]}/${fold}-${marked}.json`),source=JSON.parse(raw),model=source.model;
 const a=new PointSearch(model),b=new (linearFrontierClass(PointSearch))(model);
 const root=JSON.stringify(a.semanticState()),seen=new Set(),trace=createHash('sha256');let repeated=0,branchVisits=0,steps=0;
 for(;steps<5000;steps++){
  const decision=a.decision();assert.deepEqual(b.decision(),decision);
  if(decision.kind==='branch'){
   branchVisits++;const key=hash(JSON.stringify([...a.placed.keys()].sort()));
   if(seen.has(key))repeated++;else seen.add(key);
  }
  const x=a.advance(),y=b.advance();assert.deepEqual(y,x);trace.update(JSON.stringify(x));
  assert.deepEqual(b.stats,a.stats);
  if(steps%100===0){assert.deepEqual(b.semanticState(),a.semanticState());a.auditGraph();b.auditGraph();}
  if(['complete','unknown','exhausted'].includes(x.kind)){steps++;break;}
 }
 assert.deepEqual(b.semanticState(),a.semanticState());
 a.undo(0);b.undo(0);assert.equal(JSON.stringify(a.semanticState()),root);assert.deepEqual(b.semanticState(),a.semanticState());
 const row={fold,marked,modelSourceHash:hash(raw),steps,branchVisits,repeatedPlacementSets:repeated,traceHash:trace.digest('hex'),lockstep:true,rootRollback:true};
 results.push(row);console.log(JSON.stringify(row));
}
writeFileSync(process.argv[4],JSON.stringify({kernelHash:hash(readFileSync(process.argv[2])),results,
 scope:'Fixed 5000-step prefixes of four hard boron models. Exact scheduler/advance/state agreement; repeated placement sets are not full-stack transpositions or pruning certificates.'},null,2),{flag:'wx'});
