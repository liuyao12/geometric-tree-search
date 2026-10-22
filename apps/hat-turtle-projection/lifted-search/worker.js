import {LiftedSearch,verify} from './engine.js';
let engine=null,paused=false,epoch=0;
self.onmessage=e=>{
 if(e.data.type==='start'){epoch++;engine=new LiftedSearch(e.data.options);paused=false;run(epoch);}
 if(e.data.type==='pause')paused=e.data.value;
 if(e.data.type==='stop'&&engine){engine.stopped=true;paused=false;}
};
async function run(id){
 const started=performance.now();
 try{
  while(id===epoch){
   if(paused){await new Promise(r=>setTimeout(r,80));continue;}
   const until=performance.now()+90;let result;
   do{result=engine.step();}while(!result.done&&performance.now()<until);
   const placements=result.done&&engine.status!=='consistent finite patch'?engine.bestViable:engine.placed;
   const snapshot=engine.snapshot(placements);snapshot.elapsedMs=performance.now()-started;
   if(result.done){snapshot.verification=verify(snapshot.placements);self.postMessage({type:'done',snapshot});break;}
   self.postMessage({type:'progress',snapshot});await new Promise(r=>setTimeout(r,12));
  }
 }catch(error){self.postMessage({type:'error',message:error.message});}
}
