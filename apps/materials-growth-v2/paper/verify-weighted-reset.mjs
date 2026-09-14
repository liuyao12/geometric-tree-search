// Node.js, no dependencies. Usage: node verify-weighted-reset.mjs weighted-reset-evidence.json
import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const d=JSON.parse(readFileSync(process.argv[2]));assert.equal(d.capacity,3);
const types=new Map(d.types.map(t=>[t.id,t]));
const mParent=Array.from({length:d.types.length*3},(_,i)=>i);
const mRoot=a=>mParent[a]===a?a:mParent[a]=mRoot(mParent[a]);
function check(frame,occurrences,observed){
 const totals=Array(216).fill(0),adj=totals.map(()=>new Set()),points=totals.map(()=>[]),pairs=new Set(),paths=new Set();let maxResidual=0;
 for(const o of occurrences){
  const t=types.get(o.type);assert.ok(t);assert.deepEqual(t.roles,[1,2,1]);
  assert.equal(new Set(o.sites).size,3);assert.deepEqual(o.sites,o.permutation.map(i=>o.ids[i]));
  const path=`${o.ids[1]}:${Math.min(o.ids[0],o.ids[2])}:${Math.max(o.ids[0],o.ids[2])}`;
  assert.ok(!paths.has(path));paths.add(path);
  for(const endpoint of [o.ids[0],o.ids[2]]){const pair=[endpoint,o.ids[1]].sort((a,b)=>a-b).join(':');assert.ok(!pairs.has(pair));pairs.add(pair);}
  const R=o.pose.r;
  for(let a=0;a<3;a++)for(let b=0;b<3;b++)assert.ok(Math.abs(R[a].reduce((s,x,k)=>s+x*R[b][k],0)-(a===b?1:0))<1e-10);
  const det=R[0][0]*(R[1][1]*R[2][2]-R[1][2]*R[2][1])-R[0][1]*(R[1][0]*R[2][2]-R[1][2]*R[2][0])+R[0][2]*(R[1][0]*R[2][1]-R[1][1]*R[2][0]);assert.ok(Math.abs(det-1)<1e-10);
  o.sites.forEach((p,u)=>{
   assert.ok(Number.isInteger(p)&&p>=0&&p<216);totals[p]+=t.roles[u];o.sites.forEach(q=>adj[p].add(q));points[p].push(3*t.id+u);
   const target=o.positions[o.permutation[u]],fit=R.map((row,k)=>o.pose.t[k]+row.reduce((s,x,j)=>s+x*t.positions[u][j],0));
   const residual=Math.hypot(...fit.map((x,k)=>x-target[k]));assert.ok(residual<=.1+1e-12);maxResidual=Math.max(maxResidual,residual);
   if(observed)target.forEach((x,k)=>{const delta=(x-observed.atoms[p][k])/observed.cell[k];assert.ok(Math.abs(delta-Math.round(delta))<1e-10);});
  });
 }
 assert.ok(totals.every(v=>v===3));const reached=new Set([0]),queue=[0];for(const p of queue)for(const q of adj[p])if(!reached.has(q)){reached.add(q);queue.push(q);}assert.equal(reached.size,216);
 if(!observed)for(const g of points)for(const v of g)mParent[mRoot(v)]=mRoot(g[0]);
 console.log({frame,exactlyFilled:216,motifs:occurrences.length,uniquePairs:pairs.size,connected:true,maxResidual});
}
for(const frame of [0,1])check(frame,d.training.filter(o=>o.frame===frame));
for(const f of d.tests)check(f.frame,f.candidates,f);
const components=new Set(mParent.map((_,i)=>mRoot(i))).size;assert.equal(components,1);
console.log({scalarVariables:mParent.length,observedEqualityComponents:components,interpretation:'Only constant scalar site markings fit these training overlaps.'});
