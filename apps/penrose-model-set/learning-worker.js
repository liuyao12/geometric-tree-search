import {blindPenroseProblem} from '../../assets/penrose-blind-problem.js';
import {knownPenroseBenchmark} from '../../assets/penrose-known-benchmark.js';
import {createObstructionSearch} from '../../assets/cyclotomic-obstruction-search.js';
import {createSearchStatus} from './search-status.js';
let search,activity,done=false,computeMs=0;
self.onmessage=({data})=>{try{
 let pausedCorona=null;
 if(data.type==='init'){
  const start=performance.now(),problem=blindPenroseProblem(),adapter=data.mode==='known'?knownPenroseBenchmark(problem):{problem};
  search=createObstructionSearch({...adapter,learn:data.mode==='learned',targetCount:Infinity,nodeLimit:100000,seed:data.seed||1});
  activity=createSearchStatus();activity.accept(search.next().value);done=false;computeMs=performance.now()-start;
 }else if(data.type==='advance'&&search&&!done){
  const start=performance.now();for(let i=0;i<(data.step?1:100);i++){
   const r=search.next();done=r.done;activity.accept(r.value);
   const p=search.progress();if(r.value?.type==='add'&&p.minimumFrontierGeneration>=data.targetCorona&&p.deadPoints===0){pausedCorona=data.targetCorona;break;}
   if(done||performance.now()-start>15)break;
  }computeMs+=performance.now()-start;
 }
 self.postMessage({...search.snapshot(),done,computeMs,pausedCorona,activity:activity.snapshot()});
}catch(error){self.postMessage({error:error.message,done:true});}};
