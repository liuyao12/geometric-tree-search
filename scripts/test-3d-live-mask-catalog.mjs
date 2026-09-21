// Synthesis regression against recorded local labels; this does not re-prove
// the oracle labels. No learned assignments or positive witnesses are bundled.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {POLYCUBE_GCTS_CANDIDATES} from '../assets/polycube-census-candidates.js';
import {prepareVoxelPointModel} from '../apps/3d-lattice-tiler/voxel-point-model.js';
import {OnlineMarking,pairCompatible} from '../apps/3d-lattice-tiler/marking-learning.js';
import {pairOrbits} from './lib/3d-pair-orbits.mjs';
import {auditMarkingContacts} from './lib/audit-marking-contacts.mjs';
const recorded=JSON.parse(readFileSync(new URL('../data/3d-p9-48258-complete-2026-09-21.json',import.meta.url)));
const tile=POLYCUBE_GCTS_CANDIDATES.find(t=>t.id==='p9-48258');
const model=prepareVoxelPointModel(tile.voxels),orbits=pairOrbits(model),rows=[];
assert.equal(recorded.groups.length,orbits.groups.length);
for(const [i,g] of orbits.groups.entries()){
 const r=recorded.groups[i];assert.deepEqual(r.pair,g.pair);assert.equal(r.members,g.members.length);
 for(const m of g.members)rows[m.index]={pair:m.pair,status:r.status};
}
const trainer=new OnlineMarking(model,orbits.transforms);
for(const row of rows){const s=trainer.add(row);assert.equal(s.positivePassed,s.counts.valid);}
const marking=trainer.snapshot({maxEvaluations:2048});
assert.deepEqual(marking.counts,{valid:622,invalid:64,unresolved:0});
assert.equal(marking.negativeBlocked,64);assert.equal(marking.points,60);assert.equal(marking.labelCount,6);
for(const r of rows)assert.equal(pairCompatible(marking.fields,r.pair),r.status==='valid');
const audit=auditMarkingContacts(model,marking.fields,rows,orbits.transforms);
assert.ok(audit.noExtraPairExclusions);assert.equal(audit.counts.rejectedWithoutNegativeLabel,0);
console.log('PASS live synthesis: 622 positives pass, 64 negatives blocked, 60 assigned scalar values; exhaustive additional marking-contact audit.');
