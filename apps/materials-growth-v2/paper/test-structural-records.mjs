import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {samplePatch} from '../samples.mjs';
import {scoreStructure} from './structural-metrics.mjs';
const data=JSON.parse(readFileSync(new URL('structural-results.json',import.meta.url),'utf8'));
assert.equal(data.results.length,8);
for(const [path,hash] of Object.entries(data.sources))assert.equal(createHash('sha256').update(readFileSync(new URL('../'+path,import.meta.url))).digest('hex'),hash,path);
let count=0;
for(const row of data.results){
  assert.equal(row.status,'finished'); assert.equal(row.checkpoints.length,3);
  const reference=samplePatch(row.id).evaluation;
  for(const point of row.checkpoints){
    assert(point.legal);if(row.observedOnly)assert(point.overlapLegal);
    const replay=scoreStructure(reference,point.atoms,{poses:[point.metrics.alignment],epsilon:row.epsilon});
    assert.deepEqual(replay,point.metrics);count++;
  }
}
assert.equal(count,24);
console.log('PASS: 8 source-pinned runs, all 24 coordinate-based metric replays, terminal and legality records.');
