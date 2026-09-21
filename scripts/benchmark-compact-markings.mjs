import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {createConnectionLearner,TILE_SETS} from '../assets/tile-connection-learning.js';
import {FixedA2Marking,SparseA2Marking,solveA2Tiling,makeHexBoundary} from '../assets/a2-tiling-engine.js';
import {reduceMarking,activeMarkingSupport,CompactA2Marking} from '../assets/marking-reduction.js';
import assert from 'node:assert/strict';
globalThis.requestAnimationFrame=cb=>setImmediate(cb);
const target=32,nodeLimit=1500,seeds=[1,7,10],rows=[],reductions={};
const models=JSON.parse(fs.readFileSync(new URL('../assets/data/tile-markings.json',import.meta.url))).models;
for(const setId of Object.keys(TILE_SETS)){
 const learner=createConnectionLearner(setId),model=models[setId],start=performance.now(),compact=reduceMarking(model);
 reductions[setId]={...compact.reduction,reductionMs:Math.round(performance.now()-start)};
 for(const seed of seeds)for(const label of ['known','learned','compact']){
  const support=label==='compact'?activeMarkingSupport(compact):model.support;
  const marking=label==='known'?new FixedA2Marking(1,{rank:setId==='turtle'?3:1,tiles:learner.config.tiles}):label==='compact'?new CompactA2Marking(compact):new SparseA2Marking(support);
  const started=performance.now();
  const r=await solveA2Tiling({boundary:makeHexBoundary(40),tiles:learner.config.tiles,allowReflections:learner.config.allowReflections,initialPlacements:[learner.materialize(learner.roots[0])],fixedInitialPlacements:true,completePointGrowth:true,maximize:true,targetPlacements:target,nodeLimit,randomSeed:seed,marking});
  const placements=r.placements.map(p=>({tile:p.tile,orientation:p.orientation.index,translation:p.translation}));
  const row={setId,seed,label,result:r.result,tiles:r.placements.length,nodes:r.stats.nodes,backtracks:r.stats.backtracks,ms:Math.round(performance.now()-started),patchHash:createHash('sha256').update(JSON.stringify(placements)).digest('hex'),learnedAccepts:learner.verifyPatch(placements,model.support).compatible};
  if(label==='compact'){const full=rows.find(a=>a.setId===setId&&a.seed===seed&&a.label==='learned');for(const key of ['result','tiles','nodes','backtracks','patchHash'])assert.equal(row[key],full[key]);}
  rows.push(row);console.log(JSON.stringify(row));
 }
}
const report={target,nodeLimit,seeds,known:{extent:1,turtleRank:3,hatRank:1,mixedRank:1},conditions:'Identical fixed orientation-0 root, complete point growth, inventories and reflection policies. Timings are single runs, not a speed guarantee. Reduction preserves learned constraints, not equivalence to known markings.',reductions,rows};
if(process.argv[2])fs.writeFileSync(process.argv[2],JSON.stringify(report,null,2)+'\n');
