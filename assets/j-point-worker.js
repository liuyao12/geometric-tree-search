import {JPointSearch} from './j-point-engine.js';
let search,paused=false,token=0,start=0,pauseAt=0,pauseTotal=0;
const elapsed=()=>performance.now()-start-pauseTotal-(paused?performance.now()-pauseAt:0);
const send=type=>postMessage({type,...search.snapshot(search.bestViable),elapsedMs:elapsed()});
function tick(version){if(version!==token||paused||!search)return;const end=performance.now()+24;let result;do{result=search.step();}while(!result.done&&performance.now()<end);
 if(result.done){send('finished');return;}if(elapsed()>15000||search.pool.size>160000){search.status='unknown';send('finished');return;}send('progress');setTimeout(()=>tick(version),0);}
onmessage=({data})=>{if(data.type==='start'){token++;paused=false;pauseTotal=0;start=performance.now();search=new JPointSearch({branch:data.branch,support:data.support,target:data.target,nodeLimit:5000,seed:1});tick(token);}if(data.type==='pause'&&!paused){paused=true;pauseAt=performance.now();}if(data.type==='resume'&&paused){pauseTotal+=performance.now()-pauseAt;paused=false;tick(token);}};
