import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {certifiedDeadPointClass,checkDeadPointCertificate} from './certified-dead-point.mjs';
import {branchExclusionClass} from './branch-local-exclusions.mjs';
const {PointSearch,verify}=await import(pathToFileURL(process.argv[2]));
const Engine=certifiedDeadPointClass(branchExclusionClass(PointSearch));
let state=39191,states=0,proofs=0;const rand=n=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return (state>>>8)%n;};
for(let trial=0;trial<200;trial++){
 const model={capacity:3,required:['a','b','c'],candidates:Array.from({length:9},(_,i)=>({id:String(i),
  t:['a','b','c'].filter(()=>rand(2)).map(point=>({point,value:1+rand(3)})),
  m:rand(2)?[{point:'outside',lo:rand(2),hi:1}]:[]})).filter(c=>c.t.length)};
 const solutions=[];
 for(let mask=0;mask<(1<<model.candidates.length);mask++){
  const ids=model.candidates.filter((_,i)=>mask&(1<<i)).map(c=>c.id);if(verify(model,ids).complete)solutions.push(ids);
 }
 const e=new Engine(model),root=JSON.stringify(e.semanticState());let terminal=false;
 for(let step=0;step<10000;step++){
  states++;e.auditGraph();
  for(const solution of solutions)if([...e.placed.keys()].every(id=>solution.includes(id)))
   for(const id of solution)if(!e.placed.has(id))assert(!e.reason(e.candidates.get(id)),'Removed a compatible full solution');
  for(const cert of e.certificates){checkDeadPointCertificate(model,cert);assert(solutions.every(s=>!cert.ids.every(id=>s.includes(id))));}
  const result=e.advance();if(['complete','exhausted'].includes(result.kind)){
   assert.equal(result.kind==='complete',solutions.length>0);terminal=true;break;
  }
 }
 assert(terminal);proofs+=e.certificates.length;e.undo(0);e.stack=[];e.clearCertificates();
 assert.equal(JSON.stringify(e.semanticState()),root);
}
// A learned {x,y} nogood joins disjoint positive supports. After undo, applying
// x must invalidate y even though the base geometry has no shared support.
const model={capacity:2,required:['p','a','b'],candidates:[
 {id:'x',t:[{point:'a',value:1}]},{id:'y',t:[{point:'b',value:1}]},
 {id:'A',t:[{point:'p',value:2},{point:'a',value:2}]},
 {id:'B',t:[{point:'p',value:2},{point:'b',value:2}]},
 {id:'a',t:[{point:'a',value:1}]},{id:'b',t:[{point:'b',value:1}]}]};
const e=new Engine(model);e.apply('x');e.apply('y');assert.equal(e.decision().kind,'dead');
assert(e.learnDeadPoint('p'));e.undo(0);assert.equal(e.reason(e.candidates.get('y')),null);
e.apply('x');assert.equal(e.reason(e.candidates.get('y')),'certified-dead-point');
assert(!e.graph.get('b').has('y'));e.auditGraph();e.undo(0);assert(e.graph.get('b').has('y'));e.auditGraph();
assert.throws(()=>checkDeadPointCertificate(model,{point:'p',ids:['x']}));
const marked={capacity:1,required:['p','a','b'],candidates:[
 {id:'x',t:[{point:'a',value:1}],m:[{point:'z',lo:0,hi:0}]},
 {id:'y',t:[{point:'b',value:1}],m:[{point:'w',lo:0,hi:0}]},
 {id:'A',t:[{point:'p',value:1}],m:[{point:'z',lo:1,hi:1}]},
 {id:'B',t:[{point:'p',value:1}],m:[{point:'w',lo:1,hi:1}]}]};
const f=new Engine(marked);f.apply('x');f.apply('y');assert(f.learnDeadPoint('p'));
assert.deepEqual(f.certificates[0].ids,['x','y']);f.undo(0);f.apply('y');assert(!f.graph.get('a').has('x'));f.auditGraph();
const unary={capacity:1,required:['p','a'],candidates:[{id:'x',t:[{point:'a',value:1}]},{id:'A',t:[{point:'a',value:1},{point:'p',value:1}]}]};
const h=new Engine(unary),root=JSON.stringify(h.semanticState());h.apply('x');assert(h.learnDeadPoint('p'));h.undo(0);
assert(!h.graph.get('a').has('x'));h.auditGraph();assert.throws(()=>h.addCandidate({id:'new',t:[{point:'p',value:1}]}));
h.clearCertificates();assert.equal(JSON.stringify(h.semanticState()),root);
console.log(JSON.stringify({models:200,states,certificates:proofs,completionPreserved:true,distantDependencyAndUndo:true,markOnlyCertificate:true,unaryRuleReset:true,immutablePoolEnforced:true,invalidCertificateRejected:true,rootAfterProofReset:true}));
