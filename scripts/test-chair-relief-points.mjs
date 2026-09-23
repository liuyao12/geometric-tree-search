import assert from 'node:assert/strict';
import { FACE_DIRECTIONS, VARIANTS, key, apply, chairLeaves } from '../3d-reptiles/chair/chair44.js';
import { reliefFeatures, reliefFrame, reliefHeight } from '../3d-reptiles/chair/relief-profile.js';
import { createReliefPointModel } from './lib/chair-relief-points.mjs';

assert.deepEqual(reliefFeatures('blue'), [{u:.16,v:.08,radius:.16,height:.12},{u:-.16,v:.08,radius:.16,height:-.12}]);
assert.deepEqual(reliefFeatures('red'), [{u:0,v:.10,radius:.24,height:.12}]);
assert.deepEqual(reliefFeatures('green'), [{u:0,v:.10,radius:.24,height:-.12}]);

for(const centered of [false,true]) {
const { PROBES, FULL, height400, faceMask, compile, indexState, graphFor, clearCache, isLegal, extend }=createReliefPointModel({centered});
const [bump,dent]=reliefFeatures('blue',centered);
assert.deepEqual({...dent,u:-dent.u,height:-dent.height},bump,
  'A half-turn around the shared base edge moves the removed pyramid onto the blue bump');
const red=reliefFeatures('red',centered)[0],green=reliefFeatures('green',centered)[0];
assert.deepEqual({...green,height:-green.height},red,'Green plug and red bump are congruent');
// All extrema of the sum of two profiles occur at intersections of these
// exact ridge/base lines. Their intersections have integer (x,y) coordinates.
const lines=new Map();
const put=(a,b,c)=>lines.set(`${a},${b},${c}`,[a,b,c]);
for(const a of [-1,1])for(const b of [-1,1])for(const [u,v,r] of [[0,centered?0:10,24],[16,centered?0:8,16],[-16,centered?0:8,16]]) {
  for(const d of [-r,0,r]){put(b,-a,u+d);put(a,b,v+d);}
  put(b-a,-a-b,u-v);put(b+a,-a+b,u+v);
}
for(const c of [-50,50]){put(1,0,c);put(0,1,c);}
const vertices=new Map(),all=[...lines.values()];
for(const [a,b,c] of all)for(const [d,e,f] of all) {
  const determinant=a*e-b*d;if(!determinant)continue;
  const x=(c*e-b*f)/determinant,y=(a*f-c*d)/determinant;
  assert.ok(Number.isInteger(x)&&Number.isInteger(y));
  if(Math.abs(x)<=50&&Math.abs(y)<=50)vertices.set(`${x},${y}`,[x,y]);
}
let cases=0;
for(const n of FACE_DIRECTIONS) {
 const axis=n.findIndex(v=>v!==0),tangent=[0,1,2].filter(i=>i!==axis);
 const marks=[];
 for(const a of [-1,1])for(const b of [-1,1])for(const color of ['red','green','blue']) {
  const arrow=[0,0,0];arrow[tangent[0]]=a;arrow[tangent[1]]=b;
  marks.push({cell:[0,0,0],direction:n,arrow,color});
 }
 for(const a of marks)for(const entry of marks) {
  const b={...entry,cell:[...n],direction:n.map(v=>-v)};
  let overlap=false,gap=false;
  for(const [x,y] of vertices.values()) {
   const sum=height400(a,x,y)+height400(b,x,y);overlap ||= sum>0;gap ||= sum<0;
  }
  const maskA=faceMask(a),maskB=faceMask(b);
  assert.equal(Boolean(maskA&maskB),overlap,'Probes detect every geometric overlap');
  assert.equal((maskA|maskB)!==FULL,gap,'Probes detect every geometric gap');
  const expected=(key(a.arrow)===key(b.arrow)||(centered&&a.color!=='blue'&&b.color!=='blue'))&&((a.color==='blue'&&b.color==='blue')||(a.color==='red'&&b.color==='green')||(a.color==='green'&&b.color==='red'));
  assert.equal(!overlap&&!gap,expected);cases++;
 }
 for(const mark of marks)for(const {x,y} of PROBES) {
  const frame=reliefFrame(mark),point=[...frame.center];point[tangent[0]]+=Math.SQRT2*x/100;point[tangent[1]]+=Math.SQRT2*y/100;
  assert.ok(Math.abs(reliefHeight(mark,point,centered)*400-height400(mark,x,y))<1e-10,'Point model agrees with rendered geometry');
 }
}
// Each modification and probe lies strictly inside an L1 ball of radius 1/2
// around its panel center. These balls have disjoint interiors on the grid.
for(const color of ['red','green','blue'])for(const feature of reliefFeatures(color,centered)) {
 for(const [u,v,h] of [[feature.u,feature.v,feature.height],...[-1,1].flatMap(a=>[-1,1].map(b=>[feature.u+a*feature.radius,feature.v+b*feature.radius,0]))]) {
  const maxUV=Math.round(100*Math.max(Math.abs(u),Math.abs(v))),height=Math.round(100*Math.abs(h));
  assert.ok(height<50&&2*maxUV*maxUV<(50-height)**2, 'Exact squared L1 bound');
 }

}
for(const {x,y,h} of PROBES)assert.ok(2*(4*(Math.abs(x)+Math.abs(y)))**2<(200-Math.abs(h))**2);
for(let level=0;level<=2;level++) {
 const patch=chairLeaves(level),index=indexState(patch);
 assert.equal(index.occupied.size,7*8**level);
 // Every probe on an internal cube face is filled, including within a tile.
 for(const [id,mask] of index.faceOccupancy){const [axis,cell]=id.split(':'),a=cell.split(',').map(Number),b=[...a];b[Number(axis)]++;
 if(index.occupied.has(key(a))&&index.occupied.has(key(b)))assert.equal(mask,FULL);}
}
const root={variantId:0,origin:[0,0,0],generation:0};
const graph=graphFor([root]);
for(const [id,tile] of graph.candidates)for(const [point,node] of graph.frontier) {
 let covers=false;
 if(point.startsWith('c:'))covers=tile.cells.includes(point.slice(2));
 else {const parts=point.slice(2).split(':'),i=Number(parts.pop()),face=parts.join(':');covers=Boolean(tile.faces.find(f=>f.id===face)?.mask&(1<<i));}
 assert.equal(node.candidates.has(id),covers);
}
// Independently enumerate the full possible face-neighbor translation box.
const exhaustive = new Set(), seedCells = new Set(compile(root).cells);
for(const variant of VARIANTS)for(let x=-2;x<=2;x++)for(let y=-2;y<=2;y++)for(let z=-2;z<=2;z++) {
 const tile=compile({variantId:variant.id,origin:[x,y,z]});
 const adjacent=tile.cells.some(id=>FACE_DIRECTIONS.some(d=>seedCells.has(key(id.split(',').map((v,i)=>Number(v)+d[i])))));
 if(adjacent&&isLegal(tile,graph.index))exhaustive.add(tile.id);
}
assert.deepEqual(new Set(graph.candidates.keys()),exhaustive);

// Exact transformed point coordinates in Q(sqrt(2)): (p + q sqrt(2))/400.
function positivePoints(placement) {
 const tile=compile(placement),points=[];
 for(const id of tile.cells)points.push([id.split(',').map(v=>400*Number(v)+200),[0,0,0]]);
 for(const {id,mask} of tile.faces) {
  const [axisText,cellText]=id.split(':'),axis=Number(axisText),cell=cellText.split(',').map(Number),tangents=[0,1,2].filter(i=>i!==axis);
  for(let i=0;i<PROBES.length;i++)if(mask&(1<<i)) {
   const {x,y,h}=PROBES[i],p=cell.map((v,j)=>400*v+(j===axis?400:200)),q=[0,0,0];
   p[axis]+=h;q[tangents[0]]=4*x;q[tangents[1]]=4*y;points.push([p,q]);
  }
 }
 return new Set(points.map(([p,q])=>p.map((v,i)=>`${v},${q[i]}`).join(';')));
}
const prototype=positivePoints(root);
for(const variant of VARIANTS) {
 const rotated=new Set([...prototype].map(id=>{
  const pairs=id.split(';').map(p=>p.split(',').map(Number));
  const p=apply(variant.rotation,pairs.map(v=>v[0]-400)).map(v=>v+400),q=apply(variant.rotation,pairs.map(v=>v[1]));
  return p.map((v,i)=>`${v},${q[i]}`).join(';');
 }));
 assert.deepEqual(rotated,positivePoints({variantId:variant.id,origin:[0,0,0]}));
}
const extra=[...graph.candidates.values()].find(p=>graphFor([root,p]).dead?.startsWith('p:'));
assert.ok(extra);
assert.equal(extend([root,extra],{maxNodes:10}).status,'exhausted');
const seed=[root,{variantId:6,origin:[0,0,-2],generation:0}],before=JSON.stringify(seed);
assert.equal(extend(seed,{maxNodes:1}).status,'unknown');
const result=extend(seed,{maxNodes:100});
assert.equal(result.status,'consistent finite patch');if(!centered)assert.ok(result.backtracks>0);
assert.equal(JSON.stringify(seed),before,'Search rollback must preserve its fixed roots');
assert.deepEqual(result.witness.slice(0,2),seed);
assert.equal(graphFor(result.witness).dead,null);
console.log(JSON.stringify({centered,facingCases:cases,exactProfileVertices:vertices.size,probesPerFace:PROBES.length,rootCandidates:graph.candidates.size,frontierPoints:graph.frontier.size}));
clearCache();

}
