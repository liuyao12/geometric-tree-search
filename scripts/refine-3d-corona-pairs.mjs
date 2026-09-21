// Research-only larger-budget checks of previously unresolved pairs. No saved
// marking is used, and a budget stop never becomes a negative label.
import {Worker,isMainThread,parentPort,workerData} from 'node:worker_threads';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {gzipSync,gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {checkCorona,verifyCorona} from '../apps/3d-lattice-tiler/corona-graph.js';
import {prepareVoxelPointModel,verifyVoxelPatch} from '../apps/3d-lattice-tiler/voxel-point-model.js';
import {POLYCUBE_GCTS_CANDIDATES} from '../assets/polycube-census-candidates.js';
if(!isMainThread){
 const {tile,pair,options}=workerData,record=POLYCUBE_GCTS_CANDIDATES.find(c=>c.id===tile);
 const model=prepareVoxelPointModel(record.voxels,{name:tile,mirrors:false,radius:1});
 const started=performance.now();let result,peakHeapBytes=0;
 for await(const e of checkCorona(model,pair,{...options,deadline:started+options.timeMs})){
  peakHeapBytes=Math.max(peakHeapBytes,process.memoryUsage().heapUsed);result=e;
  parentPort.postMessage({type:'progress',nodes:e.nodes,backtracks:e.backtracks,peakHeapBytes});
 }
 if(result.status==='valid'){
  if(!verifyCorona(model,pair,result.placements).complete||!verifyVoxelPatch(model,result.placements,{requireTarget:false}).ok)throw Error('Independent corona replay failed');
 }
 parentPort.postMessage({type:'done',result,elapsedMs:performance.now()-started,peakHeapBytes});
}else{
 const args=Object.fromEntries(process.argv.slice(2).map(a=>a.replace(/^--/,'').split('=')));
 if(!args.input)throw Error('Supply --input=<archived voxel screen directory>');
 const output=args.output??'/tmp/gcts-pair-refinement';await mkdir(output,{recursive:true});
 const options={nodes:Number(args.nodes??10000),dependencyLimit:Number(args.dependencies??4000000),candidateLimit:300000,timeMs:Number(args['time-ms']??20000)};
 for(const n of Object.values(options))if(!Number.isSafeInteger(n)||n<1)throw Error('Budgets must be positive integers');
 const report={protocol:{options,model:'voxel-center-corner-1',selection:'First previously unresolved pair per tile, unless max-per-tile is specified',mirrors:false,heapLimitMiB:1024,heapMeasurement:'Sampled worker heapUsed at yielded events; not peak process RSS',sources:{}},rows:[]};
 for(const path of ['scripts/refine-3d-corona-pairs.mjs','apps/3d-lattice-tiler/corona-graph.js','apps/3d-lattice-tiler/voxel-point-model.js'])report.protocol.sources[path]=createHash('sha256').update(await readFile(new URL('../'+path,import.meta.url))).digest('hex');
 for(const tile of POLYCUBE_GCTS_CANDIDATES.filter(c=>!args.tiles||args.tiles.split(',').includes(c.id))){
  const archive=JSON.parse(gunzipSync(await readFile(`${args.input}/${tile.id}-gcts.json.gz`)));
  if(archive.config.pointModel!=='voxel-center-corner'||archive.config.mirrors)throw Error('Expected a proper-rotation voxel-model archive');
  const pending=archive.last.marking.evidence.map((row,index)=>({...row,index})).filter(r=>r.status==='unresolved').slice(0,Number(args['max-per-tile']??1));
  for(const previous of pending){
   let progress=null;const began=performance.now();
   const reply=await new Promise(resolve=>{
    const worker=new Worker(new URL(import.meta.url),{workerData:{tile:tile.id,pair:previous.pair,options},resourceLimits:{maxOldGenerationSizeMb:1024}});
    let ended=false;const finish=value=>{if(ended)return;ended=true;clearTimeout(timer);worker.terminate();resolve(value);};
    const timer=setTimeout(()=>finish({type:'watchdog',progress}),options.timeMs+10000);
    worker.on('message',e=>e.type==='progress'?progress=e:finish(e));
    worker.on('error',e=>finish({type:'error',message:e.message,progress}));
    worker.on('exit',code=>{if(!ended)finish({type:'exit',code,progress});});
   });
   const {placements,...result}=reply.result??{status:'unresolved',reason:reply.message??reply.type};
   const row={tile:tile.id,index:previous.index,pair:previous.pair,previous:{status:previous.status,reason:previous.reason,nodes:previous.nodes},...result,elapsedMs:performance.now()-began,peakHeapBytes:reply.peakHeapBytes??reply.progress?.peakHeapBytes??null};
   report.rows.push(row);await writeFile(`${output}/${tile.id}-${previous.index}.json.gz`,gzipSync(JSON.stringify({options,tile:tile.id,pair:previous.pair,...reply})));
   await writeFile(`${output}/summary.json`,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(row));
  }
 }
}
