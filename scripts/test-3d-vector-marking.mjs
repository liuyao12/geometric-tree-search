import assert from 'node:assert/strict';
import {OnlineMarking,pairCompatible,LearnedSection,learnMarking,reuseMarking,pointSymmetries} from '../apps/3d-lattice-tiler/marking-learning.js';
import {markingVectors} from '../apps/3d-lattice-tiler/marking-display.js';
import {prepareModel} from '../apps/3d-lattice-tiler/v2/model.js';
import {markingSystem} from '../apps/3d-lattice-tiler/marking-storage.js';
// Artificial labels on real translated point overlaps; this tests synthesis,
// not the oracle or any geometric impossibility claim.
const model={capacity:8,orientations:[{type:0,index:0,cells:Array.from({length:8},(_,x)=>({pos:[x,0,0],weight:1}))}]};
const transforms=[{permutation:[0,1,2],signs:[1,1,1],transform:p=>p,map:[{oi:0,shift:[0,0,0]}]}];
const pair=x=>[{oi:0,translation:[0,0,0]},{oi:0,translation:[x,0,0]}];
const single=new OnlineMarking(model,transforms,{extent:0,maxComponents:1}),vector=new OnlineMarking(model,transforms,{extent:0});
for(let x=1;x<8;x++){
 const row={pair:pair(x),status:[3,4,6].includes(x)?'valid':'invalid'};
 single.add(row);const m=vector.add(row);
 for(const positive of vector.rows.filter(r=>r.status==='valid'))assert.ok(pairCompatible(m.fields,positive.pair));
}
const a=single.snapshot({maxEvaluations:2048}),b=vector.snapshot({maxEvaluations:2048});
assert.equal(a.negativeBlocked,3);assert.equal(b.negativeBlocked,4);assert.equal(b.componentCount,2);
assert.equal(b.positivePassed,3);
assert.equal(b.values,b.fields.flat().length);assert.equal(b.points,new Set(b.fields[0].map(m=>m.pos.join())).size);
const section=new LearnedSection(model,b);section.add({type:0,index:0,translation:[0,0,0]});
for(let x=1;x<8;x++)assert.equal(section.compatible({type:0,index:0,translation:[x,0,0]}),[3,4,6].includes(x));
section.remove({type:0,index:0,translation:[0,0,0]});assert.equal(section.section.size,0);
// A later positive overrides every component's old separation of that pair.
const updated=vector.add({pair:pair(7),status:'valid'});
assert.equal(updated.positivePassed,4);assert.ok(pairCompatible(updated.fields,pair(7)));assert.equal(updated.negativeBlocked,3);
const display=markingVectors([{pos:[0,0,0],component:1,value:0},{pos:[0,0,0],component:3,value:2}],4);
assert.deepEqual(display.get('0,0,0'),['*',0,'*',2]);
assert.throws(()=>new OnlineMarking(model,transforms,{maxComponents:0}),/component budget/);
const collect=async stream=>{let final;for await(const e of stream)final=e;return final;};
// Replay genuinely oracle-labeled slab catalogues; no learned values in fixtures.
for(const tile of ['a2_turtle_prism','a2_hat_prism']){
 const slab=prepareModel({tile,radius:1,mirrors:true}),learned=(await collect(learnMarking(slab,{timeMs:30000}))).marking;
 assert.ok(learned.accepted);assert.equal(learned.negativeBlocked,learned.counts.invalid);assert.ok(learned.componentCount>1);
 const group=pointSymmetries(slab);
 const lookup=learned.fields.map(field=>new Map(field.map(m=>[`${m.pos}|${m.component}`,m.value])));
 for(let gi=0;gi<group.length;gi++)for(let oi=0;oi<learned.fields.length;oi++)for(const m of learned.fields[oi]){
  const g=group[gi],target=g.map[oi],p=g.transform(m.pos).map((x,i)=>x-target.shift[i]);
  assert.equal(lookup[target.oi].get(`${p}|${m.component}`),learned.representation[gi][m.value]);
 }
 const entry={domain:markingSystem(slab),marking:learned};
 const replay=(await collect(reuseMarking(slab,entry,{timeMs:30000}))).marking;
 for(const key of ['points','values','componentCount','negativeBlocked'])assert.equal(replay[key],learned[key]);
 for(const mutation of [m=>m.fields[0].push({...m.fields[0][0]}),m=>m.fields[0][0].component=4,m=>m.fields[0][0].component=-1,m=>m.fields[0][0].component=.5]){
  const invalid=structuredClone(entry);mutation(invalid.marking);await assert.rejects(collect(reuseMarking(slab,invalid)),/Invalid saved point value/);
 }
 console.log(JSON.stringify({tile,positivePassed:learned.positivePassed,negativeBlocked:learned.negativeBlocked,components:learned.componentCount,points:learned.points,values:learned.values,elapsedMs:learned.elapsedMs}));
}
console.log('PASS independent component separators, later-positive revalidation, symmetry, ordinary section rollback, full vectors with *, distinct point/value counts, and saved vector replay.');
// Saved vectors can assign several components at one point; count the point
// once and each assigned component separately. This constant-zero control is
// generated in this test after fresh oracle learning, never bundled as a model.
const cube=prepareModel({tile:'cube',radius:1,mirrors:false});
const cubeLearned=(await collect(learnMarking(cube))).marking;
cubeLearned.fields=cube.orientations.map(o=>o.cells.flatMap(c=>[0,1].map(component=>({pos:c.pos,component,value:0}))));
const zero=(await collect(reuseMarking(cube,{domain:markingSystem(cube),marking:cubeLearned}))).marking;
assert.equal(zero.values,2*zero.points);assert.equal(zero.componentCount,2);
console.log('PASS overlapping zero-valued components survive replay with distinct point/value counts.');
