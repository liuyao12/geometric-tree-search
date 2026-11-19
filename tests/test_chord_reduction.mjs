import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {FixedA2Marking, a2Add, a2Sub, a2InverseTransform} from '../assets/a2-tiling-engine.js';
import {createCoronaLearner} from '../assets/tile-corona-learning.js';
import {CHORD_MAX_EXTENT, DeepChordMarking} from '../assets/deep-chord-marking.js';

const certificates = JSON.parse(readFileSync(new URL('chord-deletion-witnesses.json',import.meta.url)));
const oldDigests = {
  hat:'a9d3407477ef78dd81ce4c437bd8f146c6aff43f45330afdf4ff948ee2a1f2bd',
  mixed:'75916625f0e505ad48c75f9823e4267f6014cfbbaf42f5ec9de33270e47c6991'
};

function sharedEdges(loop) {
  const result = new Set();
  for (const [i,p] of loop.entries()) {
    const q = loop[(i+1)%loop.length], delta = a2Sub(q,p);
    const gcd = (a,b) => b ? gcd(b,a%b) : a;
    const steps = delta.map(Math.abs).reduce(gcd), step = delta.map(v=>v/steps);
    let from = p;
    for (let k=0;k<steps;k++) {
      const to = a2Add(from,step);
      result.add([String(from),String(to)].sort().join('|'));
      from = to;
    }
  }
  return result;
}

function chordLabel(p,key) {
  const [xyz,c] = key.split('|');
  const sym = p.orientation.symmetry;
  const local = a2InverseTransform(a2Sub(xyz.split(',').map(Number),p.translation),sym);
  return [p.tile,local,sym.permutation[Number(c.slice(5))]].join(':');
}

for (const [setId,patches] of Object.entries(certificates)) {
  const catalog = createCoronaLearner(setId);
  const pose = ([tile,orientation,x,y])=>catalog.materialize({tile,orientation,translation:[x,y,-x-y]});
  const rule = new DeepChordMarking(setId), core = new DeepChordMarking(setId,0);
  const oldScalar = new FixedA2Marking(0,{tiles:catalog.config.tiles,rank:1});
  const labels = new Set(), needed = new Set(), digestRows = [];
  for (const o of catalog.orientations) {
    const p = pose([o.tile,o.index,0,0]);
    for (const [key,v] of rule.entries(p)) {
      const [xyz,c] = key.split('|'), [x,y] = xyz.split(',');
      if (c!=='0') digestRows.push([p.tile,o.index,x,y,c,v].join(':'));
      if (c.startsWith('chord')) labels.add(chordLabel(p,key));
      if (c==='0') assert.equal(oldScalar.entries(p).get(key),v);
    }
    // Therefore disjoint positive supports cannot lose any scalar conflict.
    for (const key of oldScalar.entries(p).keys()) assert.ok(o.occupancy.has(key.split('|')[0]));
  }
  assert.equal(createHash('sha256').update(digestRows.sort().join('\n')).digest('hex'),oldDigests[setId]);

  // Exhaust every nonoverlapping relative placement with intersecting positive
  // support. The previous rule is this same chord/corner table plus all original
  // scalar samples. Every omitted scalar disagreement already fails at extent 0.
  // Larger extents only add shared chord constraints.
  let pairs=0;
  for (const s of catalog.config.tiles) {
    const a = pose([s,0,0,0]);
    oldScalar.reset([a]); core.reset([a]);
    for (const o of catalog.orientations) {
      const offsets=new Set();
      for (const u of a.orientation.occupancy.values()) for (const v of o.occupancy.values()) {
        offsets.add(String(a2Sub(u.point,v.point)));
      }
      for (const coords of offsets) {
        const [x,y]=coords.split(',').map(Number);
        const b=pose([o.tile,o.index,x,y]);
        if ([...o.occupancy.values()].some(v=>(a.orientation.occupancy.get(String(a2Add(v.point,b.translation)))?.weight??0)+v.weight>12)) continue;
        pairs++;
        if (!oldScalar.compatible(b,[],false)) assert.equal(core.compatible(b,[],false),false);
      }
    }
  }
  assert.equal(pairs,setId==='hat'?320:624);

  // Each certificate is an edge-connected chain. All capacities are legal.
  // Replay it and identify every canonical chord value whose single deletion
  // removes *all* conflicts of the chain, in all copies of the prototile.
  for (const specs of patches) {
    const sums = new Map(), owners = new Map();
    let priorEdges = null, blockers = null;
    for (const spec of specs) {
      const p=pose(spec), edges=sharedEdges(p.loop);
      if (priorEdges) assert.ok([...edges].some(e=>priorEdges.has(e)));
      priorEdges=edges;
      for (const {point,weight} of p.orientation.occupancy.values()) {
        const key=String(a2Add(point,p.translation)), total=(sums.get(key)??0)+weight;
        assert.ok(total<=12); sums.set(key,total);
      }
      for (const [key,value] of rule.entries(p)) {
        const previous=owners.get(key)??[];
        for (const [q,other] of previous) if (value!==other) {
          assert.ok(key.includes('|chord'));
          const ends=new Set([chordLabel(p,key),chordLabel(q,key)]);
          blockers=blockers===null?ends:new Set([...blockers].filter(k=>ends.has(k)));
        }
        previous.push([p,value]); owners.set(key,previous);
      }
    }
    assert.ok(blockers?.size);
    for (const k of blockers) needed.add(k);
  }
  assert.deepEqual(needed,labels);

  const example = setId==='mixed'
    ? [['hat',6,-2,-2],['turtle',0,0,0],['turtle',0,2,2],['turtle',4,-6,9],['turtle',9,-7,5],['turtle',9,-5,1],['turtle',9,5,-1],['turtle',10,2,-7]]
    : [['hat',0,0,0],['hat',4,4,7],['hat',10,-6,3]];
  for (let extent=0;extent<=CHORD_MAX_EXTENT;extent++) {
    const two=new DeepChordMarking(setId,extent,{twoMarks:true});
    const expectedCount = extent >= (setId==='mixed'?6:3) ? 2 : 1;
    assert.equal(two.stats().supportSites,expectedCount);
    for (const o of catalog.orientations) {
      const p=pose([o.tile,o.index,2,5]);
      for (const [k,v] of two.entries(p)) {
        assert.ok(k.includes('|chord')); assert.equal(rule.entries(p).get(k),v);
      }
    }
    assert.equal(example.map(pose).every(p=>{
      if (!two.compatible(p)) return false;
      two.push(p); return true;
    }),expectedCount<2);
  }
  console.log(setId,pairs,'relative placements checked;',needed.size,'indispensable chords on',patches.length,'connected patches. Two-mark example verified.');
}
