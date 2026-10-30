import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {ONE,vector,vadd,vscale,pointKey} from '../assets/golden-field.js';
import {AMMANN_ORIENTATIONS,decorateGeometry,pointMarkingsAgree} from '../assets/icosahedral-ammann-markings.js';
import {FaceSearch,faceAttachments,prepare,compatiblePair,chooseFace} from '../assets/icosahedral-face-search.js';
import {properRotations,OnlineFields,pointLift,liftPoint,placementOf,tileOf,transformPair,pairKey,fieldsAgree,LearnedPointModel,markingGate} from '../assets/icosahedral-gcts-fields.js';
import {facePairCatalog,coronaSteps,verifyCorona,LearningSession,validateLearnedModel} from '../assets/icosahedral-gcts-learning.js';
const rotations=properRotations();assert.equal(rotations.length,60);
for(const g of rotations){assert.equal(new Set(g.map.map(m=>m.oi)).size,120);for(const t of AMMANN_ORIENTATIONS)assert.equal(tileOf(placementOf(t)).id,t.id);}
assert.deepEqual(pointLift(liftPoint([3n,-5n,7n,0n,-2n,9n])),[3n,-5n,7n,0n,-2n,9n]);
const catalog=facePairCatalog();assert.equal(catalog.length,156);assert.equal(new Set(catalog.map(r=>r.key)).size,156);
const orbit=new Set();for(const row of catalog)for(const g of rotations)for(const p of [row.pair,[row.pair[1],row.pair[0]]])orbit.add(pairKey(transformPair(p,g)));assert.equal(orbit.size,17280,'Complete directed 120 × 6 × 24 face-neighbor orbit');
const trainer=new OnlineFields();assert.equal(trainer.slots.length,10200);assert.equal(trainer.rows.length,0);assert.equal(trainer.snapshot,null);
trainer.add({...catalog[0],status:'unresolved'});assert.equal(trainer.snapshot.values,0,'An unresolved sample supplies no learned constraint');
const conflict=catalog.find(r=>!pointMarkingsAgree(...r.pair.map(tileOf)));assert(conflict);trainer.add({...conflict,status:'negative'});assert.equal(trainer.snapshot.negativeBlocked,1);assert(!fieldsAgree(trainer.snapshot.fields,conflict.pair));
const it=coronaSteps(catalog[14].pair,{attempts:1});let next;do{next=it.next();}while(!next.done);assert.equal(next.value.status,'unresolved','Budget is not a negative label');assert(!markingGate({...trainer.snapshot,counts:{positive:1,negative:1,unresolved:1},positivePassed:1,negativeBlocked:1},{complete:true,total:3}));
console.log('ok: exact half-module lift, 60 proper rotations, all 17280 directed face pairs, empty cold fields, unresolved/free semantics, gate');
const low=new LearningSession({extent:1,attempts:1});while(!['accepted','complete','incomplete'].includes(low.state))low.step();assert.equal(low.state,'incomplete');assert(low.trainer.counts.unresolved>0);const retained=low.rows.filter(r=>r.status!=='unresolved').map(r=>r.key),unresolved=low.trainer.counts.unresolved;low.continue(256);assert.equal(low.pending.length,unresolved);assert.equal(low.rows.length,retained.length);assert.equal(low.trainer.counts.unresolved,0);assert.equal(low.config.attempts,256);while(low.rows.length===retained.length)low.step();assert(retained.every(key=>low.rows.some(r=>r.key===key)));
console.log('ok: low-budget incomplete gate, retained resolved constraints, increased-budget continuation');
const session=new LearningSession();let steps=0;while(!['accepted','complete','incomplete'].includes(session.state)){session.step();if(++steps>30000)throw Error('Unexpected integration step count');}
assert.equal(session.state,'accepted');const model=session.model;assert.deepEqual(model.counts,{positive:26,negative:130,unresolved:0});assert.equal(model.positivePassed,26);assert.equal(model.negativeBlocked,130);assert(model.values>0&&model.values<model.supportSlots*3);assert(model.evidence.some(r=>r.status==='negative'&&r.reason.includes('exhausted')));
const serialized=JSON.parse(JSON.stringify(model,(_,v)=>typeof v==='bigint'?String(v):v));const validated=validateLearnedModel(serialized);assert(validated.accepted);
assert.throws(()=>validateLearnedModel({...serialized,evidence:serialized.evidence.slice(1)}),/gate/);
assert.throws(()=>new LearnedPointModel({...model,fields:[[]]}),/different exact system/);
const tampered=structuredClone(serialized);tampered.fields.find(f=>f.length)[0].value+=100000;assert.throws(()=>validateLearnedModel(tampered),/point group/);
const field=new LearnedPointModel(model);const once=field.decorate(AMMANN_ORIENTATIONS[0]);assert.equal(field.decorate(once),once,'Decorating a candidate twice must not duplicate assignments');const search=new FaceSearch({seed:4,target:12,markings:'ammann',learnedMarking:model});
function freshDomains(){for(const [key,p]of search.frontier){const expected=new Set(faceAttachments(p.owner.tile,p.owner.faceIndex).flatMap(decorateGeometry).map(t=>field.decorate(t)).filter(t=>search.legal(t)&&!search.candidates.get(t.id)?.excluded).map(t=>t.id));assert.deepEqual(p.candidates,expected,`Incremental domain ${key}`);}}
freshDomains();const before=search.inspect(),checkpoint=search.trail.length,id=[...chooseFace(search.frontier).point.candidates][0];search.apply(search.candidates.get(id).tile);freshDomains();search.undo(checkpoint);assert.deepEqual(search.inspect(),before,'Extended values, dependency graph, generations and incidence roll back exactly');
while(!['checkpoint','budget','exhausted'].includes(search.state))search.step();assert.equal(search.state,'checkpoint');freshDomains();
search.config.target=60;search.state='ready';while(!['checkpoint','budget','exhausted'].includes(search.state))search.step();assert.equal(search.state,'checkpoint');assert.equal(search.placed.size,60);freshDomains();
const tiles=[...search.placed.values()].map(r=>r.tile);for(let i=0;i<tiles.length;i++)for(let j=i+1;j<tiles.length;j++){assert(compatiblePair(tiles[i],tiles[j]));const a=new Map(tiles[i].pointMarkings.map(m=>[pointKey(m.point),m.components]));for(const m of tiles[j].pointMarkings){const other=a.get(pointKey(m.point));if(other)for(const [c,v]of Object.entries(m.components))if(Object.hasOwn(other,c))assert.deepEqual(v,other[c]);}}
const refs=new Map();for(const t of tiles)for(const m of t.pointMarkings)for(const channel of Object.keys(m.components)){const key=pointKey(m.point)+'|'+channel;refs.set(key,(refs.get(key)||0)+1);}for(const [point,channels]of search.pointMarkings.inspect().values)for(const [channel,key,count]of channels)assert.equal(count,refs.get(point+'|'+channel),'Global section reference counts match independent reconstruction');
assert(search.export().learnedMarking.id===model.id);assert.equal(search.export().windowFilter,false);
const baseline=new FaceSearch({seed:4,target:12,markings:'ammann'});assert.equal(baseline.learnedModel,null);assert.equal(baseline.summary().eliminatedLearned,0);
const measured=new FaceSearch({seed:4,target:60,markings:'ammann',learnedMarking:model});while(!['checkpoint','budget','exhausted'].includes(measured.state))measured.step();assert.equal(measured.state,'checkpoint');assert.equal(measured.stats.attempts,75);assert.equal(measured.stats.backtracks,16);assert.equal(measured.stats.eliminatedLearned,15);
if(process.env.GCTS_RECEIPT_PATH)await fs.writeFile(process.env.GCTS_RECEIPT_PATH,JSON.stringify({model,markedGrowth:measured.summary()},(_,v)=>typeof v==='bigint'?String(v):v));
console.log('ok: fresh full learning, all positive witness replays, exact field replay, serialization/reuse gate, independent marked-domain reconstruction, full rollback, 60-tile marked patch',search.summary());
