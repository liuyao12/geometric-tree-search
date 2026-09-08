import {latticeKey} from '../../assets/cyclotomic-five.js';
import {selectedPenroseProblem} from '../../assets/penrose-selection-problem.js?v=20260908-sets';
import {knownPenroseBenchmark} from '../../assets/penrose-known-benchmark.js?v=20260908-sets';
import {createObstructionSearch} from '../../assets/cyclotomic-obstruction-search.js?v=20260908-lanes';
import {createSearchStatus} from './search-status.js';
let search,activity,benchmark,done=false,computeMs=0;
self.onmessage=({data})=>{try{
 let pausedCorona=null;
 if(data.type==='init'){
  const start=performance.now(),problem=selectedPenroseProblem(data.tileKinds),adapter=data.mode==='known'?knownPenroseBenchmark(problem):{problem};benchmark=data.mode==='known'?adapter:null;
  search=createObstructionSearch({...adapter,learn:data.mode==='learned',targetCount:Infinity,nodeLimit:100000,seed:data.seed||1});
  activity=createSearchStatus();activity.accept(search.next().value);done=false;computeMs=performance.now()-start;
 }else if(data.type==='advance'&&search&&!done){
  const start=performance.now();for(let i=0;i<(data.step?1:100);i++){
   const r=search.next();done=r.done;activity.accept(r.value);
   const p=search.progress();if(r.value?.type==='add'&&p.minimumFrontierGeneration>=data.targetCorona&&p.deadPoints===0){pausedCorona=data.targetCorona;break;}
   if(done||performance.now()-start>15)break;
  }computeMs+=performance.now()-start;
 }
 const snapshot=search.snapshot();
 if(benchmark){const points=new Set();let segments=0;for(const tile of snapshot.tiles)for(const b of benchmark.decorate(tile).bars){points.add(latticeKey(b.from));points.add(latticeKey(b.to));segments++;}snapshot.memory.bars={points:points.size,endpointReferences:2*segments,segments,familyValues:segments};}
 self.postMessage({...snapshot,done,computeMs,pausedCorona,activity:activity.snapshot()});
}catch(error){self.postMessage({error:error.message,done:true});}};
