import assert from 'node:assert/strict';
import {SparseA2Marking,tileOrientations,A2_TILE_LOOPS} from '../assets/a2-tiling-engine.js';
const placement=tile=>({id:tile,tile,orientation:tileOrientations(tile,A2_TILE_LOOPS[tile])[0],translation:[0,0,0]});
const turtle=placement('turtle'),hat=placement('hat');
// Synthetic values isolate omission semantics: zero is assigned, * is absent.
const support=[{tile:'turtle',point:[0,0,0],component:0,value:0},{tile:'turtle',point:[0,0,0],component:1,value:2},{tile:'hat',point:[0,0,0],component:0,value:1},{tile:'hat',point:[0,0,0],component:1,value:2}];
const dense=new SparseA2Marking(support);dense.reset([turtle]);assert.equal(dense.compatible(hat),false);
const sparse=new SparseA2Marking(support.filter(e=>!(e.tile==='turtle'&&e.component===0)));sparse.reset([turtle]);assert.equal(sparse.compatible(hat),true);
assert.deepEqual([...sparse.entries(turtle)], [['0,0,0|1',2]]);
const before=[...sparse.contacts];sparse.push(hat);sparse.pop(hat);assert.deepEqual([...sparse.contacts],before,'Rollback must preserve assigned components and omit free ones');
const conflict=new SparseA2Marking(support.filter(e=>!(e.tile==='turtle'&&e.component===0)).map(e=>e.tile==='hat'&&e.component===1?{...e,value:-2}:e));conflict.reset([turtle]);assert.equal(conflict.compatible(hat),false,'Retained component still constrains the neighbor');
console.log('PASS individual * differs from assigned zero; neighboring components still constrain; contact rollback exact.');
