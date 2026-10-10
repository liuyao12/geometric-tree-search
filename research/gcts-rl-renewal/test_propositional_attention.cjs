const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../..'),doc=path.join(root,'docs/research/gcts-rl-renewal');
const reader=require(path.join(doc,'propositional-attention.js'));
const bytes=fs.readFileSync(path.join(doc,'propositional-receptors-001.json'));
assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),reader.DATA_SHA);
const data=JSON.parse(bytes),view=reader.inspect(data),positive=reader.trial(view,0);
assert.equal(positive.accepted,true);
assert.deepEqual(positive.tile.marks,view.tiles[4].marks);
assert.deepEqual(positive.tile.occupancy,view.tiles[4].occupancy);
const outcomes=[];
for(let j=0;j<4;j++){
  const t=reader.trial(view,j);assert.equal(t.accepted,j===0);
  outcomes.push({reference:j,accepted:t.accepted,conflicts:t.conflicts,internal_conflicts:t.tile.internal,occupancy:t.tile.occupancy,marks:t.tile.marks});
}
assert.ok(outcomes[1].conflicts.length&&outcomes[2].conflicts.length);
assert.ok(outcomes[3].internal_conflicts.length);
for(const j of [-1,4,1.5,'0'])assert.throws(()=>reader.trial(view,j));
const mutations=[
  d=>{d.authored_proofs.push({});},
  d=>{d.cases[0].target=['P'];},
  d=>{d.cases[0].runs.point.initial_marks.pop();},
  d=>{d.cases[0].runs.point.proof[0].formula=['P'];},
  d=>{d.cases[0].runs.point.proof[4].refs=[1,3];},
  d=>{d.cases[0].runs.point.point_tiles.find(t=>t.key[0]===4).marks.pop();},
  d=>{d.cases[0].runs.point.point_tiles.find(t=>t.key[0]===4).marks[0][1]=1;},
  d=>{d.cases[0].runs.point.point_tiles[0].occupancy[0][1]=6;},
  d=>{d.cases[0].runs.point.point_tiles.push(d.cases[0].runs.point.point_tiles[0]);},
  d=>{d.cases[0].runs.point.placements[0]=d.cases[0].runs.point.placements[1];},
  d=>{d.basis.rules[440].inputs.reverse();},
  d=>{d.cases[0].runs.point.point_tiles.find(t=>t.key[0]===4).key[2]=[4,3];}
];
for(const change of mutations){const d=structuredClone(data);change(d);assert.throws(()=>reader.inspect(d));}
if(process.argv[2]){
  const expected=JSON.parse(fs.readFileSync(process.argv[2]));
  assert.deepEqual(outcomes,expected.outcomes);
  assert.equal(view.assignments,expected.certificate.assignments);
}
console.log(JSON.stringify({status:'passed',existing_proof_lines:view.result.proof.length,reference_trials:outcomes.length,valid_trials:outcomes.filter(t=>t.accepted).length,mutations_rejected:mutations.length,artifact_sha256:reader.DATA_SHA,independent_trial_comparison:!!process.argv[2]}));
