// Distinguish unfinished point obligations from missing geometric information.
import {writeFileSync} from 'node:fs';
import {samplePatch} from '../samples.mjs';
import {discover,learnSections} from '../learning.mjs';
import {MaterialExperiment} from '../material.mjs';
import {compose,inverse,transform,distance} from '../geometry.mjs';
import {scoreStructure,referenceBall} from './structural-metrics.mjs';
const drain=g=>{let r;do{r=g.next();}while(!r.done);return r.value;};
const sample=samplePatch('ice'),grammar=drain(discover(sample.atoms,{epsilon:.03}));
const e=new MaterialExperiment(grammar,drain(learnSections(grammar)),{maximumPoints:80000,maximumCandidates:160000});
const results=[];
for(let step=1;step<=440;step++){
  const event=e.step();if(['unknown','budget','exhausted','complete'].includes(event.kind)){results.push({step,event});break;}
  if(![220,440].includes(step))continue;
  const snapshot=e.snapshot(false),first=e.engine.candidates.get(e.engine.placed.keys().next().value);
  const poses=grammar.types[first.meta.type].occurrences.map(o=>compose(o.pose,inverse(first.meta.pose)));
  const metrics=scoreStructure(sample.evaluation,snapshot.atoms,{poses,epsilon:.03});
  const reference=referenceBall(sample.evaluation,transform(metrics.alignment,[0,0,0]),6*metrics.spacing);
  const atoms=snapshot.atoms.map(a=>({...a,position:transform(metrics.alignment,a.position)}));
  const missing=reference.filter(r=>!atoms.some(a=>a.species===r.species&&distance(a.position,r.position)<=.03));
  const points=e.registry.points.map(p=>({...p,position:transform(metrics.alignment,p.position)}));
  const diagnostics=missing.map(r=>{
    const matches=points.filter(p=>distance(p.position,r.position)<=.03).map(p=>{
      const state=e.engine.points.get(p.id);return {id:p.id,active:state.active,total:state.total,generation:Number.isFinite(state.generation)?state.generation:null,degree:e.engine.graph.get(p.id)?.size??null,assignedMarks:[...state.marks.values()].flat().length};
    });return {...r,matches};
  });
  const row={step,atoms:atoms.length,coverage:metrics.windows.at(-1),missing:diagnostics,stats:e.engine.stats};results.push(structuredClone(row));console.log(JSON.stringify({step,atoms:row.atoms,missing:diagnostics.length,pending:diagnostics.filter(r=>r.matches.some(p=>p.active&&p.total<1)).length,uncached:diagnostics.filter(r=>!r.matches.length).length}));
}
if(process.argv[2])writeFileSync(process.argv[2],JSON.stringify({scope:'Post-hoc diagnostic of known ice counterexample; no new scientific validation claim.',results},null,2)+'\n');
