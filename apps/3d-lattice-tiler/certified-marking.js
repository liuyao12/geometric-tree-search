// Sound, partial negative learning. Every marking clash encodes exactly one
// proved-impossible pair (up to the declared point group and pair reversal).
// Unresolved pairs are never training negatives. No runtime pair classifier.
import {pointSymmetries,neighboringPairs,pairCompatible} from './marking-learning.js?v=20260921-search-inset';
import {add,sub,pointKey,allowedTranslation,validatePointModel,verifyCorona,checkCorona} from './corona-graph.js?v=20260921-vector-learning';
import {markingSystem} from './marking-storage.js?v=20260921-vector-learning';
export const CERTIFIED_VERSION='certified-pair-exclusions-1';
export const CERTIFIED_METHOD='certified-exclusions';
export function certifiedSymmetries(model){
 // A common recentering is harmless; relative translations must stay in the
 // declared lattice, including when different species have different origins.
 const transforms=pointSymmetries(model).filter(g=>new Set(g.map.map(m=>m.oi)).size===model.orientations.length&&g.map.every(m=>allowedTranslation(model,sub(m.shift,g.map[0].shift))));
 if(!transforms.length)throw Error('Certified learning needs a bijective point-group action on orientations');
 return transforms;
}
export function pairOrbitKey(pair,transforms){
 return transforms.flatMap(g=>{
  const [a,b]=pair.map(p=>({oi:g.map[p.oi].oi,translation:add(g.transform(p.translation),g.map[p.oi].shift)})),t=sub(b.translation,a.translation);
  return [`${a.oi}|${b.oi}|${t}`,`${b.oi}|${a.oi}|${t.map(x=>-x)}`];
 }).sort()[0];
}
const slotKey=s=>`${s.oi}:${s.pos}`;
const channelKey=slots=>slots.map(slotKey).join('|');
const mappedSlot=(s,g)=>({oi:g.map[s.oi].oi,pos:sub(g.transform(s.pos),g.map[s.oi].shift)});
// Compile geometry, not a table consulted during search. A channel has just
// two assigned slots in the entire orientation catalogue: zero and one.
// Two copies can disagree only at the relative pose those slots encode.
export function compileCertifiedPairs(model,proofs,{transforms=certifiedSymmetries(model),maxComponents=2048}={}){
 const channels=[],lookup=new Map(),compiled=[];let omitted=0;
 for(const row of proofs){
  if(row.status!=='invalid'||!row.certificate)throw Error('Compiler requires a certified negative');
  const [a,b]=row.pair,second=new Set(model.orientations[b.oi].cells.map(c=>pointKey(add(c.pos,b.translation))));
  const q=model.orientations[a.oi].cells.map(c=>add(c.pos,a.translation)).filter(p=>second.has(pointKey(p))).sort((a,b)=>pointKey(a).localeCompare(pointKey(b)))[0];
  if(!q)throw Error('Certified pair has no shared point support');
  const slots=[{oi:a.oi,pos:sub(q,a.translation)},{oi:b.oi,pos:sub(q,b.translation)}];
  if(slotKey(slots[0])===slotKey(slots[1]))throw Error('Degenerate marking channel');
  const orbit=new Map(transforms.map(g=>{const mapped=slots.map(s=>mappedSlot(s,g));return [channelKey(mapped),mapped];}));
  if(channels.length+[...orbit.keys()].filter(k=>!lookup.has(k)).length>maxComponents){omitted++;continue;}
  for(const [k,slots] of orbit)if(!lookup.has(k)){lookup.set(k,channels.length);channels.push(slots);}
  compiled.push(row);
 }
 const fields=model.orientations.map(()=>[]);
 channels.forEach((slots,component)=>slots.forEach((s,value)=>fields[s.oi].push({pos:s.pos,component,value})));
 const componentAction=transforms.map(g=>channels.map(slots=>{
  const result=lookup.get(channelKey(slots.map(s=>mappedSlot(s,g))));if(result===undefined)throw Error('Marking channels are not symmetry closed');return result;
 }));
 for(const action of componentAction)if(new Set(action).size!==channels.length)throw Error('Noninvertible component action');
 // Replay all possible disagreements of each sparse channel. This is complete:
 // equal-valued slots cannot clash; the only distinct values are these two.
 const proved=new Set(compiled.map(r=>pairOrbitKey(r.pair,transforms)));
 for(const slots of channels){
  const [a,b]=slots,pair=[{oi:a.oi,translation:[0,0,0]},{oi:b.oi,translation:sub(a.pos,b.pos)}];
  if(!proved.has(pairOrbitKey(pair,transforms)))throw Error('A marking clash is not a certified excluded pose');
 }
 for(const row of compiled)if(pairCompatible(fields,row.pair))throw Error('Marking failed to encode a certified pair');
 return {fields,componentCount:channels.length,componentAction,pointGroup:transforms.map(g=>({permutation:g.permutation,signs:g.signs,map:g.map})),labelCount:channels.length?2:0,points:fields.reduce((n,f)=>n+new Set(f.map(m=>pointKey(m.pos))).size,0),values:channels.length*2,compiled,omitted,extent:0};
}
function summary(model,evidence,transforms,extra={}){
 const compiled=compileCertifiedPairs(model,evidence.filter(r=>r.status==='invalid'),{transforms});
 const counts={valid:0,invalid:0,unresolved:0};for(const r of evidence)counts[r.status]++;
 // No 'unknown must agree' approximation: the sparse encoding's complete
 // disagreement audit already guarantees that every other pose agrees.
 const positivePassed=evidence.filter(r=>r.status==='valid'&&pairCompatible(compiled.fields,r.pair)).length;
 if(positivePassed!==counts.valid)throw Error('Certified marking rejects a witnessed pair');
 const {compiled:proofs,...fields}=compiled;
 return {...fields,method:CERTIFIED_METHOD,version:CERTIFIED_VERSION,redundant:true,proofs,counts,pairs:evidence.length,totalPairs:evidence.length,pairUnits:'symmetry representatives',positivePassed,negativeBlocked:proofs.length,scope:'Proved redundant for infinite exact tilings of this unmarked point model. Every mismatch is a certified impossible pair; all other relative poses remain unrestricted. Finite patch targets are a separately strengthened experiment.',...extra};
}
function decorated(model,marking){return {...model,orientations:model.orientations.map((o,i)=>({...o,marks:marking.fields[i]}))};}
export async function* learnCertifiedMarking(model,{timeMs=10000,pairNodes=500,maxPairs=20000,stop=()=>false,audit=false}={}){
 validatePointModel(model);const started=performance.now(),deadline=started+Math.max(0,timeMs),transforms=certifiedSymmetries(model),seen=new Set(),evidence=[];
 let reason=null,catalogComplete=false,snapshot,rawPairs=0;
 const expired=()=>stop()||performance.now()>=deadline;
 try{
  for(const pair of neighboringPairs(model,transforms,{maxPairs})){
   if(expired()){reason=stop()?'cancelled':'preparation time budget';break;}
   rawPairs++;const key=pairOrbitKey(pair,transforms);if(seen.has(key))continue;seen.add(key);evidence.push({pair,status:'unresolved',placements:pair,nodes:0,reason:'not checked'});
  }
  catalogComplete=!reason;
 }catch(e){if(e.kind!=='resource_limit')throw e;reason=e.message;}
 // First sweep: zero-search dead-point certificates over every pair orbit.
 // Searching for a viable corona is unnecessary for such a negative proof.
 for(const row of evidence){
  if(expired()){reason=stop()?'cancelled':'preparation time budget';break;}
  const replay=verifyCorona(model,row.pair,row.pair);
  if(replay.deadPoints.length){row.status='invalid';row.reason=null;row.certificate={kind:'dead_point',point:replay.deadPoints[0]};}
  else if(replay.complete){row.status='valid';row.reason=null;}
  else row.reason='no immediate obstruction';
 }
 snapshot=summary(model,evidence,transforms,{rawPairs,catalogComplete});
 yield {type:'marking-learning',phase:'certify',snapshot,counts:snapshot.counts,pairs:evidence.length,totalPairs:evidence.length,elapsedMs:performance.now()-started};
 // Short unmarked searches may prove further negatives. A cap is always
 // unresolved. Successful local completions are retained for inspection only.
 for(const row of evidence){
  if(row.status!=='unresolved')continue;
  if(expired()){reason=stop()?'cancelled':'preparation time budget';break;}
  yield {type:'marking-learning',phase:'pair',pair:row.pair,placements:row.pair,snapshot,counts:snapshot.counts,pairs:evidence.length,totalPairs:evidence.length,elapsedMs:performance.now()-started};
  let result;
  for await(const e of checkCorona(model,row.pair,{nodes:pairNodes,deadline,stop,audit,retainBranchCaches:false})){
   if(e.type==='corona-result')result=e;
   else yield {...e,type:'marking-learning',phase:'corona',pair:row.pair,snapshot,counts:snapshot.counts,pairs:evidence.length,totalPairs:evidence.length,elapsedMs:performance.now()-started};
  }
  Object.assign(row,result);delete row.type;
  if(row.status==='invalid')row.certificate={kind:'exhausted_pair_corona',nodes:row.nodes};
  snapshot=summary(model,evidence,transforms,{rawPairs,catalogComplete});
  yield {type:'marking-learning',phase:'update',pair:row.pair,placements:row.placements,status:row.status,snapshot,counts:snapshot.counts,pairs:evidence.length,totalPairs:evidence.length,elapsedMs:performance.now()-started};await new Promise(r=>setTimeout(r,0));
 }
 const elapsedMs=performance.now()-started;
 const marking={...snapshot,evidence,accepted:!stop(),complete:catalogComplete&&!snapshot.counts.unresolved,catalogComplete,rawPairs,pairNodes,reason:reason??(snapshot.counts.unresolved?'Unresolved pairs remain unrestricted':null),elapsedMs,trainingMs:elapsedMs,fallback:!snapshot.negativeBlocked};
 yield {type:'marking-learned',marking,model:marking.accepted?decorated(model,marking):null};
}
export async function* reuseCertifiedMarking(model,entry,{timeMs=10000,stop=()=>false}={}){
 const started=performance.now(),deadline=started+timeMs,previous=entry?.marking;
 validatePointModel(model);
 if(JSON.stringify(markingSystem(model))!==JSON.stringify(markingSystem(entry?.domain??{orientations:[]})))throw Error('Saved certified marking belongs to a different system');
 if(previous?.version!==CERTIFIED_VERSION||!previous.accepted||!Array.isArray(previous.proofs))throw Error('Incompatible certified marking');
 const transforms=certifiedSymmetries(model),allPairs=[...neighboringPairs(model,transforms)],catalogRows=new Map(allPairs.map(p=>[pairOrbitKey(p,transforms),p])),catalog=new Set(catalogRows.keys()),checked=[],seen=new Set();
 for(const row of previous.proofs){
  if(stop()||performance.now()>=deadline)throw Error('Certified marking replay budget reached');
  const key=pairOrbitKey(row.pair,transforms);if(!catalog.has(key)||seen.has(key)||row.status!=='invalid')throw Error('Invalid saved exclusion');seen.add(key);
  if(row.certificate?.kind==='dead_point'){
   if(!verifyCorona(model,row.pair,row.pair).deadPoints.some(p=>pointKey(p)===pointKey(row.certificate.point)))throw Error('Saved dead-point proof failed replay');
  }else if(row.certificate?.kind==='exhausted_pair_corona'){
   if(!Number.isSafeInteger(row.certificate.nodes)||row.certificate.nodes<0||row.certificate.nodes>1000000)throw Error('Invalid saved proof budget');
   let result;for await(const e of checkCorona(model,row.pair,{nodes:row.certificate.nodes+1,deadline,stop,retainBranchCaches:false}))if(e.type==='corona-result')result=e;
   if(result?.status!=='invalid')throw Error('Saved exhausted-search proof failed replay or reached a budget');
  }else throw Error('Unsupported certified proof');
  checked.push(row);yield {type:'marking-learning',phase:'replay',pairs:checked.length,totalPairs:previous.proofs.length,counts:{valid:0,invalid:checked.length,unresolved:0},placements:row.pair,elapsedMs:performance.now()-started};
 }
 const rebuilt=summary(model,checked,transforms);
 // Never trust imported point assignments or 'redundant' flags.
 if(JSON.stringify(rebuilt.fields)!==JSON.stringify(previous.fields)||JSON.stringify(rebuilt.componentAction)!==JSON.stringify(previous.componentAction))throw Error('Saved certified marking was modified');
 const checkedByKey=new Map(checked.map(r=>[pairOrbitKey(r.pair,transforms),r]));
 const evidence=[...catalogRows].map(([key,pair])=>checkedByKey.get(key)??{pair,status:'unresolved',placements:pair,reason:'not reclassified during proof replay'});
 const marking={...rebuilt,evidence,counts:{valid:0,invalid:checked.length,unresolved:catalog.size-checked.length},pairs:catalog.size,totalPairs:catalog.size,rawPairs:allPairs.length,catalogComplete:true,accepted:true,complete:checked.length===catalog.size,reused:true,elapsedMs:performance.now()-started,trainingMs:previous.trainingMs??previous.elapsedMs,fallback:!rebuilt.negativeBlocked};
 yield {type:'marking-learned',marking,model:decorated(model,marking)};
}
