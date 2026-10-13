import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
import {latticeProvider} from '../research/knot-classifier/lattice-lazy-search.mjs';
import {LocalExtensionMarkings} from '../research/knot-classifier/local-extension-markings.mjs';
import {embeddingKey} from '../research/knot-classifier/lattice-state.mjs';
const d=JSON.parse(readFileSync(new URL('../research/knot-classifier/lattice-blind-benchmark.json',import.meta.url))),c=d.cases[18],r=d.references.find(r=>r.evaluatorKnot===c.evaluatorKnot);
const frames=p=>[p.source,...p.steps.map(s=>s.vertices)],route=[...frames(c.provenance)].reverse().concat(frames(r.provenance).slice(1));
const local=new LocalExtensionMarkings({probeNodeCap:512}),whole=new LocalExtensionMarkings({probeNodeCap:64,maxComponentEdges:480,maxProbeHorizon:16});
const provider=latticeProvider(c.vertices,r.vertices,{maxEdges:240,extensionModel:local,globalExtensionModel:whole});
let checks=0;
for(let i=0;i<route.length;i++){
 const e={id:i,destination:embeddingKey(route[i]),raw:{point:'choice'}};
 const mark=provider.extensionDomain([e],{targetKey:provider.targetKey,remaining:route.length-1-i});
 assert.equal(mark.complete,true);assert.equal(mark.candidates.length,1);assert.equal(mark.candidates[0].m.size,0);checks++;
}
const staircase=[[100,100,0]];let x=100,y=100;
for(let i=0;i<30;i++){staircase.push([++x,y,0],[x,++y,0]);}
staircase.push([132,130,0],[132,98,0],[98,98,0],[98,100,0]);
const distant=provider.extensionDomain([{id:99,destination:embeddingKey(staircase),raw:{point:'choice'}}],{targetKey:provider.targetKey,remaining:0});
assert.equal(distant.complete,true);assert.equal(distant.candidates[0].m.size,1);assert.ok(whole.events.some(e=>e.width>48));
const stopped=latticeProvider(c.vertices,r.vertices,{extensionModel:local,globalExtensionModel:whole,shouldStop:()=>true});
assert.equal(stopped.extensionDomain([{id:0,destination:embeddingKey(c.vertices),raw:{point:'choice'}}],{targetKey:stopped.targetKey,remaining:16}).complete,false);
console.log(JSON.stringify({passed:true,knownValidContinuationChecks:checks,largeWindows:whole.events.filter(e=>e.width>48).length,cancellationUnknown:true}));
