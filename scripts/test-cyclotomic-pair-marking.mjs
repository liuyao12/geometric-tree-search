import assert from 'node:assert/strict';
import {blindPenroseProblem} from './penrose-blind-problem.mjs';
import {createPairPointMarking} from '../assets/cyclotomic-pair-marking.js';
import {num,add,sub,mul,conj} from '../assets/penrose-polygon.js';
import {latticeKey} from '../assets/cyclotomic-five.js';
const problem=blindPenroseProblem(),a=problem.seedTile;
const b=problem.movesAt(a.exactPoints[0]).find(t=>problem.pairAllowed(a,t));assert(b);
// The compilation test intentionally uses an arbitrary pair as input; whether
// it is actually impossible must be certified by the separate proof generator.
const marking=createPairPointMarking(problem);assert(marking.learnPair(a,b,a.exactPoints[0]));assert(!marking.learnPair(a,b));
marking.rebuild([a]);assert(marking.rejects(b));
for(const g of problem.actions){const x=problem.rigid(a,g),y=problem.rigid(b,g);marking.rebuild([x]);assert(marking.rejects(y));assert(!marking.learnPair(x,y));}
const forbidden=new Set(problem.actions.flatMap(g=>{const x=problem.rigid(a,g),y=problem.rigid(b,g);return[x.type+'|'+y.type+'|'+latticeKey(sub(y.origin,x.origin)),y.type+'|'+x.type+'|'+latticeKey(sub(x.origin,y.origin))];}));
let checks=0;
for(const t of problem.catalog){const x={...problem.seedTile,...problem.movesAt(num(0)).find(p=>p.type===t.type)};if(!x.id)continue;
 marking.rebuild([x]);for(const p of x.exactPoints)for(const y of problem.movesAt(p)){
  const key=x.type+'|'+y.type+'|'+latticeKey(sub(y.origin,x.origin));assert.equal(Boolean(marking.rejects(y)),forbidden.has(key));checks++;
 }
}
console.log('ok:',checks,'pair probes; exact forbidden orbit only, rigid actions and duplicate lesson removal');

const apply=(p,g)=>mul(g.factor,g.reflect?conj(p):p);
for(const h of problem.actions){
 const target=problem.rigid(a,h),actual=new Map(marking.support(target).map(r=>[r.key,[r.zeros,r.ones]])),expected=new Map();
 for(const r of marking.support(a)){
  const key=latticeKey(apply(r.point,h));if(!expected.has(key))expected.set(key,[0n,0n]);
  [r.zeros,r.ones].forEach((mask,v)=>{for(let i=0;i<problem.actions.length;i++)if(mask&(1n<<BigInt(i))){
   const g=problem.actions[i],factor=mul(h.factor,h.reflect?conj(g.factor):g.factor),reflect=h.reflect!==g.reflect;
   const j=problem.actions.findIndex(k=>k.reflect===reflect&&latticeKey(k.factor)===latticeKey(factor));assert(j>=0);expected.get(key)[v]|=1n<<BigInt(j);
  }});
 }
 assert.deepEqual(actual,expected,'the rigid group must transport both support coordinates and fiber channels');
}
console.log('ok: exact equivariance of the actual point values, not only of the rejection predicate');
