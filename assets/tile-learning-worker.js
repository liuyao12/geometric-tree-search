import {createConnectionLearner} from './tile-connection-learning.js?v=20260920-compact';
self.requestAnimationFrame=cb=>setTimeout(cb,0);
let paused=false,resume=null;
const wait=async()=>{if(paused)await new Promise(resolve=>resume=resolve);};
self.onmessage=async({data})=>{
 if(data.type==='pause'){paused=true;return;}if(data.type==='resume'){paused=false;resume?.();resume=null;return;}
 try{const learner=createConnectionLearner(data.setId);
  if(data.type==='collect'){const report=await learner.collect({...data,wait,onProgress:p=>self.postMessage({type:'progress',...p})});self.postMessage({type:'collected',report});}
  if(data.type==='extend'){const row=await learner.examine({...data,wait,onEvent:e=>{if(['placement','backtrack'].includes(e.type))self.postMessage({...e,type:'growth'});}});self.postMessage({type:'extended',index:data.index,row});}
 }catch(e){self.postMessage({type:'error',message:e.message});}
};
