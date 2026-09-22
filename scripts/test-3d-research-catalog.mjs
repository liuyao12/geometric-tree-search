import assert from 'node:assert/strict';
import {access} from 'node:fs/promises';
import {catalog,prepareModel} from '../apps/3d-lattice-tiler/v2/model.js';
import {RESEARCH_TILES,RESEARCH_SUITE_IDS,HISTORICAL_CASE_IDS} from '../apps/3d-lattice-tiler/research-catalog.js';
import {POLYCUBE_GCTS_CANDIDATES} from '../assets/polycube-census-candidates.js';
import {tileSpecs} from '../apps/3d-lattice-tiler/engine.js';
import {prepareVoxelPointModel,verifyVoxelPatch} from '../apps/3d-lattice-tiler/voxel-point-model.js';
import {runExperiment} from '../apps/3d-lattice-tiler/v2/experiment.js';
import {PointGraph,verify} from '../apps/3d-lattice-tiler/v2/search.js';
const rows=catalog();assert.equal(rows.length,54);assert.equal(new Set(rows.map(c=>c.id)).size,54);
assert.equal(RESEARCH_TILES.length,14);assert.equal(RESEARCH_TILES.filter(c=>c.group==='Unresolved polycube research').length,10);
assert.equal(RESEARCH_TILES.filter(c=>c.group==='Grid non-tiling controls').length,3);
assert.equal(RESEARCH_TILES.filter(c=>c.group==='Periodic polycube controls').length,1);
for(const c of RESEARCH_TILES){
 const source=POLYCUBE_GCTS_CANDIDATES.find(r=>r.id===c.sourceId);assert.deepEqual(c.voxels,source.voxels);
 assert.ok(tileSpecs.TILING_REGISTRY[c.id]);assert.ok(tileSpecs.figureCatalog.some(f=>f.mode_key===c.id));
 await access(new URL('../'+c.evidence.split('#')[0],import.meta.url));
 for(const mirrors of [false,true]){
  const m=prepareModel({tile:c.id,radius:1,mirrors}),reference=prepareVoxelPointModel(c.voxels,{mirrors,radius:1});
  assert.deepEqual(m.orientations,reference.orientations);assert.equal(m.required.length,91);
  assert.equal(m.allowReflections,mirrors);assert.deepEqual(m.placementDomain,{kind:'scaled_cubic',translationStep:2});
  assert.ok(m.orientations.every(o=>o.marks.length===0));
  const root={oi:0,translation:[0,0,0]};assert.ok(verifyVoxelPatch(m,[root],{requireTarget:false}).ok);
  assert.equal(verifyVoxelPatch(m,[root,root],{requireTarget:false}).reason,'voxel overlap');
 }
}
assert.equal(RESEARCH_SUITE_IDS.length,5);assert.ok(RESEARCH_SUITE_IDS.every(id=>rows.some(c=>c.id===id)));
assert.deepEqual(HISTORICAL_CASE_IDS,['a2_hat_prism','a2_turtle_prism','buckled_ring','twisted_h','tuning_fork']);
const p10=prepareModel({tile:'polycube_p10_346304',radius:1,mirrors:false}),graph=new PointGraph(p10);
assert.ok(graph.candidates.every(c=>c.translation.every(x=>x%2===0)));graph.verifyDomains();
const collect=async s=>{let last;for await(const e of s)last=e;return last;};
const config={tile:'polycube_p10_346304',radius:1,mirrors:false,timeMs:1500,nodes:30,pairNodes:1};
const free=await collect(runExperiment({...config,mode:'free'}));assert.equal(free.type,'result');assert.ok(free.voxelVerification);
assert.ok(verifyVoxelPatch(free.model,free.placements,{requireTarget:false}).ok);
if(free.result==='finite_exact'){assert.ok(free.voxelVerification.ok);assert.ok(verify(free.model,free.placements).ok);}
const learned=await collect(runExperiment({...config,mode:'gcts',timeMs:300}));assert.equal(learned.type,'result');assert.equal(learned.result,'unknown');assert.equal(learned.marking.accepted,false);
assert.equal((await collect(runExperiment({...config,action:'probe'}))).type,'error');
assert.equal(prepareModel({tile:'cube',radius:1}).required.length,27,'Historical control unchanged');
assert.equal(prepareModel({tile:'a2_turtle_prism',radius:1}).required.length,14,'Slab unchanged');
console.log('PASS 14 research geometries in both catalogues, 10 unresolved/3 obstruction/1 periodic controls, exact voxel model, lattice candidate domain, cold unresolved learning, independent voxel replay, probe guard, and historical IDs.');
