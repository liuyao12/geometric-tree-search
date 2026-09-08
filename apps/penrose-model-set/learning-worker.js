import {latticeKey} from '../../assets/cyclotomic-five.js?v=20260908-speed';
import {selectedPenroseProblem} from '../../assets/penrose-selection-problem.js?v=20260908-speed';
import {knownPenroseBenchmark} from '../../assets/penrose-known-benchmark.js?v=20260908-lines';
import {createObstructionSearch} from '../../assets/cyclotomic-obstruction-search.js?v=20260908-speed';
import {createSearchStatus} from './search-status.js?v=20260908-speed';
let search,activity,benchmark,done=false,computeMs=0,compact=false,lastRevision=-1,typeIds,wireCache;
self.onmessage=({data})=>{try{
 let pausedCorona=null;
 if(data.type==='init'){
  compact=!!data.compact;lastRevision=-1;typeIds=new Map();wireCache=new WeakMap();
  const start=performance.now(),problem=selectedPenroseProblem(data.tileKinds),adapter=data.mode==='known'?knownPenroseBenchmark(problem):{problem};benchmark=data.mode==='known'?adapter:null;
  search=createObstructionSearch({...adapter,learn:data.mode==='learned',targetCount:Infinity,nodeLimit:100000,seed:data.seed||1});
  activity=createSearchStatus();activity.accept(search.next().value);done=false;computeMs=performance.now()-start;
 }else if(data.type==='advance'&&search&&!done){
  const start=performance.now();for(let i=0;i<(data.step?1:2000);i++){
   const r=search.next();done=r.done;activity.accept(r.value);
   if(r.value?.type==='add'){const p=search.progress();if(p.minimumFrontierGeneration>=data.targetCorona&&p.deadPoints===0){pausedCorona=data.targetCorona;break;}}
   if(done||performance.now()-start>50)break;
  }computeMs+=performance.now()-start;
 }
 const snapshot=search.snapshot({afterRevision:compact?lastRevision:null});
 if(benchmark){const points=new Set();let segments=0;for(const tile of snapshot.tiles)for(const b of benchmark.decorate(tile).bars){points.add(latticeKey(b.from));points.add(latticeKey(b.to));segments++;}snapshot.memory.bars={points:points.size,endpointReferences:2*segments,segments,familyValues:segments};}
 if(compact){
  const typeId=type=>{if(!typeIds.has(type))typeIds.set(type,String(typeIds.size));return typeIds.get(type);};
  snapshot.tiles=snapshot.tiles.map(t=>{if(!wireCache.has(t))wireCache.set(t,{id:typeId(t.type)+'#'+latticeKey(t.origin),type:typeId(t.type),kind:t.kind,exactPoints:t.exactPoints,weights:t.weights,origin:t.origin,...(benchmark?{bars:benchmark.decorate(t).bars}:{})});return wireCache.get(t);});
  if(snapshot.learning){lastRevision=snapshot.learning.revision;delete snapshot.learning.certificates;if(snapshot.learning.tables)snapshot.learning.tables=snapshot.learning.tables.map(t=>({type:typeId(t.type),rows:t.rows}));}
  const e=snapshot.event;snapshot.event=e?{type:e.type,forced:e.forced,branchCount:e.branchCount,frontier:e.frontier}:null;
 }
 self.postMessage({...snapshot,done,computeMs,pausedCorona,activity:activity.snapshot()});
}catch(error){self.postMessage({error:error.message,done:true});}};
