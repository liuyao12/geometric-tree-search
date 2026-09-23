import assert from 'node:assert/strict';
import {ATOMS,BASE_ATOMIC_CELLS,ATOMIC_TEMPLATES,TETRA_FEATURES,tetraFeatures,tetraPlanes,tetraBoundary,BOUNDARY_SCALE,dot,cross,sub} from '../3d-reptiles/chair/tetra-relief.js';
import {BASE_MARKS,VARIANTS,FACE_DIRECTIONS,key,apply,chairLeaves,markValue} from '../3d-reptiles/chair/chair44.js';
import {createTetraPointModel,FULL} from '../3d-reptiles/chair/tetra-points.js';
import {createGrowthState,createGrowthStateFromPatch,growOne,shrinkOne,enumerateGrowthCandidates} from '../3d-reptiles/chair/chair-gcts.js';
const bits=ATOMS.map((_,i)=>1n<<BigInt(i));
import {WEDGES,OCCUPANCY_SIGNATURES,CHAMBER_COUNT} from '../3d-reptiles/chair/tetra-atoms.js';
assert.equal(CHAMBER_COUNT,96);
assert.equal(TETRA_FEATURES.filter(f=>f.sign>0).length,16);
assert.equal(TETRA_FEATURES.filter(f=>f.sign<0).length,16);
for(const f of TETRA_FEATURES){
 assert.ok(f.vertices.flat().every(x=>Number.isInteger(x/2)));
 const [a,b,c,d]=f.vertices;assert.equal(Math.abs(dot(sub(b,a),cross(sub(c,a),sub(d,a)))),72);
}
// The rational arrangement generator certifies completeness. Independently
// evaluate every published sample against all possible cube-local wedges.
const wedgePlanes=WEDGES.map(tetraPlanes),represented=new Set();
for(const atom of ATOMS){
 let signature=0n;
 wedgePlanes.forEach((planes,i)=>{
  if(planes.every(([x,y,z,d])=>6*(x*atom.point[0]+y*atom.point[1]+z*atom.point[2])>d*atom.den))signature|=1n<<BigInt(i);
 });
 assert.equal(signature.toString(16),atom.signature);represented.add(atom.signature);
}
assert.deepEqual(represented,new Set(OCCUPANCY_SIGNATURES));
const sig=t=>t.map(key).sort().join(';');
const shapeSignature=features=>features.map(f=>sig(f.vertices)).sort().join('|');
const reversedFeatures=mark=>tetraFeatures(mark).map(f=>({...f,vertices:[...f.vertices.slice(0,3),
 f.vertices[3].map((x,i)=>x-4*f.sign*mark.direction[i])]}));
