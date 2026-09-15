import {collect,examine} from './hat-local-learning.js?v=20260915-constraints';
self.requestAnimationFrame=callback=>setTimeout(()=>callback(performance.now()),0);
let paused=false,resume=null;
const wait=async()=>{if(paused)await new Promise(resolve=>{resume=resolve;});};
self.onmessage=async({data})=>{
 if(data.type==='pause'){paused=true;return;}if(data.type==='resume'){paused=false;resume?.();resume=null;return;}
 try{
  if(data.type==='collect'){
   const report=await collect({seed:data.seed,wait,onProgress:progress=>self.postMessage({type:'progress',...progress})});
   self.postMessage({type:'collected',report});
  }else if(data.type==='extend'){
   const row=await examine({...data,wait,onEvent:e=>{if(['placement','backtrack'].includes(e.type))self.postMessage({...e,type:'growth'});}});
   self.postMessage({type:'extended',index:data.index,row});
  }
 }catch(error){self.postMessage({type:'error',message:error.message});}
};
