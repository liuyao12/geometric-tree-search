import fs from 'node:fs';
import {collect,grow} from '../assets/hat-local-learning.js';
globalThis.requestAnimationFrame=callback=>setTimeout(callback,0);
const output=process.argv[2]||'/tmp/hat-local-patches.json';
const report=await collect({onProgress:p=>{if(p.attempts%20===0||p.training+p.test===24)console.log(`${p.attempts}/${p.total} attachments · ${p.training} training · ${p.test} held out`);}});
report.evaluations=[];
for(const seed of [701,1709]){
 const baseline=await grow({seed});const marked=await grow({seed,support:report.model.support});report.evaluations.push({seed,baseline,marked});
 console.log({seed,baseline:baseline.nodes,marked:marked.nodes,baselineMs:baseline.elapsedMs,markedMs:marked.elapsedMs});
}
fs.writeFileSync(output,JSON.stringify(report));console.log(JSON.stringify({output,training:report.training.length,test:report.test.length,passed:report.testPassed,classes:report.model.classes,nonzero:report.model.nonzero,attachments:report.attachmentCount,survivors:report.attachmentSurvivors,ms:report.elapsedMs}));
