// Exact finite point-value quotient search. This is a bounded periodic control,
// not an unbounded-growth baseline. All quotient obligations are generation 0.
export const PERIODIC_VERSION = 'point-quotient-v1';
const key = p => p.join(',');
const add = (a,b) => a.map((x,i)=>x+b[i]);
const sub = (a,b) => a.map((x,i)=>x-b[i]);
const mod = (x,n) => ((x%n)+n)%n;
const signature = ps => ps.map(p=>`${key(p.pos)}:${p.weight}`).sort().join('|');
const minimum = ps => [0,1,2].map(i=>Math.min(...ps.map(p=>p.pos[i])));
const pause = () => new Promise(resolve=>setTimeout(resolve,0));
export function reducePoint(p,h) {
  let [x,y,z]=p, q=Math.floor(z/h.f); x-=q*h.c; y-=q*h.e; z-=q*h.f;
  q=Math.floor(y/h.d); x-=q*h.b; y-=q*h.d;
  return [mod(x,h.a),y,z];
}
export const periodVectors = h => [[h.a,0,0],[h.b,h.d,0],[h.c,h.e,h.f]];
export function* hnfForms(volume,diagonal=false) {
  // Lazy enumeration avoids allocating/sorting millions of skew cells.
  const triples=[];
  for(let a=1;a<=volume;a++) if(volume%a===0)
    for(let d=1;d<=volume/a;d++) if(volume%(a*d)===0) triples.push([a,d,volume/a/d]);
  triples.sort((x,y)=>(Math.max(...x)-Math.min(...x))-(Math.max(...y)-Math.min(...y)));
  for(const [a,d,f] of triples) for(let b=0;b<(diagonal?1:a);b++)
    for(let c=0;c<(diagonal?1:a);c++) for(let e=0;e<(diagonal?1:d);e++) {
      if(!diagonal && b+c+e===0) continue;
      yield {a,d,f,b,c,e};
    }
}
export function exactOrientations(prototiles,capacity) {
  if(!Number.isSafeInteger(capacity)||capacity<1) throw Error('Integer point capacity required');
  return prototiles.flatMap((tile,type)=> {
    const seen=new Set();
    return tile.unique_orientations.flatMap((orientation,index)=> {
      const points=orientation.occupancy;
      if(!points?.length || points.some(p=>p.pos.length!==3||p.pos.some(x=>!Number.isSafeInteger(x))||!Number.isSafeInteger(p.weight)||p.weight<1||p.weight>capacity)
        ||new Set(points.map(p=>key(p.pos))).size!==points.length) throw Error('Exact integer point data required; numerical solid angles are unsupported');
      const origin=minimum(points), s=signature(points.map(p=>({...p,pos:sub(p.pos,origin)})));
      if(seen.has(s)) return []; seen.add(s);
      return [{type,index,orientation,points,species:tile.__species_id??type,
        translationLattice:tile.is_polycube&&tile.polycube_lattice==='fcc'?'fcc':'z3'}];
    });
  });
}
function allowed(p,o) {return o.translationLattice!=='fcc'||mod(p.reduce((a,b)=>a+b,0),2)===0;}
const residue = (p,h) => {const [x,y,z]=reducePoint(p,h); return x+h.a*(y+h.d*z);};
function validHnf(h) {return h&&['a','d','f'].every(k=>Number.isSafeInteger(h[k])&&h[k]>0)&&['b','c','e'].every(k=>Number.isSafeInteger(h[k])&&h[k]>=0)&&h.b<h.a&&h.c<h.a&&h.e<h.d&&Number.isSafeInteger(h.a*h.d*h.f);}

