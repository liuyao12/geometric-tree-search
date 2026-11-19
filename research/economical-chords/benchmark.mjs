// Run with node --expose-gc research/economical-chords/benchmark.mjs > trials.jsonl
// All timed trials share one process, with warmup and alternating order within pairs.
import {createHash} from 'node:crypto';
import {createCoronaLearner} from '../../assets/tile-corona-learning.js';
import {makeHexBoundary,solveA2Tiling} from '../../assets/a2-tiling-engine.js';
import {DeepChordMarking} from '../../assets/deep-chord-marking.js';

globalThis.requestAnimationFrame = cb => setImmediate(cb);
const seedFor = i => createHash('sha256').update('gcts-economy/'+i).digest().readUInt32BE(0);
async function trial(catalog,setId,tile,mode,i,target,budget) {
  const marking=new DeepChordMarking(setId,9,{economical:mode==='economical'});
  const totalMarks=marking.stats().supportSites;
  const seed=seedFor(i), root=catalog.materialize(catalog.roots.find(p=>p.tile===tile));
  const trace=createHash('sha256'), boundary=makeHexBoundary(2);
  global.gc?.();
  const start=performance.now();
  const answer=await solveA2Tiling({...catalog.config,boundary,marking,randomSeed:seed,initialPlacements:[root],
    maximize:true,completePointGrowth:true,fixedInitialPlacements:true,branchPolicy:'oldest-frontier',
    requireEdgeSharing:true,targetPlacements:target,nodeLimit:budget,onEvent:e=>{
      if(e.type==='placement')trace.update('+'+e.placements.at(-1).id+'\n');
      if(e.type==='backtrack')trace.update('-'+e.removed.id+'\n');
    }});
  const ms=Math.round(performance.now()-start);
  const reference=new DeepChordMarking(setId,9);
  const passesFull=answer.result==='yes' && answer.placements.every(p=>{
    if(!reference.compatible(p,[],false))return false;
    reference.push(p);return true;
  });
  return {setId,tile,i,seed,mode,target,budget,totalMarks,result:answer.result,achieved:answer.placements.length,
    nodes:answer.stats.nodes,backtracks:answer.stats.backtracks,ms,passesFull,trace:trace.digest('hex')};
}

for(const [setId,tile] of [['hat','hat'],['mixed','hat'],['mixed','turtle']]){
  const catalog=createCoronaLearner(setId);
  for(const mode of ['economical','full'])await trial(catalog,setId,tile,mode,190,30,180);
  for(const [first,count,target,budget] of [[210,8,75,450],[310,4,150,900]]){
    for(let i=first;i<first+count;i++){
      for(const mode of (i%2?['economical','full']:['full','economical'])){
        console.log(JSON.stringify(await trial(catalog,setId,tile,mode,i,target,budget)));
      }
    }
  }
}
