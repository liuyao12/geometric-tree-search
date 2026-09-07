import assert from 'node:assert/strict';
import {createMixedGrowth} from '../assets/penrose-mixed-growth.js';
for(const useMarkings of [false,true]){
 const search=createMixedGrowth({tileKinds:['thick','thin'],useMarkings,extent:2,targetCount:18,nodeLimit:200});
 let additions=0,removals=0;const stack=[];
 for(let n=0;n<2000;n++){
  const before=search.inspectGraph();const r=search.next();if(r.done)break;
  if(r.value.type==='try'){
   const points=before,minimum=Math.min(...points.map(p=>p.candidates.length));
   assert(minimum>0,'must detect every dead point before branching');
   assert.equal(r.value.forced,minimum===1);
   assert.equal(r.value.branchCount,minimum);
   stack.push(before);
  }
  if(r.value.type==='add'){
   additions++;
   if(additions<=4)assert.deepEqual(search.inspectGraph(),search.rebuildGraphForAudit(),'incremental graph differs from exhaustive fresh enumeration');
  }
  if(r.value.type==='remove'){
   removals++;assert.deepEqual(search.inspectGraph(),stack.pop(),'rollback did not restore every incidence');
   if(removals<=2)assert.deepEqual(search.inspectGraph(),search.rebuildGraphForAudit());
  }
 }
 const s=search.snapshot();assert(s.stats.forcedMoves>0);assert.equal(s.graph.fullBuilds,1);
 assert.equal(s.stats[useMarkings?'edgeChecks':'markingChecks'],0);
 assert.equal(s.graph.updates,s.stats.proposals);assert.equal(s.graph.rollbacks,s.stats.backtracks);
 console.log('ok:',useMarkings?'marked':'arrows',s.status,s.tiles.length,'tiles',s.stats.forcedMoves,'forced',s.stats.backtracks,'rollbacks');
}
// An impossible permitted subset exercises actual DFS restoration, including
// forced chains; a finite patch target is deliberately not supplied.
const s=createMixedGrowth({tileKinds:['thin'],useMarkings:true,extent:2,targetCount:null,nodeLimit:100});
const parents=[];let count=0;while(true){const before=s.inspectGraph(),r=s.next();if(r.done)break;if(r.value.type==='try')parents.push(before);if(r.value.type==='remove'){assert.deepEqual(s.inspectGraph(),parents.pop());count++;}}
assert.equal(s.snapshot().status,'frontier exhausted');assert(s.snapshot().graph.deadPoints>0);assert.equal(s.snapshot().graph.fullBuilds,1);console.log('ok: impossible subset detects dead points');
