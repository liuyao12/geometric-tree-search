// The volume-27 cube-dissection wedge, scaled by 1/3:
// triangle half of a unit square, apex at its centroid and normal depth 1/3.
import {BASE_MARKS,VARIANTS,apply,key,FACE_DIRECTIONS} from './chair44.js';
import {ATOMS} from './tetra-atoms.js';
export {ATOMS};
export const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
export const sub=(a,b)=>a.map((x,i)=>x-b[i]);
export const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
// Wedge vertices are integers in units of one third of a lattice spacing.
export function tetraFeatures(mark) {
 const n=mark.direction,center=mark.cell.map((x,i)=>3*x+1.5+1.5*n[i]),side=cross(mark.arrow,n);
 const axes=[0,1,2].filter(i=>n[i]===0);
 const corners=[[-1,-1],[1,-1],[1,1],[-1,1]].map(([a,b])=>center.map((v,i)=>v+(i===axes[0]?a*1.5:i===axes[1]?b*1.5:0)));
 const signs=mark.color==='blue'?[1,-1]:[mark.color==='red'?1:-1];
 return signs.map(sign=>{
  const base=corners.filter(p=>-sign*dot(sub(p,center),side)>=0);
  const apex=center.map((_,i)=>base.reduce((s,p)=>s+p[i],0)/3+sign*n[i]);
  return {color:mark.color,sign,vertices:[...base,apex]};
 });
}
export function tetraPlanes(vertices) {
 return vertices.map((opposite,i)=>{
  const face=vertices.filter((_,j)=>j!==i),n=cross(sub(face[1],face[0]),sub(face[2],face[0]));
  const d=dot(n,face[0]),sign=dot(n,opposite)>d?1:-1;
  return [...n.map(x=>x*sign),d*sign];
 });
}
const features=BASE_MARKS.flatMap(tetraFeatures).map(f=>({...f,planes:tetraPlanes(f.vertices)}));
// p has units 1/240; tetrahedron vertices have units 1/3.
const contains=(f,p)=>f.planes.every(([x,y,z,d])=>x*p[0]+y*p[1]+z*p[2]>=80*d);
const baseCells=new Set(VARIANTS[0].cells.map(key));
export const BASE_ATOMIC_CELLS=[];
for(let x=-1;x<=2;x++)for(let y=-1;y<=2;y++)for(let z=-1;z<=2;z++){
 const cell=[x,y,z],inside=baseCells.has(key(cell));let mask=0n;
 ATOMS.forEach((a,i)=>{
  const point=a.point.map((v,j)=>v+240*cell[j]);
  const cut=features.some(f=>f.sign<0&&contains(f,point));
  const bump=features.some(f=>f.sign>0&&contains(f,point));
  if((inside&&!cut)||bump)mask|=1n<<BigInt(i);
 });
 if(mask)BASE_ATOMIC_CELLS.push({cell,mask});
}
const atomByPoint=new Map(ATOMS.map((a,i)=>[key(a.point),i]));
export const ATOMIC_TEMPLATES=VARIANTS.map(v=>{
 const cells=new Map();
 for(const entry of BASE_ATOMIC_CELLS)for(let i=0;i<ATOMS.length;i++)if(entry.mask&(1n<<BigInt(i))){
  const p=apply(v.rotation,ATOMS[i].point.map((x,j)=>x+240*entry.cell[j]-240)).map(x=>x+240);
  const cell=p.map(x=>Math.floor(x/240)),local=p.map((x,j)=>x-240*cell[j]),idx=atomByPoint.get(key(local));
  if(idx===undefined)throw Error('Tetrahedral atom domain is not rotation invariant');
  const id=key(cell),target=cells.get(id)??{cell,mask:0n};target.mask|=1n<<BigInt(idx);cells.set(id,target);
 }
 return [...cells.values()];
});
// Exact boundary of the union of occupied atoms. Internal faces cancel here;
// faces shared by separate tiles remain present in the renderer.
export function tetraBoundary() {
 const faces=new Map();
 for(const {cell,mask} of BASE_ATOMIC_CELLS)for(let i=0;i<ATOMS.length;i++)if(mask&(1n<<BigInt(i))){
  for(const local of ATOMS[i].faces){
   const vertices=local.map(p=>p.map((x,j)=>x+12*cell[j]));
   const id=vertices.map(key).sort().join(';');
   if(faces.has(id))faces.delete(id);else faces.set(id,vertices);
  }
 }
 return [...faces.values()].map(vertices=>{
  const p=vertices[0],n=cross(sub(vertices[1],p),sub(vertices[2],p));
  // A relief slope is non-coordinate; the untouched part of the cube is flat.
  let color=null;
  if(n.filter(x=>x!==0).length>1){
   // Use integer sum of vertices instead of a rounded face centroid.
   const sum=vertices[0].map((_,j)=>vertices.reduce((s,v)=>s+v[j],0));
   const count=vertices.length;
   const f=features.find(f=>f.planes.every(([x,y,z,d])=>x*sum[0]+y*sum[1]+z*sum[2]>=4*count*d));
   if(!f)throw Error('Unclassified tetrahedral boundary facet');color=f.color;
  }
  return {vertices,color};
 });
}
export const TETRA_FEATURES=features;
