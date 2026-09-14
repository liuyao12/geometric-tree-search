// Fixed learned weights, same full observed candidate pool, reference scheduler.
// In-sample reconstruction control, not held-out testing or continuous growth.
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
import {residualCapacityClass,independentResidualDomains} from './residual-capacity-filter.mjs';
import {branchExclusionClass} from './branch-local-exclusions.mjs';
import {linearFrontierClass} from './linear-frontier-decision.mjs';
import {certifiedDeadPointClass} from './certified-dead-point.mjs';
import {composedPointProofClass} from './composed-point-proofs.mjs';
const [inputPath,learningPath,kernelPath,dest,mode,stepArg,secondsArg,ordering='id',priorPath]=process.argv.slice(2);
assert(['id','filling-mass','type-prior'].includes(ordering));
assert(!mode||['residual','branch-exclusions','residual-exclusions','linear','linear-exclusions','linear-nogoods','linear-composed'].includes(mode));
const maxSteps=stepArg===undefined?100000:Number(stepArg),maxSeconds=secondsArg===undefined?15:Number(secondsArg);
assert(Number.isSafeInteger(maxSteps)&&maxSteps>0&&Number.isFinite(maxSeconds)&&maxSeconds>0);
const linear=!!mode?.startsWith('linear');
const composed=mode==='linear-composed',nogoods=mode==='linear-nogoods'||composed;
const residual=!!mode?.startsWith('residual'),exclusions=!!mode?.endsWith('exclusions')||(nogoods&&!composed);
const hash=x=>createHash('sha256').update(x).digest('hex');
const researchSourceHashes=Object.fromEntries(['boron-face-reference-search.mjs','linear-frontier-decision.mjs','branch-local-exclusions.mjs','certified-dead-point.mjs','composed-point-proofs.mjs'].map(name=>[name,hash(readFileSync(new URL(name,import.meta.url)))]));
const raw=readFileSync(inputPath),learnRaw=readFileSync(learningPath),d=JSON.parse(raw),learning=JSON.parse(learnRaw),r=learning.result;
assert.equal(hash(raw),learning.inputHash);assert.equal(r.status,'exact shared integer training cover');
const priorRaw=ordering==='type-prior'?readFileSync(priorPath):null,priors=priorRaw?JSON.parse(priorRaw):null;
if(priors){assert.equal(priors.inputHash,hash(raw));assert.equal(priors.learningHash,hash(learnRaw));}
const {PointSearch,verify}=await import(pathToFileURL(kernelPath));mkdirSync(dest);const results=[];
const CapacityEngine=residual?residualCapacityClass(PointSearch):PointSearch;
const ExclusionEngine=exclusions?branchExclusionClass(CapacityEngine):CapacityEngine;
const ProofEngine=composed?composedPointProofClass(ExclusionEngine):nogoods?certifiedDeadPointClass(ExclusionEngine):ExclusionEngine;
const Engine=linear?linearFrontierClass(ProofEngine):ProofEngine;
function audit(e,model){
 const filtered=residual?independentResidualDomains(e,model):null;
 const selected=new Set(e.placed.keys()),totals=new Map(model.required.map(p=>[p,0])),marks=new Map();
 for(const id of selected){const c=e.candidates.get(id);
  for(const x of c.t)totals.set(x.point,totals.get(x.point)+x.value);
  for(const x of c.m){if(marks.has(x.point))assert.equal(marks.get(x.point),x.lo);marks.set(x.point,x.lo);}
 }
 const expected=new Map([...totals].filter(([,v])=>v<model.capacity).map(([p])=>[p,new Map()]));
 for(const c of model.candidates){const incident=[];
  const cutBlocked=(e.certificates||[]).some(cert=>cert.ids.includes(c.id)&&cert.ids.every(id=>id===c.id||selected.has(id)));
  if(!selected.has(c.id)&&!e.branchBlocked?.has(c.id)&&!cutBlocked&&c.t.every(x=>totals.get(x.point)+x.value<=model.capacity)&&c.m.every(x=>!marks.has(x.point)||marks.get(x.point)===x.lo))
   for(const x of c.t)if(expected.has(x.point)&&(!filtered||filtered.get(x.point)?.has(c.id))){expected.get(x.point).set(c.id,x.value);incident.push(x.point);}
  assert.deepEqual([...e.reverse.get(c.id)].sort(),incident.sort());
 }
 assert.deepEqual([...e.graph.keys()].sort(),[...expected.keys()].sort());
 for(const [p,cs] of expected)assert.deepEqual([...e.graph.get(p)].sort(),[...cs].sort());
 for(const [p,v] of totals)assert.equal(e.points.get(p).total,v);
}
for(const [fold,c] of d.configurations.entries()){
 const prior=priors?.folds[fold];if(prior){assert.equal(prior.excluded,fold);assert(!prior.trainingConfigurations.includes(fold));}
 const base=c.occurrences.map((o,i)=>{
  const t=d.types[o.type];assert.equal(new Set(o.ids).size,o.ids.length);
  return {id:String(i).padStart(6,'0'),t:o.ids.map((p,u)=>({point:String(p),value:r.weightsByRole[r.roleOfSite[t.offset+u]]})),
   m:o.ids.flatMap((p,u)=>{const label=r.scalarLabelsByRole[r.roleOfSite[t.offset+u]];return label===null?[]:[{point:String(p),lo:label,hi:label}];})};
 });
 for(const marked of [false,true]){
  const model={capacity:r.capacity,required:Array.from({length:c.atoms},(_,i)=>String(i)),candidates:base.map(c=>({...c,m:marked?c.m:[]}))};
  const scores=new Map(model.candidates.map(candidate=>[candidate.id,ordering==='type-prior'?prior.types[c.occurrences[Number(candidate.id)].type].rank:candidate.t.reduce((sum,x)=>sum+x.value,0)]));
  const e=new Engine({...model,preference:ordering!=='id'?c=>scores.get(c.id):()=>0}),root=JSON.stringify(e.semanticState());audit(e,model);
  let steps=0,last;const start=performance.now();
  while(steps<maxSteps&&performance.now()-start<maxSeconds*1000){
   const choice=e.decision(),frontier=[...e.graph].map(([p,cs])=>({generation:e.points.get(p).generation,count:cs.size}));
   if(frontier.some(x=>x.count===0))assert.equal(choice.kind,'dead');
   else if(frontier.some(x=>x.count===1))assert.equal(choice.kind,'forced');
   else if(frontier.length){assert.equal(choice.kind,'branch');assert.equal(e.points.get(choice.point).generation,Math.min(...frontier.map(x=>x.generation)));}
   last=e.advance();steps++;
   if(steps%100===0||['complete','exhausted'].includes(last.kind)){e.auditGraph();audit(e,model);}
   if(['complete','exhausted','unknown'].includes(last.kind))break;
  }
  const selected=[...e.placed.keys()],check=verify(model,selected);assert(check.legal);
  const result={fold,file:c.file,marked,status:check.complete?'exact finite point-cover witness':last?.kind==='exhausted'?'exhausted finite pool':'budget-unknown',
   steps,seconds:(performance.now()-start)/1000,selected,stats:{...e.stats},required:c.atoms,candidates:base.length,
   residualCapacityFilter:residual,branchLocalExclusions:exclusions,linearFrontierDecision:linear,ordering,maxSteps,maxSeconds,exclusionCount:e.exclusionCount||0,residualDiagnostics:e.capacityDiagnostics?{...e.capacityDiagnostics}:null,
   proofDiagnostics:e.proofDiagnostics?{...e.proofDiagnostics}:null,proofVersion:e.proofVersion??null,composedProofs:composed,priorHash:priorRaw?hash(priorRaw):null};
  const certificates=e.certificates?[...e.certificates]:null;
  const proofNodes=composed?[...e.proofNodes]:null;
  e.undo(0);audit(e,model);
  if(nogoods){e.stack=[];e.clearCertificates();audit(e,model);result.rootBaseStateAfterProofReset=true;}
  assert.equal(JSON.stringify(e.semanticState()),root);result.rootSemanticRollback=!nogoods;
  writeFileSync(`${dest}/${fold}-${marked}.json`,JSON.stringify({inputHash:hash(raw),learningHash:hash(learnRaw),researchSourceHashes,model,result,...(nogoods?{certificates}: {}),...(composed?{proofNodes}:{})}),{flag:'wx'});
  results.push({...result,selected:selected.length});console.log(JSON.stringify(results.at(-1)));
 }
}
writeFileSync(`${dest}/summary.json`,JSON.stringify({scope:'In-sample known-coordinate reference search; same full pool marked/unmarked; no periodic selection lock or connectivity cuts in search; no blind growth',researchSourceHashes,residualCapacityFilter:residual,branchLocalExclusions:exclusions,kernelHash:hash(readFileSync(kernelPath)),results},null,2),{flag:'wx'});
