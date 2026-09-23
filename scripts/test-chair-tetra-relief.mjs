import assert from 'node:assert/strict';
import {ATOMS,BASE_ATOMIC_CELLS,ATOMIC_TEMPLATES,TETRA_FEATURES,tetraFeatures,tetraPlanes,tetraBoundary,dot,cross,sub} from '../3d-reptiles/chair/tetra-relief.js';
import {BASE_MARKS,VARIANTS,key,apply,chairLeaves} from '../3d-reptiles/chair/chair44.js';
import {createTetraPointModel,FULL} from '../3d-reptiles/chair/tetra-points.js';
import {createGrowthState,createGrowthStateFromPatch,growOne,shrinkOne,enumerateGrowthCandidates} from '../3d-reptiles/chair/chair-gcts.js';
const bits=ATOMS.map((_,i)=>1n<<BigInt(i));
const volume144=mask=>ATOMS.reduce((s,a,i)=>s+(mask&bits[i]?a.volume[0]*144/a.volume[1]:0),0);
assert.equal(volume144(FULL),144);
assert.equal(BASE_ATOMIC_CELLS.reduce((s,c)=>s+volume144(c.mask),0),7*144);
assert.equal(TETRA_FEATURES.filter(f=>f.sign>0).length,16);
assert.equal(TETRA_FEATURES.filter(f=>f.sign<0).length,16);
for(const f of TETRA_FEATURES){
 assert.ok(f.vertices.flat().every(Number.isInteger));
 const [a,b,c,d]=f.vertices;assert.equal(Math.abs(dot(sub(b,a),cross(sub(c,a),sub(d,a)))),9);
}
// Independent exact arrangement audit: every chamber lies on one side of every
// possible cube-face tetrahedron plane. Their disjoint signatures and exact
// total volume certify a complete partition up to boundaries of zero volume.
const planes=new Map();
for(let axis=0;axis<3;axis++)for(const side of [0,1]){
 const other=[0,1,2].filter(i=>i!==axis);
 const corners=[[0,0],[3,0],[3,3],[0,3]].map(([x,y])=>{const p=[0,0,0];p[axis]=3*side;p[other[0]]=x;p[other[1]]=y;return p;});
 for(let omit=0;omit<4;omit++){
  const tri=corners.filter((_,i)=>i!==omit),apex=[0,1,2].map(i=>i===axis?1+side:tri.reduce((s,v)=>s+v[i],0)/3);
  for(const p of tetraPlanes([...tri,apex]))planes.set(key(p),p);
 }
}
const signatures=new Set();
for(const atom of ATOMS){
 const vertices=atom.faces.flat(),signature=[];
 for(const [x,y,z,d] of planes.values()){
  const side=Math.sign(x*atom.point[0]+y*atom.point[1]+z*atom.point[2]-80*d);assert.notEqual(side,0);
  for(const v of vertices)assert.ok(side*(x*v[0]+y*v[1]+z*v[2]-4*d)>=0);
  signature.push(side);
 }
 assert.ok(!signatures.has(key(signature)));signatures.add(key(signature));
}
const sig=t=>t.map(key).sort().join(';');
// Every green cut quarter-turns exactly onto a red bump along a whole leg.
for(const g of BASE_MARKS.filter(m=>m.color==='green')){
 const G=tetraFeatures(g)[0].vertices;let hits=0;
 for(const r of BASE_MARKS.filter(m=>m.color==='red')){
  const R=tetraFeatures(r)[0].vertices,common=G.slice(0,3).filter(p=>R.slice(0,3).some(q=>key(p)===key(q)));
  if(common.length!==2)continue;const delta=sub(common[1],common[0]);if(dot(delta,delta)!==9)continue;
  const axis=delta.map(v=>v/3);
  for(const sign of [-1,1]){
   const moved=G.map(p=>{const v=sub(p,common[0]),turn=cross(axis,v);return common[0].map((x,i)=>x+axis[i]*dot(axis,v)+sign*turn[i]);});
   if(sig(moved)===sig(R))hits++;
  }
 }
 assert.equal(hits,1);
}
for(const b of BASE_MARKS.filter(m=>m.color==='blue')){
 const [a,c]=tetraFeatures(b).map(f=>f.vertices),common=a.slice(0,3).filter(p=>c.slice(0,3).some(q=>key(p)===key(q)));
 assert.equal(common.length,2);const e=sub(common[1],common[0]);assert.equal(dot(e,e),18);
 const moved=a.map(p=>{const v=sub(p,common[0]);return common[0].map((x,i)=>x+e[i]*dot(e,v)/9-v[i]);});assert.equal(sig(moved),sig(c));
}
// Boundary mesh: exact orientation, no degenerate triangles, edge pairing,
// and volume. Boundary coordinates are integer twelfths.
const edges=new Map();let determinantSum=0;
for(const f of tetraBoundary())for(let i=1;i<f.vertices.length-1;i++){
 const tri=[f.vertices[0],f.vertices[i],f.vertices[i+1]], [a,b,c]=tri;
 assert.ok(cross(sub(b,a),sub(c,a)).some(v=>v));determinantSum+=dot(a,cross(b,c));
 for(let j=0;j<3;j++){const a=key(tri[j]),b=key(tri[(j+1)%3]),id=[a,b].sort().join('|'),e=edges.get(id)??[0,0];e[0]++;e[1]+=a<b?1:-1;edges.set(id,e);}
}
assert.equal(determinantSum,7*6*12**3);
assert.ok([...edges.values()].every(([count,balance])=>count===2&&balance===0));
// Geometric occupancy is rotation covariant, including every corner contact.
const globalPoints=t=>new Set(t.flatMap(({cell,mask})=>ATOMS.flatMap((a,i)=>mask&bits[i]?[key(a.point.map((v,j)=>v+240*cell[j]))]:[])));
const rootPoints=globalPoints(BASE_ATOMIC_CELLS);
for(const v of VARIANTS)assert.deepEqual(globalPoints(ATOMIC_TEMPLATES[v.id]),new Set([...rootPoints].map(k=>key(apply(v.rotation,k.split(',').map(x=>+x-240)).map(x=>x+240)))));
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
console.log(JSON.stringify({atoms:96,volume:7,rootCandidates:graph.candidates.size,tiles:64,branches:state.branchDecisions,backtracks:state.solverBacktracks,forced:state.forcedPlacements}));
