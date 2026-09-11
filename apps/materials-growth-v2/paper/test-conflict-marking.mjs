import assert from 'node:assert/strict';
import {writeFileSync} from 'node:fs';
import {compileConflictMarkings} from '../conflict-marking.mjs';
import {PointSearch,verify} from '../kernel.mjs';
const rows=[];
for(let seed=1;seed<=16;seed++){
  let rng=seed;const random=()=>((rng=(1664525*rng+1013904223)>>>0)/2**32);
  const candidates=Array.from({length:10},(_,i)=>({id:`c${i}`,t:[{point:`p${i%5}`,value:1}],m:i%3===0?[{point:'old-mark',channel:'0',lo:i%2,hi:i%2}]:[]}));
  const pairs=[];for(let i=0;i<10;i++)for(let j=0;j<i;j++)if(random()<.2)pairs.push([`c${i}`,`c${j}`]);
  const original=JSON.stringify(candidates),compiled=compileConflictMarkings(candidates,pairs);
  const grouped=compileConflictMarkings(candidates,pairs,{grouping:'star'});
  assert.equal(JSON.stringify(candidates),original);
  const required=Array.from({length:5},(_,i)=>`p${i}`),model={capacity:1,required,candidates};
  let legal=0,complete=0;
  for(let bits=0;bits<1024;bits++){
    const chosen=candidates.filter((_,i)=>bits&(1<<i)).map(c=>c.id),expected=verify(model,chosen);
    const conflict=pairs.some(([a,b])=>chosen.includes(a)&&chosen.includes(b));
    const actual=verify({...model,candidates:compiled.candidates},chosen);
    assert.equal(actual.legal,expected.legal&&!conflict);assert.equal(actual.complete,expected.complete&&!conflict);
    assert.equal(verify({...model,candidates:grouped.candidates},chosen).legal,actual.legal);
    legal+=actual.legal;complete+=actual.complete;
  }
  const solve=marked=>{
    const constraint=marked?null:(c,e)=>pairs.some(([a,b])=>(c.id===a&&e.placed.has(b))||(c.id===b&&e.placed.has(a)))?'pair-conflict':null;
    const e=new PointSearch({required,candidates:marked==='star'?grouped.candidates:marked?compiled.candidates:compiled.neutralCandidates,constraint});
    const trace=[];for(let i=0;i<10000;i++){
      const event=e.advance();trace.push([event.kind,event.id??null]);e.auditGraph();
      if(['complete','exhausted','unknown'].includes(event.kind))break;
    }
    const checkpoint=e.trail.length,before=JSON.stringify([...e.placed]);
    if(e.stack.length){e.undo(e.stack[0].checkpoint);e.auditGraph();}
    return {trace,selected:before,checkpoint,backtracks:e.stats.backtracks};
  };
  const a=solve(false),b=solve(true),star=solve('star');assert.deepEqual(a.trace,b.trace);assert.deepEqual(a.trace,star.trace);assert.equal(a.selected,b.selected);assert.equal(a.selected,star.selected);assert.equal(a.backtracks,b.backtracks);
  rows.push({seed,subsets:1024,edges:compiled.edges.length,legal,complete,traceEqual:true,backtracks:b.backtracks});
}
assert.throws(()=>compileConflictMarkings([{id:'x',t:[{point:'p',value:1}]}],[['x','x']]));
const reserved=compileConflictMarkings([{id:'a',t:[{point:'p',value:1}]},{id:'b',t:[{point:'q',value:1}]}],[['a','b']],{reservedPoints:['gcts-conflict-witness:0']});
assert.equal(reserved.edges[0].point,'gcts-conflict-witness:1');
const report={schema:'finite-conflict-marking-controls/1',scope:'16 deterministic finite CSP controls; not material replicates or a novelty/speedup claim.',subsets:16384,rows};
if(process.argv[2])writeFileSync(process.argv[2],JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report));
