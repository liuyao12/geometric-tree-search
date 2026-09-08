import assert from 'node:assert/strict';
let state;globalThis.self={postMessage:data=>{state=structuredClone(data);}};
await import('../apps/penrose-model-set/learning-worker.js');
const send=data=>{self.onmessage({data});assert(!state.error,state.error);return state;};
send({type:'init',mode:'learned'});assert.equal(state.learning.rules,0);
for(const targetCorona of [3,5]){
 let batches=0;while(!state.done&&state.pausedCorona!==targetCorona){send({type:'advance',targetCorona});assert(++batches<30000);}
 assert.equal(state.pausedCorona,targetCorona);assert(state.minimumFrontierGeneration>=targetCorona);assert.equal(state.graph.deadPoints,0);
 console.log('ok: learned worker pause',targetCorona,state.tiles.length,'tiles',state.learning.rules,'rules',state.learning.addresses,'addresses');
}
const prior=state.learning.rules;send({type:'advance',targetCorona:7,step:true});assert(state.learning.rules>=prior,'Continue retains learned points');
send({type:'init',mode:'learned'});assert.equal(state.learning.rules,0,'Reset starts empty');
