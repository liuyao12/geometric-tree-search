import {pointCompletion,createLocalPairTeacher} from '../assets/cyclotomic-local-certificate.js';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {canonical,latticeKey} from '../assets/cyclotomic-five.js';
import {num,add,sub,mul,conj} from '../assets/penrose-polygon.js';
import {makeCyclotomicProblem} from '../assets/cyclotomic-tile-catalog.js';
import {blindPenroseProblem} from './penrose-blind-problem.mjs';
import {createObstructionSearch} from '../assets/cyclotomic-obstruction-search.js';
import {createPairPointMarking} from '../assets/cyclotomic-pair-marking.js';
const source=readFileSync(new URL('../assets/cyclotomic-pair-marking.js',import.meta.url),'utf8');
assert(!/penrose|ammann|tileStates|arrowStates/i.test(source),'matching compiler must have no tile-specific imports');
const problem=blindPenroseProblem();
// Poison a forbidden capability: the learner sees only shape and problem data.
const original=problem.movesAt;problem.movesAt=p=>original(p).map(t=>{Object.defineProperty(t,'bars',{get(){throw Error('Known marking accessed');}});return t;});
const search=createObstructionSearch({problem,learn:true,targetCount:18,nodeLimit:2000,seed:1});let events=0,lastRevision=0;
while(true){const r=search.next(),s=search.snapshot();assert(s.learning.revision>=lastRevision);lastRevision=s.learning.revision;
 const points=new Map();for(const t of s.tiles)t.vertices.forEach((key,i)=>{const v=points.get(key)||{total:0,generation:Infinity};v.total+=t.weights[i];v.generation=Math.min(v.generation,t.generation);points.set(key,v);});
 const unfinished=[...points.values()].filter(p=>p.total>0&&p.total<problem.fullWeight);
 assert.equal(s.minimumFrontierGeneration,unfinished.length?Math.min(...unfinished.map(p=>p.generation)):null,'whole-patch independent corona count');
 if(events++<50||r.value?.type==='remove'&&events<200)assert(search.audit());
 if(r.done)break;
}
const snapshot=search.snapshot();assert.equal(snapshot.status,'target reached');assert(snapshot.learning.rules>0);assert(snapshot.stats.backtracks>0);assert.equal(snapshot.graph.fullBuilds,1);
for(const table of snapshot.learning.tables){const tile=problem.resolve(table.type,num(0));assert(table.rows.filter(r=>snapshot.learning.certificates[Math.floor(r.channel/problem.actions.length)].method==='point-closure').every(r=>tile.vertices.includes(latticeKey(r.offset))),'shared-vertex closure proofs reuse existing vertices');}
const certificates=snapshot.learning.certificates,weight=(t,p)=>t.weights[t.vertices.indexOf(latticeKey(p))]||0;
for(const c of certificates){const a=problem.resolve(c.a.type,c.a.origin),b=problem.resolve(c.b.type,c.b.origin),total=weight(a,c.point)+weight(b,c.point);assert(problem.pairAllowed(a,b));assert(total>0&&total<10);
 assert(c.method==='point-closure'?pointCompletion(problem,[a,b],c.point,{nodeLimit:0}).status==='impossible':problem.movesAt(c.point).every(t=>weight(t,c.point)+total>10||!problem.pairAllowed(a,t)||!problem.pairAllowed(b,t)),'independent exhaustive two-tile dead-point certificate');
}
assert.throws(()=>createObstructionSearch({problem,learn:true,initialCertificates:[{...certificates[0],point:num(1000)}]}),/Invalid pair obstruction/);
const replay=createObstructionSearch({problem,learn:true,train:false,targetCount:18,nodeLimit:2000,seed:11,initialCertificates:certificates});while(!replay.next().done){}assert.equal(replay.snapshot().status,'target reached');assert.equal(replay.snapshot().learning.rules,certificates.length);
const stopped=createObstructionSearch({problem,learn:true,targetCount:100,nodeLimit:1,seed:1});while(!stopped.next().done){}assert.equal(stopped.snapshot().status,'budget reached');assert.equal(stopped.snapshot().learning.rules,0,'a budget stop must never teach a negative');
// A rational rectangle, with 90-degree corner weights and no edge labels,
// checks that neither Penrose shapes nor 36-degree weights are required.
const z=canonical({coeff:[0,1,0,0],denominator:1}),u=mul(sub(z,conj(z)),num(2,3)),w=num(3,2);
const rect=makeCyclotomicProblem([{kind:'rational rectangle',exactPoints:[num(0),w,add(w,u),u],weights:[1,1,1,1]}],{fullWeight:4});
// Construct the nondegenerate third corner explicitly in the field.

let obstruction;
for(const p of rect.seedTile.exactPoints)for(const b of rect.movesAt(p))if(!obstruction&&rect.pairAllowed(rect.seedTile,b)){
 const total=weight(rect.seedTile,p)+weight(b,p);
 if(total>0&&total<4&&pointCompletion(rect,[rect.seedTile,b],p,{nodeLimit:0}).status==='impossible')obstruction={a:rect.seedTile,b,p};
}
assert(obstruction,'find a purely geometric obstruction for non-Penrose rational input');
const marker=createPairPointMarking(rect);
createLocalPairTeacher(rect).learn(obstruction.p,[obstruction.a,obstruction.b],marker);assert(marker.snapshot().rules>0);marker.rebuild([obstruction.a]);assert(marker.rejects(obstruction.b));
assert(marker.snapshot().tables.some(t=>t.rows.some(r=>r.offset.denominator>1)),'rational witness support must remain exact');
const coronaSearch=createObstructionSearch({problem:rect,targetCount:1,targetCorona:1,nodeLimit:2000});while(!coronaSearch.next().done){}
assert.equal(coronaSearch.snapshot().status,'target reached');assert(coronaSearch.snapshot().tiles.length>1,'corona target must override tile count');assert(coronaSearch.progress().minimumFrontierGeneration>=1);
console.log('ok: bar-free learning, independently verified pair proofs, persistent lessons, graph soundness, held-out replay, budget discipline, and rational non-Penrose input');
