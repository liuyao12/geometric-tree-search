// Continuous rigid-translation audit, separate from point-domain tiling search.
// Run from any directory with: node scripts/check-chair44-assembly.mjs
import assert from 'node:assert/strict';
import {BASE_ATOMIC_CELLS,cross,sub,dot} from '../3d-reptiles/chair/tetra-relief.js';
import {CHAMBERS} from '../3d-reptiles/chair/tetra-atoms.js';
import {chairLeaves,apply} from '../3d-reptiles/chair/chair44.js';
const gcd=(a,b)=>b?gcd(b,a%b):Math.abs(a);
function axis(n){const g=n.reduce(gcd,0);if(!g)return null;const s=n.find(x=>x!==0)<0?-1:1;return n.map(x=>s*x/g);}
function unique(ns){return [...new Map(ns.map(axis).filter(Boolean).map(n=>[n.join(','),n])).values()];}
function piece(faces){
 const vertices=[...new Map(faces.flat().map(p=>[p.join(','),p])).values()];
 assert(vertices.length>=4);
 const normals=unique(faces.map(f=>cross(sub(f[1],f[0]),sub(f[2],f[0]))));
 // Every chamber is convex: each face plane supports all its vertices.
 for(const f of faces){
  const n=cross(sub(f[1],f[0]),sub(f[2],f[0]));
  const ds=vertices.map(p=>dot(n,sub(p,f[0])));
  assert(ds.every(x=>x>=0)||ds.every(x=>x<=0));
 }
 const edges=unique(vertices.flatMap((a,i)=>vertices.slice(i+1).map(b=>sub(b,a))));
 return {vertices,normals,edges,bounds:[0,1,2].map(i=>[Math.min(...vertices.map(p=>p[i])),Math.max(...vertices.map(p=>p[i]))])};
}
const leaves=chairLeaves(2);
const tiles=leaves.map(leaf=>BASE_ATOMIC_CELLS.flatMap(({cell,mask})=>CHAMBERS.filter(c=>mask&(1n<<BigInt(c.atom))).map(c=>piece(c.faces.map(f=>f.map(p=>apply(leaf.rotation,p.map((x,i)=>x+12*cell[i]-12)).map((x,i)=>x+12+12*leaf.origin[i])))))));
// All coordinates and projection bounds are integers. Rational interval bounds
// are compared by exact integer cross multiplication, with safe-integer guards.
function cmp(a,b){const x=a[0]*b[1],y=b[0]*a[1];assert(Number.isSafeInteger(x)&&Number.isSafeInteger(y));return Math.sign(x-y);}
function overlapInterval(a,b,d,axes,initial=[[0,1],null]){
 let [lo,hi]=initial;
 for(const n of axes){
  const ap=a.vertices.map(p=>dot(n,p)),bp=b.vertices.map(p=>dot(n,p));
  const amin=Math.min(...ap),amax=Math.max(...ap),bmin=Math.min(...bp),bmax=Math.max(...bp),v=dot(n,d);
  if(!v){if(amax<=bmin||bmax<=amin)return null;continue;}
  let low=[bmin-amax,v],high=[bmax-amin,v];
  if(v<0){[low,high]=[high,low];low=low.map(x=>-x);high=high.map(x=>-x);}
  if(cmp(low,lo)>0)lo=low;
  if(!hi||cmp(high,hi)<0)hi=high;
  if(hi&&cmp(lo,hi)>=0)return null;
 }
 return [lo,hi];
}
function collision(a,b,d){
 const window=overlapInterval(a,b,d,[[1,0,0],[0,1,0],[0,0,1]]);
 if(!window)return null;
 return overlapInterval(a,b,d,unique([...a.normals,...b.normals,...a.edges.flatMap(e=>b.edges.map(f=>cross(e,f)))]),window);
}

const boxFor=pieces=>({vertices:[0,1].flatMap(a=>[0,1].flatMap(b=>[0,1].map(c=>[0,1,2].map((axis)=>{
 const low=Math.min(...pieces.map(p=>p.bounds[axis][0])),high=Math.max(...pieces.map(p=>p.bounds[axis][1]));
 return [a,b,c][axis]?high:low;
}))))});
const boxes=tiles.map(boxFor);
const d=[-24,-24,-24];let tested=0,result=null;
outer:for(let i=0;i<8;i++)for(let j=32;j<40;j++){
 if(!overlapInterval(boxes[i],boxes[j],d,[[1,0,0],[0,1,0],[0,0,1]]))continue;
 for(let a=0;a<tiles[i].length;a++)for(let b=0;b<tiles[j].length;b++){
  tested++;const interval=collision(tiles[i][a],tiles[j][b],d);
  if(interval){result={movingLeaf:leaves[i],fixedLeaf:leaves[j],pieces:[a,b],interval,
   movingVertices:tiles[i][a].vertices,fixedVertices:tiles[j][b].vertices,direction:d};break outer;}
 }
}
assert(result);console.log(JSON.stringify({tested,result},null,2));
