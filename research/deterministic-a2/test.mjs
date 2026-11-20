import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {builtIn,search,windows} from './run.mjs';
import {tileModel} from './model.mjs';
import {verify} from './verify.mjs';

const tile=JSON.parse(readFileSync(new URL('two-weights.json',import.meta.url)));
const opts={radius:1,through:2,extent:0,proofNodes:0,proposals:32,seed:6};
const results=[...windows(tile,opts)];
assert.deepEqual(results,[...windows(tile,opts)]);
assert.deepEqual(results,[...windows({...tile,points:[...tile.points].reverse()},opts)]);
assert.equal(results.length,2);
for (const r of results) {
  assert.equal(r.status,'covered');
  assert.ok(verify(tile,r)>0);
}
assert.ok(results[0].revisions.length>0);
assert.deepEqual(results[0].revisions[0].pair,['0@0,0,0','4@-1,1,0']);
assert.deepEqual(results[0].marking,[['0,0,0',0,1],['0,0,0',2,-1]]);
assert.deepEqual(results[1].marking,results[0].marking);
const raw=search(tile,{...opts,proposals:0});
assert.equal(raw.status,'covered'); assert.deepEqual(raw.marking,[]); verify(tile,raw);
const cutoff=search(tile,{...opts,nodes:0});
assert.equal(cutoff.status,'unknown'); assert.deepEqual(cutoff.revisions,[]);
const impossible=search({capacity:3,points:[[0,0,2]]},{nodes:null});
assert.equal(impossible.status,'exhausted'); assert.deepEqual(impossible.revisions,[]);
const exact=search({capacity:'9007199254740993',points:[['9007199254740994',0,'9007199254740993']]},{radius:1});
assert.equal(exact.status,'covered'); assert.equal(exact.placements.length,7);
const domino=tileModel({capacity:1,points:[[0,0,1],[1,0,1]]});
assert.equal(domino.forms.length,3);
assert.throws(()=>verify(tile,{...raw,marking:[['0,0,0',0,1]]}),/symmetry/);
// Both endpoints are assigned a full invariant orbit. All translates of this
// orientation give a valid periodic tiling, and collide at the opposite ends.
const unsafe={...raw,marking:[['0,0,0',0,1],['0,0,0',2,-1],['1,0,-1',0,-1],['1,0,-1',2,1]]};
assert.throws(()=>verify(tile,unsafe),/unproved exclusion/);
const hat=builtIn('hat');
const hatResult=search(hat,{radius:1,seed:1,nodes:60,extent:0,proofNodes:0,proposals:20});
assert.equal(hatResult.status,'covered'); assert.ok(hatResult.revisions.length>0);
const hatPairs=verify(hat,hatResult);
console.log(JSON.stringify({weighted:results.map(r=>({radius:r.config.radius,nodes:r.nodes,tiles:r.placements.length,
  revisions:r.revisions.length})),firstRevision:results[0].revisions[0],hat:{nodes:hatResult.nodes,
  tiles:hatResult.placements.length,revisions:hatResult.revisions.length,assignments:hatResult.marking.length,
  verifiedRelativePairs:hatPairs}},null,2));
