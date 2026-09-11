import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {connectionDescriptor,descriptorDistance,fitConnectionLibrary,connectionScore,twistConnection,hingeExamples} from '../connection-descriptor.mjs';
import {axisAngle,transform} from '../geometry.mjs';
import {compileConnectionHypothesis} from '../connection-marking.mjs';
import {PointSearch,verify} from '../kernel.mjs';
const data=JSON.parse(readFileSync(new URL('./connection-data.json',import.meta.url)));
const silicon=data.silicon.frames.map(f=>({id:f.id,examples:hingeExamples(f.atoms,{cell:+f.header.match(/Lattice="([\d.]+)/)[1]})}));
const qc=hingeExamples(data.quasicrystal.atoms,{box:60});
// Disjoint point supports across spatial splits, not random atom-level splitting.
const regions=[[-24,-9],[-3,3],[9,24]];
const qcGroups=regions.map(([lo,hi],id)=>({id,examples:qc.filter(e=>e.sites.every(s=>s.position[0]+e.origin[0]>=lo&&s.position[0]+e.origin[0]<=hi))}));
for(let i=0;i<3;i++)for(let j=0;j<i;j++){
  const ids=new Set(qcGroups[i].examples.flatMap(e=>e.ids));
  assert(!qcGroups[j].examples.some(e=>e.ids.some(id=>ids.has(id))));
}
const quantile=(xs,q)=>[...xs].sort((a,b)=>a-b)[Math.max(0,Math.ceil(xs.length*q)-1)];
const encode=x=>Number.isFinite(x)?x:null;
const analyses=[];
const finiteChecks=[],illustrations={};
let rotationChecks=0,hingeBlindnessChecks=0,maxRotationError=0,maxInternalChange=0;
for(const domain of ['silicon','quasicrystal']){
  const train=domain==='silicon'?silicon.slice(0,8):[qcGroups[0]],cal=domain==='silicon'?silicon.slice(8,16):[qcGroups[1]],test=domain==='silicon'?silicon.slice(16,24):[qcGroups[2]];
  assert(train.every(g=>g.examples.length)&&cal.every(g=>g.examples.length)&&test.every(g=>g.examples.length));
  for(const fraction of [.125,.25,.5,1]){
    const training=domain==='silicon'?train.slice(0,Math.round(train.length*fraction)).flatMap(g=>g.examples):train[0].examples.filter((_,i)=>i%Math.round(1/fraction)===0);
    for(const crossChannels of [false,true]){
      const started=performance.now(),library=fitConnectionLibrary(training,crossChannels),prepared=performance.now();
      const calScores=cal.flatMap(g=>g.examples.map(e=>connectionScore(library,e.sites)));
      // Infinite score is a missing label/role stratum: abstain, never silently
      // turn absence into a negative label. Calibration below is empirical only.
      const knownCal=calScores.filter(Number.isFinite),threshold=quantile(knownCal,.9);
      assert(Number.isFinite(threshold));
      const groups=test.map(g=>{
        const scores=g.examples.map(e=>{
          const positive=connectionScore(library,e.sites);
          const twists=[Math.PI/3,2*Math.PI/3,Math.PI].map(a=>connectionScore(library,twistConnection(e.sites,a)));
          return {anchor:e.anchor,positive:encode(positive),twists:twists.map(encode)};
        });
        return {id:g.id,scores};
      });
      function summary(cutoff){
        return groups.map(g=>{
          const known=g.scores.filter(s=>s.positive!==null),retained=known.filter(s=>s.positive<=cutoff);
          return {id:g.id,total:g.scores.length,unknown:g.scores.length-known.length,known:known.length,retained:retained.length,
            strictRejected:known.filter(s=>s.positive>.06).length,
            conditionalTwists:retained.length*3,conditionalRejected:retained.reduce((n,s)=>n+s.twists.filter(x=>x!==null&&x>cutoff).length,0)};
        });
      }
      const row={domain,fraction,crossChannels,trainingExamples:training.length,trainingConfigurations:domain==='silicon'?Math.round(8*fraction):null,
        labelStrata:library.buckets.size,calibrationExamples:calScores.length,calibrationUnknown:calScores.length-knownCal.length,
        threshold,groups,summary:summary(threshold),strictSummary:summary(.06),timing:{fitMs:prepared-started,totalMs:performance.now()-started}};
      analyses.push(row);
      if(fraction===1&&crossChannels){
        const heldout=test.flatMap(g=>g.examples);
        // First test example is fixed by the protocol, not selected for contrast.
        illustrations[domain]={sites:heldout[0].sites,threshold,training:training.map(e=>e.sites)};
        for(const [index,example] of heldout.slice(0,16).entries()){
          // Local attachment controls, not a coupled bulk-growth benchmark.
          // Atom geometry defines the scored relation; auxiliary point IDs below
          // are logical witnesses and never rendered as physical atoms.
          const candidates=[{id:'A',t:[{point:'root',value:1}],m:[]},...[0,1,2,3].map(i=>({id:'B'+i,t:[{point:'attachment',value:1}],m:[]}))];
          const comparisons=[0,Math.PI/3,2*Math.PI/3,Math.PI].map((a,i)=>({pair:['A','B'+i],sites:twistConnection(example.sites,a)}));
          const marked=compileConnectionHypothesis(candidates,comparisons,library,threshold,{grouping:'star'});
          const edges=marked.scores.filter(s=>s.status==='restricted').map(s=>s.pair);
          const required=['root','attachment'];
          for(let bits=0;bits<32;bits++){
            const chosen=candidates.filter((_,i)=>bits&(1<<i)).map(c=>c.id);
            const reference=verify({required,candidates},chosen);
            const conflict=edges.some(pair=>pair.every(id=>chosen.includes(id)));
            const actual=verify({required,candidates:marked.candidates},chosen);
            assert.equal(actual.legal,reference.legal&&!conflict);
            assert.equal(actual.complete,reference.complete&&!conflict);
          }
          const solve=mode=>{
            const constraint=mode==='relation'?(c,e)=>edges.some(([a,b])=>(a===c.id&&e.placed.has(b))||(b===c.id&&e.placed.has(a)))?'learned-connection':null:null;
            const engine=new PointSearch({required,candidates:mode==='marking'?marked.candidates:marked.neutralCandidates,constraint});
            const trace=[];for(let i=0;i<50;i++){const e=engine.advance();trace.push([e.kind,e.id??null]);engine.auditGraph();if(['complete','exhausted','unknown'].includes(e.kind))break;}
            return {trace,stats:engine.stats};
          };
          const relational=solve('relation'),compiled=solve('marking');assert.deepEqual(compiled.trace,relational.trace);
          finiteChecks.push({domain,index,subsets:32,edges:edges.length,auxiliaryPoints:marked.auxiliaryPoints,traceEqual:true,terminal:compiled.trace.at(-1)[0],stats:compiled.stats});
        }
      }
      console.log(JSON.stringify({...row,groups:undefined}));
    }
  }
  for(const g of test)for(const e of g.examples){
    const pose={r:axisAngle([1/Math.sqrt(14),2/Math.sqrt(14),3/Math.sqrt(14)],.731),t:[7,-11,3]};
    const d=descriptorDistance(connectionDescriptor(e.sites),connectionDescriptor(e.sites.map(s=>({...s,position:transform(pose,s.position)}))));
    maxRotationError=Math.max(maxRotationError,d);rotationChecks++;assert(d<1e-10);
    for(const angle of [Math.PI/3,2*Math.PI/3,Math.PI]){
      const d=descriptorDistance(connectionDescriptor(e.sites,false),connectionDescriptor(twistConnection(e.sites,angle),false));
      maxInternalChange=Math.max(maxInternalChange,d);hingeBlindnessChecks++;assert(d<1e-10);
    }
  }
}
const sources=Object.fromEntries(['connection-descriptor.mjs','connection-marking.mjs','conflict-marking.mjs','kernel.mjs','geometry.mjs','paper/connection-study.mjs','paper/connection-data.json','paper/prepare-connection-data.py'].map(p=>[p,createHash('sha256').update(readFileSync(new URL('../'+p,import.meta.url))).digest('hex')]));
const result={schema:'rotation-invariant-connection-transfer/1',sources,
  protocol:{silicon:{train:[0,7],calibration:[8,15],test:[16,23],scope:data.silicon.selection},quasicrystal:{regions,examples:qcGroups.map(g=>g.examples.length),disjointSupports:true,scope:data.quasicrystal.scope},motif:'Two four-point supports, sharing two anchors; two nearest exclusive neighbors each; 6 Å reach. Diagnostic supports, not the production motif-discovery algorithm.',metric:'Label- and role-stratified sorted distances; maximum component difference to nearest training exemplar. Cross channels add A–B distances. O(3) invariant, not injective; no chirality guarantee.',threshold:'Empirical 90th percentile on known calibration strata, separately for each model and training size. No conformal or population guarantee. Missing strata abstain.',challenges:'Rigidly rotate B-only atoms 60,120,180 degrees about the two shared anchors. These are unobserved geometric alternatives, NOT proven physically invalid examples. Neither motif is deformed.',scope:'Held-out local compatibility study, not generation of an amorphous ensemble, not a materials speedup benchmark.'},
  verification:{rotationChecks,maxRotationError,hingeBlindnessChecks,maxInternalChange,finiteChecks},analyses,illustrations};
if(process.argv[2])writeFileSync(process.argv[2],JSON.stringify(result)+'\n');
