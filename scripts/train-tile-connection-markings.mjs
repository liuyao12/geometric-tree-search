import fs from 'node:fs';
import {createConnectionLearner,TILE_SETS} from '../assets/tile-connection-learning.js';
globalThis.requestAnimationFrame=cb=>setTimeout(cb,0);
const directory=process.argv[2]||'/tmp/gcts-three-learning';fs.mkdirSync(directory,{recursive:true});
for(const setId of Object.keys(TILE_SETS)){
 const learner=createConnectionLearner(setId);
 const report=await learner.collect({onProgress:p=>{if(p.attempts%40===0)console.log(setId,p.attempts,p.total,p.counts);}});
 report.markedCheck=await learner.grow({support:report.model?.support||[],target:24,budget:2000,seed:701});
 fs.writeFileSync(`${directory}/${setId}.json`,JSON.stringify(report));
 console.log(JSON.stringify({setId,counts:report.counts,encoding:report.encoding,classes:report.model?.classes,nonzero:report.model?.nonzero,marked:report.markedCheck.result,ms:report.elapsedMs}));
}
