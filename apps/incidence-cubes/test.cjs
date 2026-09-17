'use strict';
// Deterministic regression tests of the independent JavaScript engine.
// Tolerances below test a renderer/calculator, not a mathematical theorem.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const E=require('./engine.js');let seed=20260917,checks=0;const rng=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/2**32;};
function ok(v,m){checks++;assert.ok(v,m);}
function near(a,b,tol=1e-9){ok(Math.abs(a-b)<=tol*(1+Math.abs(a)+Math.abs(b)),`${a} != ${b}`);}
const counts={penrose:0,fomin:0,surface:0,bridge:0};let maxEdge=0,maxFace=0,maxRatio=0;
assert.deepEqual(E.POS,[0,5,11,8,2,4,7,6,1,9,10,3]);assert.deepEqual(E.NEG,[3,1,10,9,8,0,11,5,6,2,7,4]);
for(const slots of [E.POS,E.NEG])assert.deepEqual([...slots].sort((a,b)=>a-b),Array.from({length:12},(_,i)=>i));
const lean=fs.readFileSync(path.join(__dirname,'formal/IncidenceCubes/Fomin/Surface.lean'),'utf8');
for(const [name,v] of [['positiveIndex',E.POS],['negativeIndex',E.NEG]])ok(lean.includes(`def ${name} : Fin 12 → Fin 12 := ![${v.join(',')}]`),'Lean/browser cube certificate mismatch');
for(let n=0;n<250;n++){
 const p=E.defaults();p.couplings=p.couplings.map(()=>1.8*rng()-.9);p.offsets=p.offsets.map(()=>rng()-.5);p.angles=p.angles.map(a=>a+(rng()-.5)*.4);
 const d=E.penrose(p);counts.penrose++;maxEdge=Math.max(maxEdge,d.maxEdge);maxFace=Math.max(maxFace,d.maxFace);
 ok(d.maxEdge<1e-9,'rank-one edge identity');ok(d.maxFace<1e-8,'face concurrence');
 for(const c of d.contacts){const pts=E.lineConic(d.Q[c.s],c.l);ok(pts.length===2,'sample must have two real contacts');for(const x of pts){near(E.quad(d.Q[c.s],x),0);near(E.quad(d.Q[c.t],x),0);near(E.dot(c.l,x),0);near(E.norm(E.cross(E.mul(d.Q[c.s],x),E.mul(d.Q[c.t],x))),0);}}
 for(const Q of d.Q){const ellipse=E.ellipse(Q,16);ok(ellipse!==null,'ellipse sample');for(const x of ellipse)near(E.quad(Q,[...x,1]),0);}
}
for(let n=0;n<250;n++){
 const O=[.4*rng()-.2,.4*rng()-.2,1],ts=[.30+.13*rng(),.53+.13*rng(),.77+.13*rng()],d=E.fomin(O,ts);counts.fomin++;
 ok(d.minPairing>1e-5,'nonincidence margin');maxRatio=Math.max(maxRatio,d.error);ok(d.error<1e-8,'six ratios');ok(d.thirdError<1e-9,'third intersection on completed line');
 for(const f of E.FACES){const [a,l,b,m]=f,v=d.labels;near(E.dot(E.cross(v[a],v[b]),E.cross(v[l],v[m])),0);}
}
for(let n=0;n<250;n++){
 const w=E.EDGES.map(()=> (rng()<.5?-1:1)*(1+Math.floor(100*rng()))),d=E.surface(w);counts.surface++;ok(d.product.n===1n&&d.product.d===1n,'exact closed product');
 const cw=E.coherentWeights(),e=n%12;cw[e]*=2;const x=E.surface(cw);ok(x.ratios.filter(r=>r.n!==r.d).length===2,'one edge changes two faces');ok(x.product.n===x.product.d,'perturbed product');
}
for(let n=0;n<250;n++){
 const t=2*rng()-.7,angle=6*rng(),d=E.bridge(t,angle),x=[rng(),rng(),rng()],coeff=d.veronese;
 counts.bridge++;const evalV=coeff[0]*x[0]**2+coeff[1]*x[1]**2+coeff[2]*x[2]**2+coeff[3]*x[0]*x[1]+coeff[4]*x[0]*x[2]+coeff[5]*x[1]*x[2];
 near(evalV,E.dot(d.l,x)**2);near(E.quad(d.Q,x),E.quad(d.Q0,x)-t*evalV);d.coefficients.forEach((a,i)=>near(a,d.base[i]-t*coeff[i]));
}
assert.throws(()=>E.inverse([[1,1],[1,1]]));assert.throws(()=>E.surface(Array(12).fill(0)));assert.throws(()=>E.surface(Array(12).fill(Number.MAX_SAFE_INTEGER+1)));
const result={status:'passed',seed:20260917,cases:counts,checks,maximumResiduals:{penroseEdge:maxEdge,penroseFace:maxFace,fominRatio:maxRatio},note:'Deterministic numerical/exact-arithmetic software tests. Not Lean proof evidence.'};
fs.writeFileSync(path.join(__dirname,'test-results.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));
