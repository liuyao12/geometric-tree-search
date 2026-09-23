import {mkdirSync,writeFileSync,readFileSync} from 'node:fs';
import { resolve } from 'node:path';
import {createHash} from 'node:crypto';
import { verifyPatch } from '../3d-reptiles/chair/chair44.js';
import {createGrowthState,enumerateGrowthCandidates} from '../3d-reptiles/chair/chair-gcts.js';
import { graphFor, clearCache, extend } from './lib/chair-relief-points.mjs';
const out=resolve(process.env.CHAIR_RELIEF_OUT??'output/chair44-relief-search');mkdirSync(out,{recursive:true});
const maxNodes=Number(process.env.CHAIR_RELIEF_NODES??500),maxRadius=Number(process.env.CHAIR_RELIEF_RADIUS??1);
const minRadius=Number(process.env.CHAIR_RELIEF_MIN_RADIUS??1);
const maxTiles=Number(process.env.CHAIR_RELIEF_TILES??256),retryUnknown=process.env.CHAIR_RELIEF_RETRY_UNKNOWN==='1';
const seed={variantId:0,origin:[0,0,0],generation:0};
const full=enumerateGrowthCandidates(createGrowthState()).candidateNodes;
const raw=[...graphFor([seed]).candidates.values()].map(({variantId,origin,id})=>({variantId,origin,id}));
const sourceHash=file=>createHash('sha256').update(readFileSync(new URL(file,import.meta.url))).digest('hex');
let report={schemaVersion:1,source:{date:new Date().toISOString().slice(0,10),reliefProfileSHA256:sourceHash('../3d-reptiles/chair/relief-profile.js'),tileSHA256:sourceHash('../3d-reptiles/chair/chair44.js')},model:'displayed relief; t-occupancy only; integer translations and 24 proper cubic rotations',
  noMarkingChecks:true,parameters:{maxNodes,maxTiles,maxRadius},rootCandidates:raw.length,fullArrowCandidates:full.size,pairs:[],summary:{},witnesses:[]};
function save(){writeFileSync(resolve(out,'results.json'),JSON.stringify(report,null,2)+'\n');}
if(minRadius>1){report=JSON.parse(readFileSync(resolve(out,'results.json'),'utf8'));report.parameters={maxNodes,maxTiles,maxRadius};}
else for(const p of raw) {
 const roots=[seed,{variantId:p.variantId,origin:p.origin,generation:0}];
 const graph=graphFor(roots);
 report.pairs.push({...p,extra:!full.has(p.id),deadPoint:graph.dead,frontierPoints:graph.frontier.size,candidates:graph.candidates.size,extensions:[]});
}
report.summary.immediate={extra:report.pairs.filter(p=>p.extra).length,extraDead:report.pairs.filter(p=>p.extra&&p.deadPoint).length,
 originalDead:report.pairs.filter(p=>!p.extra&&p.deadPoint).length,viable:report.pairs.filter(p=>!p.deadPoint).length};
save();console.log(JSON.stringify({phase:'initial frontier',...report.summary.immediate}));
for(let radius=minRadius;radius<=maxRadius;radius++) {
 for(const p of report.pairs.filter(p=>!p.deadPoint&&!p.extensions.some(e=>e.status==='exhausted'||(e.radius===radius&&(!retryUnknown||e.status!=='unknown'))))) {
  clearCache();
  const result=extend([seed,{variantId:p.variantId,origin:p.origin,generation:0}],{radius,maxNodes,maxTiles});
  const {witness,...stats}=result;
  stats.limits={maxNodes,maxTiles};
  const previous=p.extensions.find(e=>e.radius===radius);
  if(previous){stats.priorAttempts=[...(previous.priorAttempts??[]),{...previous,priorAttempts:undefined}];p.extensions=p.extensions.filter(e=>e.radius!==radius);}
  p.extensions.push(stats);
  if(witness){
   const filename=`pair-${report.pairs.indexOf(p)}-radius-${radius}.json`;
   const arrowCheck=verifyPatch(witness);
   writeFileSync(resolve(out,filename),JSON.stringify({model:report.model,seed:[seed,p],radius,stats,placements:witness,arrowCheck},null,2)+'\n');
   report.witnesses.push({pair:p.id,radius,file:filename,tiles:witness.length,arrowCheck});
  }
  save();
  console.log(JSON.stringify({phase:'extension',pair:p.id,radius,status:stats.status,nodes:stats.nodes,tiles:witness?.length,maxTiles:stats.maxTiles,milliseconds:stats.milliseconds}));
 }
 report.summary[`radius${radius}`]={tested:report.pairs.filter(p=>p.extensions.some(e=>e.radius===radius)).length,consistent:report.pairs.filter(p=>p.extensions.find(e=>e.radius===radius)?.status==='consistent finite patch').length,
 exhausted:report.pairs.filter(p=>p.extensions.find(e=>e.radius===radius)?.status==='exhausted').length,
 unknown:report.pairs.filter(p=>p.extensions.find(e=>e.radius===radius)?.status==='unknown').length};save();
 console.log(JSON.stringify({phase:'radius summary',radius,...report.summary[`radius${radius}`]}));
}
