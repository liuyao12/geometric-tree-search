import assert from 'node:assert/strict';
import {Worker} from 'node:worker_threads';
import {readFile} from 'node:fs/promises';
const modelData=JSON.parse(await readFile(new URL('../apps/quasicrystal-exact/data/polyhedra-exact.json',import.meta.url))),url=new URL('../apps/quasicrystal-exact/search-worker.js',import.meta.url).href;
const worker=new Worker(`const {parentPort}=require('node:worker_threads');globalThis.self={postMessage:m=>parentPort.postMessage(m)};import(${JSON.stringify(url)}).then(()=>{parentPort.on('message',data=>self.onmessage({data}));parentPort.postMessage({type:'ready'});});`,{eval:true});
const wait=predicate=>new Promise((resolve,reject)=>{const timer=setTimeout(()=>{cleanup();reject(Error('Worker response timeout'));},60000);const listener=m=>{if(m.type==='error'){cleanup();reject(Error(m.error));}else if(predicate(m)){cleanup();resolve(m);}},error=e=>{cleanup();reject(e);};function cleanup(){clearTimeout(timer);worker.off('message',listener);worker.off('error',error);}worker.on('message',listener);worker.on('error',error);});
const request=(message,predicate)=>{const response=wait(predicate);worker.postMessage(message);return response;},snap=p=>m=>m.type==='snapshot'&&p(m);
try{
 await wait(m=>m.type==='ready');let epoch=0;
 for(const system of ['danzer','danzerOcta','socolar','wang','goodman','goodmanCross','scd']){
  const token=++epoch,config={system,target:2,seed:4,budget:100,control:'source'};
  let p=await request({type:'init',epoch:token,config,modelData,delay:0},snap(m=>m.epoch===token));assert.equal(p.summary.tiles,1);assert.equal(p.running,false);assert.equal(p.system,system);assert.equal(p.learned,undefined);assert(p.scope);
  p=await request({type:'step'},snap(m=>m.epoch===token&&m.summary.tiles===2));assert.equal(p.running,false);assert(p.display.tiles.every(t=>t.faces.every(f=>f.length>=3)));
  p=await request({type:'pause'},snap(m=>!m.running));assert.equal(p.summary.tiles,2);
  const json=JSON.parse((await request({type:'export'},m=>m.type==='export')).json);assert.equal(json.model||json.system,system);assert.equal(json.tiles.length,2);assert(json.scope);
  console.log(system,'worker init / step / pause / exact export passed');
 }
 let p=await request({type:'start',target:100},snap(m=>m.summary.state==='complete'));assert.equal(p.summary.tiles,45);assert.equal(p.running,false);assert(p.summary.eliminatedMarking>0);
 p=await request({type:'init',epoch:++epoch,config:{system:'wang',control:'geometry',seed:4,target:2}},snap(m=>m.summary.tiles===1));assert.equal(p.summary.markingComponents,0);assert.equal(p.mode,'geometry');
 p=await request({type:'init',epoch:++epoch,config:{system:'ammann',markings:'ammann',seed:4,target:2}},snap(m=>m.summary.tiles===1));assert.equal(p.summary.markingComponents,12);
 console.log('All model switching and finite completion protocol checks passed');
}finally{await worker.terminate();}
