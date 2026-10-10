const assert=require('node:assert/strict');const fs=require('node:fs');const path=require('node:path');
const root=path.resolve(__dirname,'../..');const data=JSON.parse(fs.readFileSync(path.join(root,'docs/research/gcts-rl-renewal/propositional-receptors-001.json')));
const reader=require(path.join(root,'docs/research/gcts-rl-renewal/propositional-receptors.js'));
const expected=JSON.parse(fs.readFileSync(process.argv[2]));let lines=0,expanded=0;
for(const c of data.cases){const r=c.runs.point;if(!r.proof)continue;
 assert.deepEqual(reader.expand(r.proof),expected[c.id]);expanded+=expected[c.id].length;
 r.proof.forEach((row,j)=>{assert.equal(reader.tex(row.formula),r.proof_tex[j]);
  const e=reader.english(row,c.hypotheses.length);assert.equal(typeof e,'string');assert.ok(e.length>10);
  if(row.kind==='mp')for(const k of row.refs)assert.ok(e.includes(k<0?'hypothesis '+(k+c.hypotheses.length+1):'line '+(k+1)));
  if(row.kind==='lemma')assert.ok(e.includes(reader.tex(row.parameter)));lines++;
 });
}
console.log(JSON.stringify({cases:Object.keys(expected).length,formula_and_english_lines:lines,primitive_expansion_lines:expanded,all_equal_to_independent_checker:true}));
