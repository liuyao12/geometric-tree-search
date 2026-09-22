import {grow} from './growth-search.js?v=20260921-growth';
import {learnMarking,reuseMarking} from './marking-learning.js?v=20260921-search-inset';
import {verifyVoxelPatch} from './voxel-point-model.js';
// Both UIs use this protocol. Training is unmarked; only a fully validated
// browser-local field decorates the subsequent growth model.
export async function* runGrowthExperiment(initial,data){
 const started=performance.now();let model={...initial,required:[]},marking=null;
 yield {type:'model',model};
 if(data.action==='preview')return;
 if(['gcts','both'].includes(data.mode)){
  const options={timeMs:Math.max(0,(data.timeMs??120000)-(performance.now()-started)),pairNodes:data.pairNodes??500,extent:data.markingExtent??0,checkpoint:data.learningCheckpoint,stop:data.stop};
  for await(const e of (data.savedMarking?reuseMarking(model,data.savedMarking,options):learnMarking(model,options))){
   if(e.type==='marking-learned'){marking=e.marking;if(e.model)model=e.model;}
   yield {...e,mode:data.mode,elapsedMs:performance.now()-started};
  }
  if(!marking?.accepted){
   yield {type:'result',mode:data.mode,result:'unknown',reason:`Marking not activated: ${marking?.reason??'learning incomplete'}`,placements:[],stats:{totalMs:performance.now()-started,preparationMs:performance.now()-started,learningMs:marking?.elapsedMs??0},marking,model,config:data,searchProtocol:'seed-growth'};return;
  }
  yield {type:'model',model};
 }
 const preparationMs=performance.now()-started;
 for await(const e of grow(model,{...data,learnedRestriction:!!marking?.accepted,timeMs:Math.max(0,(data.timeMs??120000)-preparationMs)})){
  e.stats.preparationMs=preparationMs;e.stats.totalMs=e.stats.elapsedMs+preparationMs;e.marking=marking;e.config={...data,stop:undefined};
  if(e.type==='result'&&model.requiredVoxels){e.voxelVerification=verifyVoxelPatch(model,e.placements,{requireTarget:false});if(!e.voxelVerification.ok)throw Error('Independent voxel growth replay failed');e.stats.totalMs=performance.now()-started;}
  yield e;
 }
}
