// Separate research control. Labels come from fresh exact point formulas, not
// stored markings. Every positive and every frontier obstruction is replayed.
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {gzipSync,gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {prepareVoxelPointModel,verifyVoxelPatch} from '../apps/3d-lattice-tiler/voxel-point-model.js';
import {verifyCorona,allowedTranslation} from '../apps/3d-lattice-tiler/corona-graph.js';
import {POLYCUBE_GCTS_CANDIDATES} from '../assets/polycube-census-candidates.js';
const execute=promisify(execFile),args=Object.fromEntries(process.argv.slice(2).map(a=>a.replace(/^--/,'').split('=')));
if(!args.input)throw Error('Supply --input=<archived voxel screen directory>');
const output=args.output??'/tmp/gcts-point-sat-screen',timeMs=Number(args['time-ms']??20000),encoding=args.encoding??'points';await mkdir(output,{recursive:true});
if(!['points','voxel-cover'].includes(encoding))throw Error('Unsupported encoding');
if(!Number.isSafeInteger(timeMs)||timeMs<1)throw Error('Positive integer time budget required');
const report={protocol:{timeMs,encoding,model:'voxel-center-corner-1',mirrors:false,selection:'First previously unresolved pair per tile',backend:'Research PB/SAT control; not the reference graph scheduler',sources:{}},rows:[]};
for(const path of ['scripts/solve_point_pair_corona.py','scripts/screen-3d-point-corona-sat.mjs','apps/3d-lattice-tiler/corona-graph.js','apps/3d-lattice-tiler/voxel-point-model.js'])report.protocol.sources[path]=createHash('sha256').update(await readFile(new URL('../'+path,import.meta.url))).digest('hex');
function verifyObstruction(model,{deadPoint,placements}){
 const sums=new Map(),used=new Set();
 for(const p of placements){
  const id=`${p.oi}@${p.translation}`;if(used.has(id)||!allowedTranslation(model,p.translation))throw Error('Invalid obstruction placement');used.add(id);
  for(const cell of model.orientations[p.oi].cells){const key=cell.pos.map((v,i)=>v+p.translation[i]).join(),n=(sums.get(key)??0)+cell.weight;if(n>model.capacity)throw Error('Overlapping obstruction');sums.set(key,n);}
 }
 const total=sums.get(deadPoint.join())??0;if(total<=0||total>=model.capacity)throw Error('Obstruction point is not exposed');
 for(let oi=0;oi<model.orientations.length;oi++)for(const anchor of model.orientations[oi].cells){
  const translation=deadPoint.map((v,i)=>v-anchor.pos[i]);if(!allowedTranslation(model,translation)||used.has(`${oi}@${translation}`))continue;
  if(model.orientations[oi].cells.every(c=>(sums.get(c.pos.map((v,i)=>v+translation[i]).join())??0)+c.weight<=model.capacity))throw Error('Obstruction has a legal candidate');
 }
 if(!verifyVoxelPatch(model,placements,{requireTarget:false}).ok)throw Error('Obstruction has voxel overlap');
}
for(const tile of POLYCUBE_GCTS_CANDIDATES.filter(c=>!args.tiles||args.tiles.split(',').includes(c.id))){
 const archive=JSON.parse(gunzipSync(await readFile(`${args.input}/${tile.id}-gcts.json.gz`)));
 if(archive.config.pointModel!=='voxel-center-corner'||archive.config.mirrors)throw Error('Expected a proper-rotation voxel-model archive');
 const index=archive.last.marking.evidence.findIndex(r=>r.status==='unresolved');if(index<0)continue;
 const previous=archive.last.marking.evidence[index],model=prepareVoxelPointModel(tile.voxels,{name:tile.id,radius:1});
 const prefix=`${output}/${tile.id}-${index}`,input={model,pair:previous.pair};await writeFile(`${prefix}-input.json`,JSON.stringify(input));
 const started=performance.now();let result;
 try{
  await execute(args.python??'python3',[fileURLToPath(new URL('./solve_point_pair_corona.py',import.meta.url)),`--input=${prefix}-input.json`,`--output=${prefix}-output.json`,`--time-ms=${timeMs}`,`--encoding=${encoding}`],{timeout:timeMs+15000,maxBuffer:1048576});
  result=JSON.parse(await readFile(`${prefix}-output.json`));
 }catch(e){result={status:'unresolved',reason:e.killed?'process time limit':e.message,stats:{},nogoods:[]};}
 const solveMs=performance.now()-started,verificationStart=performance.now();
 for(const n of result.nogoods)verifyObstruction(model,n);
 if(result.status==='valid'&&(!verifyCorona(model,previous.pair,result.placements).complete||!verifyVoxelPatch(model,result.placements,{requireTarget:false}).ok))throw Error('Independent positive replay failed');
 const artifact=gzipSync(JSON.stringify({input,result}));await writeFile(`${prefix}.json.gz`,artifact);
 const row={tile:tile.id,index,pair:previous.pair,previous:{status:previous.status,reason:previous.reason,nodes:previous.nodes},status:result.status,reason:result.reason,stats:result.stats,solveMs,verificationMs:performance.now()-verificationStart,obstructionsReplayed:result.nogoods.length,artifactSha256:createHash('sha256').update(artifact).digest('hex')};
 report.rows.push(row);await writeFile(`${output}/summary.json`,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(row));
}
