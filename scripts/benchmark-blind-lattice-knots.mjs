import {readFileSync,writeFileSync,appendFileSync} from 'node:fs';
import {gzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {classifyLatticeBlind,proofId} from '../research/knot-classifier/lattice-blind-search.mjs';
import {LocalExtensionMarkings} from '../research/knot-classifier/local-extension-markings.mjs';
import {LocalPointMarkings} from '../research/knot-classifier/local-point-markings.mjs';
const args=process.argv.slice(2),get=(n,d)=>args.find(a=>a.startsWith(`--${n}=`))?.slice(n.length+3)??d;
const directory=get('directory','/private/tmp/knot-blind35'),laneName=get('lane','marked'),learn=laneName==='marked',limit=Number(get('limit','105'));
const manifest=JSON.parse(readFileSync(`${directory}/manifest.json`)),bounds={...manifest.bounds,maxMs:Number(get('max-ms','10000'))},archive=`${directory}/${laneName}-proofs.jsonl.gz`,output=`${directory}/${laneName}.json`;
const started=performance.now(),models=learn?{model:new LocalPointMarkings(),extensionModel:new LocalExtensionMarkings({probeNodeCap:bounds.extensionProbeNodeCap}),rootModel:new LocalExtensionMarkings({probeNodeCap:bounds.rootProbeNodeCap,maxComponentEdges:2*bounds.maxEdges,maxProbeHorizon:bounds.maxDepth})}:{};
const coldInitializationMs=performance.now()-started,runs=[],eventCounts={capacity:0,local:0,root:0};let archiveMs=0;writeFileSync(archive,'');
function checkpoint(incomplete){const result={lane:laneName,learn,incomplete,bounds,coldInitializationMs,queryTotalMs:runs.reduce((s,r)=>s+r.totalMs,0),archiveMs,totalMs:performance.now()-started,peakRssKiB:process.resourceUsage().maxRSS,nodes:runs.reduce((s,r)=>s+r.nodes,0),identified:runs.filter(r=>r.status==='identified').length,correct:runs.filter(r=>r.correct===true).length,incorrect:runs.filter(r=>r.correct===false).length,unknown:runs.filter(r=>r.status==='unknown').length,proofArchive:learn?{file:`${laneName}-proofs.jsonl.gz`,sha256:createHash('sha256').update(readFileSync(archive)).digest('hex'),bytes:readFileSync(archive).length,eventCounts}:null,runs};writeFileSync(output,JSON.stringify(result)+'\n');}
for(let i=0;i<Math.min(limit,manifest.cases.length);i++){
 const c=manifest.cases[i],r=classifyLatticeBlind(c.vertices,manifest.references.map(r=>r.vertices),{...bounds,...models,learn});
 r.caseIndex=i;r.predictedKnot=r.referenceIndex===null?null:manifest.references[r.referenceIndex].evaluatorKnot;r.correct=r.status==='identified'?r.predictedKnot===c.evaluatorKnot:null;
 const a=performance.now();for(const [channel,field]of [['capacity','learning'],['local','extensions'],['root','rootLearning']])if(r[field]){
  const start=eventCounts[channel];for(const event of r[field].eventsThisRun){const digest=event.signature?proofId(event.signature):createHash('sha256').update(JSON.stringify(event)).digest('hex');appendFileSync(archive,gzipSync(JSON.stringify({caseIndex:i,channel,eventIndex:eventCounts[channel]++,proofId:digest,event})+'\n'));}
  delete r[field].eventsThisRun;r[field].archiveRange=[start,eventCounts[channel]];
 }archiveMs+=performance.now()-a;runs.push(r);checkpoint(true);
 console.log(JSON.stringify({lane:laneName,caseIndex:i,knot:c.evaluatorKnot,status:r.status,predicted:r.predictedKnot,nodes:r.nodes,totalMs:r.totalMs,verificationMs:r.verificationMs,rootChecks:r.referenceChecks,admitted:r.referencesAdmitted,events:{...eventCounts},reason:r.reason}));
}
checkpoint(runs.length!==manifest.cases.length);console.log(JSON.stringify({lane:laneName,finished:true,cases:runs.length,totalMs:performance.now()-started}));
