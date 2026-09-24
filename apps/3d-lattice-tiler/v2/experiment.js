import {learnCertifiedMarking,reuseCertifiedMarking,CERTIFIED_METHOD} from '../certified-marking.js?v=20260924-certified';
import {runGrowthExperiment} from '../growth-experiment.js?v=20260924-certified';
import {verifyVoxelPatch} from '../voxel-point-model.js';
import {prepareModel} from './model.js?v=20260924-certified';
import {search} from './search.js?v=2.5.0';
import {learnMarking,reuseMarking} from '../marking-learning.js?v=20260921-search-inset';
import {preprocessTilingSystem,tileSpecs} from '../engine.js?v=20260921-growth';
import {periodicStream} from '../periodic-search.js';
export async function* runExperiment(data){
  const started=performance.now();
  try{
    let model=prepareModel(data);
    if(data.searchProtocol==='seed-growth'&&data.action!=='probe'){
      const initialMs=performance.now()-started;
      for await(const e of runGrowthExperiment(model,{...data,timeMs:Math.max(0,(data.timeMs??120000)-initialMs)})){
        if(e.stats){e.stats.preparationMs=(e.stats.preparationMs??0)+initialMs;e.stats.totalMs+=initialMs;}
        if(e.elapsedMs!==undefined)e.elapsedMs+=initialMs;e.config=data;yield e;
      }
      return;
    }
    yield {type:'model',model};
    if(data.action==='preview')return;
    if(data.action==='probe'){
      if(model.exactPointImport)throw Error('The solid-angle periodic probe is not a certificate for this imported point domain. Use the exact growth or window search.');
      if(model.requiredVoxels)throw Error('The legacy structural probes use a different point model. Recorded voxel-period evidence is linked in the catalogue.');
      if(model.slab)throw Error('The 3D periodic/isohedral probe does not certify this one-slab model. Use the original explorer for the historical 3D prism probe.');
      const p=preprocessTilingSystem({mode_key:data.tile,include_mirrors:data.mirrors,custom_system:data.custom},tileSpecs);
      for(const t of p.prototiles)t.rescaleOccupancyWeights(model.capacity);
      for await(const e of periodicStream({tiling_strategy:data.strategy,periodic_patch_max_tiles:8,periodic_require_all_types:false,include_mirrors:data.mirrors,time_limit_ms:data.timeMs,node_limit:data.nodes,criterion:'count',target_val:20},p.prototiles,model.capacity,['#4fdac5','#b7a2ff'],{})){
        if(e.type==='finished')yield {type:'probe',strategy:data.strategy,event:e,totalMs:performance.now()-started};
      }
      return;
    }
    let marking=null;
    if(['gcts','both'].includes(data.mode)){
      const options={timeMs:Math.max(0,data.timeMs-(performance.now()-started)),pairNodes:data.pairNodes??500,extent:data.markingExtent??1,checkpoint:data.learningCheckpoint};
      const certified=(data.savedMarking?.marking.method??data.markingMethod)===CERTIFIED_METHOD;
      // Reserve time for the requested search even when local checks time out.
      if(certified)options.timeMs=Math.min(30000,options.timeMs*0.4);
      const learner=data.savedMarking?(certified?reuseCertifiedMarking:reuseMarking):(certified?learnCertifiedMarking:learnMarking);
      for await(const e of learner(model,data.savedMarking??options,data.savedMarking?options:undefined)){
        if(e.type==='marking-learned'){marking=e.marking;if(model.requiredVoxels)for(const row of marking.evidence??[])if(row.status==='valid'&&!verifyVoxelPatch(model,row.placements,{requireTarget:false}).ok)throw Error('Corona witness has voxel overlap');if(e.model)model=e.model;}
        yield {...e,mode:data.mode,elapsedMs:performance.now()-started};
      }
      if(!marking.accepted){
        yield {type:'result',mode:data.mode,result:'unknown',reason:`Marking not activated: ${marking.reason}`,placements:[],verification:{ok:false,covered:0,required:model.required.length},stats:{totalMs:performance.now()-started,preparationMs:performance.now()-started,learningMs:marking.elapsedMs,attempts:0,branches:0,backtracks:0,forced:0,capacityCuts:0,lookaheadCuts:0,clusterValidated:0},marking,model,config:data};return;
      }
      yield {type:'model',model};
    }
    const preparationMs=performance.now()-started;
    for await(const e of search(model,{...data,learnedRestriction:!!marking?.accepted&&!marking?.fallback,timeMs:Math.max(0,data.timeMs-preparationMs)})){
      e.stats.preparationMs=preparationMs;e.stats.totalMs=e.stats.elapsedMs+preparationMs;e.marking=marking;
      e.config=data;
      if(e.type==='result'&&model.requiredVoxels){
        const verificationStarted=performance.now();
        e.voxelVerification=verifyVoxelPatch(model,e.placements);
        if(e.result==='finite_exact'&&!e.voxelVerification.ok)throw Error('Independent voxel replay failed');
        e.stats.voxelVerificationMs=performance.now()-verificationStarted;e.stats.totalMs=performance.now()-started;
      }
      yield e;
    }
  }catch(error){yield {type:'error',message:error.message,kind:error.kind??'unsupported',totalMs:performance.now()-started};}
}
