import {readFileSync,writeFileSync} from 'node:fs';
import {tileSpecs} from '../apps/3d-lattice-tiler/engine.js';
import {exactOrientations,searchPeriodic} from '../apps/3d-lattice-tiler/periodic-search.js';
const dir=new URL('../runs/3d-periodic-rewrite-20260910/',import.meta.url);
const rows=readFileSync(new URL('stress.jsonl',dir),'utf8').trim().split('\n').map(JSON.parse).filter(r=>!r.isohedral);
const results=[];
for(const row of rows){const ts=tileSpecs.buildCustomSystem({polycubes:[{voxels:row.voxels}]}).build(),cap=ts[0].solid_angle.max_value,os=exactOrientations(ts,cap);
 const result=await searchPeriodic(os,cap,{tiling_strategy:'isohedral',periodic_patch_max_tiles:8,periodic_nodes_per_quotient:2000,periodic_hnf_candidate_limit:20000,time_limit_ms:4000});
 results.push({id:row.id,voxels:row.voxels,...result});console.log(row.id,result.status,result.stats.elapsed_ms);
 writeFileSync(new URL('stress-refined.json',dir),JSON.stringify(results,null,2));}
