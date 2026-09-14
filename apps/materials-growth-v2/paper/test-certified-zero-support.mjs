import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {certifiedZeroSupport} from './certified-zero-support.mjs';
const {PointSearch,verify}=await import(pathToFileURL(process.argv[2]));
const model={capacity:2,required:['0','1'],candidates:[
 {id:'000000',t:[{point:'0',value:2},{point:'1',value:1}],m:[]},
 {id:'000001',t:[{point:'0',value:2},{point:'1',value:2}],m:[]}]};
const proof={excluded:[0],y:[[0,'1'],[1,'-1']],z:[],bound:'0'};
const blocked=certifiedZeroSupport(model,proof);assert.deepEqual([...blocked],['000000']);
let solutions=0;
for(let mask=0;mask<4;mask++){
 const chosen=model.candidates.filter((_,j)=>mask&(1<<j)).map(c=>c.id);
 if(verify(model,chosen).complete){assert(chosen.every(id=>!blocked.has(id)));solutions++;}
}
assert.equal(solutions,1);
const e=new PointSearch({...model,constraint:c=>blocked.has(c.id)?'certified-zero-support':null});
const root=JSON.stringify(e.semanticState());assert.equal(e.decision().kind,'forced');
e.advance();e.auditGraph();assert.equal(e.decision().kind,'complete');e.undo(0);e.auditGraph();assert.equal(JSON.stringify(e.semanticState()),root);
const corrupt=[{...proof,y:[]},{...proof,excluded:[1]},{...proof,bound:'1'},
 {...proof,z:[[0,'-1']]},{...proof,y:[[0,'1'],[0,'1']]},{...proof,excluded:[0,0]},
 {...proof,y:[[2,'1']]},{...proof,z:[[8,'1']]}];
for(const bad of corrupt)assert.throws(()=>certifiedZeroSupport(model,bad));
assert.throws(()=>certifiedZeroSupport({...model,complete:false},proof));
console.log(JSON.stringify({exhaustiveSubsets:4,solutions,mutationRejections:corrupt.length,incompletePoolRejected:true,rootRollback:true}));
