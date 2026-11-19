import assert from 'node:assert/strict';
import {A2_TILE_LOOPS, FixedA2Marking, a2Add, a2Sub, a2InverseTransform, tileOrientations} from '../assets/a2-tiling-engine.js';
import {TILE_SETS, createCoronaLearner, parity} from '../assets/tile-corona-learning.js';
import {HAT_RANK3_MAX_EXTENT, createAlternatingMarking, hatKagomeValues} from '../assets/hat-rank3-marking.js';
import {learningPointFilter} from '../assets/learning-lattice.js';

// Certify complete unmarked mixed tilings. A star consists of all tiles covering
// one lattice point. Its weights sum to 12 there and cannot exceed 12 elsewhere.
const {tiles, allowReflections} = TILE_SETS.mixed;
const orientations = tiles.flatMap(tile => tileOrientations(tile, A2_TILE_LOOPS[tile]))
  .filter(o => allowReflections || parity(o.symmetry.permutation) > 0);
const coords = key => key.split(',').map(Number);
const placementKey = (o,t) => `${o.tile}:${o.index}:${t}`;
const periodCell = [];
for (let x = 0; x < 6; x++) for (let y = 0; y < 6; y++) periodCell.push([x,y,-x-y]);

function fieldAt(placement, point) {
  const {symmetry} = placement.orientation;
  const local = a2InverseTransform(a2Sub(point,placement.translation),symmetry);
  const values = hatKagomeValues(local) ?? [0,0,0];
  return symmetry.permutation.map(c => parity(symmetry.permutation) * values[c] || 0);
}

// Both parities in hatKagomeValues repeat modulo six in each axial coordinate.
// Check the implementation on every orientation and translation class, including
// all assigned zero and exterior values. Unassigned components impose no test.
function checkMarkings(pointFilter) {
  const translations = periodCell.filter(p => !pointFilter || pointFilter(p));
  for (let extent = 0; extent <= HAT_RANK3_MAX_EXTENT; extent++) {
    const scalar = new FixedA2Marking(extent,{tiles,rank:1,pointFilter});
    const signed = createAlternatingMarking(tiles,extent,{pointFilter});
    for (const orientation of orientations) for (const translation of translations) {
      const placement = {tile:orientation.tile,orientation,translation};
      for (const rule of [scalar,signed]) for (const [key,value] of rule.entries(placement)) {
        const [point,c] = key.split('|');
        const vector = fieldAt(placement,coords(point));
        if (rule === scalar) {
          assert.equal(c,'0');
          assert.equal(value,Number(vector.some(v => v !== 0)));
        } else {
          assert.equal(value,vector[Number(c)]);
        }
      }
    }
  }
}

function addWeights(sums, weights, shift) {
  for (const [point,weight] of weights) {
    const key = a2Add(point,shift).join(',');
    const total = (sums.get(key) ?? 0) + weight;
    if (total > 12) return false;
    sums.set(key,total);
  }
  return true;
}

