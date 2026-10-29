import assert from 'node:assert/strict';
import { Worker } from 'node:worker_threads';
const url=new URL('../apps/quasicrystal-exact/search-worker.js',import.meta.url).href;
const worker=new Worker(`const {parentPort}=require('node:worker_threads');globalThis.self={postMessage:m=>parentPort.postMessage(m)};import(${JSON.stringify(url)}).then(()=>{parentPort.on('message',data=>self.onmessage({data}));parentPort.postMessage({type:'ready'});});`,{eval:true});
function wait(predicate){return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{cleanup();reject(new Error('Worker response timed out'));},20000);const listener=m=>{if(m.type==='error'){cleanup();reject(new Error(m.error));}else if(predicate(m)){cleanup();resolve(m);}};const error=e=>{cleanup();reject(e);};function cleanup(){clearTimeout(timer);worker.off('message',listener);worker.off('error',error);}worker.on('message',listener);worker.on('error',error);});}
function request(message,predicate){const response=wait(predicate);worker.postMessage(message);return response;}
const snapshot=predicate=>m=>m.type==='snapshot'&&predicate(m);
try{
 await wait(m=>m.type==='ready');
 let p=await request({type:'init',config:{target:8,seed:4},delay:0,auto:false},snapshot(m=>m.summary.tiles===1));assert.equal(p.running,false);
 p=await request({type:'step',target:8},snapshot(m=>m.summary.tiles===2));assert.equal(p.running,false);
 p=await request({type:'start',target:8},snapshot(m=>m.summary.state==='checkpoint'));assert.equal(p.summary.tiles,8);assert.equal(p.running,false);
 p=await request({type:'start',target:10},snapshot(m=>m.summary.state==='checkpoint'));assert.equal(p.summary.tiles,10);
 p=await request({type:'init',config:{target:9,seed:7,seedKind:'oblate'},auto:false},snapshot(m=>m.summary.tiles===1));assert.equal(p.display.tiles[0].kind,'oblate');
 await request({type:'step',target:14},snapshot(m=>m.summary.tiles===2));
 p=await request({type:'pause'},snapshot(m=>!m.running));assert.equal(p.summary.tiles,2);
 const exported=await request({type:'export'},m=>m.type==='export');const json=JSON.parse(exported.json);assert.equal(json.config.target,14);assert.equal(json.tiles.length,2);assert.equal(json.windowFilter,false);assert.equal(json.markings,null);assert.equal(typeof json.tiles[0].origin[0][0],'string');
 p=await request({type:'start',target:14},snapshot(m=>m.summary.state==='checkpoint'));assert.equal(p.summary.tiles,14);assert.equal(p.summary.dead,0);
 p=await request({type:'init',config:{target:6,seed:4,markings:'ammann'},auto:false},snapshot(m=>m.summary.tiles===1));
 assert.equal(p.summary.markingPoints,6);assert.equal(p.summary.markingComponents,12);assert(p.display.tiles[0].dots.length===6);assert(p.display.prototypes.every(t=>t.decoration));
 await request({type:'step',target:6},snapshot(m=>m.summary.tiles===2));
 const marked=JSON.parse((await request({type:'export'},m=>m.type==='export')).json);assert.equal(marked.markings.source,'supplied');assert.equal(marked.markings.learned,false);assert(marked.pointMarkingState.length>6);
 console.log('ok: real worker init, single-step, pause, resume, changed targets, reset to oblate root, exact JSON export, viable checkpoint');
}finally{await worker.terminate();}
