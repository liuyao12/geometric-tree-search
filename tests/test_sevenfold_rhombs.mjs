import assert from 'node:assert/strict';
import {ZERO,key,add,sub,neg,direction,xy,catalog,translated,markingsAgree,geometryAllowed,createSevenfoldSearch,chooseSevenfoldPoint} from '../assets/sevenfold-rhombs.js';

for(let i=0;i<14;i++){
 const p=xy(direction(i));assert.ok(Math.abs(p.x-Math.cos(i*Math.PI/7))<1e-12);assert.ok(Math.abs(p.y-Math.sin(i*Math.PI/7))<1e-12);
 assert.deepEqual(add(direction(i),direction(i+7)),ZERO);
}
assert.deepEqual(Array.from({length:7},(_,i)=>direction(2*i)).reduce(add,ZERO),ZERO);
const templates=catalog();assert.equal(templates.length,21);
for(const t of templates){
 assert.equal(t.weights.reduce((a,b)=>a+b),14);
 for(let i=0;i<4;i++){const d=xy(sub(t.points[i],t.points[(i+1)%4]));assert.ok(Math.abs(Math.hypot(d.x,d.y)-1)<1e-12);}
 const u=xy(sub(t.points[1],t.points[0])),v=xy(sub(t.points[3],t.points[0]));
 assert.ok(Math.abs(Math.acos(u.x*v.x+u.y*v.y)-t.weights[0]*Math.PI/7)<1e-12);
}
const seedSearch=createSevenfoldSearch();seedSearch.next();assert.equal(seedSearch.movesAt(ZERO).length,84);
const root=seedSearch.snapshot().tiles[0],u=sub(root.points[1],root.points[0]);
const adjacent=translated(root,u);assert.ok(geometryAllowed(root,adjacent));assert.equal(markingsAgree(root,adjacent),false);
assert.equal(geometryAllowed(root,root),false);assert.ok(markingsAgree(root,translated(root,u.map(x=>10*x))));
const translatedRoot=translated(root,direction(3)),translatedNeighbor=translated(adjacent,direction(3));assert.equal(markingsAgree(translatedRoot,translatedNeighbor),false);
const different=seedSearch.movesAt(root.points[0]).find(t=>t.kind!==root.kind&&geometryAllowed(root,t)&&t.vertices.filter(v=>root.vertices.includes(v)).length===2);
assert.ok(different);assert.ok(markingsAgree(root,different));
const p=(key,depth,n)=>({key,depth,candidates:Array.from({length:n},(_,i)=>String(i))});
assert.equal(chooseSevenfoldPoint([p('early',0,9),p('late',9,2)]).key,'early');
assert.equal(chooseSevenfoldPoint([p('early',0,9),p('forced',9,1)]).key,'forced');
assert.equal(chooseSevenfoldPoint([p('forced',0,1),p('dead',9,0)]).key,'dead');
assert.equal(chooseSevenfoldPoint([p('many',0,9),p('few',0,2)]).key,'few');

// Independent convex polygon clipping checks intersection area; production uses SAT.
const cross=(a,b,p)=>(b.x-a.x)*(p.y-a.y)-(b.y-a.y)*(p.x-a.x);
function intersectionArea(a,b){let out=a.slice();for(let i=0;i<b.length;i++){
 const q=b[i],r=b[(i+1)%b.length],input=out;out=[];
 for(let j=0;j<input.length;j++){const s=input[j],e=input[(j+1)%input.length],cs=cross(q,r,s),ce=cross(q,r,e);
 if(cs>=-1e-10)out.push(s);if((cs>1e-10&&ce< -1e-10)||(cs< -1e-10&&ce>1e-10)){const t=cs/(cs-ce);out.push({x:s.x+t*(e.x-s.x),y:s.y+t*(e.y-s.y)});}}
 }return Math.abs(out.reduce((sum,p,i)=>{const q=out[(i+1)%out.length];return sum+p.x*q.y-p.y*q.x;},0))/2;}
function replay(s){
 const totals=new Map();assert.equal(new Set(s.tiles.map(t=>t.id)).size,s.tiles.length);
 for(const t of s.tiles)t.vertices.forEach((v,i)=>totals.set(v,(totals.get(v)||0)+t.weights[i]));
 for(const n of totals.values())assert.ok(n<=14);
 assert.deepEqual(s.frontier.map(p=>[p.key,p.total]).sort(),[...totals].filter(([,n])=>n<14).sort());
 for(let i=0;i<s.tiles.length;i++)for(let j=0;j<i;j++){
  const a=s.tiles[i],b=s.tiles[j];assert.ok(intersectionArea(a.loop,b.loop)<1e-8,'interior overlap');
  if(s.forbidden&&a.kind===b.kind)assert.ok(a.vertices.filter(v=>b.vertices.includes(v)).length<2,'forbidden edge survived');
 }
}
const identity=s=>({tiles:s.tiles.map(t=>[t.id,t.generation]),frontier:s.frontier.map(p=>[p.key,p.total,p.depth]).sort()});
let rollbackChecks=0;
for(const forbidden of [false,true]){
 const search=createSevenfoldSearch({forbidden,nodeLimit:1200}),stack=[];let reached=false;
 search.next();search.audit();
 for(let i=0;i<4000;i++){
  const before=search.snapshot(),result=search.next(),after=search.snapshot();
  if(result.value?.type==='add')stack.push(identity(before));
  if(result.value?.type==='remove'){assert.deepEqual(identity(after),stack.pop());rollbackChecks++;}
  if(i%60===0)search.audit();
  if(after.tiles.length>=30&&!after.graph.deadPoints){reached=true;break;}if(result.done)break;
 }
 assert.ok(reached);search.audit();replay(search.snapshot());
 console.log(JSON.stringify({forbidden,tiles:search.snapshot().tiles.length,stats:search.snapshot().stats}));
}
assert.ok(rollbackChecks>0);
for(const kind of [1,2,3]){
 const s=createSevenfoldSearch({kinds:[kind],nodeLimit:100});s.next();for(let i=0;i<100;i++){const r=s.next();if(r.done||s.snapshot().tiles.length>=12)break;}
 assert.ok(s.snapshot().tiles.every(t=>t.kind===kind));replay(s.snapshot());
}
const budget=createSevenfoldSearch({nodeLimit:0});budget.next();assert.ok(budget.next().done);assert.match(budget.snapshot().status,/unknown/);
assert.throws(()=>catalog([]));
console.log(`Sevenfold arithmetic, catalog, markings, scheduling, graph completeness, geometry replay, selections, budget and ${rollbackChecks} rollback checks passed.`);
