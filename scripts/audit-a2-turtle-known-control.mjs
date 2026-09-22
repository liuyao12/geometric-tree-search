#!/usr/bin/env node
// Diagnostic only. The known marking is a control, never a learning seed.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {FixedA2Marking,SparseA2Marking} from '../assets/a2-tiling-engine.js';
import {createCoronaLearner} from '../assets/tile-corona-learning.js';
import {supportDomain,overlapContacts,probePair} from './experiment-a2-online-pairs.mjs';
import {onIndex3} from './experiment-a2-corona-consensus.mjs';
import {workflowModel} from './experiment-a2-corona-workflow.mjs';
import {verifyGrowth} from '../apps/3d-lattice-tiler/growth-search.js';
const dir=process.argv[2]??'/tmp/a2-online-control',input=process.argv[3]??'/tmp/a2-online-pairs/turtle-baseline-pair-s1.json';fs.mkdirSync(dir,{recursive:true});
const labels=JSON.parse(fs.readFileSync(input)),learner=createCoronaLearner('turtle',{lattice:'turtle-sublattice'}),known=new FixedA2Marking(1,{rank:3,tiles:['turtle'],pointFilter:onIndex3}),sparse=new SparseA2Marking(known.support),domain=supportDomain(learner,1),index=new Map(domain.map((e,i)=>[`${e.point}|${e.component}`,i]));
assert.equal(labels.counts.unresolved,0);assert.equal(labels.rows.length,learner.connections().length);
const values=domain.map(()=>null);for(const e of known.support){assert.ok(index.has(`${e.point}|${e.component}`));values[index.get(`${e.point}|${e.component}`)]=e.value;}
const model=workflowModel('turtle',known.support),counts={positivePass:0,positiveReject:0,negativePass:0,negativeReject:0,positiveCompleted:0,negativeRejectedBySearch:0},exceptions=[],constraints=[];
let witnessConflicts=0;
for(const row of labels.rows){
 const pair=[row.root,row.attachment];for(const p of pair){const materialized=learner.materialize(p);assert.deepEqual([...known.entries(materialized)],[...sparse.entries(materialized)]);}
 const contacts=overlapContacts(learner,domain,pair),direct=learner.verifyPatch(pair,known.support).compatible,encodedConflict=contacts.some(([i,j,s])=>values[i]!==null&&values[j]!==null&&values[i]!==s*values[j]);assert.equal(!encodedConflict,direct);
 const positive=row.status==='valid';constraints.push({positive,contacts});counts[`${positive?'positive':'negative'}${direct?'Pass':'Reject'}`]++;
 if(positive&&!learner.verifyPatch(row.placements,known.support).compatible)witnessConflicts++;
 if(direct){
  const check=verifyGrowth(model,pair.map(p=>({oi:p.orientation,translation:p.translation}))),search=await probePair(learner,row,{support:known.support,seed:1,nodes:100000,ms:10000});
  assert.equal(search.status,positive?'valid':'invalid');
  if(positive)counts.positiveCompleted++;else{counts.negativeRejectedBySearch++;exceptions.push({index:row.index+1,frontierDeadImmediately:!check.frontierViable,unmarkedNodes:row.oracle.nodes,markedNodes:search.nodes,markedBacktracks:search.backtracks,elapsedMs:search.elapsedMs,verified:true});}
 }
}
assert.deepEqual(counts,{positivePass:41,positiveReject:0,negativePass:13,negativeReject:193,positiveCompleted:41,negativeRejectedBySearch:13});
assert.ok(exceptions.every(e=>e.markedNodes<=2));
fs.writeFileSync(`${dir}/smt-control-input.json`,JSON.stringify({n:domain.length,values,constraints}));
const report={system:'Turtle / index-3 / reflections / known rank-3 extent 1',knownValues:known.support.length,domainValues:domain.length,representable:true,transformationMatchesLearned:true,counts,firstStrictConstraintExcludingKnown:exceptions[0].index,firstFoundPositiveWitnessesRejected:witnessConflicts,exceptions,summary:{directNegativeRejections:193,frontierDeadRejections:exceptions.filter(e=>e.frontierDeadImmediately).length,additionalSearchRejections:exceptions.filter(e=>!e.frontierDeadImmediately).length,unmarkedNodesOnExceptions:exceptions.reduce((s,e)=>s+e.unmarkedNodes,0),markedNodesOnExceptions:exceptions.reduce((s,e)=>s+e.markedNodes,0)}};
fs.writeFileSync(`${dir}/known-control-audit.json`,JSON.stringify(report,null,2));console.log(JSON.stringify(report));
