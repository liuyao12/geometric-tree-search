import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {ZERO,key,add,sub,direction,xy,rotate,star,catalog,placement,createABSearch,chooseABPoint,markingsAgree,houseChoices} from '../assets/ammann-beenker.js';
import {createABCompletion} from '../assets/ammann-beenker-marking.js';
for(let j=0;j<8;j++){const p=xy(direction(j));assert.ok(Math.abs(p.x-Math.cos(j*Math.PI/4))<1e-12);assert.ok(Math.abs(p.y-Math.sin(j*Math.PI/4))<1e-12);assert.deepEqual(add(direction(j),direction(j+4)),ZERO);assert.deepEqual(star(star(direction(j))),direction(j));}
const full=catalog(),bare=catalog([1,2],'none');assert.equal(bare.length,6);assert.equal(catalog([1,2],'edges').length,12);assert.equal(full.length,904);
for(const t of full){assert.equal(t.weights.reduce((a,b)=>a+b),8);assert.ok(t.houses.every((h,i)=>houseChoices(t.corners[i].start,t.normals[i]).includes(h)));}
function symmetrySignature(t,rotation=0,reflect=false){
 const transform=p=>p.reduce((s,n,j)=>add(s,direction((reflect?-j:j)+rotation).map(x=>x*n)),ZERO),points=t.points.map(transform);
 const origin=points.slice().sort((a,b)=>a.reduce((c,n,i)=>c||n-b[i],0))[0];
 return points.map((p,i)=>key(sub(p,origin))+'~'+t.weights[i]+'~h'+((reflect?4-t.houses[i]:t.houses[i])+rotation+8)%8).sort().join('|')+'@'+t.points.map((p,i)=>key(sub(transform(add(p,t.points[(i+1)%4])),add(origin,origin)))+'~'+((reflect?-t.edgeCodes[i]:t.edgeCodes[i])+rotation+8)%8).sort().join('|');
}
const signatures=new Set(full.map(t=>symmetrySignature(t)));
for(const t of full){assert.ok(signatures.has(symmetrySignature(t,1)));assert.ok(signatures.has(symmetrySignature(t,0,true)));}
// Independent published witness: extracted from PDF paths, not this catalog.
const fixture=JSON.parse(readFileSync(new URL('./fixtures/ammann-beenker-star.json',import.meta.url))),witness=[];
for(const f of fixture.tiles){let match;
 for(const template of full)for(let i=0;i<4&&!match;i++){
  const t=placement(template,sub(f.points[0],template.points[i]));
  if(f.points.every((p,j)=>key(t.points[(i+j)%4])===key(p)&&t.edgeCodes[(i+j)%4]===f.edgeCodes[j]&&t.houses[(i+j)%4]===f.houses[j]&&JSON.stringify(t.normals[(i+j)%4])===JSON.stringify(f.normals[j])))match=t;
 }assert.ok(match,'published decorated star tile absent');witness.push(match);
}
for(const a of witness)for(const b of witness)assert.ok(markingsAgree(a,b));
const completion=createABCompletion(full.flatMap(t=>t.corners)),stars=new Map();for(const t of witness)t.vertices.forEach((v,i)=>{if(!stars.has(v))stars.set(v,[]);stars.get(v).push(t.corners[i]);});
for(const cs of stars.values())for(let mask=1;mask<(1<<cs.length);mask++)assert.ok(completion.allows(cs.filter((_,i)=>mask&(1<<i))),'published full/partial star rejected');
// Check every support alignment against a separate template/support product.
for(const rule of ['none','edges','full']){const ts=catalog([1,2],rule),s=createABSearch({rule});s.next();for(const p of s.snapshot().tiles[0].support){
 const expected=new Set();for(const t of ts)for(const q of placement(t,ZERO).support){const d=sub(p.exact,q.exact);if(d.every(n=>n%2===0))expected.add(placement(t,d.map(n=>n/2)).id);}
 const moves=s.movesAtSupport(p.exact);assert.equal(moves.length,expected.size);assert.deepEqual(new Set(moves.map(t=>t.id)),expected);
}}
const p=(key,depth,n)=>({key,depth,candidates:Array(n).fill('x')});assert.equal(chooseABPoint([p('forced',0,1),p('dead',9,0)]).key,'dead');assert.equal(chooseABPoint([p('early',0,5),p('late',9,1)]).key,'late');assert.equal(chooseABPoint([p('early',0,5),p('late',9,2)]).key,'early');
const identity=s=>({tiles:s.snapshot().tiles.map(t=>[t.id,t.generation]),frontier:s.snapshot().frontier.map(p=>[p.key,p.total,p.depth]).sort(),marking:s.inspectMarking()});
const search=createABSearch({nodeLimit:800,trace:true}),stack=[];search.next();search.audit();let rollback=0;
for(let i=0;i<2500;i++){const before=identity(search),r=search.next();if(r.value?.type==='add')stack.push(before);if(r.value?.type==='remove'){assert.deepEqual(identity(search),stack.pop());rollback++;}const p=search.progress();if(r.done||p.tiles>=80&&!p.deadPoints)break;}
const result=search.snapshot();assert.equal(result.tiles.length,80);assert.equal(result.graph.deadPoints,0);assert.equal(result.stats.repeatedAttempts,0);assert.ok(rollback>0);assert.ok(result.marking.prunes>0);assert.ok(result.completion.prunes>0);search.audit();
// Independent polygon clipping, rather than the production separating axes.
const cross=(a,b,p)=>(b.x-a.x)*(p.y-a.y)-(b.y-a.y)*(p.x-a.x);
function area(a,b){let out=a.slice();for(let i=0;i<4;i++){const q=b[i],r=b[(i+1)%4],input=out;out=[];for(let j=0;j<input.length;j++){const s=input[j],e=input[(j+1)%input.length],cs=cross(q,r,s),ce=cross(q,r,e);if(cs>=-1e-10)out.push(s);if(cs*ce< -1e-18){const t=cs/(cs-ce);out.push({x:s.x+t*(e.x-s.x),y:s.y+t*(e.y-s.y)});}}}return Math.abs(out.reduce((n,p,i)=>{const q=out[(i+1)%out.length];return n+p.x*q.y-p.y*q.x;},0))/2;}
const totals=new Map();for(const t of result.tiles)for(const p of t.support)totals.set(p.key,(totals.get(p.key)||0)+p.weight);assert.ok([...totals.values()].every(n=>n<=8));assert.deepEqual(result.frontier.map(p=>[p.key,p.total]).sort(),[...totals].filter(([,n])=>n<8).sort());
for(let i=0;i<result.tiles.length;i++)for(let j=0;j<i;j++){assert.ok(markingsAgree(result.tiles[i],result.tiles[j]));assert.ok(area(result.tiles[i].loop,result.tiles[j].loop)<1e-8);}
for(const rule of ['none','edges']){const s=createABSearch({rule,nodeLimit:200});for(let i=0;i<650;i++){const r=s.next();if(r.done||s.progress().tiles>=20&&!s.progress().deadPoints)break;}assert.ok(s.progress().tiles>=20);s.audit();}
const budget=createABSearch({nodeLimit:0});budget.next();assert.ok(budget.next().done);assert.match(budget.snapshot().status,/unknown/);assert.throws(()=>catalog([]));
console.log(JSON.stringify({tiles:result.tiles.length,stats:result.stats,rollback}));console.log('Cyclotomic arithmetic, published house fragments, complete catalog/alignment, scheduling, exact rollback, graph audit and independent geometric replay passed.');
