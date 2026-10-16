import {solveA2Tiling} from './a2-tiling-engine.js';
import {options,displayPlacement} from './model.js';
import {findSequence} from './flips.js';
globalThis.requestAnimationFrame=callback=>setTimeout(callback,0);
let started=false,placements=[],moves=[],index=0;
const send=event=>postMessage({type:'batch',events:[{...event,placements:placements.map(displayPlacement),backtracks:0,moveCount:index,moveTotal:moves.length}]});
onmessage=async({data})=>{try{
 if(data.type==='start'&&!started){started=true;const result=await solveA2Tiling({...options('trefoil',data.seed),targetPlacements:48,nodeLimit:2000});placements=result.placements;const plan=findSequence(placements);moves=plan.moves;send({type:'start',states:plan.states});return;}
 if(data.type==='next'){
  if(index===moves.length){send({type:'finished',result:moves.length?'sequence':'no-moves'});return;}
  const move=moves[index++];placements=move.next;send({type:'flip',kind:move.kind,ids:move.ids,axis:move.axis,axisPoint:move.axisPoint});
 }
}catch(error){postMessage({type:'error',message:error.message});}};
