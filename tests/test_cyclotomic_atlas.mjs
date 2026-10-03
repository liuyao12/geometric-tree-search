import assert from 'node:assert/strict';
import {buildAtlas,inspectPatch,area,ring,cyclotomic,penroseArrows} from '../apps/penrose-model-set/atlas-engine.js';

const ids=['p3','p2','robinson','p1','ttt','ab','seven','tri7','twelve','eleven'];
const shapes={p3:2,p2:2,robinson:2,p1:6,ttt:2,ab:2,seven:3,tri7:4,twelve:3,eleven:5};
function inside(p,polygon){let winding=0;for(let i=0;i<polygon.length;i++){const a=polygon[i],b=polygon[(i+1)%polygon.length],cross=(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]);if(a[1]<=p[1]&&b[1]>p[1]&&cross>0)winding++;if(a[1]>p[1]&&b[1]<=p[1]&&cross<0)winding--;}return winding!==0;}
function coverage(m){let tested=0;for(let x=-6;x<=6;x+=.67)for(let y=-6;y<=6;y+=.71){const p=[x+.01319,y+.03271];if(Math.hypot(...p)>6)continue;const owners=m.tiles.filter(t=>inside(p,t.points));assert.equal(owners.length,1,`coverage at ${p}: ${owners.length} owners`);tested++;}return tested;}
assert.deepEqual(cyclotomic(5),[1,1,1,1,1]);
assert.deepEqual(cyclotomic(8),[1,0,0,0,1]);
assert.deepEqual(cyclotomic(12),[1,0,-1,0,1]);
for(const n of [5,7,8,11,12]){const r=ring(n);assert.deepEqual(r.unit(n),r.unit(0));for(let k=0;k<n;k++){const p=r.embed(r.unit(k));assert.ok(Math.abs(Math.hypot(...p)-1)<1e-12);}}
let samples=0;
for(const id of ids)for(const phase of id==='p1'?[0]:[0,.217,.731]){
  const model=buildAtlas(id,{radius:12,phase}),audit=inspectPatch(model);
  assert.equal(audit.duplicates,0);assert.equal(audit.nonmanifold,0);assert.ok(audit.minArea>0);assert.ok(audit.unitError<1e-11);
  assert.equal(new Set(model.tiles.map(t=>t.kind)).size,shapes[id]);
  for(const t of model.tiles)for(const c of t.coords)assert.ok(c.every(Number.isSafeInteger));
  if(id!=='p1')samples+=coverage(model);
  if(id==='ttt'||id==='tri7')for(const t of model.tiles){
    assert.equal(t.angles.reduce((s,v)=>s+v,0),model.m);
    for(const l of t.lifts){assert.equal(l.reduce((s,v)=>s+v,0),0);
      const residual=l.map((v,k)=>model.e[k][0]*t.dual[0]+model.e[k][1]*t.dual[1]+model.gamma[k]-v);
      assert.ok(Math.max(...residual)-Math.min(...residual)<=1+1e-10,'dual face must meet the section');
    }
  }
  console.log(id,phase,model.tiles.length,'tiles; coverage and incidence OK');
}
const p3=buildAtlas('p3'),tri=buildAtlas('robinson');
assert.equal(tri.tiles.length,2*p3.tiles.length);
assert.ok(Math.abs(tri.tiles.reduce((s,t)=>s+area(t.points),0)-p3.tiles.reduce((s,t)=>s+area(t.points),0))<1e-8);
const marks=penroseArrows(p3),shared=new Map();
for(const arrows of marks.values())for(const a of arrows){if(shared.has(a.edge))assert.equal(shared.get(a.edge),a.signature);shared.set(a.edge,a.signature);}
for(const id of ids.filter(id=>id!=='p1')){
  const a=buildAtlas(id,{radius:8,phase:.16}),b=buildAtlas(id,{radius:8,phase:.68});
  assert.notEqual(a.tiles.map(t=>t.id).join('|'),b.tiles.map(t=>t.id).join('|'));
  assert.deepEqual(a.tiles.map(t=>t.id),buildAtlas(id,{radius:8,phase:.16}).tiles.map(t=>t.id));
}
console.log(`PASS: ten constructions, three phases, ${samples} independent interior coverage probes, cyclotomic reductions, root-lattice witnesses, Penrose arrow agreement, and subdivision area.`);
