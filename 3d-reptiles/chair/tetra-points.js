// Exact geometric control: rational sample orbits cover every occupancy class
// of the common wedge arrangement. No arrow/color matching values.
import {ATOMS,ATOMIC_TEMPLATES} from './tetra-relief.js?v=20260923-centered-union';
import {VARIANTS,key} from './chair44.js';
import {selectFrontier} from './frontier-order.js';
export const FULL=(1n<<BigInt(ATOMS.length))-1n;
const BITS=ATOMS.map((_,i)=>1n<<BigInt(i));
export function createTetraPointModel(){
 const cache=new Map();
 function clearCache(){cache.clear();}
 function compile({variantId,origin}){
  const id=`${variantId}@${key(origin)}`;
  if(!cache.has(id))cache.set(id,{id,variantId,origin:[...origin],
   cells:VARIANTS[variantId].cells.map(c=>key(c.map((v,i)=>v+origin[i]))),
   voxels:ATOMIC_TEMPLATES[variantId].map(c=>({id:key(c.cell.map((v,i)=>v+origin[i])),mask:c.mask}))});
  return cache.get(id);
 }
 function indexState(placements){
  const occupancy=new Map(),generations=new Map();
  for(const p of placements)for(const c of compile(p).voxels){
   const old=occupancy.get(c.id)??0n;
   if(old&c.mask)throw Error('Overlapping tetrahedral chambers');
   occupancy.set(c.id,old|c.mask);generations.set(c.id,Math.min(generations.get(c.id)??Infinity,p.generation??0));
  }
  return {occupancy,generations};
 }
 const isLegal=(tile,index)=>!tile.voxels.some(c=>(index.occupancy.get(c.id)??0n)&c.mask);
 function graphFor(placements){
  const index=indexState(placements),frontier=new Map(),domains=[],candidates=new Map(),seen=new Set();
  for(const [id,mask] of index.occupancy){
   if(mask===FULL)continue;
   const missing=FULL^mask,generation=index.generations.get(id),nodes=[];
   BITS.forEach((bit,i)=>{if(missing&bit){const node={id:`t:${id}:${i}`,generation,candidates:new Set()};frontier.set(node.id,node);nodes.push([bit,node]);}});
   domains.push({id,cell:id.split(',').map(Number),missing,nodes});
  }
  const domainByCell=new Map(domains.map(d=>[d.id,d]));let tested=0,rejected=0;
  // Complete support alignment: any positive atom covering any active deficit
  // has its cube here, and all 24 orientations/support cubes are enumerated.
  for(const d of domains)for(let variantId=0;variantId<ATOMIC_TEMPLATES.length;variantId++)for(const support of ATOMIC_TEMPLATES[variantId]){
   if(!(support.mask&d.missing))continue;
   const origin=d.cell.map((v,i)=>v-support.cell[i]),id=`${variantId}@${key(origin)}`;
   if(seen.has(id))continue;seen.add(id);tested++;
   const tile=compile({variantId,origin});if(!isLegal(tile,index)){rejected++;continue;}
   let generation=Infinity;
   for(const c of tile.voxels){
    const domain=domainByCell.get(c.id);if(!domain)continue;
    for(const [bit,node] of domain.nodes)if(c.mask&bit){node.candidates.add(id);generation=Math.min(generation,node.generation);}
   }
   candidates.set(id,{id,variantId,origin,cells:tile.cells,generation:generation+1});
  }
  const {dead,forced,selected}=selectFrontier([...frontier.values()]);
  const choices=dead?[]:[...(selected?.candidates??[])].map(id=>candidates.get(id));
  choices.sort((a,b)=>a.origin.reduce((s,v)=>s+v*v,0)-b.origin.reduce((s,v)=>s+v*v,0)||a.id.localeCompare(b.id));
  return {index,frontier,candidates,choices,dead:dead?.id??null,forced:Boolean(forced),tested,rejected};
 }
 return {compile,indexState,isLegal,graphFor,clearCache};
}
