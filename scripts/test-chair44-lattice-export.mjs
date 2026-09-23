import assert from 'node:assert/strict';
import fs from 'node:fs';
import {chair44PointExport} from '../3d-reptiles/chair/lattice-export.js';
import {ATOMS,CHAMBERS} from '../3d-reptiles/chair/tetra-atoms.js';
import {ATOMIC_TEMPLATES,cross,dot} from '../3d-reptiles/chair/tetra-relief.js';
import {createTetraPointModel} from '../3d-reptiles/chair/tetra-points.js';
import {chairLeaves} from '../3d-reptiles/chair/chair44.js';
import {prepareModel} from '../apps/3d-lattice-tiler/v2/model.js';
import {prepareExactPointModel} from '../apps/3d-lattice-tiler/exact-point-import.js';
import {GrowthGraph,grow,verifyGrowth} from '../apps/3d-lattice-tiler/growth-search.js';
import {pointSymmetries,OnlineMarking} from '../apps/3d-lattice-tiler/marking-learning.js';
import {allowedTranslation} from '../apps/3d-lattice-tiler/corona-graph.js';
const data=chair44PointExport(),stored=JSON.parse(fs.readFileSync(new URL('../3d-reptiles/chair/chair44-exact-points.json',import.meta.url),'utf8'));
assert.deepEqual(stored,data);
const model=prepareModel({tile:'chair44_relief',radius:1,mirrors:false});
assert.deepEqual(model,prepareModel({tile:'custom',custom:stored,radius:1,mirrors:false}));
assert.equal(model.orientations.length,24);assert.equal(model.capacity,18);assert.equal(model.pointDomain.sites.length,55);
assert.equal(allowedTranslation(model,[8,0,0]),false);assert.equal(allowedTranslation(model,[96,0,0]),true);
assert.throws(()=>prepareExactPointModel(data,{mirrors:true}),/proper rotations/);
const bad=structuredClone(data);bad.point_model.orientations[0].cells[0].weight=.5;assert.throws(()=>prepareExactPointModel(bad),/integer point weights/);
// Independently integrate each occupied chamber, rather than using wedge counts.
const chamberVolumes=CHAMBERS.map(c=>c.faces.reduce((sum,f)=>sum+f.slice(1,-1).reduce((s,_,i)=>s+dot(f[0],cross(f[i+1],f[i+2])),0),0));
for(const [oi,template] of ATOMIC_TEMPLATES.entries()){
 const o=model.orientations[oi],weights=new Map(o.cells.map(c=>[c.pos.join(),c.weight]));
 for(const {cell,mask} of template){
  const numerator=CHAMBERS.reduce((s,c,i)=>s+(mask&(1n<<BigInt(c.atom))?chamberVolumes[i]:0),0);
  const weight=18*numerator/(6*12**3);assert.ok(Number.isInteger(weight));
  for(let axis=0;axis<3;axis++)for(const sign of [-1,1])assert.equal(weights.get(cell.map((v,i)=>96*v+48+(i===axis?sign:0)).join()),weight);
 }
 const edges=new Map();let det=0;
 for(const face of o.faces){const [a,b,c]=face.map(i=>o.vertices[i]);det+=dot(a,cross(b,c));for(let i=0;i<3;i++){const k=[face[i],face[(i+1)%3]].sort((a,b)=>a-b).join();edges.set(k,(edges.get(k)??0)+1);}}
 assert.equal(det,7*6*96**3);assert.ok([...edges.values()].every(n=>n===2));
}
const symmetries=pointSymmetries(model);assert.equal(symmetries.length,24);
const learner=new OnlineMarking(model,symmetries,{extent:0});assert.equal(learner.slots.length,11400);
const source=createTetraPointModel(),seed={oi:0,translation:[0,0,0]},sourceRoot={variantId:0,origin:[0,0,0]},sourceIndex=source.indexState([sourceRoot]);
const occupied=new Map(model.orientations[0].cells.map(c=>[c.pos.join(),c.weight]));let pairs=0;
for(let oi=0;oi<24;oi++)for(let x=-3;x<=3;x++)for(let y=-3;y<=3;y++)for(let z=-3;z<=3;z++){
 const translation=[x,y,z].map(v=>v*96);
 const legal=model.orientations[oi].cells.every(c=>(occupied.get(c.pos.map((v,i)=>v+translation[i]).join())??0)+c.weight<=18);
 assert.equal(legal,source.isLegal(source.compile({variantId:oi,origin:[x,y,z]}),sourceIndex));pairs++;
}
const graph=new GrowthGraph(model,{fixed:[seed]});graph.apply(seed,{root:true});graph.audit();
assert.notEqual(graph.schedule().kind,'closed','Full occupancy bits alone must not produce a closed seed');
const actual=new Set([...graph.candidates.values()].filter(c=>c.valid&&c.points.size).map(c=>`${c.oi}@${c.translation.map(x=>x/96)}`));
assert.deepEqual(actual,new Set(source.graphFor([sourceRoot]).candidates.keys()));
const before=graph.descriptors(),next=[...graph.schedule().point.incident].find(c=>c.valid),undo=graph.apply(next);graph.rollback(undo);graph.audit();assert.deepEqual(graph.descriptors(),before);
for(const level of [1,2]){
 const patch=chairLeaves(level).map(p=>({oi:p.variantId,translation:p.origin.map(x=>96*x)}));
 assert.ok(verifyGrowth(model,patch,{seed:patch[0],frontier:false}).ok);
}
let result;for await(const e of grow(model,{mode:'free',seed:10,targetTiles:8,timeMs:60000}))if(e.type==='result')result=e;
assert.equal(result.result,'growth_checkpoint');assert.equal(result.placements.length,8);assert.ok(result.verification.ok);assert.ok(result.stats.backtracks>0);
source.indexState(result.placements.map(p=>({variantId:p.oi,origin:p.translation.map(x=>x/96)})));
console.log(JSON.stringify({pairs,rootCandidates:actual.size,pointsPerTile:model.orientations[0].cells.length,tiles:8,branches:result.stats.branches,backtracks:result.stats.backtracks,frontierVerified:true}));
