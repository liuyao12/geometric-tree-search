import { FaceSearch, chooseFace } from '../../assets/icosahedral-face-search.js?v=gcts-learning-v2';
import { ORIENTATIONS } from '../../assets/icosahedral-exact.js';
import { AMMANN_ORIENTATIONS } from '../../assets/icosahedral-ammann-markings.js?v=ammann-point-v2';
import { LearningSession, validateLearnedModel } from '../../assets/icosahedral-gcts-learning.js?v=gcts-learning-v2';
import { LearnedPointModel, tileOf, halfPoint, fieldsAgree, supportSlots, orientationIndex } from '../../assets/icosahedral-gcts-fields.js';
import { displayTile } from './display-model.js?v=gcts-learning-v2';
let previewCache=null,reuseMs=0;
const previewSlots=(oi,model)=>supportSlots(oi,model.extent).map(slot=>({point:halfPoint(slot.pos).map(x=>x.toJSON()),values:[0,1,2].map(channel=>model.fields[oi].find(m=>m.channel===channel&&m.pos.join(',')===slot.pos.join(','))?.value??null)}));
let search=null,learning=null,phase='growth',running=false,timer=null,delay=130,epoch=0,config=null;
const barePrototypes=['prolate','oblate'].map(kind=>displayTile(ORIENTATIONS.find(t=>t.kind===kind)));
function packet(){
 if(phase==='learning'){
  const raw=learning.snapshot(),current=raw.current,oracle=current?.search;
  const tiles=oracle?[...oracle.placed.values()].map(r=>({...displayTile(r.tile),generation:r.generation})):(current?.placements||learning.catalog[0].pair).map(tileOf).map(displayTile);
  const summary=oracle?.summary()||{tiles:tiles.length,attempts:current?.attempts||0,backtracks:current?.backtracks||0,forced:0,branches:0,frontier:0,candidates:0,incidences:0,checks:0,elapsedMs:0};
  const previewTile=tileOf((current?.pair||learning.catalog[0].pair)[0]);
  const oi=current?.pair?.[0].oi??learning.catalog[0].pair[0].oi;
  const key=`${raw.marking?.revision}:${oi}`;if(previewCache?.key!==key){const preview=raw.marking?displayTile(new LearnedPointModel(raw.marking).decorate(previewTile)):displayTile(previewTile);const field=raw.marking?.fields[oi]||[];const slots=learning.trainer.fields[oi].map(slot=>({point:halfPoint(slot.pos).map(x=>x.toJSON()),values:[0,1,2].map(channel=>field.find(m=>m.channel===channel&&m.pos.join(',')===slot.pos.join(','))?.value??null)}));previewCache={key,preview,slots};}
  const {preview,slots}=previewCache;
  const learningData={...raw,current:current?{...current,search:undefined}:null,preview,slots,orientation:current?.pair?.[0].oi??learning.catalog[0].pair[0].oi,rows:learning.rows.map(r=>({key:r.key,pair:r.pair,status:r.status,reason:r.reason,placements:r.placements,attempts:r.attempts,backtracks:r.backtracks}))};
  self.postMessage({type:'snapshot',phase,epoch,running,summary,event:oracle?.lastEvent||{type:current?.status||'pair'},trace:oracle?.events.slice(-140)||[],learning:learningData,display:{tiles,connected:tiles.map((_,i)=>i),prototypes:[],window:{vertices:[],faces:[],points:[]}},nextFace:null});return;
 }
 const prototypes=search.config.markings==='ammann'?['prolate','oblate'].map(kind=>displayTile(search.markTile(AMMANN_ORIENTATIONS.find(t=>t.kind===kind&&t.decoration.hand===search.config.seedHand)))):barePrototypes;
 const tiles=[...search.placed.values()].map(r=>({...displayTile(r.tile),generation:r.generation}));
 const choice=chooseFace(search.frontier)?.point;
 self.postMessage({type:'snapshot',phase,epoch,running,summary:search.summary(),event:search.lastEvent,trace:search.events.slice(-140),tree:search.tree.slice(-200),learned:search.learnedModel?{id:search.learnedModel.model.id,name:search.learnedModel.model.name,values:search.learnedModel.model.values,preview:displayTile(search.seed),orientation:orientationIndex(search.seed),slots:previewSlots(orientationIndex(search.seed),search.learnedModel.model),reuseMs}:null,
  display:{tiles,connected:tiles.map((_,i)=>i),prototypes,window:{vertices:[],faces:[],points:[]}},
  nextFace:choice?choice.owner.tile.faces[choice.owner.faceIndex].map(i=>choice.owner.tile.vertices[i].map(x=>x.toJSON())):null});
}
function stop(){running=false;clearTimeout(timer);timer=null;}
function tick(){
 if(!running||!search)return;
 try{
  if(phase==='learning'){
   // Keep each real corona move observable. Cheap rule-conflict labels may be
   // batched, but no provisional marking is ever passed into their oracle.
   if(!learning.pending.length&&learning.state!=='validating'){learning.state='validating';packet();}learning.step();if(['accepted','complete','incomplete'].includes(learning.state))stop();packet();
  }else{search.step();if(['checkpoint','budget','exhausted'].includes(search.state))stop();packet();}
  if(running)timer=setTimeout(tick,phase==='learning'?Math.min(delay,30):delay);
 }catch(error){stop();self.postMessage({type:'error',epoch,error:error.message});}
}
self.onmessage=({data})=>{
 try{
  if(data.type==='init'){stop();epoch=data.epoch??0;config=data.config;learning=null;phase='growth';search=new FaceSearch(config);delay=data.delay??130;packet();if(data.auto){running=true;timer=setTimeout(tick,delay);}return;}
  if(!search)return;
  if(data.type==='learn'){
   stop();phase='learning';learning=new LearningSession(data.config);packet();running=true;timer=setTimeout(tick,0);return;
  }
  if(data.type==='continue-learning'){stop();learning.continue(data.attempts);phase='learning';running=true;packet();timer=setTimeout(tick,0);return;}
  if(data.type==='activate'){
   stop();const validationStart=performance.now();const fresh=learning?.model?.accepted&&learning.model.id===data.model?.id;const model=fresh?learning.model:data.model;
   const validated=fresh?model:validateLearnedModel(model);new LearnedPointModel(validated);reuseMs=fresh?0:performance.now()-validationStart;
   config={...config,...data.config};phase='growth';search=new FaceSearch({...config,markings:'ammann',learnedMarking:validated});config={...config,markings:'ammann',learnedMarking:validated};packet();running=true;timer=setTimeout(tick,0);return;
  }
  if(data.type==='inspect-pair'){const row=(phase==='learning'?learning?.rows:search.learnedModel?.model.evidence||learning?.rows)?.[data.index];if(!row)throw Error('No such resolved pair');const field=phase==='learning'?learning.trainer.snapshot:search.learnedModel?.model||learning.trainer.snapshot,model=new LearnedPointModel(field),tiles=row.pair.map(tileOf).map(t=>displayTile(model.decorate(t)));self.postMessage({type:'pair-inspection',epoch,status:row.status,reason:row.reason,compatible:fieldsAgree(field.fields,row.pair),preview:displayTile(model.decorate(tileOf(row.pair[0]))),orientation:row.pair[0].oi,slots:previewSlots(row.pair[0].oi,field),display:{tiles,connected:tiles.map((_,i)=>i),prototypes:[],window:{vertices:[],faces:[],points:[]}}});return;}
  if(data.type==='pause'){stop();packet();}
  if(data.type==='start'){
   if(phase==='growth'&&Number.isSafeInteger(data.target)&&data.target>=2){search.config.target=data.target;if(search.state==='checkpoint'&&data.target>search.placed.size)search.state='ready';}
   const terminal=phase==='learning'?['accepted','complete','incomplete'].includes(learning.state):['checkpoint','budget','exhausted'].includes(search.state);
   if(!running&&!terminal){running=true;packet();timer=setTimeout(tick,0);}
  }
  if(data.type==='step'){stop();if(phase==='learning')learning.step();else{if(Number.isSafeInteger(data.target)&&data.target>=2){search.config.target=data.target;if(search.state==='checkpoint'&&data.target>search.placed.size)search.state='ready';}search.step();}packet();}
  if(data.type==='speed')delay=data.delay;
  if(data.type==='export'){const payload=phase==='learning'?{format:'icosahedral-gcts-learning-evidence-v1',...learning.snapshot(),current:undefined,evidence:learning.rows}:search.export();const json=JSON.stringify(payload,(_,v)=>typeof v==='bigint'?String(v):v,2);self.postMessage({type:'export',epoch,json});}
 }catch(error){stop();self.postMessage({type:'error',epoch,error:error.message});}
};