// Independent certificate replay uses BigInt arithmetic and unfurled input
// supports, not the search's rows, graph, occupancy or conflict trail.
export function verifyPeriodic(orientations,capacity,certificate) {
  const h=certificate?.hnf;
  if(!validHnf(h)||!Number.isSafeInteger(capacity)||capacity<1||!Array.isArray(certificate.motif)||!certificate.motif.length) return false;
  const q=h.a*h.d*h.f;
  if(q>1000000||periodVectors(h).some(v=>orientations.some(o=>!allowed(v,o)))) return false;
  const totals=Array(q).fill(0n), used=new Set();
  const floor=(x,n)=>{let r=x/n;if(x<0n&&x%n)r--;return r;};
  for(const m of certificate.motif) {
    const o=orientations.find(o=>o.type===m.prototile_idx&&o.index===m.orientation_index), t=m.translation;
    if(!o||!Array.isArray(t)||t.length!==3||!t.every(Number.isSafeInteger)||!allowed(t,o))return false;
    // Identity is full weighted shape plus its anchor modulo the period lattice.
    const anchor=minimum(o.points), shape=signature(o.points.map(p=>({...p,pos:sub(p.pos,anchor)})));
    const id=`${o.species}:${shape}@${key(reducePoint(add(anchor,t),h))}`;
    if(used.has(id))return false; used.add(id);
    for(const p of o.points) {
      let [x,y,z]=p.pos.map((v,i)=>BigInt(v)+BigInt(t[i]));
      const a=BigInt(h.a),d=BigInt(h.d),f=BigInt(h.f);
      let k=floor(z,f); x-=k*BigInt(h.c);y-=k*BigInt(h.e);z-=k*f;
      k=floor(y,d);x-=k*BigInt(h.b);y-=k*d;x-=floor(x,a)*a;
      const r=Number(x+a*(y+d*z)); totals[r]+=BigInt(p.weight);
      if(totals[r]>BigInt(capacity))return false;
    }
  }
  return totals.every(w=>w===BigInt(capacity));
}
export function signedPermutations(reflections=false) {
  const result=[];
  for(const p of [[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]])for(let mask=0;mask<8;mask++) {
    const inversions=p.reduce((n,x,i)=>n+p.slice(i+1).filter(y=>x>y).length,0);
    if(!reflections&&(inversions+[0,1,2].filter(i=>mask&(1<<i)).length)%2)continue;
    result.push(p.map((j,i)=>[0,1,2].map(k=>k===j?(mask&(1<<i)?-1:1):0)));
  }
  return result;
}
const transform=(r,p)=>r.map(row=>row.reduce((s,x,i)=>s+x*p[i],0));
// A lattice-normalizing affine isometry taking the root to each motif member
// and permuting the ENTIRE motif proves tile transitivity of the infinite set.
export function certifyIsohedral(orientations,capacity,certificate,reflections=false) {
  if(!verifyPeriodic(orientations,capacity,certificate))return null;
  const h=certificate.hnf;
  const tiles=certificate.motif.map(m=> {
    const o=orientations.find(o=>o.type===m.prototile_idx&&o.index===m.orientation_index);
    const ps=o.points.map(p=>({...p,pos:add(p.pos,m.translation)}));
    return {species:o.species,ps,anchor:minimum(ps)};
  });
  const identity=(species,ps)=>{const a=minimum(ps);return `${species}:${signature(ps.map(p=>({...p,pos:sub(p.pos,a)})))}@${key(reducePoint(a,h))}`;};
  const ids=new Map(tiles.map((t,i)=>[identity(t.species,t.ps),i]));
  if(ids.size!==tiles.length)return null;
  const witnesses=[];
  for(let target=0;target<tiles.length;target++) {
    let witness=null;
    for(const r of signedPermutations(reflections)) {
      if(periodVectors(h).some(v=>reducePoint(transform(r,v),h).some(Boolean)))continue;
      const root=tiles[0].ps.map(p=>({...p,pos:transform(r,p.pos)}));
      const shift=sub(tiles[target].anchor,minimum(root));
      const permutation=tiles.map(t=>ids.get(identity(t.species,t.ps.map(p=>({...p,pos:add(transform(r,p.pos),shift)})))));
      if(permutation[0]===target&&permutation.every(i=>i!==undefined)&&new Set(permutation).size===tiles.length) {
        witness={rotation:r,translation:shift,permutation};break;
      }
    }
    if(!witness)return null; witnesses.push(witness);
  }
  return {method:'lattice_normalizing_affine_isometries',include_reflections:reflections,witnesses};
}

