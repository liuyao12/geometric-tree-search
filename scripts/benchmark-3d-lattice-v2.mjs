import {writeFile,mkdir} from 'node:fs/promises';
import {runExperiment} from '../apps/3d-lattice-tiler/v2/experiment.js';
import {CASES,MODES,VERSION} from '../apps/3d-lattice-tiler/v2/model.js';
const destination=process.argv[2]??'/tmp/lattice-v2-benchmark';
await mkdir(destination,{recursive:true});
const rows=[];
for(const tile of CASES.slice(0,5))for(const seed of [1,2,3]){
  // Rotate lane order across seeds; all learner state is recreated each time.
  const order=MODES.slice(seed-1).concat(MODES.slice(0,seed-1));
  for(const {id:mode} of order){
    const config={tile:tile.id,radius:1,mirrors:false,seed,mode,timeMs:2000,nodes:10000};let result;
    for await(const e of runExperiment(config))if(['result','error'].includes(e.type))result=e;
    const row={tile:tile.id,seed,mode,result:result.result??result.kind,covered:result.verification?.covered,stats:result.stats};rows.push(row);
    await writeFile(`${destination}/${tile.id}-${seed}-${mode}.json`,JSON.stringify(result));
    console.log(JSON.stringify(row));
  }
}
await writeFile(`${destination}/summary.json`,JSON.stringify({version:VERSION,protocol:{radius:1,seeds:[1,2,3],timeMs:2000,nodes:10000,mirrors:false,training:'cold online, no held-out generalization claim',timing:'sequential; model, marking, graph, learning, verification included; module load excluded'},rows},null,2));
