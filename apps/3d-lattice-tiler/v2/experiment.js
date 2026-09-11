import {prepareModel} from './model.js';
import {search} from './search.js';
import {VectorMarkings} from '../vector-markings.js';
import {preprocessTilingSystem,tileSpecs} from '../engine.js';
import {periodicStream} from '../periodic-search.js';
export async function* runExperiment(data){
  const started=performance.now();
  try{
    const model=prepareModel(data);
    yield {type:'model',model};
    if(data.action==='preview')return;
    if(data.action==='probe'){
      const p=preprocessTilingSystem({mode_key:data.tile,include_mirrors:data.mirrors,custom_system:data.custom},tileSpecs);
      for(const t of p.prototiles)t.rescaleOccupancyWeights(model.capacity);
      for await(const e of periodicStream({tiling_strategy:data.strategy,periodic_patch_max_tiles:8,periodic_require_all_types:false,include_mirrors:data.mirrors,time_limit_ms:data.timeMs,node_limit:data.nodes,criterion:'count',target_val:20},p.prototiles,model.capacity,['#4fdac5','#b7a2ff'],{})){
        if(e.type==='finished')yield {type:'probe',strategy:data.strategy,event:e,totalMs:performance.now()-started};
      }
      return;
    }
    let marking={rank:0,slots:0,scope:'none'};
    if(['gcts','both'].includes(data.mode)){
      const prepared=[model.orientations.map((o,index)=>({type:0,index,orientation:{occupancy:o.cells}}))];
      // No finite-boundary dead pair is generalized. Equate every capacity-legal
      // pair, so these static fields preserve all finite-window solutions too.
      const field=new VectorMarkings(prepared,model.capacity,{maxSlots:256});
      // A constant field cannot disagree. Elide its runtime bookkeeping after
      // synthesis instead of doubling the graph with vacuous dependencies.
      if(field.rank>1)model.orientations.forEach((o,i)=>o.marks=field.fields.get(`0:${i}`).map(m=>({pos:m.pos,value:m.basis})));
      marking={rank:field.rank,slots:field.slotCount,constantFallback:field.trivial,constantElided:field.rank<=1,scope:'redundant: all capacity-legal pairs equated; no learned pair exclusions',version:1};
    }
    const preparationMs=performance.now()-started;
    for await(const e of search(model,{...data,timeMs:Math.max(0,data.timeMs-preparationMs)})){
      e.stats.preparationMs=preparationMs;e.stats.totalMs=e.stats.elapsedMs+preparationMs;e.marking=marking;
      e.config=data;
      yield e;
    }
  }catch(error){yield {type:'error',message:error.message,kind:error.kind??'unsupported',totalMs:performance.now()-started};}
}
