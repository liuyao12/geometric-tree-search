export const LANE_IDS=['learned','plain','known'];
// Each lane owns a worker and advances independently of the displayed canvas.
export function createLaneRunner({makeWorker,notify,schedule=fn=>setTimeout(fn,0),options=()=>({})}){
 let lanes={},running=false,target=3,epoch=0;
 const eligible=l=>!l.busy&&!l.state?.done&&l.state?.pausedCorona!==target;
 function emit(){notify({lanes,running,target});}
 function pump(id,step=false){const l=lanes[id];if(!l||!eligible(l))return;l.busy=true;l.worker.postMessage({type:'advance',targetCorona:target,step});}
 function reset(){epoch++;const version=epoch;Object.values(lanes).forEach(l=>l.worker.terminate());running=false;target=3;lanes={};
  for(const id of LANE_IDS){const worker=makeWorker(),l=lanes[id]={worker,busy:true,state:null};
   worker.onmessage=({data})=>{if(version!==epoch)return;l.busy=false;l.state=data;
    if(LANE_IDS.every(k=>lanes[k]?.state&&(lanes[k].state.done||lanes[k].state.pausedCorona===target)))running=false;
    emit();if(running&&eligible(l))schedule(()=>{if(version===epoch&&running)pump(id);});};
   worker.onerror=e=>worker.onmessage({data:{done:true,error:e.message}});
   worker.postMessage({...options(),type:'init',mode:id});
  }emit();
 }
 return{reset,toggle(){if(running){running=false;emit();return;}
  if(LANE_IDS.every(id=>lanes[id].state?.done||lanes[id].state?.pausedCorona===target))target+=2;
  running=true;emit();LANE_IDS.forEach(id=>pump(id));},step(){running=false;if(LANE_IDS.every(id=>lanes[id].state?.done||lanes[id].state?.pausedCorona===target))target+=2;LANE_IDS.forEach(id=>pump(id,true));emit();},dispose(){epoch++;Object.values(lanes).forEach(l=>l.worker.terminate());}};
}
