// Adjusted cube-dissection wedge: the same half-square base and depth 1/3,
// with the apex shifted along the hinge to separate neighboring recess walls.
import {BASE_MARKS,VARIANTS,apply,key} from './chair44.js';
import {ATOMS} from './tetra-atoms.js?v=20260923-apex-shift';
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
  const right=base.find(p=>{const q=base.filter(v=>v!==p);return dot(sub(q[0],p),sub(q[1],p))===0;});
  const head=base.reduce((p,q)=>dot(p,mark.arrow)>dot(q,mark.arrow)?p:q);
  const tail=base.find(p=>p!==right&&p!==head);
  const apex=right.map((x,i)=>x+(head[i]-x)/2+(tail[i]-x)/3+2*sign*n[i]);
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
export function tetraBoundary() {
 const faces=[];
 for(const mark of BASE_MARKS){
  const features=tetraFeatures(mark);
  for(const feature of features){
   const base=feature.vertices.slice(0,3),apex=feature.vertices[3];
   if(dot(cross(sub(base[1],base[0]),sub(base[2],base[0])),mark.direction)<0)base.reverse();
   for(let i=0;i<3;i++)faces.push({vertices:[base[i],base[(i+1)%3],apex],color:mark.color});
  }
  if(mark.color!=='blue'){
   const base=features[0].vertices.slice(0,3);
   const right=base.find(p=>{const q=base.filter(v=>v!==p);return dot(sub(q[0],p),sub(q[1],p))===0;});
   const diagonal=base.filter(p=>p!==right),other=diagonal[0].map((x,i)=>x+diagonal[1][i]-right[i]);
   const flat=[...diagonal,other];
   if(dot(cross(sub(flat[1],flat[0]),sub(flat[2],flat[0])),mark.direction)<0)flat.reverse();
   faces.push({vertices:flat,color:null});
  }
 }
 return faces;
}
export const TETRA_FEATURES=features;
