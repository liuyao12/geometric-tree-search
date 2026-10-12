import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {lazyPointPath} from '../apps/knot-movie/lazy-point-path.mjs';
import {pointSearch} from '../apps/knot-movie/point-search.mjs';
import {LocalPointMarkings,localProbe,synthesize} from '../research/knot-classifier/local-point-markings.mjs';
import {rawFaceSweeps,latticeMoves} from '../research/knot-classifier/lattice-moves.mjs';
import {unitLoop,embeddingKey} from '../research/knot-classifier/lattice-state.mjs';
import {latticeProvider,solveLatticeLazy,classifyLatticeLazy} from '../research/knot-classifier/lattice-lazy-search.mjs';
const corpus=JSON.parse(readFileSync(new URL('../research/knot-classifier/lattice-corpus-12.json',import.meta.url))),p=corpus.records.find(r=>r.id==='3_1').vertices;
// Genuine unmarked local labels and individual free values, not bundled guards.
const model=new LocalPointMarkings();assert.equal(model.version,0);model.observe(1,'training-1');model.observe(2,'training-2');
assert.deepEqual(model.rules.get(1).values,[0]);assert.deepEqual(model.rules.get(2).values,[0,0]);model.validateTransfer();
assert.equal(model.transferValidationNodes,6);
const corrupted=new LocalPointMarkings();corrupted.observe(1,'x');corrupted.rules.get(1).values=[1];assert.throws(()=>corrupted.validateTransfer());
assert.equal(synthesize([{profile:[0],outcome:'unresolved'}],1),null);
for(let width=1;width<=2;width++)for(let b=0;b<(1<<width);b++){
 const profile=Array.from({length:width},(_,i)=>(b>>i)&1),result=localProbe(profile);assert.equal(result.outcome,profile.some(Boolean)?'negative':'positive');
 assert.equal(model.rules.get(width).values.every((v,i)=>v===null||v===profile[i]),result.outcome==='positive');
}
assert.deepEqual(synthesize([{profile:[0,0],outcome:'positive'},{profile:[0,1],outcome:'positive'},{profile:[1,0],outcome:'negative'},{profile:[1,1],outcome:'negative'}],2),[0,null]);
const unresolved=new LocalPointMarkings({probeNodeCap:0});unresolved.observe(2,'budget');assert.equal(unresolved.version,0);assert(unresolved.events[0].samples.every(s=>s.outcome==='unresolved'));
const overflow=pointSearch({depth:1,sourceKey:'x',targetKey:'x',tiles:[{id:0,t:new Map([[0,1]]),m:new Map()},{id:1,t:new Map([[0,1]]),m:new Map()}]},{initialSelected:[0,1]});assert.equal(overflow.status,'exhausted-finite-search');
// Exhaust all signed coordinate permutations: 48 orientations/reflections,
// translated and traversal-reversed. Exact capacity labels stay valid even
// where the fixed projection grammar itself is not symmetry invariant.
const permutations=[[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]],pk=p=>p.join(',');let transformedSamples=0;
for(const order of permutations)for(let bits=0;bits<8;bits++){
 const transformed=[...p].reverse().map(v=>order.map((k,i)=>((bits>>i)&1?-v[k]:v[k])+[12,-7,20][i]));
 const occupied=new Set(unitLoop(transformed).map(pk));
 for(const raw of rawFaceSweeps(transformed,{maxEdges:80})){
  const features=raw.replacement.slice(1,-1),values=model.values(features.length,'new-knot-location');
  const matches=features.every((v,i)=>values[i]===null||values[i]===(occupied.has(pk(v))?1:0));
  let valid=true;try{unitLoop(raw.vertices);}catch{valid=false;}
  assert.equal(matches,valid);transformedSamples++;
 }
}
// Marked and unmarked provider domains equal independently enumerated full
// lattice move inventories. No face-region restriction is supplied.
for(const id of ['3_1','4_1','5_1']){
 const input=corpus.records.find(r=>r.id===id).vertices;
 const provider=latticeProvider(input,input,{maxEdges:220,model});const d=provider.domain(provider.sourceKey),actual=new Set();
 for(const entry of d.candidates){const c=provider.decorate(entry);if([...c.m].some(([p,v])=>d.boundary.has(p)&&d.boundary.get(p)!==v))continue;const r=provider.resolve(entry);if(r)actual.add(r.key);}
 assert.deepEqual(actual,new Set(latticeMoves(input,{maxEdges:220}).map(m=>m.key)));
}
// Generic graph cases: complete domains, rule-version replay, explicit zero,
// opaque labels, symmetry requirement, node/state budgets, and unresolved lists.
function graphProvider({incomplete=false}={}){
 const graph={a:['b','c'],b:['a','d'],c:['a'],d:['b']},entries=new Map();let count=0,version=0;
 return{sourceKey:'a',targetKey:'d',reversible:true,version:()=>version,
  domain(key){if(incomplete)return{complete:false};return{complete:true,point:key,boundary:new Map([['guard',0]]),candidates:[...graph[key].map(destination=>{const x={id:count++,key,destination};entries.set(x.id,x);return x;}),{id:count++,key,destination:null}]};},
  decorate(x){return{id:x.id,t:new Map([[x.key,1]]),m:new Map(x.destination===null&&version?[['guard',1]]:[])};},
  resolve(x){return x.destination===null?null:{key:x.destination};},observeRejected(x){if(x.key==='d')version++;}
 };
}
const graph=lazyPointPath(graphProvider(),{maxDepth:2});assert.equal(graph.status,'equivalent');assert.equal(graph.distance,2);assert(graph.stats.replayedDomains>0);
assert.equal(lazyPointPath(graphProvider(),{maxDepth:1}).status,'exhausted-finite-search');
assert.equal(lazyPointPath(graphProvider(),{nodeCap:0}).status,'unknown');
assert.equal(lazyPointPath(graphProvider(),{stateCap:2}).status,'unknown');
assert.equal(lazyPointPath(graphProvider({incomplete:true})).status,'unknown');
const f=JSON.parse(readFileSync(new URL('../research/knot-classifier/fixtures/trefoil-identification.json',import.meta.url)));
const partial=solveLatticeLazy(f.source,f.target,{maxDepth:2,maxEdges:68,region:f.bounds.region});assert.equal(partial.status,'exhausted-finite-search');assert.equal(partial.knotEquivalence,'unknown');
const match=classifyLatticeLazy({vertices:p,name:'wrong',invariant:'unused'},[{id:'3_1',vertices:p}],{maxDepth:0});assert.equal(match.status,'identified');assert.equal(match.label,'3_1');
assert.equal(classifyLatticeLazy(p,[],{comparisonCap:0}).status,'unknown');
const reportFile=process.argv.find(a=>a.startsWith('--report='))?.slice(9);
let independentMovies=0;
if(reportFile){
 const report=JSON.parse(readFileSync(reportFile));assert.equal(report.region,null);assert.equal(report.stepsPerIndependentScramble,2);
 const certs=[];
 for(const lane of report.lanes)for(const run of lane.runs){
  assert.equal(run.status,'equivalent');assert.equal(run.certificate.options.region,null);assert.notEqual(run.sourceSeed,run.targetSeed);assert.notEqual(embeddingKey(run.source),embeddingKey(run.target));assert.notEqual(run.sourceDiagram,run.targetDiagram);
  certs.push(...run.provenance,run.certificate);
  if(lane.lane==='unmarked')assert.equal(run.stats.markingEliminations,0);
  else assert(run.stats.markingEliminations>0);
 }
 const baseline=report.lanes.find(l=>l.lane==='unmarked');
 for(const lane of report.lanes)for(let i=0;i<lane.runs.length;i++)assert.equal(lane.runs[i].stats.nodes,baseline.runs[i].stats.nodes);
 const transfer=report.lanes.find(l=>l.lane==='gcts-transfer');assert.equal(transfer.runs[0].learning.initialVersion,0);assert(transfer.runs.slice(1).every(r=>r.learning.initialVersion===2&&r.learning.initialAssignedValues===3&&r.learning.eventsThisRun.length===0));
 const py=spawnSync('python3',['-c',`import sys,json;sys.path.insert(0,'research/knot-classifier');from verify_lattice_movie import verify;print(json.dumps([verify(c) for c in json.load(sys.stdin)]))`],{input:JSON.stringify(certs),encoding:'utf8',maxBuffer:1024*1024});assert.equal(py.status,0,py.stderr);independentMovies=JSON.parse(py.stdout).length;
}
console.log(JSON.stringify({passed:true,transformedLocalSamples:transformedSamples,symmetries:48,wholeKnotInventories:3,localPrototypes:2,assignedComponents:3,exhaustiveLocalProfiles:6,independentMovies,versionReplay:true,budgetsRemainUnknown:true}));
