import assert from "node:assert/strict";
import { writeFileSync } from "node:fs";
import { discover, learnSections } from "../learning.mjs";
import { MaterialExperiment } from "../material.mjs";
import { samplePatch } from "../samples.mjs";
import { checkPeriodicReference } from "../reference-check.mjs";
import { CoronaCheckpoints } from "../coronas.mjs";
const drain=g=>{let r;do{r=g.next();}while(!r.done);return r.value;};
const sample=samplePatch("ice"), grammar=drain(discover(sample.atoms,{epsilon:.03}));
const rows=[];
for(const observedOnly of [false,true]) {
  const e=new MaterialExperiment(grammar,drain(learnSections(grammar,{observedOnly})),{maximumPoints:80000,maximumCandidates:160000});
  for(let step=1;step<=220;step++) {
    const event=e.step();
    assert(!["unknown","complete","budget","exhausted"].includes(event.kind),JSON.stringify(event));
    if([64,128,220].includes(step)) {
      const s=e.snapshot(false); assert.equal(s.atoms.length,step); assert(s.validation.legal);
      rows.push({observedOnly,atoms:s.atoms.length,periodic:checkPeriodicReference(sample,e,s),corona:new CoronaCheckpoints().progress(e.engine).completed,legal:s.validation.legal,overlapLegal:s.overlapValidation?.legal??null,counts:Object.fromEntries(["O","D"].map(label=>[label,s.atoms.filter(a=>a.species===label).length]))});
    }
  }
}
const report={schema:"ice-model-quality-ablation/1",protocol:{input:"192-atom Ice VIII D2O crop",epsilon:.03,seed:"one central atom",milestones:[64,128,220],scope:"Same discovery and candidate-generation policy, different learned constraint sets. One deterministic run each, no stochastic confidence intervals. Reference cell is evaluation-only. Global rigid alignment optimized over first-placement occurrence witnesses, not separately per atom. Site membership does not establish density or complete reconstruction."},rows};
if(process.argv[2])writeFileSync(process.argv[2],JSON.stringify(report,null,2)+"\n");
console.log(JSON.stringify(report,null,2));
