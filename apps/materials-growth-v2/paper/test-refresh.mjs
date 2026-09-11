import assert from "node:assert/strict";
import { PointSearch, verify } from "../kernel.mjs?v=observed-overlaps-1";
const original=PointSearch.prototype.refresh;
const model={required:["a","b"],candidates:[
  ["a-bad","a",0],["a-good","a",1],["b1","b",1],["b2","b",1]
].map(([id,point,value])=>({id,t:[{point,value:1}],m:[{point:"mark-only",channel:"x",lo:value,hi:value}]}))};
const runs=[];
for(const mode of ["local","global"]) {
  PointSearch.prototype.refresh=mode==="local"?original:function(changed){for(const id of changed){const p=this.points.get(id);if(p.active&&p.total<this.capacity){if(!this.graph.has(id))this.graph.set(id,new Map());}else this.graph.delete(id);}for(const id of this.candidates.keys())this.updateCandidate(id);};
  const e=new PointSearch(model),trace=[];
  for(let i=0;i<20&&e.decision().kind!=="complete";i++){trace.push(e.advance());e.auditGraph();}
  assert(e.stats.backtracks>0);assert(verify(model,[...e.placed.keys()]).complete);
  runs.push({trace,state:e.semanticState(),stack:e.stack});
}
PointSearch.prototype.refresh=original;
assert.deepEqual(runs[0],runs[1]);
console.log("Matched global/local refresh: failed branch, mark-only dependency, rollback, final exact finite solution and trace equality PASS");
