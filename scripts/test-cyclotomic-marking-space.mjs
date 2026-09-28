import assert from 'node:assert/strict';
import {createMarkingSpace} from '../assets/cyclotomic-marking-space.js';
import {selectedPenroseProblem} from '../assets/penrose-selection-problem.js';
import {createObstructionSearch} from '../assets/cyclotomic-obstruction-search.js';
import {add,sub,num} from '../assets/penrose-polygon.js';
import {latticeKey} from '../assets/cyclotomic-five.js';

// Independent oracle: physically transform the entire patch, collect all
// coincident addresses, then find connected components by graph traversal.
// It never calls the learner's action permutations, union operation or trail.
function oracle(problem,space,patch){
 const {slots}=space.inspect(),lookup=new Map(slots.map(s=>[s.type+'@'+latticeKey(s.offset),s.slot])),byType=new Map();
 for(const s of slots){if(!byType.has(s.type))byType.set(s.type,[]);byType.get(s.type).push(s);}
 const edges=slots.map(()=>new Set());
 for(const g of problem.actions){const occupied=new Map();
  for(const original of patch){const tile=problem.rigid(original,g);
   for(const r of byType.get(tile.type)){const key=latticeKey(add(tile.origin,r.offset)),i=lookup.get(tile.type+'@'+latticeKey(r.offset)),j=occupied.get(key);
    if(j!==undefined){edges[i].add(j);edges[j].add(i);}occupied.set(key,i);
   }
  }
 }
 const classes=Array(slots.length).fill(-1);let dimension=0;
 for(let i=0;i<slots.length;i++)if(classes[i]<0){dimension++;const todo=[i];classes[i]=i;while(todo.length){const a=todo.pop();for(const b of edges[a])if(classes[b]<0){classes[b]=i;todo.push(b);}}}
 return{classes,dimension};
}
function check(problem,space,patch){
 const expected=oracle(problem,space,patch),actual=space.inspect(),s=space.snapshot();
 assert.deepEqual(actual.classes,expected.classes);assert.equal(s.dimension,expected.dimension);assert.equal(s.variables-s.rank,s.dimension);assert(s.dimension>=1,'constants survive');
 for(const p of actual.permutations){const images=new Map();actual.classes.forEach((c,i)=>{if(images.has(c))assert.equal(images.get(c),actual.classes[p[i]]);images.set(c,actual.classes[p[i]]);});assert.equal(new Set(images.values()).size,s.dimension);}
 const active=new Map(),tables=new Map(s.tables.map(t=>[t.type,t.rows]));
 for(const t of patch)for(const r of tables.get(t.type)){const key=latticeKey(add(t.origin,r.offset));if(active.has(key))assert.equal(active.get(key),r.value);active.set(key,r.value);}
 assert.deepEqual(space.memory(),{points:active.size,values:active.size});
 return s;
}
for(const kinds of [['thick','thin'],['kite','dart'],['p5','p3','p2','diamond','boat','star'],['thick','kite']])for(const boundaryRule of ['supplied','none']){
 const problem=selectedPenroseProblem(kinds,{boundaryRule}),space=createMarkingSpace(problem),patch=[];
 const search=createObstructionSearch({problem,targetCount:9,nodeLimit:40,seed:1,generationFirst:true});
 const initial=space.snapshot();assert.equal(initial.dimension,initial.variables);assert.equal(initial.contacts,0);
 let tested=0,rollbacks=0,peakRank=0;
 for(let r=search.next();!r.done;r=search.next()){
  if(r.value.type==='add'){patch.push(r.value.tile);space.push(r.value.tile);tested++;}
  if(r.value.type==='remove'){const tile=patch.pop();assert.equal(tile.id,r.value.tile.id);space.pop(tile);rollbacks++;}
  if(['add','remove'].includes(r.value.type))peakRank=Math.max(peakRank,check(problem,space,patch).rank);
 }
 const final=check(problem,space,patch);assert(peakRank>0);assert(tested>1);
 const beforeRevision=space.revision;
 while(patch.length)space.pop(patch.pop());
 const restored=check(problem,space,patch);assert.deepEqual(restored.tables,initial.tables);assert.equal(restored.contacts,0);assert(final.rank===0||space.revision>beforeRevision);assert.throws(()=>space.pop(problem.seedTile),/rollback/);
 // Trial-independent learner does not inspect edge-label values.
 if(boundaryRule==='none')assert(problem.catalog.every(t=>t.labels.length===0));
 console.log(kinds.join('/'),boundaryRule,final.variables,'->',final.dimension,'dimensions;',rollbacks,'backtracks checked');
}
// Provisional distinctions cannot filter a candidate: observer and plain
// runs have exactly the same graph and event sequence, including failures.
for(const boundaryRule of ['supplied','none']){
 const run=learn=>createObstructionSearch({problem:selectedPenroseProblem(['thick','thin'],{boundaryRule}),learn,markingKind:'space',generationFirst:true,targetCount:15,nodeLimit:400});
 const observer=run(true),plain=run(false);let steps=0,removes=0;
 while(true){const a=observer.next(),b=plain.next();assert.equal(a.done,b.done);assert.deepEqual(a.value,b.value);assert.deepEqual(observer.inspectGraph(),plain.inspectGraph());if(a.done)break;steps++;if(a.value.type==='remove')removes++;}
 observer.audit();assert(steps>10);if(boundaryRule==='supplied')assert(removes>0);
 console.log('identical observed/plain trace:',boundaryRule,steps,'events',removes,'backtracks');
}
assert.throws(()=>selectedPenroseProblem(['thick'],{boundaryRule:'invented'}),/boundary rule/);
console.log('ok: independent orbit-contact oracle, exact rollback, induced group actions and unchanged search');
