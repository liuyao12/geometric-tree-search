const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../../docs/research/gcts-rl-renewal');
const {validateClusters}=require(path.join(root,'propositional-wang.js'));
const data=JSON.parse(fs.readFileSync(path.join(root,'propositional-wang-reader-001.json'),'utf8'));
assert.equal(validateClusters(data),true);let mutations=0;
const bad=change=>{const x=structuredClone(data);change(x);assert.throws(()=>validateClusters(x));mutations++;};
for(let i=0;i<data.cases.length;i++){
 const p=data.cases[i];
 bad(x=>x.cases[i].target=['pred','Changed',[]]);bad(x=>x.cases[i].builder.micro_steps++);bad(x=>x.cases[i].compiler.bindings[0].compiled_line++);bad(x=>x.cases[i].compiler.bindings[0].formula=['bot']);
 for(let j=0;j<p.lines.length;j++){
  bad(x=>x.cases[i].lines[j].label.line++);
  bad(x=>x.cases[i].lines[j].input.proved.push(['bot']));
  bad(x=>x.cases[i].lines[j].input.theory={});
  bad(x=>x.cases[i].lines[j].input.assumptions.push(['bot']));
  bad(x=>x.cases[i].lines[j].patch.prefix_physical_steps++);
  if(p.lines[j].outcome==='line-checked')bad(x=>x.cases[i].lines[j].output.proved.pop());
  // All tiles are validated in the unmodified projection. Mutate every
  // tile of each first line, and a head-neighborhood tile of later lines.
  for(const k of j===0?p.lines[j].patch.tiles.map((_,k)=>k):[13]){
   for(const field of ['S','N','W','E'])bad(x=>{const t=x.cases[i].lines[j].patch.tiles[k];if(Array.isArray(t[field]))t[field][0]++;else t[field]++;});
  }
 }
}
console.log(JSON.stringify({cases:data.cases.length,lines:data.cases.reduce((n,p)=>n+p.lines.length,0),tile_instances:data.cases.reduce((n,p)=>n+p.lines.reduce((m,l)=>m+l.patch.tiles.length,0),0),reader_mutations_rejected:mutations}));
