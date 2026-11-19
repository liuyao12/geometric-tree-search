import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {a2Add, a2Transform, makeHexBoundary, solveA2Tiling} from '../assets/a2-tiling-engine.js';
import {createCoronaLearner, parity} from '../assets/tile-corona-learning.js';
import {createAlternatingMarking} from '../assets/hat-rank3-marking.js';
import {CHORD_MAX_EXTENT, DeepChordMarking} from '../assets/deep-chord-marking.js';

const mixed = createCoronaLearner('mixed');
const economical = process.argv.includes('--economical');
const markingFor = (setId,extent) => new DeepChordMarking(setId,extent,{economical});
const pose = (catalog, [tile, orientation, x, y]) =>
  catalog.materialize({tile, orientation, translation:[x,y,-x-y]});
const snapshot = {};
for (const setId of ['hat','mixed']) {
  const catalog = createCoronaLearner(setId);
  const rules = Array.from({length:CHORD_MAX_EXTENT+1}, (_,e) => markingFor(setId,e));
  if (economical) assert.equal(rules.at(-1).stats().supportSites,setId==='hat'?26:52);
  snapshot[setId] = [];
  for (const orientation of catalog.orientations) {
    const {tile, index, symmetry} = orientation;
    const root = pose(catalog,[tile,0,0,0]), atOrigin = pose(catalog,[tile,index,0,0]);
    const shifted = pose(catalog,[tile,index,2,5]);
    const xyz = key => key.split(',').map(Number);
    const rows = [...rules.at(-1).entries(atOrigin)].map(([key,value]) => {
      const [q,c] = key.split('|');
      return [...xyz(q).slice(0,2),c,value];
    });
    snapshot[setId].push({tile,index,symmetry,loop:atOrigin.loop.map(p=>p.slice(0,2)),
      sites:[...orientation.occupancy.values()].map(e=>[...e.point.slice(0,2),e.weight]),marks:rows});
    // Check every pose and every setting against the maximal canonical table.
    // Shortening the extent can only remove a prediction.
    const sites = [...root.orientation.occupancy.values()].map(e=>e.point);
    for (const [extent,rule] of rules.entries()) {
      const expected = new Map();
      for (const [key,sign] of rules.at(-1).entries(root)) {
        const [q,channel] = key.split('|'), point = xyz(q);
        const distance = Math.min(...sites.map(s=>Math.max(...s.map((v,i)=>Math.abs(v-point[i])))));
        if (channel.startsWith('chord') && distance > extent) continue;
        const c = channel.startsWith('chord') ? 'chord'+symmetry.permutation.indexOf(Number(channel.slice(5))) : channel;
        const world = a2Add(a2Transform(point,symmetry),shifted.translation);
        expected.set(world+'|'+c,channel==='corner'?sign*parity(symmetry.permutation):sign);
      }
      assert.deepEqual(rule.entries(shifted),expected);
    }
  }
  for (const rule of rules) {
    const count = catalog.config.tiles.reduce((n,tile) =>
      n + rule.entries(pose(catalog,[tile,0,0,0])).size, 0);
    assert.equal(rule.stats().supportSites,count);
  }
}
if (process.argv.includes('--geometry')) {
  console.log(JSON.stringify(snapshot));
} else {
  globalThis.requestAnimationFrame = cb => setImmediate(cb);
  const patch = [
    ['hat',6,-2,-2],['turtle',0,0,0],['turtle',0,2,2],['turtle',4,-6,9],
    ['turtle',9,-7,5],['turtle',9,-5,1],['turtle',9,5,-1],['turtle',10,2,-7]
  ].map(spec => pose(mixed,spec));
  const key = '0,2,-2|chord0', [hat,,turtle] = patch;
  const deep = markingFor('mixed');
  assert.equal(deep.entries(hat).get(key),-1);
  assert.equal(deep.entries(turtle).get(key),1);
  assert.equal(markingFor('mixed',5).entries(hat).has(key),false);
  assert.equal(markingFor('mixed',6).entries(hat).get(key),-1);
  for (let extent=0; extent<=CHORD_MAX_EXTENT; extent++) {
    const rule = markingFor('mixed',extent);
    const accepts = patch.every(p=>{
      if (!rule.compatible(p)) return false;
      rule.push(p);
      return true;
    });
    assert.equal(accepts,extent < 6);
  }
  for (const [a,b] of [[hat,turtle],[turtle,hat]]) {
    deep.reset([a]); assert.equal(deep.compatible(b),false);
    deep.pop(a); assert.equal(deep.compatible(b),true);
  }
  const opts = {fixedInitialPlacements:true, completePointGrowth:true, requireEdgeSharing:true,
    branchPolicy:'oldest-frontier', maximize:true, boundary:makeHexBoundary(2), nodeLimit:6000};
  const replay = rule => solveA2Tiling({...mixed.config,...opts,marking:rule,initialPlacements:patch,targetPlacements:8});
  const prior = createAlternatingMarking(mixed.config.tiles,0);
  assert.equal((await replay(prior)).result,'yes');
  await assert.rejects(replay(deep),/Initial placements disagree on m-values/);

  // Recorded traces from the research kernels, including rollback from a Turtle start.
  const cases = economical ? [
    ['hat','hat','a316a67bc56e01dfc14438269743e8fc47dc45af7defb353d716f96fd22ad667'],
    ['mixed','hat','4f67b0f3f2b11b91a682812f6d25f4e2d4b1cc270ff551b47ba1a21538adbea9'],
    ['mixed','turtle','33e0a50babd2a4c5f5ca46f89b02bbee08af938c3c7b9ac2a2ba51142b7d3806']
  ] : [
    ['hat','hat','2786d10bdf20d049dd3014ae5bd86679d5fcd13a25cea29a10ea25200f81b99b'],
    ['mixed','hat','f2a8f0947a52e9fa80d2244cbdf6e2eff077c4b33ac820a0625d66ca9ae72aea'],
    ['mixed','turtle','aca290849dd634288d11bcba767fbe2cb6c22f8523f6cb6ae679b1d2f43bc3d8']
  ];
  for (const [setId,tile,expected] of cases) {
    const catalog = createCoronaLearner(setId), trace = createHash('sha256');
    const answer = await solveA2Tiling({...catalog.config,...opts,marking:markingFor(setId),
      initialPlacements:[pose(catalog,[tile,0,0,0])], targetPlacements:75, randomSeed:economical?3956800648:3496741806,
      auditFrontierGraph:true, onEvent:e=>{
        if (e.type==='placement') trace.update('+'+e.placements.at(-1).id+'\n');
        if (e.type==='backtrack') trace.update('-'+e.removed.id+'\n');
      }});
    assert.equal(answer.result,'yes');
    assert.equal(answer.placements.length,75);
    assert.equal(trace.digest('hex'),expected);
  }
  console.log('Eight-tile obstruction rejected. Three 75-tile searches reproduced the research traces. All rotations, translations tested and extents passed.');
}
