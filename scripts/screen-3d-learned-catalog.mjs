// Sequential cold comparison. Full replay artifacts (including experimental
// assignments) go only to the requested run directory, never into source data.
import {Worker,isMainThread,parentPort,workerData} from 'node:worker_threads';
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {gzipSync} from 'node:zlib';
import {execFileSync} from 'node:child_process';
import {catalog,VERSION} from '../apps/3d-lattice-tiler/v2/model.js';
import {runExperiment} from '../apps/3d-lattice-tiler/v2/experiment.js';
import {verify} from '../apps/3d-lattice-tiler/v2/search.js';
import {POLYCUBE_GCTS_CANDIDATES} from '../assets/polycube-census-candidates.js';

if(!isMainThread){
 let last,progress=null;
 for await(const event of runExperiment(workerData)){
  if(event.phase==='update'){
   progress={pairs:event.pairs,counts:event.counts};
   parentPort.postMessage({type:'progress',progress});
  }
  if(['result','error'].includes(event.type))last=event;
 }
 if(last?.result==='finite_exact'&&!verify(last.model,last.placements).ok)throw Error('Independent replay failed');
 parentPort.postMessage({type:'done',last,progress});
}else{
 const args=Object.fromEntries(process.argv.slice(2).map(s=>s.replace(/^--/,'').split('=')));
 const timeMs=Number(args['time-ms']??3000),pairNodes=Number(args['pair-nodes']??500),radius=Number(args.radius??1),mirrors=args.mirrors==='true';
 const output=args.output??'/tmp/gcts-catalog-screen';
 if(!(timeMs>0&&pairNodes>0))throw Error('Positive time and pair budgets required');
 await mkdir(output,{recursive:true});
 const pool=args.catalog==='polycubes'?POLYCUBE_GCTS_CANDIDATES.map(c=>({id:c.id,name:c.id,priorStatus:c.screening.status,custom:{name:c.id,polycubes:[{name:c.id,voxels:c.voxels}],polycube_lattice:'z3'}})):catalog();
 const chosen=pool.filter(c=>!args.tiles||args.tiles.split(',').includes(c.id));
 if(!chosen.length)throw Error('No matching catalogue tiles');
 const sources={};for(const path of ['scripts/screen-3d-learned-catalog.mjs','apps/3d-lattice-tiler/corona-graph.js','apps/3d-lattice-tiler/marking-learning.js','apps/3d-lattice-tiler/v2/experiment.js','apps/3d-lattice-tiler/v2/model.js','apps/3d-lattice-tiler/v2/slab.js','apps/3d-lattice-tiler/v2/search.js'])sources[path]=createHash('sha256').update(await readFile(new URL('../'+path,import.meta.url))).digest('hex');
 const protocol={version:VERSION,commit:execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),sources,catalog:args.catalog??'app',timeMs,pairNodes,radius,mirrors,nodes:10000,seed:1,cold:true,sequential:true,scope:'Finite point windows; learned failures do not prove unmarked impossibility. Full 3D and slab models are distinct.'};
 const rows=[];
 for(const tile of chosen)for(const mode of ['free','gcts']){
  const config={tile:tile.id,custom:tile.custom,mode,timeMs,pairNodes,radius,mirrors,nodes:protocol.nodes,seed:protocol.seed};
  const started=performance.now();let progress=null;
  const reply=await new Promise(resolve=>{
   const worker=new Worker(new URL(import.meta.url),{workerData:config,resourceLimits:{maxOldGenerationSizeMb:1024}});
   let ended=false;const finish=value=>{if(ended)return;ended=true;clearTimeout(timer);worker.terminate();resolve(value);};
   const timer=setTimeout(()=>finish({type:'watchdog',progress}),timeMs+10000);
   worker.on('message',event=>{if(event.type==='progress')progress=event.progress;else if(event.type==='done')finish(event);});
   worker.on('error',error=>finish({type:'worker_error',message:error.message,progress}));
   worker.on('exit',code=>{if(!ended)finish({type:'worker_exit',code,progress});});
  });
  const result=reply.last,marking=result?.marking;
  const pairOutcomes={};for(const e of marking?.evidence??[]){const k=e.reason??e.status;pairOutcomes[k]=(pairOutcomes[k]??0)+1;}
  const row={tile:tile.id,name:tile.name,mode,result:result?.result??result?.kind??reply.type,reason:result?.reason??result?.message??reply.message??null,elapsedMs:performance.now()-started,model:result?.model?{domain:result.model.domain,placementDomain:result.model.placementDomain??null,orientations:result.model.orientations.length,points:result.model.orientations.reduce((n,o)=>n+o.cells.length,0),capacity:result.model.capacity}:null,verification:result?.verification??null,stats:result?.stats??null,learning:marking?{complete:marking.complete,accepted:marking.accepted,reason:marking.reason,pairs:marking.pairs??0,counts:marking.counts??{},pairOutcomes,positivePassed:marking.positivePassed??0,negativeBlocked:marking.negativeBlocked??0,points:marking.points??0,values:marking.values??0,elapsedMs:marking.elapsedMs}:reply.progress};
  rows.push(row);
  await writeFile(`${output}/${tile.id}-${mode}.json.gz`,gzipSync(JSON.stringify({config,...reply})));
  await writeFile(`${output}/summary.json`,JSON.stringify({protocol,rows},null,2));
  console.log(JSON.stringify(row));
 }
}
