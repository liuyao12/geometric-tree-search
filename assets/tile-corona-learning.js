import {createConnectionLearner,TILE_SETS,compact,parity} from './tile-connection-learning.js?v=20260921-component-stars';
import {solveA2Tiling,makeHexBoundary,NoA2Marking,a2Add} from './a2-tiling-engine.js?v=20260921-viable-corona';
export {TILE_SETS,parity};
export const CORONA_CRITERION='viable-pair-one-corona-v2';
export const LEGACY_CORONA_CRITERION='complete-pair-one-corona-v1';
export const MARKING_ACCEPTANCE='all-valid-majority-invalid-v1';
export const markingQualifies=({valid,invalid,unresolved,validAccepted,invalidBlocked})=>valid>0&&unresolved===0&&validAccepted===valid&&(invalid===0||invalidBlocked*2>invalid);
const id=p=>`${p.tile}:${typeof p.orientation==='number'?p.orientation:p.orientation.index}:${p.translation}`;
const pairId=r=>`${id(r.root)}>${id(r.attachment)}`;
const cache=new Map();
export function createCoronaLearner(setId,{lattice='A2'}={}){
 const base=createConnectionLearner(setId,{lattice}),cacheKey=`${setId}:${base.lattice}`;
 if(cache.has(cacheKey))return cache.get(cacheKey);
 function corePoints(pair){const points=new Map();for(const spec of pair)for(const e of base.materialize(spec).orientation.occupancy.values()){const p=a2Add(e.point,spec.translation);points.set(p.join(','),p);}return [...points.values()];}
 function verifyFrontier(placements){
  base.verifyPatch(placements);
  const sums=new Map(),used=new Set(placements.map(id)),legality=new Map();
  for(const spec of placements)for(const e of base.materialize(spec).orientation.occupancy.values()){const key=a2Add(e.point,spec.translation).join(',');sums.set(key,(sums.get(key)||0)+e.weight);}
  const frontier=[...sums].filter(([,value])=>value>0&&value<12),deadPoints=[];
  for(const [key] of frontier){
   const point=key.split(',').map(Number);let viable=false;
   outer:for(const o of base.orientations)for(const anchor of o.occupancy.values()){
    const translation=point.map((v,i)=>v-anchor.point[i]),spec={tile:o.tile,orientation:o.index,translation},token=id(spec);
    if(!legality.has(token))legality.set(token,!used.has(token)&&[...o.occupancy.values()].every(e=>(sums.get(a2Add(e.point,translation).join(','))||0)+e.weight<=12));
    if(legality.get(token)){viable=true;break outer;}
   }
   if(!viable)deadPoints.push(point);
  }
  return {frontierPoints:frontier.length,frontierViable:deadPoints.length===0,deadPoints};
 }
 function verifyCorona(pair,placements){
  base.verifyPatch(placements);if(!pair.every(p=>placements.some(q=>id(p)===id(q))))throw new Error('Corona lost its fixed pair');
  const required=corePoints(pair),sums=new Map();for(const spec of placements)for(const e of base.materialize(spec).orientation.occupancy.values()){const key=a2Add(e.point,spec.translation).join(',');sums.set(key,(sums.get(key)||0)+e.weight);}
  const coreComplete=required.every(p=>sums.get(p.join(','))===12),frontier=verifyFrontier(placements);
  return {complete:coreComplete&&frontier.frontierViable,coreComplete,...frontier,requiredPoints:required.length,completedPoints:required.filter(p=>sums.get(p.join(','))===12).length};
 }
 async function examine({root,attachment,budget=5000,seed=1,wait=null,onEvent=()=>{},audit=false}){
  const pair=[root,attachment];base.verifyPatch(pair);const required=corePoints(pair),started=performance.now();let lastFailure=null;
  const result=await solveA2Tiling({boundary:makeHexBoundary(10),latticePointFilter:base.pointFilter,tiles:base.config.tiles,allowReflections:base.config.allowReflections,initialPlacements:pair.map(base.materialize),fixedInitialPlacements:true,completePointGrowth:true,requiredPoints:required,requireViableFrontier:true,maximize:true,targetPlacements:Infinity,nodeLimit:budget,randomSeed:seed,marking:new NoA2Marking(),auditFrontierGraph:audit,waitForSearchDemand:wait,
   onEvent:e=>{if(e.type==='fail')lastFailure={point:e.choice,placements:compact(e.placements)};onEvent({type:e.type,placements:compact(e.placements),choice:e.choice,frontierPoints:e.frontierPoints,nodes:e.nodes,backtracks:e.backtracks});}});
  const placements=compact(result.placements),verification=verifyCorona(pair,placements);if(result.result==='yes'&&!verification.complete)throw new Error('Incomplete corona labeled valid');
  return {root,attachment,criterion:CORONA_CRITERION,budget,seed,status:result.result==='yes'?'valid':result.result==='no'?'invalid':'unresolved',result:result.result,placements,verification,nodes:result.stats.nodes,backtracks:result.stats.backtracks,lastFailure,elapsedMs:performance.now()-started};
 }
 function train(rows){
  if(rows.some(row=>row.criterion!==CORONA_CRITERION))throw new Error('Outdated one-corona labels need a new frontier check');
  const positives=rows.filter(r=>r.status==='valid').map(r=>({placements:[r.root,r.attachment]}));
  let candidate=null,bestCorrect=-1;const training=[];
  if(positives.length)for(const halo of [1,2,3]){
    const proposal=base.encode(positives,{halo}),correct=rows.filter(r=>r.status!=='unresolved'&&base.verifyPatch([r.root,r.attachment],proposal.support).compatible===(r.status==='valid')).length;
    training.push({halo,correct,total:rows.length});if(correct>bestCorrect){candidate=proposal;bestCorrect=correct;}
    if(correct===rows.length)break;
  }
  const counts={valid:0,invalid:0,unresolved:0};let correct=0;
  const connections=rows.map(row=>{counts[row.status]++;const check=candidate?base.verifyPatch([row.root,row.attachment],candidate.support):null,predicted=check?(check.compatible?'valid':'invalid'):null;if(row.status!=='unresolved'&&predicted===row.status)correct++;return {...row,predicted,codeConflict:check?!check.compatible:null,codeWitness:check?.witness??null};});
  const catalog=new Set(base.connections().map(pairId)),total=catalog.size,complete=rows.length===total&&new Set(rows.map(pairId)).size===total&&rows.every(r=>catalog.has(pairId(r)))&&counts.unresolved===0;
  const validAccepted=connections.filter(r=>r.status==='valid'&&r.predicted==='valid').length,invalidBlocked=connections.filter(r=>r.status==='invalid'&&r.predicted==='invalid').length;
  const accepted=!!candidate&&complete&&markingQualifies({...counts,validAccepted,invalidBlocked});
  const classification={criterion:CORONA_CRITERION,total,correct,...counts,perfect:complete&&correct===total,accepted,acceptance:MARKING_ACCEPTANCE,validAccepted,invalidBlocked,training};
  const model=accepted?{...candidate,classification:{...classification,labels:rows.map(({root,attachment,status})=>({root,attachment,status}))},scope:'Accepts every valid pair and blocks most invalid pairs in the complete one-corona catalog with viable exposed frontiers; finite learned restriction, not an infinite-tiling certificate.'}:null;
  return {criterion:CORONA_CRITERION,setId,lattice,connections,counts,classification,candidateModel:candidate,model,attachmentCount:total};
 }
 async function collect({budget=5000,seed=90210,wait=null,onProgress=()=>{},onSearch=()=>{}}={}){
  const started=performance.now(),pairs=base.connections(),rows=[],counts={valid:0,invalid:0,unresolved:0};
  onProgress({phase:'classify',attempts:0,total:pairs.length,counts:{...counts},model:null,latest:[]});
  for(let i=0;i<pairs.length;i++){
   const pair=pairs[i],context={index:i,root:pair.root,attachment:pair.attachment};
   onSearch({...context,type:'pair-start',placements:[pair.root,pair.attachment],nodes:0,backtracks:0});if(wait)await wait();
   const row=await examine({...pair,budget,seed:seed^Math.imul(i+1,1987),wait,onEvent:e=>onSearch({...context,...e})});
   rows.push(row);counts[row.status]++;
   onSearch({...context,type:'pair-result',status:row.status,placements:row.status==='invalid'?(row.lastFailure?.placements??row.placements):row.placements,choice:row.lastFailure?.point,nodes:row.nodes,backtracks:row.backtracks});if(wait)await wait();
   onProgress({phase:'classify',attempts:rows.length,total:pairs.length,counts:{...counts},model:null,latest:row.placements});
  }
  onProgress({phase:'train',attempts:rows.length,total:pairs.length,counts:{...counts},model:null,latest:rows.at(-1)?.placements??[]});await new Promise(requestAnimationFrame);
  return {...train(rows),settings:{budget,seed,lattice},elapsedMs:performance.now()-started};
 }
 function validateModel(model,{allowLegacy=false}={}){
  base.validateModel(model);const c=model.classification,all=base.connections(),catalog=new Set(all.map(pairId));
  if(!(c?.criterion===CORONA_CRITERION||allowLegacy&&c?.criterion===LEGACY_CORONA_CRITERION)||c.acceptance!==MARKING_ACCEPTANCE||!c.accepted||c.unresolved!==0||c.total!==all.length||c.labels?.length!==all.length)throw new Error('Marking needs a complete qualifying one-corona classification');
  let valid=0,invalid=0,validAccepted=0,invalidBlocked=0;
  for(const row of c.labels){
   if(!catalog.delete(pairId(row))||!['valid','invalid'].includes(row.status))throw new Error('Incomplete one-corona classification');
   const compatible=base.verifyPatch([row.root,row.attachment],model.support).compatible;
   if(row.status==='valid'){valid++;if(compatible)validAccepted++;else throw new Error('Marking rejects a valid one-corona pair');}
   else{invalid++;if(!compatible)invalidBlocked++;}
  }
  if(!markingQualifies({valid,invalid,unresolved:0,validAccepted,invalidBlocked}))throw new Error('Marking must block most invalid one-corona pairs');
  if(valid!==c.valid||invalid!==c.invalid||validAccepted!==c.validAccepted||invalidBlocked!==c.invalidBlocked||c.correct!==validAccepted+invalidBlocked||c.perfect!==(c.correct===all.length))throw new Error('Wrong one-corona classification counts');return model;
 }
 function incorporate(report,index,row){const previous=report.connections[index];if(!previous||pairId(previous)!==pairId(row))throw new Error('Connection mismatch');return {...train(report.connections.map((r,i)=>i===index?(row.status==='unresolved'&&r.status!=='unresolved'?r:row):r)),settings:report.settings,elapsedMs:report.elapsedMs+row.elapsedMs};}
 const learner={...base,validateCandidate:base.validateModel,corePoints,verifyFrontier,verifyCorona,examine,collect,train,validateModel,incorporate};cache.set(cacheKey,learner);return learner;
}
