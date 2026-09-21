import assert from 'node:assert/strict';
import {pairOrbits,transportPatch} from './lib/3d-pair-orbits.mjs';
import {prepareVoxelPointModel} from '../apps/3d-lattice-tiler/voxel-point-model.js';
import {checkCorona,verifyCorona,add,sub,placementKey} from '../apps/3d-lattice-tiler/corona-graph.js';
import {POLYCUBE_GCTS_CANDIDATES} from '../assets/polycube-census-candidates.js';
const signature=cells=>cells.map(c=>`${c.pos}:${c.weight}`).sort().join('|');
for(const [name,voxels] of [['cube',[[0,0,0]]],...POLYCUBE_GCTS_CANDIDATES.map(t=>[t.id,t.voxels])]){
 const model=prepareVoxelPointModel(voxels),orbit=pairOrbits(model),covered=new Set();
 for(const group of orbit.groups)for(const member of group.members){
  assert.ok(!covered.has(member.index));covered.add(member.index);
  const {gi,origin,swap}=member.transport,g=orbit.transforms[gi],seeds=swap?[...group.pair].reverse():group.pair;
  for(let i=0;i<2;i++){
   const source=seeds[i],target=member.pair[i];
   const geometric=model.orientations[source.oi].cells.map(c=>({pos:sub(g.transform(add(c.pos,source.translation)),origin),weight:c.weight}));
   const encoded=model.orientations[target.oi].cells.map(c=>({pos:add(c.pos,target.translation),weight:c.weight}));
   assert.equal(signature(geometric),signature(encoded));
  }
  assert.deepEqual(transportPatch(group.pair,member,orbit.transforms),member.pair);
 }
 assert.equal(covered.size,orbit.pairs.length);
 if(name==='cube'){
  assert.equal(orbit.groups.length,3);assert.equal(orbit.pairs.length,26);
  for(const group of orbit.groups){let result;for await(const e of checkCorona(model,group.pair))result=e;assert.equal(result.status,'valid');for(const member of group.members){const patch=transportPatch(result.placements,member,orbit.transforms);assert.equal(new Set(patch.map(placementKey)).size,patch.length);assert.ok(verifyCorona(model,member.pair,patch).complete);}}
 }
 console.log(`${name}: ${orbit.pairs.length} pairs / ${orbit.groups.length} exact orbits; every weighted seed transport checked.`);
}