export class QuotientGraph {
  constructor(rows,q,capacity) {
    this.rows=rows;this.capacity=capacity;this.totals=new Float64Array(q);
    this.byPoint=Array.from({length:q},()=>[]);this.live=new Uint8Array(rows.length).fill(1);
    this.selected=new Set();this.trail=[];
    rows.forEach((r,i)=>r.entries.forEach(([p])=>this.byPoint[p].push(i)));
    this.degree=Int32Array.from(this.byPoint.map(a=>a.length));
  }
  disable(i) {if(!this.live[i])return;this.live[i]=0;this.trail.push(i);for(const [p]of this.rows[i].entries)this.degree[p]--;}
  apply(i) {
    const mark=this.trail.length;this.selected.add(i);this.disable(i);
    for(const [p,w]of this.rows[i].entries)this.totals[p]+=w;
    for(const [p]of this.rows[i].entries)for(const j of this.byPoint[p])
      if(this.live[j]&&this.rows[j].entries.some(([r,w])=>this.totals[r]+w>this.capacity))this.disable(j);
    return mark;
  }
  undo(i,mark) {
    for(const [p,w]of this.rows[i].entries)this.totals[p]-=w;this.selected.delete(i);
    while(this.trail.length>mark){const j=this.trail.pop();this.live[j]=1;for(const [p]of this.rows[j].entries)this.degree[p]++;}
  }
  decision() {
    let pivot=-1,forced=-1;
    for(let p=0;p<this.totals.length;p++)if(this.totals[p]<this.capacity) {
      if(!this.degree[p])return {kind:'dead',point:p};
      if(this.degree[p]===1)forced=p;
      if(pivot<0||this.degree[p]<this.degree[pivot])pivot=p;
    }
    if(pivot<0)return {kind:'complete'};
    const point=forced>=0?forced:pivot;
    return {kind:forced>=0?'forced':'branch',point,options:this.byPoint[point].filter(i=>this.live[i])};
  }
}

