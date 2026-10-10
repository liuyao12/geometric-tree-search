const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../../docs/research/gcts-rl-renewal');
const {validate}=require(path.join(root,'factored-receptors.js'));
const v=JSON.parse(fs.readFileSync(path.join(root,'factored-receptors-reader-001.json'),'utf8'));
assert.equal(validate(v),true);let mutations=0,proofs=0;
const bad=f=>{const b=structuredClone(v);f(b);assert.throws(()=>validate(b));mutations++;};
for(let i=0;i<v.cases.length;i++){
 const c=v.cases[i];if(!c.runs.factored.proof)continue;proofs++;
 bad(b=>b.cases[i].target=['P']);
 for(let j=0;j<c.runs.factored.proof.length;j++){
  bad(b=>b.cases[i].runs.factored.proof[j].formula=['P']);
  const t=c.runs.factored.point_tiles.findIndex(t=>t.key[0]===j);
  bad(b=>b.cases[i].runs.factored.point_tiles[t].occupancy[0][1]++);
  for(let k=0;k<c.runs.factored.point_tiles[t].marks.length;k++)bad(b=>b.cases[i].runs.factored.point_tiles[t].marks[k][1]='bad');
 }
}
for(let j=0;j<v.native.lines.length;j++){
 bad(b=>b.native.lines[j].label.formula=['bot']);
 bad(b=>b.native.lines[j].input.proved.push(['bot']));
 bad(b=>b.native.lines[j].output.proved.pop());
}
console.log(JSON.stringify({proofs,native_commands:v.native.lines.length,reader_mutations_rejected:mutations}));
