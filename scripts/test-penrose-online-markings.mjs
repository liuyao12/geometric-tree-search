import assert from 'node:assert/strict';
import {createMixedGrowth,mixedGeometryConflict} from '../assets/penrose-mixed-growth.js';
import {createOnlineMarkings,learnedSupport,supportsCompatible} from '../assets/penrose-online-markings.js';
import {mixedMarkingsCompatible} from '../assets/penrose-mixed-markings.js';
import {neighborCatalog} from './penrose-neighbor-catalog.mjs';
import {tileMarkingValue,tileStates} from '../assets/penrose-mixed-markings.js';
const learner=createOnlineMarkings(2);assert.equal(learner.snapshot().points,0);
const catalog=neighborCatalog(),expectedPairs=new Map(),representatives=new Map();let bad=0,good=0;
for(const pair of catalog){const {a,b}=pair,expected=mixedMarkingsCompatible(a,b,2),before=learner.snapshot();expectedPairs.set(pair,expected);
 for(const t of[a,b])representatives.set(t.kind+JSON.stringify([t.markingTransform.factor,t.markingTransform.reflect]),t);
 assert.equal(learner.compatible(a,b),expected,`${a.kind}/${b.kind}`);
 const after=learner.snapshot();
 if(after.lessons>before.lessons){assert.equal(after.lessons,before.lessons+1);assert(after.entries>before.entries);assert(!expected);}
 else assert.equal(after.entries,before.entries,'no points without a necessary new rejection');
 const teacherChecks=after.teacherChecks;assert.equal(learner.compatible(a,b),expected);assert.equal(learner.snapshot().teacherChecks,teacherChecks,'repeat uses points or a verified compatible pose');
 if(expected)good++;else bad++;
}
// Later learning may not retroactively reject any earlier teacher-compatible
// placement. Every learned value must have exact geometric provenance.
for(const pair of catalog)assert.equal(learner.compatible(pair.a,pair.b),expectedPairs.get(pair));
// Provenance is translation invariant; check every distinct oriented template.
for(const t of representatives.values())for(const p of learner.support(t).values()){
 const value=tileMarkingValue(t,tileStates(t)[0],p.point,2);p.value.forEach((x,j)=>{if(x!==null)assert.equal(x,value[j]);});
}
console.log('standalone learner audit catalog',good,'accepted',bad,'rejected',learner.snapshot().points,'points',learner.snapshot().lessons,'lessons');
for(const kinds of[['thick','thin'],['kite','dart'],['p5','p3','p2','diamond','boat','star'],['thick','thin','kite','dart']]){
 const options={tileKinds:kinds,useMarkings:true,extent:2,targetCount:12,nodeLimit:10000,seed:17};
 const online=createMixedGrowth(options),reference=createMixedGrowth({...options,learnMarkings:false});let rollbacks=0,lastRevision=0;
 while(true){const a=online.next(),b=reference.next();assert.equal(a.done,b.done);assert.equal(a.value?.type,b.value?.type);assert.equal(a.value?.tile?.id,b.value?.tile?.id);
  assert.deepEqual(online.inspectGraph(),reference.inspectGraph(),'learning must preserve the working search domains and trace');
  const s=online.snapshot();if(s.stats.proposals===0)assert.equal(s.learning.points,0,'seed bookkeeping does not train');assert(s.learning.lessons<=s.stats.proposals,'at most one lesson per chosen frontier');assert(s.learning.revision>=lastRevision,'learning survives rollback');lastRevision=s.learning.revision;if(a.value?.type==='remove')rollbacks++;
  if(a.done)break;
 }
 const s=online.snapshot();assert.equal(s.status,'target reached');assert.equal(s.stats.edgeChecks,0);assert(s.learning.learnedRejections>0);
 const before=online.snapshot();online.candidateContacts(2);assert.deepEqual(online.snapshot(),before,'inspection never trains');
 console.log(kinds.join('/'),s.learning.points,'learned points',s.learning.lessons,'lessons',s.learning.learnedRejections,'point rejections',s.learning.teacherChecks,'teacher checks',rollbacks,'rollbacks');
}
console.log('ok: online teacher equivalence, exact witnesses, reuse, persistent lessons, and unchanged graph/search traces');
