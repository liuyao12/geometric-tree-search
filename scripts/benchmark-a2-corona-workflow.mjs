#!/usr/bin/env node
import fs from 'node:fs';
import {SparseA2Marking,NoA2Marking,solveA2Tiling,makeHexBoundary,tileOrientations,A2_TILE_LOOPS} from '../assets/a2-tiling-engine.js';
import {workflowModel,compactSupport} from './experiment-a2-corona-workflow.mjs';
import {onIndex3} from './experiment-a2-corona-consensus.mjs';
import {verifyGrowth} from '../apps/3d-lattice-tiler/growth-search.js';
globalThis.requestAnimationFrame??=cb=>setImmediate(cb);
const args=Object.fromEntries(process.argv.slice(2).map(s=>s.replace(/^--/,'').split('='))),tile=args.tile??'turtle',dir=args.dir??'/tmp/a2-corona-workflow',target=+(args.target??100),ms=+(args.ms??6000),seeds=(args.seeds??'1,3').split(',').map(Number);
const family=JSON.parse(fs.readFileSync(`${dir}/${tile}-family.json`)),arms=[{id:'unmarked',support:[]}];
for(const [i,m] of family.models.entries()){
 arms.push({id:`m${i}-initial`,support:compactSupport(tile,m.support)});
 for(const radius of [1,2,3]){
  const file=`${dir}/${tile}-m${i}-c${radius}.json`;if(!fs.existsSync(file))continue;const r=JSON.parse(fs.readFileSync(file));if(r.complete&&r.solutions&&r.compactSupport)arms.push({id:`m${i}-c${radius}`,support:r.compactSupport});
 }
}
// A zero marking score in EVERY arm isolates legality changes. Same tiling
// engine, point domain, root, generation scheduler, limits and seeds.
class NeutralMarking extends SparseA2Marking{score(){return 0;}}
const orientation=tileOrientations(tile,A2_TILE_LOOPS[tile])[0],rows=[];
for(const [index,seed] of seeds.entries())for(const arm of index%2?[...arms].reverse():arms){
 const stopToken={stop:false},start=performance.now(),timer=setTimeout(()=>{stopToken.stop=true;},ms);let result;
 try{result=await solveA2Tiling({boundary:makeHexBoundary(20),tiles:[tile],allowReflections:true,initialPlacements:[{tile,orientation,translation:[0,0,0]}],fixedInitialPlacements:true,completePointGrowth:true,latticePointFilter:onIndex3,maximize:true,targetPlacements:target,nodeLimit:100000,randomSeed:seed,marking:arm.support.length?new NeutralMarking(arm.support):new NoA2Marking(),stopToken});}finally{clearTimeout(timer);}
 const elapsedMs=performance.now()-start,patch=result.placements.map(p=>({oi:p.orientation.index,translation:p.translation})),checkStart=performance.now(),verification=verifyGrowth(workflowModel(tile,arm.support),patch),verificationMs=performance.now()-checkStart;
 if(!verification.ok)throw Error('Returned growth patch failed independent replay');
 const row={arm:arm.id,seed,result:result.result,tiles:patch.length,nodes:result.stats.nodes,backtracks:result.stats.backtracks,values:arm.support.length,elapsedMs,verificationMs,verified:true};rows.push(row);console.log(JSON.stringify(row));
 fs.writeFileSync(`${dir}/${tile}-growth-${arm.id}-s${seed}.json`,JSON.stringify({support:arm.support,patch}));
}
fs.writeFileSync(`${dir}/${tile}-growth.json`,JSON.stringify({tile,protocol:{target,ms,seeds,nodeLimit:100000,score:'Zero in every arm',derivationExcluded:true,order:'Forward for first seed, reversed for second',concurrentExperimentJobs:false},rows},null,2));
