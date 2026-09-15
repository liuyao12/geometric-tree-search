import { solveA2Tiling, makeHexBoundary } from './a2-tiling-engine.js';
import { TURTLE, makeMarking, verifyPatch } from './turtle-point-learning.js';
// The shared engine yields once per placement. Workers have no window RAF.
self.requestAnimationFrame = callback => setTimeout(()=>callback(performance.now()), 25);
let paused = false, resume = null;
self.onmessage = async ({data}) => {
  if (data.type === 'pause') { paused = true; return; }
  if (data.type === 'resume') { paused = false; resume?.(); resume = null; return; }
  if (data.type !== 'start') return;
  try {
    const frozen = data.frozen, started = performance.now();
    let forced = 0, branches = 0;
    const compact = placements => placements.map(p=>({tile:p.tile,orientation:{index:p.orientation.index,symmetry:p.orientation.symmetry},translation:p.translation,loop:p.loop}));
    const result = await solveA2Tiling({ boundary: makeHexBoundary(12), tiles: ['turtle'], maximize: true,
      targetPlacements: 48, nodeLimit: 1500, randomSeed: frozen.seed, marking: makeMarking(frozen),
      initialPlacements: [{tile:'turtle',orientation:TURTLE,translation:[0,0,0]}],
      waitForSearchDemand: async()=>{if(paused) await new Promise(resolve=>{resume=resolve;});},
      onEvent: e=>{
        if (e.type === 'placement') { if(e.forced) forced++;else branches++; }
        if (['placement','backtrack','finished'].includes(e.type)) self.postMessage({type:'frame',placements:compact(e.placements),nodes:e.nodes,backtracks:e.backtracks,forced,branches,prunes:e.marking.prunes});
      }
    });
    const placements=compact(result.placements), verification=verifyPatch(frozen,placements);
    self.postMessage({type:'done',placements,verification,stats:result.stats,forced,branches,result:result.result,elapsedMs:performance.now()-started});
  } catch(error) { self.postMessage({type:'error',message:error.message}); }
};
