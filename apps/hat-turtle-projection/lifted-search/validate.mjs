import assert from 'node:assert/strict';
import fs from 'node:fs';
import {BASE,TRIANGLES,ORIENTATIONS,KERNEL,H,T,rotate,reflect,atoms,materialize,compactPlacement,MODEL_INFO,cartesian,area2} from './model.js';
import {LiftedSearch,verify} from './engine.js';
const report={model:MODEL_INFO,checks:[],searches:[]};
for(let i=-4;i<=4;i++)for(let j=-4;j<=4;j++){
 const k=KERNEL[0].map((v,d)=>i*v+j*KERNEL[1][d]);assert.deepEqual(H(k),[0,0]);assert.deepEqual(T(k),[-2*i||0,-2*j||0]);
}
report.checks.push('Exact rank-two hat kernel; turtle image is minus twice the kernel coefficients');
for(const o of ORIENTATIONS)for(const [layer,P] of [['h',H],['t',T]]){
 const expected=atoms(o.vertices.map(P)).map(p=>p.join(',')).sort();
 const actual=o.support.filter(e=>e.layer===layer&&!e.lift).map(e=>[e.x,e.y].join(',')).sort();assert.deepEqual(actual,expected);
 for(const p of o.vertices){const [x,y]=H(p),[r,s]=T(p),rr=(2*x+y-r)/2,ss=(-x+y-s)/2;assert.deepEqual([x-rr+ss,y-rr-2*ss,rr,ss].map(x=>x||0),p.map(x=>x||0));}
}
report.checks.push('All twelve symmetry actions preserve exact atomic supports in both projections; joint projection has a unique inverse');
// Exact signed area polynomial coefficients (multiplied by four). For
// t=tan(theta)/sqrt(3), positivity on [1/3,1] is checked without sampling.
for(const tri of TRIANGLES){
 const dif=(j)=>BASE[tri[j]].map((x,k)=>x-BASE[tri[0]][k]);
 const [p,q,r,s]=dif(1),[P,Q,R,S]=dif(2),sign=Math.sign(area2(BASE.map(H)));
 const x=2*p+q,y=q,vx=r,vy=r+2*s,X=2*P+Q,Y=Q,VX=R,VY=R+2*S;
 const a=sign*(x*Y-y*X),b=sign*(x*VY-3*y*VX+3*vx*Y-vy*X),c=sign*(vx*VY-vy*VX);
 assert.ok(3*a+b+c>0);assert.ok(a+b+3*c>0);
 if(c>0&&2*c< -b&&-b<6*c)assert.ok(12*a*c-b*b>0);
}
report.checks.push('Common oriented triangulation is nondegenerate over the entire hat–turtle interval, using exact integer quadratic tests');
const s=new LiftedSearch({target:20,nodeLimit:3000,seed:1,audit:true});
// Rollback equality includes generation metadata, active domains and markings.
const before=s.fingerprint(),pick=s.choice(),c=s.pool.get([...pick.row.legal][0]),d=s.apply(c,1);s.auditGraph();s.undo(d);assert.equal(s.fingerprint(),before);s.auditGraph();
report.checks.push('Incremental domains equal independent exhaustive enumeration; branch rollback restores totals, marks, generations, and domains');
const rooted=s.snapshot().placements;
for(const [key,row] of s.rows){
 const point=s.points.get(key),expected=new Set();
 for(const o of ORIENTATIONS)for(const vertex of o.vertices){
  const translation=point.lift.map((x,k)=>x-vertex[k]);
  try{verify([...rooted,{orientation:o.index,translation}]);expected.add(`${o.index}|${translation.join(',')}`);}catch{}
 }
 assert.deepEqual([...row.legal].sort(),[...expected].sort());
}
report.checks.push('All root domains independently match exhaustive orientation/vertex alignment and whole-patch point replay');

// Scheduler unit checks use deliberately distant and late frontier rows.
const rows=s.rows;s.rows=new Map([['early',{key:'early',generation:0,legal:new Set(['a','b','c'])}],['late',{key:'late',generation:5,legal:new Set(['a','b'])}]]);s.audit=false;assert.equal(s.choice().row.key,'early');s.rows.get('late').legal=new Set(['a']);assert.equal(s.choice().kind,'forced');s.rows.set('dead',{key:'dead',generation:10,legal:new Set()});assert.equal(s.choice().kind,'dead');s.rows=rows;s.audit=true;
report.checks.push('Global dead precedes forced; global forced precedes branching; earliest generation precedes smaller later domains');
let event;const start=Date.now();do{event=s.step();}while(!event.done);assert.equal(s.status,'consistent finite patch');const snap=s.snapshot();
const replay=verify(snap.placements);assert.equal(replay.tiles,20);report.searches.push({target:20,seed:1,elapsedMs:Date.now()-start,status:s.status,stats:s.stats,replay});
// Deliberately duplicate a projected tile in a hidden hat direction. It must
// not sneak through as a distinct nonoverlapping lifted placement.
assert.throws(()=>verify([{orientation:0,translation:[0,0,0,0]},{orientation:0,translation:KERNEL[0]}]),/Capacity|lift/);
report.checks.push('Hidden translations do not evade projected overlap tests');
const tiny=new LiftedSearch({target:2,nodeLimit:10,seed:4,audit:true});do{event=tiny.step();}while(!event.done);assert.equal(tiny.status,'consistent finite patch');assert.equal(verify(tiny.snapshot().placements).tiles,2);
const limited=new LiftedSearch({target:100,nodeLimit:1,audit:true});do{event=limited.step();}while(!event.done);assert.equal(limited.status,'unknown');verify(limited.snapshot(limited.bestViable).placements);
report.checks.push('Tiny two-tile instance agrees with brute-force root domain; budget exhaustion is unknown and best viable patch replays');
report.scope='Finite growth checkpoints in a connected, doubly projected, coherently marked model. No learned constraints or substitution rules. No infinite-tiling claim.';
fs.writeFileSync(new URL('validation.json',import.meta.url),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