export async function searchPeriodic(orientations,capacity,config={},stop={},progress=()=>{},checkpoint=async()=>{},trace=async()=>{}) {
  let lastYield=performance.now(), activeDomain=null;
  const cooperative=async()=>{if(!stop.stop&&performance.now()-lastYield>16){await pause();if(!stop.stop)await checkpoint({stats:{...stats},hnf:activeDomain?.h,counts:activeDomain?.tileCounts});lastYield=performance.now();}};
  const started=performance.now(), iso=config.tiling_strategy==='isohedral';
  const maxTiles=Math.max(1,Math.floor(config.periodic_patch_max_tiles??config.periodic_tile_count??8));
  const counts=config.periodic_patch_max_tiles!==undefined||config.periodic_tile_count===undefined?Array.from({length:maxTiles},(_,i)=>i+1):[maxTiles];
  const maxVolume=config.periodic_template_max_volume??512, maxForms=config.periodic_hnf_candidate_limit??20000;
  const stats={quotients:0,nodes:0,forced:0,decisions:0,backtracks:0,eliminations:0,capped_quotients:0,isohedral_rejections:0,max_candidates:0,max_edges:0};
  let reason=null;
  const interrupted=()=>{if(stop.stop)reason='stopped';else if(config.time_limit_ms>0&&performance.now()-started>=config.time_limit_ms)reason='time_limit';else if(config.node_limit>0&&stats.nodes>=config.node_limit)reason='node_limit';return !!reason;};
  const masses=new Map();for(const o of orientations){const mass=o.points.reduce((s,p)=>s+p.weight,0);if(masses.has(o.type)&&masses.get(o.type)!==mass)throw Error('Orientation mass mismatch');masses.set(o.type,mass);}
  const volumes=new Map();
  for(const count of counts) {
    let sums=new Set([0]);for(let i=0;i<count;i++){const next=new Set();for(const sum of sums)for(const m of masses.values())if(sum+m<=maxVolume*capacity)next.add(sum+m);sums=next;}
    for(const mass of sums)if(mass%capacity===0){const q=mass/capacity;if(!volumes.has(q))volumes.set(q,[]);volumes.get(q).push(count);}
  }
  const required=new Set(orientations.map(o=>o.species));
  const requireAll=config.periodic_require_all_types!==false;
  // Give each volume its boxes and a small skew tranche before completing
  // the remaining HNFs. Small oblique one-tile periods must not wait behind
  // every larger box; hard small quotients must not starve larger motifs.
  function* domains() {
    const ordered=[...volumes].sort((a,b)=>a[0]-b[0]);
    for(const [q,tileCounts]of ordered){
      for(const h of hnfForms(q,true))yield {q,tileCounts,h};
      let i=0;for(const h of hnfForms(q,false)){if(i++>=64)break;yield {q,tileCounts,h};}
    }
    for(const [q,tileCounts]of ordered){let i=0;for(const h of hnfForms(q,false))if(i++>=64)yield {q,tileCounts,h};}
  }
  for(const {q,tileCounts,h}of domains()) {
    if(interrupted())break;
    if(stats.quotients>=maxForms){reason='quotient_limit';break;}
    if(periodVectors(h).some(v=>orientations.some(o=>!allowed(v,o))))continue;
    stats.quotients++; activeDomain={h,tileCounts}; const rows=[], roots=[];
    for(const o of orientations) {
      for(let x=0;x<h.a;x++)for(let y=0;y<h.d;y++)for(let z=0;z<h.f;z++) {
        const t=[x,y,z];if(!allowed(t,o))continue;
        const weights=new Map();for(const p of o.points){const r=residue(add(p.pos,t),h);weights.set(r,(weights.get(r)||0)+p.weight);}
        if([...weights.values()].some(w=>w>capacity))continue;
        const id=rows.length;rows.push({entries:[...weights],o,translation:t});
        if(x+y+z===0)roots.push(id);
      }
      if(interrupted())break;
      await cooperative();
    }
    if(interrupted())break;
    const graph=new QuotientGraph(rows,q,capacity), chosen=[];
    stats.max_candidates=Math.max(stats.max_candidates,rows.length);stats.max_edges=Math.max(stats.max_edges,rows.reduce((n,r)=>n+r.entries.length,0));
    let local=0,capped=false,found=null;
    const limit=config.periodic_nodes_per_quotient??4000;
    const state=(action,details={})=>trace({action,...details,hnf:h,counts:tileCounts,stats:{...stats},
      motif:chosen.map(i=>({prototile_idx:rows[i].o.type,orientation_index:rows[i].o.index,translation:rows[i].translation}))});
    const reject=async(reason,details={})=>{await state('reject',{reason,...details});return false;};
    async function dfs() {
      if(stats.nodes%32===0)await cooperative();
      if(interrupted())return false;
      stats.nodes++;if(++local>limit){capped=true;return false;}
      const decision=graph.decision();
      if(decision.kind==='dead')return reject('dead_point',{point:decision.point});
      if(decision.kind==='complete') {
        if(!tileCounts.includes(chosen.length)||requireAll&&[...required].some(s=>!chosen.some(i=>rows[i].o.species===s)))return reject('tile_inventory');
        const cert={version:PERIODIC_VERSION,kind:'exact_point_quotient',model:'integer point values on Z3',capacity,point_model:orientations.map(o=>({type:o.type,index:o.index,species:o.species,translationLattice:o.translationLattice,points:o.points.map(p=>({pos:p.pos,weight:p.weight}))})),hnf:h,period_vectors:periodVectors(h),cell_volume:q,
          motif:chosen.map(i=>({prototile_idx:rows[i].o.type,orientation_index:rows[i].o.index,orientation_id:`${rows[i].o.type}:${rows[i].o.index}`,translation:rows[i].translation})),include_reflections:!!config.include_mirrors};
        if(!verifyPeriodic(orientations,capacity,cert))throw Error('Independent periodic replay failed');
        if(iso){cert.isohedral=certifyIsohedral(orientations,capacity,cert,!!config.include_mirrors);if(!cert.isohedral){stats.isohedral_rejections++;return reject('not_isohedral');}}
        found=cert;return true;
      }
      if(chosen.length>=Math.max(...tileCounts))return reject('motif_size');
      if(decision.kind==='forced')stats.forced++;else stats.decisions++;
      for(const i of decision.options) {
        const mark=graph.apply(i);stats.eliminations+=graph.trail.length-mark;chosen.push(i);
        await state('place',{forced:decision.kind==='forced'});
        const done=await dfs();chosen.pop();graph.undo(i,mark);
        if(done)return true;stats.backtracks++;
        // Successful unwinding and resource cleanup are not failed attempts.
        if(capped||reason)return false;
        await state('backtrack');
      }
      return false;
    }
    // Translating ANY chosen placement to the origin is sound. All root
    // orientations/types are retained; no unproved rotational quotienting.
    for(const i of roots) {
      const mark=graph.apply(i);chosen.push(i);await state('place',{root:true});
      await dfs();chosen.pop();graph.undo(i,mark);
      if(found||capped||reason)break;
      await state('backtrack',{root:true});
    }
    if(capped)stats.capped_quotients++;
    progress({hnf:h,counts:tileCounts,stats:{...stats},certified:!!found});
    if(found)return {certificate:found,stats:{...stats,elapsed_ms:performance.now()-started},status:'certified_tiling'};
    await cooperative();
  }
  return {certificate:null,status:'unknown',reason:reason??(stats.capped_quotients?'per_quotient_node_limit':'bounded_period_family'),stats:{...stats,elapsed_ms:performance.now()-started},scope:{max_tiles:maxTiles,max_volume:maxVolume,max_quotients:maxForms,all_tested_quotients_exhausted:!reason&&!stats.capped_quotients}};
}

