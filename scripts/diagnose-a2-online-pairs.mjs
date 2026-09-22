#!/usr/bin/env node
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {a2Transform,a2InverseTransform} from '../assets/a2-tiling-engine.js';
import {createCoronaLearner} from '../assets/tile-corona-learning.js';
const dir=process.argv[2]??'/tmp/a2-online-pairs',summary=[];
const basis=[[1,0,0],[0,1,0],[0,0,1]],same=(a,b)=>a.every((v,i)=>v===b[i]);
for(const tile of ['turtle','hat'])for(const seed of [1,3]){
 const learner=createCoronaLearner(tile,{lattice:'turtle-sublattice'}),r=JSON.parse(fs.readFileSync(`${dir}/${tile}-online-witness-s${seed}.json`)),conflicts=[];
 for(const pos of r.rows.filter(x=>x.status==='valid'))for(let i=0;i<pos.placements.length;i++)for(let j=0;j<pos.placements.length;j++){
  if(i===j)continue;const a=pos.placements[i],b=pos.placements[j],sa=learner.materialize(a).orientation.symmetry,sb=learner.materialize(b).orientation.symmetry;
  const relative=learner.orientations.find(o=>basis.every(p=>same(a2Transform(p,o.symmetry),a2InverseTransform(a2Transform(p,sb),sa))));assert.ok(relative);
  const translation=a2InverseTransform(b.translation.map((v,k)=>v-a.translation[k]),sa),negative=r.rows.find(n=>n.status==='invalid'&&n.attachment.orientation===relative.index&&same(n.attachment.translation,translation));
  if(!negative)continue;
  // Independently compare exact normalized point occupancies, not just group
  // indices, to check that the witness really contains this negative pair.
  const norm=spec=>[...learner.materialize(spec).orientation.occupancy.values()].map(e=>`${a2InverseTransform(e.point.map((v,k)=>v+spec.translation[k]-a.translation[k]),sa)}:${e.weight}`).sort();
  const raw=spec=>[...learner.materialize(spec).orientation.occupancy.values()].map(e=>`${e.point.map((v,k)=>v+spec.translation[k])}:${e.weight}`).sort();
  assert.deepEqual(norm(a),raw(negative.root));assert.deepEqual(norm(b),raw(negative.attachment));
  conflicts.push({prefix:Math.max(pos.index,negative.index)+1,positiveIndex:pos.index,negativeIndex:negative.index,tiles:[i,j],negativePair:[negative.root,negative.attachment],witness:pos.placements});
 }
 conflicts.sort((a,b)=>a.prefix-b.prefix);
 const first=conflicts[0]??null;
 if(first){const negative=r.rows[first.negativeIndex];assert.equal(negative.oracle.status,'invalid');assert.ok(learner.verifyCorona([r.rows[first.positiveIndex].root,r.rows[first.positiveIndex].attachment],first.witness).complete);}
 fs.writeFileSync(`${dir}/${tile}-witness-contradiction-s${seed}.json`,JSON.stringify(first));
 const row={tile,seed,overlaps:conflicts.length,firstContradictionAtPair:first?.prefix??null,positivePairPosition:first?first.positiveIndex+1:null,negativePairPosition:first?first.negativeIndex+1:null,independentOccupancyAndCoronaCheck:true};summary.push(row);console.log(JSON.stringify(row));
}
fs.writeFileSync(`${dir}/witness-contradictions.json`,JSON.stringify(summary,null,2));
