import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {composedPointProofClass,proofContext,checkComposedNode} from './composed-point-proofs.mjs';
const {PointSearch,verify}=await import(pathToFileURL(process.argv[2]));
const Engine=composedPointProofClass(PointSearch);let state=48217,states=0,nodes=0,resolutions=0,skipped=0;
const rand=n=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return (state>>>8)%n;};
for(let trial=0;trial<300;trial++){
 const model={capacity:1+rand(3),required:['a','b','c','d'],candidates:Array.from({length:10},(_,i)=>({id:String(i),
  t:['a','b','c','d'].filter(()=>rand(2)).map(point=>({point,value:1+rand(2)})),
  m:rand(2)?[{point:'outside',channel:String(rand(2)),lo:rand(2),hi:1}]:[]}))};
 model.candidates=model.candidates.filter(c=>c.t.length&&c.t.every(x=>x.value<=model.capacity));
 const solutions=[];
 for(let mask=0;mask<(1<<model.candidates.length);mask++){
  const ids=model.candidates.filter((_,i)=>mask&(1<<i)).map(c=>c.id);if(verify(model,ids).complete)solutions.push(ids);
 }
 const e=new Engine(model),root=JSON.stringify(e.semanticState());let terminal=false,checked=0;
 for(let step=0;step<10000;step++){
  states++;e.auditGraph();
  for(const solution of solutions)if([...e.placed.keys()].every(id=>solution.includes(id)))
   for(const id of solution)if(!e.placed.has(id))assert.equal(e.reason(e.candidates.get(id)),null);
  const result=e.advance();
  for(;checked<e.proofNodes.length;checked++){
   const node=e.proofNodes[checked];checkComposedNode(proofContext(model),e.proofNodes,node,checked);
   for(const solution of solutions)if(node.ids.every(id=>solution.includes(id)))assert(node.kind==='force'&&solution.includes(node.target),'False proof statement');
  }
  if(['complete','exhausted'].includes(result.kind)){assert.equal(result.kind==='complete',solutions.length>0);terminal=true;break;}
 }
 assert(terminal);nodes+=e.proofNodes.length;resolutions+=e.proofDiagnostics.resolutions;skipped+=e.proofDiagnostics.backjumpSkippedFrames;
 e.undo(0);assert.equal(e.assignmentProof.size,0);e.stack=[];e.clearCertificates();assert.equal(JSON.stringify(e.semanticState()),root);
}
// Force b after a; a later conflict resolves b away, leaving a proved unary
// rejection of a. This tests a nontrivial, satisfiable search rather than
// relying only on vacuous correctness for impossible random models.
const model={capacity:1,required:['p','q','r'],candidates:[
 {id:'a',t:[{point:'p',value:1}],m:[{point:'z',lo:0,hi:0}]},
 {id:'b',t:[{point:'q',value:1}],m:[{point:'w',lo:0,hi:0}]},
 {id:'c',t:[{point:'q',value:1}],m:[{point:'z',lo:1,hi:1}]},
 {id:'d',t:[{point:'r',value:1}],m:[{point:'w',lo:1,hi:1}]},
 {id:'e',t:[{point:'r',value:1}],m:[{point:'z',lo:1,hi:1}]},
 {id:'f',t:[{point:'p',value:1}],m:[{point:'z',lo:1,hi:1}]}]};
const e=new Engine(model);let terminal;
for(let step=0;step<100;step++){terminal=e.advance();if(['complete','exhausted'].includes(terminal.kind))break;}
assert.equal(terminal.kind,'complete');assert(e.proofDiagnostics.resolutions>0);
for(let i=0;i<e.proofNodes.length;i++)checkComposedNode(proofContext(model),e.proofNodes,e.proofNodes[i],i);
const proof=e.proofNodes.find(n=>n.kind==='resolve');assert(proof);
assert.throws(()=>checkComposedNode(proofContext(model),e.proofNodes,{...proof,ids:[]},e.proofNodes.length));
assert.throws(()=>checkComposedNode(proofContext(model),e.proofNodes,{kind:'dead',point:'p',ids:[],uses:[]},e.proofNodes.length));
console.log(JSON.stringify({models:300,states,proofNodes:nodes,resolutions,backjumpSkippedFrames:skipped,allProofStatementsExhaustivelyChecked:true,compatibleCompletionsPreserved:true,satisfiableForcedResolution:true,invalidProofRejections:2,coldReset:true}));
