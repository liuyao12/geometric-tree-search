import { A2_TILE_LOOPS, a2Transform, a2Sub, SparseA2Marking, tileOrientations, makeHexBoundary } from './a2-tiling-engine.js';
export const loops={turtle:A2_TILE_LOOPS.turtle,trefoil:[[1,0,-1],[2,0,-2],[2,1,-3],[0,2,-2],[-1,1,0],[-2,2,0],[-3,2,1],[-2,0,2],[0,-1,1],[0,-2,2],[1,-3,2],[2,-2,0]]};
export const stripes={turtle:[[0,10,1],[2,8,-1],[0,6,-1],[4,12,-1]],trefoil:[[0,6,-1],[4,10,-1],[8,2,-1]]};
export const parity=p=>((p[0]>p[1])+(p[0]>p[2])+(p[1]>p[2]))%2?-1:1;
export const project=([x,y,z])=>[(z-x)*Math.sqrt(3)*2.5,-y*7.5];
const gcd=(a,b)=>{a=Math.abs(a);b=Math.abs(b);while(b)[a,b]=[b,a%b];return a;};
// The three signed line components and three-step extensions from the Turtle
// game. Missing channels are unconstrained; no new zero assignments are added.
export const support=Object.entries(loops).flatMap(([tile,loop])=>stripes[tile].flatMap(([a,b,value])=>{
 const delta=a2Sub(loop[b],loop[a]),n=delta.reduce(gcd),step=delta.map(v=>v/n),component=step.findIndex((v,i)=>step.filter((_,j)=>j!==i).every(w=>v===-2*w));
 return Array.from({length:n+7},(_,i)=>({tile,point:loop[a].map((v,j)=>v+(i-3)*step[j]-loop[0][j]),component,value}));
}));
export function options(mode='trefoil',randomSeed=10){
 const tile=mode==='turtles'?'turtle':'trefoil',orientation=tileOrientations(tile,loops[tile])[0];
 const marking=new SparseA2Marking(support,{label:'Turtle game signed stripe marking'});marking.retainCurrentOnStop=true;marking.trackFailureFootprints=false;
 return {boundary:makeHexBoundary(4),customTiles:loops,tiles:mode==='turtles'?['turtle']:['turtle','trefoil'],placementFilter:p=>mode==='mixed'||p.tile==='turtle',initialPlacements:[{tile,orientation,translation:a2Transform(loops[tile][0],orientation.symmetry),generation:0}],fixedInitialPlacements:true,completePointGrowth:true,rescanAfterBacktrack:true,maximize:true,targetPlacements:128,nodeLimit:20000,randomSeed,marking};
}
// Solver origins are translated to vertex zero; CAD origins remain the original
// canonical coordinates. This rigid mapping preserves faces and handedness.
export function placementMatrix(p){
 const sym=p.orientation.symmetry,origin=loops[p.tile][0],shift=project(a2Sub(p.translation,a2Transform(origin,sym))),u=project(a2Transform([1,0,-1],sym)),v=project(a2Transform([0,1,-1],sym));
 const r00=u[0]/(-5*Math.sqrt(3)),r10=u[1]/(-5*Math.sqrt(3));
 const r01=(v[0]+2.5*Math.sqrt(3)*r00)/(-7.5),r11=(v[1]+2.5*Math.sqrt(3)*r10)/(-7.5),sign=parity(sym.permutation);
 // A shared fine-grid phase puts the seed near the central board cells. It is
 // a display translation, never a constraint on candidate legality.
 return [[r00,r01,0,shift[0]+5*Math.sqrt(3)],[r10,r11,0,shift[1]+15],[0,0,sign,sign<0?4:0],[0,0,0,1]];
}
export const displayPlacement=p=>({id:p.id,tile:p.tile,matrix:placementMatrix(p)});