let facingCases=0;
for(const n of FACE_DIRECTIONS){
 const axes=[0,1,2].filter(i=>!n[i]),marks=[];
 for(const a of [-1,1])for(const b of [-1,1])for(const color of ['red','green','blue']){
  const arrow=[0,0,0];arrow[axes[0]]=a;arrow[axes[1]]=b;marks.push({cell:[0,0,0],direction:n,arrow,color});
 }
 for(const a of marks)for(const entry of marks){
  const b={...entry,cell:n,direction:n.map(x=>-x)};
  assert.equal(shapeSignature(tetraFeatures(a))===shapeSignature(tetraFeatures(b)),key(markValue(a))===key(markValue(b)));
  if(key(markValue(a))===key(markValue(b))){
   assert.equal(shapeSignature(reversedFeatures(a)),shapeSignature(reversedFeatures(b)));
   assert.notEqual(shapeSignature(reversedFeatures(a)),shapeSignature(tetraFeatures(b)));
  }
  facingCases++;
 }
}
// Every actual transformed wedge is covered by the audited cube-local library.
const wedgeLibrary=new Set(WEDGES.map(sig));
for(const variant of VARIANTS)for(const mark of variant.marks)for(const f of tetraFeatures(mark)){
 const cell=[0,1,2].map(i=>Math.floor(f.vertices.reduce((s,p)=>s+p[i],0)/24));
 assert.ok(wedgeLibrary.has(sig(f.vertices.map(p=>p.map((x,i)=>x-6*cell[i])))));
}
// The eight intended green/red hinge pairs still quarter-turn exactly.
const hingePartner=new Map([[0,1],[5,4],[6,8],[9,10],[14,13],[18,21],[19,16],[22,23]]);
for(const g of BASE_MARKS.filter(m=>m.color==='green')){
 const G=tetraFeatures(g)[0].vertices;let hits=0;
 for(const r of [BASE_MARKS[hingePartner.get(BASE_MARKS.indexOf(g))]]){
  const R=tetraFeatures(r)[0].vertices,common=G.slice(0,3).filter(p=>R.slice(0,3).some(q=>key(p)===key(q)));
  if(common.length!==2)continue;const delta=sub(common[1],common[0]);if(dot(delta,delta)!==36)continue;
  const axis=delta.map(v=>v/6);
  for(const sign of [-1,1]){
   const moved=G.map(p=>{const v=sub(p,common[0]),turn=cross(axis,v);return common[0].map((x,i)=>x+axis[i]*dot(axis,v)+sign*turn[i]);});
   if(sig(moved)===sig(R))hits++;
  }
 }
 assert.equal(hits,1);
}
for(const b of BASE_MARKS.filter(m=>m.color==='blue')){
 const [a,c]=tetraFeatures(b).map(f=>f.vertices),common=a.slice(0,3).filter(p=>c.slice(0,3).some(q=>key(p)===key(q)));
 assert.equal(common.length,2);const e=sub(common[1],common[0]);assert.equal(dot(e,e),72);
 const moved=a.map(p=>{const v=sub(p,common[0]);return common[0].map((x,i)=>x+e[i]*dot(e,v)/36-v[i]);});assert.equal(sig(moved),sig(c));
}
// Boundary mesh: exact orientation, no degenerate triangles, edge pairing,
// and volume. Boundary coordinates are integer twelfths.
const edges=new Map();let determinantSum=0;
for(const f of tetraBoundary())for(let i=1;i<f.vertices.length-1;i++){
 const tri=[f.vertices[0],f.vertices[i],f.vertices[i+1]], [a,b,c]=tri;
 assert.ok(cross(sub(b,a),sub(c,a)).some(v=>v));determinantSum+=dot(a,cross(b,c));
 for(let j=0;j<3;j++){const a=key(tri[j]),b=key(tri[(j+1)%3]),id=[a,b].sort().join('|'),e=edges.get(id)??[0,0];e[0]++;e[1]+=a<b?1:-1;edges.set(id,e);}
}
assert.equal(determinantSum,7*6*BOUNDARY_SCALE**3);
assert.ok([...edges.values()].every(([count,balance])=>count===2&&balance===0));
// Geometric occupancy is rotation covariant, including every corner contact.
const globalPoints=t=>new Set(t.flatMap(({cell,mask})=>ATOMS.flatMap((a,i)=>mask&bits[i]?[`${key(a.point.map((v,j)=>v+a.den*cell[j]))}/${a.den}`]:[])));
const rootPoints=globalPoints(BASE_ATOMIC_CELLS);
for(const v of VARIANTS)assert.deepEqual(globalPoints(ATOMIC_TEMPLATES[v.id]),new Set([...rootPoints].map(k=>{
 const [point,d]=k.split('/'),den=Number(d);
 return `${key(apply(v.rotation,point.split(',').map(x=>+x-den)).map(x=>x+den))}/${den}`;
})));
const model=createTetraPointModel(),root={variantId:0,origin:[0,0,0],generation:0},graph=model.graphFor([root]);
// Independent exhaustive translation box, then exact positive-point alignment.
const exhaustive=new Set();
for(const v of VARIANTS)for(let x=-3;x<=3;x++)for(let y=-3;y<=3;y++)for(let z=-3;z<=3;z++){
 const tile=model.compile({variantId:v.id,origin:[x,y,z]});
 const touches=tile.voxels.some(c=>graph.index.occupancy.has(c.id)&&(c.mask&(FULL^graph.index.occupancy.get(c.id))));
 if(touches&&model.isLegal(tile,graph.index))exhaustive.add(tile.id);
}
assert.deepEqual(new Set(graph.candidates.keys()),exhaustive);
for(const node of graph.frontier.values()){
 const [,cell,atom]=node.id.split(':');
 const independently=new Set([...graph.candidates].filter(([,p])=>model.compile(p).voxels.some(v=>v.id===cell&&(v.mask&bits[+atom]))).map(([id])=>id));
 assert.deepEqual(node.candidates,independently);
}
model.clearCache();
for(const level of [0,1,2]){
 const patch=chairLeaves(level,[-3,4,-2],VARIANTS[7].rotation);model.indexState(patch);
 const state=createGrowthStateFromPatch(patch,'relief-tetra'),next=growOne(state);
 assert.equal(next.placements.length,patch.length+1);assert.deepEqual(next.placements.slice(0,patch.length),state.placements);assert.strictEqual(shrinkOne(next),state);
}
let state=createGrowthState(2,'relief-tetra');
for(let i=0;i<100&&!state.complete;i++){
 const before=JSON.stringify({...state,history:undefined}),previous=state;state=growOne(state);
 assert.equal(JSON.stringify({...previous,history:undefined}),before);assert.strictEqual(shrinkOne(state),previous);model.indexState(state.placements);
 assert.equal(enumerateGrowthCandidates(state).dead,false);
}
assert.equal(state.status,'consistent finite patch');assert.equal(state.placements.length,64);assert.ok(state.solverBacktracks>0);
console.log(JSON.stringify({samples:ATOMS.length,facingCases,volume:7,rootCandidates:graph.candidates.size,tiles:64,branches:state.branchDecisions,backtracks:state.solverBacktracks,forced:state.forcedPlacements}));
