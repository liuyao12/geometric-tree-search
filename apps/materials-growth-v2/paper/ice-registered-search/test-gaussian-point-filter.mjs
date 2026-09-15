import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {gaussianPointClass} from './gaussian-point-filter.mjs';
const {PointSearch}=await import(pathToFileURL(process.argv[2]));
const fields=[0,3,3.1].map(x=>({vectors:[[x,0,0]],amplitudes:[1],colors:['opaque'],sigma:.4}));
const c=(id,base,p,f)=>({id,base,t:[{point:p,value:1}],fieldM:[{point:'mark-only',field:f}]});
const model={capacity:1,required:['p','q'],complete:true,radius:.2,fields,candidates:[c('a-bad','left','p',0),c('b-good','left','p',1),c('c-right','right','q',1),c('d-right','right','q',2)]};
const Engine=gaussianPointClass(PointSearch,model),e=new Engine(model),root=JSON.stringify(e.semanticState());let audits=0;
function audit(){
 const active=[...e.placed.keys()].map(id=>e.candidates.get(id));
 for(const candidate of model.candidates){
  const legal=!active.some(a=>a.id===candidate.id||a.base===candidate.base||a.t[0].point===candidate.t[0].point||2-2*Math.exp(-((fields[a.fieldM[0].field].vectors[0][0]-fields[candidate.fieldM[0].field].vectors[0][0])**2)/.32)>.16);
  assert.equal(!e.reason(e.candidates.get(candidate.id)),legal);
  for(const p of ['p','q'])assert.equal(e.graph.get(p)?.has(candidate.id)||false,legal&&candidate.t[0].point===p);
 }e.auditGraph();audits++;
}
audit();const mark=e.apply('a-bad');audit();assert.equal(e.decision().kind,'dead');e.undo(mark);audit();assert.equal(JSON.stringify(e.semanticState()),root);
let last;for(let i=0;i<20;i++){last=e.advance();audit();if(['complete','exhausted','unknown'].includes(last.kind))break;}
assert.equal(last.kind,'complete');assert(e.stats.backtracks>0);assert(e.placed.has('b-good'));e.undo(0);audit();assert.equal(JSON.stringify(e.semanticState()),root);assert.equal(e.fieldAssignments.size,0);
assert.throws(()=>gaussianPointClass(PointSearch,{...model,candidates:[...model.candidates,c('third','third','r',1)]}),/two-assignment/);
// Many geometric alternatives at one anchor are safe if their shared atom
// consumes at least half the integer capacity. Enumerate every subset.
let subsets=0,capacityStates=0;
for(const capacity of [2,3,4,5])for(const value of [1,2]){
 const many={capacity,required:['shared'],complete:true,radius:2,fields,candidates:Array.from({length:5},(_,i)=>({id:`g${i}`,base:`inventory${i}`,t:[{point:'shared',value}],fieldM:[{point:'mark-only',field:i%fields.length}]}))};
 if(3*value<=capacity){assert.throws(()=>gaussianPointClass(PointSearch,many),/two-assignment/);continue;}
 const E=gaussianPointClass(PointSearch,many),state=new E(many);assert.equal(state.fieldArityCertificates[0].kind,'integer-capacity');
 for(let mask=0;mask<32;mask++){
  const ids=many.candidates.filter((_,i)=>mask&(1<<i)).map(c=>c.id);subsets++;
  if(ids.length*value>capacity)continue;
  for(const id of ids)assert.equal(state.reason(state.candidates.get(id)),null),state.apply(id);
  assert((state.fieldAssignments.get('mark-only')||[]).length<=2);state.auditGraph();state.undo(0);capacityStates++;
 }
}
const duplicate={...model,candidates:[{...model.candidates[0],fieldM:[...model.candidates[0].fieldM,...model.candidates[0].fieldM]}]};
assert.throws(()=>gaussianPointClass(PointSearch,duplicate),/Duplicate marking/);
console.log(JSON.stringify({subsets,capacityStates,status:'capacity-certificate controls passed'}));
console.log(JSON.stringify({audits,backtracks:e.stats.backtracks,status:'passed',limits:'Small mark-only/dead-end/backtracking/rollback control, not a complete adapter conformance suite.'}));
