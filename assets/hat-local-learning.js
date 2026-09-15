import {A2_TILE_LOOPS,A2_SYMMETRIES,tileOrientations,a2Transform,a2Add,a2Sub,solveA2Tiling,makeHexBoundary,NoA2Marking,SparseA2Marking} from './a2-tiling-engine.js?v=20260915-fixed-prefix';
export const VERSION='hat-local-patches-v1';
export const ORIENTATIONS=tileOrientations('hat',A2_TILE_LOOPS.hat);
export const HAT=ORIENTATIONS[0];
const parity=p=>((p[0]>p[1])+(p[0]>p[2])+(p[1]>p[2]))%2?-1:1;
const key=p=>p.join(',');
export const compact=placements=>placements.map(p=>({orientation:p.orientation.index,translation:[...p.translation]}));
export function materialize(spec){
 const index=typeof spec.orientation==='number'?spec.orientation:spec.orientation.index,o=ORIENTATIONS[index];
 if(!o||spec.translation.length!==3||!spec.translation.every(Number.isInteger)||spec.translation.reduce((s,v)=>s+v,0)!==0)throw new Error('Invalid Hat transform');
 return {id:`hat:${index}:${spec.translation}`,tile:'hat',orientation:o,translation:[...spec.translation],loop:o.loop.map(p=>a2Add(p,spec.translation))};
}
export function verifyPatch(specs,support=[]){
 const sums=new Map(),marks=new Map(),seen=new Set();let conflicts=0,agreements=0;
 for(const spec of specs){const p=materialize(spec);if(seen.has(p.id))throw new Error('Duplicate Hat');seen.add(p.id);
  for(const e of p.orientation.occupancy.values()){const at=key(a2Add(e.point,p.translation)),n=(sums.get(at)||0)+e.weight;if(n>12)throw new Error('Hat point capacity exceeded');sums.set(at,n);}
  const sym=p.orientation.symmetry,sign=parity(sym.permutation);
  for(const e of support){const at=`${a2Add(a2Transform(e.point,sym),p.translation)}|${sym.permutation.indexOf(e.component)}`,value=e.value*sign;if(marks.has(at)){if(marks.get(at)!==value)conflicts++;else agreements++;}else marks.set(at,value);}
 }
 return {tiles:specs.length,completePoints:[...sums.values()].filter(v=>v===12).length,openPoints:[...sums.values()].filter(v=>v<12).length,conflicts,agreements,compatible:conflicts===0};
}
// Canonicalize the full undecorated point model under all A2 symmetries and
// translations, so training/test splits cannot share rotated/reflected copies.
export function canonicalPatch(specs){
 const data=specs.map(spec=>{const p=materialize(spec);return [...p.orientation.occupancy.values()].map(e=>({point:a2Add(e.point,p.translation),weight:e.weight}));});
 let best=null;
 for(const sym of A2_SYMMETRIES){const transformed=data.map(tile=>tile.map(e=>({point:a2Transform(e.point,sym),weight:e.weight})));const origin=transformed.flat().map(e=>e.point).sort((a,b)=>a[0]-b[0]||a[1]-b[1]||a[2]-b[2])[0];const value=transformed.map(tile=>tile.map(e=>`${a2Sub(e.point,origin)}:${e.weight}`).sort().join(';')).sort().join('|');if(best===null||value<best)best=value;}
 return best;
}
export function attachments(){
 const found=new Map();
 for(const o of ORIENTATIONS)for(const anchor of o.occupancy.values())for(const at of HAT.occupancy.values()){
  const translation=a2Sub(at.point,anchor.point),id=`${o.index}:${translation}`;if(found.has(id)||id==='0:0,0,0')continue;
  if([...o.occupancy.values()].some(e=>e.weight+(HAT.occupancy.get(key(a2Add(e.point,translation)))?.weight||0)>12))continue;
  found.set(id,{orientation:o.index,translation});
 }
 return [...found.values()];
}
export function pointDomain(){
 const points=new Map([...HAT.occupancy.values()].map(e=>[key(e.point),e.point]));
 const steps=[[1,-1,0],[1,0,-1],[0,1,-1],[-1,1,0],[-1,0,1],[0,-1,1]];
 for(const p of [...points.values()])for(const d of steps){const q=a2Add(p,d);points.set(key(q),q);}
 return [...points.values()].sort((a,b)=>a[0]-b[0]||a[1]-b[1]);
}
// Signed equality classes learned ONLY from overlaps in the observed patches.
// An odd sign cycle forces a class to zero; other classes receive distinct
// integer labels. Distinct labels on unrelated classes are a hypothesis, not
// proof that an unseen placement is impossible.
export function encode(samples){
 const support=pointDomain().flatMap(point=>[0,1,2].map(component=>({tile:'hat',point:[...point],component}))),n=support.length;
 const parent=Array.from({length:n},(_,i)=>i),sign=Array(n).fill(1),zero=Array(n).fill(false);let observations=0;
 function find(i){if(parent[i]!==i){const [r,s]=find(parent[i]);sign[i]*=s;parent[i]=r;}return[parent[i],sign[i]];}
 function join(i,j,relation){const [a,x]=find(i),[b,y]=find(j);if(a===b){if(x!==relation*y)zero[a]=true;return;}parent[b]=a;sign[b]=relation*x*y;zero[a]||=zero[b];}
 for(const sample of samples){verifyPatch(sample.placements);const contacts=new Map();
  for(const spec of sample.placements){const p=materialize(spec),sym=p.orientation.symmetry,s=parity(sym.permutation);
   support.forEach((e,i)=>{const at=`${a2Add(a2Transform(e.point,sym),p.translation)}|${sym.permutation.indexOf(e.component)}`;const prior=contacts.get(at);if(prior){observations++;join(i,prior.i,s*prior.sign);}else contacts.set(at,{i,sign:s});});
  }
 }
 const labels=new Map();support.forEach((e,i)=>{const [r,s]=find(i);if(!labels.has(r))labels.set(r,labels.size+1);e.value=zero[r]?0:s*labels.get(r);});
 const training=samples.map(s=>verifyPatch(s.placements,support));if(training.some(r=>!r.compatible))throw new Error('Encoding lost a training patch');
 return {version:VERSION,support,classes:labels.size,nonzero:support.filter(e=>e.value!==0).length,observations,trainingCount:samples.length,trainingConflicts:0,scope:'Learned hypothesis on a fixed one-step A2 marking domain; no supplied Hat marking.'};
}
function shuffle(items,seed){let state=seed>>>0;const a=[...items];for(let i=a.length-1;i>0;i--){state=(Math.imul(1664525,state)+1013904223)>>>0;const j=Math.floor(state/4294967296*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;}
export async function grow({seed=1,support=[],initial=[{orientation:0,translation:[0,0,0]}],target=32,budget=500,onEvent=()=>{},wait=null,audit=false}={}){
 const started=performance.now();let forced=0,branches=0;
 const r=await solveA2Tiling({boundary:makeHexBoundary(10),tiles:['hat'],maximize:true,targetPlacements:target,nodeLimit:budget,randomSeed:seed,
  initialPlacements:initial.map(materialize),fixedInitialPlacements:true,marking:support.length?new SparseA2Marking(support):new NoA2Marking(),auditFrontierGraph:audit,waitForSearchDemand:wait,
  onEvent:e=>{if(e.type==='placement'){if(e.forced)forced++;else branches++;}onEvent({type:e.type,placements:compact(e.placements),nodes:e.nodes,backtracks:e.backtracks,forced,branches});}});
 const placements=compact(r.placements),verification=verifyPatch(placements,support);
 if(!verification.compatible)throw new Error('Returned patch has a marking conflict');
 return {result:r.result,placements,verification,nodes:r.stats.nodes,backtracks:r.stats.backtracks,forced,branches,prunes:r.stats.prunes,elapsedMs:performance.now()-started};
}
export async function collect({seed=90210,trainCount=16,testCount=8,target=12,budget=120,onProgress=()=>{},wait=null}={}){
 const started=performance.now(),pairs=shuffle(attachments(),seed),training=[],test=[],attempts=[],seen=new Set();let model=null,duplicates=0;
 const trials=[...pairs,...shuffle(pairs,seed^0x9e3779b9)];
 for(let i=0;i<trials.length;i++){
  if(wait)await wait();
  const searchSeed=Math.imul(i+1,1987)^((seed^90210)>>>0);
  const r=await grow({seed:searchSeed,initial:[{orientation:0,translation:[0,0,0]},trials[i]],target,budget,wait});
  const row={attachment:trials[i],seed:searchSeed,result:r.result,tiles:r.placements.length,nodes:r.nodes,elapsedMs:r.elapsedMs};attempts.push(row);
  if(r.result==='yes'){
   if(!r.placements.some(p=>p.orientation===trials[i].orientation&&key(p.translation)===key(trials[i].translation))||!r.placements.some(p=>p.orientation===0&&key(p.translation)==='0,0,0'))throw new Error('The collection search lost its fixed seed pair');
   const canonical=canonicalPatch(r.placements);
   if(seen.has(canonical))duplicates++;
   else{seen.add(canonical);const sample={seed:searchSeed,attachment:trials[i],placements:r.placements,canonical,verification:r.verification};
    if(training.length<trainCount){training.push(sample);model=encode(training);}else test.push({...sample,evaluation:verifyPatch(sample.placements,model.support)});
   }
  }
  onProgress({attempts:attempts.length,total:trials.length,training:training.length,test:test.length,duplicates,model,latest:r.placements});
  if(training.length>=trainCount&&test.length>=testCount)break;
 }
 if(!model)throw new Error('No completed local patches were collected within this budget.');
 const survivors=pairs.filter(p=>verifyPatch([{orientation:0,translation:[0,0,0]},p],model.support).compatible).length;
 return {version:VERSION,config:{seed,trainCount,testCount,target,budget,attachmentPasses:2,domain:'A2',halo:1,rank:3},training,test,model,attempts,duplicates,
  attachmentCount:pairs.length,attachmentSurvivors:survivors,testPassed:test.filter(s=>s.evaluation.compatible).length,elapsedMs:performance.now()-started,
  status:training.length===trainCount&&test.length===testCount?'collected':'sample budget exhausted',
  semantics:'Consistent finite point-value patches, not infinite tilings. Marking exclusions are learned hypotheses.'};
}
