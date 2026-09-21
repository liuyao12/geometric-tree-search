import assert from 'node:assert/strict';
import {selectMask,learnMaskedMarking} from './lib/masked-point-encoder.mjs';
import {OnlineMarking,pointSymmetries,pairCompatible} from '../apps/3d-lattice-tiler/marking-learning.js';
const graph=selectMask(3,[[0,2],[1]],[[0,1],[1,2]],[[[0,2]]]);
assert.equal(graph.blocked,1);assert.deepEqual([...graph.active],[1,0,1]);assert.notEqual(graph.find(0),graph.find(2));
assert.throws(()=>selectMask(3,[[0],[2]],[],[]),/cover/);
assert.throws(()=>selectMask(3,[[0,1],[1,2]],[],[]),/partition/);
// Synthetic classification constraints, not oracle-generated geometric labels:
// the positive contact passes through the middle slot; the negative compares
// the endpoints directly. Making the middle value free must break that path.
const model={capacity:3,allowReflections:false,orientations:[{type:0,index:0,cells:[0,1,2].map(x=>({pos:[x,0,0],weight:1}))}]};
const transforms=pointSymmetries(model),root={oi:0,translation:[0,0,0]},pair=x=>[root,{oi:0,translation:[x,0,0]}];
const rows=[{pair:pair(1),status:'valid'},{pair:pair(2),status:'invalid'}];
const baseline=new OnlineMarking(model,transforms,{extent:0});let old;for(const row of rows)old=baseline.add(row);assert.equal(old.negativeBlocked,0);
const learned=learnMaskedMarking(model,rows,{transforms,extent:0});
assert.equal(learned.positivePassed,1);assert.equal(learned.negativeBlocked,1);assert.equal(learned.points,2);
assert.ok(pairCompatible(learned.fields,pair(1)));assert.ok(!pairCompatible(learned.fields,pair(2)));
assert.ok(!learned.fields[0].some(m=>m.pos[0]===1));
const contradictory=learnMaskedMarking(model,[rows[0],{pair:pair(1),status:'invalid'}],{transforms,extent:0});
assert.equal(contradictory.positivePassed,1);assert.equal(contradictory.negativeBlocked,0);
console.log('PASS conditional free values split equality paths, preserve every positive and symmetry, and do not invent a separator for contradictory labels.');
