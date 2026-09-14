import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {binaryQuotientClass} from './binary-marking-quotient.mjs';
const {PointSearch,verify}=await import(pathToFileURL(process.argv[2]).href);const Engine=binaryQuotientClass(PointSearch);
let state=9123;const rand=n=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return state%n;};let checks=0;
function lift(candidates){
 for(let bits=0;bits<16;bits++)if(candidates.every(c=>new Set(c.xor.map(e=>((bits>>Number(e.point))&1)^e.bit)).size<=1))return true;
 return false;
}
for(let trial=0;trial<80;trial++){
 const model={capacity:2,required:['0','1','2','3'],candidates:Array.from({length:7},(_,i)=>{
  const points=['0','1','2','3'].filter(()=>rand(3));return {id:String(i),t:(points.length?points:['0']).map(point=>({point,value:1})),xor:points.map(point=>({point,bit:rand(2)}))};})};
 let exists=false;
 for(let bits=0;bits<128;bits++){const cs=model.candidates.filter((_,i)=>bits&(1<<i));if(verify(model,cs.map(c=>c.id)).complete&&lift(cs))exists=true;}
 const e=new Engine(model),root=JSON.stringify(e.semanticState());let ended=false;
 for(let step=0;step<5000;step++){
  e.auditGraph();const chosen=[...e.placed.keys()].map(id=>e.candidates.get(id));
  for(const c of e.candidates.values()){
   const physical=!e.placed.has(c.id)&&c.t.every(x=>e.points.get(x.point).total+x.value<=model.capacity);
   assert.equal(!e.reason(c),physical&&lift([...chosen,c]));checks++;
  }
  const d=e.advance();if(['complete','exhausted'].includes(d.kind)){assert.equal(d.kind==='complete',exists);ended=true;break;}
 }
 assert(ended);e.undo(0);e.auditGraph();assert.equal(JSON.stringify(e.semanticState()),root);
}
const pair=(id,a,b,bit)=>({id,t:[a,b].map(point=>({point,value:1})),xor:[{point:a,bit:0},{point:b,bit}]});
const distant=new Engine({capacity:10,required:['a','b','c','d','e','f'],candidates:[
 pair('ab','a','b',0),pair('bc','b','c',0),pair('de','d','e',0),pair('ef','e','f',0),pair('bridge','c','d',1),pair('far','a','f',0)]});
for(const id of ['ab','bc','de','ef'])distant.apply(id);
const before=JSON.stringify(distant.semanticState()),checkpoint=distant.trail.length;
assert.equal(distant.reason(distant.candidates.get('far')),null);distant.apply('bridge');
assert.equal(distant.reason(distant.candidates.get('far')),'binary-marking-inconsistent');assert(!distant.graph.get('a').has('far'));distant.auditGraph();
distant.undo(checkpoint);distant.auditGraph();assert.equal(JSON.stringify(distant.semanticState()),before);assert.equal(distant.reason(distant.candidates.get('far')),null);
console.log(JSON.stringify({models:80,domainChecks:checks,exhaustiveBinaryAssignments:true,completionEquivalence:true,rootRollback:true,distantDependencyAndRollback:true}));
