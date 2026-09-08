import {embedding} from '../assets/cyclotomic-five.js';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {neighborCatalog} from './penrose-neighbor-catalog.mjs';
import {FINITE_MARKINGS} from '../assets/penrose-finite-marking-data.js';
import {finiteMarkingSupport,finiteMarkingBounds,finiteMarkingsCompatible,finiteMarkingValue} from '../assets/penrose-finite-markings.js';
import {tileStates} from '../assets/penrose-mixed-markings.js';
import {arrowStates} from '../assets/penrose-arrows.js';
import {createMixedGrowth,mixedVariants,translateVariant} from '../assets/penrose-mixed-growth.js';
import {num,sub,onSegment,pointInPolygon} from '../assets/penrose-polygon.js';
import {extendedBars} from '../assets/penrose-mixed-markings.js';
const catalog=neighborCatalog(),report=JSON.parse(readFileSync(new URL('../docs/penrose-finite-marking-certificate.json',import.meta.url)));
assert.equal(catalog.length,report.neighbors);
let good=0,bad=0,arrows=0;
for(const {a,b,good:allowed}of catalog){
  if(allowed){assert(finiteMarkingsCompatible(a,b,4),`false rejection: ${a.kind}/${b.kind}`);good++;}
  else {assert(!finiteMarkingsCompatible(a,b,0),`missed edge violation: ${a.kind}/${b.kind}`);bad++;}
  if(a.presentation==='P3'&&b.presentation==='P3'){
    const aa=arrowStates(a).find(s=>s.start===a.arrowStart).signatures,bb=arrowStates(b).find(s=>s.start===b.arrowStart).signatures;
    assert.equal([...aa].every(([e,v])=>!bb.has(e)||bb.get(e)===v),allowed,'independent P3 arrow oracle');arrows++;
  }
}
assert.equal(good,report.allowed);assert.equal(bad,report.forbidden);
// Monotone activation makes the extreme-extent checks certify all 17 levels.
// Check exact bar/exclusion provenance and symmetric duplicate moves too.
const anchored=new Map();let positives=0,zeros=0,extensions=0;
for(const v of mixedVariants()){
 const t=translateVariant(v,num(0));let previous=new Map();
 for(let k=0;k<=16;k++){
  const support=finiteMarkingSupport(t,k/4).points,bounds=finiteMarkingBounds(t,k/4);
  for(const p of [...t.exactPoints,...[...support.values()].map(p=>p.point)]){const e=embedding(p);assert(e.x>=bounds.x0-1e-8&&e.x<=bounds.x1+1e-8&&e.y>=bounds.y0-1e-8&&e.y<=bounds.y1+1e-8, 'spatial bounds contain the entire finite support');}
  for(const[key,p]of previous){const q=support.get(key);assert(q);p.value.forEach((x,j)=>{if(x!==null)assert.equal(q.value[j],x);});}
  for(const p of support.values())p.value.forEach((x,j)=>{
   if(x===1){assert(extendedBars(t,k/4).some(b=>b.family===j&&onSegment(p.point,b.from,b.to)));positives++;}
   if(x===0){assert(pointInPolygon(p.point,t.exactPoints));assert(!extendedBars(t,4).some(b=>b.family===j&&onSegment(p.point,b.from,b.to)));zeros++;}
  });previous=support;
 }
 for(const p of v.exactPoints){const a=translateVariant(v,sub(num(0),p)),support=[...finiteMarkingSupport(a,4).points].map(([k,v])=>[k,v.value]).sort();
  if(anchored.has(a.id))assert.deepEqual(support,anchored.get(a.id),'quotiented moves must carry identical supports');else anchored.set(a.id,support);
 }
}
for(const rows of Object.values(FINITE_MARKINGS))extensions+=rows.filter(r=>r[4]>0&&r[3]===1).length;
assert(extensions>0);assert(positives&&zeros);
// Exercise edge-supervised search traces, including failed candidate alternatives.
// At extent zero the two predicates must produce exactly the same graph and trace.
for(const kinds of[['thick','thin'],['kite','dart'],['p5','p3','p2','diamond','boat','star'],['thick','thin','kite','dart']]){
 const settings={tileKinds:kinds,extent:0,targetCount:6,nodeLimit:100,seed:17};
 const edge=createMixedGrowth({...settings,useMarkings:false}),marked=createMixedGrowth({...settings,useMarkings:true});
 for(let i=0;i<1000;i++){
  const a=edge.next(),b=marked.next();assert.equal(a.done,b.done);assert.equal(a.value?.type,b.value?.type);assert.equal(a.value?.tile?.id,b.value?.tile?.id);
  assert.deepEqual(marked.inspectGraph(),edge.inspectGraph());if(a.done)break;
 }
 assert.equal(marked.snapshot().stats.edgeChecks,0);assert.equal(edge.snapshot().stats.markingChecks,0);
 const inspection=marked.candidateContacts(0);assert(inspection.points.length);
}
console.log(`ok: ${good} allowed pairs preserved; ${bad} forbidden pairs excluded at every extent; ${arrows} independent arrow comparisons; symmetry, provenance, edge-supervised traces, fixed-point runtime`);
