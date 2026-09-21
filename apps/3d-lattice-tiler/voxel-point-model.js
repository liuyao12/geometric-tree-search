// Explicit research model: unit-voxel centers carry full capacity in addition
// to corner weights. This is faithful to grid-aligned polycube packings.
// It does not claim that all Euclidean tilings must use this placement group.
import {polycubeOrientations} from '../../assets/polycube-enumerator.js';
const key=p=>p.join(',');
const faceDefs=[[[1,0,0],[[1,0,0],[1,1,0],[1,1,1],[1,0,1]]],[[-1,0,0],[[0,0,0],[0,0,1],[0,1,1],[0,1,0]]],[[0,1,0],[[0,1,0],[0,1,1],[1,1,1],[1,1,0]]],[[0,-1,0],[[0,0,0],[1,0,0],[1,0,1],[0,0,1]]],[[0,0,1],[[0,0,1],[1,0,1],[1,1,1],[0,1,1]]],[[0,0,-1],[[0,0,0],[0,1,0],[1,1,0],[1,0,0]]]];
function support(voxels){
 const weights=new Map();
 for(const v of voxels){
  weights.set(key(v.map(x=>2*x+1)),8);
  for(const x of [0,1])for(const y of [0,1])for(const z of [0,1]){const p=v.map((n,i)=>2*(n+[x,y,z][i])),k=key(p);weights.set(k,(weights.get(k)??0)+1);}
 }
 return [...weights].map(([k,weight])=>({pos:k.split(',').map(Number),weight}));
}
export function prepareVoxelPointModel(voxels,{name='Polycube',mirrors=false,radius=1}={}){
 if(!Array.isArray(voxels)||!voxels.length||voxels.some(v=>v.length!==3||v.some(x=>!Number.isSafeInteger(x)))||new Set(voxels.map(key)).size!==voxels.length)throw Error('Expected distinct integer voxels');
 if(!Number.isInteger(radius)||radius<0||radius>3)throw Error('Voxel target radius must be 0–3');
 const orientations=polycubeOrientations(voxels,{includeReflections:mirrors}).map((o,index)=>{
  const cells=support(o.voxels),vertices=cells.filter(c=>c.pos.every(x=>x%2===0)).map(c=>c.pos),lookup=new Map(vertices.map((v,i)=>[key(v),i])),occupied=new Set(o.voxels.map(key)),faces=[];
  for(const v of o.voxels)for(const [normal,face] of faceDefs){if(occupied.has(key(v.map((x,i)=>x+normal[i]))))continue;faces.push(face.map(d=>lookup.get(key(v.map((x,i)=>2*(x+d[i]))))));}
  return {type:0,index,voxels:o.voxels,cells,vertices,faces,marks:[]};
 });
 const requiredVoxels=[];for(let x=-radius;x<=radius;x++)for(let y=-radius;y<=radius;y++)for(let z=-radius;z<=radius;z++)requiredVoxels.push([x,y,z]);
 return {version:'voxel-center-corner-1',name,capacity:8,allowReflections:mirrors,orientations,requiredVoxels,required:support(requiredVoxels).map(c=>({pos:c.pos,generation:0})),placementDomain:{kind:'scaled_cubic',translationStep:2},domain:'Integer voxel grid; coordinates in half-unit steps; centers and corners required',boundary:'Open exterior; exact target voxel centers and corners',proofScope:'Capacity legality is equivalent to nonoverlap of unit voxels under cubic rotations and integer physical translations. No unrestricted-isometry claim.'};
}
// Independent voxel replay: no point weights, candidate graph or m-values.
export function verifyVoxelPatch(model,placements,{requireTarget=true}={}){
 const occupied=new Set();
 for(const p of placements){
  const o=model.orientations[p.oi];if(!o||p.translation.length!==3||p.translation.some(x=>!Number.isSafeInteger(x)||x%2))return {ok:false,reason:'invalid voxel placement'};
  for(const v of o.voxels){const q=v.map((x,i)=>x+p.translation[i]/2),k=key(q);if(occupied.has(k))return {ok:false,reason:'voxel overlap',at:q};occupied.add(k);}
 }
 const covered=model.requiredVoxels.filter(v=>occupied.has(key(v))).length;
 return {ok:!requireTarget||covered===model.requiredVoxels.length,covered,required:model.requiredVoxels.length,voxels:occupied.size};
}
