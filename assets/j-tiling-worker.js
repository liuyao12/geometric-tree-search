import {JSearch} from './j-tiling-engine.js';
let search=null,paused=false,token=0,started=0,pauseStarted=0,pauseTotal=0;
const elapsed=()=>performance.now()-started-pauseTotal-(paused?performance.now()-pauseStarted:0);
const send=(type,placements)=>postMessage({type,...search.snapshot(placements),elapsedMs:elapsed()});
function tick(version){if(version!==token||paused||!search)return;const end=performance.now()+24;let step;
 do{step=search.step();}while(!step.done&&performance.now()<end);
 if(step.done){send('finished',search.bestViable);return;}
 if(elapsed()>30000||search.pool.size>150000){search.stopped=true;while(!search.step().done){}send('finished',search.bestViable);return;}
 send('progress',search.bestViable);setTimeout(()=>tick(version),0);
}
onmessage=({data})=>{
 if(data.type==='start'){token++;paused=false;pauseTotal=0;started=performance.now();search=new JSearch({target:data.target??30,nodeLimit:20000,seed:1});send('progress');tick(token);}
 if(data.type==='pause'&&!paused){paused=true;pauseStarted=performance.now();}
 if(data.type==='resume'&&search&&paused){pauseTotal+=performance.now()-pauseStarted;paused=false;tick(token);}
 if(data.type==='cancel'){token++;search=null;}
};
