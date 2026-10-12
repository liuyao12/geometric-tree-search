import {unitLoop,embeddingKey} from './lattice-state.mjs';
import {project} from '../../apps/knot-movie/projection.mjs';
import {moves} from '../../apps/knot-movie/engine.mjs';
export const VERSION='lattice-face-reidemeister-v1';
export const DEFAULT_DIRECTION=[11,13,17];
const pk=p=>p.join(',');
const ek=(a,b)=>[pk(a),pk(b)].sort().join('|');
export function bends(input){const p=unitLoop(input);return p.filter((b,i)=>{const a=p[(i+p.length-1)%p.length],c=p[(i+1)%p.length];return b.some((x,k)=>x-a[k]!==c[k]-x);});}
export function diagram(input,direction=DEFAULT_DIRECTION){
 if(!Array.isArray(direction)||direction.length!==3||direction.some(x=>!Number.isSafeInteger(x)||x<1||x>41))throw Error('Direction requires three positive integers at most 41.');
 const p=unitLoop(input);if(p.length>2000||p.some(p=>p.some(x=>Math.abs(x)>100)))throw Error('Projection arithmetic scope exceeded.');
 return project(bends(p),direction);
}
// Every unit square meeting an edge is enumerated, in all three planes and
// both sides. The intersection with the loop must be one boundary arc.
export function rawFaceSweeps(input,{maxEdges=200,region=null}={}){
 const p=unitLoop(input),n=p.length,edges=new Map(p.map((a,i)=>[ek(a,p[(i+1)%n]),i])),faces=new Map(),out=[];
 for(let i=0;i<n;i++){
  const a=p[i],b=p[(i+1)%n],axis=a.findIndex((x,k)=>x!==b[k]);
  for(let k=0;k<3;k++)if(k!==axis)for(const sign of [-1,1]){
   const c=[...b],d=[...a];c[k]+=sign;d[k]+=sign;
   const f=[a,b,c,d];faces.set(f.map(pk).sort().join('|'),f);
  }
 }
 for(const face of faces.values()){
  if(region&&face.some(p=>p.some((x,k)=>x<region.min[k]||x>region.max[k])))continue;
  const hits=face.map((a,i)=>edges.get(ek(a,face[(i+1)%4]))).filter(x=>x!==undefined);
  if(!hits.length||hits.length===4)continue;
  const h=new Set(hits),start=hits.find(i=>!h.has((i+n-1)%n));if(start===undefined)continue;
  let len=0;while(h.has((start+len)%n))len++;if(len!==hits.length)continue;
  const a=p[start],b=p[(start+len)%n],old=Array.from({length:len+1},(_,k)=>p[(start+k)%n]);
  const root=face.findIndex(x=>pk(x)===pk(a));let replacement=null;
  for(const sign of [-1,1]){
   const path=[a];let j=root;
   for(let k=0;k<4;k++){j=(j+sign+4)%4;path.push(face[j]);if(pk(face[j])===pk(b))break;}
   if(path.length===5-len&&!edges.has(ek(path[0],path[1])))replacement=path;
  }
  if(!replacement||n+4-2*len>maxEdges)continue;
  const rotated=Array.from({length:n},(_,k)=>p[(start+k)%n]);
  const after=[...replacement.slice(0,-1),...rotated.slice(len)];
  // A unit cubic face has no lattice points in its relative interior. All
  // transverse lattice edges meet its plane at lattice points. New boundary
  // vertices are vacant, so the disk is disjoint from the unchanged knot.
  out.push({face:face.map(x=>[...x]),old:old.map(x=>[...x]),replacement:replacement.map(x=>[...x]),vertices:after});
 }
 return out;
}
// The raw domain deliberately includes capacity failures so an independently
// learned marking can reject them before expensive spatial/projection work.
export function faceSweeps(input,options={}){
 const out=[];for(const m of rawFaceSweeps(input,options)){try{unitLoop(m.vertices);out.push({...m,key:embeddingKey(m.vertices)});}catch{}}return out;
}
export function moveContext(input,options={}){
 const direction=options.direction||DEFAULT_DIRECTION,before=diagram(input,direction);
 return{direction,before,legal:new Map(moves(before.word,before.word.length/2).map(m=>[m.key,m.kind])),inputKey:embeddingKey(input)};
}
export function resolveSweep(sweep,context){
 let after;try{unitLoop(sweep.vertices);after=diagram(sweep.vertices,context.direction);}catch{return null;}
 const {before,legal,direction}=context;
 let kind=after.canonical===before.canonical?'routing':legal.get(after.canonical);
 const delta=(after.word.length-before.word.length)/2;
 if(!kind&&(delta===1||delta===2)){
  const inverse=delta===1?'I−':'II−';
  if(moves(after.word,after.word.length/2).some(m=>m.kind===inverse&&m.key===before.canonical))kind=delta===1?'I+':'II+';
 }
 const key=embeddingKey(sweep.vertices);
 if(!kind||key===context.inputKey)return null;
 return{...sweep,key,kind,beforeDiagram:before.canonical,afterDiagram:after.canonical,direction};
}
export function latticeMoves(input,options={}){
 const context=moveContext(input,options),unique=new Map();
 for(const sweep of rawFaceSweeps(input,options)){const m=resolveSweep(sweep,context);if(m&&!unique.has(m.key))unique.set(m.key,m);}
 return [...unique.values()];
}
export function verifyStep(input,step,options={}){
 const found=latticeMoves(input,options).find(m=>m.key===embeddingKey(step.vertices)&&m.kind===step.kind&&JSON.stringify(m.face.map(pk).sort())===JSON.stringify(step.face.map(pk).sort()));
 if(!found)throw Error('Invalid lattice Reidemeister face tile.');
 const pathKey=p=>p.slice(1).map((x,i)=>ek(p[i],x)).sort().join(';');
 if(step.beforeDiagram!==found.beforeDiagram||step.afterDiagram!==found.afterDiagram||pathKey(step.old)!==pathKey(found.old)||pathKey(step.replacement)!==pathKey(found.replacement)||JSON.stringify(step.direction)!==JSON.stringify(found.direction))throw Error('Inconsistent lattice tile certificate data.');
 return true;
}
