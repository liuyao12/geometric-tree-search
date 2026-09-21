import assert from 'node:assert/strict';
import {checkCorona,verifyCorona,add,pointKey} from '../apps/3d-lattice-tiler/corona-graph.js';
import {prepareModel} from '../apps/3d-lattice-tiler/v2/model.js';
import {prepareVoxelPointModel,verifyVoxelPatch} from '../apps/3d-lattice-tiler/voxel-point-model.js';
import {pointSymmetries,neighboringPairs} from '../apps/3d-lattice-tiler/marking-learning.js';
import {POLYCUBE_GCTS_CANDIDATES} from '../assets/polycube-census-candidates.js';
let positives=0,removed=0;
for(const tile of ['cube','a2_turtle_prism','a2_hat_prism','rhombic','p9-20656']){
 const geometric=tile==='p9-20656',record=POLYCUBE_GCTS_CANDIDATES.find(t=>t.id===tile);
 const model=geometric?prepareVoxelPointModel(record.voxels):prepareModel({tile,radius:1,mirrors:true});
 let checked=0;
 for(const pair of neighboringPairs(model,pointSymmetries(model))){
  if(checked++>=4)break;let result;
  for await(const e of checkCorona(model,pair,{nodes:500,dependencyLimit:4000000}))result=e;
  if(result.status!=='valid')continue;
  const core=new Set(pair.flatMap(p=>model.orientations[p.oi].cells.map(c=>pointKey(add(c.pos,p.translation)))));
  const projected=result.placements.filter(p=>model.orientations[p.oi].cells.some(c=>core.has(pointKey(add(c.pos,p.translation)))));
  assert.ok(verifyCorona(model,pair,projected).complete);
  if(geometric)assert.ok(verifyVoxelPatch(model,projected,{requireTarget:false}).ok);
  positives++;removed+=result.placements.length-projected.length;
 }
}
assert.ok(positives>0);assert.ok(removed>0,'Exercise actual removal of non-core placements');
console.log(`PASS projection of ${positives} reference corona witnesses; ${removed} non-core placements removed, all frontiers independently viable.`);
