import assert from 'node:assert/strict';
import {lazyPointPath} from '../apps/knot-movie/lazy-point-path.mjs';
import {readFileSync} from 'node:fs';
import {classifyLatticeLazy} from '../research/knot-classifier/lattice-lazy-search.mjs';
import {latticeMoves} from '../research/knot-classifier/lattice-moves.mjs';
function provider(graph,source='0',target='3',marked=false){
 const distances=new Map([[target,0]]),queue=[target];for(const key of queue)for(const next of graph.get(key)||[])if(!distances.has(next)){distances.set(next,distances.get(key)+1);queue.push(next);}
 return {sourceKey:source,targetKey:target,reversible:true,version:()=>0,
  domain(key){const point=`p:${key}`;return{point,boundary:new Map(),complete:true,candidates:(graph.get(key)||[]).map(destination=>({id:`${key}:${destination}`,point,destination}))};},
  decorate(e){return{id:e.id,t:new Map([[e.point,1]]),m:new Map()};},resolve:e=>({key:e.destination}),
  ...(marked?{extensionDomain(edges,{targetKey,remaining}){
   const d=new Map([[targetKey,0]]),q=[targetKey];for(const key of q)for(const next of graph.get(key)||[])if(!d.has(next)){d.set(next,d.get(key)+1);q.push(next);}
   return{complete:true,version:0,boundary:new Map([['budget',0]]),candidates:edges.map(e=>({id:e.id,t:new Map([[e.raw.point,1]]),m:new Map(d.get(e.destination)>remaining?[['budget',1]]:[])}))};
  }}:{}),oracle:distances.get(source)??Infinity};
}
let checks=0;
const pairs=[[0,1],[0,2],[0,3],[1,2],[1,3],[2,3]];
for(let mask=0;mask<64;mask++){
 const graph=new Map(Array.from({length:4},(_,i)=>[String(i),[]]));pairs.forEach(([a,b],i)=>{if(mask&(1<<i)){graph.get(String(a)).push(String(b));graph.get(String(b)).push(String(a));}});
 for(let maxDepth=0;maxDepth<=5;maxDepth++)for(const marked of [false,true])for(const schedule of ['balanced','smaller-frontier']){
  const p=provider(graph,'0','3',marked),r=lazyPointPath(p,{maxDepth,schedule});
  assert.equal(r.status,p.oracle<=maxDepth?'equivalent':'exhausted-finite-search');if(r.status==='equivalent')assert.equal(r.distance,p.oracle);checks++;
 }
}
const graph=new Map([['S',['A']],['A',['S','B']],['B',['A','C']],['C',['B','T']],['T',['C']]]);
for(let i=0;i<50;i++){graph.get('S').push(`leaf${i}`);graph.set(`leaf${i}`,['S']);}
const a=lazyPointPath(provider(graph,'S','T'),{maxDepth:4,schedule:'smaller-frontier'}),b=lazyPointPath(provider(graph,'S','T'),{maxDepth:4,schedule:'balanced'});
assert.equal(a.status,'equivalent');assert.equal(b.status,'equivalent');assert.equal(a.distance,4);assert.equal(b.distance,4);assert.ok(a.stats.nodes<b.stats.nodes);
assert.equal(lazyPointPath(provider(graph,'S','T'),{maxDepth:4,schedule:'balanced',nodeCap:5}).status,'unknown');
assert.equal(lazyPointPath(provider(graph,'S','T'),{maxDepth:4,schedule:'smaller-frontier',nodeCap:5}).status,'equivalent');
assert.equal(lazyPointPath(provider(graph,'S','T'),{maxDepth:4,schedule:'smaller-frontier',shouldStop:()=>true}).status,'unknown');
assert.throws(()=>lazyPointPath(provider(graph),{schedule:'invalid'}),/scheduler/);
const lattice=JSON.parse(readFileSync(new URL('../research/knot-classifier/lattice-corpus-12.json',import.meta.url))).records.find(r=>r.id==='8_1').vertices;
const next=latticeMoves(lattice,{maxEdges:240})[0].vertices;
const identified=classifyLatticeLazy({id:'misleading-input-label',vertices:lattice},[{id:'8_1',vertices:next}],{pathSchedule:'smaller-frontier',maxDepth:2,maxEdges:240,maxMs:10000,extensionLearn:true});
assert.equal(identified.status,'identified');assert.equal(identified.label,'8_1');assert.equal(identified.certificate.steps.length,1);
console.log(JSON.stringify({passed:true,exhaustiveChecks:checks,asymmetricNodes:{balanced:b.stats.nodes,adaptive:a.stats.nodes},budgetUnknown:true,adaptiveLatticeClassifier:true}));