function displayStats(stats,config) {
  return {...stats,search_model:PERIODIC_VERSION,tiling_strategy:config.tiling_strategy,
    visited_nodes:stats.nodes??0,branch_choices_visited:stats.decisions??0};
}

function placementSnapshot(prototiles,capacity,colors,placements,searchStats,previewKind=null) {
  const faces=[],totals=new Map();
  placements=placements.map((m,n)=> {
    const o=prototiles[m.prototile_idx].unique_orientations[m.orientation_index];
    const colorId=(m.periodic_motif_index??n)%colors.length;
    const vs=o.verts.map(p=>add(p,m.translation));
    o.faces.forEach((f,j)=>faces.push({key:`${n}:${j}`,v:f.map(k=>vs[k]),color:colors[colorId],color_id:colorId,type_idx:m.prototile_idx,internal:false}));
    for(const p of o.occupancy){const k=key(add(p.pos,m.translation));totals.set(k,(totals.get(k)||0)+p.weight);}
    return {...m,color_id:colorId};
  });
  const frontier=[...totals].filter(([,w])=>w<capacity).map(([k,weight])=>({pos:k.split(',').map(Number),weight,max_value:capacity,frontier:true}));
  return {type:'full_update',faces,placements,tile_count:placements.length,frontier_points:frontier,
    preview_kind:previewKind,tile_counts:prototiles.map((_,type)=>({type_idx:type,count:placements.filter(p=>p.prototile_idx===type).length,color:colors[type%colors.length]})),
    frontier_stats:{point_count:frontier.length,total_faces:faces.length,min_gen:0},search_stats:searchStats};
}

