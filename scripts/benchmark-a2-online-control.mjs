#!/usr/bin/env node
import fs from 'node:fs';
import {FixedA2Marking,SparseA2Marking,NoA2Marking,solveA2Tiling,makeHexBoundary} from '../assets/a2-tiling-engine.js';
import {createCoronaLearner} from '../assets/tile-corona-learning.js';
import {NeutralMarking} from './experiment-a2-online-pairs.mjs';
import {onIndex3} from './experiment-a2-corona-consensus.mjs';
import {workflowModel} from './experiment-a2-corona-workflow.mjs';
import {verifyGrowth} from '../apps/3d-lattice-tiler/growth-search.js';
const a=Object.fromEntries(process.argv.slice(2).map(x=>x.replace(/^--/,'').split('='))),dir=a.out??'/tmp/a2-online-control',target=+(a.target??1000),ms=+(a.ms??60000),seeds=(a.seeds??'1,3').split(',').map(Number);
fs.mkdirSync(dir,{recursive:true});const learner=createCoronaLearner('turtle',{lattice:'turtle-sublattice'}),known=new FixedA2Marking(1,{rank:3,tiles:['turtle'],pointFilter:onIndex3}).support;
const ids=(a.arms??'unmarked,known,strict-learned').split(','),label=a.label??'control';
if(ids.some(id=>!['unmarked','known','strict-learned'].includes(id)))throw Error('Unknown benchmark arm');
const learned=ids.includes('strict-learned')?JSON.parse(fs.readFileSync(a.learned??'/tmp/a2-online-pairs/turtle-online-pair-s1.json')).snapshots.at(-1).support:[];
const allArms=[{id:'unmarked',support:[]},{id:'known',support:known},{id:'strict-learned',support:learned}];const arms=allArms.filter(x=>ids.includes(x.id)),rows=[];
for(const [i,seed]of seeds.entries())for(const arm of i%2?[...arms].reverse():arms){
 const started=performance.now(),stopToken={stop:false},timer=setTimeout(()=>{stopToken.stop=true;},ms);let result;
 try{result=await solveA2Tiling({boundary:makeHexBoundary(30),tiles:['turtle'],allowReflections:true,latticePointFilter:onIndex3,initialPlacements:learner.roots.map(learner.materialize),fixedInitialPlacements:true,completePointGrowth:true,maximize:true,targetPlacements:target,nodeLimit:1000000,randomSeed:seed,marking:arm.support.length?new (a.score==='demo'?SparseA2Marking:NeutralMarking)(arm.support):new NoA2Marking(),stopToken});}finally{clearTimeout(timer);}
 const elapsedMs=performance.now()-started,patch=result.placements.map(p=>({oi:p.orientation.index,translation:p.translation})),verifyStart=performance.now(),verification=verifyGrowth(workflowModel('turtle',arm.support),patch),verificationMs=performance.now()-verifyStart;
 if(!verification.ok)throw Error('Independent growth replay failed');
 const row={arm:arm.id,seed,target,ms,result:result.result,tiles:patch.length,nodes:result.stats.nodes,backtracks:result.stats.backtracks,values:arm.support.length,elapsedMs,verificationMs,verified:true};rows.push(row);console.log(JSON.stringify(row));fs.writeFileSync(`${dir}/${label}-${arm.id}-s${seed}-growth.json`,JSON.stringify({support:arm.support,patch}));
}
fs.writeFileSync(`${dir}/${label}-growth.json`,JSON.stringify({protocol:{target,ms,seeds,score:a.score==='demo'?'normal GCTS-I marking score':'zero in every arm',lattice:'index3',tile:'turtle',reflections:true,knownExtent:1,sequential:true,derivationExcluded:true},rows},null,2));
