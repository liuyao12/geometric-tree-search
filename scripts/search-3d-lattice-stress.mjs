import {mkdirSync,writeFileSync,appendFileSync} from 'node:fs';
import {enumeratePolycubes} from '../assets/polycube-enumerator.js';
import {tileSpecs} from '../apps/3d-lattice-tiler/engine.js';
import {exactOrientations,searchPeriodic,verifyPeriodic,certifyIsohedral,PERIODIC_VERSION,signedPermutations,reducePoint} from '../apps/3d-lattice-tiler/periodic-search.js';
const output=new URL('../runs/3d-periodic-rewrite-20260910/',import.meta.url);mkdirSync(output,{recursive:true});
const config={periodic_patch_max_tiles:8,periodic_template_max_volume:512,periodic_hnf_candidate_limit:1000,periodic_nodes_per_quotient:1000,time_limit_ms:750,include_mirrors:false};
const results=[],counts=[];writeFileSync(new URL('stress.jsonl',output),'');
const start=performance.now(),maxSize=Number(process.argv[2]??7);
function voxelReplay(voxels,certificate) {
  if(!certificate)return null;
  const signature=ps=>ps.map(p=>`${p.pos.join(',')}:${p.weight}`).sort().join('|');
  const variants=new Map();
  for(const matrix of signedPermutations(false)) {
    const cells=voxels.map(v=>matrix.map(row=>(row.reduce((n,x,i)=>n+x*(2*v[i]+1),0)-1)/2));
    const min=[0,1,2].map(i=>Math.min(...cells.map(p=>p[i])));
    const normalized=cells.map(p=>p.map((x,i)=>x-min[i])),weights=new Map();
    for(const c of normalized)for(let x=0;x<=1;x++)for(let y=0;y<=1;y++)for(let z=0;z<=1;z++) {
      const p=c.map((v,i)=>v+[x,y,z][i]),k=p.join(',');weights.set(k,(weights.get(k)||0)+1);
    }
    variants.set(signature([...weights].map(([k,weight])=>({pos:k.split(',').map(Number),weight}))),normalized);
  }
  const totals=new Map();
  for(const m of certificate.motif) {
    const o=certificate.point_model.find(o=>o.type===m.prototile_idx&&o.index===m.orientation_index);
    const min=[0,1,2].map(i=>Math.min(...o.points.map(p=>p.pos[i])));
    const cells=variants.get(signature(o.points.map(p=>({pos:p.pos.map((x,i)=>x-min[i]),weight:p.weight}))));
    if(!cells)throw Error('Voxel orientation adapter mismatch');
    for(const c of cells){const k=reducePoint(c.map((v,i)=>v+min[i]+m.translation[i]),certificate.hnf).join(',');totals.set(k,(totals.get(k)||0)+1);}
  }
  return totals.size===certificate.cell_volume&&[...totals.values()].every(x=>x===1);
}
for(let size=1;size<=maxSize;size++) {
  const generation=enumeratePolycubes(size,{includeReflections:false});counts.push({size,count:generation.length});
  for(const candidate of generation) {
    const system=tileSpecs.buildCustomSystem({name:candidate.id,polycubes:[{name:candidate.id,voxels:candidate.voxels}],polycube_lattice:'z3'});
    const ts=system.build(),capacity=ts[0].solid_angle.max_value,os=exactOrientations(ts,capacity);
    const periodic=await searchPeriodic(os,capacity,config);
    let iso=null,isoSearch=null;
    if(periodic.certificate){if(!verifyPeriodic(os,capacity,periodic.certificate))throw Error('Replay failed');iso=certifyIsohedral(os,capacity,periodic.certificate,false);}
    if(!iso){isoSearch=await searchPeriodic(os,capacity,{...config,tiling_strategy:'isohedral'});iso=isoSearch.certificate?.isohedral;}
    const row={...candidate,capacity,orientations:os.length,periodic:periodic.status,motif:periodic.certificate?.motif.length??null,isohedral:!!iso,periodic_stats:periodic.stats,periodic_reason:periodic.reason??null,isohedral_stats:isoSearch?.stats??null,isohedral_reason:isoSearch?.reason??null,certificate:isoSearch?.certificate??periodic.certificate};
    if(iso&&row.certificate)row.certificate.isohedral=iso;
    row.voxel_replay=voxelReplay(candidate.voxels,row.certificate);
    results.push(row);appendFileSync(new URL('stress.jsonl',output),JSON.stringify(row)+'\n');
  }
  console.log({size,count:generation.length,total:results.length,seconds:(performance.now()-start)/1000});
}
const ranked=[...results].sort((a,b)=>Number(!b.isohedral)-Number(!a.isohedral)||(b.motif??99)-(a.motif??99)||b.periodic_stats.nodes-a.periodic_stats.nodes).slice(0,12);
const summary={version:PERIODIC_VERSION,scope:`All connected polycubes through ${maxSize} unit cubes modulo translations and proper cubic rotations; mirrors distinct. Solid-angle point model used by the app; voxel replay separately tests geometric faithfulness. No non-tiler or aperiodicity claim from bounded failure.`,config,counts,total:results.length,periodic:results.filter(r=>r.periodic==='certified_tiling').length,isohedral:results.filter(r=>r.isohedral).length,voxel_verified:results.filter(r=>r.voxel_replay===true).length,point_only_witnesses:results.filter(r=>r.voxel_replay===false).length,elapsed_ms:performance.now()-start,shortlist:ranked.map(({certificate,...row})=>row)};
writeFileSync(new URL('stress-summary.json',output),JSON.stringify(summary,null,2));
writeFileSync(new URL('stress-shortlist.json',output),JSON.stringify(ranked.map(r=>({id:r.id,reason:!r.isohedral?'No isohedral witness within budget':`${r.motif}-tile witness; ${r.periodic_stats.nodes} search nodes`,custom_system:{name:r.id,polycubes:[{name:r.id,voxels:r.voxels}],polycube_lattice:'z3'},certificate:r.certificate})),null,2));
console.log(JSON.stringify(summary));
