/** Local extension learning for the declared supplied-rule geometric lane.
 * The oracle never receives provisional learned fields. This is an explicitly
 * labeled face-corona adaptation, not the pure point-capacity oracle.
 */
import { FaceSearch, faceAttachments, prepare, compatiblePair, chooseFace } from './icosahedral-face-search.js?v=gcts-learning-v2';
import { AMMANN_ORIENTATIONS, decorateGeometry, pointMarkingsAgree, AMMANN_RULE_VERSION } from './icosahedral-ammann-markings.js?v=ammann-point-v2';
import { OnlineFields, properRotations, placementOf, tileOf, canonicalPair, pairKey, fieldsAgree, markingGate, verifyFieldAction, LearnedPointModel, LEARNING_VERSION } from './icosahedral-gcts-fields.js';

let catalog;
export function facePairCatalog(){
 if(catalog)return catalog;
 const rotations=properRotations(),covered=new Set(),pairs=new Map();let raw=0;
 for(let oi=0;oi<AMMANN_ORIENTATIONS.length;oi++){
  if(covered.has(oi))continue;for(const g of rotations)covered.add(g.map[oi].oi);
  const root=AMMANN_ORIENTATIONS[oi];
  for(let face=0;face<6;face++)for(const bare of faceAttachments(root,face))for(const tile of decorateGeometry(bare)){
   if(!compatiblePair(root,tile))throw Error('Face attachment is not face-to-face');raw++;
   const pair=[placementOf(root),placementOf(tile)],key=canonicalPair(pair,rotations);if(!pairs.has(key))pairs.set(key,{key,pair,face});
  }
 }
 if(covered.size!==120||raw!==576)throw Error('Incomplete decorated face-pair representatives');
 // Closure under the independently verified action covers all 120 roots.
 catalog=[...pairs.values()].sort((a,b)=>a.key.localeCompare(b.key));return catalog;
}
export function* coronaSteps(pair,{attempts=128,maxTiles=48,seed=4}={}){
 if(!Number.isSafeInteger(attempts)||attempts<1||!Number.isSafeInteger(maxTiles)||maxTiles<3)throw Error('Invalid corona budget');
 const [a,b]=pair.map(tileOf);
 if(!compatiblePair(a,b))throw Error('Oracle seed is not a legal geometric pair');
 if(!pointMarkingsAgree(a,b))return {status:'negative',reason:'supplied face-rule conflict',attempts:0,backtracks:0,placements:pair};
 const search=new FaceSearch({seed,seedTile:a,seedKind:a.kind,seedHand:a.decoration.hand,markings:'ammann',target:Number.MAX_SAFE_INTEGER,budget:attempts});
 if(!search.legal(b))throw Error('Seed pair rejected despite exact compatibility');
 search.apply(b);
 // Both fixed tiles are root seeds, not a growth placement and its child.
 // Set all initial face obligations to generation zero before retaining the
 // fixed-pair state; later placements and rollback use the ordinary trail.
 for(const record of search.placed.values())record.generation=0;
 for(const owners of search.faceOwners.values())for(const owner of owners)owner.generation=0;
 for(const point of search.frontier.values())point.generation=0;
 search.stats.maxTiles=2;search.trail=[];search.frames=[];
 const core=new Set([...prepare(a).faces,...prepare(b).faces]);
 while(true){
  const choice=chooseFace(search.frontier),placements=[...search.placed.values()].map(r=>placementOf(r.tile));
  if(choice?.kind!=='dead'&&[...core].every(key=>search.faceOwners.get(key)?.length===2))return {status:'positive',reason:'one face-corona completed; full frontier viable',attempts:search.stats.attempts,backtracks:search.stats.backtracks,placements};
  if(search.placed.size>=maxTiles)return {status:'unresolved',reason:'corona tile budget',attempts:search.stats.attempts,backtracks:search.stats.backtracks,placements};
  search.step();
  yield {search,event:search.lastEvent,pair};
  if(search.state==='exhausted')return {status:'negative',reason:'complete fixed-pair face-corona search exhausted',attempts:search.stats.attempts,backtracks:search.stats.backtracks,placements:pair};
  if(search.state==='budget')return {status:'unresolved',reason:'corona attempt budget',attempts:search.stats.attempts,backtracks:search.stats.backtracks,placements:[...search.placed.values()].map(r=>placementOf(r.tile))};
 }
}
export function verifyCorona(pair,placements){
 // Independent reconstruction: fixed seeds first; exact pairwise legality,
 // global marking agreement, face incidence, and freshly enumerated domains.
 const tiles=placements.map(tileOf);if(tiles.length<2||pairKey(placements.slice(0,2))!==pairKey(pair))return false;
 const ids=new Set(),owners=new Map();
 for(const t of tiles){
  if(ids.has(t.id))return false;ids.add(t.id);
  for(const other of tiles)if(other!==t&&(!compatiblePair(t,other)||!pointMarkingsAgree(t,other)))return false;
  for(const key of prepare(t).faces)owners.set(key,(owners.get(key)||0)+1);
 }
 if([...owners.values()].some(n=>n>2))return false;
 if(!tiles.slice(0,2).every(t=>prepare(t).faces.every(key=>owners.get(key)===2)))return false;
 for(const t of tiles)for(let i=0;i<6;i++)if(owners.get(prepare(t).faces[i])===1){
  const viable=faceAttachments(t,i).flatMap(decorateGeometry).some(c=>!ids.has(c.id)&&tiles.every(other=>compatiblePair(c,other)&&pointMarkingsAgree(c,other)));
  if(!viable)return false;
 }
 return true;
}
export class LearningSession{
 constructor({extent=1,attempts=1024,maxTiles=96}={}){
  this.config={extent,attempts,maxTiles};this.catalog=facePairCatalog();this.pending=[...this.catalog];this.trainer=new OnlineFields({extent});this.index=0;this.iterator=null;this.rows=[];this.current=null;this.running=false;this.state='ready';this.started=performance.now();this.oracleMs=0;this.learningMs=0;this.totalAttempts=0;this.totalBacktracks=0;this.model=null;
 }
 step(){
  if(['complete','incomplete','accepted'].includes(this.state))return;
  if(!this.pending.length){this.finish();return;}
  const record=this.pending[0];
  if(!this.iterator){this.iterator=coronaSteps(record.pair,this.config);this.current={pair:record.pair,placements:record.pair,status:'testing',reason:'Testing a fixed neighboring pair'};}
  const started=performance.now(),next=this.iterator.next();this.oracleMs+=performance.now()-started;
  if(!next.done){const search=next.value.search;this.current={...this.current,search,event:search.lastEvent,placements:[...search.placed.values()].map(r=>placementOf(r.tile)),attempts:search.stats.attempts,backtracks:search.stats.backtracks};return;}
  const row={...record,...next.value};delete row.face;this.rows.push(row);this.totalAttempts+=row.attempts;this.totalBacktracks+=row.backtracks;
  const update=performance.now();this.trainer.add(row);this.learningMs+=performance.now()-update;this.current={...row,search:null};this.iterator=null;this.pending.shift();this.index=this.rows.length;this.state='learning';
 }
 continue(attempts=this.config.attempts*2){
  if(this.state!=='incomplete')throw Error('No unresolved catalogue to continue');
  this.config.attempts=Math.max(attempts,this.config.attempts*2);this.config.maxTiles=Math.min(512,this.config.maxTiles*2);
  this.pending=this.catalog.filter(r=>this.rows.some(row=>row.key===r.key&&row.status==='unresolved'));this.rows=this.rows.filter(r=>r.status!=='unresolved');this.trainer.rows=this.trainer.rows.filter(r=>r.status!=='unresolved');this.trainer.counts.unresolved=0;this.index=this.rows.length;this.model=null;this.state='learning';
 }
 finish(){
  const started=performance.now(),snapshot=this.trainer.update(256);this.learningMs+=performance.now()-started;
  const validationStarted=performance.now();verifyFieldAction(snapshot);
  let positives=0,blocked=0;
  for(const row of this.rows){
   if(row.status==='positive'){if(!verifyCorona(row.pair,row.placements))throw Error('Independent corona replay failed');if(!fieldsAgree(snapshot.fields,row.pair))throw Error('Positive field replay failed');positives++;}
   if(row.status==='negative'&&!fieldsAgree(snapshot.fields,row.pair))blocked++;
  }
  if(positives!==snapshot.positivePassed||blocked!==snapshot.negativeBlocked)throw Error('Independent score replay failed');
  const accepted=markingGate(snapshot,{complete:true,total:this.catalog.length});
  this.state=accepted?'accepted':snapshot.counts.unresolved?'incomplete':'complete';
  this.model={...snapshot,oracleConfig:{...this.config,seed:4},validationMs:performance.now()-validationStarted,id:`${LEARNING_VERSION}:${Date.now()}:${Math.random().toString(36).slice(2,10)}`,name:`Ammann GCTS · ${new Date().toISOString()}`,createdAt:new Date().toISOString(),system:'120 supplied Ammann orientations; integer star-module translations; proper rotations',oracle:'supplied-rule geometric face-corona; provisional fields excluded',scope:'learned restriction from finite face-pair evidence; extra halo contacts and infinite extension are not certified',totalPairs:this.catalog.length,accepted,evidence:this.rows,trainingMs:performance.now()-this.started,oracleMs:this.oracleMs,learningMs:this.learningMs};
 }
 snapshot(){return {state:this.state,config:this.config,total:this.catalog.length,resolved:this.index,current:this.current,marking:this.trainer.snapshot,counts:{...this.trainer.counts},attempts:this.totalAttempts+(this.current?.status==='testing'?(this.current.attempts||0):0),backtracks:this.totalBacktracks+(this.current?.status==='testing'?(this.current.backtracks||0):0),oracleMs:this.oracleMs,learningMs:this.learningMs,validationMs:this.model?.validationMs||0,elapsedMs:performance.now()-this.started,model:this.model};}
}
export function validateLearnedModel(model){
 if(model?.version!==LEARNING_VERSION||model.ruleVersion!==AMMANN_RULE_VERSION||!model.accepted||!Array.isArray(model.evidence))throw Error('Unaccepted learned marking');
 const revive=p=>{if(!Number.isInteger(p.oi)||p.oi<0||p.oi>=120||!Array.isArray(p.translation)||p.translation.length!==6)throw Error('Invalid evidence placement');return {oi:p.oi,translation:p.translation.map(x=>{if(!/^-?\d+$/.test(String(x)))throw Error('Invalid lift coefficient');return BigInt(x);})};};
 model={...model,evidence:model.evidence.map(row=>({...row,pair:row.pair.map(revive),placements:row.placements.map(revive)}))};
 new LearnedPointModel(model);verifyFieldAction(model);
 const catalog=facePairCatalog(),eligible=new Set(catalog.map(r=>r.key)),seen=new Set(),counts={positive:0,negative:0,unresolved:0};let positivePassed=0,negativeBlocked=0;
 for(const row of model.evidence){if(!eligible.has(row.key)||seen.has(row.key)||canonicalPair(row.pair)!==row.key||!Object.hasOwn(counts,row.status))throw Error('Invalid learned evidence catalogue');seen.add(row.key);counts[row.status]++;
  if(row.status==='positive'){if(!verifyCorona(row.pair,row.placements))throw Error('Invalid saved positive witness');if(fieldsAgree(model.fields,row.pair))positivePassed++;}
  if(row.status==='negative'&&!fieldsAgree(model.fields,row.pair))negativeBlocked++;
 }
 if(!markingGate({...model,counts,positivePassed,negativeBlocked},{complete:seen.size===catalog.length,total:catalog.length}))throw Error('Saved marking fails the replay gate');
 return model;
}
