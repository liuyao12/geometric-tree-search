import fs from 'node:fs';
import {createCoronaLearner,TILE_SETS,CORONA_CRITERION} from '../assets/tile-corona-learning.js';
import {reduceMarking} from '../assets/marking-reduction.js';
globalThis.requestAnimationFrame=cb=>setImmediate(cb);
const directory=process.argv[2]||'/tmp/gcts-corona';fs.mkdirSync(directory,{recursive:true});const models={};
for(const setId of Object.keys(TILE_SETS)){
 const learner=createCoronaLearner(setId),report=await learner.collect({budget:5000,onProgress:p=>{if(p.attempts%50===0)console.log(setId,p.attempts,p.counts);}});
 if(report.model){learner.validateModel(report.model);models[setId]=reduceMarking(report.model,{preserveInterior:true});}
 fs.writeFileSync(`${directory}/tile-corona-${setId}.json`,JSON.stringify(report)+'\n');console.log(setId,report.classification);
}
fs.writeFileSync(`${directory}/tile-corona-markings.json`,JSON.stringify({criterion:CORONA_CRITERION,models})+'\n');
