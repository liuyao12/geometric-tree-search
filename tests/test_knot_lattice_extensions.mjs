import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {coverProbe,projectedAlphabet,extensionComponents,LocalExtensionMarkings} from '../research/knot-classifier/local-extension-markings.mjs';
import {lazyPointPath} from '../apps/knot-movie/lazy-point-path.mjs';
import {latticeMoves} from '../research/knot-classifier/lattice-moves.mjs';
import {scrambleLattice} from '../research/knot-classifier/lattice-scramble.mjs';
import {solveLatticeLazy} from '../research/knot-classifier/lattice-lazy-search.mjs';
const broken={reversible:true,sourceKey:'a',targetKey:'b',version:()=>0,domain:()=>({complete:true,point:'a',boundary:new Map(),candidates:[{id:0}]}),decorate:x=>({...x,t:new Map([['a',1]]),m:new Map()}),resolve:()=>({key:'b'}),extensionDomain:()=>({complete:true,candidates:[],boundary:new Map(),version:0})};
assert.throws(()=>lazyPointPath(broken,{maxDepth:1}),/complete base candidate universe/);
broken.extensionDomain=()=>({complete:false});assert.equal(lazyPointPath(broken,{maxDepth:1}).status,'unknown');
const corpus=JSON.parse(readFileSync(new URL('../research/knot-classifier/lattice-corpus-12.json',import.meta.url))),trefoil=corpus.records.find(r=>r.id==='3_1');
// Independent finite cover oracle exhausts all unions, without the probe's DFS.
function oracle(width,masks,h){let states=new Set([0n]);const goal=(1n<<BigInt(width))-1n;for(let k=0;k<=h;k++){if(states.has(goal))return true;states=new Set([...states].flatMap(s=>masks.map(m=>s|m)));}return false;}
let checks=0;
for(let width=1;width<=6;width++){
 const masks=Array.from({length:width},(_,i)=>1n<<BigInt(i));if(width>2)masks.push(7n);if(width>4)masks.push(24n);
 for(let h=0;h<=width;h++){const r=coverProbe(width,masks,h);assert.equal(r.outcome==='positive',oracle(width,masks,h));assert.notEqual(r.outcome,'unresolved');checks++;}
}
assert.equal(coverProbe(2,[1n,2n],1,{nodeCap:0}).outcome,'unresolved');
const model=new LocalExtensionMarkings(),first=latticeMoves(trefoil.vertices,{maxEdges:220});
for(const move of first.slice(0,16)){
 for(const c of extensionComponents(move.vertices,trefoil.vertices))assert.deepEqual(c.masks.map(String).sort(),projectedAlphabet(c.edges).map(String).sort());
 assert.ok(model.compile(move.vertices,trefoil.vertices,1).lower<=1);checks++;
 for(const next of latticeMoves(move.vertices,{maxEdges:220}).slice(0,8)){assert.ok(model.compile(next.vertices,trefoil.vertices,2).lower<=2);checks++;}
}
// Translation transfer preserves each complete alphabet and proof stencil.
const moved=first[0].vertices,translate=p=>p.map(v=>v.map((x,i)=>x+[13,-9,7][i]));
assert.deepEqual(extensionComponents(moved,trefoil.vertices).map(c=>c.signature),extensionComponents(translate(moved),translate(trefoil.vertices)).map(c=>c.signature));
model.compile(translate(moved),translate(trefoil.vertices),1);assert.ok(model.transferredApplications>0);model.validateTransfer();
const unknown=new LocalExtensionMarkings({probeNodeCap:0});assert.equal(unknown.compile(moved,trefoil.vertices,0).m.size,0);assert.equal(unknown.report().assignedComponents,0);
const rule=model.rules.values().next().value,lower=rule.lower;rule.lower++;assert.throws(()=>model.validateTransfer(),/stencil/);rule.lower=lower;
const masks=rule.masks;rule.masks=[];assert.throws(()=>model.validateTransfer(),/alphabet/);rule.masks=masks;
const a=scrambleLattice(trefoil.vertices,{steps:3,seed:43,maxEdges:220}),b=scrambleLattice(trefoil.vertices,{steps:3,seed:901,maxEdges:220});
const run=solveLatticeLazy(a.vertices,b.vertices,{maxDepth:6,maxEdges:220,extensionLearn:true});assert.equal(run.status,'equivalent');assert.ok(run.stats.extensionEliminations>0);assert.ok(run.extensions.eventsThisRun.length>0);
const verify=spawnSync('python3',['-c',"import sys,json;sys.path.insert(0,'research/knot-classifier');from verify_lattice_movie import verify;print(json.dumps(verify(json.load(sys.stdin))))"],{input:JSON.stringify(run.certificate),encoding:'utf8'});assert.equal(verify.status,0,verify.stderr);
// Frozen proofs are reusable, but finite search failure is never inequivalence.
const bounded=solveLatticeLazy(a.vertices,b.vertices,{maxDepth:1,maxEdges:220,extensionLearn:true});assert.equal(bounded.knotEquivalence,'unknown');assert.equal(bounded.certificate,null);
const reportArg=process.argv.find(x=>x.startsWith('--report='));
if(reportArg){
 const report=JSON.parse(readFileSync(reportArg.slice(9)));assert.equal(report.region,null);assert.ok(report.stepsPerIndependentScramble>=3);
 let movies=0;for(const lane of [...report.lanes,...(report.additionalDeeperTrials||[])])for(const r of lane.runs){
  assert.notEqual(r.sourceSeed,r.targetSeed);assert.notEqual(r.sourceDiagram,r.targetDiagram);if(r.certificate)assert.equal(r.certificate.options.region,null);else assert.equal(r.knotEquivalence,'unknown');
  for(const certificate of [...r.provenance,r.certificate].filter(Boolean)){
   const p=spawnSync('python3',['-c',"import sys,json;sys.path.insert(0,'research/knot-classifier');from verify_lattice_movie import verify;print(json.dumps(verify(json.load(sys.stdin))))"],{input:JSON.stringify(certificate),encoding:'utf8'});assert.equal(p.status,0,p.stderr);movies++;
  }
  // Independently generated witnesses are evaluation evidence, never solver input.
  const sourceFrames=[r.provenance[0].source,...r.provenance[0].steps.map(s=>s.vertices)];
  const targetFrames=[r.provenance[1].source,...r.provenance[1].steps.map(s=>s.vertices)];
  const route=[...sourceFrames].reverse().concat(targetFrames.slice(1)),audit=new LocalExtensionMarkings();
  for(let i=0;i<route.length;i++)assert.ok(audit.compile(route[i],r.target,route.length-1-i).lower<=route.length-1-i);
  if(lane.lane.startsWith('extension')){assert.ok(r.stats.extensionEliminations>0);for(const e of r.extensions.eventsThisRun)for(const s of e.samples){const p=coverProbe(e.width,e.masks.map(m=>BigInt('0x'+m)),s.horizon);assert.equal(p.outcome,s.outcome);checks++;}}
 }
 console.log(JSON.stringify({movies,checks}));
}
console.log(JSON.stringify({status:'passed',checks,trefoilNodes:run.stats.nodes,extensionEliminations:run.stats.extensionEliminations}));
