import assert from 'node:assert/strict';
let state;globalThis.self={postMessage:data=>{state=structuredClone(data);}};
await import('../apps/penrose-model-set/learning-worker.js');
const send=data=>{self.onmessage({data});assert(!state.error,state.error);return state;};
send({type:'init',mode:'learned'});assert.equal(state.learning.kind,'space');assert.equal(state.learning.rank,0);assert.equal(state.learning.dimension,state.learning.variables);
for(const targetCorona of [3,5]){
 let batches=0;while(!state.done&&state.pausedCorona!==targetCorona){send({type:'advance',targetCorona});assert(++batches<30000);}
 assert.equal(state.pausedCorona,targetCorona);assert(state.minimumFrontierGeneration>=targetCorona);assert.equal(state.graph.deadPoints,0);
 console.log('ok: learned worker pause',targetCorona,state.tiles.length,'tiles',state.learning.dimension,'dimensions',state.learning.addresses,'addresses');
}
const prior=state.learning.variables;send({type:'advance',targetCorona:7,step:true});assert.equal(state.learning.variables,prior,'Continue retains the same marking support');
send({type:'init',mode:'learned'});assert.equal(state.learning.rank,0,'Reset restores independent variables');

send({type:'init',mode:'learned',boundaryRule:'none',tileKinds:['kite','dart']});assert.equal(state.learning.rank,0);send({type:'advance',targetCorona:3,step:true});assert.equal(state.learning.kind,'space');assert(!state.learning.proofSource);
