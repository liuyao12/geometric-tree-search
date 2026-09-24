import assert from 'node:assert/strict';
import {createPointMarking,createVertexCompletion} from '../assets/sevenfold-point-marking.js';
import {catalog,placement,ZERO,sub,key,createSevenfoldSearch} from '../assets/sevenfold-rhombs.js';
import {socolarWitness} from './socolar-multigrid.mjs';

// Assigned zero is not missing; shared references survive one tile's rollback.
const field=createPointMarking(),a={marks:[{address:'p/0',point:ZERO,channel:0,value:0}]};
const bad={marks:[{...a.marks[0],value:1}]};
assert.equal(field.rejects(bad),false);field.add(a);field.add(a);
assert.equal(field.rejects(bad),true);field.remove(a);
assert.deepEqual(field.inspect(),[['p/0',0,1]]);field.remove(a);
assert.deepEqual(field.inspect(),[]);assert.equal(field.rejects(bad),false);

// Enumerate ALL positive-support alignments independently, including the
// midpoint obligations missed by the previous corner-only model.
for(const rule of ['none','socolar']){
 const templates=catalog([1,2,3],rule),search=createSevenfoldSearch({rule});search.next();
 for(const p of search.snapshot().tiles[0].support){
  const expected=new Set();
  for(const t of templates)for(const q of placement(t,ZERO).support){
   const delta=sub(p.exact,q.exact);if(delta.some(n=>n%2))continue;
   expected.add(placement(t,delta.map(n=>n/2)).id);
  }
  const moves=search.movesAtSupport(p.exact);
  assert.deepEqual(new Set(moves.map(t=>t.id)),expected);
  assert.equal(moves.length,expected.size,'no duplicate decorated placements');
  for(const t of moves)assert.ok(t.support.some(q=>q.key===key(p.exact)));
 }
}

const templates=catalog([1,2,3],'socolar');
const palette=[...new Map(templates.flatMap(t=>t.corners).map(c=>[JSON.stringify(c),c])).values()];
const completion=createVertexCompletion(palette,{cacheLimit:128});
// Independent exact-cover backtracker over sector masks, not the production
// gap/bitset dynamic program. Labels are constraints on boundary rays.
const sectorMask=c=>Array.from({length:c.width},(_,j)=>1<<((c.start+j)%14)).reduce((a,b)=>a|b,0);
const choices=palette.map(c=>({...c,mask:sectorMask(c)}));
function reference(given){
 let mask=0,labels=Array(14).fill(-1);
 function fit(c,m,l){if(m&c.mask)return null;const next=l.slice(),end=(c.start+c.width)%14;
  for(const [ray,value]of [[c.start,c.from],[end,c.to]]){if(next[ray]!==-1&&next[ray]!==value)return null;next[ray]=value;}return next;}
 for(const c of given){const item={...c,mask:sectorMask(c)},next=fit(item,mask,labels);if(!next)return false;mask|=item.mask;labels=next;}
 const failed=new Set();
 function fill(m,l){if(m===16383)return true;const signature=m+':'+l.join(',');if(failed.has(signature))return false;
  let bit=1;while(m&bit)bit<<=1;
  for(const c of choices)if(c.mask&bit){const next=fit(c,m,l);if(next&&fill(m|c.mask,next))return true;}
  failed.add(signature);return false;}
 return fill(mask,labels);
}
let random=7;const rng=n=>{random=(Math.imul(random,1664525)+1013904223)>>>0;return random%n;};
let negatives=0;
for(let i=0;i<250;i++){
 const corners=Array.from({length:1+rng(4)},()=>palette[rng(palette.length)]),expected=reference(corners);
 assert.equal(completion.allows(corners),expected);assert.equal(completion.allows(corners.slice().reverse()),expected);negatives+=!expected;
}
assert.ok(negatives>0);assert.equal(completion.snapshot().cached,128);assert.ok(completion.snapshot().hits>=250);
const witness=await socolarWitness(),stars=new Map();
for(const tile of witness)tile.vertices.forEach((v,i)=>{if(!stars.has(v))stars.set(v,[]);stars.get(v).push(tile.corners[i]);});
for(const corners of stars.values()){
 assert.equal(completion.allows(corners),true,'independent seven-grid star');
 for(let i=0;i<corners.length;i++)assert.equal(completion.allows(corners.filter((_,j)=>j!==i)),true,'partial witness star');
}

// Regression for the reported stall: useful growth, forced propagation, no
// repeated decorated attempt in the same parent, and exhaustive graph audit.
const search=createSevenfoldSearch({rule:'socolar',nodeLimit:400,trace:true});
for(let i=0;i<1200;i++){const r=search.next(),p=search.progress();if(p.tiles>=80&&!p.deadPoints||r.done)break;}
const result=search.snapshot();assert.equal(result.tiles.length,80);assert.equal(result.graph.deadPoints,0);
assert.ok(result.stats.forcedMoves>0);assert.equal(result.stats.repeatedAttempts,0);
assert.ok(result.marking.prunes>0);assert.ok(result.completion.prunes>0);search.audit();
console.log(JSON.stringify({tiles:result.tiles.length,stats:result.stats,marking:result.marking,completion:result.completion}));
console.log('Point marking rollback, complete midpoint alignments, independent corner solver, witness stars and 80-tile growth passed.');
