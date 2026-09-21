// Warm finite-window growth. Assignments and full witnesses stay outside the repo.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {gunzipSync,gzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {prepareVoxelPointModel,verifyVoxelPatch} from '../apps/3d-lattice-tiler/voxel-point-model.js';
import {pairCompatible} from '../apps/3d-lattice-tiler/marking-learning.js';
import {search,verify} from '../apps/3d-lattice-tiler/v2/search.js';
const args=Object.fromEntries(process.argv.slice(2).map(x=>x.replace(/^--/,'').split('=')));
if(!args.input||!args.output)throw Error('Supply --input=<local marking.json.gz> and --output=<directory>');
const radii=(args.radii??'2,3').split(',').map(Number),seeds=(args.seeds??'1,2').split(',').map(Number),timeMs=Number(args['time-ms']??20000),nodes=Number(args.nodes??1000000);
if(radii.some(r=>!Number.isInteger(r)||r<0||r>3)||seeds.some(s=>!Number.isSafeInteger(s))||!Number.isSafeInteger(timeMs)||timeMs<1||!Number.isSafeInteger(nodes)||nodes<1)throw Error('Invalid options');
const input=await readFile(args.input),saved=JSON.parse(gunzipSync(input)),sha=b=>createHash('sha256').update(b).digest('hex');
if(!saved.accepted||saved.labels.some(r=>r.status==='unresolved'))throw Error('Only a fully classified accepted marking may run');
const fields=saved.marking.fields,positives=saved.labels.filter(r=>r.status==='valid'),negatives=saved.labels.filter(r=>r.status==='invalid');
if(positives.some(r=>!pairCompatible(fields,r.pair))||negatives.length&&negatives.filter(r=>!pairCompatible(fields,r.pair)).length*2<=negatives.length)throw Error('Marking failed replay');
await mkdir(args.output,{recursive:true});
const sources={};for(const p of ['scripts/grow-3d-learned-voxel-windows.mjs','apps/3d-lattice-tiler/v2/search.js','apps/3d-lattice-tiler/voxel-point-model.js'])sources[p]=sha(await readFile(new URL('../'+p,import.meta.url)));
const report={protocol:{inputSha256:sha(input),sources,radii,seeds,timeMs,nodes,scope:'Sequential warm finite point-window growth; learned restriction, not an unmarked non-tiling proof. Collection and synthesis excluded.'},rows:[]};
for(const radius of radii){
 const model=prepareVoxelPointModel(saved.model.orientations[0].voxels,{name:saved.model.name,mirrors:saved.model.allowReflections,radius});
 if(JSON.stringify(model.orientations)!==JSON.stringify(saved.model.orientations))throw Error('Orientation order or point data changed');
 for(const seed of seeds)for(const mode of ['free','gcts']){
  const marked=mode==='free'?model:{...model,orientations:model.orientations.map((o,i)=>({...o,marks:fields[i]}))};let result;
  for await(const e of search(marked,{mode,seed,timeMs,nodes,learnedRestriction:mode==='gcts'}))result=e;
  const pointReplay=verify(marked,result.placements),voxelReplay=verifyVoxelPatch(model,result.placements);
  if(result.result==='finite_exact'&&(!pointReplay.ok||!voxelReplay.ok))throw Error('Independent replay failed');
  const raw=gzipSync(JSON.stringify({model:marked,result,pointReplay,voxelReplay}));await writeFile(`${args.output}/r${radius}-${mode}-${seed}.json.gz`,raw);
  const row={radius,seed,mode,result:result.result,reason:result.reason,pointReplay,voxelReplay,tiles:result.placements.length,stats:result.stats,artifactSha256:sha(raw)};report.rows.push(row);
  await writeFile(`${args.output}/summary.json`,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(row));
 }
}
