// A declared periodic point domain, independent of solid-angle weights.
import {validatePointModel} from './corona-graph.js';
const key=p=>p.join(','),integerPoint=p=>Array.isArray(p)&&p.length===3&&p.every(x=>Number.isSafeInteger(x)&&Math.abs(x)<=1e7);
export function prepareExactPointModel(custom,{mirrors=false,radius=1}={}){
 const p=custom?.point_model;
 if(p?.format!=='gcts-exact-points-v1')throw Error('Unsupported exact point-model format');
 const period=p.pointDomain?.period,sites=p.pointDomain?.sites;
 if(!Number.isSafeInteger(period)||period<1||period>100000||!Array.isArray(sites)||!sites.length||sites.length>10000||sites.some(q=>!integerPoint(q)||q.some(x=>x<0||x>=period))||new Set(sites.map(key)).size!==sites.length)throw Error('Invalid periodic point domain');
 if(!Array.isArray(p.orientations)||!p.orientations.length||p.orientations.length>96)throw Error('Invalid point orientations');
 const residues=new Set(sites.map(key)),residue=q=>q.map(x=>(x%period+period)%period);
 const orientations=p.orientations.map((o,index)=>{
  if(!Array.isArray(o.cells)||o.cells.length>100000||o.cells.some(c=>!integerPoint(c.pos)||!residues.has(key(residue(c.pos)))))throw Error('Support leaves the declared point domain');
  if(!Array.isArray(o.vertices)||o.vertices.length>100000||o.vertices.some(q=>!integerPoint(q))||!Array.isArray(o.faces)||o.faces.length>100000||o.faces.some(f=>!Array.isArray(f)||f.length<3||f.some(i=>!Number.isSafeInteger(i)||i<0||i>=o.vertices.length)))throw Error('Invalid display mesh');
  if(o.marks?.length)throw Error('Import the unmarked point model; learn markings in the app');
  return {type:0,index,cells:o.cells.map(c=>({pos:c.pos.slice(),weight:c.weight})),vertices:o.vertices.map(q=>q.slice()),faces:o.faces.map(f=>f.slice()),marks:[]};
 });
 if(mirrors){
  if(!p.allowReflections)throw Error('This export declares proper rotations only; turn off reflections');
  if(sites.some(q=>!residues.has(key(residue([-q[0],q[1],q[2]])))))throw Error('This point domain has no declared reflection symmetry');
  const seen=new Set(orientations.map(o=>o.cells.map(c=>`${c.pos}:${c.weight}`).sort().join('|')));
  for(const o of [...orientations]){
   const flip=q=>[-q[0],q[1],q[2]],cells=o.cells.map(c=>({pos:flip(c.pos),weight:c.weight}));
   const signature=cells.map(c=>`${c.pos}:${c.weight}`).sort().join('|');if(seen.has(signature))continue;seen.add(signature);
   orientations.push({...o,index:orientations.length,cells,vertices:o.vertices.map(flip),faces:o.faces.map(f=>f.slice().reverse())});
  }
 }
 if(!Number.isInteger(radius)||radius<1||radius>3)throw Error('Point-domain window radius must be 1–3');
 const required=[];
 for(let x=-radius;x<=radius;x++)for(let y=-radius;y<=radius;y++)for(let z=-radius;z<=radius;z++)for(const q of sites)required.push({pos:q.map((v,i)=>v+period*[x,y,z][i]),generation:0});
 const model={version:'exact-point-import-1',name:String(custom.name??'Exact point tile'),capacity:p.capacity,orientations,required,
  pointDomain:{period,sites:sites.map(q=>q.slice())},placementDomain:{kind:'scaled_cubic',translationStep:period},allowReflections:mirrors,
  coordinateScale:p.coordinateScale,exactPointImport:true,domain:String(p.domain??'Periodic exact point domain'),
  proofScope:String(p.proofScope??'Exact point model; geometric equivalence supplied by the author.'),source:p.source,
  boundary:'Every declared point in the finite cube window must reach capacity; growth activates partially filled support points.'};
 validatePointModel(model);return model;
}
