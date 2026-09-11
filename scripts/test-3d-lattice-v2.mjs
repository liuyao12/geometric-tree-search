import assert from 'node:assert/strict';
import {PointGraph,search,verify} from '../apps/3d-lattice-tiler/v2/search.js';
const p=(x,weight=1)=>({pos:[x,0,0],weight});
const model=(cells,required=[0,1],capacity=1)=>({capacity,orientations:cells.map(c=>({cells:c,marks:[]})),required:required.map(x=>({pos:[x,0,0],generation:0}))});
async function result(m,c={}){let last;for await(const e of search(m,{timeMs:10000,nodes:100000,...c}))last=e;return last;}
// Independent exhaustive binary placement enumeration on tiny finite models.
function brute(m){
  const candidates=new Map();for(const q of m.required)for(const [oi,o] of m.orientations.entries())for(const a of o.cells){const translation=q.pos.map((x,i)=>x-a.pos[i]);candidates.set(`${oi}@${translation}`,{oi,translation});}
  const cs=[...candidates.values()];assert(cs.length<20);for(let bits=0;bits<2**cs.length;bits++){const placements=cs.filter((_,i)=>bits&(1<<i));if(verify(m,placements).ok)return true;}return false;
}
const fixtures=[model([[p(0)]]),model([[p(0),p(1)]]),model([[p(0,1),p(1,2)]],[0,1],3),model([[p(0,2)]],[0],3),model([[p(0,1)],[p(0,2)]],[0],3),model([[p(0,1),p(2,1)]],[0,1],2)];
for(const m of fixtures){
  const graph=new PointGraph(m),original=graph.digest();graph.verifyDomains();
  for(const c of graph.candidates){const mark=graph.apply(c);graph.verifyDomains();for(const d of graph.candidates.filter(x=>x.valid).slice(0,2)){const sub=graph.apply(d);graph.verifyDomains();graph.rollback(sub);graph.verifyDomains();}graph.rollback(mark);assert.equal(graph.digest(),original);}
  for(const mode of ['free','gcts','rl','both']){const r=await result(m,{mode});assert.equal(r.result==='finite_exact',brute(m),`${mode} vs exhaustive verifier`);if(r.result==='finite_exact')assert(verify(m,r.placements).ok);}
}
// Shared candidate incidence, untouched required points, residual weights.
const g=new PointGraph(fixtures[1]);assert(g.candidates.some(c=>c.points.length===2));assert.equal(g.points.size,2);
// Far marking-only dependencies, explicit zero vs absent, and exact rollback.
const decorated=model([[p(0)],[p(0)]],[0,1]);decorated.orientations[0].marks=[{pos:[4,0,0],value:0}];decorated.orientations[1].marks=[{pos:[3,0,0],value:1}];
const dg=new PointGraph(decorated),before=dg.digest(),a=dg.candidates.find(c=>c.oi===0&&c.translation[0]===0),b=dg.candidates.find(c=>c.oi===1&&c.translation[0]===1),trail=dg.apply(a);assert.equal(b.valid,false);dg.verifyDomains();dg.rollback(trail);assert.equal(dg.digest(),before);assert.equal(b.valid,true);
// Decision precedence, independent of iteration order.
const sg=new PointGraph(model([[p(0)],[p(0)]],[0,1,2]));const pts=[...sg.points.values()];pts[0].degree=1;pts[1].degree=0;assert.equal(sg.schedule().kind,'dead');pts[1].degree=2;assert.equal(sg.schedule().point,pts[0]);pts[0].degree=9;pts[0].generation=0;pts[1].generation=1;pts[2].generation=1;assert.equal(sg.schedule().point,pts[0]);
// Budget exhaustion cannot be called a proof; truncated graphs throw.
assert.equal((await result(fixtures[1],{timeMs:0})).result,'unknown');assert.throws(()=>new PointGraph(fixtures[1],{candidateLimit:1}),/Complete graph/);
assert.equal(verify(fixtures[0],[{oi:0,translation:[0,0,0]},{oi:0,translation:[0,0,0]}]).ok,false);
// Failed-move probes and cluster transactions leave the problem solution set intact.
for(let mask=1;mask<8;mask++){const m=model([[0,1,2].filter(i=>mask&(1<<i)).map(x=>p(x))],[0,1]);const expected=brute(m);for(const mode of ['gcts','rl','both'])assert.equal((await result(m,{mode,seed:mask})).result==='finite_exact',expected);}
console.log('PASS: exhaustive tiny-model agreement, incidence, rollback, fractional residuals, marking-only dependencies, scheduling precedence, budgets, cluster/probe transactions.');
