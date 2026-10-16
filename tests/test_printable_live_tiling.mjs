import assert from 'node:assert/strict';
import {solveA2Tiling,tileOrientations,a2Transform,a2Sub} from '../turtle-trefoil-printables/search/a2-tiling-engine.js';
import {options,loops,support,placementMatrix,project,parity} from '../turtle-trefoil-printables/search/model.js';
globalThis.requestAnimationFrame=cb=>setTimeout(cb,0);
const weights={turtle:[6,4,9,4,3,4,9,4,3,8,3,8,3,4],trefoil:[9,4,3,4,9,4,3,4,9,4,3,4]};
for(const [tile,loop] of Object.entries(loops)){
 const identity=tileOrientations(tile,loop)[0];
 loop.forEach((p,i)=>assert.equal(identity.occupancy.get(a2Sub(p,loop[0]).join(',')).weight,weights[tile][i]));
}
for(const [tile,loop] of Object.entries(loops))for(const orientation of tileOrientations(tile,loop)){
 const p={tile,orientation,translation:[4,-7,3]},m=placementMatrix(p);
 for(const v of loop){
  const local=project(v),draw=[0,1].map(i=>m[i][0]*local[0]+m[i][1]*local[1]+m[i][3]);
  const world=a2Transform(a2Sub(v,loop[0]),orientation.symmetry).map((x,i)=>x+p.translation[i]);
  const expected=project(world).map((x,i)=>x+[5*Math.sqrt(3),15][i]);
  assert(draw.every((x,i)=>Math.abs(x-expected[i])<1e-8));
 }
 assert(Math.abs(m[0][0]*m[1][1]-m[0][1]*m[1][0]-m[2][2])<1e-8);
}
function verify(placements){
 const totals=new Map(),marks=new Map(),ids=new Set();
 for(const p of placements){
  assert(!ids.has(p.id));ids.add(p.id);
  for(const [key,e] of p.occupancy){assert(Number.isInteger(e.weight));const value=(totals.get(key)||0)+e.weight;assert(value<=12);totals.set(key,value);}
  const s=p.orientation.symmetry;
  for(const mark of support.filter(m=>m.tile===p.tile)){
   const point=s.permutation.map(i=>s.sign*mark.point[i]).map((v,i)=>v+p.translation[i]);
   const key=point.join(',')+'|'+s.permutation.indexOf(mark.component),value=mark.value*parity(s.permutation);
   if(marks.has(key))assert.equal(marks.get(key),value);marks.set(key,value);
  }
 }
}
for(const mode of ['turtles','trefoil','mixed']){
 let prior=[],changes=0;
 const r=await solveA2Tiling({...options(mode),targetPlacements:16,nodeLimit:100,auditFrontierGraph:true,onEvent:e=>{
  if(!['start','placement','backtrack'].includes(e.type))return;
  verify(e.placements);const ids=e.placements.map(p=>p.id);
  if(e.type==='placement'){assert.deepEqual(ids.slice(0,-1),prior);changes++;}
  if(e.type==='backtrack')assert.deepEqual(ids,prior.slice(0,-1));prior=ids;
 }});
 assert.equal(r.result,'yes');assert.equal(r.placements.length,16);assert.equal(changes,15);
 if(mode==='trefoil')assert.equal(r.placements.filter(p=>p.tile==='trefoil').length,1);
 console.log(mode,'16-tile checkpoint: independent t/m replay and full frontier audit passed');
}
let previous=[],removals=0;const stopToken={stop:false};
const result=await solveA2Tiling({...options('mixed',1),targetPlacements:96,nodeLimit:150,auditFrontierGraph:true,stopToken,onEvent:e=>{
 if(!['start','placement','backtrack'].includes(e.type))return;
 verify(e.placements);const ids=e.placements.map(p=>p.id);
 if(e.type==='backtrack'){assert.deepEqual(ids,previous.slice(0,-1));assert.equal(e.removed.id,previous.at(-1));removals++;if(removals===2)stopToken.stop=true;}
 previous=ids;
}});
assert.equal(removals,2);assert.equal(result.result,'unknown');
console.log('Mixed seed 1: two genuine DFS backtracks and exact prefix rollback verified');
