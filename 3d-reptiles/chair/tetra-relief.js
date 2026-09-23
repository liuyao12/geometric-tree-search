// Centered cube-dissection wedge: half-square base and normal depth 1/3.
// Touching cuts are joined; internal walls are removed from the actual boundary.
import {BASE_MARKS,VARIANTS,apply,key} from './chair44.js';
import {ATOMS,CHAMBERS} from './tetra-atoms.js?v=20260923-centered-union';
export {ATOMS};
export const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
export const sub=(a,b)=>a.map((x,i)=>x-b[i]);
export const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
// Wedge vertices are integers in units of one sixth of a lattice spacing.
export function tetraFeatures(mark) {
 const n=mark.direction,center=mark.cell.map((x,i)=>6*x+3+3*n[i]),side=cross(mark.arrow,n);
 const axes=[0,1,2].filter(i=>n[i]===0);
 const corners=[[-1,-1],[1,-1],[1,1],[-1,1]].map(([a,b])=>center.map((v,i)=>v+(i===axes[0]?a*3:i===axes[1]?b*3:0)));
 const signs=mark.color==='blue'?[1,-1]:[mark.color==='red'?1:-1];
 return signs.map(sign=>{
  const base=corners.filter(p=>-sign*dot(sub(p,center),side)>=0);
  const apex=[0,1,2].map(i=>base.reduce((sum,p)=>sum+p[i],0)/3+2*sign*n[i]);
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
// Each sample has its own exact denominator; vertices use units of 1/6.
const contains=(f,p,den)=>f.planes.every(([x,y,z,d])=>6*(x*p[0]+y*p[1]+z*p[2])>=d*den);
const baseCells=new Set(VARIANTS[0].cells.map(key));
export const BASE_ATOMIC_CELLS=[];
for(let x=-1;x<=2;x++)for(let y=-1;y<=2;y++)for(let z=-1;z<=2;z++){
 const cell=[x,y,z],inside=baseCells.has(key(cell));let mask=0n;
 ATOMS.forEach((a,i)=>{
  const point=a.point.map((v,j)=>v+a.den*cell[j]);
  const cut=features.some(f=>f.sign<0&&contains(f,point,a.den));
  const bump=features.some(f=>f.sign>0&&contains(f,point,a.den));
  if((inside&&!cut)||bump)mask|=1n<<BigInt(i);
 });
 if(mask)BASE_ATOMIC_CELLS.push({cell,mask});
}
const pointKey=(point,den)=>`${key(point)}/${den}`;
const atomByPoint=new Map(ATOMS.map((a,i)=>[pointKey(a.point,a.den),i]));
export const ATOMIC_TEMPLATES=VARIANTS.map(v=>{
 const cells=new Map();
 for(const entry of BASE_ATOMIC_CELLS)for(let i=0;i<ATOMS.length;i++)if(entry.mask&(1n<<BigInt(i))){
  const den=ATOMS[i].den;
  const p=apply(v.rotation,ATOMS[i].point.map((x,j)=>x+den*entry.cell[j]-den)).map(x=>x+den);
  const cell=p.map(x=>Math.floor(x/den)),local=p.map((x,j)=>x-den*cell[j]),idx=atomByPoint.get(pointKey(local,den));
  if(idx===undefined)throw Error('Tetrahedral atom domain is not rotation invariant');
  const id=key(cell),target=cells.get(id)??{cell,mask:0n};target.mask|=1n<<BigInt(idx);cells.set(id,target);
 }
 return [...cells.values()];
});
// Direct, outward-oriented boundary. The exact geometry audit certifies that
// the distinct wedges have disjoint interiors and no coincident face areas.
export const BOUNDARY_SCALE=12;
export function tetraBoundary() {
 const faces=new Map();
 for(const {cell,mask} of BASE_ATOMIC_CELLS)for(const chamber of CHAMBERS)if(mask&(1n<<BigInt(chamber.atom))){
  for(const local of chamber.faces){
   const vertices=local.map(p=>p.map((x,j)=>x+BOUNDARY_SCALE*cell[j]));
   const id=vertices.map(key).sort().join(';');
   if(faces.has(id))faces.delete(id);else faces.set(id,vertices);
  }
 }
 return [...faces.values()].map(vertices=>{
  const p=vertices[0],n=cross(sub(vertices[1],p),sub(vertices[2],p));
  let color=null;
  if(n.filter(x=>x!==0).length>1){
   const sum=[0,1,2].map(j=>vertices.reduce((s,v)=>s+v[j],0)),count=vertices.length;
   const feature=features.find(f=>f.planes.every(([x,y,z,d])=>x*sum[0]+y*sum[1]+z*sum[2]>=2*count*d));
   if(!feature)throw Error('Unclassified tetrahedral boundary facet');
   color=feature.color;
  }
  return {vertices,color};
 });
}
export const TETRA_FEATURES=features;
