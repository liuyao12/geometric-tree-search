import {runGrowthExperiment} from './growth-experiment.js?v=20260921-growth';
import {placedMarkingPoints} from './marking-display.js';
export async function* legacyGrowthStream(model,config,palette,stopToken){
 const mode=config.gcts_failure_marking?(config.agent_policy?'both':'gcts'):config.agent_policy?'rl':'free';
 const data={mode,searchProtocol:'seed-growth',targetTiles:config.target_val??1000,seed:config.random_seed??10,timeMs:config.time_limit_ms??Infinity,nodes:config.node_limit??1000000,pairNodes:config.marking_pair_nodes??500,markingExtent:config.marking_extent??0,savedMarking:config.savedMarking,learningCheckpoint:config.learningCheckpoint,stop:()=>!!stopToken.stop};
 let current=model;
 yield {type:'branch_set',parent:null,branches:[{id:'growth',text:'Seed-based point growth'}]};
 for await(const e of runGrowthExperiment(model,data)){
  if(e.type==='model'){current=e.model;continue;}
  if(e.type==='marking-learning'){
   if(!current.learningAnnounced){yield {type:'marking-learning-model',model:current};current={...current,learningAnnounced:true};}
   yield e;continue;
  }
  if(e.type==='marking-learned'){yield e;continue;}
  if(!['progress','result'].includes(e.type))continue;
  const faces=[],totals=new Map(),generations=new Map(),counts=new Map();
  for(const [i,p] of e.placements.entries()){
   const o=current.orientations[p.oi],colorId=i%palette.length;
   const entry=counts.get(o.type)??{type_idx:o.type,name:`Tile ${o.type+1}`,color:palette[o.type%palette.length],count:0};entry.count++;counts.set(o.type,entry);
   for(const face of o.faces??[])faces.push({v:face.map(j=>o.vertices[j].map((v,a)=>v+p.translation[a])),color:palette[colorId],color_id:colorId,prototile_idx:o.type,internal:false});
   for(const c of o.cells){const pos=c.pos.map((v,a)=>v+p.translation[a]),k=pos.join();totals.set(k,(totals.get(k)??0)+c.weight);generations.set(k,Math.min(generations.get(k)??Infinity,p.generation??0));}
  }
  const frontier_points=[...totals].filter(([,n])=>n<current.capacity).map(([k,weight])=>({pos:k.split(',').map(Number),weight,max_value:current.capacity,layer:generations.get(k),frontier:true}));
  const centers=e.placements.map(p=>{const vertices=current.orientations[p.oi].vertices??[];return [0,1,2].map(a=>vertices.reduce((n,v)=>n+v[a],0)/Math.max(1,vertices.length)+p.translation[a]);});
  const spans=[0,1,2].map(a=>centers.length?Math.max(...centers.map(p=>p[a]))-Math.min(...centers.map(p=>p[a])):0),maxSpan=Math.max(...spans);
  const stats={...e.stats,growth_spans:spans,growth_isotropy:maxSpan?Math.min(...spans)/maxSpan:0,growth_axis_rank:spans.filter(x=>x>0).length,search_protocol:'seed-growth',visited_nodes:e.stats.attempts??0,forced_total:e.stats.forced??0,branch_choices_visited:e.stats.branches??0,backtracks:e.stats.backtracks??0,max_live_tiles:e.placements.length,marking_learning_ms:e.marking?.elapsedMs??0,marking_learning_accepted:!!e.marking?.accepted,marking_learning_pairs:e.marking?.pairs??0,marking_prunes:e.stats.markingCuts??0,termination_reason:e.reason,tiling_strategy:config.tiling_strategy};
  const frontier_stats={point_count:frontier_points.length,count:frontier_points.length,min_gen:frontier_points.length?Math.min(...frontier_points.map(p=>p.layer)):0};
  yield {type:'full_update',node_id:'growth',tile_count:e.placements.length,tile_counts:[...counts.values()],placements:e.placements,faces,frontier_points,marking_points:placedMarkingPoints(current,e.placements),frontier_stats,search_stats:stats};
  if(e.type==='result'){
   const success=['growth_checkpoint','closed_patch'].includes(e.result);
   yield {type:'node_status',id:'growth',status:success?'success':'fail',text:success?'Verified finite growth patch':e.reason??e.result};
   yield {type:'finished',success,result_kind:success?'patch_found':'search_incomplete',search_incomplete:!success,can_tile:null,tile_count:e.placements.length,search_stats:stats,marking:e.marking,verification:e.verification,tiling_evidence:{kind:'seed_growth_checkpoint',certified:false,scope:'Finite point patch with viable frontier; no infinite-tiling claim'}};
  }
 }
}