export async function* periodicStream(config,prototiles,capacity,colors,stop={}) {
  let orientations,unsupported;
  try {orientations=exactOrientations(prototiles,capacity);}catch(error){unsupported=error.message;}
  yield {type:'search_prepared',search_model:PERIODIC_VERSION,orientations:orientations?.length??0};
  // Always draw the seed, even if no admissible quotient or exact adapter exists.
  // This is only an input preview; it makes no claim of extendibility.
  let snapshot=placementSnapshot(prototiles,capacity,colors,
    prototiles[0]?.unique_orientations?.length?[{prototile_idx:0,orientation_index:0,translation:[0,0,0]}]:[],
    displayStats({},config),'seed');
  yield snapshot;
  if(unsupported){yield {type:'finished',success:false,result_kind:'search_incomplete',can_tile:null,search_incomplete:true,tile_count:snapshot.tile_count,
    termination_reason:'unsupported_exact_data',message:unsupported,search_stats:snapshot.search_stats};return;}
  // Every checkpoint suspends the producer until the consumer resumes it.
  const updates=[];let done=false,result,error,resume=null;
  const checkpoint=p=>new Promise(resolve=>{
    resume=resolve;
    const searchStats=displayStats(p.stats,config);
    const message=p.action
      ? {...placementSnapshot(prototiles,capacity,colors,p.motif,searchStats,'search_state'),
          periodic_state:{action:p.action,reason:p.reason,forced:!!p.forced,root:!!p.root,point:p.point,hnf:p.hnf,counts:p.counts}}
      : {type:'periodic_work',...p,search_stats:searchStats};
    updates.push({message,release:resolve});
  });
  const report=p=>updates.push({message:{type:'periodic_progress',...p,search_stats:displayStats(p.stats,config)}});
  const task=searchPeriodic(orientations,capacity,config,stop,report,checkpoint,checkpoint).then(r=>{result=r;done=true;},e=>{error=e;done=true;});
  try {
    // Drain final queued snapshots as well as those produced before completion.
    while(!done||updates.length){
      while(updates.length){const {message,release}=updates.shift();if(message.type==='full_update')snapshot=message;yield message;if(release){resume=null;release();}}
      if(!done)await pause();
    }
  } finally {
    if(!done){stop.stop=true;if(resume)resume();await task;}
  }
  await task;if(error)throw error;
  const cert=result.certificate,iso=config.tiling_strategy==='isohedral';
  const searchStats=displayStats(result.stats,config);
  if(!cert){yield {type:'finished',success:false,result_kind:'search_incomplete',can_tile:null,search_incomplete:true,tile_count:snapshot.tile_count,
    termination_reason:result.reason,search_stats:searchStats,search_scope:result.scope};return;}
  cert.prototile_counts=prototiles.map((_,type)=>({prototile_idx:type,count:cert.motif.filter(m=>m.prototile_idx===type).length})).filter(p=>p.count);
  cert.mixed_prototile=new Set(cert.motif.map(m=>orientations.find(o=>o.type===m.prototile_idx).species)).size>1;
  yield {type:iso?'isohedral_certificate':'translational_check',certified:true,patch_size:cert.motif.length,periodic_template:cert};
  const placements=[],limit=Math.min(Math.max(1,+config.safety_max_tiles||2000),config.criterion==='count'?Math.max(1,+config.target_val||80):Math.max(cert.motif.length*8,24));
  for(let radius=0;placements.length<limit;radius++) {
    for(let x=-radius;x<=radius;x++)for(let y=-radius;y<=radius;y++)for(let z=-radius;z<=radius;z++) {
      if(Math.max(Math.abs(x),Math.abs(y),Math.abs(z))!==radius)continue;
      for(let i=0;i<cert.motif.length&&placements.length<limit;i++) {
        const m=cert.motif[i];
        const t=m.translation.map((v,j)=>v+x*cert.period_vectors[0][j]+y*cert.period_vectors[1][j]+z*cert.period_vectors[2][j]);
        placements.push({...m,translation:t,periodic_motif_index:i});
      }
    }
  }
  searchStats.growth_axis_rank=3;
  yield placementSnapshot(prototiles,capacity,colors,placements,searchStats);
  yield {type:'finished',success:true,result_kind:'certified_tiling',can_tile:true,search_incomplete:false,tile_count:placements.length,goal_reached:config.criterion==='count'&&placements.length>=config.target_val,search_stats:searchStats,
    tiling_evidence:{kind:iso?'isohedral_certificate':'translational_certificate',certified:true,strategy:config.tiling_strategy,model:'integer point values; geometric faithfulness separate',patch_size:cert.motif.length,certificate:cert,period_vectors:cert.period_vectors}};
}
