import {validatePointModel,verifyCorona,placementKey} from '../../apps/3d-lattice-tiler/corona-graph.js';
// Independent weighted-point replay; no voxel bitsets, CNF or SAT assignment.
export function verifyPointWindowFrontier(model,placements,fixed=[]){
 validatePointModel(model);
 if(!model.required?.length||model.required.some(p=>p.pos.length!==3||!p.pos.every(Number.isSafeInteger)))throw Error('Invalid required point window');
 if(model.orientations.some(o=>o.marks?.length))throw Error('Expected unmarked window');
 if(placements.some(p=>!Number.isInteger(p.oi)||!model.orientations[p.oi]||p.translation?.length!==3||!p.translation.every(Number.isSafeInteger)))throw Error('Invalid window placement');
 const boundary=verifyCorona(model,[],placements),used=new Set(placements.map(placementKey));
 if(fixed.some(p=>!used.has(placementKey(p))))throw Error('Window lost a fixed placement');
 const totals=new Map();
 for(const p of placements)for(const c of model.orientations[p.oi].cells){const k=c.pos.map((x,i)=>x+p.translation[i]).join();totals.set(k,(totals.get(k)??0)+c.weight);}
 const covered=model.required.filter(p=>totals.get(p.pos.join())===model.capacity).length,coreComplete=covered===model.required.length;
 return {complete:coreComplete&&boundary.frontierViable,coreComplete,covered,required:model.required.length,frontierViable:boundary.frontierViable,deadPoints:boundary.deadPoints,frontierPoints:[...totals.values()].filter(n=>n<model.capacity).length};
}
