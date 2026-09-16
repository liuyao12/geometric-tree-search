import assert from 'node:assert/strict';
import {A2_TILE_LOOPS, FixedA2Marking, FixedTurtleMarking, tileOrientations, solveA2Tiling, makeHexBoundary} from '../assets/a2-tiling-engine.js';
globalThis.requestAnimationFrame = callback => setTimeout(callback, 0);
const root = tile => ({tile, orientation:tileOrientations(tile,A2_TILE_LOOPS[tile])[0], translation:[0,0,0]});
const hat = root('hat');
const marking = new FixedA2Marking(0,{rank:1,tiles:['hat']});
// Explicit Hat fixture: four scalar stripes, with the intervening boundary site zero.
const ones = [[0,0,0],[1,1,-2],[2,2,-4],[3,3,-6],[0,3,-3],[-1,5,-4],[4,1,-5],[0,6,-6]];
assert.deepEqual([...marking.entries(hat)].filter(([,v])=>v===1).map(([k])=>k).sort(),ones.map(p=>`${p}|0`).sort());
assert.equal(marking.entries(hat).get('1,4,-5|0'),0);
assert.equal(marking.entries(hat).get('1,0,-1|0'),0);
assert.equal(marking.entries(hat).get('-1,-1,2|0'),undefined);
assert.equal(new FixedA2Marking(1,{rank:1,tiles:['hat']}).entries(hat).get('-1,-1,2|0'),1);
assert.throws(()=>new FixedA2Marking(1,{rank:3,tiles:['hat']}));
for(const tile of ['turtle','hat'])for(const orientation of tileOrientations(tile,A2_TILE_LOOPS[tile])){
 const model = new FixedA2Marking(1,{rank:1,tiles:[tile]});
 assert.ok([...model.entries({...root(tile),orientation}).values()].every(v=>v===0||v===1));
 assert.equal(model.segments({...root(tile),orientation}).length,4);
}
marking.push(hat);
const before = structuredClone(marking.contacts), shifted = {...hat,translation:[1,0,-1]};
assert.equal(marking.compatible(shifted),false); // Assigned zero conflicts with shifted scalar one.
marking.push(hat);marking.pop(hat);assert.deepEqual(marking.contacts,before);
marking.pop(hat);assert.equal(marking.contacts.size,0);assert.equal(marking.compatible(shifted),true);
for(const rank of [1,3])assert.deepEqual(new FixedA2Marking(1,{rank}).entries(root('turtle')),new FixedTurtleMarking(1,{rank}).entries(root('turtle')));
for(const tiles of [['turtle'],['hat'],['turtle','hat']]){
 const model = new FixedA2Marking(1,{rank:1,tiles});
 const result = await solveA2Tiling({boundary:makeHexBoundary(12),tiles,initialPlacements:[root(tiles[0])],fixedInitialPlacements:true,completePointGrowth:true,allowReflections:tiles.length===1,maximize:true,targetPlacements:12,nodeLimit:3000,marking:model,auditFrontierGraph:true,randomSeed:701});
 assert.equal(result.result,'yes');assert.equal(result.placements.length,12);
 if(tiles.length===2)assert.deepEqual(new Set(result.placements.map(p=>p.tile)),new Set(tiles));
 // Independently replay integer capacities and scalar equality, without compatible()/push().
 const totals = new Map(), values = new Map();let matches=0;
 for(const p of result.placements){
  if(tiles.length===2){const q=p.orientation.symmetry.permutation;assert.equal(((q[0]>q[1])+(q[0]>q[2])+(q[1]>q[2]))%2,0);}
  for(const entry of p.orientation.occupancy.values()){
   const key=entry.point.map((v,i)=>v+p.translation[i]).join(',');const total=(totals.get(key)||0)+entry.weight;
   assert.ok(Number.isInteger(total)&&total<=12);totals.set(key,total);
  }
  for(const [key,value] of model.entries(p)){if(values.has(key)){assert.equal(value,values.get(key));matches++;}values.set(key,value);}
 }
 assert.ok(matches>0);console.log(`${tiles.join('+')}: 12-tile scalar-marked patch, exact replay and frontier graph audit passed`);
}
