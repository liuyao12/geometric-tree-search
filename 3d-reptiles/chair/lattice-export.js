// Exact geometric export. Angles are not rounded or used as point weights.
import {VARIANTS,apply,key} from './chair44.js';
import {ATOMS,ATOMIC_TEMPLATES,TETRA_FEATURES,tetraBoundary,BOUNDARY_SCALE} from './tetra-relief.js?v=20260923-centered-union';
export const CHAIR_POINT_SCALE=96,CHAIR_CAPACITY=18;
const offsets=[];
for(let axis=0;axis<3;axis++)for(const sign of [-1,1])offsets.push([48,48,48].map((x,i)=>x+(i===axis?sign:0)));
const sites=ATOMS.map(a=>a.point.map(x=>x*CHAIR_POINT_SCALE/a.den));
const boundary=tetraBoundary();
export function chair44PointExport(){
 const orientations=VARIANTS.map((variant,oi)=>{
  const volumes=new Map(variant.cells.map(c=>[key(c),CHAIR_CAPACITY]));
  for(const f of TETRA_FEATURES){
   const center=[0,1,2].map(i=>f.vertices.reduce((s,p)=>s+p[i],0)/24);
   const cell=apply(variant.rotation,center.map(x=>x-1)).map(x=>Math.floor(x+1));
   const id=key(cell);volumes.set(id,(volumes.get(id)??0)+f.sign);
  }
  const cells=[];
  for(const {cell,mask} of ATOMIC_TEMPLATES[oi]){
   ATOMS.forEach((a,i)=>{if(mask&(1n<<BigInt(i)))cells.push({pos:sites[i].map((x,j)=>x+96*cell[j]),weight:18});});
   const weight=volumes.get(key(cell));
   if(!Number.isInteger(weight)||weight<1||weight>18)throw Error('Invalid exact Chair44 cube volume');
   for(const p of offsets)cells.push({pos:p.map((x,j)=>x+96*cell[j]),weight});
  }
  const vertices=[],lookup=new Map(),faces=[];
  for(const face of boundary)faces.push(face.vertices.map(p=>{
   const q=apply(variant.rotation,p.map(x=>x*96/BOUNDARY_SCALE-96)).map(x=>x+96),id=key(q);
   if(!lookup.has(id)){lookup.set(id,vertices.length);vertices.push(q);}return lookup.get(id);
  }));
  return {type:0,index:oi,cells,vertices,faces,marks:[]};
 });
 return {name:'Chair44 · centered lattice relief',point_model:{
  format:'gcts-exact-points-v1',allowReflections:false,capacity:18,coordinateScale:96,
  pointDomain:{period:96,sites:[...sites,...offsets]},orientations,
  domain:'Chair44 chamber occupancy + cube-volume points',
  proofScope:'Exact for cubic orientations and translations by whole original small cubes. Chamber representatives detect positive-volume overlaps; rational cube-volume points expose unfilled touched cubes. No arrow/color constraints, angle rounding, unrestricted-isometry or aperiodicity claim.',
  source:{id:'chair44-centered-union-v1',geometry:'Centered apexes; touching dents joined; 98 planar faces',normalizedVolume:7,geometricVertexScale:12,chamberClasses:49,volumeSitesPerCube:6,solidAngleWeights:false}
 }};
}
