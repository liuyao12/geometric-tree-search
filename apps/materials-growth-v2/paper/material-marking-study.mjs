import assert from 'node:assert/strict';
import {writeFileSync,readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {samplePatch} from '../samples.mjs';
import {discover,learnSections} from '../learning.mjs';
import {MaterialExperiment} from '../material.mjs';
import {acceptsOverlap} from '../overlap-rules.mjs';
import {compileConflictMarkings} from '../conflict-marking.mjs';
import {verify} from '../kernel.mjs';
const drain=g=>{let r;do{r=g.next();}while(!r.done);return r.value;};
const results=[];
for(const id of ['ice','copper']){
  const g=drain(discover(samplePatch(id).atoms,{epsilon:.03}));
  const marking=drain(learnSections(g)),e=new MaterialExperiment(g,marking,{maximumPoints:80000,maximumCandidates:160000});
  for(let i=0;i<12;i++){const r=e.step();assert(!['unknown','budget','exhausted'].includes(r.kind));}
  const selected=[...e.engine.placed.keys()].slice(0,6);
  const rejected=[...e.engine.reasons].filter(([_,reason])=>reason==='unobserved-overlap').map(([id])=>id).slice(0,6);
  const ids=[...new Set([...selected,...rejected,...e.engine.candidates.keys()])].slice(0,12);
  const candidates=ids.map(id=>e.engine.candidates.get(id));
  const sites=c=>c.meta.sites.map((id,i)=>({id,species:g.types[c.meta.type].sites[i].species,position:e.registry.points[Number(id.slice(1))].position}));
  const pairs=[];let asymmetric=0,baseLegalConflicts=0;
  for(let i=0;i<candidates.length;i++)for(let j=0;j<i;j++){
    const a=candidates[i],b=candidates[j];
    const ab=acceptsOverlap(marking.overlapRules,a.meta.type,b.meta.type,sites(a),sites(b));
    const ba=acceptsOverlap(marking.overlapRules,b.meta.type,a.meta.type,sites(b),sites(a));
    if(ab!==ba)asymmetric++;
    if(!ab||!ba){pairs.push([a.id,b.id]);if(verify({required:[],candidates},[a.id,b.id]).legal)baseLegalConflicts++;}
  }
  const compiled=compileConflictMarkings(candidates,pairs);
  const necessaryPairs=pairs.filter(pair=>verify({required:[],candidates},pair).legal);
  const compressed=compileConflictMarkings(candidates,necessaryPairs,{grouping:'star'});
  const base={required:[],candidates},marked={required:[],candidates:compiled.candidates};
  let legalBase=0,legalRestricted=0;
  for(let bits=0;bits<2**ids.length;bits++){
    const chosen=ids.filter((_,i)=>bits&(1<<i)),b=verify(base,chosen).legal;
    const relational=b&&!pairs.some(([a,b])=>chosen.includes(a)&&chosen.includes(b));
    assert.equal(verify(marked,chosen).legal,relational);
    assert.equal(verify({...base,candidates:compressed.candidates},chosen).legal,relational);
    legalBase+=b;legalRestricted+=relational;
  }
  results.push({id,candidates:ids.length,candidateIds:ids,selection:'first six selected plus first six unobserved-overlap rejections after 12 advances; fill from creation order if necessary',pairs:compiled.edges,asymmetric,baseLegalConflicts,subsets:2**ids.length,legalBase,legalRestricted,equivalent:true,uncompressed:{points:compiled.auxiliaryPoints,assignments:compiled.additionalAssignments},compressed:{points:compressed.auxiliaryPoints,assignments:compressed.additionalAssignments,edges:compressed.edges},compressionScope:'Remove pair exclusions already implied by original t/m data, then group remaining edges into exact star witnesses. This is finite conflict encoding, not learned geometric field compression.'});
}
const sources=Object.fromEntries(['conflict-marking.mjs','kernel.mjs','overlap-rules.mjs','paper/material-marking-study.mjs'].map(p=>[p,createHash('sha256').update(readFileSync(new URL('../'+p,import.meta.url))).digest('hex')]));
const report={schema:'material-finite-marking-equivalence/1',scope:'Frozen 12-candidate illustrative universes, not complete pose domains or held-out material validation. Unordered relation rejects if either directional overlap test rejects. No production behavior changed.',sources,results};
if(process.argv[2])writeFileSync(process.argv[2],JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(results.map(({pairs,candidateIds,...r})=>({...r,conflicts:pairs.length}))));
