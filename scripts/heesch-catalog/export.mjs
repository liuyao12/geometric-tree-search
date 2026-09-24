import fs from 'node:fs';import {catalog} from '../../apps/3d-lattice-tiler/v2/model.js';import {tileSpecs} from '../../apps/3d-lattice-tiler/engine.js';
const rows=[];
for(const c of catalog()){
 const entry=tileSpecs.TILING_REGISTRY[c.id],tiles=entry?.build()??[],row={id:c.id,name:c.name,group:c.group,note:c.note,evidence:c.evidence,categories:entry?.category??[],components:tiles.map(t=>({name:t.name,vertices:t.verts,faces:t.faces,solidAngle:t.solid_angle}))};
 if(entry?.category?.includes('Polycubes')){
  const t=tiles[0],scale=tileSpecs.SCALE,occ=new Map(t.occupancy_points.map(p=>[p.pos.map(x=>x/scale).join(','),p.weight])),pts=[...occ.keys()].map(k=>k.split(',').map(Number)),lo=[0,1,2].map(i=>Math.min(...pts.map(p=>p[i]))),hi=[0,1,2].map(i=>Math.max(...pts.map(p=>p[i]))),vox=new Map();
  for(let x=lo[0];x<=hi[0];x++)for(let y=lo[1];y<=hi[1];y++)for(let z=lo[2];z<=hi[2];z++){
   let value=occ.get([x,y,z].join(','))??0;
   for(let a=0;a<=1;a++)for(let b=0;b<=1;b++)for(let d=0;d<=1;d++)if(a||b||d)value-=vox.get([x-a,y-b,z-d].join(','))??0;
   if(value!==0&&value!==1)throw Error(`Nonvoxel occupancy ${c.id}: ${value}`);if(value)vox.set([x,y,z].join(','),value);
  }
  row.voxels=[...vox.keys()].map(k=>k.split(',').map(Number));
  const replay=new Map();for(const v of row.voxels)for(let a=0;a<=1;a++)for(let b=0;b<=1;b++)for(let d=0;d<=1;d++){const k=[v[0]+a,v[1]+b,v[2]+d].join(',');replay.set(k,(replay.get(k)??0)+1);}
  if(replay.size!==occ.size||[...occ].some(([k,v])=>replay.get(k)!==v))throw Error('Voxel export mismatch');row.voxelCornerReplay=true;
 }
 rows.push(row);
}
const output=process.argv[2]??'data/heesch-catalog/catalog.json';fs.writeFileSync(output,JSON.stringify({source:'apps/3d-lattice-tiler/v2/model.js catalog()',systems:rows,figures:tileSpecs.figureCatalog.map(f=>({id:f.id,name:f.name,mode:f.mode_key,index:f.tile_index,systems:f.system_names}))},null,2));console.log(JSON.stringify({systems:rows.length,polycubes:rows.filter(r=>r.voxels).map(r=>[r.id,r.voxels.length])}));
