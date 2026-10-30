import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {Golden as G,vector,vadd,vscale,dot} from '../assets/golden-field.js';
import {I,O,mv,preparePrototype,place,exactIntersectionVolume,fullFeatureContacts,PolyhedralModel,PolyhedralSearch,chooseObligation} from '../assets/polyhedral-exact-search.js';
import {FinitePointSearch} from '../assets/finite-point-search.js';
import {createSearchModel,CONCRETE_SYSTEMS,wangTiles} from '../apps/quasicrystal-exact/search-models.js';
import {goodmanControl,scdControl} from '../apps/quasicrystal-exact/registered-controls.js';
const data=JSON.parse(await readFile(new URL('../apps/quasicrystal-exact/data/polyhedra-exact.json',import.meta.url)));
const body=preparePrototype({...wangTiles()[0],id:'box',pointMarkings:[]}),unit=place(body);
const shift=(x,y=0n,z=0n)=>place(body,I,vector(x,y,z));
assert(exactIntersectionVolume(unit,shift(new G(1n,0n,2n))).equals(new G(1n,0n,2n)));
assert(exactIntersectionVolume(unit,unit).equals(1n));
for(const p of [vector(1n,0n,0n),vector(1n,1n,0n),vector(1n,1n,1n),vector(3n,0n,0n)]){
 const other=place(body,I,p);assert.equal(exactIntersectionVolume(unit,other).sign(),0);assert(fullFeatureContacts(unit,other));
}
assert.equal(fullFeatureContacts(unit,shift(1n,new G(1n,0n,2n))),false,'partial-face contact rejected');
const huge=10n**40n,far=place(body,I,vector(huge,0n,0n)),farHalf=place(body,I,vector(new G(2n*huge+1n,0n,2n),0n,0n));
assert(exactIntersectionVolume(far,farHalf).equals(new G(1n,0n,2n)),'huge translations retain exact half volume');
const obligation=(key,generation,n)=>({key,generation,candidates:new Set(Array.from({length:n},(_,i)=>i))});
assert.equal(chooseObligation(new Map([['a',obligation('a',0,1)],['b',obligation('b',9,0)]])).kind,'dead');
assert.equal(chooseObligation(new Map([['a',obligation('a',0,3)],['b',obligation('b',9,1)]])).point.key,'b');
assert.equal(chooseObligation(new Map([['a',obligation('a',0,8)],['b',obligation('b',9,2)]])).point.key,'a');
const finish=(s,limit=500)=>{for(let i=0;i<limit&&!['complete','checkpoint','exhausted','budget'].includes(s.state);i++)s.step();return s;};
for(const id of ['danzer','danzerOcta','wang','socolar']){
 const model=createSearchModel(id,data),s=new PolyhedralSearch(model,{target:4,budget:30,maxCandidates:5000});
 const before=JSON.stringify(s.inspect()),candidate=[...s.candidates.values()].find(r=>r.legal),trail=s.trail.length;s.apply(candidate.tile);s.undo(trail);assert.equal(JSON.stringify(s.inspect())===before,true,`${id} exact rollback`);
 finish(s);assert.equal(s.state,'checkpoint',`${id} real growth`);assert.equal(s.summary().domainsComplete,true);
 for(const p of s.frontier.values()){
  const expected=model.attachments(p.owner.tile,p.owner.face).filter(t=>!s.candidates.get(t.id)?.excluded&&s.legal(t)).map(t=>t.id).sort();assert.deepEqual([...p.candidates].sort(),expected,`${id} complete bipartite domain`);
 }
 const tiles=[...s.placed.values()].map(r=>r.tile);for(let i=0;i<tiles.length;i++)for(let j=0;j<i;j++)assert.equal(exactIntersectionVolume(tiles[i],tiles[j]).sign(),0);
 console.log(id,s.summary().attempts,'trials',s.summary().backtracks,'backtracks');
}
const marked=createSearchModel('danzer',data),bare=createSearchModel('danzer',data,{geometryOnly:true});
assert(marked.prototypes.some(p=>p.mirror));assert(marked.prototypes.every(p=>p.rightAngleEdges.length));
let restricted=false;for(const proto of marked.prototypes.filter(p=>!p.mirror)){const t=place(proto);for(let f=0;f<t.faces.length;f++)if(marked.attachments(t,f).length<bare.attachments(t,f).length)restricted=true;}assert(restricted,'blue-edge rule restricts exact attachments');
const exhausted=new PolyhedralSearch(new PolyhedralModel({id:'budget',tiles:[wangTiles()[0]],mirrors:false}),{maxCandidates:0});assert.equal(exhausted.state,'budget');assert.equal(exhausted.summary().domainsComplete,false);assert.equal(exhausted.summary().dead,null);
for(const id of ['goodman','goodmanCross','scd']){
 const model=id==='scd'?scdControl(data):goodmanControl(id,data),s=new FinitePointSearch(model,{target:150});
 const before=JSON.stringify(s.inspect()),r=[...s.candidates.values()].find(r=>r.legal),trail=s.trail.length;s.apply(r.tile);s.undo(trail);assert.equal(JSON.stringify(s.inspect())===before,true,`${id} point rollback`);
 finish(s);assert.equal(s.state,'complete');assert(s.verify());
 for(const p of s.points.values())assert.equal(p.total,3n===model.capacity?3n:1n);
 const tiles=[...s.placed.values()].map(r=>r.tile);for(let i=0;i<tiles.length;i++)for(let j=0;j<i;j++)assert.equal(exactIntersectionVolume(tiles[i],tiles[j],{used:0,max:150000}).sign(),0,`${id} independently replayed solid interiors`);
 if(id==='scd')assert(s.summary().eliminatedMarking>0,'layer-history mark-only pruning');
 console.log(id,s.placed.size,'tiles; independent finite replay passed');
}
// A rational residue with no remaining candidate is dead, even though the point
// has a positive assigned value. Mark-only points register independent edges.
const tile=(id,key,weight,value)=>({id,kind:id,occupancy:[{key,weight}],pointMarkings:value===undefined?[]:[{point:vector(20n,0n,0n),components:{x:value}}],vertices:[],faces:[]});
const tiny={id:'residue',placements:[tile('root','p',1n),tile('a','q',1n,0n),tile('b','r',1n,1n)],required:['p','q','r'],capacity:3n,seedId:'root'};
const residual=new FinitePointSearch(tiny);assert.equal(chooseObligation(residual.frontier).kind,'dead');
const t2={...tiny,capacity:1n},marks=new FinitePointSearch(t2);const saved=JSON.stringify(marks.inspect()),at=marks.trail.length;marks.apply(t2.placements[1]);assert.equal(marks.frontier.get('r').candidates.size,0);marks.undo(at);assert.equal(JSON.stringify(marks.inspect())===saved,true);
assert(!CONCRETE_SYSTEMS.includes('taylor'));assert(!CONCRETE_SYSTEMS.includes('schmittTriple'));
assert.throws(()=>createSearchModel('taylor',data),/No generic/);
const d=data,L=place(preparePrototype(d.systems.goodman[1])),X=place(preparePrototype(d.systems.goodmanCross[1])),p=preparePrototype(d.systems.goodman[0]),axes=[I,[vector(0n,1n,0n),vector(-1n,0n,0n),vector(0n,0n,1n)],[vector(0n,0n,1n),vector(0n,1n,0n),vector(-1n,0n,0n)]],parts=axes.map(R=>place(p,R));
assert(exactIntersectionVolume(L,X).equals(X.volume));for(const t of parts)assert(exactIntersectionVolume(t,X).equals(t.volume));for(let i=0;i<3;i++)for(let j=0;j<i;j++)assert.equal(exactIntersectionVolume(parts[i],parts[j]).sign(),0);assert(parts.reduce((s,t)=>s.add(t.volume),new G(0n)).equals(X.volume));console.log('Exact nonconvex containment and three-I dissection passed');

console.log('All exact carrier/control conformance checks passed');
