import {createCoronaLearner as createConnectionLearner} from './tile-corona-learning.js?v=20260921-viable-corona';
self.requestAnimationFrame=cb=>setTimeout(cb,0);
let paused=false,resume=null,frameAck=null,frameId=0;
const frames=[];
const pauseGate=async()=>{if(paused)await new Promise(resolve=>resume=resolve);};
const enqueue=event=>{if(['pair-start','placement','backtrack','fail','frontier-viable','pair-result'].includes(event.type))frames.push(event);};
// The solver's existing demand hook drains actual events before searching on.
// Waiting for the displayed frame prevents an unbounded animation backlog.
const wait=async()=>{
 await pauseGate();
 while(frames.length){
  const event=frames.shift(),id=++frameId;
  await new Promise(resolve=>{frameAck={id,resolve};self.postMessage({type:'search-frame',id,event});});
  await pauseGate();
 }
};
self.onmessage=async({data})=>{
 if(data.type==='frame-shown'){if(frameAck?.id===data.id){const ack=frameAck;frameAck=null;ack.resolve();}return;}
 if(data.type==='pause'){paused=true;return;}if(data.type==='resume'){paused=false;resume?.();resume=null;return;}
 try{const learner=createConnectionLearner(data.setId,{lattice:data.lattice});
  if(data.type==='collect'){const report=await learner.collect({...data,wait,onSearch:enqueue,onProgress:p=>self.postMessage({type:'progress',...p})});self.postMessage({type:'collected',report});}
  if(data.type==='extend'){
   const context={index:data.index,root:data.root,attachment:data.attachment};
   enqueue({...context,type:'pair-start',placements:[data.root,data.attachment],nodes:0,backtracks:0});await wait();
   const row=await learner.examine({...data,wait,onEvent:e=>enqueue({...context,...e})});
   enqueue({...context,type:'pair-result',status:row.status,placements:row.status==='invalid'?(row.lastFailure?.placements??row.placements):row.placements,choice:row.lastFailure?.point,nodes:row.nodes,backtracks:row.backtracks});await wait();
   self.postMessage({type:'extended',index:data.index,row});
  }
 }catch(e){self.postMessage({type:'error',message:e.message});}
};
