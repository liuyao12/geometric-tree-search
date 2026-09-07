import assert from 'node:assert/strict';
import {Worker} from 'node:worker_threads';
import {createPenroseGrowth} from '../assets/penrose-growth.js';
import {createSearchStatus} from '../apps/penrose-model-set/search-status.js';
const options={useMarkings:true,extent:2,targetCount:8,nodeLimit:100,seed:1};
const reference=createPenroseGrowth(options),expected=createSearchStatus();
for(let step=reference.next();!step.done;step=reference.next())expected.accept(step.value);
const moduleURL=new URL('../apps/penrose-model-set/growth-worker.js',import.meta.url).href;
const source=`import {parentPort} from 'node:worker_threads';globalThis.self={postMessage:data=>parentPort.postMessage(data)};await import(${JSON.stringify(moduleURL)});parentPort.on('message',data=>self.onmessage({data}));`;
const worker=new Worker(new URL(`data:text/javascript,${encodeURIComponent(source)}`));
const request=data=>new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('worker timeout')),10000);worker.once('message',data=>{clearTimeout(timer);resolve(data);});worker.postMessage(data);});
try{
 let s=await request({type:'init',options});assert.deepEqual(s.activity,{kind:'ready'});
 while(!s.done){s=await request({type:'advance',events:200});assert(!s.error);assert(s.activity);}
 assert.deepEqual(s.activity,expected.snapshot());
 assert.deepEqual((await request({type:'advance',events:200})).activity,s.activity,'terminal polls do not recount events');
 assert.deepEqual((await request({type:'init',options})).activity,{kind:'ready'});
 console.log('ok: actual batched worker status matches every-event reference; reset and terminal freeze');
}finally{await worker.terminate();}
