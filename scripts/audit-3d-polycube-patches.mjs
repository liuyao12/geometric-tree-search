import {readFile,writeFile} from 'node:fs/promises';
import {gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {preprocessTilingSystem,tileSpecs} from '../apps/3d-lattice-tiler/engine.js';
import {verify} from '../apps/3d-lattice-tiler/v2/search.js';
import {POLYCUBE_GCTS_CANDIDATES} from '../assets/polycube-census-candidates.js';
const folder=process.argv[2]??'/tmp/gcts-hard-audit-final',output=process.argv[3]??'/tmp/gcts-polycube-geometric-audit.json',rows=[];
const signature=cells=>cells.map(c=>`${c.pos}:${c.weight}`).sort().join('|');
for(const tile of POLYCUBE_GCTS_CANDIDATES){
 const artifact=`${tile.id}-free.json.gz`,bytes=await readFile(`${folder}/${artifact}`),record=JSON.parse(gunzipSync(bytes)),r=record.last;
 if(r?.result!=='finite_exact')continue;
 assert.equal(record.config.mirrors,false);assert.ok(verify(r.model,r.placements).ok);
 const prepared=preprocessTilingSystem({mode_key:'cube',custom_system:{polycubes:[{voxels:tile.voxels}]},polycube_lattice:'z3'},tileSpecs),seen=new Map(),overlaps=[];
 for(const [i,p] of r.placements.entries()){
  const descriptor=r.model.orientations[p.oi],o=prepared.prototiles[descriptor.type].unique_orientations[descriptor.index];
  assert.equal(signature(descriptor.cells),signature(o.occupancy),'Archived orientation identity changed');
  for(const v of tile.voxels){
   // Rotate the voxel center, use the engine's recorded normalization shift,
   // then recover its lower corner. No solid-angle or point-weight test.
   const q=o.__mark_matrix.map((row,j)=>row.reduce((sum,a,k)=>sum+a*(v[k]+.5),0)-o.__mark_shift[j]-.5+p.translation[j]),key=q.join();
   assert.ok(q.every(Number.isSafeInteger));
   if(seen.has(key))overlaps.push({voxel:q,placements:[seen.get(key),i]});else seen.set(key,i);
  }
 }
 const first=overlaps[0];rows.push({tile:tile.id,artifact,sha256:createHash('sha256').update(bytes).digest('hex'),pointVerified:true,placements:r.placements.length,voxelOverlapCount:overlaps.length,firstOverlap:first?{...first,poses:first.placements.map(i=>r.placements[i])}:null});
}
const report={schema:'gcts.vertex_point_voxel_audit.v1',scope:'Proper cubic rotations and integer translations; archived finite point windows replayed before independent voxel overlap checks.',rows};
await writeFile(output,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
