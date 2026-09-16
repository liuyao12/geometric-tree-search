import {A2_TILE_LOOPS,A2_SYMMETRIES,tileOrientations,a2Transform,a2Add,a2Sub,solveA2Tiling,makeHexBoundary,NoA2Marking,SparseA2Marking} from './a2-tiling-engine.js?v=20260915-three-sets';
export const VERSION='tile-connection-markings-v1';
export const TILE_SETS=Object.freeze({
 turtle:{label:'Turtle',tiles:['turtle'],allowReflections:true},
 hat:{label:'Hat',tiles:['hat'],allowReflections:true},
 mixed:{label:'Turtle + Hat · rotations only',tiles:['turtle','hat'],allowReflections:false}
});
export const parity=p=>((p[0]>p[1])+(p[0]>p[2])+(p[1]>p[2]))%2?-1:1;
const key=p=>p.join(','),id=p=>`${p.tile}:${typeof p.orientation==='number'?p.orientation:p.orientation.index}:${p.translation}`;
export const compact=placements=>placements.map(p=>({tile:p.tile,orientation:p.orientation.index,translation:[...p.translation]}));
function shuffle(items,seed){let state=seed>>>0;const a=[...items];for(let i=a.length-1;i>0;i--){state=(Math.imul(1664525,state)+1013904223)>>>0;const j=Math.floor(state/4294967296*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;}
const learners=new Map();
export function createConnectionLearner(setId){
 if(learners.has(setId))return learners.get(setId);
 const config=TILE_SETS[setId];if(!config)throw new Error('Unknown tile set');
 const symmetries=A2_SYMMETRIES.filter(s=>config.allowReflections||parity(s.permutation)>0);
 const orientations=config.tiles.flatMap(tile=>tileOrientations(tile,A2_TILE_LOOPS[tile])).filter(o=>config.allowReflections||parity(o.symmetry.permutation)>0);
 const roots=config.tiles.map(tile=>({tile,orientation:0,translation:[0,0,0]}));
 function materialize(spec){
  const index=typeof spec.orientation==='number'?spec.orientation:spec.orientation.index,o=orientations.find(o=>o.tile===spec.tile&&o.index===index);
  if(!o||spec.translation?.length!==3||!spec.translation.every(Number.isSafeInteger)||spec.translation.reduce((s,v)=>s+v,0)!==0)throw new Error('Invalid placement for this tile set');
  return {id:id(spec),tile:spec.tile,orientation:o,translation:[...spec.translation],loop:o.loop.map(p=>a2Add(p,spec.translation))};
 }
 function entries(spec,support){const p=materialize(spec),sym=p.orientation.symmetry;
  return support.filter(e=>e.tile===p.tile).map(e=>({point:a2Add(a2Transform(e.point,sym),p.translation).map(v=>v||0),component:sym.permutation.indexOf(e.component),value:e.value*parity(sym.permutation)||0}));
 }
 function verifyPatch(specs,support=[]){
  const sums=new Map(),marks=new Map(),seen=new Set();let conflicts=0,agreements=0,witness=null;
  for(const spec of specs){const p=materialize(spec);if(seen.has(p.id))throw new Error('Duplicate placement');seen.add(p.id);
   for(const e of p.orientation.occupancy.values()){const at=key(a2Add(e.point,p.translation)),n=(sums.get(at)||0)+e.weight;if(n>12)throw new Error('Point capacity exceeded');sums.set(at,n);}
   for(const e of entries(spec,support)){const at=`${e.point}|${e.component}`;if(marks.has(at)){if(marks.get(at)!==e.value){conflicts++;witness??={point:e.point,component:e.component,values:[marks.get(at),e.value]};}else agreements++;}else marks.set(at,e.value);}
  }
  return {tiles:specs.length,completePoints:[...sums.values()].filter(v=>v===12).length,openPoints:[...sums.values()].filter(v=>v<12).length,conflicts,agreements,compatible:conflicts===0,witness};
 }
 function pointDomain(tile){
  const o=orientations.find(o=>o.tile===tile&&o.index===0);if(!o)throw new Error('Unknown tile');
  const points=new Map([...o.occupancy.values()].map(e=>[key(e.point),e.point]));
  const steps=[[1,-1,0],[1,0,-1],[0,1,-1],[-1,1,0],[-1,0,1],[0,-1,1]];
  for(const p of [...points.values()])for(const d of steps){const q=a2Add(p,d);points.set(key(q),q);}
  return [...points.values()].sort((a,b)=>a[0]-b[0]||a[1]-b[1]);
 }
 function connections(){const result=[];
  for(const root of roots){const source=materialize(root).orientation.occupancy,found=new Set();
   for(const o of orientations)for(const anchor of o.occupancy.values())for(const at of source.values()){
    const p={tile:o.tile,orientation:o.index,translation:a2Sub(at.point,anchor.point)},token=id(p);if(found.has(token)||token===id(root))continue;found.add(token);
    if([...o.occupancy.values()].some(e=>e.weight+(source.get(key(a2Add(e.point,p.translation)))?.weight||0)>12))continue;
    result.push({root,attachment:p});
   }
  }return result;
 }
 function canonicalPatch(specs){
  const data=specs.map(spec=>{const p=materialize(spec);return {tile:p.tile,points:[...p.orientation.occupancy.values()].map(e=>({point:a2Add(e.point,p.translation),weight:e.weight}))};});
  let best=null;
  for(const sym of symmetries){const transformed=data.map(tile=>({...tile,points:tile.points.map(e=>({point:a2Transform(e.point,sym),weight:e.weight}))}));const origin=transformed.flatMap(t=>t.points).map(e=>e.point).sort((a,b)=>a[0]-b[0]||a[1]-b[1]||a[2]-b[2])[0];const value=transformed.map(tile=>tile.tile+':'+tile.points.map(e=>`${a2Sub(e.point,origin)}:${e.weight}`).sort().join(';')).sort().join('|');if(best===null||value<best)best=value;}
  return best;
 }
 function encode(samples){
  const support=config.tiles.flatMap(tile=>pointDomain(tile).flatMap(point=>[0,1,2].map(component=>({tile,point:[...point],component})))),n=support.length;
  const parent=Array.from({length:n},(_,i)=>i),sign=Array(n).fill(1),zero=Array(n).fill(false);let observations=0;
  function find(i){if(parent[i]!==i){const [r,s]=find(parent[i]);sign[i]*=s;parent[i]=r;}return[parent[i],sign[i]];}
  function join(i,j,relation){const [a,x]=find(i),[b,y]=find(j);if(a===b){if(x!==relation*y)zero[a]=true;return;}parent[b]=a;sign[b]=relation*x*y;zero[a]||=zero[b];}
  for(const sample of samples){verifyPatch(sample.placements);const contacts=new Map();
   for(const spec of sample.placements){const p=materialize(spec),sym=p.orientation.symmetry,s=parity(sym.permutation);
    support.forEach((e,i)=>{if(e.tile!==p.tile)return;const at=`${a2Add(a2Transform(e.point,sym),p.translation)}|${sym.permutation.indexOf(e.component)}`;const prior=contacts.get(at);if(prior){observations++;join(i,prior.i,s*prior.sign);}else contacts.set(at,{i,sign:s});});
   }
  }
  const labels=new Map();support.forEach((e,i)=>{const [r,s]=find(i);if(!labels.has(r))labels.set(r,labels.size+1);e.value=zero[r]?0:s*labels.get(r);});
  if(samples.some(s=>!verifyPatch(s.placements,support).compatible))throw new Error('Encoding rejected an observed extension');
  return {version:VERSION,setId,tiles:config.tiles,allowReflections:config.allowReflections,support,classes:labels.size,nonzero:support.filter(e=>e.value!==0).length,observations,sampleCount:samples.length,scope:'Provisional matching rules inferred from finite extensions; no known markings supplied.'};
 }
 function validateModel(model){
  if(model?.version!==VERSION||model.setId!==setId||model.allowReflections!==config.allowReflections||JSON.stringify(model.tiles)!==JSON.stringify(config.tiles))throw new Error('Marking belongs to a different tile set or symmetry group');
  const domain=new Set(config.tiles.flatMap(tile=>pointDomain(tile).flatMap(point=>[0,1,2].map(c=>`${tile}:${point}|${c}`))));
  if(model.support?.length!==domain.size)throw new Error('Incomplete marking domain');
  for(const e of model.support){if(!Array.isArray(e.point)||e.point.length!==3||!e.point.every(Number.isSafeInteger)||e.point.reduce((s,v)=>s+v,0)!==0||![0,1,2].includes(e.component))throw new Error('Invalid marking coordinate');const token=`${e.tile}:${e.point}|${e.component}`;if(!domain.delete(token)||!Number.isSafeInteger(e.value)||Math.abs(e.value)>10000)throw new Error('Invalid marking entry');}
  return model;
 }
 async function grow({seed=1,support=[],initial=[roots[0]],target=32,budget=500,onEvent=()=>{},wait=null,audit=false}={}){
  const started=performance.now();let lastFailure=null;
  const r=await solveA2Tiling({boundary:makeHexBoundary(10),tiles:config.tiles,allowReflections:config.allowReflections,maximize:true,targetPlacements:target,nodeLimit:budget,randomSeed:seed,
   initialPlacements:initial.map(materialize),fixedInitialPlacements:true,completePointGrowth:true,marking:support.length?new SparseA2Marking(support):new NoA2Marking(),auditFrontierGraph:audit,waitForSearchDemand:wait,
   onEvent:e=>{if(e.type==='fail')lastFailure={point:e.choice,placements:compact(e.placements)};onEvent({type:e.type,placements:compact(e.placements),nodes:e.nodes,backtracks:e.backtracks});}});
  const placements=compact(r.placements),verification=verifyPatch(placements,support);if(!verification.compatible)throw new Error('Returned marking conflict');
  return {result:r.result,placements,verification,nodes:r.stats.nodes,backtracks:r.stats.backtracks,lastFailure,elapsedMs:performance.now()-started};
 }
 async function examine({root,attachment,seed=1,target=12,budget=120,wait=null,onEvent=()=>{},audit=false}){
  const r=await grow({initial:[root,attachment],seed,target,budget,wait,onEvent,audit});
  if(![root,attachment].every(wanted=>r.placements.some(p=>id(p)===id(wanted))))throw new Error('Search lost its fixed connection');
  return {root,attachment,seed,target,budget,...r,status:r.result==='no'?'dead':r.result==='yes'?'extended':'unresolved'};
 }
 function summarize(rows,settings,elapsedMs=0){
  const samples=[],seen=new Set();let duplicates=0;
  for(const connection of rows)if(connection.status!=='dead')for(const row of [...(connection.history||[]),connection])if(row.status==='extended'){
   const canonical=canonicalPatch(row.placements);if(seen.has(canonical)){duplicates++;continue;}seen.add(canonical);
   samples.push({root:row.root,attachment:row.attachment,seed:row.seed,placements:row.placements,canonical,verification:row.verification});
  }
  const model=samples.length?encode(samples):null,counts={extended:0,dead:0,unresolved:0},encoding={deadSeparated:0,deadUnseparated:0,extendedRejected:0,unresolvedRejected:0};
  const audited=rows.map(row=>{counts[row.status]++;const checked=model?verifyPatch([row.root,row.attachment],model.support):null,codeConflict=checked?!checked.compatible:null;
   if(row.status==='dead')encoding[codeConflict?'deadSeparated':'deadUnseparated']++;else if(codeConflict)encoding[row.status==='extended'?'extendedRejected':'unresolvedRejected']++;
   return {...row,codeConflict,codeWitness:checked?.witness||null};
  });
  if(encoding.extendedRejected)throw new Error('Point codes rejected an observed connection');
  return {version:VERSION,setId,config:{...config,...settings},connections:audited,samples,model,counts,encoding,duplicates,attachmentCount:rows.length,elapsedMs,
   semantics:'Finite extensions are provisional. Only exhausted unmarked fixed-pair searches exclude connections. Learned markings restrict subsequent marked searches and do not prove unmarked impossibility.'};
 }
 async function collect({seed=90210,target=12,budget=120,onProgress=()=>{},wait=null}={}){
  const started=performance.now(),pairs=shuffle(connections(),seed),rows=[];let model=null;
  for(let i=0;i<pairs.length;i++){
   if(wait)await wait();const row=await examine({...pairs[i],seed:Math.imul(i+1,1987)^((seed^90210)>>>0),target,budget,wait});rows.push(row);
   const counts={extended:0,dead:0,unresolved:0};rows.forEach(r=>counts[r.status]++);
   if(row.status==='extended')model=encode(rows.filter(r=>r.status==='extended'));
   onProgress({attempts:rows.length,total:pairs.length,counts,model,latest:row.placements,status:row.status});
  }
  return summarize(rows,{seed,target,budget,domain:'A2',halo:1,rank:3},performance.now()-started);
 }
 function incorporate(report,index,row){const previous=report.connections[index];
  if(!previous||id(previous.root)!==id(row.root)||id(previous.attachment)!==id(row.attachment))throw new Error('Connection mismatch');
  const history=[...(previous.history||[]),{...previous,history:undefined},row],evidence=row.status==='unresolved'&&previous.status!=='unresolved'?previous:row;
  return summarize(report.connections.map((r,i)=>i===index?{...evidence,history,lastAttempt:row}:r),report.config,report.elapsedMs+row.elapsedMs);
 }
 const learner={setId,config,orientations,roots,materialize,entries,verifyPatch,pointDomain,connections,canonicalPatch,encode,validateModel,grow,examine,summarize,collect,incorporate};learners.set(setId,learner);return learner;
}
