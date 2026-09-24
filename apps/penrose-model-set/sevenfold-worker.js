import {createSevenfoldSearch} from '../../assets/sevenfold-rhombs.js?v=20260924-sevenfold';
let search,done=false,computeMs=0;
self.onmessage=({data})=>{try{
  const start=performance.now();let event=null,paused=false;
  if(data.type==='init'){search=createSevenfoldSearch(data.options);done=false;computeMs=0;event=search.next().value;}
  else if(search&&!done){
    do {
      const result=search.next();done=result.done;event=result.value;
      const s=search.snapshot();
      paused=s.tiles.length>=data.target&&s.graph.deadPoints===0;
      if(done||paused||data.step)break;
    }while(performance.now()-start<35);
  }
  computeMs+=performance.now()-start;
  self.postMessage({...search.snapshot(),done,paused,event,computeMs});
}catch(error){self.postMessage({error:error.message,done:true});}};
