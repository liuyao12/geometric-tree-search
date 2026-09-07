// Cold, bounded re-review. A goal patch is not a tiling certificate.
import { createTilingStream, tileSpecs, INTERESTING_TILE_REVIEW } from '../apps/3d-lattice-tiler/engine.js';
import { writeFileSync } from 'node:fs';
const modes=Object.keys(tileSpecs.TILING_REGISTRY);
const lanes=['free_range','learning_free_range','rl_free_range','gcts_rl','translational','isohedral'];
const results=[];
for(const mode_key of modes) {
 const attempts=[];
 for(const tiling_strategy of lanes) {
  let final;
  const gcts=['learning_free_range','gcts_rl'].includes(tiling_strategy);
  const rl=['rl_free_range','gcts_rl'].includes(tiling_strategy);
  const started=performance.now();
  for await(const e of createTilingStream({mode_key,tiling_strategy,criterion:'count',target_val:8,
   move_order:rl?'rl':'balanced',agent_policy:rl?'cold_linucb':null,
   complete_lattice_point_branching:true,gcts_failure_marking:gcts,
   template_preflight:false,known_periodic_template:null,
   node_limit:500,time_limit_ms:250,safety_max_tiles:40,ui_yield_interval_ms:1000},tileSpecs)) {
   if(e.type==='finished') final=e;
  }
  if(!final) throw Error(`Missing terminal result: ${mode_key}/${tiling_strategy}`);
  attempts.push({lane:tiling_strategy,result_kind:final.result_kind,success:final.success,
   can_tile:final.can_tile,search_incomplete:final.search_incomplete,
   evidence:final.tiling_evidence,tiles:final.tile_count,
   milliseconds:Math.round(performance.now()-started),marking_rank:final.search_stats?.marking_rank});
 }
 const row={mode_key,attempts};results.push(row);console.log(JSON.stringify(row));
}
writeFileSync(process.argv[2],JSON.stringify({date:'2026-09-06',scope:'weighted lattice functions, native system symmetry; cold bounded regression, not exhaustive classification',
 criteria:INTERESTING_TILE_REVIEW.criteria,limits:{milliseconds_per_lane:250,nodes:500,target_tiles:8},systems:modes.length,results},null,2));
