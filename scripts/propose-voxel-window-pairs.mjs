// A viable unmarked window proposes pairs to check; it does not label them.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {execFile} from 'node:child_process';import {promisify} from 'node:util';import {createHash} from 'node:crypto';import {fileURLToPath} from 'node:url';
import {pairOrbits} from './lib/3d-pair-orbits.mjs';
import {verifyPointWindowFrontier} from './lib/verify-point-window-frontier.mjs';
import {verifyPointObstruction} from './lib/verify-point-obstruction.mjs';
import {verifyCorona,placementKey} from '../apps/3d-lattice-tiler/corona-graph.js';
import {verifyVoxelPatch} from '../apps/3d-lattice-tiler/voxel-point-model.js';
const args=Object.fromEntries(process.argv.slice(2).map(a=>a.replace(/^--/,'').split('='))),execute=promisify(execFile),sha=b=>createHash('sha256').update(b).digest('hex');
if(!args.catalog||!args.input||!args.result||!args.output)throw Error('Supply --catalog, --input, --result and --output');
const timeMs=Number(args['pair-ms']??5000),limit=Number(args['max-pairs']??8);if(!Number.isSafeInteger(timeMs)||timeMs<1||!Number.isSafeInteger(limit)||limit<1)throw Error('Invalid budget');
const started=performance.now(),sourceRaw=await readFile(args.result),source=JSON.parse(sourceRaw),inputRaw=await readFile(args.input),data=JSON.parse(inputRaw),checkpoint=JSON.parse(await readFile(`${args.catalog}/checkpoint.json`));
let model;try{model=JSON.parse(await readFile(`${args.catalog}/model.json`));}catch(e){if(e.code!=='ENOENT')throw e;({model}=JSON.parse(await readFile(`${args.catalog}/pair-0.json`)));}
const canonical=x=>Array.isArray(x)?x.map(canonical):x&&typeof x==='object'?Object.fromEntries(Object.keys(x).sort().map(k=>[k,canonical(x[k])])):x;
if(sha(JSON.stringify(model))!==checkpoint.modelSha||source.problemSha256!==sha(JSON.stringify(canonical(data))))throw Error('Mismatched catalogue or source input');
const system=m=>JSON.stringify([m.capacity,m.placementDomain,m.allowReflections,m.orientations]);if(system(model)!==system(data.model))throw Error('Window and catalogue systems differ');
if(source.status!=='valid'||!(data.pair?verifyCorona(data.model,data.pair,source.placements):verifyPointWindowFrontier(data.model,source.placements,data.fixed)).complete||!verifyVoxelPatch(data.model,source.placements,{requireTarget:false}).ok)throw Error('Proposal window is not independently verified');
const orbits=pairOrbits(model),token=p=>p.map(placementKey).join('|'),lookup=new Map(orbits.groups.map((g,i)=>[token(g.pair),i])),totals=new Map(),supports=source.placements.map(p=>new Map(model.orientations[p.oi].cells.map(c=>[c.pos.map((x,i)=>x+p.translation[i]).join(),c.weight])));
for(const cells of supports)for(const [k,w] of cells)totals.set(k,(totals.get(k)??0)+w);
const proposals=new Map();
for(let i=0;i<supports.length;i++)for(let j=0;j<i;j++){
 if(![...supports[i].keys()].some(k=>supports[j].has(k)))continue;
 const core=new Set([...supports[i].keys(),...supports[j].keys()]),missing=[...core].filter(k=>totals.get(k)!==model.capacity).length;
 let orbit,hint;outer:for(const g of orbits.transforms)for(const swap of [false,true]){
  let pair=[source.placements[j],source.placements[i]].map(p=>({oi:g.map[p.oi].oi,translation:g.transform(p.translation).map((x,a)=>x+g.map[p.oi].shift[a])}));if(swap)pair.reverse();const origin=pair[0].translation;pair=pair.map(p=>({...p,translation:p.translation.map((x,a)=>x-origin[a])}));
  const found=lookup.get(token(pair));if(found!==undefined){orbit=found;hint=source.placements.map(p=>({oi:g.map[p.oi].oi,translation:g.transform(p.translation).map((x,a)=>x+g.map[p.oi].shift[a]-origin[a])}));break outer;}
 }
 if(orbit===undefined)throw Error('Observed adjacent pair missing from complete catalogue');
 if(checkpoint.groups[orbit]?.status&&checkpoint.groups[orbit].status!=='unresolved')continue;
 if(!proposals.has(orbit)||missing<proposals.get(orbit).missingCorePoints)proposals.set(orbit,{orbit,missingCorePoints:missing,sourcePair:[j,i],pair:orbits.groups[orbit].pair,hint});
}
const ranked=[...proposals.values()].sort((a,b)=>a.missingCorePoints-b.missingCorePoints||a.orbit-b.orbit).slice(0,limit);
await mkdir(args.output,{recursive:false});const sources={};for(const name of ['scripts/propose-voxel-window-pairs.mjs','scripts/solve_voxel_pair_corona.py','scripts/lib/verify-point-window-frontier.mjs','scripts/lib/3d-pair-orbits.mjs'])sources[name]=sha(await readFile(new URL('../'+name,import.meta.url)));
const manifest={sources,sourceWindow:{inputSha256:sha(inputRaw),resultSha256:sha(sourceRaw),tiles:source.placements.length,elapsedMs:source.stats.elapsedMs},rows:[]},report={timeMs,limit,phaseHints:args['phase-hints']!=='false',observedUnresolvedOrbits:proposals.size,proposals:ranked.map(({hint,...p})=>p),rows:[],scope:'Viable windows rank pair proposals. Every imported label comes from a complete unmarked pair-corona check, never from the ranking.'};
const persist=async()=>{report.elapsedMs=performance.now()-started;await writeFile(`${args.output}/summary.json`,JSON.stringify(report,null,2)+'\n');await writeFile(`${args.output}/resolved.json`,JSON.stringify(manifest,null,2)+'\n');};
await persist();
for(const proposal of ranked){
 const inputFile=`${args.output}/pair-${proposal.orbit}.json`,file=`${args.output}/result-${proposal.orbit}.json`;await writeFile(inputFile,JSON.stringify({model,pair:proposal.pair}));
 const hintFile=`${args.output}/hint-${proposal.orbit}.json`;
 if(args['phase-hints']!=='false'){
  const used=new Set(proposal.hint.map(placementKey));
  if(proposal.pair.some(p=>!used.has(placementKey(p)))||!verifyCorona(model,[],proposal.hint).complete||!verifyVoxelPatch(model,proposal.hint,{requireTarget:false}).ok)throw Error('Transported proposal patch failed replay');
  await writeFile(hintFile,JSON.stringify({placements:proposal.hint}));
 }
 const command=[fileURLToPath(new URL('./solve_voxel_pair_corona.py',import.meta.url)),`--input=${inputFile}`,`--output=${file}`,`--time-ms=${timeMs}`,'--frontier-batch=4'],prior=checkpoint.groups[proposal.orbit];
 if(args['phase-hints']!=='false')command.push(`--phase-hint=${hintFile}`);
 if(prior){const old=JSON.parse(await readFile(`${args.catalog}/${prior.file}`));if(old.stats?.frontier==='occupancy')command.push(`--resume=${args.catalog}/${prior.file}`);}
 await execute(args.python??'python3',command,{timeout:timeMs+15000,maxBuffer:1048576});const raw=await readFile(file),r=JSON.parse(raw);
 for(const n of r.nogoods??[])verifyPointObstruction(model,n);
 if(r.status==='valid'&&(!verifyCorona(model,proposal.pair,r.placements).complete||!verifyVoxelPatch(model,r.placements,{requireTarget:false}).ok))throw Error('Proposed pair witness failed independent replay');
 if(r.status!=='unresolved')manifest.rows.push({orbit:proposal.orbit,file,sha256:sha(raw),status:r.status});
 const row={orbit:proposal.orbit,missingCorePoints:proposal.missingCorePoints,status:r.status,reason:r.reason,stats:r.stats};report.rows.push(row);await persist();console.log(JSON.stringify(row));
}
