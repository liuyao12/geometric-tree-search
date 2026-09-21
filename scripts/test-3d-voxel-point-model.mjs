import assert from 'node:assert/strict';
import {prepareVoxelPointModel,verifyVoxelPatch} from '../apps/3d-lattice-tiler/voxel-point-model.js';
import {pointSymmetries,neighboringPairs,learnMarking} from '../apps/3d-lattice-tiler/marking-learning.js';
import {CoronaGraph,allowedTranslation} from '../apps/3d-lattice-tiler/corona-graph.js';
import {PointGraph,search,verify} from '../apps/3d-lattice-tiler/v2/search.js';
import {POLYCUBE_GCTS_CANDIDATES} from '../assets/polycube-census-candidates.js';
const collect=async stream=>{let last;for await(const e of stream)last=e;return last;};
for(const voxels of [[[0,0,0]],[[0,0,0],[1,0,0],[0,1,0]],POLYCUBE_GCTS_CANDIDATES[0].voxels]){
 const model=prepareVoxelPointModel(voxels),root={oi:0,translation:[0,0,0]},weights=new Map(model.orientations[0].cells.map(c=>[c.pos.join(),c.weight]));
 let tested=0;
 for(let oi=0;oi<model.orientations.length;oi++)for(let x=-3;x<=3;x++)for(let y=-3;y<=3;y++)for(let z=-3;z<=3;z++){
  const p={oi,translation:[2*x,2*y,2*z]};
  const pointLegal=model.orientations[oi].cells.every(c=>(weights.get(c.pos.map((v,i)=>v+p.translation[i]).join())??0)+c.weight<=8);
  assert.equal(pointLegal,verifyVoxelPatch(model,[root,p],{requireTarget:false}).ok);tested++;
 }
 const syms=pointSymmetries(model);assert.equal(syms.length,24);
 for(const pair of neighboringPairs(model,syms))assert.ok(verifyVoxelPatch(model,pair,{requireTarget:false}).ok);
 assert.equal(allowedTranslation(model,[1,0,0]),false);assert.equal(allowedTranslation(model,[2,0,0]),true);
 const graph=new PointGraph(model);assert.ok(graph.candidates.every(c=>c.translation.every(x=>x%2===0)));
 assert.equal(verify(model,[{oi:0,translation:[1,0,0]}]).reason,'translation leaves scaled lattice');
 assert.throws(()=>new CoronaGraph({...model,placementDomain:{kind:'scaled_cubic',translationStep:0}}),/translation step/);
 console.log(`PASS ${voxels.length}-voxel model: ${tested} pair comparisons agree exactly with independent voxel nonoverlap.`);
}
const cube=prepareVoxelPointModel([[0,0,0]]),learned=await collect(learnMarking(cube,{timeMs:30000}));
assert.ok(learned.marking.accepted);assert.equal(learned.marking.counts.unresolved,0);
for(const row of learned.marking.evidence)if(row.status==='valid')assert.ok(verifyVoxelPatch(cube,row.placements,{requireTarget:false}).ok);
const grown=await collect(search(learned.model,{mode:'gcts',learnedRestriction:true,timeMs:5000}));assert.equal(grown.result,'finite_exact');assert.ok(verify(learned.model,grown.placements).ok);assert.ok(verifyVoxelPatch(cube,grown.placements).ok);
console.log('PASS shared learner and marked search on the voxel-faithful model, with independent geometric replay.');
