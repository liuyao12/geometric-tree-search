import assert from 'node:assert/strict';
import {ZERO,key,add,sub,neg,compare,direction,xy,catalog,translated,markingsAgree,geometryAllowed,createSevenfoldSearch,chooseSevenfoldPoint} from '../assets/sevenfold-rhombs.js';

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
const adjacent=translated(root,u);assert.ok(geometryAllowed(root,adjacent));assert.ok(markingsAgree(root,adjacent));
assert.equal(geometryAllowed(root,root),false);
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
  assert.ok(markingsAgree(a,b),'edge label conflict');
 }
}
const identity=s=>({tiles:s.tiles.map(t=>[t.id,t.generation]),frontier:s.frontier.map(p=>[p.key,p.total,p.depth]).sort()});
let rollbackChecks=0;
for(const rule of ['none','socolar']){
 const search=createSevenfoldSearch({rule,nodeLimit:1200}),stack=[];let reached=false;
 search.next();search.audit();
 for(let i=0;i<(rule==='socolar'?120:4000);i++){
  const before=search.snapshot(),result=search.next(),after=search.snapshot();
  if(result.value?.type==='add')stack.push(identity(before));
  if(result.value?.type==='remove'){assert.deepEqual(identity(after),stack.pop());rollbackChecks++;}
  if(i%60===0)search.audit();
  if(after.tiles.length>=30&&!after.graph.deadPoints){reached=true;break;}if(result.done)break;
 }
 if(rule==='none')assert.ok(reached);search.audit();replay(search.snapshot());
 console.log(JSON.stringify({rule,tiles:search.snapshot().tiles.length,stats:search.snapshot().stats}));
}
assert.ok(rollbackChecks>0);
for(const kind of [1,2,3]){
 const s=createSevenfoldSearch({kinds:[kind],nodeLimit:100});s.next();for(let i=0;i<100;i++){const r=s.next();if(r.done||s.snapshot().tiles.length>=12)break;}
 assert.ok(s.snapshot().tiles.every(t=>t.kind===kind));replay(s.snapshot());
}
const budget=createSevenfoldSearch({nodeLimit:0});budget.next();assert.ok(budget.next().done);assert.match(budget.snapshot().status,/unknown/);
assert.throws(()=>catalog([]));
console.log(`Sevenfold arithmetic, catalog, markings, scheduling, graph completeness, geometry replay, selections, budget and ${rollbackChecks} rollback checks passed.`);

// Published construction: 8 variants per shape up to rotation, 16 for a
// fixed oriented geometry; 21 oriented geometries give 336 templates.
const marked=catalog([1,2,3],'socolar');assert.equal(marked.length,336);
const {placement,edgeAxis}=await import('../assets/sevenfold-rhombs.js');
for(const t of marked){
 for(let i=0;i<4;i++){
  const a=edgeAxis(sub(t.points[(i+1)%4],t.points[i]));
  const b=edgeAxis(sub(t.points[(i+2)%4],t.points[(i+1)%4]));
  const delta=(b.axis-a.axis+7)%7,k=Math.min(delta,7-delta)-1;
  assert.equal(t.edgeCodes[i].value^t.edgeCodes[(i+2)%4].value,1<<k);
 }
}
const markedSearch=createSevenfoldSearch({rule:'socolar'});markedSearch.next();assert.equal(markedSearch.movesAt(ZERO).length,1344);
const mr=markedSearch.snapshot().tiles[0];
const neighbors=markedSearch.movesAt(mr.points[0]).filter(t=>t.kind===mr.kind&&geometryAllowed(mr,t)&&t.vertices.filter(v=>mr.vertices.includes(v)).length===2);
assert.ok(neighbors.some(t=>markingsAgree(mr,t)),'must allow some same-shaped neighbors');
assert.ok(neighbors.some(t=>!markingsAgree(mr,t)),'must reject wrong same-shaped sides/arrows');
const {socolarWitness}=await import('./socolar-multigrid.mjs');
const witness=await socolarWitness();assert.ok(witness.length>400);
replay({tiles:witness,frontier:(()=>{const totals=new Map();for(const t of witness)t.vertices.forEach((v,i)=>totals.set(v,(totals.get(v)||0)+t.weights[i]));return [...totals].filter(([,n])=>n<14).map(([key,total])=>({key,total}));})()});
// Independently read row chains: equal shapes must alternate the OTHER axis.
const edges=new Map();for(const t of witness)for(let i=0;i<4;i++){
 const m=t.marks[i],address=m.address;if(!edges.has(address))edges.set(address,[]);edges.get(address).push({t,i});
}
let chains=0;
for(let m=0;m<7;m++)for(const first of witness){
 const start=first.edgeCodes.findIndex(c=>c.channel===m);if(start<0)continue;
 let tile=first,entry=start;const seen=new Set(),last=new Map();
 while(tile&&!seen.has(tile.id)){
  seen.add(tile.id);const other=tile.edgeCodes.find(c=>c.channel!==m).channel,delta=(other-m+7)%7,k=Math.min(delta,7-delta);
  if(last.has(k))assert.equal((last.get(k)+other-2*m+14)%7,0,'row orientation must alternate');last.set(k,other);
  const exit=(entry+2)%4,next=edges.get(tile.marks[exit].address).find(x=>x.t!==tile);tile=next?.t;entry=next?.i;
 }
 if(seen.size>5)chains++;
}
assert.ok(chains>100);console.log(`Socolar catalog, side-specific same-shape contacts, ${witness.length}-tile independent witness and ${chains} row chains passed.`);
// Verify exact closure under rotations/reflection and the 24 rotation classes.
function transformedSignature(t,turn=0,reflect=false){
 const transform=p=>p.reduce((sum,n,j)=>add(sum,direction(turn+(reflect?-2*j:2*j)).map(x=>x*n)),ZERO);
 const points=t.points.map(transform),origin=points.slice().sort(compare)[0];
 const support=points.map((p,i)=>key(sub(p,origin))+'~'+t.weights[i]).sort().join('|');
 const marks=t.edgeCodes.map((m,i)=>{
  const axis=edgeAxis(transform(direction(2*m.channel))),point=transform(add(t.points[i],t.points[(i+1)%4]));
  return key(sub(point,origin.map(x=>2*x)))+'/'+axis.axis+'='+ (axis.sign===1?m.value:m.value^7);
 }).sort().join('|');
 return t.kind+':'+support+'@'+marks;
}
const signatures=new Set(marked.map(t=>transformedSignature(t))),orbits=new Set();
for(const t of marked){
 assert.ok(signatures.has(transformedSignature(t,1)),'rotation closure');
 assert.ok(signatures.has(transformedSignature(t,0,true)),'reflection closure');
 orbits.add(Array.from({length:14},(_,j)=>transformedSignature(t,j)).sort()[0]);
}
assert.equal(orbits.size,24);console.log('24 decorated rotation classes; rotation/reflection actions verified.');
