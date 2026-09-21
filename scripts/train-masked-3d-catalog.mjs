// Offline research validation; never installs a marking in the app or source.
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {gzipSync,gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {pairOrbits,transportPatch} from './lib/3d-pair-orbits.mjs';
import {verifyPointObstruction} from './lib/verify-point-obstruction.mjs';
import {learnMaskedMarking} from './lib/masked-point-encoder.mjs';
import {auditMarkingContacts} from './lib/audit-marking-contacts.mjs';
import {verifyCorona,placementKey} from '../apps/3d-lattice-tiler/corona-graph.js';
import {verifyVoxelPatch} from '../apps/3d-lattice-tiler/voxel-point-model.js';
import {search,verify} from '../apps/3d-lattice-tiler/v2/search.js';
const args=Object.fromEntries(process.argv.slice(2).map(a=>a.replace(/^--/,'').split('=')));
if(!args.input)throw Error('Supply --input=<completed orbit-catalogue directory>');
const output=args.output??'/tmp/gcts-masked-catalogue',timeMs=Number(args['growth-ms']??20000),nodes=Number(args.nodes??1000000),seeds=(args.seeds??'1,2,3').split(',').map(Number);
if(!Number.isSafeInteger(timeMs)||timeMs<1||!Number.isSafeInteger(nodes)||nodes<1||seeds.some(s=>!Number.isSafeInteger(s)||s<1))throw Error('Invalid growth budgets or seeds');
await mkdir(output,{recursive:true});const sha=s=>createHash('sha256').update(s).digest('hex');
const input=await readFile(`${args.input}/learning.json.gz`),{model,labels}=JSON.parse(gunzipSync(input)),checkpoint=JSON.parse(await readFile(`${args.input}/checkpoint.json`)),orbits=pairOrbits(model);
if(checkpoint.modelSha!==sha(JSON.stringify(model))||checkpoint.orbitSha!==sha(JSON.stringify(orbits.groups)))throw Error('Catalogue geometry changed');
if(labels.length!==orbits.pairs.length||labels.some((r,i)=>r.pair.map(placementKey).join('|')!==orbits.pairs[i].map(placementKey).join('|')))throw Error('Incomplete or reordered pair catalogue');
let positiveWitnesses=0,obstructions=0;
for(let i=0;i<orbits.groups.length;i++){
 const group=orbits.groups[i],entry=checkpoint.groups[i];
 if(!entry){if(group.members.some(m=>labels[m.index].status!=='unresolved'))throw Error('Unrecorded resolved label');continue;}
 const raw=await readFile(`${args.input}/${entry.file}`);if(sha(raw)!==entry.sha256)throw Error('Oracle artifact changed');const result=JSON.parse(raw);
 for(const n of result.nogoods??[]){verifyPointObstruction(model,n);obstructions++;}
 for(const member of group.members){
  if(labels[member.index].status!==result.status)throw Error('Catalogue label changed');
  if(result.status==='valid'){
   const placements=transportPatch(result.placements,member,orbits.transforms);
   if(!verifyCorona(model,member.pair,placements).complete||!verifyVoxelPatch(model,placements,{requireTarget:false}).ok)throw Error('Positive witness failed replay');positiveWitnesses++;
  }
 }
}
const sources={};for(const p of ['scripts/train-masked-3d-catalog.mjs','scripts/lib/masked-point-encoder.mjs','scripts/lib/audit-marking-contacts.mjs','scripts/lib/3d-pair-orbits.mjs','scripts/lib/verify-point-obstruction.mjs','apps/3d-lattice-tiler/marking-learning.js','apps/3d-lattice-tiler/corona-graph.js','apps/3d-lattice-tiler/voxel-point-model.js','apps/3d-lattice-tiler/v2/search.js'])sources[p]=sha(await readFile(new URL('../'+p,import.meta.url)));
const candidates=[];let best;
for(const extent of [1,2,3]){
 const candidate=learnMaskedMarking(model,labels,{transforms:orbits.transforms,extent,iterations:2000,seed:1}),{fields,representation,...metadata}=candidate;candidates.push(metadata);
 if(!best||candidate.negativeBlocked>best.negativeBlocked||candidate.negativeBlocked===best.negativeBlocked&&candidate.points<best.points)best=candidate;
}
const accepted=best.counts.unresolved===0&&best.counts.valid>0&&best.positivePassed===best.counts.valid&&(best.counts.invalid===0||best.negativeBlocked*2>best.counts.invalid);
const contactAudit=auditMarkingContacts(model,best.fields,labels,orbits.transforms);
await writeFile(`${output}/marking.json.gz`,gzipSync(JSON.stringify({model,labels,marking:best,accepted,contactAudit})));
const report={protocol:{inputSha256:sha(input),sources,timeMs,nodes,seeds,trainingIncludedInGrowth:false,oracleRuns:checkpoint.runs,scope:'Warm sequential finite-window comparison; catalogue collection and synthesis reported separately. No infinite construction or aperiodicity proof.'},replay:{positiveWitnesses,obstructions},learning:{accepted,chosenExtent:best.extent,candidates},contactAudit,rows:[]};
for(const seed of seeds)for(const mode of ['free','gcts']){
 if(mode==='gcts'&&!accepted)continue;
 const marked=mode==='free'?model:{...model,orientations:model.orientations.map((o,i)=>({...o,marks:best.fields[i]}))};let result;
 for await(const e of search(marked,{mode,learnedRestriction:mode==='gcts',timeMs,nodes,seed}))result=e;
 const pointReplay=verify(marked,result.placements),voxelReplay=verifyVoxelPatch(model,result.placements);
 if(result.result==='finite_exact'&&(!pointReplay.ok||!voxelReplay.ok))throw Error('Growth failed independent replay');
 const artifact=gzipSync(JSON.stringify({model:marked,result,pointReplay,voxelReplay}));await writeFile(`${output}/${mode}-${seed}.json.gz`,artifact);
 const row={mode,seed,result:result.result,reason:result.reason,pointReplay,voxelReplay,stats:result.stats,artifactSha256:sha(artifact)};report.rows.push(row);
 await writeFile(`${output}/summary.json`,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(row));
}
console.log(JSON.stringify({accepted,counts:best.counts,passed:best.positivePassed,blocked:best.negativeBlocked,points:best.points,values:best.values,contactAudit}));
