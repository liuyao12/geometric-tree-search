// node run.mjs collect|compare|geometry [75|150]; writes JSON lines to stdout.
// node run.mjs replay collected.jsonl replays every unmarked dead end.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {createCoronaLearner} from '../../assets/tile-corona-learning.js';
import {FixedA2Marking, NoA2Marking, makeHexBoundary, solveA2Tiling} from '../../assets/a2-tiling-engine.js';

const action = process.argv[2];
globalThis.requestAnimationFrame = cb => setImmediate(cb);
const pose = p => [p.tile, p.orientation.index, p.translation[0], p.translation[1]];
if (action === 'geometry') {
  const geometry = {};
  for (const id of ['hat', 'mixed']) {
    geometry[id] = createCoronaLearner(id).orientations.map(o => ({
      tile:o.tile, index:o.index, symmetry:o.symmetry,
      sites:[...o.occupancy.values()].map(e => [...e.point.slice(0,2), e.weight])
    }));
  }
  console.log(JSON.stringify(geometry));
} else if (action === 'replay') {
  const {createFailureMarking} = await import('../../assets/failure-rank3-marking.js');
  const counts = {};
  for (const line of readFileSync(process.argv[3],'utf8').trim().split('\n')) {
    const {setId,seed,mode,failures} = JSON.parse(line);
    assert.equal(mode,'none');
    const catalog = createCoronaLearner(setId), marking = createFailureMarking(setId);
    const stats = counts[setId] ??= {deadEnds:0,rejected:0,beforeLastPlacement:0};
    for (const {point,patch} of failures) {
      marking.reset();
      const owners = new Map();
      stats.deadEnds++;
      for (const [j,[tile,orientation,x,y]] of patch.entries()) {
        const p = catalog.materialize({tile,orientation,translation:[x,y,-x-y]});
        if (!marking.compatible(p)) {
          const [key,value] = [...marking.entries(p)].find(([k,v]) => owners.has(k) && owners.get(k).value !== v);
          const previous = owners.get(key);
          stats.rejected++;
          if (j+1 < patch.length) stats.beforeLastPlacement++;
          stats.example ??= {seed,deadPoint:point,deadEndSize:patch.length,
            moves:[previous.step,j+1],poses:[patch[previous.step-1],patch[j]],key,values:[previous.value,value]};
          break;
        }
        marking.push(p);
        for (const [key,value] of marking.entries(p)) owners.set(key,{value,step:j+1});
      }
    }
  }
  console.log(JSON.stringify(counts));
} else {
  if (!['collect','compare'].includes(action)) throw new Error('Unknown run type');
  const collecting = action === 'collect';
  const target = collecting ? 65 : Number(process.argv[3] ?? 75);
  if (!collecting && ![75,150].includes(target)) throw new Error('Use target 75 or 150');
  const budget = collecting ? 180 : 6 * target;
  const cases = [['hat','hat'], ['mixed','hat'], ['mixed','turtle']];
  if (!collecting) cases.push(['turtle','turtle']);
  for (const [setId, tile] of cases) {
    const catalog = createCoronaLearner(setId);
    const root = catalog.materialize(catalog.roots.find(p => p.tile === tile));
    for (const seed of collecting ? [17,39,73,101] : [227,349,503,641,809,997]) {
      for (const mode of collecting ? ['none'] : setId === 'turtle' ? ['constant'] : ['none','encoded']) {
        const marking = mode === 'none' ? new NoA2Marking() : mode === 'constant'
          ? new FixedA2Marking(9, {tiles:['turtle'],rank:3})
          : (await import('../../assets/failure-rank3-marking.js')).createFailureMarking(setId,9);
        const failures = [], unique = new Set(), trace = createHash('sha256');
        const answer = await solveA2Tiling({...catalog.config, initialPlacements:[root], fixedInitialPlacements:true,
          completePointGrowth:true, requireEdgeSharing:true, branchPolicy:'oldest-frontier', maximize:true,
          boundary:makeHexBoundary(2), targetPlacements:target, nodeLimit:budget, randomSeed:seed, marking,
          onEvent(e) {
            if (e.type === 'placement') trace.update('+' + e.placements.at(-1).id + '\n');
            if (e.type === 'backtrack') trace.update('-' + e.removed.id + '\n');
            if (e.type !== 'fail') return;
            const patch = e.placements.map(pose);
            const key = JSON.stringify([patch,e.choice]);
            if (!unique.has(key)) failures.push({patch, point:e.choice});
            unique.add(key);
          }});
        console.log(JSON.stringify({setId,tile,seed,mode,target,budget,result:answer.result,achieved:answer.placements.length,
          nodes:answer.stats.nodes,backtracks:answer.stats.backtracks,trace:trace.digest('hex'),
          ...(collecting ? {failures} : {deadEnds:failures.length})}));
      }
    }
  }
}
