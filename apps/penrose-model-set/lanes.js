export const LANE_IDS=['learned','plain','known'];
// Keep each search, but dispatch work to only one worker at a time.
export function createLaneRunner({makeWorker,notify,schedule=fn=>setTimeout(fn,0),options=()=>({}),now=()=>performance.now()}){
 let lanes={},running=false,selected='learned',stepPending=false;
 const fresh=()=>({worker:null,busy:false,state:null,target:3,elapsedMs:0,started:null});
 const elapsed=id=>{const l=lanes[id];return l?l.elapsedMs+(l.started===null?0:now()-l.started):0;};
 function emit(){notify({lanes,running,selected,target:lanes[selected]?.target});}
 function dispatch(l,message){l.busy=true;l.started=now();l.worker.postMessage(message);}
 function pump(){
  if(Object.values(lanes).some(l=>l.busy))return;
  const id=selected,l=lanes[id];if(!l)return;
  if(!l.worker){
   l.worker=makeWorker();l.worker.onmessage=({data})=>{
    if(lanes[id]!==l)return;
    l.elapsedMs+=now()-l.started;l.started=null;l.busy=false;
    if(data.learning&&!data.learning.tables)data.learning.tables=l.state?.learning?.tables||[];l.state=data;
    if(id===selected&&(data.done||data.pausedCorona===l.target)){running=false;stepPending=false;}
    emit();schedule(pump);
   };
   l.worker.onerror=e=>l.worker.onmessage({data:{done:true,error:e.message}});
   dispatch(l,{...options(),type:'init',mode:id});emit();return;
  }
  if(l.state?.done||(!running&&!stepPending))return;
  const step=stepPending;stepPending=false;
  dispatch(l,{type:'advance',targetCorona:l.target,step});emit();
 }
 function prepare(){const l=lanes[selected];if(l.state?.pausedCorona===l.target)l.target+=2;}
 function stop(){running=false;stepPending=false;}
 function reset(){stop();Object.values(lanes).forEach(l=>l.worker?.terminate());lanes=Object.fromEntries(LANE_IDS.map(id=>[id,fresh()]));emit();pump();}
 return{reset,elapsed,select(id){if(!LANE_IDS.includes(id)||id===selected)return;stop();selected=id;emit();pump();},
  toggle(){if(running){stop();emit();return;}if(lanes[selected]?.state?.done)return;prepare();running=true;emit();pump();},
  step(){if(lanes[selected]?.state?.done)return;stop();prepare();stepPending=true;pump();emit();},
  resetCurrent(){stop();lanes[selected]?.worker?.terminate();lanes[selected]=fresh();emit();pump();},
  dispose(){stop();Object.values(lanes).forEach(l=>l.worker?.terminate());lanes={};}
 };
}
