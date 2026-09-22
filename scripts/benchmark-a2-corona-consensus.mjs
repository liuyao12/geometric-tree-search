#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import {FixedA2Marking,solveA2Tiling,makeHexBoundary,tileOrientations,A2_TILE_LOOPS} from '../assets/a2-tiling-engine.js';
import {pointModel,onIndex3,verifyCoronaPatch} from './experiment-a2-corona-consensus.mjs';
import {verifyGrowth} from '../apps/3d-lattice-tiler/growth-search.js';
globalThis.requestAnimationFrame??=cb=>setImmediate(cb);
const args=Object.fromEntries(process.argv.slice(2).map(s=>s.replace(/^--/,'').split('=')));
const input=args.input??'/tmp/a2-corona-consensus/turtle-r3-index3-c2.json',out=args.out??'/tmp/a2-corona-consensus',target=+(args.target??100),ms=+(args.ms??10000),nodeLimit=+(args.nodes??50000),seeds=(args.seeds??'1,3,10').split(',').map(Number);
const source=JSON.parse(fs.readFileSync(input));if(!source.complete||!source.solutions)throw Error('Only complete, nonempty corona enumerations may be promoted');
const {tile,rank,lattice,support,radius}=source,pointFilter=lattice==='index3'?onIndex3:null;
// Use the original marking's score in BOTH arms. Only legal candidate removal
// changes; extra support cannot win merely by changing preference scores.
class ConsensusMarking extends FixedA2Marking{
 constructor(extended){super(1,{rank,tiles:[tile],pointFilter});this.ranking=new FixedA2Marking(1,{rank,tiles:[tile],pointFilter});if(extended)this.support=support;}
 push(p){super.push(p);this.ranking.push(p);}
 pop(p){super.pop(p);this.ranking.pop(p);}
 reset(context=[]){this.contacts=new Map();this.ranking.reset();for(const p of context)this.push(p);}
 score(p){return this.ranking.score(p);}
}
const base=pointModel({tile,rank,lattice}),extended=pointModel({tile,rank,lattice,support});
const validation={coronas:source.patches.length,baseValid:0,extendedCompatible:0,extendedFrontierViable:0};
for(const patch of source.patches){if(verifyCoronaPatch(base,patch,radius).ok)validation.baseValid++;if(verifyGrowth(extended,patch,{frontier:false}).ok)validation.extendedCompatible++;if(verifyGrowth(extended,patch).ok)validation.extendedFrontierViable++;}
const orientations=tileOrientations(tile,A2_TILE_LOOPS[tile]),rows=[];
for(const [i,seed] of seeds.entries())for(const kind of i%2?['extended','known']:['known','extended']){
 const marking=new ConsensusMarking(kind==='extended'),stopToken={stop:false},started=performance.now();const timer=setTimeout(()=>{stopToken.stop=true;},ms);
 let result;try{result=await solveA2Tiling({boundary:makeHexBoundary(20),tiles:[tile],allowReflections:true,initialPlacements:[{tile,orientation:orientations[0],translation:[0,0,0]}],fixedInitialPlacements:true,completePointGrowth:true,latticePointFilter:pointFilter,maximize:true,targetPlacements:target,nodeLimit,randomSeed:seed,marking,stopToken});}finally{clearTimeout(timer);}
 const elapsedMs=performance.now()-started,patch=result.placements.map(p=>({oi:p.orientation.index,translation:p.translation}));
 const validationStarted=performance.now(),originalCheck=verifyGrowth(base,patch),extendedCheck=verifyGrowth(extended,patch);
 const row={kind,seed,target,budgetMs:ms,nodeLimit,result:result.result,tiles:patch.length,elapsedMs,verificationMs:performance.now()-validationStarted,nodes:result.stats.nodes,backtracks:result.stats.backtracks,markingPrunes:result.stats.prunes,originalCompatible:originalCheck.ok,extendedCompatible:verifyGrowth(extended,patch,{frontier:false}).ok,extendedFrontierViable:extendedCheck.frontierViable};
 if(result.result==='yes'&&!(kind==='extended'?extendedCheck:originalCheck).ok)throw Error('Growth result failed independent replay');
 rows.push(row);console.log(JSON.stringify(row));
}
const summary={tile,rank,lattice,radius,compaction:source.compaction??null,source:{complete:source.complete,solutions:source.solutions,nodes:source.nodes,elapsedMs:source.elapsedMs,baseValues:source.baseValues,commonValues:source.commonValues,addedValues:source.addedValues},validation,protocol:{target,ms,nodeLimit,seeds,allowReflections:true,knownExtent:1,ordering:'Identical original-marking score in both arms; shared GCTS-I engine; arm order alternates',trainingChargedSeparately:true},rows};
fs.mkdirSync(out,{recursive:true});fs.writeFileSync(path.join(out,`${tile}-r${rank}-${lattice}-c${radius}${source.compaction?'-compact':''}-benchmark-t${target}.json`),JSON.stringify(summary,null,2));console.log(JSON.stringify({validation}));
