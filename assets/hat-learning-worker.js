import {collect,grow} from './hat-local-learning.js';
self.requestAnimationFrame=callback=>setTimeout(()=>callback(performance.now()),0);
let paused=false,resume=null;
const wait=async()=>{if(paused)await new Promise(resolve=>{resume=resolve;});};
self.onmessage=async({data})=>{
 if(data.type==='pause'){paused=true;return;}if(data.type==='resume'){paused=false;resume?.();resume=null;return;}
 try{
  if(data.type==='collect'){
   const report=await collect({seed:data.seed,wait,onProgress:progress=>self.postMessage({type:'progress',...progress})});
   self.postMessage({type:'collected',report});
  }else if(data.type==='compare'){
   const result={seed:data.seed};
   for(const variant of ['baseline','marked'])result[variant]=await grow({seed:data.seed,support:variant==='marked'?data.support:[],wait,
    onEvent:e=>{if(['placement','backtrack'].includes(e.type))self.postMessage({...e,type:'growth',variant});}});
   self.postMessage({type:'compared',result});
  }
 }catch(error){self.postMessage({type:'error',message:error.message});}
};
