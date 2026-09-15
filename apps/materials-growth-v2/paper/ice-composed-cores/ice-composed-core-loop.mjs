import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {gaussianPointClass} from './gaussian-point-filter.mjs';
import {linearFrontierClass} from './linear-frontier-decision.mjs';
import {verifiedGeometryCoreClass} from './verified-geometry-cores.mjs';
import {deriveGeometryCore} from './composed-geometry-core.mjs';
const [input,kernel,out]=process.argv.slice(2),data=JSON.parse(readFileSync(input)),row=data.models[0],model=row.model;
const sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex'),{PointSearch,verify}=await import(pathToFileURL(kernel));
const cores=[],rounds=[],start=performance.now();let status='budget-unknown',selected=[];
for(let round=0;round<40&&performance.now()-start<120000;round++){
 const prior=structuredClone(cores),setup=performance.now(),G=gaussianPointClass(linearFrontierClass(PointSearch),model,{enabled:true}),Engine=verifiedGeometryCoreClass(G,model,prior),e=new Engine(model),setupSeconds=(performance.now()-setup)/1000,root=JSON.stringify(e.semanticState());
 let proof=null,last=null,steps=0;const searchStart=performance.now();
 while(steps<2000&&performance.now()-start<120000){
  const d=e.decision();
  if(d.kind==='dead'){proof=deriveGeometryCore(model,e.fieldOwners,d.point,prior);if(proof)break;}
  last=e.advance();steps++;if(['complete','exhausted','unknown'].includes(last.kind))break;
 }
 selected=[...e.placed.keys()];const basic=verify(model,selected);assert(basic.legal);e.auditGraph();
 const r={round,priorCores:prior.length,setupSeconds,searchAndDerivationSeconds:(performance.now()-searchStart)/1000,steps,stats:{...e.stats},selected:selected.length,scalarComplete:basic.complete,newCoreSize:proof?.owners.length??null,newCoreDependencies:proof?.dependencies??[],status:proof?'verified-core-proposal':last?.kind??'budget-unknown'};
 e.undo(0);e.auditGraph();assert.equal(JSON.stringify(e.semanticState()),root);r.rootRollback=true;
 if(proof){verifiedGeometryCoreClass(G,model,[...prior,proof]);cores.push(proof);}
 rounds.push(r);console.log(JSON.stringify(r));
 if(last?.kind==='complete'){status='complete-awaiting-independent-replay';break;}
 if(!proof){status=last?.kind==='exhausted'?'exhausted-finite-pool':'budget-unknown';break;}
}
writeFileSync(out,JSON.stringify({scope:'Restarted marked reference search with ordered, validated geometry-only proof composition. No selected cover or feasibility-solver witness supplied.',sourceHash:sha(input),kernelHash:sha(kernel),codeHashes:Object.fromEntries(['ice-composed-core-loop.mjs','gaussian-point-filter.mjs','linear-frontier-decision.mjs','verified-geometry-cores.mjs','composed-geometry-core.mjs'].map(f=>[f,sha(new URL(f,import.meta.url))])),cores,rounds,status,selected,secondsIncludingRestarts:(performance.now()-start)/1000,limits:'Developmental finite registered pool and radius. Static validated rules per restart; no in-stack rule mutation. Up to 40 restarts/120 seconds, cooperative budget. Independent proof/witness replay pending. Not learned material markings, continuous completeness or blind growth.'},null,2),{flag:'wx'});
