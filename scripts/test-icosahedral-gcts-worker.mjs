import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {Worker} from 'node:worker_threads';
const workerURL=new URL('../apps/quasicrystal-exact/search-worker.js',import.meta.url).href;
const worker=new Worker(`const {parentPort}=require('node:worker_threads');globalThis.self={postMessage:m=>parentPort.postMessage(m)};import(${JSON.stringify(workerURL)}).then(()=>{parentPort.on('message',data=>self.onmessage({data}));parentPort.postMessage({type:'ready'});});`,{eval:true});
function wait(predicate){return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{cleanup();reject(Error('GCTS worker response timeout'));},120000),listener=m=>{if(m.type==='error'){cleanup();reject(Error(m.error));}else if(predicate(m)){cleanup();resolve(m);}},error=e=>{cleanup();reject(e);};function cleanup(){clearTimeout(timer);worker.off('message',listener);worker.off('error',error);}worker.on('message',listener);worker.on('error',error);});}
function request(message,predicate){const response=wait(predicate);worker.postMessage(message);return response;}
const snap=p=>m=>m.type==='snapshot'&&p(m);
try{
 await wait(m=>m.type==='ready');await request({type:'init',config:{target:12,seed:4,markings:'ammann'},delay:0},snap(m=>m.summary.tiles===1));
 let p=await request({type:'learn',config:{extent:1,attempts:1}},snap(m=>m.phase==='learning'&&m.learning.resolved>=2));assert(p.learning.counts.negative>=2);assert.equal(p.learning.preview.learnedPoints.length>0,true);
 p=await request({type:'pause'},snap(m=>m.phase==='learning'&&!m.running));const count=p.learning.resolved,revision=p.learning.marking.revision;
 p=await request({type:'step'},snap(m=>m.phase==='learning'&&!m.running&&m.learning.resolved>count));assert(p.learning.marking.revision>revision);
 const inspection=await request({type:'inspect-pair',index:0},m=>m.type==='pair-inspection');assert.equal(inspection.status,'negative');assert.equal(inspection.compatible,false);assert.equal(inspection.slots.length,13);assert.equal(inspection.display.tiles.length,2);
 await request({type:'start'},snap(m=>m.phase==='learning'&&m.running));await request({type:'pause'},snap(m=>!m.running));
 const receiptPath=process.env.GCTS_RECEIPT_PATH;if(receiptPath){const receipt=JSON.parse(await fs.readFile(receiptPath,'utf8')),model=receipt.model;
  p=await request({type:'activate',model,config:{seed:4,target:60,markings:'ammann'}},snap(m=>m.phase==='growth'&&m.summary.state==='checkpoint'));assert.equal(p.summary.tiles,60);assert(p.summary.eliminatedLearned>0);assert(p.display.tiles.some(t=>t.learnedPoints?.length));assert.equal(p.learned.id,model.id);assert.equal(p.learned.slots.length,13);const reusedInspection=await request({type:'inspect-pair',index:0},m=>m.type==='pair-inspection');assert.equal(reusedInspection.compatible,false);assert.equal(reusedInspection.slots.length,13);
  const exported=JSON.parse((await request({type:'export'},m=>m.type==='export')).json);assert.equal(exported.learnedMarking.id,model.id);assert(exported.pointMarkingState.length>6);
 }
 p=await request({type:'init',config:{target:3,seed:4,markings:'none'},auto:false},snap(m=>m.phase==='growth'&&m.summary.tiles===1));assert.equal(p.summary.markingPoints,0);assert.equal(p.learned,null);
 console.log('ok: real learner worker collection, pause/resume/single-step, separate field preview, exact pair inspection, optional validated reuse/growth/export, and clean baseline reset');
}finally{await worker.terminate();}
