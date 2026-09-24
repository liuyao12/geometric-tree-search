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
const leaves=chairLeaves(1);
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
function extract(i,d,others){
 for(const j of others)for(let a=0;a<tiles[i].length;a++)for(let b=0;b<tiles[j].length;b++){
  const interval=collision(tiles[i][a],tiles[j][b],d);
  if(interval)return {blockedBy:j,pieces:[a,b],interval};
 }
 return null;
}
// Independent elementary motion cases catch sign, tangency and finite-interval errors.
const box=(lo,hi)=>piece([
 [[lo,lo,lo],[hi,lo,lo],[hi,hi,lo],[lo,hi,lo]],
 [[lo,lo,hi],[hi,lo,hi],[hi,hi,hi],[lo,hi,hi]],
 [[lo,lo,lo],[hi,lo,lo],[hi,lo,hi],[lo,lo,hi]],
 [[lo,hi,lo],[hi,hi,lo],[hi,hi,hi],[lo,hi,hi]],
 [[lo,lo,lo],[lo,hi,lo],[lo,hi,hi],[lo,lo,hi]],
 [[hi,lo,lo],[hi,hi,lo],[hi,hi,hi],[hi,lo,hi]]]);
assert.equal(collision(box(0,1),box(1,2),[-1,-1,-1]),null);
assert(collision(box(0,1),box(1,2),[1,1,1]));
assert.equal(collision(box(0,1),box(1,2),[1,0,0]),null);
const delayed=collision(box(0,1),box(2,3),[1,1,1]);
assert.equal(cmp(delayed[0],[1,1]),0);assert.equal(cmp(delayed[1],[3,1]),0);
const blockedIndividualPaths=[];
for(let i=0;i<8;i++)if(i!==4){
 const d=leaves[i].origin.map(x=>12*(x-1));
 const result=extract(i,d,[0,1,2,3,4,5,6,7].filter(j=>j!==i));
 assert(result,'Expected this individual diagonal extraction to be blocked');
 blockedIndividualPaths.push({tile:i,direction:d.map(x=>x/12),...result});
}
for(let i=0;i<8;i++)for(let j=i+1;j<8;j++){
 const d=leaves[i].origin.map((x,k)=>12*(x-leaves[j].origin[k]));
 let result=null;
 outer:for(let a=0;a<tiles[i].length;a++)for(let b=0;b<tiles[j].length;b++){
  const interval=collision(tiles[i][a],tiles[j][b],d);
  if(interval){result={pieces:[a,b],interval};break outer;}
 }
 assert.equal(result,null,`Simultaneous radial extraction collides for tiles ${i},${j}`);
}

console.log(JSON.stringify({
 geometry:'Chair44 centered merged-cavity relief', piecesPerTile:tiles[0].length,
 coordinateScale:12, placements:leaves.map(p=>({origin:p.origin,variantId:p.variantId})),
 blockedIndividualPaths,
 simultaneousExtraction:{fixedCenter:4,pairsChecked:28,collisionFree:true,
 parameter:'origin(lambda) = origin + lambda * (origin - [1,1,1]), lambda >= 0',
 orientationsFixed:true,boundaryContactAllowed:true},
 scope:'Only this eight-tile supertile and these straight paths; no general assembly or aperiodicity claim.'
},null,2));
