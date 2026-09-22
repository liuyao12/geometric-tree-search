#!/usr/bin/env node
import fs from 'node:fs';
import {createCoronaLearner} from '../assets/tile-corona-learning.js';
import {NeutralMarking} from './experiment-a2-online-pairs.mjs';
import {solveA2Tiling,makeHexBoundary,NoA2Marking} from '../assets/a2-tiling-engine.js';
import {workflowModel} from './experiment-a2-corona-workflow.mjs';
import {verifyGrowth} from '../apps/3d-lattice-tiler/growth-search.js';
const dir=process.argv[2]??'/tmp/a2-online-pairs',target=100,ms=3000,seeds=[1,3],rows=[];
for(const tile of ['turtle','hat']){
 const learner=createCoronaLearner(tile,{lattice:'turtle-sublattice'}),arms=[{id:'unmarked',support:[],after:0}];
 for(const positiveMode of ['pair','witness']){
  const source=JSON.parse(fs.readFileSync(`${dir}/${tile}-online-${positiveMode}-s1.json`));
  for(const snap of source.snapshots.filter(s=>[16,64,128,source.counts.total].includes(s.after)))arms.push({id:`${positiveMode}-${snap.after}`,positiveMode,...snap});
 }
 for(const [i,seed]of seeds.entries())for(const arm of i%2?[...arms].reverse():arms){
  const started=performance.now(),stopToken={stop:false},timer=setTimeout(()=>{stopToken.stop=true;},ms);let result;
  try{result=await solveA2Tiling({boundary:makeHexBoundary(20),tiles:learner.config.tiles,allowReflections:true,latticePointFilter:learner.pointFilter,initialPlacements:learner.roots.map(learner.materialize),fixedInitialPlacements:true,completePointGrowth:true,maximize:true,targetPlacements:target,nodeLimit:100000,randomSeed:seed,marking:arm.support.length?new NeutralMarking(arm.support):new NoA2Marking(),stopToken});}finally{clearTimeout(timer);}
  const elapsedMs=performance.now()-started,patch=result.placements.map(p=>({oi:p.orientation.index,translation:p.translation})),checkStart=performance.now(),check=verifyGrowth(workflowModel(tile,arm.support),patch),verificationMs=performance.now()-checkStart;
  if(!check.ok)throw Error('Checkpoint growth replay failed');
  const row={tile,arm:arm.id,after:arm.after,seed,status:arm.status??'empty',values:arm.support.length,result:result.result,tiles:patch.length,nodes:result.stats.nodes,backtracks:result.stats.backtracks,elapsedMs,verificationMs,verified:true};rows.push(row);console.log(JSON.stringify(row));
  fs.writeFileSync(`${dir}/${tile}-checkpoint-${arm.id}-s${seed}.json`,JSON.stringify({support:arm.support,patch}));
 }
}
fs.writeFileSync(`${dir}/checkpoint-growth.json`,JSON.stringify({protocol:{target,ms,seeds,trainingOrderSeed:1,score:'zero in every arm',prefixTrainingCostExcluded:true,armOrder:'forward seed 1, reverse seed 3'},rows},null,2));
