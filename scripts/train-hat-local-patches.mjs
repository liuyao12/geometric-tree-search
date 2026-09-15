import fs from 'node:fs';
import {collect} from '../assets/hat-local-learning.js';
globalThis.requestAnimationFrame=callback=>setTimeout(callback,0);
const output=process.argv[2]||'/tmp/hat-local-patches.json';
const report=await collect({onProgress:p=>{if(p.attempts%20===0)console.log(`${p.attempts}/${p.total} connections · ${JSON.stringify(p.counts)}`);}});
fs.writeFileSync(output,JSON.stringify(report));
console.log(JSON.stringify({output,counts:report.counts,patches:report.samples.length,encoding:report.encoding,classes:report.model?.classes,ms:report.elapsedMs}));
