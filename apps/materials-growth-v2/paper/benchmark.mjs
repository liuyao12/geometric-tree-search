// Matched implementation ablation; does not modify production engine files.
import { Worker, isMainThread, parentPort, workerData } from "node:worker_threads";
import { readFileSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import os from "node:os";
import assert from "node:assert/strict";
import { PointSearch } from "../kernel.mjs?v=observed-overlaps-1";
import { discover, learnSections } from "../learning.mjs";
import { MaterialExperiment } from "../material.mjs";
import { samplePatch } from "../samples.mjs";
import { checkPeriodicReference } from "../reference-check.mjs";
const hash = value => createHash("sha256").update(typeof value === "string" ? value : JSON.stringify(value)).digest("hex");
const drain = g => { let r; do { r=g.next(); } while(!r.done); return r.value; };
const cases = [{id:"nacl",steps:96},{id:"ice",steps:64},{id:"copper",steps:64}];
if (!isMainThread) {
  const {id,steps,mode,trial}=workerData;
  if(mode === "global") PointSearch.prototype.refresh = function(changed) {
    // Update the same obligation nodes, then recompute every cached candidate.
    // No deliberately duplicated local pass or disabled relation cache.
    for(const id of changed) {
      const p=this.points.get(id);
      if(p.active && p.total<this.capacity) { if(!this.graph.has(id)) this.graph.set(id,new Map()); }
      else this.graph.delete(id);
    }
    for(const id of this.candidates.keys()) this.updateCandidate(id);
  };
  const start=performance.now(), sample=samplePatch(id);
  const grammar=drain(discover(sample.atoms,{epsilon:.03}));
  const discovered=performance.now();
  const marking=drain(learnSections(grammar));
  const trained=performance.now();
  const e=new MaterialExperiment(grammar,marking,{maximumPoints:40000,maximumCandidates:80000});
  const initialized=performance.now(), initialChecks=e.engine.stats.checks;
  const trace=[];
  for(let i=0;i<steps;i++) {
    const event=e.step(); trace.push([event.kind,event.id||null]);
    assert(!["unknown","budget","exhausted","complete"].includes(event.kind),JSON.stringify(event));
  }
  const grown=performance.now(), stats={...e.engine.stats};
  const state=e.snapshot();
  assert(state.validation.legal && state.overlapValidation.legal);
  e.engine.auditGraph();
  const periodic=checkPeriodicReference(sample,e,state);
  if(periodic) assert.equal(periodic.fraction,1);
  const verified=performance.now();
  parentPort.postMessage({id,steps,mode,trial,atoms:state.atoms.length,
    checks:stats.checks-initialChecks,initialChecks,stats,points:state.pointCount,candidates:state.candidateCount,
    traceHash:hash(trace),stateHash:hash(e.engine.semanticState()),candidateHash:hash([...e.engine.candidates.keys()]),
    geometryHash:hash(state.atoms),stackHash:hash(e.engine.stack),legal:true,periodic,
    milliseconds:{discovery:discovered-start,learning:trained-discovered,initialization:initialized-trained,growth:grown-initialized,verification:verified-grown,total:verified-start},
    peakRssMiB:process.resourceUsage().maxRSS/1024});
} else {
  const results=[];
  for(const c of cases) for(let trial=0;trial<3;trial++) {
    const pair=[];
    for(const mode of trial%2 ? ["global","local"] : ["local","global"]) {
      const row=await new Promise(resolve=> {
        const w=new Worker(new URL(import.meta.url),{workerData:{...c,mode,trial}});
        const timer=setTimeout(()=>{w.terminate();resolve({...c,mode,trial,error:"120-second hard timeout"});},120000);
        w.once("message",r=>{clearTimeout(timer);resolve(r);});
        w.once("error",e=>{clearTimeout(timer);resolve({...c,mode,trial,error:e.message});});
      });
      results.push(row);pair.push(row); console.log(JSON.stringify(row));
    }
    if(pair.every(r=>!r.error)) for(const key of ["traceHash","stateHash","candidateHash","geometryHash","stackHash"]) assert.equal(pair[0][key],pair[1][key],`${c.id} ${key}`);
  }
  const sourceFiles=["kernel.mjs","material.mjs","geometry.mjs","learning.mjs","overlap-rules.mjs","samples.mjs","paper/benchmark.mjs"];
  const report={schema:"gcts-refresh-ablation/1",created:new Date().toISOString(),
    protocol:{cases,trials:3,order:"paired alternating; local/global, global/local, local/global",epsilon:.03,observedOnly:true,maximumPoints:40000,maximumCandidates:80000,hardTimeoutSeconds:120,scope:"Global cached-candidate revalidation vs dependency-local refresh; same scheduler, rules, proposal/cache policy. Not a comparison against state-of-the-art CSP packages or molecular dynamics. Timing repeats are not independent material replicates. Worker processes share one parent; RSS is process-wide high-water mark, not isolated per-case memory."},
    environment:{node:process.version,platform:process.platform,arch:process.arch,cpu:os.cpus()[0]?.model},
    sources:Object.fromEntries(sourceFiles.map(f=>[f,hash(readFileSync(new URL("../"+f,import.meta.url),"utf8"))])),results};
  if(process.argv[2]) writeFileSync(process.argv[2],JSON.stringify(report,null,2)+"\n");
  if(results.some(r=>r.error)) process.exitCode=1;
}
