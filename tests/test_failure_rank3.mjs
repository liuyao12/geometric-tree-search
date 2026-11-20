import assert from 'node:assert/strict';
import {A2_TILE_LOOPS, a2Add, a2Transform, tileOrientations} from '../assets/a2-tiling-engine.js';
import {createCoronaLearner, parity} from '../assets/tile-corona-learning.js';
import {createFailureMarking, failureExtent} from '../assets/failure-rank3-marking.js';

const examples = {
  hat:[['hat',0,0,0],['hat',4,4,7],['hat',10,-6,3]],
  mixed:[['hat',6,-2,-2],['turtle',0,0,0],['turtle',0,2,2],['turtle',4,-6,9],
    ['turtle',9,-7,5],['turtle',9,-5,1],['turtle',9,5,-1],['turtle',10,2,-7]]
};
const snapshot = {}, witnesses = {};
for (const setId of ['hat','mixed']) {
  const catalog = createCoronaLearner(setId), rules = Array.from({length:10}, (_,i) => createFailureMarking(setId,i));
  const full = rules.at(-1);
  snapshot[setId] = [];
  for (const tile of catalog.config.tiles) {
    const orientations = tileOrientations(tile,A2_TILE_LOOPS[tile]);
    const canonical = {orientation:orientations[0], tile, translation:[0,0,0]};
    const root = [...full.entries(canonical)].map(([k,value]) => {
      const [xyz,channel] = k.split('|');
      assert.ok(/^[012]$/.test(channel));
      return {point:xyz.split(',').map(Number), component:Number(channel), value};
    });
    for (const orientation of orientations) {
      const {symmetry} = orientation, shift = [5,-7,2], p = {tile,orientation,translation:shift};
      for (const [extent,rule] of rules.entries()) {
        const expected = new Map();
        for (const {point,component,value} of root) {
          const distance = Math.min(...[...canonical.orientation.occupancy.values()]
            .map(e => Math.max(...e.point.map((v,i) => Math.abs(v-point[i])))));
          if (distance > extent) continue;
          const key = a2Add(a2Transform(point,symmetry),shift) + '|' + symmetry.permutation.indexOf(component);
          expected.set(key,value*parity(symmetry.permutation));
        }
        assert.deepEqual(rule.entries(p),expected);
      }
      if (!catalog.config.allowReflections && parity(symmetry.permutation)<0) continue;
      const marks = [...full.entries({tile,orientation,translation:[0,0,0]})].map(([key,v]) => {
        const [coord,axis] = key.split('|');
        return [...coord.split(',').slice(0,2).map(Number),Number(axis),v];
      });
      snapshot[setId].push({tile,index:orientation.index,symmetry,marks,
        sites:[...orientation.occupancy.values()].map(e => [...e.point.slice(0,2),e.weight])});
    }
    assert.deepEqual(rules[failureExtent(setId)].entries(canonical),full.entries(canonical));
  }
  const placements = examples[setId].map(([tile,orientation,x,y]) =>
    catalog.materialize({tile,orientation,translation:[x,y,-x-y]}));
  catalog.verifyPatch(placements); // All ordinary point capacities fit.
  const first = placements.findIndex((p,i) => {
    if (full.compatible(p)) { full.push(p); return false; }
    for (const [key,value] of full.entries(p)) for (const [j,q] of placements.slice(0,i).entries()) {
      const prev = full.entries(q).get(key);
      if (prev !== undefined && prev !== value) {
        witnesses[setId] = {tiles:[j+1,i+1], key, values:[prev,value]};
        full.reset([q]); assert.equal(full.compatible(p),false);
        full.pop(q); assert.equal(full.compatible(p),true);
        return true;
      }
    }
    assert.fail('Rejection without an unequal assigned overlap');
  });
  assert.ok(first>0);
}
console.log(JSON.stringify(process.argv.includes('--geometry') ? snapshot : witnesses));
