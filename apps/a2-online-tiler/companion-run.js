import {fill,rng} from '../../research/deterministic-a2/search.mjs?v=companion-tiles';
import {worldPoint,worldMark} from '../../research/deterministic-a2/model.mjs';
import {board,tileSet} from './companion-model.js';
import {onlineMarks} from './companion-learning.js';

export function runExperiment({ids,first,radius,seed,learning,budget=15000},emit) {
  const model=tileSet(ids),root=model.types.get(first).root;
  const learned=learning?onlineMarks(model):null;
  const screen=p=>p.slice(0,2).map(Number);
  let previous=0,nodes=0,backtracks=0,ring=0;
  function report(status,stack,n,b) {
    const marks=[...(learned?.table.values()??[])];
    const placements=stack.map(p=>({
      tile:p.tile,loop:model.types.get(p.tile).localLoop.map(q=>screen(worldPoint(p,q))),
      marks:marks.filter(m=>m.tile===p.tile).map(m=>{
        const w=worldMark(p,m);return [...screen(w.point),w.axis,w.value];
      })
    }));
    emit({status,ring,nodes:nodes+n,backtracks:backtracks+b,placements,
      ...(learned?.stats()??{revisions:0,assignments:0,tests:0})});
  }
  report('searching',[root],0,0);
  for(ring=0;ring<=radius;ring++) {
    const failed=new Set(),targets=board(ring);
    let result,last=[root];
    do {
      const marks=[...(learned?.table.values()??[])];
      result=fill(model,targets,[root],marks,rng(seed),budget-nodes,learned?.consider,failed,new Set(),
        (stack,n,b)=>{
          last=stack;
          if(performance.now()-previous>=100) {
            report('searching',stack,n,b);previous=performance.now();
          }
        });
      nodes+=result.nodes;backtracks+=result.backtracks;
      if(result.status==='revised') report('revised',[root],0,0);
    } while(result.status==='revised');
    const status=result.status==='covered' && ring<radius?'ring':result.status;
    report(status,result.status==='covered'?result.placements:last,0,0);
    if(result.status!=='covered') return;
  }
}
