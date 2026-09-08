import assert from 'node:assert/strict';
import {createDisplayCache} from '../apps/penrose-model-set/learning-display.js';
let state,previousTables,previousRevision=-1,modelMessages=0,frames=0,cache=createDisplayCache();
globalThis.self={postMessage(raw){
 const data=structuredClone(raw);assert(!data.error,data.error);frames++;
 if(data.learning){
  if(data.learning.tables){assert.notEqual(data.learning.revision,previousRevision);modelMessages++;previousTables=data.learning.tables;}
  else assert.equal(data.learning.revision,previousRevision);
  previousRevision=data.learning.revision;data.learning.tables=previousTables;
  const f=cache.frame(data.tiles,data.learning.tables),marked=f.points.filter(p=>p.marked);
  assert.equal(marked.length,data.memory.activeMarking.points);
  assert.equal(marked.reduce((n,p)=>n+[...p.values.values()].reduce((s,v)=>s+(v==='conflict'?2:1),0),0),data.memory.activeMarking.values);
  assert(data.tiles.every(t=>!t.labels&&!t.signatures&&!t.sourceTransform));
 }state=data;
}};
await import('../apps/penrose-model-set/learning-worker.js');
self.onmessage({data:{type:'init',mode:'learned',compact:true}});
while(!state.done&&state.pausedCorona!==3)self.onmessage({data:{type:'advance',targetCorona:3}});
assert.equal(state.pausedCorona,3);assert(frames>modelMessages,'unchanged models should not be retransmitted');
self.onmessage({data:{type:'init',mode:'known',compact:true}});
assert(state.tiles.every(t=>t.bars.length===5));assert(createDisplayCache().frame(state.tiles,undefined,true,true).tiles[0].bars.length===5);
console.log('ok: compact frames preserve all displayed point values, model revisions, and known bars;',frames,'frames /',modelMessages,'model updates');