function certify(lattice, neighborSteps, expectedCounts) {
  const pointFilter = learningPointFilter(lattice);
  checkMarkings(pointFilter);
  const candidates = [], atOrigin = new Map();
  for (const orientation of orientations) {
    const sites = [...orientation.occupancy.values()].filter(e => !pointFilter || pointFilter(e.point));
    for (const anchor of sites) {
      const translation = anchor.point.map(v => -v);
      const placement = {orientation,translation};
      const candidate = {
        ...placement, weight:anchor.weight,
        weights:sites.map(e => [a2Add(e.point,translation),e.weight]),
        phase:periodCell.flatMap(p => fieldAt(placement,p)).join(',')
      };
      candidates.push(candidate);
      atOrigin.set(placementKey(orientation,translation),candidate);
    }
  }
  const origin = [0,0,0], stars = [];
  function fill(start, remaining, members, sums) {
    if (remaining === 0) {
      stars.push({members,sums});
      return;
    }
    for (let i = start; i < candidates.length; i++) {
      const c = candidates[i];
      if (c.weight > remaining) continue;
      const next = new Map(sums);
      if (addWeights(next,c.weights,origin)) fill(i+1,remaining-c.weight,[...members,c],next);
    }
  }
  fill(0,12,[],new Map());

  // Every point occupied by a tile of the star must itself have a complete star.
  // Include already placed tiles exactly once and test capacities on the union.
  // A star in a complete unmarked tiling always has these neighbors.
  const byMember = new Map(candidates.map(c => [c,[]]));
  for (const star of stars) for (const c of star.members) byMember.get(c).push(star);
  function canCompleteAt(star, q) {
    const required = star.members.map(c => atOrigin.get(
      placementKey(c.orientation,a2Sub(c.translation,q)))).filter(Boolean);
    assert.ok(required.length);
    return byMember.get(required[0]).some(neighbor => {
      if (!required.every(c => neighbor.members.includes(c))) return false;
      const sums = new Map(star.sums);
      return neighbor.members.every(c => required.includes(c) || addWeights(sums,c.weights,q));
    });
  }
  const viable = stars.filter(s => [...s.sums.keys()].every(q => q === '0,0,0' || canCompleteAt(s,coords(q))));
  assert.deepEqual([stars.length,viable.length],expectedCounts);
  for (const s of viable) for (const c of s.members) assert.equal(c.phase,s.members[0].phase);

  // Adjacent stars intersect in positive support. In a complete tiling the star
  // at that intersection has one phase, which makes the phases of the neighboring
  // stars equal. The steps below and their negatives generate the tested lattice.
  for (const step of neighborSteps) {
    const translated = viable.map(s => [...s.sums.keys()].map(k => a2Add(coords(k),step).join(',')));
    for (const s of viable) {
      if (s.sums.has(step.join(','))) continue;
      for (const points of translated) assert.ok(points.some(k => s.sums.has(k)));
    }
  }
  console.log(`${lattice}: ${stars.length} unmarked stars, ${viable.length} pass neighboring point checks; one common field for both markings at extents 0–${HAT_RANK3_MAX_EXTENT}.`);
}
certify('A2',[[1,-1,0],[1,0,-1],[0,1,-1]],[841,550]);
certify('turtle-sublattice',[[1,1,-2],[1,-2,1],[-2,1,1]],[1547,320]);

// Optional empirical cross-check. Independently classify each touching pair by
// unmarked one-corona search, then replay it against both production rules.
if (process.argv.includes('--corona')) {
  globalThis.requestAnimationFrame = cb => setImmediate(cb);
  const learner = createCoronaLearner('mixed');
  const pairs = [];
  for (const [i,pair] of learner.connections().entries()) {
    const {status} = await learner.examine({...pair,budget:5000,seed:90210 ^ Math.imul(i+1,1987)});
    assert.notEqual(status,'unresolved');
    pairs.push({root:learner.materialize(pair.root),other:learner.materialize(pair.attachment),status});
  }
  const valid = pairs.filter(pair => pair.status === 'valid').length;
  assert.deepEqual([pairs.length,valid],[624,70]);
  for (let extent = 0; extent <= HAT_RANK3_MAX_EXTENT; extent++) {
    const rules = [new FixedA2Marking(extent,{tiles,rank:1}),createAlternatingMarking(tiles,extent)];
    const rejected = rules.map(rule => {
      let count = 0;
      for (const {root,other,status} of pairs) {
        rule.reset([root]);
        if (!rule.compatible(other,[],false)) {
          assert.equal(status,'invalid');
          count++;
        }
      }
      return count;
    });
    console.log(`Extent ${extent}: both accepted all ${valid} viable pairs; rejected ${rejected.join(' and ')} of ${pairs.length-valid} impossible pairs (rank 1 and rank 3).`);
  }
}
