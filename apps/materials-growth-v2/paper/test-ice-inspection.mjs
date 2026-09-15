import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {webcrypto} from 'node:crypto';
import {parseFrame,reorderFrame,coverage,readSourceFrame} from './ice-inspection-data.mjs';
const [inspection,corpus,pilot]=process.argv.slice(2),data=JSON.parse(readFileSync(inspection)),coords=new Map(JSON.parse(readFileSync(`${pilot}/coordinates.json`)).configurations.map(c=>[c.id,c]));
let states=0,atoms=0;
for(const c of data.configurations){
 const bytes=readFileSync(`${corpus}/${c.phase}-${c.split==='training'?'train':'test'}.extxyz`),text=bytes.toString().split('\n').slice(0,c.atoms+2).join('\n')+'\n';
 const frame=reorderFrame(parseFrame(text),c),expected=coords.get(c.id);
 assert.deepEqual(frame.atoms.map(a=>a.position),expected.positions);assert.deepEqual(frame.atoms.map(a=>a.species),expected.species);assert.deepEqual(frame.cell,expected.cell);
 const fakeFetch=async()=>new Response(new ReadableStream({start(controller){const encoded=new TextEncoder().encode(text+'unread next frame\n');for(let i=0;i<encoded.length;i+=97)controller.enqueue(encoded.slice(i,i+97));controller.close();}}));
 assert.deepEqual(await readSourceFrame(c,{fetcher:fakeFetch,cryptoApi:webcrypto}),frame);
 await assert.rejects(readSourceFrame({...c,firstFrameHash:'0'.repeat(64)},{fetcher:fakeFetch,cryptoApi:webcrypto}),/hash mismatch/);
 assert.throws(()=>reorderFrame(frame,{...c,sourceOrder:Array(c.atoms).fill(0)}),/mapping mismatch/);
 for(const state of Object.values(c.states)){
  assert.deepEqual(coverage(state,c.atoms),state.totals);assert.equal(state.complete,state.totals.every(t=>t===2));assert.equal(state.massFraction,state.totals.reduce((a,b)=>a+b,0)/(2*c.atoms));assert.deepEqual(coverage(state,c.atoms,0),Array(c.atoms).fill(0));
  for(let count=0;count<=state.supports.length;count++){const t=coverage(state,c.atoms,count);assert(t.every(v=>v>=0&&v<=2));}
  states++;
 }
 atoms+=c.atoms;
}
assert.throws(()=>coverage({supports:[[0],[0],[0]]},1),/Overfilled/);
assert.throws(()=>coverage({supports:[[0,0]]},1),/Repeated/);
assert.throws(()=>coverage({supports:[[1]]},1),/outside/);
assert.throws(()=>parseFrame('1\nProperties=species:S:1:pos:R:3\nH 0 0 0\n'),/schema or cell/);
console.log(JSON.stringify({configurations:data.configurations.length,states,atoms,sourceMapping:true,streamedFrameHash:true,allRevealPrefixes:true,corruptHashRejected:true,invalidMappingsRejected:true}));
